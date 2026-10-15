# Python 机器人接口

本项目提供本地 HTTP API，把已有 AI 机器人的文字、表情和语音接到智乃网页形象上。不包含大模型、语音合成或语音识别服务；这些由你的机器人提供。

## 快速开始

需要 Python 3.10+ 和现代 Chrome / Edge。Python 端只使用标准库，无需 pip 安装。

1. 在项目目录执行 `python avatar_server.py`。
2. 打开 <http://127.0.0.1:8765/?robot=1>，等待形象出现。
3. 点击页面上的“启用机器人语音”（浏览器要求用户手动授权音频播放）。
4. 另开终端执行 `python examples/robot_client.py`，查看字幕和微笑表情。
5. 测试语音：`python examples/robot_client.py "你的语音.wav"`。可用浏览器支持的 WAV、MP3 等音频。

普通离线双击 HTML 的方式仍可使用；机器人连接需运行服务器并带上 `?robot=1`。机器人模式会关闭随机口型、麦克风和面部追踪输入，保留眨眼和待机动作；语音播放期间由音量驱动简化嘴型，结束或停止时闭嘴。不是音素级口型。

## 接到已有机器人

把 `examples/robot_client.py` 的 `send` 和 `say` 函数复制到你的程序，或者把 examples 目录加入 Python 导入路径。假设 AI 与语音合成已有结果：

```python
from robot_client import send, say

# reply = 你的大模型返回的文字
# wav_path = 你的语音合成生成的文件路径
reply = "欢迎回来，今天想聊些什么？"
wav_path = "reply.wav"
send({"type": "expression", "name": "smile"})
say(reply, wav_path)

# 想打断当前语音时：
send({"type": "stop"})
```

首次接入建议先 `say(reply)` 验证字幕，再传音频路径。API 密钥保留在自己的 Python 机器人中，不放到网页里。

## HTTP 协议

`POST http://127.0.0.1:8765/api/command`，请求头 `Content-Type: application/json`。

| 目的 | JSON 请求 |
| --- | --- |
| 文字字幕 | `{"type":"say","text":"你好"}` |
| 字幕与语音 | `{"type":"say","text":"你好","audio":"/reply.wav"}` |
| 表情 | `{"type":"expression","name":"smile"}` |
| 参数 | `{"type":"params","values":{"angleX":0.3,"mouthOpen":0.5}}` |
| 停止语音、闭嘴并清除字幕 | `{"type":"stop"}` |

表情：`neutral`、`smile`、`usume`、`surprise`、`jito`、`winkL`、`winkR`。

`audio` 可以是项目目录内文件的 `/相对路径`，或者 `data:audio/wav;base64,...`。示例客户端会自动把本地音频编码为 data URL，因此无需把音频复制到项目目录。禁止外部音频 URL；单个 JSON 请求上限 16 MiB，base64 会增加约三分之一体积。较长语音可使用项目目录内音频路径。新 `say` 替换当前语音；播放失败或尚未启用音频时仍显示字幕，页面按钮提示原因，启用后请重新发送。

参数沿用网页滑条名称与范围，例如头部 `angleX/angleY/angleZ`（-1～1）、`eyeOpenL/eyeOpenR`（0～1）、`mouthOpen`（0～1）、`mouthForm`（-1～1）。数值在浏览器端限制到对应滑条范围，未知参数忽略。

成功返回 `{"ok":true,"id":1}`，表示服务器已接收，**不代表浏览器已播放成功**。浏览器每 100ms 轮询 `GET /api/commands?after=事件编号`。暂存最近 100 条命令，仅适合本地单机器人演示，不是持久消息队列；刷新网页会重放缓存中的命令，重启服务器会清空缓存。

服务器仅监听 `127.0.0.1:8765`，不开放跨域访问。请保持本地使用，不直接映射到公网；它提供项目目录的静态文件访问，项目目录内不要放密钥或私人文件。直接 JavaScript 或 pywebview 集成也可调用 `window.ChinoAvatar.robotMode()`、`.expression(name)`、`.params(values)` 和 `.mouth(0到1)`。

## 验证

运行 `python -m unittest discover -s tests` 检查 HTTP API。开发用浏览器集成测试可在安装 Playwright 后执行 `node tests/browser.cjs`（先启动服务器）。
