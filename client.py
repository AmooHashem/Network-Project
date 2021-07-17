import json
import socket
import threading
import re

from Packet import Packet, PacketEncoder
from setting import host, manager_port, get_listen_port, make_tcp_connection, make_link

my_listen_port = get_listen_port()

receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receive_socket.bind((host, my_listen_port))
receive_socket.listen()

parent_id = -1
parent_port = -1
right_child_id = -1
right_child_port = -1
left_child_id = -1
left_child_port = -1
known_ids = []
right_subtree_ids = []
left_subtree_ids = []


def get_message(client):
    message = json.loads(client.recv(1024).decode('ascii'))
    return message


def send_message(link, message):
    message = json.dumps(message, cls=PacketEncoder).encode('ascii')
    print(message)
    link.send(message)


def receive():
    global left_child_id, known_ids
    while True:
        try:
            client, address = receive_socket.accept()
            response = get_message(client)
            type = response['type']
            if type == 41:
                chile_port = response['data']
                child_id = response['src_id']
                print(child_id)
                if left_child_id == -1:
                    left_child_id = child_id
                    left_child_port = chile_port
                else:
                    right_child_id = child_id
                    right_child_port = chile_port
            if type == 20:
                child_id = response['src_id']
                src_id = response['data']
                known_ids.append(src_id)
                if child_id == left_child_id:
                    left_subtree_ids.append(src_id)
                else:
                    right_subtree_ids.append(src_id)
                if parent_port != -1:
                    make_tcp_connection(parent_port, Packet(20, id, parent_id, src_id))

        # if message == 'username':
        #     sender.send(id.encode('ascii'))
        except:
            # sender.close()
            break


def write():
    while True:
        command = input()
        command_parts = command.split(' ')
        if command == 'SHOW KNOWN CLIENTS':
            print(known_ids)
        if command_parts[0] == 'ROUTE':
            dest_id = command_parts[1]


if __name__ == '__main__':

    id = input("Please enter your id: ")
    manager_link = make_link(manager_port)
    manager_link.send(f"{id} REQUESTS FOR CONNECTING TO NETWORK ON PORT {my_listen_port}".encode('ascii'))
    message_parts = manager_link.recv(1024).decode('ascii').split(' ')
    manager_link.close()
    parent_id, parent_port = message_parts[2], int(message_parts[5])
    known_ids.append(parent_id)

    if parent_id != '-1':
        make_tcp_connection(parent_port, Packet(41, id, parent_id, my_listen_port))
        make_tcp_connection(parent_port, Packet(20, id, parent_id, id))

    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    write_thread = threading.Thread(target=write)
    write_thread.start()
