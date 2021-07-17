import socket
import re

manager_port = 12100
host = '127.0.0.1'


def get_listen_port():
    f = open('listen_port_number.txt', 'r+')
    listen_port = int(f.read())
    f.seek(0)
    f.truncate()
    f.write(str(listen_port + 1))
    f.close()
    return listen_port


def make_link(port):
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.connect((host, port))
    return my_socket
