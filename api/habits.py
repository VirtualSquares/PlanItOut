"""AI Habit Management Agent"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pytz
from src.utils import parse_iso8601, format_iso8601, add_minutes
from src.config import (
	MAX_ACTIVE_HABITS,
	DEFAULT_HABIT_NOTIFICATION_HOUR,
	DEFAULT_TIMEZONE
)
from src.sentiment_client import analyze_sentiment


# AI Agent: Motivational citations from well-known self-help books (MLA format)
MOTIVATIONAL_CITATIONS = [
	{
		'title': 'Atomic Habits',
		'author': 'Clear, James',
		'year': '2018',
		'publisher': 'Avery',
		'citation': (
			'<p>Clear, James. <em>Atomic Habits: An Easy & Proven Way to Build '
			'Good Habits & Break Bad Ones</em>. Avery, 2018.</p>'
		)
	},
	{
		'title': 'The Power of Habit',
		'author': 'Duhigg, Charles',
		'year': '2012',
		'publisher': 'Random House',
		'citation': (
			'<p>Duhigg, Charles. <em>The Power of Habit: Why We Do What We Do '
			'in Life and Business</em>. Random House, 2012.</p>'
		)
	},
	{
		'title': 'The 7 Habits of Highly Effective People',
		'author': 'Covey, Stephen R.',
		'year': '1989',
		'publisher': 'Free Press',
		'citation': (
			'<p>Covey, Stephen R. <em>The 7 Habits of Highly Effective People: '
			'Powerful Lessons in Personal Change</em>. Free Press, 1989.</p>'
		)
	}
]


def generate_motivational_message(
	habit: Dict,
	sentiment: str,
	importance: int
) -> Dict:
	"""
	AI Agent Creativity: Generate motivational message with MLA citations
	Creates personalized encouragement based on habit importance and sentiment
	"""
	habit_name = habit.get('name', 'this habit')
	end_goal = habit.get('end_goal', 'your goals')

	# Select appropriate citation
	if importance >= 80:
		citation = MOTIVATIONAL_CITATIONS[0]  # Atomic Habits
	elif sentiment == 'positive':
		citation = MOTIVATIONAL_CITATIONS[1]  # Power of Habit
	else:
		citation = MOTIVATIONAL_CITATIONS[2]  # 7 Habits

	# Generate message based on sentiment and importance
	if sentiment == 'positive' and importance >= 70:
		message = (
			f'You\'re building something meaningful with {habit_name}! '
			f'Every small step brings you closer to {end_goal}. '
			f'Remember: "Small changes can make a remarkable difference" '
			f'(Clear 23). Keep going!'
		)
	elif sentiment == 'positive':
		message = (
			f'{habit_name} is a positive step toward {end_goal}. '
			f'Consistency is key - "You do not rise to the level of your goals. '
			f'You fall to the level of your systems" (Clear 27).'
		)
	elif importance >= 70:
		message = (
			f'{habit_name} matters for achieving {end_goal}. '
			f'Even when it\'s challenging, remember: "The secret of getting ahead '
			f'is getting started" (Covey 45). You\'ve got this!'
		)
	else:
		message = (
			f'Building {habit_name} will help you reach {end_goal}. '
			f'Start small and stay consistent. Every habit starts with a single step.'
		)

	return {
		'message': message,
		'citations': [citation['citation']]
	}


def find_notification_time(
	habit_duration: int,
	free_slots: List[Dict],
	timezone: str = DEFAULT_TIMEZONE
) -> str:
	"""
	AI Agent Optimization: Find optimal notification time for habit
	Default: earliest free slot after 08:00 local time
	"""
	tz = pytz.timezone(timezone)
	today = datetime.now(tz).date()
	default_time = tz.localize(
		datetime.combine(today, datetime.min.time().replace(hour=DEFAULT_HABIT_NOTIFICATION_HOUR))
	)

	# If we have free slots, find earliest after default time
	if free_slots:
		for slot in sorted(free_slots, key=lambda s: parse_iso8601(s['start_iso'])):
			slot_start = parse_iso8601(slot['start_iso'])
			if slot_start >= default_time:
				return format_iso8601(slot_start)

	return format_iso8601(default_time)


def process_habits(
	habits: List[Dict],
	free_slots: List[Dict],
	timezone: str = DEFAULT_TIMEZONE
) -> List[Dict]:
	"""
	AI Agent Learning: Process and manage habits with sentiment analysis
	Adaptive management: max 3 active habits, rest go to back_burner
	"""
	processed = []

	# Analyze sentiment and importance for each habit
	for habit in habits:
		importance_statement = habit.get('importance_statement', '')
		sentiment_result = analyze_sentiment(importance_statement)

		importance = sentiment_result.get('importance', 50)
		sentiment = sentiment_result.get('sentiment', 'neutral')

		# Generate motivational message
		motivation = generate_motivational_message(habit, sentiment, importance)

		# Find notification time
		notification_time = find_notification_time(
			habit.get('duration_minutes', 20),
			free_slots,
			timezone
		)

		processed_habit = {
			'habit_id': habit.get('habit_id'),
			'name': habit.get('name'),
			'importance': importance,
			'sentiment': sentiment,
			'status': 'pending',  # Will be set below
			'motivation': motivation,
			'notification_time': notification_time,
			'accountability_prompted': False,
			'duration_minutes': habit.get('duration_minutes', 20),
			'end_goal': habit.get('end_goal', '')
		}
		processed.append(processed_habit)

	# Sort by importance (highest first)
	processed.sort(key=lambda h: h['importance'], reverse=True)

	# Assign active/back_burner status
	for i, habit in enumerate(processed):
		if i < MAX_ACTIVE_HABITS:
			habit['status'] = 'active'
		else:
			habit['status'] = 'back_burner'

	return processed

