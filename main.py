import socket

from Receiver import Receiver
from Sender import Sender

IP_ADDRESS = socket.gethostbyname(socket.gethostname())
PORT = 42069
ADDRESS = (IP_ADDRESS, PORT)
wanna_terminate = False

if __name__ == '__main__':
    print(f"Welcome 💻 {socket.gethostname()} you are {ADDRESS}")

    while not wanna_terminate:
        mode = input("Choose operation mode: 📡 RECEIVER -> 1️⃣ | 📨 SENDER -> 2️⃣ >> ")

        while mode != "1" and mode != "2":
            print(f"‼️ Error ‼️\n\t- Incorrect operation mode")
            mode = input("Choose operation mode: 📡 RECEIVER -> 1️⃣ | 📨 SENDER -> 2️⃣ >> ")

        if mode == "1":
            try:
                receiver = Receiver(ADDRESS)
            except OSError:
                print(f"‼️ Error ‼️\n\t- Receiver with same config is already awake")
        elif mode == "2":
            sender = Sender(ADDRESS)
