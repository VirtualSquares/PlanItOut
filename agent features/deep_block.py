"""Deep-Block Planner Agent Feature"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pytz
import logging
from src.utils import parse_iso8601, format_iso8601, add_minutes, calculate_duration_minutes
from src.config import DEFAULT_TIMEZONE

logger = logging.getLogger(__name__)


def create_deep_block(
	tasks: List[Dict],
	calendar_free: List[Dict],
	duration_minutes: int = 120,
	timezone: str = DEFAULT_TIMEZONE
) -> Dict[str, Any]:
	"""
	AI Agent Feature: Deep-Block Planner
	Creates interruption-free deep work blocks and pauses notifications during those blocks.
	Justifies placement by priority and focus windows to maximize productivity.
	"""
	# Validate inputs
	if not tasks:
		logger.warning("create_deep_block called with no tasks")
		return {
			'success': False,
			'message': 'No tasks provided for deep block creation.',
			'reasoning': 'AI Agent: Tasks list is empty.',
			'schedule_updates': []
		}
	
	if not calendar_free:
		logger.warning("create_deep_block called with no calendar slots")
		return {
			'success': False,
			'message': 'No available calendar slots for deep block.',
			'reasoning': 'AI Agent: No free time slots available.',
			'schedule_updates': []
		}
	
	if not isinstance(duration_minutes, int) or duration_minutes <= 0:
		logger.warning(f"Invalid duration_minutes: {duration_minutes}, using default 120")
		duration_minutes = 120
	
	# Find high-priority, deep-focus tasks
	deep_focus_tasks = [
		task for task in tasks
		if _requires_deep_focus(task)
	]
	
	if not deep_focus_tasks:
		return {
			'success': False,
			'message': 'No deep-focus tasks found. Deep blocks work best for tasks requiring concentration.',
			'reasoning': 'AI Agent: No tasks identified as requiring deep focus.'
		}
	
	# Sort by priority
	deep_focus_tasks.sort(
		key=lambda t: t.get('priority_score', 0),
		reverse=True
	)
	
	# Find suitable time slot (prefer morning for deep work)
	tz = pytz.timezone(timezone)
	current_time = datetime.now(tz)
	
	# Look for morning slots (8 AM - 12 PM)
	best_slot = None
	best_start = None
	
	for slot in calendar_free:
		slot_start = parse_iso8601(slot['start_iso'])
		slot_end = parse_iso8601(slot['end_iso'])
		slot_duration = calculate_duration_minutes(slot_start, slot_end)
		
		# Check if slot is in morning hours
		hour = slot_start.hour
		is_morning = 8 <= hour < 12
		
		# Check if slot fits the duration
		if slot_duration >= duration_minutes:
			# Prefer morning slots
			if is_morning and (best_slot is None or not best_slot.get('is_morning', False)):
				best_slot = slot
				best_start = slot_start
			elif best_slot is None:
				best_slot = slot
				best_start = slot_start
	
	if not best_slot:
		return {
			'success': False,
			'message': f'No available time slot found for {duration_minutes}-minute deep block.',
			'reasoning': 'AI Agent: Insufficient free time for deep work block.'
		}
	
	# Select tasks that fit in the block
	selected_tasks = []
	total_duration = 0
	
	for task in deep_focus_tasks:
		task_duration = task.get('duration_minutes', 60)
		if total_duration + task_duration <= duration_minutes:
			selected_tasks.append(task)
			total_duration += task_duration
		if total_duration >= duration_minutes:
			break
	
	if not selected_tasks:
		return {
			'success': False,
			'message': 'Could not fit any tasks into the deep block.',
			'reasoning': 'AI Agent: Tasks too large for available block duration.'
		}
	
	# Create deep block schedule
	block_start = best_start
	block_schedule = []
	
	for task in selected_tasks:
		task_duration = task.get('duration_minutes', 60)
		task_scheduled = {
			**task,
			'scheduled_time': format_iso8601(block_start),
			'deep_block': True,
			'justification': (
				f'AI Agent: Scheduled in deep work block. High priority task requiring '
				f'focused attention. Notifications paused during this block.'
			)
		}
		block_schedule.append(task_scheduled)
		block_start = add_minutes(block_start, task_duration)
	
	# Generate reasoning
	hour = best_start.hour
	time_period = 'morning' if 8 <= hour < 12 else 'afternoon' if 12 <= hour < 17 else 'evening'
	
	reasoning = (
		f'AI Agent created {duration_minutes}-minute deep work block in {time_period} '
		f'({format_iso8601(best_start)}). Selected {len(selected_tasks)} high-priority '
		f'deep-focus tasks. Notifications will be paused during this block to maximize '
		f'productivity and minimize interruptions.'
	)
	
	return {
		'success': True,
		'message': f'Created {duration_minutes}-minute deep work block with {len(selected_tasks)} tasks.',
		'reasoning': reasoning,
		'deep_block': {
			'start_time': format_iso8601(best_start),
			'duration_minutes': duration_minutes,
			'tasks': block_schedule,
			'notifications_paused': True
		},
		'schedule_updates': block_schedule
	}


def _requires_deep_focus(task: Dict) -> bool:
	"""Determine if task requires deep focus"""
	description = task.get('description', '').lower()
	
	# Keywords that indicate deep focus needed
	deep_focus_keywords = [
		'code', 'programming', 'write', 'design', 'analyze', 'research',
		'plan', 'strategy', 'think', 'solve', 'create', 'develop',
		'build', 'architect', 'review', 'debug', 'draft', 'study',
		'implement'
	]
	
	# Check if description contains deep focus keywords
	for keyword in deep_focus_keywords:
		if keyword in description:
			return True
	
	# High importance tasks often need deep focus
	if task.get('importance', 0) >= 70:
		return True
	
	# Long tasks (60+ min) often need deep focus
	if task.get('duration_minutes', 0) >= 60:
		return True
	
	return False

