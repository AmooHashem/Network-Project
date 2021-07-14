import json
import socket
import threading
import re

PORT_NUMBER = 12245

from constants import MANAGER_PORT, HOST

MY_PORT_NUMBER = PORT_NUMBER
PORT_NUMBER += 1

sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receiver.bind((HOST, MY_PORT_NUMBER))
receiver.listen()


def get_json_message():
    message = json.loads(sender.recv(1024).decode('ascii'))
    return message


def get_text_message():
    message = sender.recv(1024).decode('ascii')
    return message


def send_json_message(message):
    message = json.dumps(message).encode('ascii')
    sender.send(message)


def send_text_message(message):
    message = message.encode('ascii')
    sender.send(message)


def receive():
    while True:
        try:
            message = get_json_message()
            print(message)
            if message == 'username':
                sender.send(id.encode('ascii'))
        except:
            sender.close()
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
    # while input() != "CONNECT TO MANAGER":
    #     pass
    sender.connect((HOST, MANAGER_PORT))
    send_text_message(f"{id} REQUESTS FOR CONNECTING TO NETWORK ON PORT {MY_PORT_NUMBER}")

    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    write_thread = threading.Thread(target=write)
    write_thread.start()
