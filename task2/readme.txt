Reliable UDP File Transfer - 程序说明文档

1. 项目简介
本项目实现了一个基于UDP协议的可靠文件传输系统，模拟TCP的三次握手和四次挥手过程，实现了数据包的可靠传输、流量控制和拥塞控制。主要用于演示如何在UDP上实现可靠传输机制。

2. 运行环境
操作系统: Windows/Linux/macOS
Python版本: 3.6及以上
依赖库:
必需: socket, struct, threading, time, random
可选: pandas（用于统计信息输出）

3. 文件说明
udpclient.py: 客户端程序
udpserver.py: 服务器程序
common.py: 公共协议定义文件

4. 使用步骤
(1) 启动服务器：
python udpserver.py <端口>
示例：python udpserver.py 1200

(2) 运行客户端：
python udpclient.py <服务器IP> <端口>
示例：python udpclient.py 192.168.1.100 1200

(3) 传输过程：
客户端会自动生成测试数据（30个40-80字节的数据包）
服务器会接收数据并返回确认
传输完成后自动断开连接

(4) 查看结果：
客户端会显示每个数据包的传输状态和RTT时间
传输结束后会显示统计信息（丢包率、RTT等）

5. 配置说明
服务器配置：
默认监听所有接口（0.0.0.0）
可通过参数指定监听端口
默认丢包率10%（可在代码中修改loss_rate参数）

客户端配置：
窗口大小：默认400字节（可在代码中修改send_window_size）
数据包大小：40-80字节随机（可在代码中修改min/max_packet_size）
超时时间：动态调整（基于RTT估计）

6. 协议说明
使用自定义协议头格式（见common.py）
支持四种控制标记：SYN/ACK/DATA/FIN
实现类TCP的序列号确认机制
支持累计确认和重复ACK
实现动态超时重传（基于RTT估计）