"""AI Sentiment Analysis Agent"""
from typing import Dict, Optional
import requests
from src.config import SENTIMENT_API_ENDPOINT, SENTIMENT_API_KEY


def analyze_sentiment(importance_statement: str) -> Dict[str, any]:
	"""
	AI Agent Understanding: Analyze sentiment and importance from statement
	Uses external API for emotional intelligence and importance assessment
	"""
	try:
		headers = {}
		if SENTIMENT_API_KEY:
			headers['Authorization'] = f'Bearer {SENTIMENT_API_KEY}'

		payload = {
			'text': importance_statement,
			'analyze_importance': True
		}

		response = requests.post(
			SENTIMENT_API_ENDPOINT,
			json=payload,
			headers=headers,
			timeout=10
		)

		if response.status_code == 200:
			data = response.json()
			return {
				'sentiment': data.get('sentiment', 'neutral'),
				'importance': data.get('importance_score', 50),
				'confidence': data.get('confidence', 0.5)
			}
		else:
			# Fallback on API error
			return _fallback_sentiment_analysis(importance_statement)

	except (requests.RequestException, ValueError, KeyError) as e:
		# AI Agent Resilience: Fallback to local analysis
		return _fallback_sentiment_analysis(importance_statement)


def _fallback_sentiment_analysis(importance_statement: str) -> Dict[str, any]:
	"""
	AI Agent Fallback: Local heuristic sentiment analysis
	Maintains agent functionality when external API is unavailable
	"""
	statement_lower = importance_statement.lower()

	# Simple sentiment detection
	positive_words = [
		'important', 'crucial', 'essential', 'vital', 'help', 'improve',
		'benefit', 'achieve', 'goal', 'success', 'progress', 'growth'
	]
	negative_words = [
		'stress', 'worry', 'anxiety', 'difficult', 'hard', 'struggle',
		'problem', 'issue', 'concern', 'fear'
	]

	positive_count = sum(1 for word in positive_words if word in statement_lower)
	negative_count = sum(1 for word in negative_words if word in statement_lower)

	if positive_count > negative_count:
		sentiment = 'positive'
	elif negative_count > positive_count:
		sentiment = 'negative'
	else:
		sentiment = 'neutral'

	# Estimate importance based on statement length and keywords
	importance_keywords = [
		'important', 'crucial', 'essential', 'vital', 'critical', 'priority'
	]
	has_importance_keywords = any(
		keyword in statement_lower for keyword in importance_keywords
	)

	# Base importance score
	if has_importance_keywords:
		importance = 75
	elif sentiment == 'positive':
		importance = 60
	elif sentiment == 'negative':
		importance = 70  # Negative might indicate urgency
	else:
		importance = 50

	return {
		'sentiment': sentiment,
		'importance': importance,
		'confidence': 0.5,
		'fallback': True
	}

