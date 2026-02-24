# video2robot（中文增强版）

视频（或文本动作）到机器人动作的端到端流水线：

`Prompt / Video -> PromptHMR -> SMPL-X -> GMR -> Robot Motion`

## 本仓库新增功能

- 接入 `Seedance` 视频生成（默认可用，保留 Veo/Sora）
- Web UI 中文化，支持：
  - 文生视频
  - 上传视频
  - 自动流水线（生成/提取/重定向）
- Web 3D 可视化支持机器人外观切换：
  - 彩色（按角色区分）
  - 铁皮原色（更真实）
- 多人轨迹支持：
  - `--all-tracks` 生成所有轨迹机器人动作
  - `--robot-all` 在 robot-viser 同时显示多角色
- 新增 MuJoCo 多机器人录制脚本：
  - `third_party/GMR/scripts/vis_robot_motion_multi.py`
  - 支持多个 `robot_motion_track_*.pkl` 同场显示与录制

## 环境准备

需要两个 conda 环境：

- `phmr`：视频生成 + 姿态提取 + Web + robot-viser
- `gmr`：机器人重定向 + MuJoCo 可视化/录制

### 环境复刻（推荐：YAML + patch）

目标：在另一台服务器尽量“一键”复现当前可用环境与代码改动。

#### A) 克隆你的 fork（含子模块）

```bash
git clone --recursive https://github.com/hope5hope/video2robot.git
cd video2robot
git submodule update --init --recursive
```

#### B) 用 YAML 创建两个环境

```bash
conda env create -f envs/gmr.yml
conda env create -f envs/phmr.yml
```

若环境已存在，可改为：

```bash
conda env update -n gmr -f envs/gmr.yml --prune
conda env update -n phmr -f envs/phmr.yml --prune
```

#### C) 应用 3 个 patch（主仓库 + 两个子仓库）

```bash
git apply patches/main.patch
git -C third_party/PromptHMR apply ../../patches/prompthmr.patch
git -C third_party/GMR apply ../../patches/gmr.patch
```

> 注意：patch 需要在匹配的基线 commit 上应用（见 `PATCHES.md`）。

#### D) 在当前机器导出 YAML（用于迁移到其他服务器）

```bash
mkdir -p envs
conda env export -n gmr > envs/gmr.yml
conda env export -n phmr > envs/phmr.yml
```

> 说明：YAML 会记录多数 conda/pip 包，但不会自动包含你手工改过的源码、未提交补丁或额外下载的模型文件，所以仍需配合 `patches/*.patch` 与模型下载步骤。

### 1) 克隆（含 submodule）

```bash
git clone --recursive https://github.com/hope5hope/video2robot.git
cd video2robot
# 或
git submodule update --init --recursive
```

### 2) GMR 环境

```bash
conda create -n gmr python=3.10 -y
conda activate gmr
pip install -e .
```

### 3) PromptHMR 环境（4090/常规 GPU）

```bash
conda create -n phmr python=3.10 -y
conda activate phmr
cd third_party/PromptHMR
bash scripts/install.sh --pt_version=2.4
```

> 若 `install.sh` 在你的机器上不稳定，可参考 `01春晚舞蹈机器人复刻.md` 的手动安装方案。

## API 配置

在仓库根目录创建 `.env`：

```bash
cp .env.example .env
```

常用变量：

- `SEEDANCE_API_KEY=...`
- `GOOGLE_API_KEY=...`
- `OPENAI_API_KEY=...`

## 常用命令

### 一键流水线

```bash
python scripts/run_pipeline.py --action "动作序列：角色向前走四步"
```

### 从已有视频开始

```bash
python scripts/run_pipeline.py --video /path/to/video.mp4
```

### 分步运行

```bash
python scripts/generate_video.py --model seedance --action "动作序列：角色向前走四步"
python scripts/extract_pose.py --project data/video_001
python scripts/convert_to_robot.py --project data/video_001 --all-tracks
```

### 可视化（CLI）

```bash
python scripts/visualize.py --project data/video_001 --pose
python scripts/visualize.py --project data/video_001 --robot-viser --robot-all
python scripts/visualize.py --project data/video_001 --robot
```

## Web UI

```bash
conda activate phmr
python -m pip install -U fastapi "uvicorn[standard]" jinja2 python-multipart

# 建议固定端口，避免 iframe 随机端口拒绝连接
pkill -f "video2robot/visualization/robot_viser.py"
export VISER_FIXED_PORT=8789

cd /root/gpufree-data/video2robot
python -m uvicorn web.app:app --host 0.0.0.0 --port 8000
```

浏览器打开：`http://localhost:8000`

## MuJoCo 录制

### 单机器人

```bash
conda activate gmr
cd third_party/GMR
python scripts/vis_robot_motion.py \
  --robot unitree_g1 \
  --robot_motion_path /root/gpufree-data/video2robot/data/video_005/robot_motion.pkl \
  --record_video \
  --video_path /root/gpufree-data/video2robot/data/video_005/mujoco_robot.mp4
```

### 多机器人（本仓库新增）

```bash
conda activate gmr
cd third_party/GMR
python scripts/vis_robot_motion_multi.py \
  --robot unitree_g1 \
  --robot_motion_paths \
    /root/gpufree-data/video2robot/data/video_005/robot_motion_track_1.pkl \
    /root/gpufree-data/video2robot/data/video_005/robot_motion_track_2.pkl \
  --record_video \
  --max_seconds 10 \
  --camera_azimuth 0 \
  --video_path /root/gpufree-data/video2robot/data/video_005/mujoco_multi_robot_10s_front.mp4
```

可选相机参数（轻微拉近）：

- `--camera_distance_scale 0.82`
- `--camera_elevation -8`
- `--camera_lookat_y_offset 0.1`

## Submodule 与补丁策略（推荐）

本项目建议保留 submodule，不建议把 `third_party` 全量并入主仓库（体积会非常大）。

建议交付方式：

1. 记录基线 commit
2. 导出主仓库与 submodule patch
3. 在目标机器应用 patch

### 记录基线 commit

```bash
git rev-parse HEAD
git -C third_party/PromptHMR rev-parse HEAD
git -C third_party/GMR rev-parse HEAD
```

### 生成 patch

```bash
mkdir -p patches
git diff > patches/main.patch
git -C third_party/PromptHMR diff > patches/prompthmr.patch
git -C third_party/GMR diff > patches/gmr.patch
```

### 应用 patch（在同基线上）

```bash
git apply patches/main.patch
git -C third_party/PromptHMR apply ../../patches/prompthmr.patch
git -C third_party/GMR apply ../../patches/gmr.patch
```

## 许可证说明

- 主仓库代码：MIT
- `PromptHMR`：非商业科研限制
- `GMR`：MIT

使用前请确认第三方许可证要求。
