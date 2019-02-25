import json
import socket


class MyClient:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.name = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.activate()

    def activate(self):
        self.name.connect((self.ip, self.port))

    def send(self, msg):
        self.name.send(msg.encode('utf-8'))

    def send_dict(self, dic):
        self.name.send(json.dumps(dic).encode('utf-8'))

    def recv(self, bufsize=1024):
        return self.name.recv(bufsize).decode('utf-8')

    def my_recv(self, bufsize):
        return self.name.recv(bufsize)

    def my_send(self, msg):
        self.name.send(msg)


class MyServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.name = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind()

    def activate(self):
        self.name.listen(5)
        return self.name.accept()

    def bind(self):
        self.name.bind((self.ip, self.port))

    @staticmethod
    def get_dict(data):
        return json.loads(data.decode('utf-8'))
