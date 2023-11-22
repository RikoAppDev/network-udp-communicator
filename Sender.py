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
        fragment_size = handle_fragment_size_input()
        file_path = handle_file_path_input()

        with open(file_path, 'rb') as file:
            data = file.read()
            file.close()

        return self.send_data(data, fragment_size, file_path.split('\\')[-1])

    def send_data(self, data, fragment_size, file_name=None):
        amount_of_packets = math.ceil(len(data) / fragment_size)

        filename_length = None
        filename_sent = False
        data_length = len(data)

        if file_name is not None:
            filename_length = len(file_name.encode())
            data = file_name.encode() + data
            amount_of_packets += 1

        print(f"\nℹ️ INFO:\n\t📏 Size of the data: {data_length}B")
        print(
            f"\t📦 Data was parsed into {amount_of_packets} packets\n" if amount_of_packets > 1 else f"\t📦 Data was packaged into 1 packet\n"
        )
        print("🪵 LOG:")

        conn_lost = False
        packet_counter = 0
        failed_counter = 0

        while len(data) != 0:
            if file_name is not None and not filename_sent:
                fractional_data = data[:filename_length]
            else:
                fractional_data = data[:fragment_size]

            if file_name:
                self.sender.sendto(DataHeader(4, fractional_data, amount_of_packets).pack_data(), self.address)
            else:
                self.sender.sendto(DataHeader(3, fractional_data.encode(), amount_of_packets).pack_data(), self.address)

            try:
                receiver_message, receiver_address = self.sender.recvfrom(1024)

                if open_data(receiver_message)[0] == 5:
                    packet_counter += 1
                    if file_name is not None and not filename_sent:
                        data = data[filename_length:]
                        filename_sent = True
                    else:
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

        print(
            f"\n🧾 Summary:\n"
            f"\t📦 Sent packets: {packet_counter}\n"
            f"\t🔁 Retransmitted packets: {failed_counter}\n"
            f"\t📏 Size of the data: {data_length}B"
        )

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
