import math
from socket import *
from time import sleep

from DataHeader import DataHeader
from utils import *


class Sender:
    address: tuple
    sender: socket

    def __init__(self, address):
        self.address = address
        self.sender = socket(AF_INET, SOCK_DGRAM)

    def send(self):
        while True:
            task = handle_send_input_type()

            if task == "1":
                if self.send_text_message():
                    break
            elif task == "2":
                if self.send_file():
                    break
            elif task == "3":
                self.send_swap_request()
                return 6
            elif task == "4":
                self.send_fin_request()
                return 7

    def send_text_message(self):
        fragment_size = handle_fragment_size_input()
        message = input(f"📝 Input message for {format_address(self.address)} 📨 >> ")

        return self.send_data(message, fragment_size)

    def send_file(self):
        pass

    def send_data(self, data, fragment_size):
        amount_of_packets = math.ceil(len(data) / fragment_size)

        print(f"\nℹ️ INFO:\n\t📏 Size of the data: {len(data)}B")
        print(
            f"\t📦 Data was parsed into {amount_of_packets} packets\n" if amount_of_packets > 1 else f"\t📦 Data was packaged into 1 packet\n"
        )
        print("🪵 LOG:")

        conn_lost = False
        packet_counter = 0
        failed_counter = 0

        while len(data) != 0:
            fractional_data = data[:fragment_size]

            self.sender.sendto(DataHeader(3, fractional_data.encode(), amount_of_packets).pack_data(), self.address)
            try:
                receiver_message, receiver_address = self.sender.recvfrom(1024)

                if open_data(receiver_message)[0] == 5:
                    packet_counter += 1
                    data = data[fragment_size:]
                    print(f"\t💻 {format_address(receiver_address)} 🔊 {open_data(receiver_message)[4].decode()}")
                    print(f"\t✅ Packet {packet_counter} was successfully sent 📭")
                elif open_data(receiver_message)[0] == 0:
                    failed_counter += 1
                    print(f"\t💻 {format_address(receiver_address)} 🔊 {open_data(receiver_message)[4].decode()}")
                    print(f"\t🔁 Packet {packet_counter} will be retransmitted 📬")
            except ConnectionResetError:
                print(f"⚠️ Warning ⚠️\n\t- Receiver is not alive, connection lost")
                conn_lost = True
                break

        print(f"\n🧾 Summary:\n\t📦 Sent packets: {packet_counter}\n\t🔁 Retransmitted packets: {failed_counter}")

        return conn_lost

    def send_swap_request(self):
        self.sender.sendto(DataHeader(6, "SWAP".encode(), 1).pack_data(), self.address)
        try:
            receiver_message, receiver_address = self.sender.recvfrom(1024)
            print(f"💻 {format_address(receiver_address)} 🔊 {open_data(receiver_message)[4].decode()}")
        except ConnectionResetError:
            print(f"⚠️ Warning ⚠️\n\t- Receiver is not alive, connection lost")

    def send_fin_request(self):
        self.sender.sendto(DataHeader(7, "FIN".encode(), 1).pack_data(), self.address)
        try:
            receiver_message, receiver_address = self.sender.recvfrom(1024)
            print(f"💻 {format_address(receiver_address)} 🔊 {open_data(receiver_message)[4].decode()}")
        except ConnectionResetError:
            print(f"⚠️ Warning ⚠️\n\t- Receiver is not alive, connection lost")

    def check_aliveness(self):
        sleep(.5)
        self.sender.sendto(DataHeader(2, "Are you alive?".encode(), 1).pack_data(), self.address)

        try:
            receiver_message, receiver_address = self.sender.recvfrom(1024)
            tag, packet_number, data_size, crc, data = open_data(receiver_message)
            print(f"Connected to 💻 {format_address(receiver_address)} 🔊 {data.decode()}")
        except ConnectionResetError:
            print(f"‼️ Error ‼️\n\t- Receiver is not alive")
            return False

        return True

    def keep_alive(self):
        while True:
            self.sender.sendto(DataHeader(8, "KEEP ALIVE".encode(), 1).pack_data(), self.address)
            sleep(5)
