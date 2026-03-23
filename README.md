# Deep Agents Docker Sandbox

一个为 Deep Agents 框架提供自定义 Docker 沙盒后端的项目，让 AI Agent 可以在隔离的 Docker 容器中安全地执行代码和操作文件。

## 功能特性

- **隔离执行环境**：使用 Docker 容器提供安全的代码执行环境
- **完整的文件操作**：支持读取、写入、编辑、上传、下载文件
- **命令执行**：在沙盒中执行 shell 命令
- **批量文件传输**：支持批量上传和下载文件
- **文件搜索**：提供目录列表、模式匹配和文本搜索功能
- **易于集成**：无缝集成到 Deep Agents 框架

## 系统要求

- Python 3.13+
- Docker 和 Docker Compose
- DeepSeek API 密钥

## 安装

1. 克隆仓库：
```bash
git clone <repository-url>
cd langchain_docker_sandbox
```

2. 安装依赖：
```bash
uv sync
```

3. 配置环境变量：
```bash
cp example/.env.example example/.env
# 编辑 example/.env，填入你的 API 密钥
```

## 快速开始

### 1. 启动 Docker 沙盒容器

```bash
docker compose up -d
```

这会启动一个名为 `uv-sandbox` 的 Docker 容器，使用 `astral/uv:python3.13-bookworm-slim` 镜像，并将本地的 `filesystem/` 目录挂载到容器的 `/workspace`。

### 2. 运行示例

```bash
cd example
python main.py
```

示例代码会创建一个 Deep Agent，让它在沙盒中创建并运行一个 "Hello World" Python 脚本。

## 使用方法

### 基本 Agent 创建

```python
from deepagents import create_deep_agent
from langchain_docer_sandbox import DockerSandbox

# 创建 Docker 沙盒后端
backend = DockerSandbox(
    container_name="uv-sandbox",
    work_dir="/workspace"
)

# 创建 Deep Agent
agent = create_deep_agent(
    model="deepseek:deepseek-chat",
    backend=backend,
    system_prompt="你是一个拥有沙盒访问权限的编程助手。你可以在沙盒中创建和运行代码。",
)

# 与 Agent 交互
result = agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": "创建一个计算斐波那契数列的 Python 脚本并运行它"
        }
    ]
})

print(result["messages"][-1].content)
```

### DockerSandbox API

#### 执行命令

```python
backend = DockerSandbox(container_name="uv-sandbox", work_dir="/workspace")

# 执行简单命令
result = backend.execute("echo 'Hello from Docker!'")
print(result.output)  # 输出命令结果
print(result.exit_code)  # 退出码
```

#### 文件操作

```python
# 写入文件
backend.write("hello.py", "print('Hello World!')")

# 读取文件（带行号）
content = backend.read("hello.py")

# 编辑文件
backend.edit("hello.py", "Hello", "你好", replace_all=False)

# 批量上传
backend.upload_files([
    ("script1.py", b"print('script1')"),
    ("script2.py", b"print('script2')"),
])

# 批量下载
files = backend.download_files(["script1.py", "script2.py"])
```

#### 文件搜索

```python
# 列出目录
files = backend.ls_info("/workspace")

# 模式匹配搜索
py_files = backend.glob_info("*.py", path="/workspace")

# 文本搜索
matches = backend.grep_raw("hello", path="/workspace", glob="*.py")
```

## 测试

运行测试套件需要先启动 Docker 沙盒容器：

```bash
# 启动容器
docker compose up -d

# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest test/test_docker_sandbox.py::TestDockerSandboxExecute::test_execute_simple_command

# 查看测试覆盖率
uv run pytest --cov=langchain_docer_sandbox
```

## 项目结构

```
langchain_docker_sandbox/
├── langchain_docer_sandbox.py   # DockerSandbox 后端实现
├── docker-compose.yml            # Docker Compose 配置
├── filesystem/                   # 挂载到沙盒的目录
├── example/                      # 示例代码
│   ├── main.py                   # 示例入口
│   ├── settings.py               # 配置管理
│   └── .env                      # 环境变量
├── test/                        # 测试代码
│   └── test_docker_sandbox.py    # DockerSandbox 测试
├── pyproject.toml                # 项目配置
└── README.md                     # 本文件
```

## 配置说明

### 环境变量

在 `example/.env` 中配置以下变量：

```env
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
TAVILY_API_KEY=your-tavily-api-key    # 可选，用于搜索功能
DAYTONA_API_KEY=your-daytona-api-key   # 可选
```

### Docker Compose 配置

`docker-compose.yml` 配置说明：

```yaml
services:
  uv-sandbox:
    image: astral/uv:python3.13-bookworm-slim  # 基础镜像
    container_name: uv-sandbox                   # 容器名称
    working_dir: /workspace                     # 工作目录
    volumes:
      - ./filesystem:/workspace                 # 挂载本地目录
```

你可以根据需要修改镜像、工作目录或挂载点。

## 依赖项

**核心依赖：**
- `deepagents>=0.4.11` - Deep Agents 框架
- `docker>=7.1.0` - Docker SDK for Python

**开发依赖：**
- `pytest>=9.0.2` - 测试框架
- `dotenv>=0.9.9` - 环境变量加载
- `pydantic>=2.12.5`, `pydantic-settings>=2.13.1` - 配置管理
- `ruff>=0.15.6` - 代码格式化和检查

## 代码风格

项目使用 Ruff 进行代码格式化和检查：

```bash
# 检查代码
ruff check .

# 自动修复问题
ruff check --fix .

# 格式化代码
ruff format .
```

**代码规范：**
- 行长度：150 字符
- 字符串：双引号
- 导入顺序：标准库 → 第三方 → 第一方 → 本地
- 文档字符串：Google 风格

## 故障排除

### 容器无法启动

```bash
# 检查 Docker 是否运行
docker ps

# 查看容器日志
docker compose logs uv-sandbox

# 重启容器
docker compose restart
```

### 找不到容器错误

确保 Docker 容器名称 `uv-sandbox` 正确，并且容器正在运行：

```bash
docker ps | grep uv-sandbox
```

### 测试失败

确保在运行测试前先启动沙盒容器：

```bash
docker compose up -d
uv run pytest
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 参考资料

- [Deep Agents 文档](https://reference.langchain.com/python/deepagents)
- [LangChain 文档](https://reference.langchain.com/python/langchain)
- [Docker SDK for Python](https://docker-py.readthedocs.io/)
