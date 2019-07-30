# udp-broadcast-relay-py

## Introduction

This package provides a way to relay UDP broadcast packets between networks.

The need for this tool came when using a cheap wireless NVR which uses Goolink to provide access to the video streams. If you are within the same network, it all works just fine, but it won't work accross different networks. Goolink uses P2P networking to handle this use case, but it only works if the NVR is somehow exposed to the Internet, and has access to Goolinks servers. I needed to access my NVR through a VPN so neither use case would work. I'm still not entirely sure how the Goolink protocol works (all the documentation is in Chinese, and there's no easy access to the SDK), but using a protocol analyzer, I managed to figure out that the app broadcasts a UDP packet (which contains information to identify the NVR and stream) and the NVR starts streaming the video source. This tool takes care of relaying the UDP broadcast packets to the network on which the NVR is hosted.

How does it work?

The package contains two scripts:

* **``udp_broadcast_forward.py``**

  This script listens for UDP broadcasts on a specific port, and when a package is received, some info of its header and the payload are packed (Using the ``struct`` module) and sent to a specific address/port onto which the replay script is listening.

* **``udp_broadcast_replay.py``**

  This script is listening on a specific (configurable) port for packets sent from the forward script. Once a packet is received, the payload is dissasembled to extract the forwarded packet info and it is used to broadcast at new raw IP packet the imitates the original packet, essentially "replaying" the original behavior. It needs to be run using root privileges as they are needed to use RAW sockets.

The code has been tested using Python 2.7 and 3.7, and it has been kept as simple as possible so it can be run with most Python interpreters (event stripped down implementations). Originally, I intended for it to run using [MicroPython](http://micropython.org), but it doesn't support RAW sockets as of this writing.

## Usage

### udp_broadcast_forward

```
$ python udp_broadcast_forward.py
Usage: udp_broadcast_forward.py <port> <dest_ip>:<dest_port> [<bind>]
```

* port: The UDP port to listen to broadcasts.
* dest_ip: IP address on which udp_broadcast_replay is running.
* dest_port: IP port on which  udp_broadcast_replay is listening.
* bind: IP address to bind to (Optional. Default: 255.255.255.255).

### udp_broadcast_replay

```
$ python udp_broadcast_replay.py 
Usage: udp_broadcast_replay.py <bind_ip>:<bind_port> <interface>
```

* bind_ip: The IP address to bind to.
* bind_port: The IP port to listen for forwarded UDP packets.
* interface: The name of the interfce onto which the replayed packets are going to be written to.
