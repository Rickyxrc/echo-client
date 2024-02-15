## 简介

等稳定了在写。

注意：本项目仍在活跃开发中，下方的所有信息可能会发生改变，请以代码为准。

## 安装

首先您需要正确地在 OBS 中安装 Echo-live。

然后定位到 `config.js` 的 websocket 这部分，将 `websocket_enable` 改为 `true`。

下方的 `websocket_url` 中请填写服务端的 ip 地址与端口号。（如果您在一台电脑上同时运行 OBS 和本程序则 ip 可以写 `127.0.0.1`）

```js
        // 启用 WebSocket
        // * 如果没人要求您这么做，请不要动它。
        // * 广播模式下启用 WebSocket 可连接至服务器以从第三方软件获取消息。
        // * 可从服务器接收的消息和广播消息一致，发送的消息须使用类似于 JSON.stringify 的方法序列化。
        // * 详见：https://sheep-realms.github.io/Echo-Live-Doc/dev/broadcast/
        websocket_enable: true,
        // WebSocket 连接地址
        // websocket_url: 'ws://192.168.1.12:3000', // iPad
        websocket_url: 'ws://127.0.0.1:3000',
```

如果您在两台设备上分别运行 OBS 和本程序，请务必将 `server.py` 的 `host = "127.0.0.1"` 修改为 `host = "0.0.0.0"`（监听局域网）。

如果您有 python 环境，请使用如下命令安装（不推荐，还在开发）

```sh
pip install echo-client
```

## 配置

还没写。

