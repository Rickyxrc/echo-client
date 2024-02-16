"""
websocket 服务器模块
这可能是我这辈子到现在代码文档写的最详细的一次ww
"""
import asyncio
import json
import os

import websockets
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from rich.console import Console

from .message import get_delay, parse_message, render

# TODO: 用配置文件来改这些，别修改源代码
config = {}
config["command_prefix"] = "/"
config["username"] = "/"
config["host"] = "127.0.0.1"
config["port"] = 3000
config["typewriting"] = False
# 自动在某些字符后面等待，自动在行末等待
# 本质是文本替换，不知道有没有问题
config["autopause"] = False
# 在哪些字符后面等待呢？
config["autopausestr"] = ",，.。;；:：!！"
# 等待多久呢？
config["autopausetime"] = 20

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
                                        {
                                            "text": "websocket服务器，",
                                            "pause": 15,
                                            "typewrite": "websocketfu'wu'qi",
                                        },
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
        console.print(response)


async def listen_queue(websocket, cid):
    """
    监听事件队列，如果有啥事情就执行
    """
    proceed = 0
    while True:
        await asyncio.sleep(1)
        if proceed < len(events):
            for event in events[proceed:]:
                console.print(f"客户端{cid}: 执行 {event}")
                if event["action"] == "message_data":
                    console.print(f"客户端{cid}: 发送文字信息")
                    await websocket.send(event["data"])
                    await asyncio.sleep(event["delay"] / 1000.0)
                else:
                    console.print(f"[red]客户端{cid}: 上面那个事件的实现程序还没写呢！执行不了！[/red]")
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
        console.print(f"客户端{client_id}: 已建立连接")
        listen = asyncio.create_task(listen_queue(websocket, cid))
        get = asyncio.create_task(get_message(websocket, cid))
        await listen
        await get
    except websockets.exceptions.ConnectionClosedOK:
        console.print(f"客户端{client_id}: 连接已断开")


def parse_command(command: str) -> None:
    """
    解析用户输入的内容
    递归是因为要使用 source 来解析文件中的内容（适合预演）
    """
    # TODO: 这个太简陋了，考虑用 argparse 之类的库在这里解析命令

    # pylint: disable = global-variable-not-assigned
    global config
    if command == "":
        console.print("[red]打个字再回车啊宝！[/red]")
    elif command[0] != config["command_prefix"]:
        if config["autopause"]:
            delay_str = f"/d{config['autopausetime']}"
            command_tmp = ""
            for index, ch in enumerate(command):
                if ch in config["autopausestr"] and (
                    index != len(command) - 1
                    and command[index + 1] not in config["autopausestr"]
                ):  # 不要重复delay，像'！！！'这样的情况在最后添加/d20
                    command_tmp += ch + delay_str
                else:
                    command_tmp += ch
            if not command_tmp.endswith(delay_str):  # 别加重复了宝
                command_tmp += delay_str
            command = command_tmp
        console.print(f"发送文字消息: {command}")
        syntax = parse_message(command)
        events.append(
            {
                "action": "message_data",
                "data": render(config, syntax),
                "delay": get_delay(syntax),
            }
        )
    else:
        console.print(f"执行命令：{command}")
        commands = command.split(" ")
        if commands[0][1:] in ["rename", "ren"]:
            if len(commands) == 2:
                console.print(f"[green]已经将显示名称更改为 {commands[1]}[/green]")
                config["username"] = commands[1]
            else:
                console.print("[red]命令接受一个参数，不多不少。[/red]")
        elif commands[0][1:] in ["quit", "q"]:
            console.print("拜拜~")
            # TODO: 消掉退出时的错误提示
            raise SystemExit(3)  # 就是用来退出的别见怪
        elif commands[0][1:] in ["source", "s"]:
            if len(commands) == 2:
                path = os.path.join(os.getcwd(), commands[1])
                console.print(f"[blue]从文件 {path} 中载入内容（文件中的每一行会被作为独立的部分输入到控制台里！）[/]")
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        texts = file.read().splitlines()
                        for text in texts:
                            if text == "" or text[0] == "#":
                                continue  # 空行我们留在输入流里，使用 '#' 可以使用注释
                            console.print(
                                f"[blue]（自动执行）[/blue]请输入命令：{text}"
                            )  # 给用户看着玩的，同时显示执行的每行命令
                            parse_command(text)  # 递归解析，可以用来玩花活（自己递归自己导致的后果概不负责！）
                except FileNotFoundError:
                    console.print("[red]这个文件怕是不存在吧！已终止后续的解析！[/]")
                    return
                console.print("[green]所有命令已执行完成！[/]")
            else:
                console.print("[red]命令接受一个参数，不多不少。[/red]")
        elif commands[0][1:] in ["toggle-typewriting", "tt"]:  # 打开 / 关闭 typewriting 功能
            config["typewriting"] = not config["typewriting"]
            console.print(f"[green]Typewriting 状态已经变更为 {config['typewriting']}[/]")
        elif commands[0][1:] in ["toggle-autopause", "ta"]:  # 打开 / 关闭 autopause 功能
            config["autopause"] = not config["autopause"]
            console.print(f"[green]autopause 状态已经变更为 {config['autopause']}[/]")
        else:
            console.print("[red]这个命令怕是不存在吧……[/]")
            console.print("[blue]tips: 如果你想要发消息，请不要用 '/' 开头！[/]")


async def run_input():
    """
    获取用户输入，执行命令
    """
    # pylint: disable=global-statement
    session = PromptSession()
    while True:
        with patch_stdout(raw=True):
            input_data = await session.prompt_async("请输入命令: ")
            parse_command(input_data)


asyncio.get_event_loop().run_until_complete(
    websockets.serve(echo, config["host"], config["port"])
)

console.print(
    f"[green]已经在 {config['host']}:{config['port']} 监听 websocket 请求，等待 echo 客户端接入...[/green]"
)
console.print("[blue]tips: 如果没有看到成功的连接请求，可以尝试刷新一下客户端[/blue]")

asyncio.get_event_loop().create_task(run_input())
console.print("[green]用户输入模块加载成功，您现在可以开始输入命令了，客户端连接后会自动执行！[/green]")

asyncio.get_event_loop().run_forever()
