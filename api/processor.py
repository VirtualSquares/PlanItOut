"""AI Agent Main Processor"""
from typing import Dict, List, Any
from src.prioritizer import prioritize_tasks
from src.grouper import group_tasks
from src.scheduler import schedule_tasks
from src.habits import process_habits
from src.gemini_client import optimize_schedule
from src.output_formatter import format_output
from src.config import DEFAULT_TIMEZONE


def process_schedule_request(input_data: Dict[str, Any]) -> Dict[str, Any]:
	"""
	AI Agent Orchestration: Main processing function
	Coordinates all agent components to produce scheduled output
	"""
	# Extract input
	tasks = input_data.get('tasks', [])
	calendar_free = input_data.get('calendar_free', [])
	habits_input = input_data.get('habits', [])
	timezone = input_data.get('timezone', DEFAULT_TIMEZONE)

	# Validation messages (agent reasoning)
	validation_messages = []

	# Step 1: Prioritize tasks
	prioritized = prioritize_tasks(tasks)
	validation_messages.append(
		f'AI Agent prioritized {len(prioritized)} tasks using intelligent scoring algorithm.'
	)

	# Step 2: Group tasks
	grouped = group_tasks(prioritized)
	validation_messages.append(
		f'AI Agent grouped tasks into {len(set(t.get("group") for t in grouped))} categories for efficiency.'
	)

	# Step 3: Process habits
	processed_habits = process_habits(habits_input, calendar_free, timezone)
	active_count = sum(1 for h in processed_habits if h.get('status') == 'active')
	validation_messages.append(
		f'AI Agent processed {len(processed_habits)} habits, {active_count} active, '
		f'{len(processed_habits) - active_count} on back-burner.'
	)

	# Step 4: Optimize schedule (try Gemini, fallback to local)
	# Note: Frontend now uses OpenAI, so Gemini is optional here
	gemini_result = optimize_schedule(
		grouped,
		calendar_free,
		habits_input,
		timezone,
		use_gemini=False  # Disable Gemini by default since frontend uses OpenAI
	)

	scheduled = gemini_result.get('optimized_schedule', [])

	if gemini_result.get('success'):
		validation_messages.append(
			'AI Agent optimized schedule using Gemini API with intelligent reasoning.'
		)
	else:
		validation_messages.append(
			'AI Agent used local heuristic scheduler (Gemini API unavailable). '
			'Maintained full functionality with intelligent fallback.'
		)

	# Step 5: Format output
	output = format_output(
		scheduled,
		processed_habits,
		gemini_result,
		calendar_free,
		tasks,
		habits_input,
		timezone
	)

	# Add validation summary
	output['validation_summary'] = ' '.join(validation_messages)

	return output

