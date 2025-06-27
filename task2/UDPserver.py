# UDPserver.py
import socket
import struct
import time
import random
import threading
from common import Packet, TYPE_SYN, TYPE_ACK, TYPE_DATA, TYPE_FIN, HEADER_FORMAT, HEADER_SIZE

class UDPServer:
    def __init__(self, server_port, loss_rate=0.1):
        self.server_port = server_port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(("", server_port))
        self.client_address = None
        self.is_connected = False
        self.seq_num = 0  # 初始序列号
        self.ack_num = 0
        self.expected_seq_num = 0  # 期望接收的序列号
        self.loss_rate = loss_rate  # 丢包率
        self.received_data = b""  # 接收的数据
        self.received_packets = 0  # 已接收的数据包数
        self.required_packets = 30  # 需要接收的数据包总数
        self.buffer={}   #字典型缓冲区
        self.tot_byte=0

        # 启动接收线程
        self.running = True
        self.receive_thread = threading.Thread(target=self._receive_packets)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        print(f"UDP服务器已启动，监听端口 {server_port}")   #创建即启动

    #数据包接收线程
    def _receive_packets(self):
        #连接建立阶段
        while not self.is_connected:
            try:
                data, client_addr = self.server_socket.recvfrom(1024)

                # 首次接收数据，记录客户端地址
                if not self.client_address:
                    self.client_address = client_addr
                    print(f"收到来自 {client_addr} 的连接请求")

                # 处理SYN包
                packet = Packet.unpack(data)
                if packet.flags == TYPE_SYN and not self.is_connected:
                    print(f"收到SYN: seq={packet.seq_num}")

                    # 发送SYN-ACK
                    syn_ack_packet = Packet(
                        flags=TYPE_SYN | TYPE_ACK,
                        seq_num=self.seq_num,
                        ack_num=1,
                    )
                    self.server_socket.sendto(syn_ack_packet.pack(), client_addr)
                    print(f"发送SYN-ACK: ack={packet.seq_num + 1}")
                    self.seq_num+=1   #1
                    self.expected_seq_num = 1  # 期望接收数据包1

                    # 收到第三次握手ACK
                    while not self.is_connected:
                        data, client_addr = self.server_socket.recvfrom(1024)
                        packet = Packet.unpack(data)
                        if packet.flags & TYPE_ACK:
                            print(f"收到ACK: seq={packet.seq_num}")
                            self.is_connected = True  # 彻底建立连接
                            print("与客户端成功建立连接")

            except Exception as e:
                if self.running:
                    print(f"建立连接时出错: {e}")

        #数据传输阶段
        while self.running:
            time.sleep(0.01)   #手动设置一个时延，要不然RTT趋近于0了
            try:
                #接收数据包
                data, client_addr = self.server_socket.recvfrom(1024)

                #模拟丢包
                if random.random() < self.loss_rate:
                    print(f"模拟丢包: 丢弃来自 {client_addr} 的数据包，其序列号为{Packet.unpack(data).seq_num}")
                    continue

                #处理数据包
                self._handle_packet(data, client_addr)

            except Exception as e:
                if self.running:
                    print(f"接收数据包时出错: {e}")

    #数据包处理函数
    def _handle_packet(self, data, client_addr):
        packet = Packet.unpack(data)

        # 处理FIN包 (连接断开)
        if packet.flags & TYPE_FIN and self.is_connected:
            print(f"收到FIN: seq={packet.seq_num}")   #31

            # 发送FIN-ACK
            fin_ack_packet = Packet(
                flags=TYPE_ACK | TYPE_FIN,
                ack_num=packet.seq_num + 1   #32
            )
            self.server_socket.sendto(fin_ack_packet.pack(), client_addr)
            print(f"发送FIN-ACK: ack={packet.seq_num + 1}")

            # 发送FIN (第三次挥手)
            fin_packet=Packet(
                flags=TYPE_FIN,
                seq_num=self.seq_num   #1 前面只发过一个FIN+ACK包，占用序列号0
            )
            self.server_socket.sendto(fin_packet.pack(), client_addr)
            print(f"发送FIN: seq={self.seq_num}")
            self.seq_num+=1

            # 接收ACK (第四次挥手)
            while self.is_connected:
                data, client_addr = self.server_socket.recvfrom(1024)
                packet = Packet.unpack(data)
                if packet.flags & TYPE_ACK:
                    print(f"收到ACK：ack={packet.ack_num}")
                    self.is_connected = False  # 彻底断开连接
                    self.running = False  # 结束线程
                    print("与客户端成功断开连接")
                    self.server_socket.close()  # 关闭套接字
                    self.client_address = None
                    print("UDP服务器已停止")

        # 处理数据包
        elif packet.flags == TYPE_DATA and self.is_connected:
            self.buffer[packet.seq_num]=packet.data   #存入缓冲区

            if packet.seq_num == self.expected_seq_num:
                #接收到期望数据包
                self.received_data += packet.data
                start_byte=self.tot_byte+1
                end_byte=start_byte+packet.data_len-1
                print(f"收到第{packet.seq_num}个({start_byte}-{end_byte}字节)数据包")

                #累计确认
                while self.expected_seq_num in self.buffer:
                    self.tot_byte+=len(self.buffer[self.expected_seq_num])   #累计字节数
                    self.expected_seq_num+=1

                # 发送ACK
                ack_packet = Packet(
                    flags=TYPE_ACK,
                    ack_num=self.expected_seq_num
                )
                self.server_socket.sendto(ack_packet.pack(), client_addr)
                print(f"发送ACK: ack={self.expected_seq_num}")

            else:
                #接收到失序包，发送重复ACK
                print(f"收到失序包: 期望 seq={self.expected_seq_num}, 实际 seq={packet.seq_num}")
                ack_packet = Packet(
                    flags=TYPE_ACK,
                    ack_num=self.expected_seq_num
                )
                self.server_socket.sendto(ack_packet.pack(), client_addr)
                print(f"发送重复ACK: ack={self.expected_seq_num}")

    def stop(self):
        """停止服务器"""
        self.running = False
        if self.receive_thread.is_alive():
            self.receive_thread.join()
        self.server_socket.close()


if __name__ == "__main__":
    server_port = 1200
    server = UDPServer(server_port)

    try:
        #保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()