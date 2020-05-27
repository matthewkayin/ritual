import threading
import socket
import time


client_socket = None
client_server_ip = None
client_server_port = None


def client_connect(server_ip, server_port):
    global client_socket, client_server_ip, client_server_port

    client_server_ip = server_ip
    client_server_port = server_port

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(0.001)
    client_socket.sendto("c".encode(), (server_ip, server_port))


def client_read_server():
    global client_socket

    try:
        received_data = client_socket.recvfrom(32)
        if received_data:
            message, address = received_data
            message = message.decode()
            if len(message) >= 1:
                command = message[0]
                if command == "h":
                    print("server tick")
    except socket.error:
        return


def client_disconnect():
    global client_socket, client_server_ip, client_server_port

    client_socket.sendto("d".encode(), (client_server_ip, client_server_port))
    client_socket.close()


# Server-side Code
client_threads = {}
client_thread_flags = {}


def server_thread_main(server_port):
    global client_threads, client_thread_flags

    listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listener.settimeout(1.0)
    listener.bind(("127.0.0.1", server_port))

    print("Server started.")
    while True:
        try:
            received_data = listener.recvfrom(32)
            if received_data:
                message, address = received_data
                message = message.decode()
                if len(message) >= 1:
                    command = message[0]
                    if command == "c":
                        client_threads[address] = threading.Thread(target=server_thread_client, args=(address,))
                        client_thread_flags[address] = True
                        client_threads[address].start()
                    elif command == "d":
                        client_thread_flags[address] = False
        except socket.error:
            continue
        addresses_to_clear = []
        for address in client_threads.keys():
            if not client_threads[address].is_alive():
                addresses_to_clear.append(address)
        for address in addresses_to_clear:
            del client_threads[address]
            del client_thread_flags[address]
    listener.close()


def server_thread_client(address):
    global client_thread_flags

    print("Connected new client at " + str(address[0]) + ":" + str(address[1]))
    sending_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while client_thread_flags[address]:
        sending_socket.sendto("h".encode(), address)
        time.sleep(1.0)
    print("Disconnected client at " + str(address[0]) + ":" + str(address[1]))
    sending_socket.close()


if __name__ == "__main__":
    server_thread = threading.Thread(target=server_thread_main, args=(3535,))
    server_thread.start()
    server_thread.join()
