import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Telegram Bot
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        # PostgreSQL - Admin credentials for migrations and data load
        self.POSTGRES_ADMIN_USER = os.getenv('POSTGRES_ADMIN_USER', 'admin')
        self.POSTGRES_ADMIN_PASSWORD = os.getenv(
            'POSTGRES_ADMIN_PASSWORD', 'admin_password'
        )
        # PostgreSQL - Readonly credentials for bot
        self.POSTGRES_READONLY_USER = os.getenv(
            'POSTGRES_READONLY_USER', 'readonly_user'
        )
        self.POSTGRES_READONLY_PASSWORD = os.getenv(
            'POSTGRES_READONLY_PASSWORD', 'readonly_password'
        )
        # PostgreSQL - Common settings
        self.POSTGRES_DB = os.getenv('POSTGRES_DB', 'video_analytics')
        self.POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
        self.POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
        # Redis
        self.REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
        self.CACHE_TTL = int(os.getenv('CACHE_TTL', '86400'))
        # Ollama
        self.OLLAMA_BASE_URL = os.getenv(
            'OLLAMA_BASE_URL', 'http://ollama.com'
        )
        self.OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3-coder:480b-cloud')
        self.OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY', '')
        self.validate()

    def validate(self):
        """Validate that required settings are present."""
        required_vars = {
            'TELEGRAM_BOT_TOKEN': self.TELEGRAM_BOT_TOKEN,
            'OLLAMA_BASE_URL': self.OLLAMA_BASE_URL,
            'OLLAMA_MODEL': self.OLLAMA_MODEL,
            'OLLAMA_API_KEY': self.OLLAMA_API_KEY,
            'POSTGRES_ADMIN_USER': self.POSTGRES_ADMIN_USER,
            'POSTGRES_ADMIN_PASSWORD': self.POSTGRES_ADMIN_PASSWORD,
            'POSTGRES_READONLY_USER': self.POSTGRES_READONLY_USER,
            'POSTGRES_READONLY_PASSWORD': self.POSTGRES_READONLY_PASSWORD,
            'POSTGRES_DB': self.POSTGRES_DB,
            'POSTGRES_HOST': self.POSTGRES_HOST,
            'POSTGRES_PORT': self.POSTGRES_PORT,
            'REDIS_URL': self.REDIS_URL,
            'CACHE_TTL': self.CACHE_TTL,
        }
        missing = [name for name, value in required_vars.items() if not value]
        if missing:
            raise ValueError(
                f'Missing required environment variables: {", ".join(missing)}'
            )

    @property
    def DATABASE_URL_ADMIN(self) -> str:
        """Database URL with admin credentials for migrations and data load."""
        return (
            f'postgresql+asyncpg://{self.POSTGRES_ADMIN_USER}:'
            f'{self.POSTGRES_ADMIN_PASSWORD}@'
            f'{self.POSTGRES_HOST}:'
            f'{self.POSTGRES_PORT}/'
            f'{self.POSTGRES_DB}'
        )

    @property
    def DATABASE_URL_READONLY(self) -> str:
        """Database URL with readonly credentials for bot queries."""
        return (
            f'postgresql+asyncpg://{self.POSTGRES_READONLY_USER}:'
            f'{self.POSTGRES_READONLY_PASSWORD}@'
            f'{self.POSTGRES_HOST}:'
            f'{self.POSTGRES_PORT}/'
            f'{self.POSTGRES_DB}'
        )


settings = Settings()
