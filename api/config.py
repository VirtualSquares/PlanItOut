"""AI Agent Configuration"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API Configuration
OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')

# Gemini API Configuration - Using Google's Generative AI API (optional fallback)
GEMINI_API_KEY: Optional[str] = os.getenv('GEMINI_API_KEY')

# Sentiment Analysis API Configuration
SENTIMENT_API_ENDPOINT: str = os.getenv(
	'SENTIMENT_API_ENDPOINT',
	'https://api.sentiment.example/v1/analyze'
)
SENTIMENT_API_KEY: Optional[str] = os.getenv('SENTIMENT_API_KEY')

# Default Timezone
DEFAULT_TIMEZONE: str = os.getenv('TIMEZONE', 'America/Los_Angeles')

# Agent Behavior Settings
MAX_ACTIVE_HABITS: int = 3
BREAK_AFTER_90_MIN: int = 15  # minutes
BREAK_AFTER_50_MIN: int = 5  # minutes
MEETING_BUFFER_MINUTES: int = 30
DEFAULT_HABIT_NOTIFICATION_HOUR: int = 8

