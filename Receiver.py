from socket import *
from tqdm import tqdm

from DataHeader import DataHeader
from utils import *


class Receiver:
    address: tuple
    receiver: socket
    show_progress_bar: bool
    SWAP_INITIALISATION: bool

    def __init__(self, address):
        self.show_progress_bar = handle_show_progress()
        self.file_save_location = get_file_save_path()
        keyboard.add_hotkey('ctrl+s', self.swap_initialization)
        self.SWAP_INITIALISATION = False

        self.address = address
        self.receiver = socket(AF_INET, SOCK_DGRAM)
        self.receiver.bind(address)

    def receive(self):
        flags = None
        connected = False
        all_packets = False
        filename = None
        correctly_received = 0
        failed_counter = 0
        received_data = b""
        progress_bar = None
        keep_conn_alive = 0
        start = None
        ka_start_helper = False
        no_incoming_comm = 0
        sender_not_communicating = 0
        packet_ack_number = 0

        while True:
            try:
                if not contain_flags(flags, 'K') and not connected:
                    print(f"📡 Waiting for connection on {format_address(self.address)} 🪢", end="")
                elif not contain_flags(flags, 'K') and connected and all_packets is False:
                    print(f"📡 Waiting for data on {format_address(self.address)} 🪢", end="")

                self.receiver.settimeout(60)
                # 1500 - 20 - 8 = 1472
                sender_message, sender_address = self.receiver.recvfrom(1472)
                flags, seq_number, crc, data = open_data(sender_message)

                no_incoming_comm = 0
                sender_not_communicating = 0

                new_crc = get_crc_value(flags, seq_number, data)
                if new_crc == crc:
                    # Keep alive
                    if contain_flags(flags, 'K'):
                        if not ka_start_helper:
                            start = timer()
                            start -= 5
                            ka_start_helper = True

                        keep_conn_alive += 1
                        print(f"\r({timer() - start:.0f}s) Keeping connection alive...", end="")

                        self.receiver.sendto(
                            DataHeader('KA' if not self.SWAP_INITIALISATION else 'KAS', "KA-ACK".encode(),
                                       0).pack_data(), sender_address)
                    # FIN communication
                    elif match_flags(flags, 'Q'):
                        print(f"\r💻 {format_address(sender_address)} want to end communication: {data.decode()} 🏷️")
                        self.receiver.sendto(
                            DataHeader('QA', "Got your request! Thank you and bye! 👋".encode(), 0).pack_data(),
                            sender_address
                        )
                        self.receiver.close()
                        return 'Q', sender_address
                    # SWAP modes ACK from SENDER
                    elif match_flags(flags, 'SA'):
                        print(f"\r💻 {format_address(sender_address)} 🔊 {data.decode()}")

                        self.receiver.close()
                        return 'S', sender_address
                    # SWAP modes wanted by SENDER
                    elif contain_flags(flags, 'S'):
                        print(
                            f"\r💻 {format_address(sender_address)} want to swap mode to receiver 📡: {data.decode()} 🏷️")
                        self.receiver.sendto(
                            DataHeader('SA', "Got your request! Swapping mode to sender! 📨".encode(), 0).pack_data(),
                            sender_address
                        )
                        self.receiver.close()
                        return 'S', sender_address
                    # Are you alive?
                    elif contain_flags(flags, 'E'):
                        print(f"\rConnected 💻 {format_address(sender_address)} 🔊 {data.decode()} 🛎️")
                        self.receiver.sendto(
                            DataHeader('EA', "Got your request! We are connected! 🫱🏼‍🫲🏼".encode(), 0).pack_data(),
                            sender_address
                        )
                        connected = True
                        if self.show_progress_bar:
                            progress_bar = tqdm(unit="B", unit_scale=True)
                    # Basic data
                    else:
                        if packet_ack_number == seq_number:
                            packet_ack_number = seq_number + 1
                            correctly_received += 1
                            received_data += data

                            if self.show_progress_bar:
                                progress_bar.update(1)

                            if contain_flags(flags, 'T'):
                                if self.show_progress_bar:
                                    progress_bar.desc = "📡 Receiving message"
                                else:
                                    print(
                                        f"\rPacket {seq_number}. from 💻 {format_address(sender_address)} was accepted 🛂✅")
                                    print(f"\t📦 Packet data size: {len(sender_message)}B -", bin(flags), seq_number,
                                          crc,
                                          data)
                            elif contain_flags(flags, 'F'):
                                if filename is None:
                                    received_data = b""
                                    filename = data.decode()
                                    if self.show_progress_bar:
                                        progress_bar.desc = f"📡 Receiving file {filename}"
                                if not self.show_progress_bar:
                                    print(
                                        f"\rPacket {seq_number} from 💻 {format_address(sender_address)} was accepted 🛂✅")
                                    print(f"\t📦 Packet data size: {len(sender_message)}B -", bin(flags), seq_number,
                                          crc,
                                          data)

                            if contain_flags(flags, 'FQ') or contain_flags(flags, 'TQ'):
                                self.receiver.sendto(
                                    DataHeader('FA' if contain_flags(flags, 'F') else 'TA',
                                               f"Got last packet {seq_number}. Thank you! 👌".encode(),
                                               seq_number).pack_data(),
                                    sender_address
                                )
                                all_packets = True
                            else:
                                self.receiver.sendto(
                                    DataHeader('FA' if contain_flags(flags, 'F') else 'TA',
                                               f"Got packet {seq_number}. Thank you! 👌".encode(),
                                               seq_number).pack_data(),
                                    sender_address
                                )
                else:
                    failed_counter += 1
                    if not self.show_progress_bar:
                        print(f"\rPacket {seq_number} from 💻 {format_address(sender_address)} was rejected 🛂⛔")
                        print(f"\t📦 Packet data size: {len(sender_message)}B -", bin(flags), seq_number, crc, data)
                    self.receiver.sendto(
                        DataHeader('R', f"Got corrupted packet {seq_number}! It needs to be retransmitted! 🛂".encode(),
                                   seq_number).pack_data(),
                        sender_address
                    )

                if all_packets:
                    if self.show_progress_bar:
                        progress_bar.close()

                    if contain_flags(flags, 'F'):
                        print(f'\nStreaming data into {filename} ...', end="")

                    if contain_flags(flags, 'T'):
                        print(f"\n📄 Received message is: {received_data.decode()}")
                        print(f"📏 Message size: {len(received_data)}B \n")
                    elif contain_flags(flags, 'F'):
                        stream_data_into_file(self.file_save_location, filename, received_data)

                    all_packets = False
                    filename = None
                    correctly_received = 0
                    failed_counter = 0
                    received_data = b""
                    start = timer()
                    packet_ack_number = 0

            except TimeoutError:
                if not connected:
                    no_incoming_comm += 60
                    print(f"\r⚠️ Warning ⚠️\n\t- No incoming communication ({no_incoming_comm}s)")
                    if no_incoming_comm == 120:
                        print(f"\r⚠️ SHUTTING DOWN ⚠️")
                        exit()
                else:
                    sender_not_communicating += 60
                    print(f"\r⚠️ Warning ⚠️\n\t- Sender is not communicating ({sender_not_communicating})s")
                    if sender_not_communicating == 120:
                        print(f"\r⚠️ SHUTTING DOWN ⚠️")
                        exit()
            except ConnectionResetError:
                print_error_connection_reset()

    def swap_initialization(self):
        if not self.SWAP_INITIALISATION:
            print("\n🔄️ Swap Initialization")
            self.SWAP_INITIALISATION = True
