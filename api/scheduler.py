"""AI Scheduling Agent"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pytz
from src.utils import (
	parse_iso8601,
	format_iso8601,
	add_minutes,
	calculate_duration_minutes
)
from src.config import MEETING_BUFFER_MINUTES
from src.break_manager import insert_breaks_in_schedule


def find_suitable_slot(
	task_duration: int,
	free_slots: List[Dict],
	prefer_morning: bool = False
) -> Optional[Dict]:
	"""
	AI Agent Autonomy: Find suitable calendar slot for task
	Uses optimization algorithms to match tasks to available time
	"""
	if not free_slots:
		return None

	# Sort slots by start time
	sorted_slots = sorted(
		free_slots,
		key=lambda s: parse_iso8601(s['start_iso'])
	)

	# If prefer_morning, prioritize earlier slots
	if prefer_morning:
		for slot in sorted_slots:
			slot_start = parse_iso8601(slot['start_iso'])
			slot_duration = calculate_duration_minutes(
				parse_iso8601(slot['start_iso']),
				parse_iso8601(slot['end_iso'])
			)
			if slot_duration >= task_duration:
				return slot

	# Otherwise, find first suitable slot
	for slot in sorted_slots:
		slot_duration = calculate_duration_minutes(
			parse_iso8601(slot['start_iso']),
			parse_iso8601(slot['end_iso'])
		)
		if slot_duration >= task_duration:
			return slot

	return None


def is_deep_focus_task(task: Dict) -> bool:
	"""AI Agent: Determine if task requires deep focus"""
	description = task.get('description', '').lower()
	group = task.get('group', '').lower()

	deep_focus_keywords = [
		'code', 'programming', 'write', 'draft', 'design', 'plan',
		'study', 'research', 'analyze', 'implement', 'develop'
	]

	return any(keyword in description or keyword in group for keyword in deep_focus_keywords)


def is_meeting_task(task: Dict) -> bool:
	"""AI Agent: Determine if task is a meeting/collaborative"""
	description = task.get('description', '').lower()
	group = task.get('group', '').lower()

	meeting_keywords = [
		'meeting', 'call', 'conference', 'discussion', 'standup',
		'sync', 'presentation', 'demo', 'interview'
	]

	return any(keyword in description or keyword in group for keyword in meeting_keywords)


def split_task(
	task: Dict,
	available_duration: int,
	slot_start: datetime
) -> List[Dict]:
	"""
	AI Agent Reasoning: Split task across multiple time slots
	Intelligently divides tasks that exceed available continuous time
	"""
	task_duration = task.get('duration_minutes', 0)
	remaining_duration = task_duration
	parts = []
	current_start = slot_start

	while remaining_duration > 0:
		part_duration = min(remaining_duration, available_duration)
		part_end = add_minutes(current_start, part_duration)

		part = {
			**task,
			'scheduled_time': format_iso8601(current_start),
			'duration_minutes': part_duration,
			'split': True,
			'part_number': len(parts) + 1,
			'total_parts': (task_duration + available_duration - 1) // available_duration
		}

		parts.append(part)
		remaining_duration -= part_duration
		current_start = part_end

	return parts


def schedule_task(
	task: Dict,
	free_slots: List[Dict],
	timezone: str = 'America/Los_Angeles'
) -> tuple[Optional[Dict], List[Dict]]:
	"""
	AI Agent Autonomy: Schedule a single task into calendar
	Returns (scheduled_task, remaining_slots)
	"""
	task_duration = task.get('duration_minutes', 0)
	prefer_morning = is_deep_focus_task(task)
	is_meeting = is_meeting_task(task)

	# Add buffer for meetings
	required_duration = task_duration
	if is_meeting:
		required_duration += MEETING_BUFFER_MINUTES * 2  # Before and after

	slot = find_suitable_slot(required_duration, free_slots, prefer_morning)

	if not slot:
		# Cannot schedule - mark for postponement
		return None, free_slots

	slot_start = parse_iso8601(slot['start_iso'])
	slot_end = parse_iso8601(slot['end_iso'])
	slot_duration = calculate_duration_minutes(slot_start, slot_end)

	# Adjust start time for meeting buffer
	if is_meeting:
		slot_start = add_minutes(slot_start, MEETING_BUFFER_MINUTES)

	# Check if task needs to be split
	if task_duration > slot_duration - (MEETING_BUFFER_MINUTES * 2 if is_meeting else 0):
		# Split the task - schedule first part in current slot
		available_duration = slot_duration - (MEETING_BUFFER_MINUTES * 2 if is_meeting else 0)
		first_part_duration = min(task_duration, available_duration)
		first_part_end = add_minutes(slot_start, first_part_duration)

		# Create first part
		first_part = {
			**task,
			'scheduled_time': format_iso8601(slot_start),
			'duration_minutes': first_part_duration,
			'split': True,
			'part_number': 1,
			'justification': (
				f'AI Agent split task across multiple parts due to limited '
				f'continuous time. Part 1 of {((task_duration + available_duration - 1) // available_duration)} scheduled.'
			),
			'quick_actions': ['Move earlier', 'Mark as urgent', 'Postpone']
		}

		# Update remaining slots - remove used portion of current slot
		remaining_slots = []
		for s in free_slots:
			if s != slot:
				remaining_slots.append(s)
			else:
				# Check if there's remaining time in this slot after first part
				if first_part_end < slot_end:
					remaining_slots.append({
						'start_iso': format_iso8601(first_part_end),
						'end_iso': slot['end_iso']
					})

		# Try to schedule remaining parts in subsequent slots
		remaining_duration = task_duration - first_part_duration
		scheduled_parts = [first_part]
		part_number = 2

		# Schedule remaining parts across available slots
		while remaining_duration > 0 and remaining_slots:
			# Find next suitable slot (any slot that can fit at least some of the remaining duration)
			# We'll take whatever fits, even if it's less than the full remaining duration
			next_slot = find_suitable_slot(
				1,  # Minimum 1 minute - we'll take whatever fits
				remaining_slots,
				prefer_morning
			)

			if not next_slot:
				# No more slots available - mark remaining as unscheduled
				unscheduled_part = {
					**task,
					'scheduled_time': None,
					'duration_minutes': remaining_duration,
					'split': True,
					'part_number': part_number,
					'justification': (
						f'AI Agent: Part {part_number} could not be scheduled due to '
						f'insufficient available time. Consider rescheduling.'
					),
					'quick_actions': ['Move earlier', 'Mark as urgent', 'Postpone']
				}
				scheduled_parts.append(unscheduled_part)
				break

			# Schedule this part
			next_slot_start = parse_iso8601(next_slot['start_iso'])
			if is_meeting:
				next_slot_start = add_minutes(next_slot_start, MEETING_BUFFER_MINUTES)

			next_slot_duration = calculate_duration_minutes(
				parse_iso8601(next_slot['start_iso']),
				parse_iso8601(next_slot['end_iso'])
			)
			available_in_slot = next_slot_duration - (MEETING_BUFFER_MINUTES * 2 if is_meeting else 0)
			part_duration = min(remaining_duration, available_in_slot)
			part_end = add_minutes(next_slot_start, part_duration)

			part = {
				**task,
				'scheduled_time': format_iso8601(next_slot_start),
				'duration_minutes': part_duration,
				'split': True,
				'part_number': part_number,
				'justification': (
					f'AI Agent: Part {part_number} of split task scheduled in available slot.'
				),
				'quick_actions': ['Move earlier', 'Mark as urgent', 'Postpone']
			}
			scheduled_parts.append(part)
			remaining_duration -= part_duration
			part_number += 1

			# Update remaining slots
			new_remaining_slots = []
			for s in remaining_slots:
				if s != next_slot:
					new_remaining_slots.append(s)
				else:
					# Check if there's remaining time in this slot
					if part_end < parse_iso8601(next_slot['end_iso']):
						new_remaining_slots.append({
							'start_iso': format_iso8601(part_end),
							'end_iso': next_slot['end_iso']
						})
			remaining_slots = new_remaining_slots

		# Return first part (caller will handle all parts via special handling)
		# Actually, we need to return all parts, but the interface expects one task
		# So we'll attach all parts to the first part for the caller to extract
		first_part['_all_split_parts'] = scheduled_parts
		return first_part, remaining_slots

	# Task fits in slot
	scheduled_end = add_minutes(slot_start, task_duration)

	# Update remaining slots
	remaining_slots = []
	for s in free_slots:
		if s == slot:
			# Check if there's remaining time in this slot
			if scheduled_end < slot_end:
				remaining_slots.append({
					'start_iso': format_iso8601(scheduled_end),
					'end_iso': slot['end_iso']
				})
		else:
			remaining_slots.append(s)

	justification_parts = []
	if prefer_morning:
		justification_parts.append('Scheduled in morning slot for deep-focus work')
	if is_meeting:
		justification_parts.append(f'Added {MEETING_BUFFER_MINUTES}-min buffers for context switching')
	if task.get('tags'):
		tags_str = ', '.join(task.get('tags', []))
		justification_parts.append(f'Tags: {tags_str}')

	justification = 'AI Agent: ' + '. '.join(justification_parts) if justification_parts else 'AI Agent scheduled task.'

	scheduled_task = {
		**task,
		'scheduled_time': format_iso8601(slot_start),
		'split': False,
		'justification': justification,
		'quick_actions': ['Move earlier', 'Mark as urgent', 'Postpone']
	}

	return scheduled_task, remaining_slots


def schedule_tasks(
	tasks: List[Dict],
	free_slots: List[Dict],
	timezone: str = 'America/Los_Angeles'
) -> List[Dict]:
	"""
	AI Agent Autonomy: Schedule all tasks into calendar slots
	Intelligently optimizes task placement with clustering and break management
	"""
	# Sort tasks by priority (highest first)
	sorted_tasks = sorted(
		tasks,
		key=lambda t: t.get('priority_score', 0),
		reverse=True
	)

	scheduled = []
	remaining_slots = free_slots.copy()

	# Cluster similar tasks together
	from src.grouper import batch_similar_tasks
	batched_tasks = batch_similar_tasks(sorted_tasks)

	# Schedule tasks by batch (similar tasks together)
	for batch in batched_tasks:
		for task in batch:
			scheduled_task, remaining_slots = schedule_task(
				task,
				remaining_slots,
				timezone
			)
			if scheduled_task:
				# Check if this task was split and has multiple parts
				if '_all_split_parts' in scheduled_task:
					# Add all split parts to schedule
					all_parts = scheduled_task.pop('_all_split_parts')
					scheduled.extend(all_parts)
				else:
					# Single task, add normally
					scheduled.append(scheduled_task)
			else:
				# Task couldn't be scheduled - mark for postponement
				task['justification'] = (
					'AI Agent: Task could not be scheduled due to insufficient '
					'available time. Consider rescheduling or splitting.'
				)
				task['quick_actions'] = ['Move earlier', 'Mark as urgent', 'Postpone']
				scheduled.append(task)

	# Insert breaks intelligently
	scheduled_with_breaks = insert_breaks_in_schedule(scheduled, timezone)

	return scheduled_with_breaks

