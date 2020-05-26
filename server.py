import socket

ip = "127.0.0.1"
port = 3535
listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
listener.bind((ip, port))

players = {}


if __name__ == "__main__":
    print("Server started.")
    while True:
        received_data = listener.recvfrom(32)
        if received_data:
            message, address = received_data
            message = message.decode()
            if len(message) >= 1:
                command = message[0]
                if command == "c":
                    print(str(address[0]) + " connected.")
                    players[address] = 1
                elif command == "d":
                    print(str(address[0]) + " disconnect.")
                    del players[address]
                elif command == "g":
                    listener.sendto("h".encode(), address)
        print("skips")
        for player_address in players.keys():
            listener.sendto("h".encode(), player_address)
