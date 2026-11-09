import sys

from dotenv import load_dotenv

from agent import CodingAgent
from llm_client import LLMClient


def main():
    # 确保 Windows 控制台下中文输入输出正常编码
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    # 自动加载当前目录下的 .env 配置文件
    load_dotenv()

    print("=" * 60)
    print("  欢迎使用 Coding Agent (v0.1 MVP - REPL 交互模式)")
    print("  当前支持工具: read_file, list_directory")
    print("  输入 'exit'、'quit' 或按 Ctrl+C 可退出程序")
    print("=" * 60)

    try:
        llm_client = LLMClient()
    except ValueError as e:
        print(f"\n[启动失败] {e}")
        print("请先复制 .env.example 为 .env，并填入您的 DEEPSEEK_API_KEY：")
        print("   copy .env.example .env\n")
        sys.exit(1)

    agent = CodingAgent(llm_client=llm_client, workspace_dir=".")

    while True:
        try:
            user_input = input("\nYou : ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("再见！")
                break

            response = agent.run(user_input)
            print(f"\nAgent :\n{response}\n")

        except (KeyboardInterrupt, EOFError):
            print("\n程序已退出。")
            break


if __name__ == "__main__":
    main()
