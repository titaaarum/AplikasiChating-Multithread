import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(5)
print("Server listening on {}:{}".format(HOST, PORT))

# Dictionary to store usernames, group names, and client sockets
clients = {}
lock = threading.Lock()


def handle_client(client_socket, client_address):
    try:
        # Minta username dan groupname dari klien
        client_socket.send("Enter your username: ".encode("utf-8"))
        username = client_socket.recv(1024).decode("utf-8").strip()

        # Ask for group name from the client
        client_socket.send("Enter your group name: ".encode("utf-8"))
        groupname = client_socket.recv(1024).decode("utf-8").strip()

        print("User {} from group {} connected from {}:{}".format(username, groupname, client_address[0], client_address[1]))

        with lock:
            clients[username] = (client_socket, groupname)  # Store both username and groupname as a tuple

        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            # Check if server wants to close
            if data.decode("utf-8").lower() == "exit":
                raise KeyboardInterrupt  # Raise an exception to close the server
            elif data.decode("utf-8").startswith("$"):
                # Group message: forward the message to all clients in the same group
                parts = data.decode("utf-8").split(" ", 1)
                recipient_group = parts[0][1:]
                message = parts[1]
                if recipient_group == groupname:
                    message = "[Group {} from {}] {}".format(groupname, username, message)
                    with lock:
                        for client, client_group in clients.values():
                            if client_group == groupname:
                                client.send(message.encode("utf-8"))
                else:
                    # Broadcast to all clients from different groups
                    message = "[Group {} Broadcast from {}] {}".format(groupname, username, message)
                    with lock:
                        for client, client_group in clients.values():
                            if client_group != groupname:
                                client.send(message.encode("utf-8"))
            elif data.decode("utf-8").startswith("@"):
                # Unicast: forward the message to the specified user
                parts = data.decode("utf-8").split(" ", 1)
                recipient = parts[0][1:]
                message = parts[1]
                if recipient in clients:
                    recipient_socket, _ = clients[recipient]
                    message = "[Unicast from {}] {}".format(username, message)
                    recipient_socket.send(message.encode("utf-8"))
            elif data.decode("utf-8").startswith("*Broadcast"):
                # Broadcast to all clients from different groups
                message = "[Broadcast from {}] {}".format(username, data.decode("utf-8")[10:])  # Remove "*Broadcast" from the message
                with lock:
                    for client, client_group in clients.values():
                        client.send(message.encode("utf-8"))
            elif data.decode("utf-8").startswith("!file"):
                    parts = data.decode("utf-8").split(" ", 2)
                    file_type = parts[1]
                    file_size = int(parts[2])
                    filename = f"{username}_.{file_type}"
                    with open(filename, "wb") as file:
                        remaining_bytes = file_size
                        while remaining_bytes > 0:
                            file_data = client_socket.recv(min(remaining_bytes, 1024))
                            if not file_data:
                                break
                            file.write(file_data)
                            remaining_bytes -= len(file_data)
                    print(f"Received file {filename} from {username}")
            elif data.decode("utf-8").startswith("!send"):
                parts = data.decode("utf-8").split(" ", 3)
                target_username = parts[1]
                file_path = parts[2]
                # ... (rest of the code)

                # Create the full message
                full_message = f"!send {target_username} {file_path}"

                # Send the message through the socket
                client_socket.send(full_message.encode("utf-8"))

                    
            elif data.decode("utf-8").startswith("@file"):
                parts = data.decode("utf-8").split(" ", 3)
                recipient, file_name, file_size = parts[1], parts[2], int(parts[3])
                if recipient in clients:
                    file_data(clients[recipient], username, file_name, file_size)

                    
            else:
                pass

    except KeyboardInterrupt:
        print("Server is closing...")
    except:
        pass
    finally:
        # If the connection is lost, close the client socket and remove from the list
        with lock:
            if username in clients:
                del clients[username]
        client_socket.close()


def main():
    try:
        while True:
            client_socket, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_thread.start()
    except KeyboardInterrupt:
        print("Closing all connections...")
        with lock:
            for client, _ in clients.values():
                client.close()

    server_socket.close()
    print("Server is closed.")


if __name__ == "__main__":
    main()


