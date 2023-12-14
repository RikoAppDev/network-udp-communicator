"""
-----------------------------------------------
Flags (ETFARQSK) 8bit - 1Byte
-----------------------------------------------
E (1 = Establish connection. Are you alive?)
T (1 = Text message)
F (1 = File transfer)
A (1 = Acknowledge packet)
R (1 = Retransmit packet)
Q (1 = Quit/Fin comm)
S (1 = Swap modes)
K (1 = Keep alive)
-----------------------------------------------
"""
import binascii
import struct


class DataHeader:
    def __init__(self, tags, data, seq_number):
        self.flags = self.create_flags_byte(tags)
        self.data = data
        self.seq_number = seq_number

    def pack_data(self, error_sim=False):
        header = struct.pack("!BH", int.from_bytes(self.flags, byteorder='big'), self.seq_number)
        crc = binascii.crc_hqx(header + self.data, 0)
        if error_sim:
            crc = self.simulate_crc_error(crc, 2)
        header += struct.pack("!H", crc)

        return header + self.data

    @staticmethod
    def simulate_crc_error(crc, num_bits_to_flip):
        bitmask = (1 << num_bits_to_flip)
        return crc ^ bitmask

    @staticmethod
    def create_flags_byte(flags):
        flags_byte = 0

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

        for flag in flags:
            position = flag_positions.get(flag)
            flags_byte |= 1 << position

        return bytes([flags_byte])
