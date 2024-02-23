"""
这个文件用于处理配置
"""
import os
import pathlib

import yaml
from rich.console import Console


# TODO: add config check
def load_config(console: Console) -> dict:
    """
    加载配置
    """
    config = {}
    config_path = (
        pathlib.Path(os.path.expanduser("~"))
        / ".config"
        / "echo-client"
        / "config.yaml"
    )
    if config_path.exists():
        config = yaml.safe_load(open(config_path, "r", encoding="utf-8"))
        console.log(f"[green]从 {config_path} 加载了配置[/]")
    else:
        default_config = {
            "command_prefix": "/",
            "username": "/",
            "host": "127.0.0.1",
            "port": 3000,
            "typewriting": False,
            # 自动在某些字符后面等待，自动在行末等待
            # 本质是文本替换，不知道有没有问题
            "autopause": False,
            # 在哪些字符后面等待呢？
            "autopausestr": ",，.。;；:：!！",
            # 等待多久呢？
            "autopausetime": 20,
        }
        try:
            os.mkdir(config_path.parent)
        except FileExistsError:
            pass
        with open(config_path, "w", encoding="utf-8") as write_stream:
            write_stream.write(yaml.safe_dump(default_config))
        console.log("[yellow]您没有配置文件，已经创建了一个默认的[/]")
        load_config(console)
    return config


if __name__ == "__main__":
    print(load_config(Console()))
