import binascii
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


def handle_port_input(text):
    while True:
        port = input(text)

        if port.isdigit():
            if 0 < int(port) < 64536:
                return int(port)
            else:
                print(f"‼️ Error ‼️\n\t- Incorrect port")
        else:
            print(f"‼️ Error ‼️\n\t- Port must be a number")


def get_port(rec=True):
    if rec:
        p = handle_port_input("Choose listening port 🔌 >> ")
    else:
        p = handle_port_input("Receiver's port 🔌 >> ")

    return p


def get_ip_address():
    ip = input("Receiver's device IP address >> ")

    while not check_ip_address(ip.strip()):
        print(f"‼️ Error ‼️\n\t- Incorrect IP address type")
        ip = input("Receiver's IP address >> ")

    return ip


DEFAULT_IP_ADDRESS = socket.gethostbyname(socket.gethostname())
DEFAULT_PORT = 42069
DEFAULT_ADDRESS = (DEFAULT_IP_ADDRESS, DEFAULT_PORT)
wanna_terminate = False

if __name__ == '__main__':
    print(f"Welcome 💻 {socket.gethostname()} you are '{DEFAULT_IP_ADDRESS}'")

    state = ""
    mode = ""
    address = ("", 0)
    while not wanna_terminate:
        if state != "!S":
            mode = input("Choose operation mode: 📡 RECEIVER -> 1️⃣ | 📨 SENDER -> 2️⃣ >> ")
            while mode != "1" and mode != "2":
                print(f"‼️ Error ‼️\n\t- Incorrect operation mode")
                mode = input("Choose operation mode: 📡 RECEIVER -> 1️⃣ | 📨 SENDER -> 2️⃣ >> ")
        elif state == "!S":
            if mode == "1":
                mode = "2"
            else:
                mode = "1"

        if mode == "1":
            print("\nMODE 1️⃣: RECEIVER 📡")
        else:
            print("\nMODE 2️⃣: SENDER 📨")

        if mode == "1":
            if state != "!S":
                address = (DEFAULT_IP_ADDRESS, get_port())

            try:
                receiver = Receiver(address)
                state, address = receiver.receive()
            except OSError:
                print(f"‼️ Error ‼️\n\t- Receiver with same config is already awake")
        elif mode == "2":
            if state != "!S":
                address = (get_ip_address(), get_port(False))
            sender = Sender(address)
            while not sender.check_aliveness():
                address = (address[0], get_port(False))
                sender = Sender(address)

            state = sender.send()
            if state == "!Q":
                wanna_terminate = True
