"""AI Task Prioritization Agent"""
from typing import Dict, List, Optional
from datetime import datetime
import pytz
from src.utils import parse_iso8601, is_overdue


def calculate_priority_score(
	task: Dict,
	current_time: Optional[datetime] = None
) -> float:
	"""
	AI Agent Reasoning: Calculate priority score using intelligent algorithm
	Score = deadline_factor * 0.5 + importance_norm * 0.4 + effort_factor * -0.1 + overdue_bonus
	"""
	if current_time is None:
		current_time = datetime.now(pytz.UTC)

	# Deadline factor: normalized inverse of time until deadline
	deadline_factor = 0.0
	deadline_iso = task.get('deadline_iso')
	if deadline_iso:
		try:
			deadline_dt = parse_iso8601(deadline_iso)
			time_until_deadline = (deadline_dt - current_time).total_seconds()
			
			if time_until_deadline <= 0:
				# Overdue - maximum urgency
				deadline_factor = 1.0
			else:
				# Normalize: closer deadline = higher factor
				# Use inverse relationship: 1 / (1 + hours_until_deadline)
				hours_until = time_until_deadline / 3600
				deadline_factor = min(1.0, 1.0 / (1.0 + hours_until / 24))
		except (ValueError, TypeError):
			deadline_factor = 0.0

	# Importance normalization: scale to [0, 1]
	importance = task.get('importance', 0)
	importance_norm = min(1.0, max(0.0, importance / 100.0))

	# Effort factor: longer tasks get slightly lower score (prefer quick wins)
	duration_minutes = task.get('duration_minutes', 60)
	# Normalize duration: 0-30 min = 1.0, 60 min = 0.9, 120+ min = 0.7
	if duration_minutes <= 30:
		effort_factor = 1.0
	elif duration_minutes <= 60:
		effort_factor = 0.9
	elif duration_minutes <= 120:
		effort_factor = 0.8
	else:
		effort_factor = 0.7

	# Overdue bonus
	overdue_bonus = 0.3 if is_overdue(deadline_iso, current_time) else 0.0

	# Calculate final score
	score = (
		deadline_factor * 0.5 +
		importance_norm * 0.4 +
		effort_factor * -0.1 +
		overdue_bonus
	)

	return min(1.0, max(0.0, score))


def generate_visual_tags(task: Dict, current_time: Optional[datetime] = None) -> List[str]:
	"""AI Agent: Generate intelligent visual tags based on task properties"""
	if current_time is None:
		current_time = datetime.now(pytz.UTC)

	tags = []
	deadline_iso = task.get('deadline_iso')
	duration_minutes = task.get('duration_minutes', 60)
	importance = task.get('importance', 0)

	# Overdue detection
	if deadline_iso and is_overdue(deadline_iso, current_time):
		tags.append('Overdue')

	# Due today
	if deadline_iso:
		try:
			deadline_dt = parse_iso8601(deadline_iso)
			hours_until = (deadline_dt - current_time).total_seconds() / 3600
			if 0 <= hours_until <= 24:
				tags.append('Due today')
		except (ValueError, TypeError):
			pass

	# High importance
	if importance >= 80:
		tags.append('High importance')

	# Quick win
	if duration_minutes <= 30:
		tags.append('Quick win')

	return tags


def prioritize_tasks(tasks: List[Dict]) -> List[Dict]:
	"""
	AI Agent Reasoning: Prioritize tasks using intelligent scoring
	Returns tasks sorted by priority (highest first) with priority scores and tags
	"""
	current_time = datetime.now(pytz.UTC)

	# Calculate priority for each task
	prioritized = []
	for task in tasks:
		priority_score = calculate_priority_score(task, current_time)
		tags = generate_visual_tags(task, current_time)

		# Determine urgency level
		if priority_score >= 0.7:
			urgency = 'high'
		elif priority_score >= 0.4:
			urgency = 'medium'
		else:
			urgency = 'low'

		prioritized_task = {
			**task,
			'priority': round(priority_score * 100),  # Scale to 0-100
			'urgency': urgency,
			'tags': tags,
			'priority_score': priority_score
		}
		prioritized.append(prioritized_task)

	# Sort by priority score (descending)
	prioritized.sort(key=lambda x: x['priority_score'], reverse=True)

	return prioritized

