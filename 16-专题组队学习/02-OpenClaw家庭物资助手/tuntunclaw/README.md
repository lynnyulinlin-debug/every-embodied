# tuntunclaw 代码目录

这个目录用于放置 OpenClaw 家庭物资助手专题中可公开的 `tuntunclaw` 代码。

后续迁入代码时，建议只保留读者复现实验需要的最小集合：

- `frontend/`
- `openclaw_like/`
- `inventory.py`
- `integrations.py`
- `workflow_hooks.py`
- `main.py`
- `requirements-py311.txt`
- `.env.example`

不要提交以下内容：

- `.env`
- `sam_b.pt`
- `temp/`
- `trash/`
- `__pycache__/`
- `mask_*.png`
- `scene_layout_editor.py`
- `SCENE_LAYOUT_EDITOR_README.md`

场景编辑器和本地调试产物不属于公开教程范围。读者需要的是能复现家庭物资助手闭环的代码，而不是本机开发过程中的完整工作目录。
