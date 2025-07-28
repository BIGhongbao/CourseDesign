# 计算机网络课程设计 TCP/UDP协议传输
北京林业大学2025第2学期计算机网络课程设计，模拟TCP和UDP协议传输。
本项目是计算机网络课程设计的综合实现，包含两个主要子任务：

- **Task 1：基于 TCP 的文本反转服务**
- **Task 2：基于 UDP 的可靠数据传输模拟**

通过该项目，展示了 **Socket 编程、TCP/UDP 协议实现、可靠传输机制、超时重传、流量控制、拥塞控制** 等核心知识点。

---

## 📂 项目结构
```
CourseDesign/
├── task1/ # TCP 文本反转任务
│ ├── TCPclient.py # TCP 客户端
│ ├── TCPserver.py # TCP 服务器
│ └── readme.txt # 子任务task1说明文档
│
├── task2/ # UDP 可靠传输任务
│ ├── UDPclient.py # UDP 客户端
│ ├── UDPserver.py # UDP 服务器
│ ├── readme.txt # 子任务task2说明文档
│ └── common.py # UDP 公共协议头定义
│
└── README.md # 总体项目说明（本文件）
```

---

## 🚀 功能概述

### ✅ Task 1: Reverse TCP Text Processor
- 基于 **TCP** 协议的文本反转服务。
- 客户端将文本分块后逐块发送至服务器，服务器返回反转块，客户端拼接生成最终反转文本。
- 演示了 **TCP Socket 编程、消息分块与重组**。

### ✅ Task 2: Reliable UDP Transfer
- 基于 **UDP** 的可靠数据传输，模拟 **TCP 三次握手、四次挥手**。
- 实现了 **自定义协议头、序列号/确认机制、RTT 动态超时估计、超时重传、累计确认与重复 ACK**。
- 支持 **丢包模拟（loss_rate 可调）、窗口流量控制、统计 RTT 及丢包率**。

---

## 🛠️ 运行环境

- **操作系统**：Windows / Linux / macOS  
- **Python 版本**：3.6+  
- **依赖库**：
  - 标准库：`socket`、`struct`、`threading`、`random`、`sys`、`time`
  - 第三方：`pandas`（可选，用于 RTT 统计）

---

## ⚙️ 可配置参数

### TCP
- **服务器监听地址**：默认 `127.0.0.1:8888`
- **客户端分块长度**：
  - `<最小分块长度>`：建议 ≥ 2  
  - `<最大分块长度>`：建议 ≤ 10  

### UDP
- **丢包率**：  
  - 默认 `10%`（可在 `UDPserver.py` 中通过 `loss_rate` 参数修改）
  
- **发送窗口大小**：  
  - 默认 `400` 字节（可在 `UDPclient.py` 中 `send_window_size` 调整）
  
- **数据包大小**：  
  - 默认 `40–80` 字节随机（在 `UDPclient.py` 中的 `min_packet_size` 和 `max_packet_size` 可改）
  
- **超时时间**：  
  - 动态调整，基于 RTT 平滑估计（`UDPclient.py` 内部自动计算）

---

## 📊 示例输出

### TCP 客户端
```text
第1块：olleH
第2块：tenretnI
...
反转后的文本为：
gnimargorP krowteN olleH
```

### UDP 客户端
```text
第1个数据包(1-62字节，共62字节)已发送
Server端确认第1个包，RTT=25.4ms
...
【汇总】
丢包率: 3.33%
平均RTT: 26.7ms
RTT标准差: 4.1ms
```
