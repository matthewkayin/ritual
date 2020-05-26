import threading
import socket


class GameClient(threading.Thread):
    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        self.connected = False
        self.ticks = 0
        self.server_ip = ip
        self.server_port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self):
        self.socket.sendto("c".encode(), (self.server_ip, self.server_port))
        self.connected = True
        while self.connected:
            received_data = self.socket.recvfrom(32)
            if received_data:
                message, address = received_data
                message = message.decode()
                if len(message) >= 1:
                    command = message[0]
                    if command == "h":
                        self.ticks += 1
                        print("server ticks " + str(self.ticks))
        self.socket.sendto("d".encode(), (self.server_ip, self.server_port))

    def disconnect(self):
        self.connected = False
