import socket
import select
import protocol

SERVER_PORT = 8888
SERVER_IP = "0.0.0.0"

block_list = {}
messages_to_send = []


def block(blocker, blockee):
    """
    Adds 'blockee' to the block list of 'blocker'.
    """
    # If the blocker is not in the block list, initialize an empty list
    if blocker not in block_list:
        block_list[blocker] = []
    # Add the blockee to the blocker's list
    if blockee not in block_list[blocker]:
        block_list[blocker].append(blockee)



# Function to check if a sender has blocked a sendee
def blockCheck(sender, sendee):
    """
    Checks if 'sender' has blocked 'sendee'.
    """
    # Check if the sender has a block list and if the sendee is in it
    if sender in block_list and sendee in block_list[sender]:
        return 1
    else:
        return 0


def handle_client_request(current_socket, clients_names, data,):
    # Strip any leading/trailing whitespace
    data = data.strip()

    # Handle empty messages
    if not data:
        return "ERROR: Empty command", current_socket

    command = data.split(' ')[0]

    if command == "NAME":
        # Ensure name is provided
        if len(data.split(' ')) < 2:
            return "ERROR: Name not specified", current_socket

        name = data.split(' ')[1]

        # Check for empty name
        if not name:
            return "ERROR: Name cannot be empty", current_socket

        # Check for duplicate names
        if name in clients_names.values():
            return "ERROR: Name already in use", current_socket

        if name == 'BROADCAST':
            return "ERROR: Name CANT be equal to broadcast", current_socket

        clients_names[current_socket] = name
        return f"HELLO {name}", current_socket

    elif command == "GET_NAMES":
        # Ensure at least one client is named
        if not clients_names:
            return "No clients connected", current_socket

        names = ", ".join(clients_names.values())
        return names, current_socket


    elif command == "MSG" and len(data.split(' ')) > 2:

        parts = data.split(' ', 2)

        target_name = parts[1]

        message = parts[2]

        # Check if sender has a name

        if current_socket not in clients_names:
            return "ERROR: Set your name first", current_socket

        sender_name = clients_names[current_socket]

        if target_name == "broadcast":

            for sock, name in clients_names.items():

                # Skip sender

                if sock == current_socket:
                    continue

                # Check if the recipient has blocked the sender

                if sender_name in block_list.get(name, []):
                    continue

                # Add the message to be sent to this recipient

                messages_to_send.append((sock, f"{sender_name} broadcasted: {message}"))

            return "Message broadcasted to all unblocked clients", current_socket

        # Handle regular direct messaging (MSG <name> <message>)

        # Find recipient socket
        recipient_socket = None
        for sock, name in clients_names.items():
            if name == target_name:
                recipient_socket = sock
                break

        # Check if recipient exists
        if not recipient_socket:
            return "ERROR: Recipient not found", current_socket

        # Check blocking
        sender_name = clients_names[current_socket]
        if blockCheck(target_name, sender_name):
            return "ERROR: You are blocked by the recipient", current_socket

        return f"{sender_name} sent: {message}", recipient_socket

    elif command == "BLOCK":
        # Ensure block command has a name
        if len(data.split(' ')) < 2:
            return "ERROR: Specify who to block", current_socket

        blockee = data.split(' ')[1]

        # Check if sender has a name
        if current_socket not in clients_names:
            return "ERROR: Set your name first", current_socket

        sender_name = clients_names[current_socket]

        # Prevent blocking self
        if sender_name == blockee:
            return "ERROR: Cannot block yourself", current_socket

        # Ensure blockee exists
        if blockee not in clients_names.values():
            return "ERROR: User to block not found", current_socket

        block(sender_name, blockee)
        return "User blocked", current_socket

    elif command == "EXIT":
        # Remove the client's name from clients_names
        if current_socket in clients_names:
            del clients_names[current_socket]
        return "", None  # Signal to close the connection

    else:
        return "ERROR: Unknown command", current_socket


def print_client_sockets(client_sockets):
    for c in client_sockets:
        print("\t", c.getpeername())


def main():
    print("Setting up server")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    print("Listening for clients")
    server_socket.listen()
    client_sockets = []
    clients_names = {}
    while True:
        read_list = client_sockets + [server_socket]
        ready_to_read, ready_to_write, in_error = select.select(read_list, client_sockets, [])
        for current_socket in ready_to_read:
            if current_socket is server_socket:
                client_socket, client_address = server_socket.accept()
                print("Client joined!\n", client_address)
                client_sockets.append(client_socket)
                print_client_sockets(client_sockets)
            else:
                try:
                    print("Data from client\n")
                    data = protocol.get_message(current_socket)
                    if data == "":
                        # Handle client disconnection
                        print("Connection closed by client\n")
                        if current_socket in clients_names:
                            del clients_names[current_socket]
                        client_sockets.remove(current_socket)
                        current_socket.close()
                    else:
                        print(data)
                        (response, dest_socket) = handle_client_request(current_socket, clients_names, data)

                        # Handle graceful disconnection
                        if dest_socket is None:
                            if current_socket in client_sockets:
                                client_sockets.remove(current_socket)
                            current_socket.close()
                            continue

                        messages_to_send.append((dest_socket, response))
                except (ConnectionResetError, ConnectionAbortedError):
                    # Handle forceful disconnection
                    print("Client forcefully disconnected\n")
                    if current_socket in clients_names:
                        del clients_names[current_socket]
                    if current_socket in client_sockets:
                        client_sockets.remove(current_socket)
                    current_socket.close()
                except Exception as e:
                    print(f"Unexpected error: {e}")

        # write to everyone (note: only ones which are free to read...)
        for message in messages_to_send:
            current_socket, data = message
            if current_socket in ready_to_write:
                response = protocol.create_msg(data)
                current_socket.send(response)
                messages_to_send.remove(message)


if __name__ == '__main__':
    main()