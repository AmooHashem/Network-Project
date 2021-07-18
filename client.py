import json
import socket
import threading
import re

from Packet import Packet, PacketEncoder
from setting import host, manager_port, get_listen_port, send_on_link, make_link

my_listen_port = get_listen_port()
my_send_port = my_listen_port + 1

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
    return Packet(message['type'], message['src_id'], message['dst_id'], message['data'])


def send_message(link, message):
    message = json.dumps(message, cls=PacketEncoder).encode('ascii')
    print(message)
    link.send(message)


def find_next_port(dst_id):
    if dst_id in left_subtree_ids:
        return left_child_port
    elif dst_id in right_subtree_ids:
        return right_child_port
    else:
        return parent_port


def receive():
    global left_child_id, left_child_port, right_child_id, right_child_port
    while True:
        try:
            client, address = receive_socket.accept()
            packet = get_message(client)
            type = packet.type
            src_id = packet.src_id
            dst_id = packet.dst_id
            data = packet.data

            print("%%%")
            print(packet)

            if type == 41:
                chile_port = data
                child_id = src_id
                print(child_id)
                if left_child_id == -1:
                    left_child_id = child_id
                    left_child_port = chile_port
                else:
                    right_child_id = child_id
                    right_child_port = chile_port
                continue

            if type == 20:
                child_id = src_id
                src_id = data
                known_ids.append(src_id)
                if child_id == left_child_id:
                    left_subtree_ids.append(src_id)
                else:
                    right_subtree_ids.append(src_id)
                if parent_port != -1:
                    send_on_link(my_send_port, parent_port, Packet(20, id, parent_id, src_id))
                continue

            if dst_id == id:
                if type == 10:
                    next_port = find_next_port(src_id)
                    new_data = '<-' + id if next_port == parent_id else '->' + id
                    send_on_link(my_send_port, next_port, Packet(11, id, src_id, new_data))
                if type == 11:
                    print(id + data)
                if type == 31:
                    print(data)

                continue

            next_port = find_next_port(dst_id)
            if next_port == -1:
                next_port = find_next_port(src_id)
                send_on_link(my_send_port, next_port, Packet(31, id, src_id, f'DESTINATION {dst_id} NOT FOUND'))
                continue
            #
            #
            #
            if type == 11:
                packet.data = ('<-' + id if next_port == parent_id else '->' + id) + packet.data

            send_on_link(my_send_port, next_port, packet)



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
            dst_id = command_parts[1]
            if dst_id not in known_ids:
                print(f'Unknown destination {dst_id}')
                continue
            next_port = find_next_port(dst_id)
            if next_port == -1:
                print(f'DESTINATION {dst_id} NOT FOUND')
                continue
            send_on_link(my_send_port, next_port, Packet(10, id, dst_id, ''))

        if command_parts[0] == 'ADVERTISE':
            dst_id = command_parts[1]
            if dst_id not in known_ids:
                print(f'Unknown destination {dst_id}')
                continue
            # todo
            continue


if __name__ == '__main__':

    id = input("Please enter your id: ")

    manager_link = make_link(my_send_port, manager_port)
    manager_link.send(f"{id} REQUESTS FOR CONNECTING TO NETWORK ON PORT {my_listen_port}".encode('ascii'))
    message_parts = manager_link.recv(1024).decode('ascii').split(' ')
    parent_id, parent_port = message_parts[2], int(message_parts[5])
    known_ids.append(parent_id)

    if parent_id != '-1':
        send_on_link(my_send_port, parent_port, Packet(41, id, parent_id, my_listen_port))
        send_on_link(my_send_port, parent_port, Packet(20, id, parent_id, id))

    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    write_thread = threading.Thread(target=write)
    write_thread.start()
