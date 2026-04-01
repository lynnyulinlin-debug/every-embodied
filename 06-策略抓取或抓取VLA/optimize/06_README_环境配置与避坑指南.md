# 06 章节实战教程：环境配置与避坑指南

本章节包含多个不同侧重点的实战教程（极简推理、仿真闭环、数据集解析）。由于具身智能（Embodied AI）处于深度学习、物理仿真和海量数据工程的交叉领域，这些教程所需的底层环境**存在较大差异，甚至可能发生底层库冲突**。

为了保证大家在实操时不被环境配置劝退，**强烈建议为这三个教程分别创建独立的虚拟环境（Conda Environment）**，或者仔细阅读本指南中的避坑说明。

---

## 💻 硬件护航：12G显存笔记本（如4070Ti/5070Ti）的最佳入坑策略

很多初学者看到“7B VLA大模型”就觉得自己 12G 的笔记本没救了。其实不然，只要你掌握了量化压缩和显存错峰调度的技巧，**12G 显存完全可以作为顶级具身代码的本地 Debug 工作站！**

1.  **首选 SmolVLA (450M)：** 对于 `08_MuJoCo复现实战_ACT_Pi0_SmolVLA.md` 教程，强烈建议直接上手只有 450M 参数的 SmolVLA。它在 GPU 中只占不到 1GB 显存，你可以开满 MuJoCo 仿真器最高渲染画质，验证代码逻辑毫无压力。
2.  **大模型的 4-bit 量化降维：** 在进行 `02_开源VLA极简推理实战.md` 教程时，必须通过 `bitsandbytes` 开启 `load_in_4bit=True`，将 14GB 的 OpenVLA-7B 极限压缩至 **~5.5GB 显存**，完美跑通。
3.  **大模型 + 仿真器的显存错峰调度：** 在进行 `03_VLA仿真闭环抓取实战.md` 时，VLA 推理 (5.5G) + ManiSkill 渲染 (3G) 逼近 12G 红线。必须：
    -   调低仿真相机分辨率（如 `camera_width=256`）。
    -   在每次大模型推理完毕、把动作交到底层物理引擎进行高频渲染前，调用 `torch.cuda.empty_cache()` 清理碎片腾出空间。
4.  **数据集内存溢出与显存抢占：** 在 `04_RT系列架构演进与动作Token化实战.md` 处理 RT-X 数据集时，TensorFlow 会瞬间抢光 12G 显存，且全量数据会死机。必须在代码顶端加上 `os.environ["CUDA_VISIBLE_DEVICES"] = "-1"` 强制禁用 GPU，并使用 `split='train[:10]'` 仅加载一小部分数据。

如果后续你想要对 7B 大模型进行全参微调（Full Fine-tuning），那就不应该在笔记本上浪费时间，请参考 `09_12G显存笔记本复现指南与云算力Docker策略.md` 上云租用算力。

---

## 🛠️ 环境 1：OpenVLA 极简推理 (纯深度学习环境)

**适用教程：** `02_开源VLA极简推理实战.md`
**核心痛点：** 把庞大的 7B 视觉语言模型塞进显卡，并加速其自回归生成。

### 1. 依赖清单 (`requirements-tut1.txt`)
```text
torch>=2.1.0        # 核心框架 (注意匹配 CUDA 版本，如 cu118/cu121)
torchvision
transformers>=4.40.0 # OpenVLA 依赖 AutoModelForVision2Seq
accelerate          # 用于模型按需加载和显存自动分配
pillow              # 图像处理
numpy
bitsandbytes        # 12G笔记本的 4-bit 量化护航插件
flash-attn>=2.0.0   # 【强烈建议】大幅降低显存占用并加速推理
```

### 2. 避坑指南 (Troubleshooting)
*   **FlashAttention 编译报错：** `flash-attn` 对 CUDA 版本和 GCC 编译器版本极其挑剔。如果安装一直报错，请在代码中去掉 `attn_implementation="flash_attention_2"` 参数，回退到 PyTorch 默认的注意力机制（代价是推理变慢，显存占用增加约 3-5GB）。

---

## 🚀 环境 2：VLA 在 ManiSkill 的闭环抓取 (物理渲染 + 深度学习)

**适用教程：** `03_VLA仿真闭环抓取实战.md`
**核心痛点：** 将 PyTorch 张量与底层物理引擎（SAPIEN）的高频渲染流打通。

### 1. 依赖清单 (`requirements-tut2.txt`)
```text
# 包含 tut1 的所有依赖
torch
transformers
accelerate
bitsandbytes

# 强化学习与环境交互标准库
gymnasium>=0.29.1

# ManiSkill 仿真器及底层物理引擎
mani_skill
sapien
opencv-python       # 处理仿真器输出的 RGBD 相机数据流
```

### 2. 避坑指南 (Troubleshooting)
*   **无头服务器渲染崩溃 (Headless Rendering Error)：** SAPIEN 和 ManiSkill 需要调用 GPU 的 Vulkan 或 EGL 接口进行图像渲染。如果你是在没有连接显示器的 Linux 服务器上运行，在调用 `env.reset()` 时极易引发核心转储（Core Dump）或报错。
    *   **解法：** 运行脚本前，设置环境变量强制使用 EGL 渲染：
        ```bash
        export SAPIEN_EGL_ENV_GPU=0
        export MANISKILL_ENABLE_RENDERER=1
        ```
*   **动作空间报错：** 确保环境初始化时设置了 `control_mode="pd_ee_delta_pose"`，否则直接将 7D 的 VLA 动作传入默认的关节扭矩（Joint Torque）环境会导致维度不匹配崩溃。

---

## 📊 环境 3：RT 系列架构与 X-Embodiment 数据集 (数据工程环境)

**适用教程：** `04_RT系列架构演进与动作Token化实战.md`
**核心痛点：** 处理 Google 庞大的 TFDS (TensorFlow Datasets) 数据格式，并防止与 PyTorch 发生显存争抢。

### 1. 依赖清单 (`requirements-tut3.txt`)
```text
numpy
# Google 数据处理全家桶
tensorflow>=2.14.0
tensorflow-datasets # 用于下载和解析 bridge 等 Open X-Embodiment 数据集
etils[epath]
```

### 2. 避坑指南 (Troubleshooting)
*   **致命冲突：PyTorch 与 TensorFlow 显存争夺大战！** 
    TensorFlow 默认在 `import` 时会立刻霸占当前 GPU 的**所有**可用显存。如果你在同一个脚本里既加载了 TFDS 处理数据，又想用 PyTorch 加载大模型，PyTorch 必然报 `CUDA Out of Memory`。
    *   **解法：** 参考开头硬件护航指南，强制屏蔽 GPU `os.environ["CUDA_VISIBLE_DEVICES"] = "-1"`，使用 CPU 做数据流水线处理。
*   **网络问题：** RT-X 数据集存储在 Google Cloud Storage (GCS) 上。如果你在国内服务器运行 `builder_from_directory('gs://...')`，大概率会遇到连接超时。请确保服务器配置了有效的全局代理或使用镜像源下载。