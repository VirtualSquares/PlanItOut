"""Smart Deadline Negotiator Agent Feature"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pytz
import logging
from src.utils import parse_iso8601, format_iso8601
from src.config import DEFAULT_TIMEZONE

logger = logging.getLogger(__name__)


def negotiate_deadline(
	tasks: List[Dict],
	calendar_free: List[Dict],
	task_id: Optional[str] = None,
	new_deadline: Optional[str] = None,
	timezone: str = DEFAULT_TIMEZONE
) -> Dict[str, Any]:
	"""
	AI Agent Feature: Smart Deadline Negotiator
	Suggests realistic deadline extensions and creates email/snippet templates to request
	extensions based on workload and calendar analysis.
	
	Args:
		tasks: List of tasks
		calendar_free: Available calendar slots
		task_id: Optional task ID to negotiate deadline for
		new_deadline: Optional new deadline ISO string (if provided, will use this instead of calculating)
		timezone: User timezone
	"""
	# Validate inputs
	if not tasks:
		logger.warning("negotiate_deadline called with no tasks")
		return {
			'success': False,
			'message': 'No tasks provided.',
			'reasoning': 'AI Agent: Tasks list is empty.',
			'deadline_analysis': {},
			'email_template': None
		}
	
	# Find the task
	if task_id:
		task = next((t for t in tasks if t.get('task_id') == task_id), None)
	else:
		# Find most urgent task with deadline
		tasks_with_deadlines = [
			t for t in tasks
			if t.get('deadline_iso') and t.get('priority_score', 0) > 0
		]
		if not tasks_with_deadlines:
			return {
				'success': False,
				'message': 'No tasks with deadlines found.',
				'reasoning': 'AI Agent: Cannot negotiate deadline without existing deadline.'
			}
		task = max(tasks_with_deadlines, key=lambda t: t.get('priority_score', 0))
	
	if not task:
		return {
			'success': False,
			'message': 'Task not found.',
			'reasoning': 'AI Agent: Task ID not found in task list.'
		}
	
	deadline_iso = task.get('deadline_iso')
	if not deadline_iso:
		return {
			'success': False,
			'message': 'Task does not have a deadline.',
			'reasoning': 'AI Agent: Cannot negotiate deadline for task without existing deadline.'
		}
	
	# Calculate available time before deadline
	deadline_dt = parse_iso8601(deadline_iso)
	tz = pytz.timezone(timezone)
	current_time = datetime.now(tz)
	
	# Calculate total available time in calendar
	total_available_minutes = 0
	for slot in calendar_free:
		slot_start = parse_iso8601(slot['start_iso'])
		slot_end = parse_iso8601(slot['end_iso'])
		
		# Only count slots before deadline
		if slot_start < deadline_dt:
			slot_duration = (slot_end - slot_start).total_seconds() / 60
			total_available_minutes += slot_duration
	
	task_duration = task.get('duration_minutes', 60)
	
	# Calculate other tasks' time requirements
	other_tasks_time = sum(
		t.get('duration_minutes', 60)
		for t in tasks
		if t.get('task_id') != task.get('task_id') and t.get('deadline_iso')
	)
	
	# Determine if extension is needed
	time_until_deadline = (deadline_dt - current_time).total_seconds() / 3600  # hours
	needs_extension = (
		total_available_minutes < task_duration + other_tasks_time * 0.5 or
		time_until_deadline < 24  # Less than 24 hours
	)
	
	if not needs_extension:
		return {
			'success': False,
			'message': 'Deadline appears realistic based on available time.',
			'reasoning': (
				f'AI Agent: {total_available_minutes:.0f} minutes available before deadline, '
				f'task requires {task_duration} minutes. Current deadline is feasible.'
			)
		}
	
	# Use provided new_deadline or calculate suggested extension
	if new_deadline:
		try:
			new_deadline_dt = parse_iso8601(new_deadline)
			suggested_extension_hours = (new_deadline_dt - deadline_dt).total_seconds() / 3600
			logger.info(f"Using provided new_deadline: {new_deadline}")
		except Exception as e:
			logger.warning(f"Failed to parse new_deadline {new_deadline}: {e}, calculating instead")
			new_deadline_dt = None
	else:
		new_deadline_dt = None
	
	if not new_deadline_dt:
		# Suggest extension duration
		# Add buffer: task duration + 50% buffer + time for other tasks
		suggested_extension_hours = max(
			24,  # At least 1 day
			(task_duration + other_tasks_time * 0.3) / 60 + 8  # Hours needed + 8 hour buffer
		)
		new_deadline_dt = deadline_dt + timedelta(hours=suggested_extension_hours)
	else:
		suggested_extension_hours = (new_deadline_dt - deadline_dt).total_seconds() / 3600
	
	# Generate email template
	email_template = _generate_email_template(task, deadline_dt, new_deadline_dt)
	
	reasoning = (
		f'AI Agent analyzed workload and calendar. Current deadline ({format_iso8601(deadline_dt)}) '
		f'is unrealistic given {total_available_minutes:.0f} minutes available and '
		f'{task_duration} minutes required. Suggested extension: {suggested_extension_hours:.0f} hours '
		f'to {format_iso8601(new_deadline_dt)}.'
	)
	
	logger.info(f"Deadline negotiation completed: task_id={task.get('task_id')}, extension={suggested_extension_hours:.0f}h")
	
	return {
		'success': True,
		'message': f'Suggested deadline extension: {suggested_extension_hours:.0f} hours',
		'reasoning': reasoning,
		'deadline_analysis': {
			'current_deadline': format_iso8601(deadline_dt),
			'suggested_deadline': format_iso8601(new_deadline_dt),
			'extension_hours': suggested_extension_hours,
			'available_time_minutes': total_available_minutes,
			'task_duration_minutes': task_duration,
			'workload_analysis': f'{other_tasks_time} minutes for other tasks'
		},
		'email_template': email_template,
		'task_id': task.get('task_id')
	}


def _generate_email_template(
	task: Dict,
	current_deadline: datetime,
	new_deadline: datetime
) -> Dict[str, str]:
	"""Generate email template for deadline extension request"""
	task_description = task.get('description', 'Task')
	days_extension = (new_deadline - current_deadline).days
	
	subject = f"Request for Deadline Extension: {task_description}"
	
	body = f"""Dear [Recipient],

I hope this message finds you well. I am writing to request a deadline extension for the following task:

Task: {task_description}
Current Deadline: {current_deadline.strftime('%B %d, %Y at %I:%M %p')}
Requested New Deadline: {new_deadline.strftime('%B %d, %Y at %I:%M %p')}
Extension Requested: {days_extension} day{'s' if days_extension != 1 else ''}

After analyzing my current workload and calendar availability, I have determined that the current deadline is not feasible given the scope of work required. I want to ensure I deliver high-quality work, and the additional time will allow me to complete this task thoroughly.

I am happy to discuss this further and can provide more details about my current commitments if needed.

Thank you for your understanding.

Best regards,
[Your Name]"""
	
	return {
		'subject': subject,
		'body': body,
		'snippet': f"Requesting {days_extension}-day extension for {task_description}"
	}

