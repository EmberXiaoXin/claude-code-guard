# 旧设备 / 旧账号残留

Claude Code 在 macOS 和 Windows 都会留下**设备身份**和**账号凭证**。官方 `/logout` 只丢掉会话，**不会**清 `machineID`。旧号在这台机器上被标记过，再登新号容易秒封。

客户说「换号」或「这台曾经封过」时，先 `ccg_identity.py scan`，确认后 `ccg_identity.py purge --yes`。先退出 Claude / 指纹浏览器。

## 会留下什么

| 位置 | 内容 | 为何危险 |
|---|---|---|
| macOS 钥匙串 / Windows 凭据管理器 `Claude Code-credentials` | `accessToken` + `refreshToken`（刷新链，常被叫做 chain key） | 旧号登录态；新进程会自动续上旧号 |
| `~/.claude.json` → `machineID` | 64 hex，本机长期设备 ID | 换号仍上报同一设备 |
| `~/.claude.json` → `userID` | 64 hex，统计/实验用户键 | 和旧账号绑定 |
| `~/.claude.json` → `oauthAccount` | `accountUuid`、组织、邮箱等 | 旧账号档案 |
| `~/.claude.json` 其它缓存 | `groveConfigCache`、`passesEligibilityCache`、`cachedUsageUtilization`、GrowthBook | 带 account/org |
| `~/.claude/stats-cache.json` | 本机使用统计 | 次要 |
| `~/.claude/telemetry/` | 未送出的事件，含 session / user_type | 次要 |
| `~/.claude/session-env/` | 会话环境 | 次要 |
| Camoufox `profiles/*/browser-data/cookies.sqlite` | claude.ai Cookie | 浏览器侧旧登录 |

硬件 UUID（`ioreg` 的 IOPlatformUUID）清不掉。防护的 PreToolUse 会拦截主动枚举；换号仍然要清上面这些**软件身份**。

## 扫描

```bash
python3 scripts/ccg_identity.py scan
```

只打印「有/无」和路径。禁止打印 token、refresh、machineID 全文、邮箱。

## 清理

```bash
python3 scripts/ccg_identity.py purge --yes
python3 scripts/ccg_identity.py purge --yes --purge-browser
```

备份目录：macOS 在 `~/Library/Application Support/Claude Network Guard Backups/`，Windows 在 `%APPDATA%\Claude Network Guard Backups\`。

默认**保留** `~/.claude/settings.json`、`hooks/`、项目会话记录。不要手滑 `rm -rf ~/.claude`。

清完再装防护，再用 Camoufox 做**第一次**登录。不要先在系统浏览器里登录一次。

## 不要做

- 把钥匙串密码或 `~/.claude.json` 贴进聊天
- 只删 `oauthAccount` 却留着 `machineID`
- Claude 还在跑的时候清钥匙串
- 把作者机器上的备份身份拷到客户机器
