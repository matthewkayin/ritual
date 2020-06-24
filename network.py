import socket
import select


SERVER_EVENT_NEW_PLAYER = 0
SERVER_EVENT_PLAYER_INPUT = 1

server_game_started = False

server_listener = None
server_ip = "127.0.0.1"
server_username = ""
server_last_pings_at_once = 0
server_event_queue = []
server_client_read_buffer = {}
server_client_usernames = {}
server_client_inputs_received = {}
server_client_ping = {}


def server_begin(port):
    global server_listener, server_ip

    server_finder = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        server_finder.connect(('10.255.255.255', 1))
        server_ip = server_finder.getsockname()[0]
    except Exception:
        server_ip = "127.0.0.1"
    finally:
        server_finder.close()

    server_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_listener.bind((server_ip, port))


def server_set_username(username):
    global server_username
    server_username = username


def server_start_game():
    global server_game_started

    server_game_started = True
    for address in server_client_read_buffer.keys():
        server_listener.sendto("s".encode(), address)


def server_read():
    global server_listener, server_event_queue, server_client_read_buffer

    # Read from socket and fill player buffers
    readable, writable, exceptionable = select.select([server_listener], [], [], 0.001)
    for ready_socket in readable:
        message, address = ready_socket.recvfrom(1024)
        message = message.decode()
        if address in server_client_read_buffer.keys():
            if server_game_started:
                server_client_read_buffer[address] += message
            else:
                if message.startswith("u="):
                    server_client_usernames[address] = message[message.index("=") + 1:]
                server_client_ping[address] = True
        else:
            if message == "c":
                if not server_game_started and len(server_client_read_buffer.keys()) < 9:
                    response = "u?"
                    server_listener.sendto(response.encode(), address)
            elif message.startswith("u="):
                next_player_index = len(server_client_read_buffer.keys()) + 1
                response = "welc" + str(next_player_index) + "\n"
                server_listener.sendto(response.encode(), address)
                server_client_usernames[address] = message[message.index("=") + 1:]
                server_client_inputs_received[address] = 0
                server_client_read_buffer[address] = ""
                server_client_ping[address] = False

    # Read from player buffers
    current_player_index = 1
    for address in server_client_read_buffer.keys():
        while "\n" in server_client_read_buffer[address]:
            terminator_index = server_client_read_buffer[address].index("\n")
            command = server_client_read_buffer[address][:terminator_index]
            server_client_read_buffer[address] = server_client_read_buffer[address][terminator_index + 1:]

            if command == "e" or command == "r":
                continue

            if int(command[0]) == 1:
                server_client_ping[address] = True
            command = command[command.index("#") + 1:]

            if len(command) == 0:
                continue

            command_inputs = command.split("&")
            for command_input in command_inputs:
                input_items = command_input.split(",")
                if len(input_items) == 2:
                    input_items = [int(part) for part in input_items]
                else:
                    input_items = [int(input_items[0]), int(input_items[1]), (int(input_items[2]), int(input_items[3]))]
                server_event_queue.append([SERVER_EVENT_PLAYER_INPUT, current_player_index, input_items])
                server_client_inputs_received[address] += 1
        current_player_index += 1


def server_write(state_data):
    global server_listener, server_client_read_buffer, server_last_pings_at_once

    packet_length = 3 + len(state_data)

    server_last_pings_at_once = sum(server_client_ping.values())
    for address in server_client_read_buffer.keys():
        if server_client_ping[address]:
            out_string = int(packet_length).to_bytes(2, "little", signed=False) + int(server_client_inputs_received[address]).to_bytes(1, "little", signed=False) + state_data
            server_client_inputs_received[address] = 0
            server_listener.sendto(out_string, address)
            server_client_ping[address] = False


def server_lobby_write():
    usernames_string = "u=" + server_username
    for address in server_client_read_buffer.keys():
        usernames_string += "," + server_client_usernames[address]
    usernames_string += "\n"

    for address in server_client_read_buffer.keys():
        if server_client_ping[address]:
            server_listener.sendto(usernames_string.encode(), address)
            server_client_ping[address] = False


def server_check_clients_ready():
    readable, writable, exceptionable = select.select([server_listener], [], [], 0.001)
    for ready_socket in readable:
        message, address = ready_socket.recvfrom(1024)
        message = message.decode()
        if address in server_client_read_buffer.keys():
            if message == "r\n":
                server_client_ping[address] = True

    return not (False in server_client_ping.values())


def server_send_all_ready():
    for address in server_client_read_buffer.keys():
        server_client_ping[address] = False
        server_listener.sendto("r\n".encode(), address)


client_socket = None
client_server_address = None
client_connected = False
client_server_buffer = ""
client_event_queue = []
client_received_inputs = 0


def client_connect(server_ip, server_port):
    global client_socket, client_server_address

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_server_address = (server_ip, server_port)
    client_socket.sendto("c".encode(), client_server_address)


def client_check_response():
    readable, writable, exceptionable = select.select([client_socket], [], [], 0.001)
    for ready_socket in readable:
        message, address = ready_socket.recvfrom(1024)
        message = message.decode()
        if message.startswith("u?"):
            return 1
        elif message.startswith("welc"):
            return int(message[message.index("c") + 1:message.index("\n")])

    return 0


def client_send_username(username):
    username_packet = "u=" + username
    client_socket.sendto(username_packet.encode(), client_server_address)


def client_read():
    global client_socket, client_connected, client_server_buffer, client_received_inputs

    return_data = []

    readable, writable, exceptionalbe = select.select([client_socket], [], [], 0.001)
    for ready_socket in readable:
        message, address = ready_socket.recvfrom(1024)
        client_server_buffer += message

    while len(client_server_buffer) != 0:
        next_packet_header = client_server_buffer[0:2]
        next_packet_length = int.from_bytes(next_packet_header, "little", signed=False)
        if len(client_server_buffer) < next_packet_length:
            break

        next_packet = client_server_buffer[2:next_packet_length]
        client_server_buffer = client_server_buffer[next_packet_length:]

        client_received_inputs += int.from_bytes(next_packet[0:1], "little", signed=False)
        return_data.append(next_packet[1:])

    return return_data


def client_write(ping_server):
    global client_socket, client_server_address, client_event_queue

    command = str(int(ping_server)) + "#"
    while len(client_event_queue) != 0:
        client_event = client_event_queue.pop(0)

        mouse_pos_string = ""
        if len(client_event) > 2:
            mouse_pos_string = "," + str(client_event[2][0]) + "," + str(client_event[2][1])

        if "," in command:
            command += "&"
        command += str(int(client_event[0])) + "," + str(client_event[1]) + mouse_pos_string
    command += "\n"

    client_socket.sendto(command.encode(), client_server_address)


def client_lobby_write():
    client_socket.sendto("e\n".encode(), client_server_address)


def client_lobby_read():
    global client_server_buffer

    readable, writable, exceptable = select.select([client_socket], [], [], 0.001)
    for ready_socket in readable:
        message, address = ready_socket.recvfrom(1024)
        message = message.decode()
        if message.startswith("s"):
            client_server_buffer = ""
            return "start"
        else:
            client_server_buffer += message

    if "\n" in client_server_buffer:
        message = client_server_buffer[message.index("=") + 1:message.index("\n")]
        client_server_buffer = client_server_buffer[client_server_buffer.index("\n") + 1:]
        player_usernames = message.split(",")
        return player_usernames

    return []


def client_send_ready():
    client_socket.sendto("r\n".encode(), client_server_address)


def client_check_server_ready():
    global client_server_buffer

    readable, writable, exceptionable = select.select([client_socket], [], [], 0.001)
    for ready_socket in readable:
        message, address = ready_socket.recvfrom(1024)
        message = message.decode()
        if message == "r\n":
            # now that we're receiving state data we'll want to switch the data type of the buffer
            client_server_buffer = "".encode()
            return True

    return False
