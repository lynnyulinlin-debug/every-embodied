# 语音按钮灯效与桌宠流程

这一章把桌宠交互拆成四类可验证动作：语音、按钮、灯效和舵机。每一类动作都先检查状态，再执行命令，最后确认设备是否响应。

## 语音链路

语音链路通常包含 ASR、LLM 对话和 TTS 播报。调试时不要一开始就让 agent 直接说话，先确认语音服务状态。

```bash
sudo /userdata/magicclaw/runtime/bin/magicboxctl voice status
sudo /userdata/magicclaw/runtime/bin/magicboxctl voice asr start
sudo /userdata/magicclaw/runtime/bin/magicboxctl voice chat start
sudo /userdata/magicclaw/runtime/bin/magicboxctl voice say "你好，我是桌宠助手"
```

## 按钮链路

按钮适合绑定几个固定动作，例如唤醒语音、切换灯效或触发手势 demo。

```bash
sudo /userdata/magicclaw/runtime/bin/magicboxctl buttons show
sudo /userdata/magicclaw/runtime/bin/magicboxctl buttons set left stereo
sudo /userdata/magicclaw/runtime/bin/magicboxctl buttons set middle gesture
sudo /userdata/magicclaw/runtime/bin/magicboxctl buttons set right voice_chat
sudo /userdata/magicclaw/runtime/bin/magicboxctl buttons invoke right
```

## 灯效链路

灯效适合用来给桌宠反馈当前状态：待机、听取指令、执行中、完成或失败。

```bash
sudo /userdata/magicclaw/runtime/bin/magicboxctl led preset blue
sudo /userdata/magicclaw/runtime/bin/magicboxctl led blink green 3 0.2
sudo /userdata/magicclaw/runtime/bin/magicboxctl led off
```

## 舵机链路

舵机动作要限制角度，避免在演示中反复打到极限位置。教程中建议使用小角度动作表达点头、招手或提醒。

```bash
sudo /userdata/magicclaw/runtime/bin/magicboxctl servo set left 15
sudo /userdata/magicclaw/runtime/bin/magicboxctl servo set right 45
sudo /userdata/magicclaw/runtime/bin/magicboxctl servo greet 1
```

## 推荐桌宠流程

1. 灯效切到待机色
2. 用户通过飞书或按钮触发任务
3. 桌宠播报当前动作
4. OpenClaw Gateway 执行对应工具
5. 灯效或舵机反馈结果
6. 飞书返回状态摘要

## 排障顺序

先检查 SSH 和 `magicboxctl status`，再检查具体子命令。不要直接把失败归因到 OpenClaw agent，板端服务、权限和音频链路都可能是原因。
