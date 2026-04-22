# 发布清单与忽略规则

这一章用于发布前检查，避免把本机缓存、下载包、板端镜像和临时调试脚本带进公开仓库。

## 必须排除

以下内容不应提交：

- `.cache/`
- `repos/`
- `相关文件下载/`
- `openclaw_magicbox_bundle.tar`
- `tmp_*`
- `_tmp_*.log`
- `page_*.html`
- `openclaw_linux.html`
- `magicbox_index.html`
- `.env`

这些文件大多是下载缓存、第三方仓库、调试脚本或本机运行产物。读者可以按教程重新下载或生成，不需要把它们放进仓库。

## 建议保留

以下内容适合保留：

- `README.md`
- `README_01_环境准备与刷机.md`
- `README_02_有线网口连接与登录.md`
- `README_03_快速入门与基础外设.md`
- `README_04_算法Demo_双目与手势.md`
- `README_05_算法Demo_语音与LLM.md`
- `README_06_OpenClaw部署与接入.md`
- `README_09_飞书控制入口.md`
- `README_10_Windows主机OpenClaw语音桥接与家庭物资助手.md`
- `assets/`

## 提交前检查

在仓库根目录运行：

```bash
git status --short
git ls-files | grep -E "openclaw_magicbox_bundle|相关文件下载|\\.cache/|repos/|tmp_|\\.env$|page_.*\\.html"
```

第二条命令不应该输出任何内容。如果有输出，先检查 `.gitignore` 或从暂存区移除对应文件。

## 说明方式

教程正文只需要告诉读者去哪下载、如何校验和如何运行。不要把完整安装包、开发板镜像或第三方仓库打包进本仓库。
