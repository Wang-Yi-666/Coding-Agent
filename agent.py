import json
from pathlib import Path

from llm_client import LLMClient
from tools import TOOLS_SCHEMA, execute_tool

SYSTEM_PROMPT = """你是一个本地运行的 Coding Agent 编程助手。
你的目标是帮助用户理解代码仓库、分析代码逻辑并回答开发相关的问题。

原则与能力：
1. 你可以使用提供的工具（如 list_directory 查看目录结构、read_file 查看文件内容）探索与理解实际项目。
2. 当用户询问项目结构或查找文件位置时，优先调用 list_directory；当询问某个具体文件、配置或函数实现时，必须先调用 read_file 查看真实内容，严禁凭空臆造。
3. 得到工具返回的真实结果后，仔细分析，并在获得足够信息后直接给出最终回答，不要多余调用工具。
4. 语言风格清晰、专业、直奔主题。
"""


class CodingAgent:
    """Coding Agent 核心控制器，负责维护对话上下文与驱动 Agent Loop。"""

    def __init__(
        self,
        llm_client: LLMClient,
        workspace_dir: str = ".",
        max_steps: int = 5,
    ):
        self.llm_client = llm_client
        self.workspace_dir = str(Path(workspace_dir).resolve())
        self.max_steps = max_steps
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def run(self, user_prompt: str) -> str:
        """执行单轮任务的 Agent Loop。

        Args:
            user_prompt: 用户的输入任务

        Returns:
            模型最终生成的回答或终止提示
        """
        self.messages.append({"role": "user", "content": user_prompt})
        step = 0

        while step < self.max_steps:
            step += 1
            print(f"\n[Step {step}] 正在请求模型...")

            try:
                message = self.llm_client.chat(
                    messages=self.messages,
                    tools=TOOLS_SCHEMA,
                )
            except Exception as e:
                error_msg = f"调用 LLM 失败: {str(e)}"
                print(f"[Error] {error_msg}")
                return error_msg

            # 判断是否有工具调用
            tool_calls = getattr(message, "tool_calls", None)

            if not tool_calls:
                # 模型直接返回了最终答案，正常结束循环
                final_answer = message.content or ""
                self.messages.append({"role": "assistant", "content": final_answer})
                print(f"[Step {step}] 模型已完成思考，给出最终回答。")
                return final_answer

            # 模型请求调用工具：先将 assistant 的工具调用消息写入历史
            self.messages.append(message.model_dump(exclude_unset=True))

            for tool_call in tool_calls:
                func_name = tool_call.function.name
                call_id = tool_call.id
                raw_args = tool_call.function.arguments

                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    args = {}
                    print(f"[Warning] 工具参数 JSON 解析失败: {raw_args}")

                print(f"[Step {step}] [调用工具] {func_name}({args})")

                # 执行真实工具操作
                result = execute_tool(
                    name=func_name,
                    arguments=args,
                    workspace_dir=self.workspace_dir,
                )

                # 打印适量概要日志
                preview = result[:120] + "..." if len(result) > 120 else result
                print(f"[Step {step}] [工具返回] {preview}")

                # 将工具执行结果作为 tool 角色消息追加进上下文
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": func_name,
                        "content": str(result),
                    }
                )

        # 超过最大限制步数强制终止
        stop_msg = (
            f"已达到最大执行步数限制 ({self.max_steps} 步)，为防止死循环已安全中止。"
        )
        print(f"\n[Terminated] {stop_msg}")
        return stop_msg
