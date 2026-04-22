# RDK X5 Magicbox 教程工程（从 0 到 Demo）

本目录用于编写新款 `RDK X5 Magicbox` 的中文教程，目标是形成一套可直接交付的“开发板式”学习路径，并把近期热度较高的 `OpenClaw` 作为扩展平台整合进来：

1. 开箱与系统准备
2. 快速入门与基础外设
3. 视觉 Demo（双目深度、手势）
4. 本机语音 + LLM 原生链路
5. OpenClaw 在 Magicbox 上的部署与接入
6. FAQ/已知问题/排障

## 1. 教程总大纲

- [README_01_环境准备与刷机.md](./README_01_环境准备与刷机.md)
- [README_02_快速入门与基础外设.md](./README_02_快速入门与基础外设.md)
- [README_03_算法Demo_双目与手势.md](./README_03_算法Demo_双目与手势.md)
- [README_04_算法Demo_语音与LLM.md](./README_04_算法Demo_语音与LLM.md)
- [README_05_OpenClaw部署与接入.md](./README_05_OpenClaw部署与接入.md)
- [README_06_排障与发布建议.md](./README_06_排障与发布建议.md)

## 2. 已拉取的参考仓库（本地）

已克隆到 `./repos`：

- `hobot_stereonet`
- `magicbox_gesture_interaction`
- `magicbox_audio_io`
- `magicbox_qwen_llm`
- `openclaw`
- `sherpa-onnx`

说明：

- 文档中出现的 `https://github.com/D-Robotics/magicboxaudioio` 仓库当前不存在（2026-03-06 验证）。
- `magicbox_audio_io` 克隆时遇到 1 个 Git LFS 大文件 404（`SenseVoiceGGUF/sense-voice-small-fp16.gguf`），不影响先编写教程结构，但后续需要补齐模型下载方案。
- `OpenClaw` 官方仓库与文档已核对：
  - 仓库：https://github.com/openclaw/openclaw
  - 文档：https://docs.openclaw.ai
  - Linux 安装主线：`npm install -g openclaw@latest` 后执行 `openclaw onboard --install-daemon`

## 3. 官方资料入口（已核对）

- 在线文档首页：https://d-robotics.github.io/magicbox_doc/magicbox
- 章节：
  - 产品概述：https://d-robotics.github.io/magicbox_doc/magicbox
  - 快速入门：https://d-robotics.github.io/magicbox_doc/quickstart
  - 基础外设：https://d-robotics.github.io/magicbox_doc/basic-peripherals
  - 资源下载：https://d-robotics.github.io/magicbox_doc/resource-download
  - 算法开发：https://d-robotics.github.io/magicbox_doc/algorithm-development
  - FAQ：https://d-robotics.github.io/magicbox_doc/faq
  - 已知问题：https://d-robotics.github.io/magicbox_doc/known_issues
  - 更新日志：https://d-robotics.github.io/magicbox_doc/changelog
  - 技术支持：https://d-robotics.github.io/magicbox_doc/technical-support

## 4. 重构后的主线

为了把 `OpenClaw` 合理融入教程，当前文档按两条能力线拆开：

1. `Magicbox 原生能力线`
   - 刷机、联网、基础外设、双目、手势、语音、LLM
2. `平台扩展能力线`
   - 在 Magicbox 上部署 `OpenClaw Gateway`
   - 接入 WebChat / Telegram / Feishu 等远程入口
   - 预留和本地 ROS 动作、灯光、语音链路的桥接点

这样可以避免把 `OpenClaw` 和板端原生 ROS demo 混写，后续扩写时层次更清楚。

## 5. 建议交付物结构

- 阶段 1（本轮完成）：教程大纲 + 章节拆分 + 参考仓库落地
- 阶段 2（下一轮可继续）：
  - 为每个章节补齐实机截图位
  - 每个 Demo 补齐“预期现象 / 失败现象 / 回滚步骤”
  - 加入一键启动脚本（可选）
  - 增加 OpenClaw 与本地 ROS/脚本动作桥接示例

## 6. 版本信息

- 文档抓取时间：2026-03-06
- 本地 PDF：`d_robotics_rdk_x5_magicbox_zh_v1.0.pdf`（7 页）
- 在线文档最近更新时间（页面显示）：
  - 核心章节多为 `2026-03-05`
  - FAQ/已知问题/更新日志/技术支持为 `2026-03-06`
