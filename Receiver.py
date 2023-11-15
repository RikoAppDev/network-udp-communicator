from socket import *


class Receiver:
    address: tuple
    receiver: socket

    def __init__(self, address):
        self.address = address
        self.receiver = socket(AF_INET, SOCK_DGRAM)
        self.receiver.bind(address)

    def receive(self):
        while True:
            print(f"📡 Waiting for message on {self.address} 🪢", end="")
            message, sender_address = self.receiver.recvfrom(1024)

            if message.decode('utf-8').upper() == "!F":
                print(f"\r💻 {sender_address} want to end communication: {message.decode('utf-8')}")
                self.receiver.sendto("Got your request! Thank you and bye! 👋".encode('utf-8'), sender_address)
            elif message.decode('utf-8').upper() == "!Q":
                print(f"\r💻 {sender_address} quited connection: {message.decode('utf-8')}")
                self.receiver.sendto("See you soon and bye! 👋".encode('utf-8'), sender_address)
                self.receiver.close()
                break
            elif message.decode('utf-8').upper() == "!S":
                print(f"\r💻 {sender_address} want to swap mode to receiver 📡: {message.decode('utf-8')}")
                self.receiver.sendto("Got your request! Swapping mode to sender! 📨".encode('utf-8'), sender_address)
                self.receiver.close()
                break
            else:
                print(f"\rMessage from 💻 {sender_address} is: {message.decode('utf-8')}")
                self.receiver.sendto("Got your message! Thank you! 👌".encode('utf-8'), sender_address)

        return message.decode('utf-8').upper(), self.address
