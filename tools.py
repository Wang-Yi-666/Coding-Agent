import json
from pathlib import Path


def list_directory(
    dir_path: str = ".",
    workspace_dir: str = ".",
    max_depth: int = 2,
    max_entries: int = 100,
) -> str:
    """列出工作区内某个目录的文件与子目录结构。

    Args:
        dir_path: 要列出的目录路径（相对路径或 "." 表示工作区根目录）
        workspace_dir: 项目工作区根目录，防止越界访问
        max_depth: 最大递归深度（默认 2）
        max_entries: 最多返回的条目数（默认 100），超出时截断并告知

    Returns:
        格式化的目录树字符串，或明确的错误说明
    """
    try:
        base_path = Path(workspace_dir).resolve()
        target_path = (base_path / dir_path).resolve()

        # 安全边界检查：确保目标路径在工作区范围内
        if not target_path.is_relative_to(base_path):
            return f"Error: 访问被拒绝，路径越界: '{dir_path}' 超出工作区范围。"

        if not target_path.exists():
            return f"Error: 目录不存在: '{dir_path}'"

        if not target_path.is_dir():
            return f"Error: 目标路径不是目录: '{dir_path}'"

        lines = []
        truncated = False
        entry_count = 0

        def _walk(path: Path, depth: int, prefix: str):
            nonlocal entry_count, truncated
            if depth > max_depth:
                return
            try:
                entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
            except PermissionError:
                lines.append(f"{prefix}[权限不足，无法读取]")
                return

            for i, entry in enumerate(entries):
                if entry_count >= max_entries:
                    truncated = True
                    return
                is_last = (i == len(entries) - 1)
                connector = "└── " if is_last else "├── "
                suffix = "/" if entry.is_dir() else ""
                lines.append(f"{prefix}{connector}{entry.name}{suffix}")
                entry_count += 1

                if entry.is_dir() and depth < max_depth:
                    extension = "    " if is_last else "│   "
                    _walk(entry, depth + 1, prefix + extension)

        rel = target_path.relative_to(base_path)
        root_label = str(rel) if str(rel) != "." else "."
        lines.append(f"{root_label}/")
        _walk(target_path, depth=1, prefix="")

        result = "\n".join(lines)
        if truncated:
            result += f"\n\n[注意：结果已截断，仅显示前 {max_entries} 个条目，实际条目更多。]"
        return result

    except PermissionError:
        return f"Error: 没有权限访问目录: '{dir_path}'"
    except Exception as e:
        return f"Error: 列出目录失败: {str(e)}"


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
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": (
                "列出工作区内某个目录的文件与子目录结构（树形格式）。"
                "当用户需要了解项目结构、查找文件位置时使用。"
                "默认列出工作区根目录，也可指定子目录路径。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": (
                            "要列出的目录相对路径（例如：'.' 表示根目录，'src' 表示 src 子目录）"
                        ),
                        "default": ".",
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "目录树的最大递归深度，默认为 2",
                        "default": 2,
                    },
                },
                "required": [],
            },
        },
    },
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
    elif name == "list_directory":
        dir_path = arguments.get("dir_path", ".")
        max_depth = arguments.get("max_depth", 2)
        return list_directory(
            dir_path=dir_path,
            workspace_dir=workspace_dir,
            max_depth=max_depth,
        )
    else:
        return f"Error: 未知工具 '{name}'"
