import socket
import threading

HOST = '127.0.0.1'
PORT = 23000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))


def receive():
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            if message == 'username':
                client.send(username.encode('ascii'))

            print(message)
        except:
            client.close()
            break


def write():
    while True:
        message = f'{username}: {input("")}'
        client.send(message.encode('ascii'))


if __name__ == '__main__':
    username = input("Please enter your username: ")
    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    write_thread = threading.Thread(target=write)
    write_thread.start()
