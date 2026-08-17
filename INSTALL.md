# Claude Code 防封 Skill — 安装说明

解压后得到 `claude-code-guard/` 目录。

## 1. 装到 AI 工具里

在解压后的目录里执行（或把路径改成你的实际位置）：

```bash
# Grok
mkdir -p ~/.grok/skills
ln -s "$PWD/claude-code-guard" ~/.grok/skills/claude-code-guard

# Claude Code
mkdir -p ~/.claude/skills
ln -s "$PWD/claude-code-guard" ~/.claude/skills/claude-code-guard
```

Windows：把整个文件夹拷到 `%USERPROFILE%\.grok\skills\claude-code-guard` 或 `%USERPROFILE%\.claude\skills\claude-code-guard`。

新开一个对话，输入 `/claude-code-guard`。

## 2. 必须先选一个固定节点

先打开你自己的梯子，然后：

```bash
python3 claude-code-guard/scripts/ccg_detect.py --list
```

Windows 用 `py -3` 或 `python`。

从清单里选 **一个固定叶子节点**（推荐台湾家宽，不要选自动切换）。把完整名字发给帮你配置的人，或自己执行：

```bash
python3 claude-code-guard/scripts/ccg_install.py --node "这里换成你选的完整节点名" --region TW
```

没选定节点之前不要装防护、不要登录。

## 3. 这台电脑如果以前封过号

先退出 Claude，再扫描 / 清理旧凭证（不会打印密码）：

```bash
python3 claude-code-guard/scripts/ccg_identity.py scan
python3 claude-code-guard/scripts/ccg_identity.py purge --yes
```

换号再加 `--purge-browser`。

完整流程见 `SKILL.md`。
