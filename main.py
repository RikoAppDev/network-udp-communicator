import socket
import threading

from utils import *
from Receiver import Receiver
from Sender import Sender

DEFAULT_IP_ADDRESS = socket.gethostbyname(socket.gethostname())
DEFAULT_PORT = 42069
DEFAULT_ADDRESS = (DEFAULT_IP_ADDRESS, DEFAULT_PORT)
wanna_terminate = False

if __name__ == '__main__':
    print(f"Welcome 💻 {socket.gethostname()} you are '{DEFAULT_IP_ADDRESS}' 🌐")

    state = None
    mode = None
    address = (None, None)
    while not wanna_terminate:
        if state != 6:
            mode = select_mode()
        elif state == 6:
            if mode == "1":
                mode = "2"
            else:
                mode = "1"

        if mode == "1":
            print("\nMODE 1️⃣ ➡ RECEIVER 📡")
        else:
            print("\nMODE 2️⃣ ➡ SENDER 📨")

        if mode == "1":
            if state != 6:
                # address = (DEFAULT_IP_ADDRESS, get_port())
                address = (DEFAULT_IP_ADDRESS, DEFAULT_PORT)

            receiver = Receiver(address)
            state, address = receiver.receive()

        elif mode == "2":
            if state != 6:
                # address = (get_ip_address(), get_port(False))
                address = ('147.175.162.234', 42069)
            sender = Sender(address)
            while not sender.check_aliveness():
                address = (address[0], get_port(False))
                sender = Sender(address)

            # keep_alive_thread = threading.Thread(target=sender.keep_alive, daemon=True).start()

            state = sender.send()
            if state == 7:
                wanna_terminate = True
