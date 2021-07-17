import json
import socket
import threading
import re

from Packet import Packet, PacketEncoder
from setting import host, manager_port, get_listen_port, make_link
import application
my_listen_port = get_listen_port()

receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receive_socket.bind((host, my_listen_port))
receive_socket.listen()

parent_id = '-1'
parent_listen_port = '-1'
known_ports = []
subtree_ids = []


def get_message(client):
    message = json.loads(client.recv(1024).decode('ascii'))
    return message


def send_message(link, message):
    message = json.dumps(message, cls=PacketEncoder).encode('ascii')
    print(message)
    link.send(message)


def receive():
    while True:
        try:
            client, address = receive_socket.accept()
            response = get_message(client)
            type = response['type']
            if type == 41:
                known_ports.append(response['data'])
                print(known_ports)

                parent_link = make_link(parent_listen_port)
                send_message(parent_link, Packet(41, id, parent_id, my_listen_port))
            if type == 0 and response['data'][:5] == 'CHAT:':
                application.handle_chat(response['dst_id'], response['data'])
        # if message == 'username':
        #     sender.send(id.encode('ascii'))
        except:
            # sender.close()
            break


def write():
    while True:
        command = input()
        # if re.search(f"CONNECT TO MANAGER", command):
        #     print("salam")
        #     client.connect((HOST, MANAGER_PORT))

        # client.send(message.encode('ascii'))


if __name__ == '__main__':

    id = input("Please enter your id: ")
    manager_link = make_link(manager_port)
    manager_link.send(f"{id} REQUESTS FOR CONNECTING TO NETWORK ON PORT {my_listen_port}".encode('ascii'))
    message_parts = manager_link.recv(1024).decode('ascii').split(' ')
    manager_link.close()
    parent_id, parent_listen_port = message_parts[2], int(message_parts[5])
    known_ports.append(parent_listen_port)

    if parent_id != '-1':
        parent_link = make_link(parent_listen_port)
        send_message(parent_link, Packet(41, id, parent_id, my_listen_port))
        parent_link.close()

    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    write_thread = threading.Thread(target=write)
    write_thread.start()
