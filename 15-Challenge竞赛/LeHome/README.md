# LeHome Challenge 比赛镜像使用教程

本文档面向已经拿到官方 LeHome 比赛镜像、希望尽快开始训练与评测的同学。

重点回答四个问题：

1. 当前镜像环境能不能直接用。
2. 训练应该下载 `merged` 还是非 `merged` 数据。
3. 如何用最小代价启动训练、评测、复现实验。
4. 哪些大文件不要提交进教程仓库。

---

## 1. 当前镜像是否可用

结论：可用。

我已在当前镜像中完成以下验证：

- `LeHome` 仓库路径：`/root/lehome-challenge`
- `isaacsim` 可用：`5.1.0.0`
- `lerobot` 可用：`0.4.3`
- GPU：`NVIDIA L40`
- 已成功跑通一轮 ACT 评测
- 已成功跑通一轮 DP 评测，并且 `--policy_num_inference_steps 1` 生效

本地已验证的输出视频：

- ACT:
  - `/root/gpufree-data/lehome-eval-outputs/repro_videos_act/failure/episode0_observation_images_top_rgb.mp4`
  - `/root/gpufree-data/lehome-eval-outputs/repro_videos_act/failure/episode0_observation_images_left_rgb.mp4`
  - `/root/gpufree-data/lehome-eval-outputs/repro_videos_act/failure/episode0_observation_images_right_rgb.mp4`
- DP:
  - `/root/gpufree-data/lehome-eval-outputs/repro_videos_dp/failure/episode0_observation_images_top_rgb.mp4`
  - `/root/gpufree-data/lehome-eval-outputs/repro_videos_dp/failure/episode0_observation_images_left_rgb.mp4`
  - `/root/gpufree-data/lehome-eval-outputs/repro_videos_dp/failure/episode0_observation_images_right_rgb.mp4`

说明：

- 环境是能启动、能加载模型、能建场景、能完成评测的。
- 当前复现实验结果与官方复现包描述一致，成功率依旧偏低，这更像是任务本身/物理效果问题，不是镜像起不来。

---

## 2. 训练数据该下载哪个

### 2.1 结论

如果目标是尽快开始基线训练，优先下载：

```bash
hf download lehome/dataset_challenge_merged --repo-type dataset --local-dir Datasets/example
```

也就是优先使用 `merged` 版本。

### 2.2 原因

官方训练配置默认就是 `merged` 数据：

- `configs/train_act.yaml` 使用 `Datasets/example/top_long_merged`
- `configs/train_dp.yaml` 使用 `Datasets/example/top_long_merged`
- `configs/train_smolvla.yaml` 使用 `Datasets/example/top_long_merged`

这说明官方预期的训练入口就是“合并后的数据集”。

### 2.3 `merged` 和非 `merged` 的区别

可以这样理解：

- `dataset_challenge`
  - 更偏原始/分散的数据组织。
  - 适合你自己做数据处理、拆分、增广、补深度、补点云。
  - 如果你想研究数据生产流程，或者自己重构训练集，可以用它。
- `dataset_challenge_merged`
  - 更偏训练直接可用的整理结果。
  - 已经按类别合并成 `top_long_merged`、`pant_long_merged` 这类目录。
  - 最适合直接喂给 `lerobot-train`。

### 2.4 深度数据要不要下载

如果你只是先跑通 baseline：

- 先用 `merged`
- 先不用深度
- 先用官方 RGB + joint state 基线

原因：

- 官方文档明确支持 `state + RGB` 作为已验证组合
- 深度虽然可用，但会增加存储、I/O 和配置复杂度
- 官方数据处理文档里还专门给了“去掉 depth 减小存储”的流程

### 2.5 推荐选择

推荐顺序：

1. 入门/比赛 baseline：`dataset_challenge_merged`
2. 需要深度实验：在 `merged` 基础上再加 `observation.top_depth`
3. 需要自己做数据重构：再研究非 `merged` 的 `dataset_challenge`

---

## 3. 最小启动流程

## 3.1 克隆官方仓库

```bash
git clone https://github.com/lehome-official/lehome-challenge.git
cd lehome-challenge
```

如果镜像已经预装好了，直接进入现成目录即可：

```bash
cd /root/lehome-challenge
```

## 3.2 下载资产

```bash
hf download lehome/asset_challenge --repo-type dataset --local-dir Assets
```

## 3.3 下载训练样例数据

```bash
hf download lehome/dataset_challenge_merged --repo-type dataset --local-dir Datasets/example
```

如果只想快速验证一个类别，也可以只下载需要的子目录，例如：

```bash
hf download lehome/dataset_challenge_merged \
  --repo-type dataset \
  --local-dir Datasets/example \
  --include 'top_long_merged/**'
```

## 3.4 训练 ACT

```bash
lerobot-train --config_path=configs/train_act.yaml
```

## 3.5 训练 DP

```bash
lerobot-train --config_path=configs/train_dp.yaml
```

## 3.6 评测 ACT

```bash
python -m scripts.eval \
  --policy_type lerobot \
  --policy_path outputs/train/act/checkpoints/last/pretrained_model \
  --dataset_root Datasets/example/top_long_merged \
  --garment_type top_long \
  --num_episodes 2 \
  --enable_cameras \
  --save_video \
  --video_dir outputs/eval_videos_act \
  --device cpu
```

## 3.7 评测 DP

CPU 评测时建议显式限制 diffusion 推理步数：

```bash
python -m scripts.eval \
  --policy_type lerobot \
  --policy_path outputs/train/dp/checkpoints/last/pretrained_model \
  --dataset_root Datasets/example/top_long_merged \
  --garment_type top_long \
  --num_episodes 2 \
  --enable_cameras \
  --save_video \
  --video_dir outputs/eval_videos_dp \
  --device cpu \
  --policy_device cpu \
  --policy_num_inference_steps 1
```

---

## 4. 推荐训练策略

### 4.1 baseline 配置

建议先从下面这套开始：

- policy: `ACT`
- 输入：`observation.state + top/left/right RGB`
- 输出：`action`
- device: 训练时用 `cuda`
- 评测时 env 用 `cpu`

### 4.2 为什么不建议一上来就上 depth

- 深度会增大数据量和训练复杂度
- baseline 先跑通更重要
- 官方文档明确说 `state + RGB` 已验证可用
- 如果要加 depth，建议在 baseline 收敛后做对照实验

### 4.3 是否建议用 EE pose

不建议作为首选。

官方文档也明确提醒：

- `observation.ee_pose`
- `action.ee_pose`

由于 IK 和硬件限制，稳定性不如 joint-space control。比赛 baseline 更建议用：

- `observation.state`
- `action`

---

## 5. 当前镜像中的推荐保留内容

如果你要把这个教程整理进自己的大仓库，只建议保留这些轻量内容：

- 教程文档
- 训练配置样例
- 评测命令
- 少量日志片段
- 少量截图或短视频链接
- 必要的 patch / overlay 说明

不建议提交这些大资源：

- `Assets/`
- `Datasets/`
- `outputs/`
- `logs/`
- `models/`
- `videos/`
- `plots/`
- `.cache/`
- 任何大于几十 MB 的权重和素材

原因很简单：这些内容都应该通过下载命令获取，不应该进教程子仓库。

---

## 6. 建议的仓库组织方式

建议在 `every-embodied` 中新增如下结构：

```text
15-Challenge竞赛/
└── LeHome/
    ├── README.md
    ├── .gitignore
    └── resources/
        └── commands.md
```

如果后续你还会增加其他比赛，也可以沿用同样的结构。

---

## 7. 可直接复用的检查命令

## 7.1 检查 GPU

```bash
nvidia-smi
```

## 7.2 检查核心包

```bash
python - <<'PY'
import isaacsim, lerobot
print("isaacsim ok")
print("lerobot", getattr(lerobot, "__version__", "unknown"))
PY
```

## 7.3 检查官方资产是否已下载

```bash
ls Assets
ls Datasets/example
```

## 7.4 检查单件服装评测列表

```bash
cat Assets/objects/Challenge_Garment/Release/Release_test_list.txt
```

---

## 8. 镜像发布建议

如果你要宣传这个镜像，建议在说明里强调：

- 已预装官方 LeHome 环境
- 已验证可跑通训练与评测
- 建议首次使用时下载 `asset_challenge` + `dataset_challenge_merged`
- 已适配 `L40` / 服务器场景
- 提供 ACT/DP baseline 启动命令
- 默认不把比赛大资源打进教程仓库

可直接对外描述为：

> 一个面向 LeHome Challenge 的开箱即用镜像，预装 Isaac Sim / LeRobot / LeHome 运行环境，提供训练、评测、数据下载和问题复现的最小闭环。

---

## 9. 本地验证结果

本地已经验证：

- ACT 单 garment 评测可跑通，结果 `Success Rate = 0.00%`
- DP 单 garment 评测可跑通，且 `policy_num_inference_steps=1` 能生效
- 评测视频可以成功导出

这说明：

- 镜像可用
- 训练/评测链路可用
- 教程可以基于这套镜像直接编写和发布

