# 指纹浏览器（必须绑同一出口）

Claude Code 的 OAuth / 登录页如果用系统 Chrome、Safari、Edge，会用另一条网和另一套指纹。登录必须走 Camoufox（或同等指纹浏览器），代理必须是 `state.json` 的 `upstream_port`，不要写死 7898。

## 原则

1. **同一出口**：浏览器代理 = Claude Gate 的 upstream（探测出来的专用口或 mixed-port）。
2. **同一出口 IP**：启动前经 7898 探测出口；GeoIP 得到时区、locale、经纬度。
3. **一份档案跟一个节点**：节点或出口身份变了，换 profile，不要混 Cookie。
4. **关 WebRTC**：否则 STUN 打出真实网卡 IP。
5. **不要系统浏览器**：`settings.json` 的 `BROWSER` 必须是本 skill 的 `claude-camoufox`。

## 本机已有 Camoufox Persistent 时

`scripts/claude-camoufox.sh` 会调用：

```text
python launch_camoufox.py --strict-network <oauth-url>
```

`--strict-network` 要求：Rule、TUN、AI 策略组叶子 = 绑定节点、经 Claude 域名探测到的 `loc` = 选定区域。不满足就拒绝打开。

启动时用出口 IP 调 Camoufox 的 `geoip` / `get_geolocation`，再：

- `timezone`、`locale` 跟该 IP
- 台湾用繁中系统字体（PingFang TC 等），不要用大陆默认字体去登台湾出口
- `block_webrtc=True`
- `persistent_context` 写在 `~/Library/Application Support/Camoufox Persistent/profiles/<node-hash>/`

已有窗口且是严格模式：只把 URL 塞进队列，不要再开一套身份。

## 客户没有 Persistent 包时

至少满足：

- Camoufox / Playwright 启动参数带 `proxy=http://127.0.0.1:7898`
- `geoip=<经 upstream 测到的出口 IP>`
- `block_webrtc=True`
- 独立 `user_data_dir`，按节点名分目录
- 打不开系统代理就退出，禁止直连

## 换号

旧 Camoufox profile 里的 `cookies.sqlite` 会带着被封账号的 claude.ai 登录态。`purge-identity.sh --purge-browser` 会删这些 profile。先退出浏览器再清。

## 不要做

- 用系统 Chrome / Edge / Safari 登录
- 一个 profile 换多个节点复用
- 开 IPv6 或 WebRTC「提高连通」
- 在防护还没钉死节点时先打开登录页
