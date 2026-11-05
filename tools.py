import json
from pathlib import Path


def read_file(file_path: str, workspace_dir: str = ".") -> str:
    """读取工作区内的文件内容。
    
    Args:
        file_path: 要读取的文件路径（相对路径或绝对路径）
        workspace_dir: 项目工作区根目录，防止越界访问
        
    Returns:
        文件内容字符串，或明确的错误说明
    """
    try:
        base_path = Path(workspace_dir).resolve()
        target_path = (base_path / file_path).resolve()

        # 安全边界检查：确保目标路径在工作区范围内
        if not target_path.is_relative_to(base_path):
            return f"Error: 访问被拒绝，路径越界: '{file_path}' 超出工作区范围。"

        if not target_path.exists():
            return f"Error: 文件不存在: '{file_path}'"

        if not target_path.is_file():
            return f"Error: 目标路径不是一个普通文件: '{file_path}'"

        # 尝试 UTF-8 读取，兼容异常
        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        return content

    except PermissionError:
        return f"Error: 没有权限读取文件: '{file_path}'"
    except Exception as e:
        return f"Error: 读取文件失败: {str(e)}"


# 符合 OpenAI Function Calling 规范的工具 Schema 列表
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取本地文件内容并返回文本。当需要查看、分析某个文件的具体代码或配置时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要读取的文件相对路径（例如：'main.py' 或 'src/utils.py'）",
                    }
                },
                "required": ["file_path"],
            },
        },
    }
]


def execute_tool(name: str, arguments: dict, workspace_dir: str = ".") -> str:
    """工具调用分发器，校验参数并执行对应工具。
    
    Args:
        name: 工具名称
        arguments: 传入的参数字典
        workspace_dir: 当前工作区根目录
        
    Returns:
        工具真实执行结果字符串
    """
    if name == "read_file":
        file_path = arguments.get("file_path")
        if not file_path:
            return "Error: 缺少必要参数 'file_path'"
        return read_file(file_path, workspace_dir=workspace_dir)
    else:
        return f"Error: 未知工具 '{name}'"
