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
    # Check for None
    if message == 'EXIT':
        return "EXIT"

    if message is None:
        raise ValueError("Message cannot be None")

    # Ensure message is a string
    if not isinstance(message, str):
        raise TypeError("Message must be a string")

    # Check for empty string
    if len(message) == 0:
        raise ValueError("Message cannot be empty")

    # Ensure message length fits in 4 digits (0-9999)
    if len(message) > 9999:
        raise ValueError("Message length exceeds 4-digit limit")

    message_length = len(message)
    return f"{message_length:04d}{message}".encode()