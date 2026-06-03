# CB Monitor

CB Monitor 是一个 Windows 上运行的绿色版异步 CLI 工具，用于读取当前 Chaturbate 账号的 `followed-cams` 在线主播列表，选择主播后解析该直播间的 HLS/m3u8 清晰度列表，并调用本机 `mpv` 播放选定分辨率的视频流。

项目目标是轻量、清晰、可维护：只做在线关注主播监视、直播流解析和播放器启动，不做录制、不做批量下载、不做绕过访问权限的行为。

## 功能

- 读取 `https://chaturbate.com/followed-cams/` 当前账号可访问的在线关注主播。
- 通过 Chaturbate 页面实际使用的 room-list API 获取在线主播列表。
- 使用 `questionary` 提供美观的终端选择界面。
- 主播列表 10 分钟无操作自动刷新。
- 主播选择和清晰度选择前自动清屏，避免终端日志堆积。
- 支持手动刷新在线主播列表。
- 支持从清晰度选择界面返回主播列表。
- 主播下播、房间无流、网络波动时不会直接退出，会回到选择流程。
- 解析 master m3u8 中的不同分辨率视频流。
- 将选定分辨率的视频 m3u8 地址交给 Windows 上的 `mpv` 播放。
- 支持 Netscape 格式 `cookies.txt`，适配 Get cookies.txt local 插件导出的 Cookie 文件。
- 第二步访问直播间页面和请求 master m3u8 时使用系统代理。
- 使用 Loguru 输出清晰的终端日志。
- 使用 Ruff、Pyright strict、Pytest 保持代码质量。

## 环境要求

- Windows
- uv
- Python 3.14
- mpv 已安装并加入系统环境变量
- 有可访问 `followed-cams` 的 Chaturbate 登录 Cookie

确认 mpv 可用：

```powershell
mpv --version
```

确认 uv 可用：

```powershell
uv --version
```

## 安装

把项目解压到任意英文或中文路径均可。推荐路径中不要包含会频繁变化的临时目录。

进入解压后的项目目录，也就是包含 `pyproject.toml` 的目录：

```powershell
cd 你的解压目录\CB_Monitor
```

同步依赖：

```powershell
uv sync
```

## 配置 Cookie

复制示例配置：

```powershell
copy .env.example .env
```

推荐使用 Get cookies.txt local 插件导出的 Netscape 格式 `cookies.txt`：

```env
CB_COOKIE_FILE=C:\Users\你的用户名\Downloads\cookies.txt
```

为了减少路径错误，绿色版推荐把导出的 Cookie 文件放到项目根目录，然后这样配置：

```env
CB_COOKIE_FILE=cookies.txt
```

如果你误把 `cookies.txt` 文件路径填进了 `CB_COOKIE`，程序也会自动识别 `.txt` 文件路径：

```env
CB_COOKIE=C:\Users\你的用户名\Downloads\cookies.txt
```

也可以直接填浏览器 Cookie 字符串：

```env
CB_COOKIE=sessionid=...; csrftoken=...
```

`.env.example` 中的主要配置：

```env
CB_COOKIE=
CB_COOKIE_FILE=
CB_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36
CB_TIMEOUT_SECONDS=15
CB_RETRY_ATTEMPTS=3
CB_MPV_PATH=mpv
CB_LOG_LEVEL=INFO
```

## 运行

```powershell
uv run cb_monitor
```

运行后程序会：

1. 拉取在线关注主播列表。
2. 显示本次刷新时间和自动刷新倒计时。
3. 等待用户选择主播。
4. 进入主播直播间页面解析 master m3u8。
5. 输出可选清晰度。
6. 调用 mpv 播放选中的视频流。
7. 播放器启动后回到主播选择界面继续等待。

每次回到主播列表或进入清晰度列表前，程序都会自动清屏，终端不会一直累积旧日志。

## 交互说明

主播选择界面包含：

```text
   本次刷新时间: 21:38:31                      自动刷新倒计时: 09:59
»  1. nicolle_mitchelle
   2. linda_warners
     手动刷新列表
     退出
```

- 使用方向键移动。
- 按 Enter 确认。
- 选择 `手动刷新列表` 会立即重新拉取在线主播。
- 10 分钟无操作会自动刷新在线主播。
- 选择 `退出` 会结束程序。

清晰度选择界面包含：

```text
» 1. 1080p · 1920x1080 · 7128 kbps
  2. 720p · 1280x720 · 4596 kbps
    返回主播列表
    退出
```

- 选择清晰度后会启动 mpv。
- 选择 `返回主播列表` 会回到主播选择界面。
- 选择 `退出` 会结束程序。

## 代理说明

程序分两段访问网络：

- 读取 followed-cams 页面和在线主播 API。
- 访问主播直播间页面并请求 master m3u8。

其中第二段会使用系统代理，方便访问直播间页面和流信息。mpv 播放阶段由 mpv 自己处理网络环境。如果你已经在 mpv 中配置代理，程序不会额外传递代理参数。

## 播放说明

当前版本只播放所选分辨率的视频 m3u8，不额外合成音轨。

原因是 Chaturbate 的低延迟 HLS 常见音视频分离结构，不同 mpv 环境下强行合成音轨可能导致画面卡住或播放失败。为了稳定播放，项目保留最直接、最可靠的方式：把选定分辨率的视频地址交给 mpv。

mpv 播放阶段不会额外传入代理、User-Agent 或 Referer 参数。如果你需要代理，请直接在 mpv 自己的配置中设置。

## 项目结构

```text
CB_Monitor/
├── pyproject.toml
├── uv.lock
├── README.md
├── .env.example
├── src/
│   └── cb_monitor/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── cookies.py
│       ├── errors.py
│       ├── followed.py
│       ├── http_client.py
│       ├── logging.py
│       ├── models.py
│       ├── player.py
│       ├── playlist.py
│       └── room.py
└── tests/
    ├── test_config.py
    ├── test_cookies.py
    ├── test_followed.py
    ├── test_playlist.py
    └── test_room.py
```

## 模块职责

- `cli.py`: 终端交互、菜单循环、自动刷新、用户选择。
- `config.py`: Pydantic Settings 配置读取与校验。
- `cookies.py`: Netscape cookies.txt 和直接 Cookie 字符串解析。
- `followed.py`: followed-cams 登录校验和在线关注主播 API 解析。
- `http_client.py`: httpx 异步请求、超时、重试、系统代理、URL 脱敏日志。
- `room.py`: 主播房间页 master m3u8 提取。
- `playlist.py`: master m3u8 分辨率解析。
- `player.py`: Windows mpv 启动。
- `models.py`: Pydantic V2 数据模型。
- `errors.py`: 业务异常。
- `logging.py`: Loguru 输出配置。

## 开发检查

格式化：

```powershell
uv run ruff format .
```

静态分析：

```powershell
uv run ruff check .
```

严格类型检查：

```powershell
uv run pyright
```

测试：

```powershell
uv run pytest
```

一次性运行全部检查：

```powershell
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest
```

如果 `cb_monitor.exe` 正在运行，`uv run` 可能因为 Windows 文件占用而无法同步项目。先退出正在运行的程序，或者临时使用：

```powershell
uv run --no-sync pytest
uv run --no-sync pyright
```

## 代码质量

本项目采用：

- `uv` 管理依赖与虚拟环境
- `pyproject.toml` 统一项目、依赖、Ruff、Pyright、Pytest 配置
- `Ruff` 负责格式化和 lint
- `Pyright strict` 负责类型安全
- `Pydantic V2` 负责运行时数据校验
- `httpx` 负责异步 HTTP
- `tenacity` 负责重试
- `Loguru` 负责终端日志
- `questionary` 负责终端选择界面

## 安全与边界

- 不在源码中写入 Cookie。
- 不输出 Cookie 值。
- 不在 debug 日志中暴露 m3u8 token。
- `.env`、`cookies.txt`、虚拟环境、缓存、日志和媒体产物都已加入 `.gitignore`。
- 只访问当前 Cookie 本身有权限访问的 followed-cams 和主播房间页面。
- 不做权限绕过、爆破、批量压测或平台限制规避。

## 绿色版建议

如果你希望解压即用，推荐目录保持如下形式：

```text
CB_Monitor/
├── .env
├── cookies.txt
├── pyproject.toml
├── uv.lock
├── README.md
├── src/
└── tests/
```

`.env` 中使用相对路径：

```env
CB_COOKIE_FILE=cookies.txt
CB_MPV_PATH=mpv
```

运行时始终先进入项目根目录：

```powershell
cd 你的解压目录\CB_Monitor
uv run cb_monitor
```

这样 Cookie 文件路径、`.env` 读取和 uv 虚拟环境路径都最稳定。

## 常见问题

### 提示 Cookie 失效

重新用浏览器登录 Chaturbate，然后用 Get cookies.txt local 插件重新导出 `cookies.txt`，更新 `.env` 中的路径。

### 主播列表为空

可能是当前没有关注主播在线，也可能是 Cookie 没有读取到正确账号。先确认浏览器页面上 `FOLLOWING` 是否显示在线数量。

### 房间无可播放直播流

主播可能刚下播，或者房间页面结构临时变化。程序会自动回到主播选择界面。

### mpv 没有启动

确认 `mpv` 已加入系统环境变量，或者在 `.env` 中配置完整路径：

```env
CB_MPV_PATH=C:\Program Files\mpv\mpv.exe
```

### 播放没有声音

当前版本只播放选中分辨率的视频 m3u8，不合成音轨。这是为了保持播放稳定性。

## License

本项目仅用于个人学习和自动化实践。推送到公开仓库前，请根据你的使用场景补充合适的许可证。
