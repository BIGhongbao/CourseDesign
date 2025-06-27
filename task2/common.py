# common.py 修正版
import struct
import time

# 调整协议首部格式，扩展时间戳为8字节
HEADER_FORMAT = "!BHIQH"  # !:网络字节序, B:flags, H:seq_num, I:ack_num, Q:timestamp, H:data_len
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

TYPE_SYN = 0x01
TYPE_ACK = 0x02
TYPE_DATA = 0x04
TYPE_FIN = 0x08  # 2^x，方便组合标记


class Packet:
    def __init__(self, flags=0, seq_num=0, ack_num=0, data=b"", timestamp=0):
        self.flags = flags
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.data = data
        self.data_len = len(data)
        self.timestamp = timestamp

    # 打包
    def pack(self):
        header = struct.pack(
            HEADER_FORMAT,
            self.flags,
            self.seq_num,
            self.ack_num,
            self.timestamp,
            self.data_len,
        )
        return header + self.data

    # 解包
    @staticmethod
    def unpack(data):
        header = data[:HEADER_SIZE]  # 切片分离首部和数据
        payload = data[HEADER_SIZE:]
        flags, seq_num, ack_num, timestamp, data_len = struct.unpack(HEADER_FORMAT, header)
        return Packet(flags, seq_num, ack_num, payload, timestamp)