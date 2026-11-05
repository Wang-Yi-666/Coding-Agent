# Coding Agent (v0.1 MVP)

本地运行的最小命令行 Coding Agent，验证核心 Agent Loop 与工具调用闭环。

## 目录结构

```
.
├── main.py          # REPL 交互入口
├── agent.py         # Agent Loop 核心调度与上下文管理
├── tools.py         # read_file 工具实现与参数校验
├── llm_client.py    # DeepSeek / OpenAI 兼容接口封装
├── sample.py        # 供 Agent 测试读取的示例代码
├── requirements.txt # 项目依赖
├── .env.example     # 环境变量示例
└── .gitignore       # Git 忽略规则
```

## 快速上手

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，并填入你的 DeepSeek API Key：

```bash
copy .env.example .env
```

编辑 `.env`：
```ini
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### 3. 运行体验

启动 REPL 交互界面：

```bash
python main.py
```

#### 体验用例 1：测试正常工具调用
```
You > 请读取 sample.py，解释这个文件的主要作用。
```
你会观察到终端输出：
1. `[Step 1] 正在请求模型...`
2. `[Step 1] 🛠️ 调用工具: read_file({'file_path': 'sample.py'})`
3. `[Step 1] 📥 工具执行结果: ...`
4. `[Step 2] 模型已完成思考，给出最终回答。`
5. 输出最终基于文件内容的详细解释。

#### 体验用例 2：测试文件不存在容错
```
You > 请帮我读取不存在的 not_found.py 文件。
```
Agent 会尝试调用工具，工具捕获并返回 `Error: 文件不存在`，Agent 再据此如实告知你文件不存在，不会崩溃。

#### 体验用例 3：普通闲聊（不触发工具）
```
You > 你好，你是谁？
```
模型直接给出回答，不会盲目触发工具。
