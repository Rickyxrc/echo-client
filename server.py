"""
websocket 服务器模块
"""
import asyncio
import json

import websockets
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from rich.console import Console


def parse_message(msg: str) -> str:
    """
    解析文字输入，传出为 echo 程序可以理解的文本
    """
    # 目前先返回单句话，这个逻辑待定
    return json.dumps(
        {
            "action": "message_data",
            "data": {
                "username": "还在开发急什么",
                "messages": [
                    {"message": msg},
                ],
            },
        }
    )


COMMAND_PREFIX = "/"

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
                                {"message": "websocket服务器连接成功！"},
                            ],
                        },
                    }
                )
            )
            # await websocket.send(json.dumps({
            # "action": "echo_next",
            # }))
        elif data["action"] == "close":
            response += "发出下线请求"
        elif data["action"] == "page_hidden":
            response += "页面被隐藏"
        elif data["action"] == "page_visible":
            response += "页面恢复显示"
        else:
            response += f"发送了未知事件，事件原文: {data}"
        console.log(response)


async def listen_queue(websocket, _cid):
    """
    监听事件队列，如果有啥事情就执行
    """
    proceed = 0
    while True:
        await asyncio.sleep(1)
        if proceed < len(events):
            for event in events[proceed:]:
                # print(event)
                console.log(f"客户端{client_id}: 执行 {event}")
                if event["action"] == "message_data":
                    console.log(f"客户端{client_id}: 发送文字信息")
                    await websocket.send(event["data"])
                else:
                    console.log(f"[red]客户端{client_id}: 上面那个事件的实现程序还没写呢！执行不了！[/red]")
            proceed = len(events)


async def echo(websocket, _path):
    """
    websocket 连接上就执行这个
    """
    # pylint: disable=global-statement
    global client_id
    client_id += 1
    cid = client_id
    console.log(f"客户端{client_id}: 调用了一个echo函数")
    await asyncio.create_task(listen_queue(websocket, cid))
    await asyncio.create_task(get_message(websocket, cid))


async def run_input():
    """
    获取用户输入，执行命令
    """
    session = PromptSession()
    while True:
        with patch_stdout(raw=True):
            input_data = await session.prompt_async("请输入命令: ")
        if input_data[0] != COMMAND_PREFIX:
            console.log(f"发送文字消息: {input_data}")
            events.append({"action": "message_data", "data": parse_message(input_data)})
        else:
            console.log(f"执行命令：{input_data}")
            console.log("[red]这个功能还没做好，不急！！！！[/red]")


host = "127.0.0.1"
port = 3000

asyncio.get_event_loop().run_until_complete(websockets.serve(echo, host, port))

console.log(f"[green]已经在 {host}:{port} 监听 websocket 请求，等待 echo 客户端接入...[/green]")
console.log("[blue]tips: 如果没有看到成功的连接请求，可以尝试刷新一下客户端[/blue]")

asyncio.get_event_loop().create_task(run_input())
console.log("[green]用户输入模块加载成功，您现在可以开始输入命令了，客户端连接后会自动执行！[/green]")

asyncio.get_event_loop().run_forever()
