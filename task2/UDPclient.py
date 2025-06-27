# UDPclient.py
import socket
import struct
import time
import random
import threading
import pandas as pd
from common import Packet, TYPE_SYN, TYPE_ACK, TYPE_DATA, TYPE_FIN, HEADER_FORMAT, HEADER_SIZE
import sys
#python UDPclient.py 192.168.71.128 1200

class UDPClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.settimeout(0.1)  # 非阻塞读取

        # 连接状态
        self.is_connected = False
        self.seq_num = 0  # 初始序列号，也是下一个要发送的包的序列号
        self.ack_num = 0   #先暂时放着
        self.acknowledged_seq = 0  # 最后一个被确认的包的序列号
        self.send_window_size = 400  #窗口大小(字节)
        self.max_packet_size = 80  # 最大数据包大小(字节)
        self.min_packet_size = 40  # 最小数据包大小(字节)
        self.packets = [None] * 31  # 数据包列表(元组列表)，存储 (data, beg_byte, end_byte, timestamp, sent_time, size)

        # RTT 统计
        self.rtt_samples = []
        self.max_rtt = 0
        self.min_rtt = float('inf')
        self.avg_rtt = 0
        self.rtt_std = 0

        # 丢包统计
        self.total_sent_packets = 0
        self.required_packets = 30  # 需要发送的数据包总数
        self.acknowledged_packets = 0

        # 超时时间(ms)
        self.estimated_rtt=0   #估计RTT
        self.dev_rtt=0   #RTT偏差
        self.timeout = 300
        self.adjusted_timeout = self.timeout

    def connect(self):
        """模拟TCP三次握手建立连接"""
        print("正在尝试连接到服务器...")

        max_retries=3   #最多尝试连接3次
        for attempt in range(max_retries):
            # 第一次握手：发送SYN
            syn_packet = Packet(flags=TYPE_SYN, seq_num=self.seq_num)
            self.client_socket.sendto(syn_packet.pack(), (self.server_ip, self.server_port))
            print(f"发送SYN: seq={self.seq_num}")

            # 等待SYN-ACK
            try:
                data, server_addr = self.client_socket.recvfrom(1024)
                packet = Packet.unpack(data)
                #print(f"{packet.flags} {TYPE_SYN | TYPE_ACK} {packet.ack_num} {self.seq_num}")

                if (packet.flags == (TYPE_SYN | TYPE_ACK)) and (packet.ack_num == (self.seq_num + 1)):
                    print(f"收到SYN-ACK：ack={packet.ack_num}")

                    # 第三次握手：发送ACK
                    ack_packet = Packet(
                        flags=TYPE_ACK,
                        seq_num=self.seq_num,
                        ack_num=self.ack_num
                    )
                    self.client_socket.sendto(ack_packet.pack(), (self.server_ip, self.server_port))
                    print(f"发送握手ACK：seq={self.seq_num}")
                    self.acknowledged_seq = packet.seq_num  # 0
                    self.seq_num += 1  # 1

                    self.is_connected = True   #成功建立连接
                    print("与服务器建立连接成功")
                    return True

            except Exception as e:
                print(f"连接过程中出现异常：{e}")
                continue

        print("连接服务器失败")
        return False

    def prepare_packets(self):
        """准备30个数据包并计算字节位置"""
        current_byte = 1  # 第一个字节位置是1

        for i in range(self.required_packets):   #下标是1-30
            packet_size = random.randint(self.min_packet_size, self.max_packet_size)
            data = b"d" * packet_size   #构造 40-80B 随机大小的数据

            # 计算字节位置
            start_byte = current_byte
            end_byte = current_byte + packet_size - 1

            #(data, beg_byte, end_byte, timestamp, sent_time, size) 时间戳和发送时间还没定
            self.packets[i+1] = (data, start_byte, end_byte, None, None, packet_size)
            #print(f"结束字节：{self.packets[i+1][2]}")
            current_byte = end_byte + 1  # 下一个包的起始位置

        self.packets[0]=(None,None,0,None,None,None)   #设置起始位置

    def send_data(self):
        """发送数据，实现可靠传输"""
        if not self.is_connected:
            print("尚未建立连接")
            return

        # 准备数据包
        self.prepare_packets()

        # 启动超时重传线程
        timeout_thread = threading.Thread(target=self._timeout_retransmit)
        timeout_thread.daemon = True
        timeout_thread.start()

        # 发送数据
        while self.acknowledged_seq < self.required_packets:
            # 检查窗口是否有空间：当前包的end_byte <= 最后确认包的end_byte + 窗口大小
            #当前包序列号 <= 30
            #print(f"------------------序列号：{self.seq_num} 窗口伸多远：{self.packets[self.acknowledged_seq][2] + self.send_window_size} 结束位置：{self.packets[self.seq_num][2]}--------------------")
            if self.seq_num <= self.required_packets and self.packets[self.seq_num][2] < self.packets[self.acknowledged_seq][2] + self.send_window_size:
                # 获取要发送的数据包
                index = self.seq_num
                data, start_byte, end_byte, _, _, size = self.packets[index]
                timestamp = int(time.time() * 1000)  # 毫秒时间戳

                # 创建数据包
                packet = Packet(
                    flags=TYPE_DATA,
                    seq_num=index,   #序列号就是包的索引
                    ack_num=index+1,   #感觉不太重要
                    data=data,
                    #data_len=size,
                    timestamp=timestamp,
                )

                # 发送数据包
                self.client_socket.sendto(packet.pack(), (self.server_ip, self.server_port))
                self.total_sent_packets += 1

                # 更新数据包的发送状态 补充上时间戳和发送时间
                self.packets[index] = (data, start_byte, end_byte, timestamp, time.time(), size)

                # 打印发送信息
                print(f"第{index}个数据包({start_byte}-{end_byte}字节，共{size}字节)已发送")

                # 更新下一个要发送的序列号
                self.seq_num += 1

            # 接收服务器响应
            try:
                data, server_addr = self.client_socket.recvfrom(1024)
                self._handle_response(data)   #发完就等着接收响应？
            except socket.timeout:
                # 超时由专门的线程处理
                continue

        #所有包都被确认过了
        #关闭连接
        self.close()

        # 打印统计信息
        self._print_statistics()

    def _handle_response(self, data):
        """处理服务器响应"""
        packet = Packet.unpack(data)

        if packet.flags & TYPE_ACK:
            # 服务器回复的ack是下一个希望收到的序列号，客户端的acknowledged_seq是最后一个被确认的
            ack_seq = packet.ack_num-1

            #是不是第一次来的ACK
            if ack_seq > self.acknowledged_seq and ack_seq < self.seq_num:
                # 计算RTT
                if self.packets[ack_seq][4]:  # 如果该包已发送
                    sent_time = self.packets[ack_seq][4]
                    #print(f"当前时间：{time.time()} 发送时间：{sent_time}")
                    rtt = (time.time() - sent_time) * 1000  # 来回一趟的时间(毫秒)
                    self.rtt_samples.append(rtt)

                    # 更新RTT统计
                    self.max_rtt = max(self.max_rtt, rtt)
                    self.min_rtt = min(self.min_rtt, rtt)

                    # 调整超时时间
                    if self.estimated_rtt==0:
                        self.estimated_rtt=rtt
                    else:
                        self.estimated_rtt=0.875*self.estimated_rtt+0.125*rtt

                    if self.dev_rtt==0:
                        self.dev_rtt=rtt/2
                    else:
                        self.dev_rtt=0.75*self.dev_rtt+0.25*rtt

                    self.adjusted_timeout = self.estimated_rtt+4*self.dev_rtt

                    # 打印确认信息
                    _, start_byte, end_byte, _, _, size = self.packets[ack_seq]
                    print(f"第{ack_seq}个数据包({start_byte}-{end_byte}，共{size}字节)Server端已收到，RTT: {rtt:.2f} ms")

                # 更新已确认的序列号
                self.acknowledged_seq = ack_seq
                self.acknowledged_packets = ack_seq + 1  # 这他妈啥

    def _timeout_retransmit(self):
        """超时重传线程 - 实现N步回退"""
        while self.acknowledged_seq < self.required_packets:
            current_time = time.time()
            earliest_timeout_seq = None

            # 遍历查找最早的超时包
            for seq in range(self.acknowledged_seq + 1, self.seq_num):
                _, _, _, timestamp, sent_time, _ = self.packets[seq]

                if sent_time and (current_time - sent_time) * 1000 > self.adjusted_timeout:
                    if earliest_timeout_seq is None or seq < earliest_timeout_seq:
                        earliest_timeout_seq = seq   #找到了
                        break

            # 如果找到超时包，回退seq_num并重传
            if earliest_timeout_seq is not None:
                print(f"检测到超时，最早超时包序列号: {earliest_timeout_seq}")

                # 回退seq_num到最早超时包的序列号
                self.seq_num = earliest_timeout_seq

                # 重传该包
                data, start_byte, end_byte, timestamp, _, size = self.packets[earliest_timeout_seq]
                packet = Packet(
                    flags=TYPE_DATA,
                    seq_num=earliest_timeout_seq,
                    ack_num=earliest_timeout_seq+1,
                    data=data,
                    #data_len=size,
                    timestamp=timestamp,
                )

                self.client_socket.sendto(packet.pack(), (self.server_ip, self.server_port))
                self.total_sent_packets += 1

                print(f"重传第{earliest_timeout_seq}个数据包({start_byte}-{end_byte}字节，共{size}字节)")

                # 更新发送时间
                self.packets[earliest_timeout_seq] = (data, start_byte, end_byte, timestamp, current_time, size)

            time.sleep(0.1)  # 避免CPU占用过高

    #关闭连接
    def close(self):
        print("正在尝试关闭连接...")

        #发送FIN (第一次挥手)
        fin_packet = Packet(flags=TYPE_FIN, seq_num=self.seq_num, ack_num=self.ack_num)
        self.client_socket.sendto(fin_packet.pack(), (self.server_ip, self.server_port))
        print(f"发送FIN: seq={self.seq_num}, ack={self.ack_num}")

        #等待FIN-ACK (第二次挥手)
        while True:
            #self.client_socket.settimeout(1.0)   #设置超时时间为1秒
            data, server_addr = self.client_socket.recvfrom(1024)
            packet = Packet.unpack(data)
            if packet.flags == (TYPE_ACK | TYPE_FIN) and packet.ack_num == self.seq_num + 1:
                print(f"收到FIN+ACK: ack={packet.ack_num}")
                break

        # 等待FIN (第三次挥手)
        while True:
            # self.client_socket.settimeout(1.0)   #设置超时时间为1秒
            data, server_addr = self.client_socket.recvfrom(1024)
            fin_packet = Packet.unpack(data)
            if fin_packet.flags == TYPE_FIN:
                print(f"收到FIN: seq={fin_packet.seq_num}")
                break

        # 发送ACK (第四次挥手)
        ack_packet = Packet(flags=TYPE_ACK, seq_num=self.seq_num + 1, ack_num=fin_packet.seq_num + 1)
        self.client_socket.sendto(ack_packet.pack(), (self.server_ip, self.server_port))
        print(f"发送挥手ACK: ack={ack_packet.ack_num}")

        self.is_connected = False
        self.client_socket.close()
        print("连接已关闭")


    def _print_statistics(self):
        """打印统计信息"""
        if self.rtt_samples:
            # 使用pandas计算标准差
            rtt_series = pd.Series(self.rtt_samples)
            self.rtt_std = rtt_series.std()
            self.avg_rtt = rtt_series.mean()

        print("\n【汇总】")
        loss_rate = (1 - self.required_packets / self.total_sent_packets) * 100
        print(f"丢包率: {loss_rate:.2f}%")
        print(f"最大RTT: {self.max_rtt:.2f} ms")
        print(f"最小RTT: {self.min_rtt:.2f} ms")
        print(f"平均RTT: {self.avg_rtt:.2f} ms")
        print(f"RTT标准差: {self.rtt_std:.2f} ms")
        print(f"实际发送的UDP数据包数: {self.total_sent_packets}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("运行程序的正确格式: python UDPclient.py <SERVER_IP> <SERVER_PORT>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    client = UDPClient(server_ip, server_port)
    if client.connect():
        client.send_data()