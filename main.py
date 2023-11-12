import socket
import re

from Receiver import Receiver
from Sender import Sender


def check_ip_address(ip):
    ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')

    if ip_pattern.match(ip):
        for octet in ip.split('.'):
            if not (0 <= int(octet) <= 255):
                return False
        return True
    else:
        return False


DEFAULT_IP_ADDRESS = socket.gethostbyname(socket.gethostname())
DEFAULT_PORT = 42069
DEFAULT_ADDRESS = (DEFAULT_IP_ADDRESS, DEFAULT_PORT)
wanna_terminate = False

if __name__ == '__main__':
    print(f"Welcome 💻 {socket.gethostname()} you are '{DEFAULT_IP_ADDRESS}'")

    state = ""
    mode = ""
    while not wanna_terminate:
        if state != "!S":
            mode = input("Choose operation mode: 📡 RECEIVER -> 1️⃣ | 📨 SENDER -> 2️⃣ >> ")
        elif state == "!S":
            if mode == "1":
                mode = "2"
                print("\nMODE 2️⃣: SENDER 📨")
            else:
                print("\nMODE 1️⃣: RECEIVER 📡")
                mode = "1"

        while mode != "1" and mode != "2":
            print(f"‼️ Error ‼️\n\t- Incorrect operation mode")
            mode = input("Choose operation mode: 📡 RECEIVER -> 1️⃣ | 📨 SENDER -> 2️⃣ >> ")

        if mode == "1":
            port = int(input("Choose listening port 🔌 >> "))

            while not (0 < port < 65536):
                print(f"‼️ Error ‼️\n\t- Incorrect port")
                port = int(input("Choose listening port 🔌 >> "))

            DEFAULT_ADDRESS = (DEFAULT_IP_ADDRESS, port)

            try:
                receiver = Receiver(DEFAULT_ADDRESS)
                state = receiver.receive()
            except OSError:
                print(f"‼️ Error ‼️\n\t- Receiver with same config is already awake")
        elif mode == "2":
            ip_address = input("Receiver's device IP address >> ")

            while not check_ip_address(ip_address):
                print(f"‼️ Error ‼️\n\t- Incorrect IP address type")
                ip_address = input("Receiver's IP address >> ")

            port = int(input("Receiver's port >> "))

            while not (0 < port < 65536):
                print(f"‼️ Error ‼️\n\t- Incorrect port")
                port = input("Receiver's port >> ")

            sender = Sender((ip_address, port))
            state = sender.send()
            if state == "!Q":
                wanna_terminate = True
