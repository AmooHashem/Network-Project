import re


MANAGER_PORT = 11113
PORT_NUMBER = 12245
HOST = '127.0.0.1'
NODE_ID = 1



if __name__ == '__main__':
    txt = "The rain in Spaindfvbgfdefv"
    x = re.search("The rain in (S\w+)", txt)
    print(x.group())
