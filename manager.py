import json
import socket
import threading

from constants import MANAGER_PORT, HOST

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, MANAGER_PORT))
server.listen()

clients = []
ids = []


def get_json_message(client):
    message = json.loads(client.recv(1024).decode('ascii'))
    return message


def get_text_message(client):
    message = client.recv(1024).decode('ascii')
    return message


def send_json_message(client, message):
    message = json.dumps(message).encode('ascii')
    client.send(message)


def send_text_message(client, message):
    message = message.encode('ascii')
    client.send(message)


def broadcast(message):
    for client in clients:
        send_json_message(client, message)


def handle(client):
    while True:
        try:
            message = get_json_message(client)
            print(message)
            broadcast(message)
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            # username = usernames[index]
            # usernames.remove(username)
            break


if __name__ == '__main__':
    while True:
        client, address = server.accept()
        clients.append(client)
        print(f'connected with {address}')

        message_parts = get_text_message(client).split(' ')
        id, listen_port = message_parts[0], message_parts[len(message_parts) - 1]

        print(id, listen_port)
        ids.append((id, listen_port))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()
