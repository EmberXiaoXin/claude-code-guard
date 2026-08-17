# 防护分层

目标：Claude Code 只走**探测到的、客户选定的那一个出口**。端口和客户端以 `ccg_detect.py` 的结果为准。

## 层（按能力叠加，不是按作者机器抄）

| 层 | 何时有 | 失败时 |
|---|---|---|
| 时区 | 永远：`TZ` 跟出口地区走 | 时间与出口矛盾 |
| 本地代理绑定 | 永远：Claude 的 HTTP(S)_PROXY 指向 gate，gate 转到探测到的 upstream | 代理没开则拒绝 |
| 出口探测 | 永远：经 upstream 拉 cdn-cgi/trace，`loc` 必须等于选定地区 | Hook block |
| 节点名校验 | 仅 Clash/Mihomo 控制口可用时 | 叶子被改则拒绝 |
| TUN / Rule / IPv6 | 仅控制口能读到这些字段时 | 读到且不安全则拒绝；读不到就不要假装 |
| 专用 listener | 仅 Mihomo 且客户配置支持 | 做不到就退回 mixed-port + 叶子校验 |
| Seatbelt | 仅 macOS | Windows 没有，不要装 |
| 指纹浏览器 | 永远：登录走 Camoufox，代理 = 同一个 upstream | 禁止系统浏览器 |
| 身份清理 | 换号 / 曾被封 | 见 `identity-purge.md` |

## 端口

**不要写死 7897/7898。** detect 会：

- 读 Clash `mixed-port` 或扫描本机已在听的常见代理口
- 给 gate / control 找空闲端口
- 若能加专用 listener，再挑一个空闲口建议给客户合并进配置

`~/.claude-guard/state.json` 是唯一权威。

## Hook

- `--fast`：代理口还在听；有 API 再核对模式 / 叶子
- `--check`：经 **state 里的 upstream** 做地区探测，sticky 90 秒
- 有 gate 时 Hook 发 `CHECK`；没有（或 Windows gate 没起）就直接跑 `ccg_guard.py --check`
- 模型重试也会再检
