def get_message(socket):
    # Step 1: Read the 4-byte length prefix
    length_data = socket.recv(4)
    if not length_data:
        return ""
    message_length = int(length_data.decode())  # Convert to an integer

    # Step 2: Read the actual message
    data = socket.recv(message_length).decode()
    return data

def create_msg(message):

    message_length = len(message)  # Calculate the message length
    return f"{message_length:04d}{message}".encode()  # Prefix with 4-digit length