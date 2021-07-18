import json
import socket
import threading
import re

from Packet import Packet, PacketEncoder
from setting import host, manager_port, get_listen_port, make_tcp_connection, make_link
import re

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

            if type == 0 and response['data'][:5] == 'CHAT:':
                handle_chat_recive(response['src_id'], response['data'])
            if type == 0 and response['data'] == 'Salam Salam Sad Ta Salam':
                handle_salam(response['src_id'])     
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

is_chat = False
my_id = None
my_name = ''
chat_ids = []
chat_dict = {}
if __name__ == '__main__':

    id = input("Please enter your id: ")
    my_id = id__
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

    while True:
        if not is_chat:
            comment = input("enter order:\n")
            if re.match(r'START CHAT (\w+): (\w+)([, \w]+)', comment):
                m = re.match(r'START CHAT (\w+): (\w+)([, \w]+)', comment)
                name = m[1]
                ids = m[2] + m[3].split(", ")[1:]
                chat_start(name, ids)
        else:
            message = input()
            send_message_to_group_of_ids(chat_dict.keys, f'{message}')
            
## application

def send_message_to_id(dst_id, message):
    #send message to dst_id
    pass

def send_message_to_group_of_ids(dst_ids, message):
    for id in dst_ids:
        if id in known_ids:
            send_message_to_id(id, message)

def handle_chat_recive(src_id, message):
    if re.match(r"CHAT: REQUESTS FOR STARTING WITH (\w+): (\w+)([, \w]*)", message):
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
    else :
        print(f'{chat_dict[src_id]}: {message[5:]}')
        

def chat_start(name, ids):
    my_name = name
    i = 0
    while i < len(ids):
        if ids[i] in known_ids:
            i+=1
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