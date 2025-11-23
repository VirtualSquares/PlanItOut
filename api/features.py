"""AI Feature Definitions"""
from typing import List, Dict


def get_features() -> List[Dict]:
	"""
	AI Agent Features: Four practical and easy-to-implement features
	"""
	return [
		{
			'name': 'Deep-Block Planner',
			'purpose': (
				'AI agent auto-creates interruption-free deep work blocks and '
				'pauses notifications during those blocks. Justifies placement by '
				'priority and focus windows to maximize productivity.'
			),
			'type': 'practical',
			'implementation_difficulty': 'medium'
		},
		{
			'name': 'Smart Deadline Negotiator',
			'purpose': (
				'AI agent suggests realistic deadline extensions and creates email/snippet '
				'templates to request extensions based on workload and calendar analysis. '
				'Helps users communicate effectively when deadlines are unrealistic.'
			),
			'type': 'practical',
			'implementation_difficulty': 'medium'
		},
		{
			'name': 'One-Click Snooze',
			'purpose': (
				'AI agent postpones a scheduled item by +15/30/60 minutes with one click '
				'and auto-reschedules dependent tasks. Provides instant flexibility when '
				'plans change.'
			),
			'type': 'easy',
			'implementation_difficulty': 'easy'
		},
		{
			'name': 'Quick-Tags',
			'purpose': (
				'AI agent enables instant task tagging (e.g., #email, #errand, #urgent) '
				'and auto-groups them for batch execution. Streamlines task organization '
				'and improves efficiency.'
			),
			'type': 'easy',
			'implementation_difficulty': 'easy'
		}
	]


def get_feature_suggestions() -> List[Dict]:
	"""
	AI Agent: Feature suggestions for future enhancements
	"""
	return [
		{
			'name': 'Context-Aware Task Batching',
			'justification': (
				'Automatically groups tasks that require similar tools, locations, or '
				'mental states to minimize context switching and maximize efficiency. '
				'For example, batch all email tasks together or all coding tasks in one block.'
			)
		},
		{
			'name': 'Energy Level Optimization',
			'justification': (
				'Learns user energy patterns throughout the day and schedules high-cognitive '
				'tasks during peak energy hours. Adapts to individual circadian rhythms for '
				'optimal productivity.'
			)
		},
		{
			'name': 'Habit Streak Tracker',
			'justification': (
				'Visualizes habit completion streaks and provides motivational feedback. '
				'Helps users maintain consistency by showing progress and celebrating milestones.'
			)
		}
	]

