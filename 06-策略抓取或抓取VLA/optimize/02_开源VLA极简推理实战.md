# 实战教程 1：开源 OpenVLA 极简推理跑通与动作解析

## 1. 教程定位与核心目标
对于熟悉大模型（LLM）但对机器人控制较为陌生的开发者来说，最大的黑盒在于：“输入一张图片和一句文本，大模型到底输出了什么？它是如何变成机械臂动作的？” 
本教程将脱离复杂的物理仿真，使用纯 Python 脚本，以当前最主流的 7B 级模型 **OpenVLA** 为例，带你完成一次纯净的极简推理（Forward Pass），并对输出的 7 维动作张量进行深度的物理学解析。

## 2. 环境配置与模型加载

首先，安装基础依赖：

```bash
pip install torch torchvision transformers pillow numpy bitsandbytes accelerate
```

### 💻 硬件适配：12G 显存笔记本（如 4070Ti/5070Ti）显存全生命周期估算与加载方案
很多初学者直接用 `from_pretrained` 加载 7B 模型，结果在 12G 显卡上秒报 OOM (Out of Memory)。这是因为他们没有算清楚大模型运行时的**全生命周期显存占用**。

在这里，我们必须引入一个极其重要的工程概念：**峰值显存（Peak VRAM）**。
你笔记本配置的 12GB 显存，就是你的**物理硬天花板**。只要在程序运行的任何一毫秒，瞬时的总显存需求超过了 12GB，程序就会立刻崩溃。

一个大模型在运行时的**峰值显存**由以下几部分构成：
**峰值显存占用 = 静态权重参数 + 激活值 (Activations) + KV Cache + 框架运行开销 (CUDA Context)**

1.  **静态权重参数（参数量 × 精度）**：
    对于 `OpenVLA-7B`（约 70 亿参数）：
    *   在标准的 `BFloat16`（半精度，2 Bytes/参数）下：$7 \text{B} \times 2 \text{ Bytes} \approx 14 \text{ GB}$。仅仅加载权重就直接顶破了 12G 显存的物理天花板！
2.  **激活值与 KV Cache（动态开销导致峰值飙升）**：
    *   在自回归推理（生成动作 Token）时，模型需要缓存之前生成的键值对（KV Cache），并且在前向传播（Forward Pass）的过程中，**每一层的输入输出张量会瞬间产生巨大的激活值**。
    *   这个过程会导致**显存的瞬间峰值远高于模型静静躺在显存里的驻留大小**。对于 7B 模型，这部分动态峰值开销根据 Batch Size 和输入序列长度，通常需要额外占用 **1.5GB ~ 2.5GB**。
3.  **框架开销**：PyTorch 初始化 CUDA 环境自带的约 0.5GB。

**破局方案：INT4 (4-bit) 动态量化加载**
为了把峰值显存压制在 12GB 笔记本物理配置之下，我们必须引入 `bitsandbytes` 库将权重压缩：
*   **INT4 量化后静态权重计算：** 4-bit 相当于 0.5 Bytes。权重占用 = $7 \text{B} \times 0.5 \text{ Bytes} \approx 3.5 \text{ GB}$。
*   **真实峰值占用推演：** 3.5 GB (静态权重) + 2.5 GB (推理时的动态激活峰值) + 0.5 GB (CUDA开销) $\approx$ **6.5 GB (Peak VRAM)**。

这不仅能完美运行，还为你后续开启吃显存的仿真器留足了至少 5.5GB 的安全空间！

```python
import torch
from transformers import AutoModelForVision2Seq, AutoProcessor, BitsAndBytesConfig
from PIL import Image

# 1. 配置 4-bit 量化参数 (12G显存救星)
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16, # 计算时仍用 bf16 保证推理精度
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

# 2. 初始化 Processor 和 Model
model_id = "openvla/openvla-7b"
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

# 加载量化模型
model = AutoModelForVision2Seq.from_pretrained(
    model_id, 
    attn_implementation="flash_attention_2",  # 建议开启 FlashAttention，能大幅削减激活值产生的峰值显存！
    quantization_config=quantization_config,  # <--- 开启 4-bit 量化
    low_cpu_mem_usage=True, 
    trust_remote_code=True
)

print("4-bit 模型加载完成！请使用 nvidia-smi 查看，实际常驻显存应在 5~6GB 左右。")
```

## 3. 图像与指令输入处理

找一张带有桌面的图片（例如 `apple_on_table.jpg`），或者从现有的具身数据集中抽取一帧。

```python
# 3. 准备输入
image = Image.open("apple_on_table.jpg").convert("RGB")
instruction = "pick up the red apple"
# OpenVLA 的标准 prompt 格式
prompt = f"In: What action should the robot take to {instruction}?\nOut:"

# 将图像和文本编码为模型输入张量
inputs = processor(prompt, image).to("cuda:0", dtype=torch.bfloat16)
```

## 4. 前向推理与 Action 生成

OpenVLA 会自回归地生成连续的 token，然后通过 Detokenizer（去词元化）将这些特殊 token 映射回真实的连续物理动作（Continuous Actions）。

```python
# 4. 执行自回归动作预测
# OpenVLA 默认预测下一个状态的 7 自由度动作
action_prediction = model.predict_action(**inputs, unnorm_key="bridge_orig")

print("大模型输出的原始动作向量:", action_prediction)
# 预期输出类似: [ 0.021, -0.015, 0.050, 0.000, 0.000, 0.120, 1.000 ]
```

## 5. 系统分析：这个 7 维数组到底是什么？

初学者最容易卡在这里。在上述代码中，大模型输出的 `[ 0.021, -0.015, 0.050, 0.000, 0.000, 0.120, 1.000 ]` 到底怎么控制机械臂？

在绝大多数 VLA 任务（如 Bridge 数据集或 RT-X 标准）中，这 7 个维度代表**末端执行器（End-Effector, EEF）在笛卡尔坐标系下的目标增量（Delta Pose）与夹爪开合度**：

1. **`action[0:3]` (x, y, z 平移增量)**：
   - 代表机械臂末端要在三维空间中移动的距离（通常单位是米）。
   - 例如 `[0.021, -0.015, 0.050]` 意味着：向前走 2.1cm，向右走 1.5cm，向上抬高 5.0cm。
2. **`action[3:6]` (roll, pitch, yaw 旋转增量)**：
   - 代表机械臂夹爪的姿态角变化（欧拉角，弧度制）。
   - 例如 `[0, 0, 0.12]` 意味着只在水平面（Yaw）上旋转约 6.8 度（0.12 弧度）。
3. **`action[6]` (Gripper state 夹爪状态)**：
   - 通常是离散值或归一化连续值。`1.0` 代表完全闭合（抓住），`0.0` 或 `-1.0` 代表完全张开。

**与 02 章节知识的串联：**
注意，大模型**只负责告诉你末端要怎么动**。它不关心你的机械臂是 6 轴还是 7 轴。实际部署时，你需要将这个 7D 动作传入机器人的**逆运动学（IK）求解器**（详见 02 章节），算出各个关节的目标角度（Joint Angles），再交给底层的 PID 控制器去驱动电机。

## 6. 下一步
现在，我们已经把大模型变成了“看图说话给坐标”的函数。在下一篇教程中，我们将把这个函数塞进 ManiSkill 仿真环境，让机械臂真正动起来。