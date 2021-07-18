import json
import socket
import threading
import re

from Packet import Packet, PacketEncoder
from setting import host, manager_port, get_listen_port, send_on_link, make_link
import re

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

            #################
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

            #################

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

            #################

            next_port = find_next_port(dst_id)
            if next_port == -1:
                next_port = find_next_port(src_id)
                send_on_link(my_send_port, next_port, Packet(31, id, src_id, f'DESTINATION {dst_id} NOT FOUND'))
                continue

            #################

            if type == 0 and data[:5] == 'CHAT:':
                handle_chat_receive(src_id, data)
            if type == 0 and data == 'Salam Salam Sad Ta Salam':
                handle_salam(src_id)

            #
            #
            #
            if type == 11:
                packet.data = ('<-' + id if next_port == parent_id else '->' + id) + packet.data

            #################

            send_on_link(my_send_port, next_port, packet)

        except:
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


is_chat = False
my_id = None
my_name = ''
chat_ids = []
chat_dict = {}
app_fw = 'A'


def send_message_to_id(dst_id, message):
    # send message to dst_id
    pass


def send_message_to_group_of_ids(dst_ids, message):
    for id in dst_ids:
        if id in known_ids:
            send_message_to_id(id, message)


def handle_chat_receive(src_id, message):
    global chat_ids, chat_dict
    if re.match(r"CHAT: REQUESTS FOR STARTING WITH (\w+): (\w+)([, \w]*)", message) and not is_chat and app_fw == 'A':
        m = re.match(r"CHAT: REQUESTS FOR STARTING WITH (\w+): (\w+)([, \w]*)", message)
        cname = m[1]
        cid = m[2]
        ids = m[2] + m[3].split(", ")[1:]
        answer = input(f'{cname} with id {cid} has asked you to join a chat. Would you like to join?[Y/N]')
        if answer == 'Y':
            name = input("Choose a name for yourself")
            my_name = name
            chat_ids = ids
            message = f'CHAT: {my_id} :{name}'
            send_message_to_group_of_ids(ids, message)
        else:
            message = "CHAT: CANCLE"
            send_message_to_group_of_ids(ids, message)
    elif re.match(r'CHAT: (\w+) :(\w+)', message):
        m = re.match(r'CHAT: (\w+) :(\w+)', message)
        name = m[1]
        id = m[2]
        if id in chat_ids:
            chat_dict[id] = name
            print(f'{name}({id}) was joind to the chat.')
    elif message == "CHAT: CANCLE":
        try:
            chat_ids.remove(src_id)
        except:
            pass
    elif re.match("CHAT: EXIT CHAT (\w+)", message):
        m = re.match("CHAT: EXIT CHAT (\w+)", message)
        id = m[1]
        print(f'{chat_dict[id]}({id}) left the chat.')
        chat_ids.remove(id)
        chat_dict.pop(id)
    else:
        print(f'{chat_dict[src_id]}: {message[5:]}')


def chat_start(name, ids):
    if app_fw == 'D':
        print("Chat is disabled. Make sure the firewall allows you to chat.")
        return
    my_name = name
    i = 0
    while i < len(ids):
        if ids[i] in known_ids:
            i += 1
        else:
            ids.pop(i)
    is_chat = True
    chat_ids = ids
    message = f'CHAT: REQUESTS FOR STARTING WITH {my_name}: {my_id}'
    for id in ids:
        message += f', {id}'
    send_message_to_group_of_ids(ids, message)


def handle_salam(src_id):
    message = 'Hezaro Sisad Ta Salam'
    send_message_to_id(src_id, message)


if __name__ == '__main__':

    id = input("Please enter your id: ")
    my_id = id
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

    # while True:
    #     if not is_chat:
    #         comment = input("enter order:\n")
    #         if re.match(r'START CHAT (\w+): (\w+)([, \w]+)', comment):
    #             m = re.match(r'START CHAT (\w+): (\w+)([, \w]+)', comment)
    #             name = m[1]
    #             ids = m[2] + m[3].split(", ")[1:]
    #             chat_start(name, ids)
    #
    #         elif comment == 'FW CHAT DROP':
    #             app_fw = 'D'
    #         elif comment == 'FW CHAT ACCEPT':
    #             app_fw = 'A'
    #     else:
    #         message = input()
    #         if message == "EXIT CHAT":
    #             is_chat = False
    #             send_message_to_group_of_ids(chat_dict.keys, f'CHAT: EXIT CHAT {my_id}')
    #             chat_dict = {}
    #             chat_ids = []
    #
    #         else:
    #             send_message_to_group_of_ids(chat_dict.keys, f'{message}')
    #
## application
