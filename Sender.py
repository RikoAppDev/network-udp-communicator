import math
import random
import socket
from threading import Thread
from socket import *
from time import sleep

from tqdm import tqdm

from DataHeader import DataHeader
from utils import *


class Sender:
    address: tuple
    sender: socket
    KEEP_ALIVE_THREAD_STATUS: bool

    def __init__(self, address):
        self.address = address
        self.sender = socket(AF_INET, SOCK_DGRAM)
        self.KEEP_ALIVE_THREAD_STATUS = False
        self.RECEIVER_SWAP_INITIALISATION = False

    def send(self):
        while True:
            task = handle_send_input_type()

            self.KEEP_ALIVE_THREAD_STATUS = False
            if not self.RECEIVER_SWAP_INITIALISATION:
                if task == "1":
                    if self.send_text_message():
                        break
                elif task == "2":
                    if self.send_file():
                        break
                elif task == "3":
                    if self.send_swap_request():
                        return 'S'
                    else:
                        break
                elif task == "4":
                    if self.send_fin_request():
                        return 'Q'
                    else:
                        break
                else:
                    self.KEEP_ALIVE_THREAD_STATUS = True
                    print(f"‼️ Error ‼️\n\t- Unsupported task")
            else:
                return 'S'

    def send_text_message(self):
        message = input(f"📝 Input message for {format_address(self.address)} 📨 >> ")
        return self.send_data(message)

    def send_file(self):
        file_path = handle_file_path_input()

        with open(file_path, 'rb') as file:
            data = file.read()
            file.close()

        return self.send_data(data, file_path.split('\\')[-1])

    def send_data(self, data, filename=None):
        fragment_size = handle_fragment_size_input()
        error_sim = handle_error_sim_input()
        show_progress_bar = handle_show_progress()

        amount_of_packets = math.ceil(len(data) / fragment_size)

        filename_length = None
        filename_sent = False
        data_length = len(data)

        if filename is not None:
            filename_length = len(filename.encode())
            data = filename.encode() + data
            amount_of_packets += 1

        print(f"\r\nℹ️ INFO:\n\t📏 Size of the data: {data_length}B")
        print(
            f"\t📦 Data was parsed into {amount_of_packets} packets\n" if amount_of_packets > 1 else f"\t📦 Data was packaged into 1 packet\n"
        )
        print("🪵 LOG:")

        if show_progress_bar:
            progress_bar = tqdm(
                total=amount_of_packets,
                desc=f"{f'📨 Sending file {filename}' if filename is not None else '📨 Sending message'}",
                unit="B",
                unit_scale=True
            )

        conn_lost = False
        seq_number = 0
        failed_counter = 0
        packet_length = 0

        while len(data) != 0:
            if filename is not None and not filename_sent:
                fractional_data = data[:filename_length]
            else:
                fractional_data = data[:fragment_size]

            packet_length = len(fractional_data) + 5
            if filename:
                self.sender.sendto(
                    DataHeader('F' if seq_number < amount_of_packets - 1 else 'FQ', fractional_data, seq_number)
                    .pack_data(random.randrange(0, 100) < error_sim), self.address
                )
            else:
                self.sender.sendto(
                    DataHeader('T' if seq_number < amount_of_packets - 1 else 'TQ', fractional_data.encode(),
                               seq_number)
                    .pack_data(random.randrange(0, 100) < error_sim), self.address
                )

            try:
                receiver_message, receiver_address = self.sender.recvfrom(1024)
                flags, _, _, d = open_data(receiver_message)

                if contain_flags(flags, 'A'):
                    if show_progress_bar:
                        progress_bar.update(1)

                    if filename is not None and not filename_sent:
                        data = data[filename_length:]
                        filename_sent = True
                    else:
                        data = data[fragment_size:]

                    if not show_progress_bar:
                        print(f"\t💻 {format_address(receiver_address)} 🔊 {d.decode()}")
                        print(f"\t✅ Packet {seq_number} with size {packet_length}B was successfully sent 📭")

                    seq_number += 1
                elif contain_flags(flags, 'R'):
                    failed_counter += 1
                    if not show_progress_bar:
                        print(f"\t💻 {format_address(receiver_address)} 🔊 {d.decode()}")
                        print(f"\t🔁 Packet {seq_number} with size {packet_length}B will be retransmitted 📬")
            except ConnectionResetError:
                print_error_connection_reset(2)
                if self.try_reestablish_connection():
                    conn_lost = False
                else:
                    conn_lost = True
                    break
            except TimeoutError:
                print_error_timout(2)
                if self.try_reestablish_connection():
                    conn_lost = False
                else:
                    conn_lost = True
                    break

        if not conn_lost:
            print(
                f"\n🧾 Summary:\n"
                f"\t📦 All sent packets: {seq_number + failed_counter}\n"
                f"\t🔁 Retransmitted packets: {failed_counter}\n"
                f"\t📏 Size of the data: {data_length}B"
            )

            self.KEEP_ALIVE_THREAD_STATUS = True
            Thread(target=self.keep_alive, daemon=True).start()
        else:
            print("⚠️ Communication was unsuccessful due to connection loss ⚠️\n\t- All transmitted data was lost.")

        return conn_lost

    def send_swap_request(self):
        self.sender.sendto(DataHeader('S', "SWAP".encode(), 0).pack_data(), self.address)
        try:
            receiver_message, receiver_address = self.sender.recvfrom(1024)
            flags, packet_number, crc, data = open_data(receiver_message)
            if contain_flags(flags, 'SA'):
                print(f"💻 {format_address(receiver_address)} 🔊 {data.decode()}")
                return True
        except ConnectionResetError:
            print_error_connection_reset(2)
            return False
        except TimeoutError:
            print_error_timout(2)
            return False

    def send_fin_request(self):
        self.sender.sendto(DataHeader('Q', "FIN".encode(), 0).pack_data(), self.address)
        try:
            receiver_message, receiver_address = self.sender.recvfrom(1024)
            flags, packet_number, crc, data = open_data(receiver_message)

            if contain_flags(flags, 'QA'):
                print(f"💻 {format_address(receiver_address)} 🔊 {data.decode()}")
                return True
        except ConnectionResetError:
            print_error_connection_reset(2)
            return False
        except TimeoutError:
            print_error_timout(2)
            return False

    def check_aliveness(self, reestablish=False):
        if not reestablish:
            handle_wait_for_server_setup()

        if not reestablish:
            print("\rEstablishing connection...", end="")
        sleep(.5)
        self.sender.settimeout(10)
        self.sender.sendto(DataHeader('E', "Are you alive?".encode(), 0).pack_data(), self.address)

        try:
            receiver_message, receiver_address = self.sender.recvfrom(1024)
            flags, packet_number, crc, data = open_data(receiver_message)
            if contain_flags(flags, 'EA'):
                if reestablish:
                    print(f"\rConnection reestablished with 💻 {format_address(receiver_address)} 🔊 {data.decode()}")
                else:
                    print(f"\rConnected to 💻 {format_address(receiver_address)} 🔊 {data.decode()}")

                self.KEEP_ALIVE_THREAD_STATUS = True
                Thread(target=self.keep_alive, daemon=True).start()

                return True
        except ConnectionResetError:
            if not reestablish:
                print_error_connection_reset(2)
            return False
        except TimeoutError:
            if not reestablish:
                print_error_timout(2)
            return False

    def keep_alive(self):
        start = timer()
        sleep(5)
        seq_number = 0

        while self.KEEP_ALIVE_THREAD_STATUS:
            print(f"\r({timer() - start:.0f}s) Keeping connection alive... >> ", end="")
            self.sender.settimeout(10)
            self.sender.sendto(DataHeader('K', "KEEP ALIVE".encode(), seq_number).pack_data(), self.address)

            try:
                receiver_message, receiver_address = self.sender.recvfrom(1024)
                flags, packet_number, crc, data = open_data(receiver_message)

                if contain_flags(flags, 'S'):
                    print(
                        f"\r💻 {format_address(receiver_address)} want to swap mode to sender 📨: SWAP 🏷️")
                    print("Click enter for RECEIVER setup ;)", end="")
                    self.sender.sendto(
                        DataHeader('SA', "Got your request! Swapping mode to receiver! 📡".encode(), 0).pack_data(),
                        receiver_address
                    )
                    self.KEEP_ALIVE_THREAD_STATUS = False
                    self.RECEIVER_SWAP_INITIALISATION = True
                    break
                if contain_flags(flags, 'KA'):
                    seq_number += 1
            except ConnectionResetError:
                print_error_connection_reset(2)
                self.try_reestablish_connection()
                break
            except TimeoutError:
                print_error_timout(2)
                self.try_reestablish_connection()
                break
            sleep(5)

    def try_reestablish_connection(self):
        start_reestablish = timer()
        while timer() - start_reestablish < 30:
            print(f"\rTrying to reestablish connection ({30 - (timer() - start_reestablish):.0f}s)...", end="")
            if self.check_aliveness(True):
                sleep(0.5)
                print(">> ", end="")
                self.KEEP_ALIVE_THREAD_STATUS = False
                return True
            sleep(0.1)

        print("\r\n⚠️ CONNECTION WAS LOST ⚠️")
        self.KEEP_ALIVE_THREAD_STATUS = False
        os._exit(0)
