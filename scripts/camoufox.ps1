$ErrorActionPreference = "Stop"
$guardDir = Join-Path $HOME ".claude-guard"
$python = if ($env:CLAUDE_GUARD_PYTHON) { $env:CLAUDE_GUARD_PYTHON } else { "python" }
& $python (Join-Path $guardDir "ccg_guard.py") --status | Out-Null
if ($LASTEXITCODE -ne 0) { exit 78 }
$state = Get-Content (Join-Path $guardDir "state.json") -Raw | ConvertFrom-Json
$upstream = if ($state.upstream_port) { $state.upstream_port } else { $state.bind_port }
Write-Error "请用 Camoufox（或同等指纹浏览器）经 http://127.0.0.1:$upstream 打开登录页，关闭 WebRTC。不要用 Edge/Chrome。"
exit 78
