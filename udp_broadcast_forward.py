from __future__ import print_function

import socket
import struct
import sys


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print('Usage: {} <port> <dest_ip>:<dest_port> [<bind>]'.format(sys.argv[0]), file=sys.stderr)
        sys.exit(-1)

    _, args_port, args_dest, args_bind = sys.argv + (['255.255.255.255'] if len(sys.argv) < 4 else [])

    dest_ip, dest_port = args_dest.split(':', 1)

    print('{}: args_port = {}, dest_ip = {}, dest_port = {}, bind = {}'.format(sys.argv[0], args_port, dest_ip, dest_port, args_bind))

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server_socket.bind((args_bind, int(args_port)))

    while True:
        data, (src_address, src_port) = server_socket.recvfrom(1024)

        print('{}: recvfrom, data = {!r}, src_address = {}, src_port = {}'.format(sys.argv[0], data, src_address, src_port))

        payload = struct.pack('!4sH4sH{}s'.format(len(data)), socket.inet_aton(src_address), src_port, socket.inet_aton(args_bind), int(args_port), data)
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(payload, (dest_ip, int(dest_port)))


if __name__ == '__main__':
    main()
