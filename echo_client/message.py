"""
解析消息的模块
该模块主要将消息解析为 json 列表的形式
然后可以同时解析成 rich 支持的输出方式预览以及 Echo 程序支持的 json 格式。
"""
import json

from rich.console import Console
from rich.markup import escape

# 消息模式下，命令的前缀
# 用 '/' 是因为中文输入法也可以快速打出这个字符
# 只能有一个字符啊！没见过自己折磨自己的……
# TODO: 添加配置检查
CHAR_PREFIX = "/"

# 对下文造成影响的控制指令（入栈）
# 用类似于字典树（Trie 树）的方式存储
# 方便有共同前缀的多字符命令（比如 ab 和 ac 这种）的快速解析
#   I 立即生效的指令
#   D 对下文造成影响的指令
SYM_I = 1  # 这里值的意义仅仅是区分
SYM_D = 2

# TODO: 这些注释可以删了，废稿但是没完全废
# 这里前置属性/附加属性的区分只是为了方便理解
# 前置属性影响下一个短落
# 附加属性影响上一个段落（同时结束段落）
SYMBOLS = {
    # bold 粗体
    "b": SYM_D,
    # delay 延迟
    "d": SYM_I,
    # reset 重置所有样式（清除样式栈）
    "r": SYM_D,
    # shake / shout 屏幕摇晃动效
    "s": {"h": SYM_I},
    # color 颜色
    # 色值以及其他的最后都可以配置！！现在最好不要用
    "c": {"r": SYM_D, "b": SYM_D},
}
# 这个如果有多字符命令就直接写完整名字就行了
SYM_ARGS = {
    # 这些符号后面可接多个参数（这是为了输入效率而创造的程序，应该不会有这么复杂的命令，但是先准备着）
    # 如果这里没有符号的定义就是不接受参数
    # 数字参数的闭合方法很简单，非数字字符即可
    # 可能会遇到以下问题，如果有一个人叫 11 （纯属虚构），然后 ta 的名字前面需要使用 delay 命令
    # 此时可能需要使用 '/' 手动闭合
    #   这样吗？/d1000/11今天也很想你！
    # 因此，整体的检测逻辑如下：
    #   在检测命令需要参数之后，会一直获取参数直到遇到 '/' 或者不合法字符。
    #   如果遇到 '/' 会从 '/' 后面接着解析（丢弃字符 '/'），如果是不合法字符就留在输入流里面
    # 举例：假设有一个命令 z 需要的参数类型依次是 int, str, int
    # /z123abc/456 就是命令的最简化写法，会被解析为 {'cmd': 'z', 'arg': [123, 'abc', '456']}
    # /z123/123/456 也是合法写法，会被解析为 {'cmd': 'z', 'arg': [123, '123', 123]}
    # 延迟的字符数量
    "d": [
        "int",
    ],
}


def node_exists(pointer: dict, char: str) -> bool:
    """
    输入一个在字典树上的位置和下一个字符，输出这个节点是否存在
    """
    return pointer.get(char, None) is not None


def node_end(pointer: dict, char: str) -> bool:
    """
    输入一个在字典树上的位置和下一个字符，输出这个节点是否存在且是否恰好是指令末尾
    """
    if pointer.get(char, None) is None or isinstance(pointer.get(char), int) is False:
        return False
    return True


def parse_message(msg: str) -> list[dict[str, str | int | dict]]:
    """
    解析文字输入，传出为 json 列表格式
    目前的语法是这样的，示例文本在下一行：
        各位，/d500大家好！/d500几天不见，你想我了吗？/d1000什么，/b没有？？？/r
    解析的原理大概是栈。
    """
    style = {}  # 当前的样式信息
    results = []
    buffer = ""
    index = 0
    while index < len(msg):
        if msg[index] == CHAR_PREFIX:  # 这个是命令
            pointer = SYMBOLS
            command = ""
            index += 1
            while True:
                if node_exists(pointer, msg[index]):
                    command += msg[index]
                    if node_end(pointer, msg[index]):
                        pointer = pointer[msg[index]]
                        index += 1
                        break
                    pointer = pointer[msg[index]]
                    index += 1
                else:
                    break

            if SYM_ARGS.get(command, None) is not None:
                args = SYM_ARGS.get(command, None)
                res = []
                for arg in args:  # 逐个获取
                    if arg == "int":  # 一个数值型变量
                        res_val = 0
                        res_str = ""
                        try:
                            while True:
                                res_val = int(res_str + msg[index])
                                res_str += msg[index]
                                index += 1
                        except ValueError:
                            if msg[index] == "/":
                                index += 1
                        except IndexError:
                            # 到达文本末尾，停止解析
                            pass
                        res.append(res_val)
                    else:
                        # 你放了不该放的参数，应该修改 SYM_ARGS
                        # console.print("[red]这是一个内部错误！[/red]")
                        raise ValueError

            if command == "sh":
                results.append({"text": "", "event": "shout"})

            results.append(
                {
                    "text": buffer,
                    "style": style.copy(),
                }
            )
            buffer = ""

            if command == "r":
                style = {}
            elif command == "d":
                results.append({"text": "", "pause": res[0]})
            elif command == "cr":
                style["color"] = "#ff0000"
            elif command == "cb":
                style["color"] = "#66ccff"  # 塞点私货，天依什么的最可爱了ww
            elif command == "b":
                style = {"bold": True}

        else:
            buffer += msg[index]
            index += 1

    results.append(
        {
            "text": buffer,
            "style": style.copy(),
        }
    )
    return results


def preview(console: Console, messages: list[dict[str, str | int | dict]]) -> None:
    """
    使用控制台预览效果
    别指望我做个QQ的窗口抖动效果出来哈
    没想好窗口抖动和延迟怎么预览，就先不预览了
    反正看效果你还是得OBS
    """
    for message in messages:
        res_str = escape(message["text"])
        if message.get("style", None) is not None:
            if message["style"].get("bold", False):
                res_str = f"[bold]{res_str}[/bold]"
            if message["style"].get("color", False):
                color = message["style"].get("color", False)
                res_str = f"[{color}]{res_str}[/{color}]"

        console.print(res_str, end="")


def render(config, messages: list[dict[str, str | int | dict]]) -> str:
    """
    渲染为 Echo 程序可以理解的格式
    """
    # TODO: 简化发送向 Echo 客户端的内容，减轻客户端压力（如不发空 style）
    res_list = []
    for message in messages:
        res_list.append(message)

    return json.dumps(
        {
            "action": "message_data",
            "data": {
                "username": config["username"],
                "messages": [
                    {"message": res_list},
                ],
            },
        }
    )


if __name__ == "__main__":
    console = Console()
    console.print("[yellow]调试模式 & 示例查看[/yellow]")
    console.print("[yellow]若您不想更改此程序，请不要手动运行这个文件！[/yellow]")

    sample_text = [
        "这句话用来测试异常处理（delay在末尾的情况）/d100",
        "这句话用来测试屏幕振动动效/sh",
        "这句话的文本有/cr颜/cb色！！/r",
        "各位，/d50大家好！/d50几天不见，你想我了吗？/d100什么，/sh/b没有？？？/r",
    ]

    for tindex, sample in enumerate(sample_text):
        console.print(f"[blue]示例文本 {tindex+1}/{len(sample_text)}: {sample}[/blue]")
        console.print("[blue]语法解析[/]：")

        res_messages = parse_message(sample)
        console.print(res_messages)

        console.print("[blue]语句预览：[/]")
        preview(console, res_messages)
        console.print()

        console.print("发送给 Echo 程序的消息：")
        console.print(render({"username": "用户名"}, res_messages))

        console.print()