"""
websocket 服务器模块
这可能是我这辈子到现在代码文档写的最详细的一次ww
"""
import asyncio
import json

import websockets
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from rich.console import Console

from .message import parse_message, render

# TODO: 用配置文件来改这些，别修改源代码
config = {}
config["command_prefix"] = "/"
config["username"] = "/"
config["host"] = "127.0.0.1"
config["port"] = 3000

console = Console()

events = []

# 生成连续递增的 client 编号
# pylint: disable=invalid-name
client_id = 0


async def get_message(websocket, cid):
    """
    从 Echo client 处接收消息并显示（或回传一些内容）
    """

    async for message in websocket:
        data = json.loads(message)
        response = f"客户端{cid}: "
        _data_response = None
        if data["action"] == "hello":
            response += "上线"
            await websocket.send(
                json.dumps(
                    {
                        "action": "message_data",
                        "data": {
                            "username": "系统",
                            "messages": [
                                {
                                    "message": [
                                        {"text": "websocket服务器，", "pause": 15},
                                        {"text": "连接成功！", "event": "shout"},
                                    ]
                                },
                            ],
                        },
                    }
                )
            )

        elif data["action"] == "close":
            response += "发出下线请求"
        elif data["action"] == "page_hidden":
            response += "页面被隐藏"
        elif data["action"] == "page_visible":
            response += "页面恢复显示"
        else:
            response += f"发送了未知事件，事件原文: {data}"
        console.log(response)


async def listen_queue(websocket, cid):
    """
    监听事件队列，如果有啥事情就执行
    """
    proceed = 0
    while True:
        await asyncio.sleep(1)
        if proceed < len(events):
            for event in events[proceed:]:
                console.log(f"客户端{cid}: 执行 {event}")
                if event["action"] == "message_data":
                    console.log(f"客户端{cid}: 发送文字信息")
                    await websocket.send(event["data"])
                else:
                    console.log(f"[red]客户端{cid}: 上面那个事件的实现程序还没写呢！执行不了！[/red]")
            proceed = len(events)


async def echo(websocket, _path):
    """
    websocket 连接上就执行这个
    """
    # pylint: disable=global-statement
    try:
        global client_id
        client_id += 1
        cid = client_id
        console.log(f"客户端{client_id}: 已建立连接")
        listen = asyncio.create_task(listen_queue(websocket, cid))
        get = asyncio.create_task(get_message(websocket, cid))
        await listen
        await get
    except websockets.exceptions.ConnectionClosedOK:
        console.log(f"客户端{client_id}: 连接已断开")


async def run_input():
    """
    获取用户输入，执行命令
    """
    # pylint: disable=global-statement
    session = PromptSession()
    while True:
        with patch_stdout(raw=True):
            input_data = await session.prompt_async("请输入命令: ")
        # TODO: 这个太简陋了，考虑用 argparse 之类的库在这里解析命令
        if input_data == "":
            console.log("[red]打个字再回车啊宝！[/red]")
        elif input_data[0] != config["command_prefix"]:
            console.log(f"发送文字消息: {input_data}")
            events.append(
                {
                    "action": "message_data",
                    "data": render(config, parse_message(input_data)),
                }
            )
        else:
            console.log(f"执行命令：{input_data}")
            commands = input_data.split(" ")
            if commands[0][1:] in ["rename", "ren"]:
                if len(commands) == 2:
                    console.log(f"[green]已经将显示名称更改为 {commands[1]}[/green]")
                    config["username"] = commands[1]
                else:
                    console.log("[red]命令接受一个参数，不多不少。[/red]")
            elif commands[0][1:] in ["quit", "q"]:
                console.log("拜拜~")
                # TODO: 消掉退出时的错误提示
                raise SystemExit(3)  # 就是用来退出的别见怪
            else:
                console.log(
                    f"[red]用 COMMAND_PREFIX（当前为'{config['command_prefix']}'）开头的消息"
                    "将会被作为命令解析，这个功能还没做好，不急！！！！[/red]"
                )


asyncio.get_event_loop().run_until_complete(
    websockets.serve(echo, config["host"], config["port"])
)

console.log(
    f"[green]已经在 {config['host']}:{config['port']} 监听 websocket 请求，等待 echo 客户端接入...[/green]"
)
console.log("[blue]tips: 如果没有看到成功的连接请求，可以尝试刷新一下客户端[/blue]")

asyncio.get_event_loop().create_task(run_input())
console.log("[green]用户输入模块加载成功，您现在可以开始输入命令了，客户端连接后会自动执行！[/green]")

asyncio.get_event_loop().run_forever()
