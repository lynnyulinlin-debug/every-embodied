# 发布前检查清单

发布 `tuntunclaw` 公开教程前，逐项确认：

- `.env` 没有进入 Git；
- 飞书应用密钥、多维表格 token 和表格 ID 没有写入源码；
- `sam_b.pt`、模型权重、压缩包和下载产物没有进入 Git；
- `temp/`、`trash/`、`__pycache__/` 和调试截图没有进入 Git；
- `scene_layout_editor.py`、`SCENE_LAYOUT_EDITOR_README.md` 和场景生成脚本没有进入 Git；
- README 中的命令可以在没有真实机械臂的环境下安全阅读和运行；
- 真机控制代码必须放在适配层后面，不要和教程 demo 入口混在一起。
