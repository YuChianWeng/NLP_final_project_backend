import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./movie_insight.db")

    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")

    # Azure Language
    AZURE_LANGUAGE_API_KEY: str = os.getenv("AZURE_LANGUAGE_API_KEY", "")
    AZURE_LANGUAGE_ENDPOINT: str = os.getenv("AZURE_LANGUAGE_ENDPOINT", "")

    # Azure Speech
    AZURE_SPEECH_API_KEY: str = os.getenv("AZURE_SPEECH_API_KEY", "")
    AZURE_SPEECH_REGION: str = os.getenv("AZURE_SPEECH_REGION", "eastus")
    AZURE_SPEECH_VOICE_NAME: str = os.getenv("AZURE_SPEECH_VOICE_NAME", "zh-TW-HsiaoChenNeural")

settings = Settings()