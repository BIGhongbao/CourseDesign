Reverse TCP Text Processor - 程序说明文档

1. 项目简介
本项目是一个基于TCP协议的文本反转服务。客户端将文本分块发送给服务器，服务器逐块反转后返回结果。主要用于演示TCP Socket编程和网络协议设计。

2. 运行环境
操作系统: Windows/Linux/macOS
Python版本: 3.6及以上
依赖库: socket, struct, threading, random, sys（均为Python标准库）

3. 文件说明
reversetcpclient.py: 客户端程序
reversetcpserver.py: 服务器程序
tcp_input.txt: 客户端输入文本文件（需手动创建）
tcp_output.txt: 客户端输出文本文件（程序自动生成）

4. 使用步骤
(1) 准备输入文件：
创建tcp_input.txt文件并写入要反转的文本内容

(2) 启动服务器：
python reversetcpserver.py

(3) 运行客户端：
python reversetcpclient.py <服务器IP> <端口> <最小分块长度> <最大分块长度>
示例：python reversetcpclient.py 127.0.0.1 8888 2 10

(4) 查看结果：
客户端命令行会显示每块的反转结果
最终结果保存在tcp_output.txt中

5. 配置说明
服务器默认监听127.0.0.1:8888

客户端参数：
<服务器IP>: 要连接的服务器地址
<端口>: 服务器监听端口
<最小分块长度>: 建议≥2
<最大分块长度>: 建议≤10