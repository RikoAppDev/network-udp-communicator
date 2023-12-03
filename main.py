import socket

from utils import *
from Receiver import Receiver
from Sender import Sender

DEFAULT_IP_ADDRESS = socket.gethostbyname(socket.gethostname())
wanna_terminate = False

if __name__ == '__main__':
    print(f"Welcome 💻 {socket.gethostname()} you are '{DEFAULT_IP_ADDRESS}' 🌐")

    state = None
    mode = None
    address = (None, None)
    sender_address = (None, None)
    while not wanna_terminate:
        if state != 'S':
            mode = select_mode()
        elif state == 'S':
            if mode == "1":
                mode = "2"
            else:
                mode = "1"

        if mode == "1":
            print("\nMODE 1️⃣ ➡ RECEIVER 📡")
        else:
            print("\nMODE 2️⃣ ➡ SENDER 📨")

        if mode == "1":
            if state != 'S':
                address = (DEFAULT_IP_ADDRESS, get_port())
            else:
                address = (DEFAULT_IP_ADDRESS, address[1])

            try:
                receiver = Receiver(address)
                state, sender_address = receiver.receive()
            except OSError:
                print(f"‼️ Error ‼️\n\t- Receiver with the same config is already alive")
        elif mode == "2":
            if state != 'S':
                address = (get_ip_address(), get_port(False))
            else:
                address = (sender_address[0], address[1])

            sender = Sender(address)
            input_wrong_address = 0
            while not sender.check_aliveness():
                if input_wrong_address < 2:
                    address = (address[0], get_port(False))
                else:
                    address = (get_ip_address(), get_port(False))
                    input_wrong_address = 0

                sender = Sender(address)
                input_wrong_address += 1

            state = sender.send()
            if state == 'Q':
                wanna_terminate = True
