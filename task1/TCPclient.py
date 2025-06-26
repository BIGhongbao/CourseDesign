import socket
import struct
import threading
import random
import sys

TYPE_INIT=1
TYPE_AGREE=2
TYPE_REQUEST=3
TYPE_ANSWER=4
HEADER_FORMAT="!HI"
HEADER_LEN=6
SERVER_IP="127.0.0.1"   #先默认着
SERVER_PORT=8888
MIN_LEN=2
MAX_LEN=10
#python TCPclient.py 127.0.0.1 8888 2 10
#python TCPclient.py 192.168.71.128 8888 2 10

#分块函数
def get_blocks(text:str,min_len:int,max_len:int)->list[bytes]:
    blocks=[]
    pos=0
    tot_len=len(text)

    while pos<tot_len:
        block_len=random.randint(min_len,max_len)
        if pos+block_len>tot_len:
            block_len=tot_len-pos
        blocks.append(text[pos:pos+block_len].encode())
        pos+=block_len

    return blocks

def send_text():
    try:
        #读取文本
        with open('tcp_input.txt', 'r', encoding='utf-8') as file:
            text = file.read()

        blocks = get_blocks(text, MIN_LEN, MAX_LEN)
        n = len(blocks)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.connect((SERVER_IP, SERVER_PORT))

            # 发送initialization
            init = struct.pack(HEADER_FORMAT, TYPE_INIT, n)
            server_socket.sendall(init)

            # 接收agree
            agree = server_socket.recv(2)
            type = struct.unpack("!H", agree)[0]

            if len(agree) != 2:
                print("initialization首部长度出错")
                return
            if type != TYPE_AGREE:
                print("initialization首部类型出错")
                return

            # 逐块发request
            reversed_list = []
            for i, block in enumerate(blocks):
                request = struct.pack(HEADER_FORMAT, TYPE_REQUEST, len(block)) + block
                server_socket.sendall(request)

                # 接收answer
                header = server_socket.recv(HEADER_LEN)
                if len(header) != HEADER_LEN:
                    print("answer首部长度出错")
                    return

                type, data_len = struct.unpack(HEADER_FORMAT, header)
                if type != TYPE_ANSWER:
                    print("answer首部类型出错")
                    return

                reversed_data = server_socket.recv(data_len)
                if len(reversed_data) != data_len:
                    print("answer数据长度出错")
                    return
                reversed_list.append(reversed_data)

                # 命令行输出
                print(f"第{i + 1}块：{reversed_data.decode()}")

            reversed_text = b"".join(reversed(reversed_list)).decode()
            print(f"反转后的文本为：\n{reversed_text}")

            #写入文件
            with open('tcp_output.txt', 'w', encoding='utf-8') as file:
                file.write(reversed_text)

    except FileNotFoundError:
        print("未找到tcp_input.txt文件")
        return
    except Exception as e:
        print(f"发生错误：{e}")
        return

if __name__=="__main__":
    if len(sys.argv) != 5:
        print("运行程序的正确格式: python TCPclient.py <SERVER_IP> <SERVER_PORT> <MIN_LEN> <MAX_LEN>")
        sys.exit(1)

    SERVER_IP=sys.argv[1]
    SERVER_PORT=int(sys.argv[2])
    MIN_LEN=int(sys.argv[3])
    MAX_LEN=int(sys.argv[4])

    send_text()