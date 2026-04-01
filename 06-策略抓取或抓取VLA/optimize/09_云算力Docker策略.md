# 09_云算力Docker策略：当笔记本性能成为瓶颈时

针对拥有 **12GB 显存 (VRAM) + 32GB 内存** 的笔记本开发者（如配备 RTX 4070 / 4070Ti / 5070Ti 的移动端工作站），具身智能的复现会遇到一个非常明显的分水岭。
在阅读前几个实战教程（02、03、04、08）时，你也看到了我们在本地运行 7B 大模型所做的各种“极限降级”妥协（4-bit 量化、极小分辨率仿真渲染）。

这台笔记本应该成为你顶级的代码调试工作站，用 SmolVLA (450M) 或 4-bit 量化跑通极简的 ManiSkill/MuJoCo 仿真闭环，验证代码逻辑、IK 求解、坐标系转换没有 Bug。

但遇到以下场景，请不要在笔记本上浪费时间调参，直接上云租算力：
1.  **7B 级 VLA 模型的微调（LoRA / Full FT）：** 微调 OpenVLA (BF16) 至少需要 24GB 显存（单张 RTX 3090/4090 的极限），加大 Batch Size 甚至需要 40GB - 80GB 显存（如 A6000 或 A100）。
2.  **超过 10B 参数的模型推理与训练：** 像 RT-2 (12B) 级别的大脑，12G 显存连 4-bit 量化都塞不下。
3.  **处理超大规模的 Open X-Embodiment 数据集：** RT-X 的完整数据集高达数 TB。在本地解压和进行 TFDS 数据流预处理，会直接撑爆固态硬盘并引发内存 Swap 导致死机。

当你准备前往 AutoDL、趋动云或 RunPod 租用 RTX 4090 (24G) 或 A100 (40G/80G) 时，这里有一套成熟的工程策略。

---

## 1. Docker 制作与云端部署黄金法则

具身智能的环境配置极其折磨人（Vulkan、EGL 渲染、SAPIEN、MuJoCo、ROS），每次租机器重新 `pip install` 绝对会让人崩溃。提前把 Docker 镜像搞好方便多次使用，是极其专业且正确的工程直觉！

### 法则一：环境与数据彻底分离 (Environment vs. Data)
*   **千万不要把数据集打包进 Docker 镜像！** Docker 镜像应该只包含操作系统、CUDA、Python 库和物理引擎依赖。镜像大小控制在 10GB-20GB 左右。
*   **数据挂载：** 租用算力时，平台通常会提供“数据盘（Data Volume）”或云存储。把几十 GB 的网络权重和上 TB 的 RT-X 示范数据放在云盘上，启动 Docker 时使用 `-v /cloud_drive/data:/workspace/data` 将其挂载进容器。

### 法则二：解决无头渲染 (Headless Rendering) 的终极 Dockerfile
在云服务器上跑具身仿真（ManiSkill / MuJoCo），最惨的痛点是没有物理显示器，导致 OpenGL/Vulkan 初始化失败（回顾 `06_README_环境配置与避坑指南.md` 提到的坑）。你的 Docker 镜像必须预装这些虚拟渲染库：

```dockerfile
# 推荐基于 NVIDIA 官方的 PyTorch 镜像
FROM nvcr.io/nvidia/pytorch:23.10-py3

# 安装虚拟显示和渲染依赖 (针对 Ubuntu)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libosmesa6-dev \
    libx11-6 \
    libglfw3 \
    libglew-dev \
    xvfb \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 设置环境变量，强制物理引擎使用 EGL 渲染（极度重要！）
ENV MUJOCO_GL="egl"
ENV SAPIEN_EGL_ENV_GPU=0
ENV MANISKILL_ENABLE_RENDERER=1

# 安装 Python 具身智能核心库
RUN pip install torch torchvision transformers accelerate bitsandbytes
RUN pip install mujoco gymnasium mani_skill tensorflow-datasets
```

### 法则三：利用平台的“自定义镜像 / 保存环境”功能
*   如果你在国内使用 **AutoDL**：不需要自己从零写 Dockerfile。你可以先租一台便宜的卡（如 RTX 3060），花几个小时在 Jupyter 终端里把所有的 `pip install`、EGL 渲染配置全部跑通，测试一个简单的 MuJoCo 脚本无误后。直接在控制台点击**“保存镜像”**。
*   下次你要炼 7B 的大模型时，直接租一台昂贵的 A100，并在启动时选择你保存的这个**自定义镜像**，10 秒钟即可进入完美配置好的开发环境，立省几百块钱的配环境机器费。

---

## 2. 总结你的终极开发工作流 (The Workflow)

拥有这台 12G 显存的 5070Ti 笔记本，你的完美工作流应该是：

1.  **本地代码开发与 Debug (Local)：** 在笔记本上写代码。使用 SmolVLA 或 4-bit 量化的 OpenVLA 跑通极简的 ManiSkill/MuJoCo 仿真闭环，验证代码逻辑、IK 求解、坐标系转换没有 Bug。
2.  **云端大规模微调 (Cloud)：** 逻辑验证通了之后，将代码 push 到 GitHub。在云端拉起一台 24G 显存的 4090（加载你预先保存好的具身智能 Docker 镜像），挂载云盘里的真实数据集，进行 OpenVLA 的 LoRA 微调。
3.  **云端到本地的部署 (Deploy)：** 微调结束后，把几十 MB 的 LoRA 权重文件下载回你的笔记本。在笔记本上加载合并后的模型，再次在本地的 MuJoCo 里观看机器人完美执行抓取动作。