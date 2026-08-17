# 按客户梯子决策

先 `ccg_detect.py`，再选施工路径。禁止默认 Clash Verge + macOS。

## Clash / Mihomo 系

包括 Clash Verge（Mac/Win）、Clash for Windows、独立 mihomo。特征：本机控制口（unix socket 或 `127.0.0.1:9090/9097/...`）能 `GET /proxies`。

可做：列出叶子、推荐台湾关键字、校验当前组叶子、尽量加 `listeners` 钉死节点。

TUN / Rule / 关 IPv6：控制口读到才强制。Windows 上 TUN 经常没开，只警告；macOS 的 Clash 读到 TUN 关闭则 `--fast` 失败。

## 只有本地端口（v2rayN、sing-box、Nekoray、Hiddify…）

列不出节点名。流程改成：

1. 请客户在客户端里点一个固定节点（不要自动切换），并把**名字**发过来。
2. 安装仍必须 `--node '那个名字'`。
3. Claude / Camoufox 走探测到的本地代理口。
4. `--check` 只能校验出口地区，不能再核对叶子名。

## 什么都没有

停。让客户先打开梯子。

## Windows 特有

- 无 Seatbelt：`wrapper.ps1` 只设代理环境变量
- 凭据在 Windows 凭据管理器，不是钥匙串
- Hook 用 `python hook_*.py`，不要依赖 zsh
- 指纹浏览器同样要绑 `upstream_port`，不要用 Edge
