import json
import socket
import threading

from setting import manager_port, host

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, manager_port))
server.listen()

clients = []
ids = []
listen_ports = []


def get_json_message(client):
    message = json.loads(client.recv(1024).decode('ascii'))
    return message


def send_message(client, message):
    message = json.dumps(message).encode('ascii')
    client.send(message)


def handle(client):
    while True:
        try:
            message = get_json_message(client)
            print(message)
        except:
            # index = clients.index(client)
            # clients.remove(client)
            # client.close()
            # username = usernames[index]
            # usernames.remove(username)
            break


if __name__ == '__main__':
    while True:
        client, address = server.accept()
        print(f'connected with {address}')

        message_parts = client.recv(1024).decode('ascii').split(' ')
        print(message_parts)
        id, listen_port = message_parts[0], message_parts[8]

        if len(clients) == 0:
            answer = f'CONNECT TO {-1} WITH PORT {-1}'
        else:
            answer = f'CONNECT TO {ids[(len(ids) - 1) // 2]} WITH PORT {listen_ports[(len(listen_ports) - 1) // 2]}'
        client.send(answer.encode('ascii'))

        clients.append(client)
        ids.append(id)
        listen_ports.append(listen_port)

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()
