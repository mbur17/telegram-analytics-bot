import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    # Database
    DATABASE_URL: str = os.getenv(
        'DATABASE_URL',
        'postgresql+asyncpg://user:password@localhost:5432/video_analytics'
    )
    # Ollama settings
    OLLAMA_BASE_URL: str = os.getenv(
        'OLLAMA_BASE_URL', 'http://localhost:11434'
    )
    OLLAMA_MODEL: str = os.getenv('OLLAMA_MODEL', 'sqlcoder:7b')

    def validate(self):
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError('TELEGRAM_BOT_TOKEN is required')
        if not self.OLLAMA_BASE_URL:
            raise ValueError('OLLAMA_BASE_URL is required')
        if not self.OLLAMA_MODEL:
            raise ValueError('OLLAMA_MODEL is required')


settings = Settings()
