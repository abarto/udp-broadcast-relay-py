#!/usr/bin/env python

"""
udp_broadcast_replay

This scripts listens on a specific port for UDP packets sent by the
udp_broadcast_forward.py script and "replays" the forwarded packet
constructing an Ethernet frame with the headers and payload of the original
packet.

Usage: udp_broadcast_replay.py <bind_ip>:<bind_port> <interface>

* bind_ip: The IP address to bind to.
* bind_port: The IP port to listen for forwarded UDP packets.
* interface: The name of the interfce onto which the replayed packets are
  going to be written to.

Copyright (c) 2020 Agustin Barto <abarto@gmail.com>
"""

from __future__ import absolute_import, print_function

import array
import fcntl
import IN
import os
import socket
import struct
import sys


__author__ = 'Agustin Barto'
__copyright__ = 'Copyright (C) 2019 Agustin Barto'
__license__ = 'MIT License'
__version__ = '0.1'


def _checksum(buf):
    """Computes a checksum using 16-bit one's complement"""
    
    n = len(buf)
    a = array.array("H", buf[:n & (~0x1)])

    if n & 0x1 == 0x1:
        a.append(struct.unpack('<H', buf[-1:] + b'\x00')[0])

    s = sum(a)
    s = (s >> 16) + (s & 0xFFFF)
    s += (s >> 16)
    
    return socket.ntohs((~s) & 0xFFFF)


def _eth(dst, src, data):
    """Builds an Ethernet frame with and IP packet as payload"""

    packet = (
        dst +        # dst
        src +        # src
        b'' +        # vlan
        b'\x08\x00'  # type
    ) + data

    return packet


def _ip(src_addr, dest_addr, src_port, dest_port, data):
    """Builds an IP packet with a UDP packet as payload"""

    header = (
        b'\x45' +                            # v_hl
        b'\x00' +                            # tos
        struct.pack('!H', 20 + len(data)) +  # len
        b'\x00\x00' +                        # id
        b'\x00\x00' +                        # off
        b'\x40' +                            # ttl
        b'\x11' +                            # p (UDP)
        struct.pack('!H', 0) +               # sum
        src_addr +                           # src
        dest_addr                            # dst
    )

    sum_ = _checksum(header)

    packet = header[:-10] + (
        struct.pack('!H', sum_) + # sum
        src_addr +                # src
        dest_addr +               # dst
        data                      # data
    )

    return packet


def _udp(src_addr, dest_addr, src_port, dest_port, data):
    """Builds a UDP packet"""

    packet = (
        struct.pack('!H', src_port) +     # sport
        struct.pack('!H', dest_port) +    # dport
        struct.pack('!H', 8 + len(data))  # ulen
    )

    s = struct.pack('>4s4sbBH', src_addr, dest_addr, 0, 17, 8 + len(data))

    sum_ = _checksum(s + packet + data)
    if sum_ == 0:
        sum_ = 0xffff

    packet += (
        struct.pack('!H', sum_) + # sum
        data                      # data
    )

    return packet


def _get_ip_address(interface):
    """Returns the IP address of a network inerface"""
    
    probe_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(
        fcntl.ioctl(probe_socket.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', interface[:15].encode('utf-8')))[20:24])


def main():
    if len(sys.argv) < 2:
        print('Usage: {} <bind_ip>:<bind_port> <interface> [<ip|eth>]'.format(sys.argv[0]), file=sys.stderr)
        sys.exit(-1)

    _, args_bind, args_interface = sys.argv[:3]
    extra_args = sys.argv[3:]

    bind_ip, bind_port = args_bind.split(':', 1)
    
    mode = 'eth' if 'eth' in extra_args else 'ip'
    debug = 'DEBUG' in os.environ

    print('{}: bind_ip = {}, bind_port = {}, interface = {}, mode = {}, debug = {}'.format(
        sys.argv[0], bind_ip, bind_port, args_interface, mode, debug))

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(socket.getaddrinfo(bind_ip, int(bind_port), 0)[0][-1])

    if mode == 'eth':
        raw_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        raw_socket.bind((args_interface, 0))
    else:
        raw_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        raw_socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        raw_socket.setsockopt(socket.SOL_SOCKET, IN.SO_BINDTODEVICE, args_interface)
        #raw_socket.bind((_get_ip_address(args_interface), 0))
  
    while True:
        data, forward_address = server_socket.recvfrom(1024)

        print('{}: recvfrom, data = {!r}, forward_address = {}'.format(sys.argv[0], data, forward_address))

        src_address_bin, src_port, dest_address_bin, dest_port, forwarded_data = struct.unpack('!4sH4sH{}s'.format(
            len(data) - 12), data)

        if debug:
            print('{}: src_address_bin: {!r} ({})'.format(sys.argv[0], src_address_bin, socket.inet_ntoa(src_address_bin)))
            print('{}: src_port: {}'.format(sys.argv[0], src_port))
            print('{}: dest_address_bin: {!r} ({})'.format(sys.argv[0], dest_address_bin, socket.inet_ntoa(dest_address_bin)))
            print('{}: dest_port: {}'.format(sys.argv[0], dest_port))
            print('{}: forwarded_data: {!r}'.format(sys.argv[0], forwarded_data))
            print('{}: len(forwarded_data): {}'.format(sys.argv[0], len(forwarded_data)))

        udp_packet = _udp(src_address_bin, dest_address_bin, src_port, dest_port, forwarded_data)
        ip_packet = _ip(src_address_bin, dest_address_bin, src_port, dest_port, udp_packet)

        if debug:
            print('{}: udp_packet:\n{!r}'.format(sys.argv[0], udp_packet))
            print('{}: ip_packet:\n{!r}'.format(sys.argv[0], ip_packet))

        if mode == 'eth':
            eth_frame = _eth(
                b'\xff\xff\xff\xff\xff\xff',  # FF:FF:FF:FF:FF:FF
                b'\x0a\x0b\x0c\x01\x02\x03',  # 0A:0B:0C:01:02:03
                ip_packet)

            if debug:
                print('{}: eth_frame:\n{!r}'.format(sys.argv[0], eth_frame))

            raw_socket.send(eth_frame)
        else:
            raw_socket.sendto(ip_packet, (socket.inet_ntoa(dest_address_bin), dest_port))
        

if __name__ == '__main__':
    main()
