# LeRobot 新手扫盲与实战指南：开启具身智能之旅

欢迎来到物理世界的 AI 大门！如果你听说过 ChatGPT 是语言模型领域的革命，那么 **LeRobot** 就是机器人（具身智能）领域的革命。本指南将带你从零了解什么是 LeRobot，以及如何配置和操作它。

---

## 🤖 第一部分：什么是 LeRobot？(知识扫盲)

### 1. 它是 Hugging Face 的“亲儿子”
在 AI 圈，Hugging Face (抱抱脸) 相当于开源模型的 GitHub。以前大家都去那里下载语言模型或画图模型。现在，Hugging Face 官方推出了 **LeRobot**，旨在为真实世界的机器人提供一个**端到端**的开源机器学习库。

### 2. LeRobot 到底能干什么？
传统机器人需要复杂的 C++、ROS（机器人操作系统）和运动学方程。而 LeRobot 极其简单粗暴，它的核心逻辑是：**“看图学动作”（模仿学习 Imitation Learning）**。

它提供了一站式的解决方案：
1. **控制真机**：内置了对常见开源硬件（如 SO-101 机械臂、Koch 机械臂）的底层驱动。
2. **采集数据**：帮你轻松录制带有时间戳的摄像头视频和电机角度数据。
3. **训练大脑**：内置了当下最先进的具身智能算法模型（如 ACT, Diffusion Policy, VQ-BeT）。
4. **推理执行**：训练好模型后，一键部署，让机器人脱离手柄，自己看着摄像头干活。

### 3. 为什么它会火？
- **极度降低门槛**：只要懂一点 Python，就能训练一台机器人。
- **拥抱廉价硬件**：它完美适配用普通 3D 打印件和百元级舵机（如 Feetech、Dynamixel）拼装起来的开源机械臂。
- **统一的数据集标准**：建立了一个类似于图像界 ImageNet 的机器人数据集仓库，大家可以共享自己录制的机器人抓取数据。

---

## ⚙️ 第二部分：如何配置 LeRobot 环境？

配置 LeRobot 其实就是配置一个标准的 Python 深度学习环境，再加上一点硬件驱动。以下是极简配置思路：

### 1. 准备基础环境
强烈推荐使用 `conda`（或 `micromamba`）创建一个干净的环境。
```bash
# 创建环境
conda create -y -n lerobot python=3.10
conda activate lerobot

# 安装录制视频所需的基础组件
conda install ffmpeg -c conda-forge
```

### 2. 下载并安装 LeRobot
```bash
# 拉取 Hugging Face 的开源仓库
git clone https://github.com/huggingface/lerobot
cd lerobot

# 如果你使用的是国内网络，建议换源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装（如果你用的是飞特 Feetech 舵机，加上对应的拓展包）
pip install -e ".[feetech]"
# 如果用的是 Dynamixel 舵机，则执行 pip install -e ".[dynamixel]"
```

### 3. （硬件专属）确认串口权限
如果是在 Linux 或 RDK-X5 这种开发板上，插入 USB 舵机控制板后，必须给系统串口赋权：
```bash
sudo chmod 666 /dev/ttyACM0
sudo chmod 666 /dev/ttyACM1
```

---

## 🕹️ 第三部分：如何操作 LeRobot？(实战流程)

LeRobot 的所有核心操作，都集成在一个名为 `control_robot.py` 的脚本中。只要掌握了这个脚本的几个参数，你就掌握了全套流程。

*(以使用 SO-101 双臂遥操作套件为例，包含一个主臂 Leader 和一个从臂 Follower)*

### 步骤 1：找串口 (寻址)
你的电脑插上了好几个 USB，系统怎么知道哪个是主臂，哪个是从臂？
```bash
python lerobot/scripts/find_motors_bus_port.py
```
跟着终端的提示，拔掉再插上 USB，系统就会帮你识别出端口（比如从臂是 `/dev/ttyACM0`，主臂是 `/dev/ttyACM1`）。识别后，修改代码里的配置字典。

### 步骤 2：硬件校准 (Calibration)
机械臂的电机没有眼睛，它不知道自己现在弯到了什么程度。所以每次重装或开机，都需要校准“零位”。
```bash
python lerobot/scripts/control_robot.py \
  --robot.type=so101 \
  --robot.cameras='{}' \
  --control.type=calibrate \
  --control.arms='["main_follower"]'  # 先校准从臂，再校准主臂
```
运行后，你需要用手把机械臂摆成终端里描述的特定姿势（比如全部伸直），然后按回车。

### 步骤 3：遥操作 (Teleoperation)
一切就绪！现在我们要让人类（主臂）控制机器（从臂）。
```bash
python lerobot/scripts/control_robot.py \
  --robot.type=so101 \
  --robot.cameras='{}' \
  --control.type=teleoperate
```
**见证奇迹：** 当你用手掰动主臂（Leader）时，从臂（Follower）会像照镜子一样，丝毫不差地复刻你的动作！

### 步骤 4：录制数据集 (Record)
如果你想教 AI 抓杯子，你需要开启摄像头录制：
```bash
python lerobot/scripts/control_robot.py \
  --robot.type=so101 \
  --control.type=record \
  --dataset_name=my_first_cup_grasping
```
这时候，你控制主臂抓杯子，LeRobot 会在后台自动把每一帧的画面和舵机角度存成一个标准的数据集。

### 步骤 5：训练与重放 (Train & Replay)
录满几十次后，你可以调用 LeRobot 的训练脚本（通常需要带 GPU 的电脑），训练出一个模型。
训练完成后，使用 `control.type=replay` 或直接运行推断脚本，你的机械臂就能抛开主臂，自己看着摄像头去抓杯子了！

---

## 💡 总结
**LeRobot 不是一个硬件，而是一个大脑框架。**
- 它把复杂的机器人控制，简化成了只需敲几行命令的流水线。
- **校准 -> 遥控 -> 录制 -> 训练 -> 自动执行**。
- 这就是如今具身智能（Embodied AI）最标准、最前沿的研发范式。