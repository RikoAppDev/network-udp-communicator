import binascii
import re
import struct


def select_mode():
    mode = input("\n⚙️ Choose operation mode: 📡 RECEIVER ➡ 1️⃣ | 📨 SENDER ➡ 2️⃣ >> ")
    while mode != "1" and mode != "2":
        print(f"‼️ Error ‼️\n\t- Incorrect operation mode")
        mode = input("\n⚙️ Choose operation mode: 📡 RECEIVER ➡ 1️⃣ | 📨 SENDER ➡ 2️⃣ >> ")

    return mode


def check_ip_address(ip):
    ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')

    if ip_pattern.match(ip):
        for octet in ip.split('.'):
            if not (0 <= int(octet) <= 255):
                return False
        return True
    else:
        return False


def get_ip_address():
    ip = input("📡 Receiver's IP address >> ")

    while not check_ip_address(ip.strip()):
        print(f"‼️ Error ‼️\n\t- Incorrect IP address type")
        ip = input("📡 Receiver's IP address >> ")

    return ip


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


def handle_send_input_type():
    while True:
        task = input(
            "\n🔢 What you wanna do?\n"
            "\t1️⃣ Send text message ✉️\n"
            "\t2️⃣ Send file 📁\n"
            "\t3️⃣ Swap modes 🔄️\n"
            "\t4️⃣ End communication 💔\n"
            ">> "
        )
        if task in ["1", "2", "3", "4"]:
            return task
        else:
            print(f"‼️ Error ‼️\n\t- Unsupported task")


def handle_fragment_size_input():
    while True:
        size = input("📏 Input fragment size (max 65 500 B) >> ")

        if size.isdigit():
            if 0 < int(size) <= 65500:
                return int(size)
            else:
                print(f"‼️ Error ‼️\n\t- Fragment size is out of range (1 - 65500)")
        else:
            print(f"‼️ Error ‼️\n\t- Fragment size must be a number")


def format_address(address):
    return f"'{address[0]}:{address[1]}'"


def open_data(header_data):
    tag, amount_of_packets, data_size, crc = struct.unpack('!BIIH', header_data[:11])
    data = header_data[11:11 + data_size]
    return tag, amount_of_packets, data_size, crc, data


def get_crc_value(tag, amount_of_packets, data_size, data):
    header = struct.pack("!BII", tag, amount_of_packets, data_size)
    return binascii.crc_hqx(header + data, 0)
