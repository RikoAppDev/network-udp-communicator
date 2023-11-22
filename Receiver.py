import threading
from socket import *

from DataHeader import DataHeader
from utils import *


class Receiver:
    address: tuple
    receiver: socket

    def __init__(self, address):
        self.address = address
        self.receiver = socket(AF_INET, SOCK_DGRAM)
        self.receiver.bind(address)

    def receive(self):
        tag = None
        connected = False
        total_packets = None
        filename = None
        correctly_received = 0
        failed_counter = 0
        received_data = []

        while True:
            if tag != 8 and not connected:
                print(f"📡 Waiting for connection on {format_address(self.address)} 🪢", end="")
            elif tag != 8 and connected:
                print(f"📡 Waiting for data on {format_address(self.address)} 🪢", end="")

            # 1500 - 20 - 8 = 1472
            sender_message, sender_address = self.receiver.recvfrom(1472)
            tag, amount_of_packets, data_size, crc, data = open_data(sender_message)

            new_crc = get_crc_value(tag, amount_of_packets, data_size, data)
            if new_crc == crc:
                # FIN communication
                if tag == 7:
                    print(f"\r💻 {format_address(sender_address)} want to end communication: {data.decode()} 🏷️")
                    self.receiver.sendto(
                        DataHeader(5, "Got your request! Thank you and bye! 👋".encode(), 1).pack_data(),
                        sender_address
                    )
                    self.receiver.close()
                    break
                # SWAP modes
                elif tag == 6:
                    print(f"\r💻 {format_address(sender_address)} want to swap mode to receiver 📡: {data.decode()} 🏷️")
                    self.receiver.sendto(
                        DataHeader(5, "Got your request! Swapping mode to sender! 📨".encode(), 1).pack_data(),
                        sender_address
                    )
                    self.receiver.close()
                    break
                # Are you alive?
                elif tag == 2:
                    print(f"\rConnected 💻 {format_address(sender_address)} 🔊 {data.decode()} 🛎️")
                    self.receiver.sendto(
                        DataHeader(1, "Got your request! We are connected! 🫱🏼‍🫲🏼".encode(), 1).pack_data(),
                        sender_address
                    )
                    connected = True

                    # keep_alive_thread = threading.Thread(target=self.handle_keep_alive, daemon=True).start()
                # Basic data
                else:
                    correctly_received += 1
                    received_data.append(data)

                    if total_packets is None:
                        total_packets = amount_of_packets

                    if tag == 3:
                        print(f"\rMessage from 💻 {format_address(sender_address)} is: {data.decode()}")
                    elif tag == 4:
                        if filename is None:
                            received_data.clear()
                            filename = data.decode()
                        print(f"\rData from 💻 {format_address(sender_address)} are: {data}")
                    self.receiver.sendto(
                        DataHeader(5, "Got your message! Thank you! 👌".encode(), 1).pack_data(),
                        sender_address
                    )
            else:
                failed_counter += 1
                print(f"\rData from 💻 {format_address(sender_address)} was rejected 🛂⛔")
                print(tag, amount_of_packets, data_size, crc, data)
                self.receiver.sendto(
                    DataHeader(0, "Got corrupted packet! It needs to be retransmitted! 🛂".encode(), 1).pack_data(),
                    sender_address
                )

            if correctly_received == total_packets:
                if tag == 4:
                    print(f'\nStreaming data into {filename} ...', end="")

                all_data = self.build_data(received_data)

                if tag == 3:
                    print(f"\n📜 Received message is: {all_data.decode()}")
                    print(f"📏 Message size: {len(all_data)}B \n")
                elif tag == 4:
                    stream_data_into_file(filename, all_data)

                    print(f"\n📜 File location is '{os.path.abspath(filename)}'")
                    print(f"📏 File size: {len(all_data)}B \n")

                total_packets = None
                filename = None
                correctly_received = 0
                failed_counter = 0
                received_data = []

        return tag, self.address

    @staticmethod
    def build_data(received_data):
        data: bytes = b""

        for d in received_data:
            data += d

        return data

    def handle_keep_alive(self):
        while True:
            data, sender_address = self.receiver.recvfrom(1024)
            if open_data(data)[0] == 8:
                self.receiver.sendto(DataHeader(9, "KA-ACK".encode(), 1).pack_data(), sender_address)
