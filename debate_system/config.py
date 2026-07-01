"""
Configuration module for the Debate Agent System.
Loads API keys and settings from environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Global configuration."""

    # LLM Configuration
    LLM_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))

    # Debate Configuration
    MAX_OPENING_WORDS: int = 300
    MAX_CROSS_EXAMINATION_ROUNDS: int = 3
    MAX_DISCUSSION_ROUNDS: int = 3
    MAX_CLOSING_WORDS: int = 200

    # ReAct Configuration
    MAX_REACT_STEPS: int = 5

    # Memory Configuration
    DEBATE_STORE_DIR: str = os.getenv("DEBATE_STORE_DIR", "./debate_history")
    VECTOR_DB_DIR: str = os.getenv("VECTOR_DB_DIR", "./debate_vector_db")

    # Tool Configuration
    SEARCH_MAX_RESULTS: int = 5

    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        if not cls.LLM_API_KEY:
            raise ValueError(
                "DEEPSEEK_API_KEY not set. Please set it in .env file "
                "or environment variable."
            )
        return True


config = Config()
