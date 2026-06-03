# CB Monitor

极简异步 CLI：读取 Chaturbate 关注主播列表，解析直播间 HLS/m3u8 清晰度，并用 `mpv` 播放。

## Setup

```powershell
uv sync
copy .env.example .env
```

`.env` 最小配置：

```env
CB_COOKIE_FILE=./cookies/Tokyo.txt
CB_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36
CB_PROXY_URL=http://127.0.0.1:7890
CB_MPV_PATH=mpv
CB_LOG_LEVEL=INFO
```

说明：

- `CB_COOKIE_FILE` 支持 Netscape `cookies.txt`。
- `CB_USER_AGENT` 必须和通过验证的 Chrome 一致。
- `CB_PROXY_URL` 留空时使用系统代理；Chrome 使用代理客户端/插件时建议显式填写 HTTP 或 mixed 端口。
- `cf_clearance` 会从 Cookie 文件读取；也可用 `CB_CF_CLEARANCE` 覆盖。

## Run

```powershell
uv run cb_monitor
```

流程：读取在线关注主播，选择主播，选择清晰度，启动 `mpv`。

## Quality

```powershell
ruff check
ruff format
pytest
pyright
```

## Troubleshooting

- `Cloudflare 已拦截当前会话`：在同一节点的 Chrome 完成验证，重新导出 Cookie，确认 `CB_USER_AGENT` 和 `CB_PROXY_URL`。
- `未解析到正在直播的关注主播`：确认关注列表里确实有在线主播，且 Cookie 属于正确账号。
- `未找到 mpv`：把 `mpv` 加入系统环境变量，或设置 `CB_MPV_PATH` 为完整路径。
