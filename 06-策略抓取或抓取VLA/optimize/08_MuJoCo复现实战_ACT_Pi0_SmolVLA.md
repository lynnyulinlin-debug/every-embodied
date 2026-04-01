# 08_MuJoCo复现实战：ACT、Pi0与SmolVLA在复杂仿真中的部署

## 1. 教程背景与目标
在前面我们利用 ManiSkill 跑通了基础抓取。但当前具身智能界（Embodied AI）最主流的物理引擎是 **MuJoCo**（由 DeepMind 开源，因其极其精确的接触动力学而闻名）。

本实战教程将基于 `04mujoco复现ACT、Pi0、SmolVLA` 文件夹中的环境，手把手带你复现三种当下最前沿的控制架构：
1. **ACT (Action Chunking with Transformers)**：模仿学习（IL）的巅峰之作，专治自回归预测的长程灾难。
2. **Pi0 (Physical Intelligence 0)**：基于流匹配（Flow Matching）的通用基础模型。
3. **SmolVLA**：Hugging Face 开源的 450M 极限轻量级 VLA，专为边缘设备和单卡玩家打造。

---

## 2. 硬件适配与全生命周期显存预算分析

### 💻 12G 显存笔记本（如 4070Ti/5070Ti）的最佳入坑路径
对于拥有 12GB 显存的笔记本开发者，当你看到别人动辄使用 A100 炼 7B 级的大模型时，难免会感到算力焦虑。但这 12GB 的 VRAM，恰恰是你复现具身控制闭环的黄金工具！

在上述三个模型中，**强烈建议您将 SmolVLA (450M) 作为您的“第一入坑选择”**。
让我们来做一个极度严谨的 **全生命周期显存预算分析 (VRAM Budgeting)**：

**总显存占用 = 静态权重参数 + 激活值与 KV Cache + 物理仿真与渲染管线 + 框架开销**

1.  **静态权重参数：**
    SmolVLA 只有 450M（0.45B）参数。在默认的 `BFloat16` 精度（2 Bytes/参数）下，它的纯权重占用 = $0.45\text{B} \times 2\text{ Bytes} \approx \textbf{0.9 GB}$！
    （对比 OpenVLA-7B，哪怕量化到 4-bit 还需要 3.5GB）
2.  **激活值与 KV Cache（动态）：** 
    由于参数量极小，推理时的 KV Cache 开销也非常低，通常仅需额外 **0.5 GB** 左右。
3.  **MuJoCo 物理与渲染管线：** 
    MuJoCo 的渲染库相对 SAPIEN 更轻量，在跑单环境时通常仅占用 **0.5 GB ~ 1.5 GB**（取决于抗锯齿和纹理质量）。
4.  **PyTorch 框架开销：** 约 **0.5 GB**。

**死亡计算：0.9 + 0.5 + 1.5 + 0.5 = 3.4 GB。**

**结论：** 在 12GB 显存下，你可以**毫无顾忌地开满 MuJoCo 仿真器的最高渲染画质**，甚至同时开启 4 个并行的多进程环境做批量推理测试，而绝对不会遇到任何 OOM (Out of Memory) 警告！

在本地跑通 SmolVLA 的完整流转后（验证 IK 解算、动作闭环等），再将代码无缝切换到云端去跑 7B 大模型，这是具身智能开发的最优路径。

---

## 3. 环境搭建与 MuJoCo 解析

首先，确保你安装了最新的 `mujoco` 和其 Python 绑定。
```bash
pip install mujoco glfw opencv-python numpy
```

在 `04mujoco复现ACT、Pi0、SmolVLA/mujoco_env/mujoco_parser.py` 中，作者封装了一个极简但功能强大的 `MuJoCoMinimalViewer`。它处理了相机的位姿、鼠标拖拽扰动（Perturbations）以及渲染回调。这是我们复现高级算法的底座。

### 3.1 加载桌面抓取场景
我们可以从 `asset/tabletop/object/floor_mujoco_style.xml` 加载一个带有桌面的 MuJoCo 场景。

```python
import mujoco
from mujoco_env.mujoco_parser import MuJoCoMinimalViewer

# 1. 加载 MuJoCo 模型和数据
xml_path = "asset/tabletop/object/floor_mujoco_style.xml"
model = mujoco.MjModel.from_xml_path(xml_path)
data = mujoco.MjData(model)

# 2. 启动 Viewer (用于可视化验证物理是否正常)
viewer = MuJoCoMinimalViewer(model, data, title="MuJoCo RL Environment")
# viewer.render() # 暂时注释，我们要在控制循环中步进
```

---

## 4. 复现 SmolVLA (450M 极限边缘计算)

SmolVLA 是 Hugging Face 给具身社区的礼物。它将极其庞大的 VLA 模型（如 7B 的 OpenVLA）通过极致的剪枝和蒸馏，压缩到了仅 450M 参数。
这意味着什么？意味着你可以直接在笔记本甚至 `地瓜RDK-X5` 这种边缘板子上，不用任何远程 GPU 服务器，直接跑 VLA 控制 MuJoCo。

```python
from transformers import AutoModelForVision2Seq, AutoProcessor

# 1. 加载 SmolVLA
processor = AutoProcessor.from_pretrained("HuggingFaceTB/SmolVLA-450M")
# 注意：不需要 load_in_4bit，450M 模型在显存里只占不到 1GB！
model = AutoModelForVision2Seq.from_pretrained("HuggingFaceTB/SmolVLA-450M").to("cuda")

prompt = "Action to pick up the red block:"

while viewer.is_alive():
    # 采集 MuJoCo 的视觉
    img = viewer.get_camera_image()
    
    # 预处理
    inputs = processor(prompt, img, return_tensors="pt").to("cuda")
    
    # 推理 (极速！单步可能只需 20ms)
    out = model.generate(**inputs, max_new_tokens=7)
    
    # 解码得到 7D 动作增量 [dx, dy, dz, droll, dpitch, dyaw, dgripper]
    action_delta = decode_smolvla_action(out)
    
    # 将增量通过逆运动学 (IK) 转化为关节角，传给 MuJoCo
    target_qpos = ik_solver(current_qpos=data.qpos[:7], delta_pose=action_delta)
    data.ctrl[:7] = target_qpos
    
    mujoco.mj_step(model, data)
    viewer.render()
```

**工程避坑与总结：**
运行 SmolVLA 最大的坑在于**逆运动学 (IK)**。因为 SmolVLA 输出的是末端笛卡尔坐标的增量，而 MuJoCo 默认的驱动器（Actuators）接受的是关节力矩或关节目标角度。你必须在两者之间手写一个基于雅可比矩阵的伪逆求解器（或调用 `mujoco.mj_jac`）来进行坐标系转换。

---

## 5. 复现 ACT (Action Chunking with Transformers)

ACT 解决了传统模仿学习的一个死穴：多模态分布的矛盾（人类在演示时，既可能从左边绕过障碍，也可能从右边绕，传统 MSE 损失会取平均，直接撞上障碍物）。

ACT 引入了 CVAE（条件变分自编码器）和 Transformer，不仅能建模多模态，还会一次性输出未来 $k$ 步的动作（Action Chunking），极大平滑了轨迹。

```python
# 伪代码：在 MuJoCo 中闭环运行 ACT
# 假设 act_policy 是加载好权重的 ACT 模型

chunk_size = 100 # ACT 的经典设定，一次预测 100 步
action_queue = [] # 动作缓冲区

while viewer.is_alive():
    # 1. 获取当前相机的 RGB 图像 (MuJoCo 渲染)
    img = viewer.get_camera_image(camera_name="front_cam")
    qpos = data.qpos[:7] # 机械臂 7 关节角
    
    # 2. 如果动作队列空了，呼叫 ACT 大脑进行长程规划
    if len(action_queue) == 0:
        # 输入：当前图像 + 当前关节角
        # 输出：未来 100 步的关节角目标轨迹 [100, 7]
        pred_actions = act_policy(img, qpos)
        action_queue.extend(pred_actions)
    
    # 3. 弹出队列头部的动作，交给底层的 MuJoCo 执行
    target_qpos = action_queue.pop(0)
    
    # 将目标关节角赋值给执行器 (Actuator)
    data.ctrl[:7] = target_qpos 
    
    # 4. MuJoCo 物理步进 (100Hz+)
    mujoco.mj_step(model, data)
    viewer.render()
```

**系统分析：**
这里的关键在于 `action_queue`。由于一次预测了 100 步，我们可以让 MuJoCo 以极高的频率平滑执行这些关节指令，而不用每一步都去等神经网络漫长的推理。这是一种典型的时序解耦。

---

## 6. 复现 Pi0 (Flow Matching 基础模型)

Pi0 (Physical Intelligence) 是近期最火的架构之一，它彻底抛弃了离散 Token 和扩散模型（Diffusion），采用了更高效的**流匹配 (Flow Matching)** 来生成连续动作。

Pi0 的最大优势是它天然支持多模态输入（图像、文本、本体状态）的任意组合，并且生成速度比 Diffusion 快几个数量级。

```python
# 伪代码：在 MuJoCo 中闭环运行 Pi0 
# Pi0 的输入包含了语言指令
instruction = "Fold the towel on the table"

while viewer.is_alive():
    img = viewer.get_camera_image()
    qpos = data.qpos[:7]
    
    # Pi0 通过 Flow Matching 直接从高斯噪声中采样出确定性的动作轨迹
    # 注意：Pi0 同样支持 Chunking
    pred_actions = pi0_policy(img, qpos, instruction)
    
    data.ctrl[:7] = pred_actions[0] # 取当前步
    mujoco.mj_step(model, data)
    viewer.render()
```

通过在同一个 MuJoCo 环境中复现这三大算法，你会深刻体会到：
- **ACT** 赢在模仿学习的极高质量。
- **Pi0** 赢在物理基础模型的通用性与流匹配的速度。
- **SmolVLA** 赢在无与伦比的边缘部署成本。