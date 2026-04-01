# 12_地平线 RDK-X5 具身智能实战指南：从边缘感知到云边协同大模型

如果你手里有一块 **地平线 RDK-X5**，恭喜你，你拥有了目前国内机器人开发者生态最好、最具性价比的边缘计算板之一。

RDK-X5 搭载了约 **5 TOPS 算力的 BPU（伯努利 2.0 架构）**，拥有极佳的 ROS2 生态支持（Hobot 节点）。在具身智能的物理落地中，它的定位绝不是用来“硬抗 7B 大模型”的，而是作为**“云-边-端”架构中最核心的“边缘枢纽（Edge Hub）”**。

本教程将手把手带你利用 RDK-X5，完成一个**“语义分拣机械臂（Language-Guided Sorting Arm）”**的真实具身智能实战项目。

---

## 1. 架构设计：RDK-X5 能做什么？不能做什么？

在动手写代码前，我们必须基于 RDK-X5 的硬件特性做好系统架构（参考 `10_云边端协同架构` 教程）：

*   ❌ **不能做：** 在 RDK-X5 本地运行 OpenVLA-7B 甚至 450M 的 SmolVLA（Transformer 架构在 BPU 上的算子转换极度痛苦且显存不够）。
*   ✅ **最佳实践（云边协同）：** 
    1.  **RDK-X5 (边缘 Edge)：** 利用 5 TOPS 的 BPU 满血运行 **YOLOv8** 进行 30Hz 的实时物体检测；利用 ARM CPU 运行 **ROS2** 和逆运动学（IK）解算器，以 100Hz 控制底层机械臂。
    2.  **云端 API / 笔记本 (云 Cloud)：** 接收 RDK-X5 发来的物体列表和用户语音指令，利用大模型（如 Qwen-VL, GPT-4o 或局域网的 4070Ti）进行逻辑推理，返回目标物体的 ID。

---

## 2. 实战项目：语义分拣机械臂

**任务场景：** 桌面上放着一个红苹果、一个烂香蕉、一个药瓶。用户对 RDK-X5 说：“把能吃的水果给我”。机械臂自主定位并抓起红苹果。

### Step 1: 环境配置与摄像头驱动 (ROS2 Node)

RDK-X5 官方提供了 `TogetheROS.Bot` 系统。首先，我们需要唤醒摄像头并发布图像。

```bash
# SSH 登录到 RDK-X5
# 启动 USB 摄像头节点 (假设使用的是普通 USB 相机)
ros2 run hobot_usb_cam hobot_usb_cam --ros-args -p video_device:="/dev/video0" -p image_width:=640 -p image_height:=480
```

### Step 2: 边缘视觉感知（BPU 硬件加速 YOLO）

这是 RDK-X5 的强项！不要用纯 CPU 跑 OpenCV，我们必须调用地平线的 BPU 硬件加速。地平线官方已经提供了编译好的 YOLOv8 BPU 模型（`.bin` 格式）。

编写一个 Python 脚本 `edge_perception.py`：

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from hobot_dnn import pyeasy_dnn as dnn # 地平线 BPU 推理库
import cv2
import numpy as np

class BPUPerceptionNode(Node):
    def __init__(self):
        super().__init__('bpu_perception')
        self.subscription = self.create_subscription(Image, '/image_raw', self.image_callback, 10)
        
        # 1. 加载转换好的 BPU 模型 (YOLOv8)
        self.models = dnn.load('yolov8n_640x640_nv12.bin')
        self.detected_objects = {} # 存储当前画面中的物体 { "apple": [x, y, w, h] }

    def image_callback(self, msg):
        # 2. 将 ROS 图像转换为 BPU 需要的 NV12 格式
        cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        nv12_image = bgr2nv12(cv_image) 
        
        # 3. 极其快速的 BPU 前向推理 (约 10-20ms)
        outputs = self.models[0].forward(nv12_image)
        
        # 4. 后处理 (解析 Bounding Box)
        self.detected_objects = parse_yolo_outputs(outputs)
        self.get_logger().info(f"RDK-X5 边缘感知到: {list(self.detected_objects.keys())}")
```

### Step 3: 云边协同语义大脑 (API Request)

现在 RDK-X5 知道了桌子上有 `["apple", "rotten_banana", "medicine"]`。接下来，它遇到了一句模糊的语音指令：“把能吃的水果给我”。
RDK-X5 的 CPU 算不出这个逻辑，我们需要调用大模型 API。

在你的控制脚本中加入大模型请求：

```python
import requests
import json

def get_target_from_llm(instruction, detected_objects_list):
    """
    RDK-X5 作为瘦客户端，请求云端大模型
    """
    # 构造 Prompt：告诉大模型当前环境和人类指令
    prompt = f"""
    You are a robot brain. 
    Human instruction: "{instruction}"
    Objects on table: {detected_objects_list}
    Which exact object should the robot pick up? Reply with ONLY the object name.
    """
    
    # 调用大模型 API (如智谱、千问，或者你局域网里 4070Ti 部署的 vLLM 接口)
    url = "http://your_local_4070ti_ip:8000/v1/chat/completions"
    payload = {
        "model": "qwen-7b-chat",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    response = requests.post(url, json=payload).json()
    target_object = response['choices'][0]['message']['content'].strip()
    
    return target_object

# --- 测试 ---
objects = ["apple", "rotten_banana", "medicine"]
target = get_target_from_llm("把能吃的水果给我", objects)
print(f"云端大模型决策结果: 机器人应抓取 [{target}]") # 预期输出: apple
```

### Step 4: 局部运动学与机械臂控制 (Local Control Loop)

云端返回了 `"apple"`，RDK-X5 立刻从 Step 2 的 `detected_objects` 中查出苹果的像素坐标 `(u, v)`。
接下来，RDK-X5 必须完成**最后一步硬核控制**：将像素坐标转化为 3D 空间坐标，解算 IK，并驱动串口舵机。

```python
# 1. 像素坐标转 3D 相机坐标 (结合手眼标定和深度相机，参考 02 章节)
target_bbox = bpu_perception.detected_objects["apple"]
target_3d_xyz = pixel_to_3d(target_bbox, depth_image, camera_intrinsics)

# 2. 逆运动学解算 (IK) —— 运行在 RDK-X5 的 ARM CPU 上
# 计算 6 个电机的目标角度
target_joint_angles = calculate_ik(current_pose, target_3d_xyz)

# 3. 高频控制循环 (100Hz)
import serial
ser = serial.Serial('/dev/ttyUSB0', 115200)

# 发送包含 6 个关节角度的控制指令给底层的 STM32 驱动板
command = format_servo_command(target_joint_angles)
ser.write(command)
print("RDK-X5: 动作指令下发完毕，正在抓取！")
```

---

## 3. 进阶极客玩法：将 ACT (模仿学习) 部署到 RDK-X5

如果你不想依赖云端大模型，而是想让 RDK-X5 完全离线运行一套像人类一样丝滑的抓取动作（例如折叠衣服），你可以尝试部署 **ACT (Action Chunking with Transformers)**。

这需要极强的工程能力，核心步骤如下：

1. **PC 端训练：** 在你的 4070Ti 笔记本上，使用 PyTorch 收集几十条遥操作数据，训练 ACT 模型。
2. **模型拆分：** ACT 包含 ResNet（提取视觉特征）和 Transformer（预测动作）。
3. **PTQ 量化与转换 (地狱难度)：** 
   使用地平线的 `hb_mapper` 工具链，将 PyTorch 模型转换为 ONNX，再量化为 INT8 精度的 `.bin` 格式。
   *坑点：* BPU 对 CNN（ResNet）的支持极好，但对 Transformer 的某些算子（如复杂的 Attention）支持较弱。你可能需要手动修改 ACT 的网络结构，将不支持的算子替换为等效的 CNN 算子。
4. **BPU 推理：** 在 RDK-X5 上加载转换好的 `.bin` 模型，通过 C++ 或 Python 的 `hobot_dnn` 接口实现 20Hz+ 的完全离线具身控制！

## 总结

RDK-X5 在具身智能中的完美角色是**“强悍的感知者”**和**“敏捷的执行者”**。通过将耗时的语义推理抛给云端大模型，将高频的视觉检测（BPU加速）和运动控制留给本地，你可以用极低的成本打造出一台极具科技感的具身智能机器人！