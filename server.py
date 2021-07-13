import socket
import threading

HOST = '127.0.0.1'
PORT = 23000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []
usernames = []


def broadcast(message):
    for client in clients:
        client.send(message)


def handle(client):
    while True:
        try:
            message = client.recv(1024)
            print(message.decode('ascii'))
            broadcast(message)
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            username = usernames[index]
            usernames.remove(username)
            break


if __name__ == '__main__':
    while True:
        client, address = server.accept()
        print(f'connected with {address}')

        client.send("username".encode('ascii'))
        username = client.recv(1024).decode('ascii')
        usernames.append(username)
        clients.append(client)

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()
