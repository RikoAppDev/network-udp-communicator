import binascii
import os
import re
import struct
from timeit import default_timer as timer

import keyboard


def select_mode():
    mode = input("\n⚙️ Choose operation mode: 📡 RECEIVER ➡ 1️⃣ | 📨 SENDER ➡ 2️⃣ >> ").strip()
    while mode != "1" and mode != "2":
        print(f"‼️ Error ‼️\n\t- Incorrect operation mode")
        mode = input("\n⚙️ Choose operation mode: 📡 RECEIVER ➡ 1️⃣ | 📨 SENDER ➡ 2️⃣ >> ").strip()

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

        if port.strip().isdigit():
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
        ).strip()
        if task in ["1", "2", "3", "4"]:
            return task
        else:
            print(f"‼️ Error ‼️\n\t- Unsupported task")


def handle_fragment_size_input():
    while True:
        size = input("📏 Input fragment size (max 1467 B) >> ").strip()

        # 1500 - 20 - 8 - 5 = 1467
        if size.upper() in ["MAX", "M"]:
            return 1467
        elif size.isdigit():
            if 0 < int(size) <= 1467:
                return int(size)
            else:
                print(f"‼️ Error ‼️\n\t- Fragment size is out of range (1 - 1467)")
        else:
            print(f"‼️ Error ‼️\n\t- Fragment size must be a number")


def handle_error_sim_input():
    while True:
        error_probability = input("🎲 Choose percentual error probability >> ").strip()

        if error_probability.isdigit():
            if 0 <= int(error_probability) <= 80:
                return int(error_probability)
            else:
                print(f"‼️ Error ‼️\n\t- Error probability is out of range (0 - 80)")
        else:
            print(f"‼️ Error ‼️\n\t- Error probability must be a number")


def handle_show_progress():
    while True:
        progress = input("⌛ Do you want to show progress bar instead log? >> ")

        if progress.lower().strip() in ["y", "yes", "1"]:
            return True
        else:
            return False


# Finds file between project structure
def find_file(file_name):
    directory = os.path.dirname(os.path.abspath(__file__ or ''))

    file_paths = []
    for root, dirs, files in os.walk(directory):
        if file_name in files:
            file_paths.append(os.path.join(root, file_name))
    return file_paths


# Sets file name
def get_file(file):
    file_paths = find_file(file)
    if len(file_paths) > 1:
        print("⚠️ WARNING ⚠️\n\t- File found at the following locations within your project structure:")
        for path in file_paths:
            print("\t\t-", path)
        print("\t- Make sure there are no file name duplicates! For now we selected first found!")
        return True, file_paths[0]
    elif len(file_paths) == 1:
        return True, file_paths[0]

    return False, None


def handle_file_path_input():
    while True:
        file = input("📂 Input filename >> ").strip()
        found, file_path = get_file(file)

        if found:
            return file_path
        else:
            print(f"‼️ Error ‼️\n\t- File {file} not found within your project structure!")


def stream_data_into_file(path, filename, data_to_stream):
    with open(path + filename, 'wb') as file:
        try:
            file.write(data_to_stream)
            file.close()
            print(f'\rData has been successfully streamed to {filename}')

            print(f"\n🗃️ File location is '{os.path.abspath(path + filename)}'")
            print(f"📏 File size: {len(data_to_stream)}B \n")
        except Exception as exc:
            print(f'\r‼️ Error ‼️\n\t- While streaming data to {filename}, error: {exc}!!!')


def format_address(address):
    return f"'{address[0]}:{address[1]}'"


def open_data(header_data):
    flags, seq_number, crc = struct.unpack('!BHH', header_data[:5])
    data = header_data[5:]
    return flags, seq_number, crc, data


def get_crc_value(flags, seq_number, data):
    header = struct.pack("!BH", flags, seq_number)
    return binascii.crc_hqx(header + data, 0)


def contain_flags(flags, flags_to_check):
    if flags is None:
        return False

    flag_positions = {
        'E': 7,
        'T': 6,
        'F': 5,
        'A': 4,
        'R': 3,
        'S': 2,
        'Q': 1,
        'K': 0,
    }

    for flag in flags_to_check:
        position = flag_positions.get(flag)
        if not (flags & (1 << position)):
            return False

    return True


def match_flags(flags, flags_to_match):
    flag_positions = {
        'E': 7,
        'T': 6,
        'F': 5,
        'A': 4,
        'R': 3,
        'S': 2,
        'Q': 1,
        'K': 0,
    }

    # Convert the flags_to_match string into a set of flag positions
    positions_to_match = {flag_positions[flag]: flag for flag in flags_to_match}

    # Check if the specified flags are present and others are absent
    return all((flags & (1 << position)) != 0 if position in positions_to_match else (flags & (1 << position)) == 0 for
               position in flag_positions.values())


def print_error_connection_reset(device=1):
    if device:
        print(f"\n‼️ Error ‼️\n\t- RECEIVER is not alive anymore")
    else:
        print(f"\n‼️ Error ‼️\n\t- SENDER is not alive anymore")


def print_error_timout(device=1):
    if device:
        print(f"\r‼️ Error ‼️\n\t- RECEIVER is not responding")
    else:
        print(f"\r‼️ Error ‼️\n\t- SENDER is not responding")


def handle_wait_for_server_setup():
    start = timer()
    print(
        f"Wait some time to setup the RECEIVER or press SPACE key to try connect now..."
    )
    while timer() - start < 30:
        print(f"\rConnecting in {30 - int(timer() - start)}s", end="")

        if keyboard.is_pressed("space"):
            break


def get_file_save_path():
    default_path = "./received_files"

    while True:
        user_input = input(
            f"🗃️ Input the directory to save the file (ENTER key for default: './received_files') >> "
        ).strip()

        if user_input == "":
            user_input = default_path

        if not user_input.endswith("/"):
            user_input += "/"

        if not os.path.exists(user_input):
            os.makedirs(user_input)

        if os.path.isdir(user_input):
            return user_input
        else:
            print("\r‼️ Error ‼️\n\t- Invalid path. Please enter a valid directory.")
