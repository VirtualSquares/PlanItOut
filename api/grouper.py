"""AI Task Grouping Agent"""
from typing import Dict, List
import re


# AI Agent: Semantic understanding patterns for task categorization
GROUP_PATTERNS = {
	'Emails': [
		r'\b(email|reply|respond|inbox|message|correspondence)\b',
		r'\b(send|read|check|review.*email)\b'
	],
	'Errands': [
		r'\b(errand|grocery|shopping|store|pickup|delivery|post office|bank)\b',
		r'\b(buy|purchase|get|fetch|collect)\b'
	],
	'Coding': [
		r'\b(code|programming|develop|debug|fix|implement|refactor|test|git|commit)\b',
		r'\b(function|class|api|endpoint|database|sql|python|javascript|typescript)\b'
	],
	'Study': [
		r'\b(study|learn|read|research|review|notes|homework|assignment|exam|test)\b',
		r'\b(chapter|book|article|course|lecture|practice)\b'
	],
	'Meetings': [
		r'\b(meeting|call|conference|discussion|standup|sync|presentation|demo)\b',
		r'\b(zoom|teams|video|phone|interview)\b'
	],
	'Writing': [
		r'\b(write|draft|edit|document|report|blog|article|essay|proposal)\b',
		r'\b(content|copy|manuscript|script)\b'
	],
	'Planning': [
		r'\b(plan|organize|schedule|prepare|outline|strategy|roadmap)\b',
		r'\b(design|architecture|structure|framework)\b'
	]
}


def analyze_task_semantics(description: str) -> str:
	"""
	AI Agent Intelligence: Semantic analysis to identify task category
	Uses pattern matching and keyword detection for intelligent categorization
	"""
	description_lower = description.lower()
	scores = {}

	for group, patterns in GROUP_PATTERNS.items():
		score = 0
		for pattern in patterns:
			matches = len(re.findall(pattern, description_lower, re.IGNORECASE))
			score += matches
		if score > 0:
			scores[group] = score

	if scores:
		# Return group with highest score
		return max(scores.items(), key=lambda x: x[1])[0]

	# Default group for uncategorized tasks
	return 'General'


def group_tasks(tasks: List[Dict]) -> List[Dict]:
	"""
	AI Agent Reasoning: Group similar tasks for efficiency
	Analyzes task descriptions to identify semantic similarity and assign group labels
	"""
	grouped = []

	for task in tasks:
		description = task.get('description', '')
		group = analyze_task_semantics(description)

		grouped_task = {
			**task,
			'group': group
		}
		grouped.append(grouped_task)

	return grouped


def batch_similar_tasks(tasks: List[Dict]) -> List[List[Dict]]:
	"""
	AI Agent Optimization: Batch similar tasks together for efficiency
	Groups tasks by their assigned group label
	"""
	grouped = group_tasks(tasks)
	batches = {}

	for task in grouped:
		group = task.get('group', 'General')
		if group not in batches:
			batches[group] = []
		batches[group].append(task)

	# Return batches sorted by group name
	return [batches[group] for group in sorted(batches.keys())]

