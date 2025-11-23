"""One-Click Snooze Agent Feature"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pytz
import logging
from src.utils import parse_iso8601, format_iso8601, add_minutes
from src.scheduler import schedule_task
from src.config import DEFAULT_TIMEZONE

logger = logging.getLogger(__name__)


def snooze_task(
	tasks: List[Dict],
	calendar_free: List[Dict],
	task_id: str,
	snooze_minutes: int = 30,
	timezone: str = DEFAULT_TIMEZONE
) -> Dict[str, Any]:
	"""
	AI Agent Feature: One-Click Snooze
	Postpones a scheduled item by +15/30/60 minutes with one click and auto-reschedules
	dependent tasks. Provides instant flexibility when plans change.
	
	Note: snooze_minutes can also be passed as 'hours' in action_data (converted to minutes)
	"""
	# Validate inputs
	if not tasks:
		logger.warning("snooze_task called with no tasks")
		return {
			'success': False,
			'message': 'No tasks provided.',
			'reasoning': 'AI Agent: Tasks list is empty.',
			'schedule_updates': []
		}
	
	if not task_id:
		logger.warning("snooze_task called without task_id")
		return {
			'success': False,
			'message': 'Task ID is required.',
			'reasoning': 'AI Agent: No task ID provided.',
			'schedule_updates': []
		}
	
	# Handle hours parameter (convert to minutes)
	if isinstance(snooze_minutes, (int, float)) and snooze_minutes > 0 and snooze_minutes < 24:
		# If it's a small number, might be hours
		pass  # Keep as is
	elif isinstance(snooze_minutes, (int, float)) and snooze_minutes >= 24:
		# Likely hours, convert to minutes
		snooze_minutes = int(snooze_minutes * 60)
		logger.info(f"Converted hours to minutes: {snooze_minutes}")
	
	if not isinstance(snooze_minutes, (int, float)) or snooze_minutes <= 0:
		logger.warning(f"Invalid snooze_minutes: {snooze_minutes}, using default 30")
		snooze_minutes = 30
	
	snooze_minutes = int(snooze_minutes)
	
	# Find the task
	task = next((t for t in tasks if t.get('task_id') == task_id), None)
	
	if not task:
		return {
			'success': False,
			'message': f'Task {task_id} not found.',
			'reasoning': 'AI Agent: Task ID not found in task list.'
		}
	
	current_scheduled_time = task.get('scheduled_time')
	
	if not current_scheduled_time:
		return {
			'success': False,
			'message': 'Task is not currently scheduled.',
			'reasoning': 'AI Agent: Cannot snooze unscheduled task. Please schedule it first.'
		}
	
	# Calculate new scheduled time
	current_time_dt = parse_iso8601(current_scheduled_time)
	new_scheduled_time = add_minutes(current_time_dt, snooze_minutes)
	
	# Check if new time conflicts with other scheduled tasks
	# (This is a simplified check - in production, you'd check against full schedule)
	
	# Update task
	snoozed_task = {
		**task,
		'scheduled_time': format_iso8601(new_scheduled_time),
		'snoozed': True,
		'snooze_minutes': snooze_minutes,
		'justification': (
			f'AI Agent: Task snoozed by {snooze_minutes} minutes. '
			f'Original time: {current_scheduled_time}, new time: {format_iso8601(new_scheduled_time)}.'
		)
	}
	
	# Check for dependent tasks (tasks that might depend on this one)
	# Simple heuristic: tasks with same group or similar description
	dependent_tasks = [
		t for t in tasks
		if (
			t.get('task_id') != task_id and
			t.get('scheduled_time') and
			(
				t.get('group') == task.get('group') or
				_are_tasks_related(t, task)
			)
		)
	]
	
	# Reschedule dependent tasks if needed
	rescheduled_dependent = []
	if dependent_tasks:
		for dep_task in dependent_tasks:
			dep_scheduled = parse_iso8601(dep_task.get('scheduled_time'))
			# If dependent task is scheduled before the new time, might need adjustment
			if dep_scheduled < new_scheduled_time:
				# Check if there's a conflict
				dep_duration = dep_task.get('duration_minutes', 60)
				dep_end = add_minutes(dep_scheduled, dep_duration)
				
				if dep_end > new_scheduled_time:
					# Conflict detected - reschedule dependent task
					new_dep_time = add_minutes(new_scheduled_time, task.get('duration_minutes', 60))
					dep_task['scheduled_time'] = format_iso8601(new_dep_time)
					dep_task['justification'] = (
						f'AI Agent: Auto-rescheduled due to dependency on snoozed task {task_id}.'
					)
					rescheduled_dependent.append(dep_task)
	
	reasoning = (
		f'AI Agent snoozed task "{task.get("description")}" by {snooze_minutes} minutes. '
		f'New scheduled time: {format_iso8601(new_scheduled_time)}. '
		f'{len(rescheduled_dependent)} dependent task(s) auto-rescheduled to prevent conflicts.'
	)
	
	return {
		'success': True,
		'message': f'Task snoozed by {snooze_minutes} minutes',
		'reasoning': reasoning,
		'snoozed_task': snoozed_task,
		'dependent_tasks_rescheduled': rescheduled_dependent,
		'schedule_updates': [snoozed_task] + rescheduled_dependent
	}


def _are_tasks_related(task1: Dict, task2: Dict) -> bool:
	"""Check if two tasks are related (simple heuristic)"""
	desc1 = task1.get('description', '').lower()
	desc2 = task2.get('description', '').lower()
	
	# Check for common keywords
	common_words = set(desc1.split()) & set(desc2.split())
	return len(common_words) >= 2

