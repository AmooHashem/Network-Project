import json
import socket
import threading
import re

from Filter import Filter
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
filters = []


def get_message(client):
    message = json.loads(client.recv(1024).decode('ascii'))
    return Packet(int(message['type']), int(message['src_id']), int(message['dst_id']), message['data'])


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


def does_filter_apply_on_packet(packet: Packet, filter: Filter):
    if filter.type != str(packet.type): return False
    if (filter.direction == 'INPUT' or filter.direction == 'FORWARD') and \
            (str(packet.src_id) == filter.src_id or filter.src_id == '*'):
        return True
    if (filter.direction == 'OUTPUT' or filter.direction == 'FORWARD') and \
            (str(packet.dst_id) == filter.dst_id or filter.dst_id == '*'):
        return True
    return False


def receive():
    global left_child_id, left_child_port, right_child_id, right_child_port
    while True:
        try:
            client, address = receive_socket.accept()
            sender_port = address[1]
            packet = get_message(client)
            type = packet.type
            src_id = packet.src_id
            dst_id = packet.dst_id
            data = packet.data
            # print("new packet", type, src_id, dst_id, data)

            #################

            can_pass = True
            for filter in filters:
                print(filter)
                if does_filter_apply_on_packet(packet, filter):
                    if filter.action == 'ACCEPT':
                        can_pass &= True
                    else:
                        can_pass &= False

            if not can_pass:
                continue

            #################

            if type == 41:
                chile_port = data
                child_id = src_id
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
                known_ids.append(int(src_id))
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
                if type == 21:
                    if data not in known_ids:
                        known_ids.append(int(data))
                if type == 0 and data[:5] == 'CHAT:':
                    handle_chat_receive(src_id, data)
                if type == 0 and data == 'Salam Salam Sad Ta Salam':
                    handle_salam(src_id)
                    print(f'{src_id}: {data}')
                if type == 0 and data == 'Hezaro Sisad Ta Salam':
                    print(f'{src_id}: {data}')
                continue

            #################

            if dst_id == -1:
                if type == 21:
                    if data not in known_ids:
                        known_ids.append(int(data))

                sender_receive_port = address[1] - 1
                if parent_port != -1 and parent_port != sender_receive_port:
                    send_on_link(my_send_port, parent_port, packet)

                if left_child_port != -1 and left_child_port != sender_receive_port:
                    send_on_link(my_send_port, left_child_port, packet)

                if right_child_port != -1 and right_child_port != sender_receive_port:
                    send_on_link(my_send_port, right_child_port, packet)
                continue

            #################

            next_port = find_next_port(dst_id)
            if next_port == -1:
                next_port = find_next_port(src_id)
                send_on_link(my_send_port, next_port, Packet(31, id, src_id, f'DESTINATION {dst_id} NOT FOUND'))
                continue

            #################

            if type == 11:
                packet.data = ('<-' + id if next_port == parent_id else '->' + id) + packet.data

            #################

            send_on_link(my_send_port, next_port, packet)

        except:
            break


is_chat = False
my_id = None
my_name = ''
chat_ids = []
chat_dict = {}
app_fw = 'A'

global_command = ''
chat_input = False


def send_message_to_id(dst_id, message):
    global known_ids, my_id
    if dst_id not in known_ids:
        print(f'Unknown destination {dst_id}')
        return
    next_port = find_next_port(dst_id)
    if next_port == -1:
        print(f'DESTINATION {dst_id} NOT FOUND')
        return
    send_on_link(my_send_port, next_port, Packet(0, my_id, dst_id, message))
    print(dst_id, message, "sent!")


def send_message_to_group_of_ids(dst_ids, message):
    for id in dst_ids:
        if id in known_ids:
            send_message_to_id(id, message)


def handle_chat_receive(src_id, message):
    global is_chat, my_id, my_name, chat_dict, chat_ids, app_fw, chat_input, global_command
    print("chat", src_id, message, "resive!")
    if re.match(r"CHAT: REQUESTS FOR STARTING WITH (\w+): (\w+)([, \w]*)", message) and not is_chat and app_fw == 'A':
        print("!1")
        m = re.match(r"CHAT: REQUESTS FOR STARTING WITH (\w+): (\w+)([, \w]*)", message)
        cname = m[1]
        cid = m[2]
        ids = [m[2]] + m[3].split(", ")[1:]
        print(f'{cname} with id {cid} has asked you to join a chat. Would you like to join?[Y/N]')
        chat_input = True
        while chat_input:
            # can be better impelement!
            pass
        answer = global_command
        if answer == 'Y':
            chat_dict[cid] = cname
            print("Choose a name for yourself")
            chat_input = True
            while chat_input:
                # can be better impelement!
                pass
            name = global_command
            my_name = name
            chat_ids = ids
            is_chat = True
            message = f'CHAT: {my_id} :{name}'
            send_message_to_group_of_ids(ids, message)
        else:
            message = "CHAT: CANCLE"
            send_message_to_group_of_ids(ids, message)
    elif re.match(r'CHAT: (\w+) :(\w+)', message):
        print("!2")
        m = re.match(r'CHAT: (\w+) :(\w+)', message)
        name = m[2]
        id = m[1]
        if id in chat_ids:
            chat_dict[id] = name
            print(f'{name}({id}) was joind to the chat.')
    elif message == "CHAT: CANCLE":
        print("!3")
        try:
            chat_ids.remove(src_id)
        except:
            pass
    elif re.match("CHAT: EXIT CHAT (\w+)", message):
        print("!4")
        m = re.match("CHAT: EXIT CHAT (\w+)", message)
        id = m[1]
        print(f'{chat_dict[id]}({id}) left the chat.')
        chat_ids.remove(id)
        chat_dict.pop(id)
    else:
        print("!5")
        print(chat_dict, src_id, message)
        print(f'{chat_dict[src_id]}: {message[5:]}')


def chat_start(name, ids):
    global is_chat, my_id, my_name, chat_dict, chat_ids, app_fw
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
    print("salam", src_id, "resive!")
    message = 'Hezaro Sisad Ta Salam'
    send_message_to_id(src_id, message)


def write():
    global is_chat, my_id, my_name, chat_dict, chat_ids, app_fw, chat_input, global_command
    while True:
        if not is_chat:
            command = input("enter command:\n")
            command_parts = command.split(' ')

            if chat_input:
                global_command = command
                chat_input = False
                continue

            if command == 'SHOW KNOWN CLIENTS':
                print(known_ids)

            if command_parts[0] == 'ROUTE':
                dst_id = int(command_parts[1])
                if dst_id not in known_ids:
                    print(f'Unknown destination {dst_id}')
                    continue
                next_port = find_next_port(dst_id)
                if next_port == -1:
                    print(f'DESTINATION {dst_id} NOT FOUND')
                    continue
                send_on_link(my_send_port, next_port, Packet(10, id, dst_id, ''))

            if command_parts[0] == 'ADVERTISE':
                dst_id = int(command_parts[1])
                if dst_id not in known_ids and dst_id != -1:
                    print(f'Unknown destination {dst_id}')
                    continue
                if dst_id != -1:
                    next_port = find_next_port(dst_id)
                    print(dst_id, next_port)
                    send_on_link(my_send_port, next_port, Packet(21, id, dst_id, id))
                else:
                    print("SDERGFBDFRGTBFDS")
                    if parent_port != -1:
                        send_on_link(my_send_port, parent_port, Packet(21, id, -1, id))
                    if left_child_port != -1:
                        send_on_link(my_send_port, left_child_port, Packet(21, id, -1, id))
                    if right_child_port != -1:
                        send_on_link(my_send_port, right_child_port, Packet(21, id, -1, id))

            if command_parts[0] == 'FILTER':
                filters.append \
                    (Filter(command_parts[1], command_parts[2], command_parts[3], command_parts[4], command_parts[5]))

            if re.match(r'START CHAT (\w+): (\w+)([, \w]*)', command):
                m = re.match(r'START CHAT (\w+): (\w+)([, \w]*)', command)
                name = m[1]
                ids = [m[2]] + m[3].split(", ")[1:]

                print(m[3], ids)
                chat_start(name, ids)

            elif command == 'FW CHAT DROP':
                app_fw = 'D'
            elif command == 'FW CHAT ACCEPT':
                app_fw = 'A'
            elif re.match("SALAM TO (\w+)", command):
                m = re.match("SALAM TO (\w+)", command)
                send_message_to_id(m[1], "Salam Salam Sad Ta Salam")

        else:
            message = input()
            if message == "EXIT CHAT":
                is_chat = False
                send_message_to_group_of_ids(list(chat_dict.keys()), f'CHAT: EXIT CHAT {my_id}')
                chat_dict = {}
                chat_ids = []

            else:
                send_message_to_group_of_ids(list(chat_dict.keys()), f'CHAT: {message}')


if __name__ == '__main__':
    id = input("Please enter your id: ")
    my_id = id
    manager_link = make_link(my_send_port, manager_port)
    manager_link.send(f"{id} REQUESTS FOR CONNECTING TO NETWORK ON PORT {my_listen_port}".encode('ascii'))
    message_parts = manager_link.recv(1024).decode('ascii').split(' ')
    parent_id, parent_port = message_parts[2], int(message_parts[5])
    known_ids.append(int(parent_id))

    if parent_id != '-1':
        send_on_link(my_send_port, parent_port, Packet(41, id, parent_id, my_listen_port))
        send_on_link(my_send_port, parent_port, Packet(20, id, parent_id, id))

    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    write_thread = threading.Thread(target=write)
    write_thread.start()
