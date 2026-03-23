from deepagents import create_deep_agent

from langchain_docer_sandbox import DockerSandbox
from example.settings import settings


# Custom Docker sandbox using local Docker container
backend = DockerSandbox(container_name="uv-sandbox", work_dir="/workspace")

agent = create_deep_agent(
    model="deepseek:deepseek-chat",
    backend=backend,
    system_prompt="You are a coding assistant with sandbox access. You can create and run code in the sandbox.",
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Create a hello world Python script and run it",
            }
        ]
    }
)
print(result["messages"][-1].content)
