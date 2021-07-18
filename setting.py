import json
import socket
import time
import re

from Packet import PacketEncoder

manager_port = 21110
host = '127.0.0.1'
my_send_link = None


def get_listen_port():
    f = open('listen_port_number.txt', 'r+')
    listen_port = int(f.read())
    f.seek(0)
    f.truncate()
    f.write(str(listen_port + 2))
    f.close()
    return listen_port


def send_on_link(src_port, dst_port, packet):
    link = make_link(src_port, dst_port)
    message = json.dumps(packet, cls=PacketEncoder).encode('ascii')
    link.send(message)


# todo: clean TOF?
def make_link(src_port, dst_port):
    global my_send_link
    if my_send_link:
        my_send_link.close()
        time.sleep(0.1)

    my_send_link = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_send_link.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_send_link.bind((host, src_port))
    my_send_link.connect((host, dst_port))
    return my_send_link
