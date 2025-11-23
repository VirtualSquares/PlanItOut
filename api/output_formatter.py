"""AI Output Formatter"""
from typing import Dict, List, Any
from src.features import get_features, get_feature_suggestions
from src.config import GEMINI_API_KEY


def format_schedule_item(task: Dict) -> Dict:
	"""Format a scheduled task item with all required fields"""
	return {
		'task_id': task.get('task_id', ''),
		'description': task.get('description', ''),
		'group': task.get('group', 'General'),
		'priority': task.get('priority', 0),
		'urgency': task.get('urgency', 'low'),
		'scheduled_time': task.get('scheduled_time') or '',
		'duration_minutes': task.get('duration_minutes', 0),
		'split': task.get('split', False),
		'justification': task.get('justification', 'AI Agent scheduled task.'),
		'quick_actions': task.get('quick_actions', ['Move earlier', 'Mark as urgent', 'Postpone'])
	}


def format_habit_item(habit: Dict) -> Dict:
	"""Format a habit item with all required fields"""
	motivation = habit.get('motivation', {})
	return {
		'habit_id': habit.get('habit_id', ''),
		'name': habit.get('name', ''),
		'importance': habit.get('importance', 50),
		'sentiment': habit.get('sentiment', 'neutral'),
		'status': habit.get('status', 'active'),
		'motivation': {
			'message': motivation.get('message', ''),
			'citations': motivation.get('citations', [])
		},
		'notification_time': habit.get('notification_time', ''),
		'accountability_prompted': habit.get('accountability_prompted', False)
	}


def generate_cursor_prompt(scheduled_tasks: List[Dict]) -> str:
	"""
	AI Agent: Generate concise action-oriented cursor prompt (max 12 words)
	Recommends the top-next action based on highest priority scheduled task
	"""
	if not scheduled_tasks:
		return 'No tasks scheduled. Add tasks to begin.'

	# Find highest priority task that's not a break
	work_tasks = [t for t in scheduled_tasks if t.get('type') != 'break']
	if not work_tasks:
		return 'Schedule complete. Take a break!'

	# Sort by priority
	work_tasks.sort(key=lambda t: t.get('priority', 0), reverse=True)
	top_task = work_tasks[0]

	description = top_task.get('description', 'Task')
	duration = top_task.get('duration_minutes', 0)
	scheduled_time = top_task.get('scheduled_time', '')

	# Extract time for display
	try:
		from src.utils import parse_iso8601
		dt = parse_iso8601(scheduled_time)
		time_str = dt.strftime('%H:%M')
	except:
		time_str = 'soon'

	# Create concise prompt (max 12 words)
	words = f'Start: {description} — {duration}m at {time_str}'.split()
	if len(words) > 12:
		# Truncate description if needed
		desc_words = description.split()[:8]
		words = ['Start:'] + desc_words + [f'—', f'{duration}m', 'at', time_str]

	return ' '.join(words[:12])


def format_output(
	scheduled_tasks: List[Dict],
	habits: List[Dict],
	gemini_result: Dict,
	calendar_free: List[Dict],
	tasks_input: List[Dict],
	habits_input: List[Dict],
	timezone: str = 'America/Los_Angeles'
) -> Dict[str, Any]:
	"""
	AI Agent Communication: Format agent reasoning into strict JSON structure
	Produces exactly the required output format with all fields
	"""
	# Format schedule items
	schedule = []
	for task in scheduled_tasks:
		if task.get('type') == 'break':
			# Format break as schedule item
			scheduled_time = task.get('scheduled_time') or ''
			schedule.append({
				'task_id': f"break_{scheduled_time}",
				'description': task.get('description', 'Break'),
				'group': 'Wellness',
				'priority': 0,
				'urgency': 'low',
				'scheduled_time': scheduled_time,
				'duration_minutes': task.get('duration_minutes', 0),
				'split': False,
				'justification': task.get('justification', 'AI Agent inserted break for cognitive health.'),
				'quick_actions': ['Move earlier', 'Mark as urgent', 'Postpone']
			})
		else:
			schedule.append(format_schedule_item(task))

	# Ensure at least one schedule item
	if not schedule:
		schedule.append({
			'task_id': 'sample_1',
			'description': 'Sample scheduled task',
			'group': 'General',
			'priority': 50,
			'urgency': 'medium',
			'scheduled_time': '2025-11-22T09:00:00-08:00',
			'duration_minutes': 30,
			'split': False,
			'justification': 'AI Agent: Sample task for demonstration.',
			'quick_actions': ['Move earlier', 'Mark as urgent', 'Postpone']
		})

	# Format habit items
	formatted_habits = [format_habit_item(h) for h in habits]

	# Ensure at least one habit item
	if not formatted_habits:
		formatted_habits.append({
			'habit_id': 'sample_habit_1',
			'name': 'Sample habit',
			'importance': 60,
			'sentiment': 'positive',
			'status': 'active',
			'motivation': {
				'message': 'Sample motivational message for habit tracking.',
				'citations': [
					'<p>Clear, James. <em>Atomic Habits: An Easy & Proven Way to Build '
					'Good Habits & Break Bad Ones</em>. Avery, 2018.</p>'
				]
			},
			'notification_time': '2025-11-22T08:00:00-08:00',
			'accountability_prompted': False
		})

	# Get features
	features = get_features()

	# Get feature suggestions
	feature_suggestions = get_feature_suggestions()

	# Format Gemini API call info
	gemini_api_call = {
		'endpoint': 'google-generativeai (gemini-pro)' if GEMINI_API_KEY else 'not configured',
		'input': {
			'tasks': tasks_input,
			'calendar_free': calendar_free,
			'habits': habits_input,
			'timezone': timezone
		},
		'output_format': ['features', 'schedule', 'habits', 'feature_suggestions', 'cursor_prompt']
	}

	# Add error info if Gemini failed
	if not gemini_result.get('success', False):
		gemini_api_call['error'] = gemini_result.get('error', {})

	# Generate cursor prompt
	cursor_prompt = generate_cursor_prompt(scheduled_tasks)

	# Build final output
	output = {
		'features': features,
		'schedule': schedule,
		'habits': formatted_habits,
		'gemini_api_call': gemini_api_call,
		'feature_suggestions': feature_suggestions,
		'cursor_prompt': cursor_prompt
	}

	return output

