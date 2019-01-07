from __future__ import print_function

import array
import socket
import struct
import sys


def _to_hex(data):
    return r''.join(r'\x{:02x}'.format(b if isinstance(b, int) else ord(b)) for b in data)


def _checksum(buf):
    n = len(buf)
    a = array.array("H", buf[:n & (~0x1)])

    if n & 0x1 == 0x1:
        a.append(struct.unpack('<H', buf[-1:] + b'\x00')[0])

    s = sum(a)
    s = (s >> 16) + (s & 0xFFFF)
    s += (s >> 16)
    
    return socket.ntohs((~s) & 0xFFFF)


def _eth(dst, src, ip_src_addr, ip_dest_addr, src_port, dest_port, data):
    ip_packet = _ip(ip_src_addr, ip_dest_addr, src_port, dest_port, data)

    packet = (
        dst +        # dst
        src +        # src
        b'' +        # vlan
        b'\x08\x00'  # type
    ) + ip_packet

    return packet


def _ip(src_addr, dest_addr, src_port, dest_port, data):
    udp_packet = _udp(src_addr, dest_addr, src_port, dest_port, data)

    header = (
        b'\x45' +                                 # v_hl
        b'\x00' +                                 # tos
        struct.pack('H', 20 + len(udp_packet)) +  # len
        b'\x00\x00' +                             # id
        b'\x00\x00' +                             # off
        b'\x40' +                                 # ttl
        b'\x11' +                                 # p
        struct.pack('!H', 0) +                    # sum
        src_addr +                                # src
        dest_addr                                 # dst
    )

    sum_ = _checksum(header)

    packet = header[:-10] + (
        struct.pack('!H', sum_) + # sum
        src_addr +                # src
        dest_addr +               # dst
        udp_packet                # data
    )

    return packet


def _udp(src_addr, dest_addr, src_port, dest_port, data):
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


def main():
    if len(sys.argv) < 2:
        print('Usage: {} <bind_ip>:<bind_port> <interface>'.format(sys.argv[0]), file=sys.stderr)
        sys.exit(-1)

    _, args_bind, args_interface = sys.argv

    bind_ip, bind_port = args_bind.split(':', 1)

    print('{}: bind_ip = {}, bind_port = {}, interface = {}'.format(sys.argv[0], bind_ip, bind_port, args_interface))

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(socket.getaddrinfo(bind_ip, int(bind_port), 0)[0][-1])

    raw_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    raw_socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    raw_socket.bind((args_interface, 0))
  
    while True:
        data, forward_address = server_socket.recvfrom(1024)

        print('{}: recvfrom, data = {!r}, forward_address = {}'.format(sys.argv[0], data, forward_address))

        src_address_bin, src_port, dest_address_bin, dest_port, forwarded_data = struct.unpack('!4sH4sH{}s'.format(len(data) - 12), data)

        payload = _eth(
            b'\xff\xff\xff\xff\xff\xff',  # FF:FF:FF:FF:FF:FF
            b'\x0a\x0b\x0c\x01\x02\x03',  # 0A:0B:0C:01:02:03
            src_address_bin,
            dest_address_bin,
            src_port,
            dest_port,
            forwarded_data)

        raw_socket.send(payload)
        

if __name__ == '__main__':
    main()
