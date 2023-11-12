from socket import *


class Sender:
    address: tuple
    sender = socket(AF_INET, SOCK_DGRAM)

    def __init__(self, address):
        self.address = address
        self.send()

    def send(self):
        message = ""
        while message.upper() != "!Q":
            message = input(f"Input message for {self.address} 📨 >> ")
            self.sender.sendto(message.encode('utf-8'), self.address)
            try:
                receiver_message, receiver_address = self.sender.recvfrom(1024)
                print(f"💻 {receiver_address} response: " + receiver_message.decode('utf-8'))
            except ConnectionResetError:
                print(f"‼️ Error ‼️\n\t- Receiver is not alive")
