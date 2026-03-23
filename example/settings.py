from dotenv import load_dotenv
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):

    # deepseek API
    DEEPSEEK_API_KEY: SecretStr
    DEEPSEEK_BASE_URL: SecretStr


    TAVILY_API_KEY:SecretStr
    DAYTONA_API_KEY:SecretStr

settings = Settings() # type: ignore

# 加载环境变量
# print(settings)
