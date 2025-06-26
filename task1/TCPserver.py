import socket
import struct
import threading

#定义一些常量
TYPE_INIT=1
TYPE_AGREE=2
TYPE_REQUEST=3
TYPE_ANSWER=4
HEADER_FORMAT="!HI"
HEADER_LEN=6
SERVER_IP="127.0.0.1"
SERVER_PORT=8888

#客户处理函数
def handle_client(client_socket:socket.socket):
    try:
        #接收initialization
        init=client_socket.recv(HEADER_LEN)
        if len(init)!=HEADER_LEN:
            print("initialization首部长度出错")
            return

        type,n=struct.unpack(HEADER_FORMAT,init)
        if type!=TYPE_INIT:
            print("initialization首部type字段出错")
            return

        #回复agree
        agree=struct.pack("!H",TYPE_AGREE)
        client_socket.sendall(agree)

        #循环接收数据
        for _ in range(n):
            #接收request
            header=client_socket.recv(HEADER_LEN)
            if len(header)!=HEADER_LEN:
                print("request首部长度出错")
                return

            data_type,data_len=struct.unpack(HEADER_FORMAT,header)
            if data_type!=TYPE_REQUEST:
                print("request首部type字段出错")
                return

            data=client_socket.recv(data_len)
            if len(data)!=data_len:
                print("request数据部分长度出错")
                return

            #切片反转
            reversed_data=data[::-1]

            #回复answer
            answer=struct.pack(HEADER_FORMAT,TYPE_ANSWER,data_len)+reversed_data
            client_socket.sendall(answer)
    except Exception as e:
        print(f"出现异常：{e}")
        return

if __name__=="__main__":
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as server_socket:
        #创建服务器套接字
        server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        server_socket.bind((SERVER_IP,SERVER_PORT))
        #开始监听
        server_socket.listen(5)
        while True:
            client_socket,addr=server_socket.accept()
            print(f"新客户端连接：{addr}")
            #用线程管理每个客户端
            client_thread=threading.Thread(target=handle_client,args=(client_socket,))
            client_thread.start()

            