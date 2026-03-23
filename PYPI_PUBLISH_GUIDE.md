# PyPI 发布指南

本文档介绍如何将 `langchain-docker-sandbox` 发布到 PyPI。

## 前置准备

### 1. 更新配置信息

在发布前，请在 `pyproject.toml` 中更新以下信息：

```toml
[project]
name = "langchain-docker-sandbox"
version = "0.1.0"  # 每次发布需要增加版本号
description = "Custom Docker sandbox backend for Deep Agents framework, providing isolated code execution environments"
authors = [
    { name = "你的名字", email = "your.email@example.com" }
]

[project.urls]
Homepage = "https://github.com/yourusername/langchain-docker-sandbox"
Documentation = "https://github.com/yourusername/langchain-docker-sandbox#readme"
Repository = "https://github.com/yourusername/langchain-docker-sandbox"
Issues = "https://github.com/yourusername/langchain-docker-sandbox/issues"
```

### 2. 注册 PyPI 账户

如果还没有 PyPI 账户，请访问 https://pypi.org/account/register/ 注册。

### 3. 配置发布工具

安装发布所需的工具：

```bash
uv pip install build twine
```

或使用 pip：

```bash
pip install build twine
```

### 4. 创建 API Token

1. 登录 PyPI：https://pypi.org/account/
2. 进入 "Account settings" → "API tokens"
3. 点击 "Add API token"
4. 选择 "Scope: Entire account"（如果这是你的第一个包）
5. 给 Token 起个名字，如 "langchain-docker-sandbox"
6. 复制生成的 Token（**只显示一次，请妥善保存**）

## 构建和发布流程

### 第一步：清理旧的构建产物

```bash
rm -rf dist/ build/ src/*.egg-info
```

### 第二步：构建包

```bash
uv run build
```

或使用 Python：

```bash
python -m build
```

这会在 `dist/` 目录下生成两个文件：
- `langchain_docker_sandbox-0.1.0-py3-none-any.whl`（wheel 包）
- `langchain_docker_sandbox-0.1.0.tar.gz`（源码包）

### 第三步：检查包

使用 Twine 检查包的元数据：

```bash
uv run twine check dist/*
```

如果没有错误，可以继续发布。

### 第四步：测试发布到 TestPyPI（推荐）

在发布到正式 PyPI 前，建议先发布到 TestPyPI 进行测试：

```bash
uv run twine upload --repository testpypi dist/*
```

发布成功后，可以在 TestPyPI 查看你的包：
https://test.pypi.org/project/langchain-docker-sandbox/

### 第五步：测试安装 TestPyPI 包

```bash
uv pip install --index-url https://test.pypi.org/simple/ langchain-docker-sandbox
```

### 第六步：发布到正式 PyPI

确认测试通过后，发布到正式 PyPI：

```bash
uv run twine upload dist/*
```

第一次上传时，Twine 会提示输入：
- **Username**: `__token__`（注意是两个下划线）
- **Password**: 你刚才创建的 API Token

## 验证发布

发布成功后，可以：

1. 在 PyPI 访问你的包：https://pypi.org/project/langchain-docker-sandbox/
2. 测试安装：

```bash
pip install langchain-docker-sandbox
```

3. 测试使用：

```python
from langchain_docker_sandbox import DockerSandbox

backend = DockerSandbox(container_name="uv-sandbox", work_dir="/workspace")
print(backend.id)
```

## 版本管理

每次发布新版本时：

1. 在 `pyproject.toml` 中增加版本号（遵循语义化版本规范）
2. 可选：在项目根目录创建 `CHANGELOG.md` 记录变更
3. 重复上述构建和发布流程

## 常见问题

### 包名已被占用

如果出现 "Project already exists" 错误，说明包名已被使用。你需要：

1. 更改 `pyproject.toml` 中的包名
2. 或者联系原包的所有者

### 上传失败

如果上传失败：

1. 检查网络连接
2. 确认 API Token 正确
3. 查看错误信息，根据提示修复

### 构建错误

如果构建出现错误：

1. 确保 `pyproject.toml` 格式正确
2. 检查 `src/` 目录结构是否正确
3. 确认所有依赖都已安装

## 发布清单

发布前请确认：

- [ ] 已更新版本号
- [ ] `pyproject.toml` 信息完整且正确
- [ ] README.md 已更新
- [ ] LICENSE 文件存在
- [ ] 所有代码已提交到 Git
- [ ] 已创建 Git tag（可选）
- [ ] 已在 TestPyPI 测试通过
- [ ] 已备份重要数据

## 自动化发布（可选）

为了简化发布流程，可以配置 GitHub Actions 自动发布：

创建 `.github/workflows/publish.yml`：

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - run: pip install build
      - run: python -m build
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

然后在 GitHub Settings 中添加 `PYPI_API_TOKEN` secret。

## 参考资料

- [PyPI 官方文档](https://packaging.python.org/tutorials/packaging-projects/)
- [Twine 文档](https://twine.readthedocs.io/)
- [Hatchling 文档](https://hatch.pypa.io/latest/build/)
