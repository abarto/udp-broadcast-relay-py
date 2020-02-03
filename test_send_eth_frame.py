import array
import socket
import struct
import sys

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


def _ip(src_addr, dest_addr, data):
    """Builds an IP packet with a UDP packet as payload"""

    header = (
        b'\x45' +                            # v_hl
        b'\x00' +                            # tos
        struct.pack('!H', 20 + len(data)) +  # len
        b'\x00\x01' +                        # id
        b'\x00\x00' +                        # off
        b'\x40' +                            # ttl
        b'\x11' +                            # p (UDP)
        struct.pack('!H', 0) +               # sum
        src_addr +                           # src
        dest_addr                            # dst
    )

    sum_ = _checksum(header)

    packet = header[:-10] + (
        struct.pack('!H', sum_) +  # sum
        src_addr +                 # src
        dest_addr +                # dst
        data                       # data
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
        struct.pack('!H', sum_) +  # sum
        data                       # data
    )

    return packet


if __name__ == '__main__':
    _, src_addr, dst_addr, src_port, dst_port, iface = sys.argv

    raw_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    raw_socket.bind((iface, 0))

    src_address_bin = socket.inet_aton(src_addr)
    dst_address_bin = socket.inet_aton(dst_addr)

    udp_packet = _udp(src_address_bin, dst_address_bin, int(src_port), int(dst_port), b'\x01\x02\x03\x04\x05\x06')
    ip_packet = _ip(src_address_bin, dst_address_bin, udp_packet)
    eth_frame = _eth(
        b'\xff\xff\xff\xff\xff\xff',  # FF:FF:FF:FF:FF:FF
        b'\x0a\x0b\x0c\x01\x02\x03',  # 0A:0B:0C:01:02:03
        ip_packet)

    print('eth_frame = {!r}'.format(eth_frame))

    raw_socket.send(eth_frame)
    raw_socket.close()
