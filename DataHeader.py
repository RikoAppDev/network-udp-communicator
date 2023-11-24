"""
TAGS:
are you alive? > 2
are you alive? ACK > 1

text message > 3
file transfer > 4
ACK > 5
retransmit packet > 0

swap modes > 6
fin comm > 7

keep alive > 8
keep alive ACK > 9
"""
import binascii
import struct


class DataHeader:
    tag: int
    data_size: int
    data: bytes
    amount_of_packets: int

    def __init__(self, tag, data, amount_of_packets):
        self.tag = tag
        self.data_size = len(data)
        self.data = data
        self.amount_of_packets = amount_of_packets

    def pack_data(self, error_sim=False):
        header = struct.pack("!BII", self.tag, self.amount_of_packets, self.data_size)
        crc = binascii.crc_hqx(header + self.data, 0)
        if error_sim:
            crc = self.simulate_crc_error(crc, 2)
        header += struct.pack("!H", crc)

        return header + self.data

    @staticmethod
    def simulate_crc_error(crc, num_bits_to_flip):
        bitmask = (1 << num_bits_to_flip)
        return crc ^ bitmask
