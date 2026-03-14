# LeHome 常用命令速查

## 下载资产

```bash
hf download lehome/asset_challenge --repo-type dataset --local-dir Assets
```

## 下载合并训练集

```bash
hf download lehome/dataset_challenge_merged --repo-type dataset --local-dir Datasets/example
```

## 训练 ACT

```bash
lerobot-train --config_path=configs/train_act.yaml
```

## 训练 DP

```bash
lerobot-train --config_path=configs/train_dp.yaml
```

## 评测 ACT

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

## 评测 DP

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
