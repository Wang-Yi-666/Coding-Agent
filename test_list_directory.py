"""
list_directory 工具验收测试

验收标准：
  AC1 - 正确列出工作区内的文件和目录
  AC2 - 能够列出指定子目录的内容
  AC3 - 不存在或无法访问的目录能够被正确处理
  AC4 - 能够执行目录深度与结果数量限制，并在截断时告知模型
  AC5 - 路径穿越以及工作区外部路径会被拒绝
  AC6 - 新工具能够被 Agent 正确调用，返回结果能够继续进入原有 Agent Loop
  AC7 - 原有 MVP 测试（read_file）仍然通过，没有引入明显回归问题
"""

import os
import sys
import tempfile
from pathlib import Path

# Windows 控制台强制 UTF-8 输出
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 保证可以 import 项目代码
sys.path.insert(0, str(Path(__file__).parent))

from tools import list_directory, read_file, execute_tool, TOOLS_SCHEMA

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []


def check(label: str, condition: bool, detail: str = ""):
    icon = PASS if condition else FAIL
    msg = f"{icon}  {label}"
    if detail:
        msg += f"\n       detail: {detail}"
    print(msg)
    results.append((label, condition))
    return condition


# ─────────────────────────────────────────────
# 准备临时工作区
# ─────────────────────────────────────────────
tmp = tempfile.mkdtemp(prefix="ac_test_")
ws = Path(tmp)

# 目录结构
(ws / "src").mkdir()
(ws / "src" / "deep").mkdir()
(ws / "docs").mkdir()
(ws / "main.py").write_text("print('hello')", encoding="utf-8")
(ws / "README.md").write_text("# Test", encoding="utf-8")
(ws / "src" / "utils.py").write_text("def foo(): pass", encoding="utf-8")
(ws / "src" / "deep" / "nested.py").write_text("x = 1", encoding="utf-8")
(ws / "docs" / "guide.md").write_text("# Guide", encoding="utf-8")

print(f"\n临时工作区: {ws}\n")
print("=" * 60)

# ─────────────────────────────────────────────
# AC1 正确列出工作区根目录
# ─────────────────────────────────────────────
print("\n[AC1] 正确列出工作区内的文件和目录")
out = list_directory(".", workspace_dir=str(ws))
print(out)
check("AC1-a: 返回非空字符串", bool(out.strip()))
check("AC1-b: 包含 main.py", "main.py" in out)
check("AC1-c: 包含 src/", "src" in out)
check("AC1-d: 包含 docs/", "docs" in out)
check("AC1-e: 不含 Error 前缀", not out.startswith("Error"))

# ─────────────────────────────────────────────
# AC2 列出指定子目录
# ─────────────────────────────────────────────
print("\n[AC2] 列出指定子目录内容")
out2 = list_directory("src", workspace_dir=str(ws))
print(out2)
check("AC2-a: 包含 utils.py", "utils.py" in out2)
check("AC2-b: 包含 deep/", "deep" in out2)
check("AC2-c: 不含 Error 前缀", not out2.startswith("Error"))

# ─────────────────────────────────────────────
# AC3 不存在目录 / 路径是文件（非目录）
# ─────────────────────────────────────────────
print("\n[AC3] 不存在或无法访问的目录处理")
out3a = list_directory("nonexistent_dir", workspace_dir=str(ws))
print(f"不存在目录: {out3a}")
check("AC3-a: 不存在目录返回 Error", out3a.startswith("Error"))

out3b = list_directory("main.py", workspace_dir=str(ws))   # 文件路径
print(f"文件路径当目录: {out3b}")
check("AC3-b: 文件路径当目录返回 Error", out3b.startswith("Error"))

# ─────────────────────────────────────────────
# AC4 深度与数量限制
# ─────────────────────────────────────────────
print("\n[AC4] 深度限制 & 数量截断")

# 深度=1 时，不应显示 src/deep/nested.py（嵌套两层）
out4_depth = list_directory(".", workspace_dir=str(ws), max_depth=1)
print(f"depth=1:\n{out4_depth}")
check("AC4-a: depth=1 时不出现 nested.py", "nested.py" not in out4_depth)
check("AC4-b: depth=1 时仍出现 src/", "src" in out4_depth)

# 数量限制：max_entries=3 时截断
out4_trunc = list_directory(".", workspace_dir=str(ws), max_entries=3)
print(f"max_entries=3:\n{out4_trunc}")
check("AC4-c: 截断时告知模型", "截断" in out4_trunc or "注意" in out4_trunc)

# ─────────────────────────────────────────────
# AC5 路径穿越 / 工作区外部路径被拒绝
# ─────────────────────────────────────────────
print("\n[AC5] 路径穿越防护")
out5a = list_directory("../../", workspace_dir=str(ws))
print(f"../../: {out5a}")
check("AC5-a: ../ 穿越被拒绝", out5a.startswith("Error"))

out5b = list_directory(str(Path(tmp).parent), workspace_dir=str(ws))  # 绝对路径越界
print(f"绝对路径越界: {out5b}")
check("AC5-b: 绝对路径越界被拒绝", out5b.startswith("Error"))

# ─────────────────────────────────────────────
# AC6 execute_tool 分发 & TOOLS_SCHEMA 注册
# ─────────────────────────────────────────────
print("\n[AC6] execute_tool 分发 & Schema 注册")
tool_names = {t["function"]["name"] for t in TOOLS_SCHEMA}
check("AC6-a: TOOLS_SCHEMA 中包含 list_directory", "list_directory" in tool_names)
check("AC6-b: TOOLS_SCHEMA 中保留 read_file", "read_file" in tool_names)

result_via_dispatch = execute_tool(
    name="list_directory",
    arguments={"dir_path": "src"},
    workspace_dir=str(ws),
)
print(f"execute_tool 结果: {result_via_dispatch}")
check("AC6-c: execute_tool 能调用 list_directory", "utils.py" in result_via_dispatch)
check("AC6-d: execute_tool 返回字符串", isinstance(result_via_dispatch, str))

# 未知工具仍返回明确错误（不崩溃）
unknown = execute_tool("fly_to_moon", {}, workspace_dir=str(ws))
check("AC6-e: 未知工具返回 Error 字符串", unknown.startswith("Error"))

# ─────────────────────────────────────────────
# AC7 回归测试：read_file 功能
# ─────────────────────────────────────────────
print("\n[AC7] 回归测试 (read_file)")
content = read_file("main.py", workspace_dir=str(ws))
check("AC7-a: read_file 正常读取文件", "print" in content)

err_missing = read_file("not_exist.py", workspace_dir=str(ws))
check("AC7-b: read_file 文件不存在返回 Error", err_missing.startswith("Error"))

err_traverse = read_file("../../etc/passwd", workspace_dir=str(ws))
check("AC7-c: read_file 路径穿越被拒绝", err_traverse.startswith("Error"))

dispatch_rf = execute_tool("read_file", {"file_path": "README.md"}, workspace_dir=str(ws))
check("AC7-d: execute_tool 分发 read_file 正常", "Test" in dispatch_rf)

# ─────────────────────────────────────────────
# 汇总
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"结果汇总: {passed}/{total} 通过")
for label, ok in results:
    icon = "✅" if ok else "❌"
    print(f"  {icon} {label}")

if passed < total:
    sys.exit(1)
