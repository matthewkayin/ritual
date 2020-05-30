import socket
import select

SERVER_EVENT_NEW_PLAYER = 0
SERVER_EVENT_PLAYER_INPUT = 1

server_listener = None
server_event_queue = []
server_client_read_buffer = {}


def server_begin(port):
    global server_listener

    server_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_listener.bind(("127.0.0.1", port))


def server_read():
    global server_listener, server_event_queue, server_client_read_buffer

    # Read from socket and fill player buffers
    readable, writable, exceptionable = select.select([server_listener], [], [], 0.001)
    for ready_socket in readable:
        message, address = ready_socket.recvfrom(1024)
        if address in list(server_client_read_buffer.keys()):
            server_client_read_buffer[address] += message.decode()
        else:
            next_player_index = len(server_client_read_buffer.keys()) + 1
            server_client_read_buffer[address] = ""
            server_event_queue.append([SERVER_EVENT_NEW_PLAYER])
            response = "ack," + str(next_player_index) + "\n"
            server_listener.sendto(response.encode(), address)

    # Read from player buffers
    current_player_index = 1
    for address in server_client_read_buffer.keys():
        while "\n" in server_client_read_buffer[address]:
            terminator_index = server_client_read_buffer[address].index("\n")
            command = server_client_read_buffer[address][:terminator_index]
            server_client_read_buffer[address] = server_client_read_buffer[address][terminator_index + 1:]

            command = command.split(",")
            command_items = [int(part) for part in command]
            server_event_queue.append([SERVER_EVENT_PLAYER_INPUT, current_player_index, command_items])
        current_player_index += 1


def server_write(state_data):
    global server_listener, server_client_read_buffer

    state_string = ""
    for player in state_data:
        if state_string != "":
            state_string += "&"
        player_string = ""
        for value in player:
            if player_string != "":
                player_string += ","
            player_string += str(value)
        state_string += player_string
    state_string += "\n"

    for address in server_client_read_buffer.keys():
        server_listener.sendto(state_string.encode(), address)


client_socket = None
client_server_address = None
client_connected = False
client_server_buffer = ""
client_event_queue = []


def client_connect(server_ip, server_port):
    global client_socket, client_server_address

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_server_address = (server_ip, server_port)
    client_socket.sendto("c".encode(), client_server_address)


def client_read():
    global client_socket, client_connected, client_server_buffer

    return_data = []

    readable, writable, exceptionalbe = select.select([client_socket], [], [], 0.001)
    for ready_socket in readable:
        message, address = ready_socket.recvfrom(1024)
        client_server_buffer += message.decode()

    while "\n" in client_server_buffer:
        terminator_index = client_server_buffer.index("\n")
        command = client_server_buffer[:terminator_index]
        client_server_buffer = client_server_buffer[terminator_index + 1:]

        if command.startswith("ack"):
            client_connected = True
            command_values = command.split(",")
            return_data.append([command_values[0], int(command_values[1])])
        else:
            return_data_entry = []
            command_parts = command.split("&")
            for part in command_parts:
                command_values = part.split(",")
                return_data_entry.append(command_values)
            return_data.append(return_data_entry)

    return return_data


def client_write():
    global client_socket, client_server_address, client_event_queue

    while len(client_event_queue) != 0:
        client_event = client_event_queue.pop(0)
        command = str(int(client_event[0])) + "," + str(client_event[1]) + "\n"
        client_socket.sendto(command.encode(), client_server_address)
