import socket

import select
import msvcrt
import protocol
from protocol import create_msg

# NAME <name> will set name. Server will reply error if duplicate
# GET_NAMES will get all names
# MSG <NAME> <message> will send message to client name or to broadcast
# BLOCK <name> will block a user from sending messages to the client who sent the block command
# EXIT will close client

# keyboard key that represents the end of message
END_MSG = '\r'
SPECIAL_KEYS = [b'\xe0', b'\x00']
BACKSPACE = '\x08'

my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
my_socket.connect(("127.0.0.1", 8888))
print("Enter commands\n")
msg = ""
while msg != "EXIT":
    rlist, wlist, xlist = select.select([my_socket], [], [], 0.2)
    if rlist:
        response = protocol.get_message(rlist[0])
        # print response sent by server, new line in case the destination user was typing
        print(f"\nServer sent: {response}")
    if msvcrt.kbhit():
        # get the character that was pressed
        ch = msvcrt.getch()
        # if the key pressed is a special key we'll catch it's prefix and ignore the following key
        # special key functionality could be added in the future
        if ch in SPECIAL_KEYS:
            msvcrt.getch()
            continue
        # decode the char now that we know it isn't a special key, make sure we can decode it
        try:
            ch = ch.decode()
        except UnicodeDecodeError:
            continue
        # check if the character is what's defined as the send button
        if ch == END_MSG:
            # we'll ignore the case of sending nothing
            if msg:
                # send message
                my_socket.send(protocol.create_msg(msg))
                # new line
                print()
                # clear message
                msg = ""
        elif ch == BACKSPACE:
            if msg:
                msg = msg[:-1]
                print('\b \b', end="", flush=True)
        else:
            # print each letter as it's typed so user can keep track of what he's typing
            print(ch, end="", flush=True)
            # add the character typed to the msg
            msg += ch

my_socket.close()

