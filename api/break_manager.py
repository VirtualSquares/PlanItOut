"""AI Break Management Agent"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import pytz
from src.utils import parse_iso8601, format_iso8601, add_minutes, calculate_duration_minutes
from src.config import BREAK_AFTER_90_MIN, BREAK_AFTER_50_MIN


def should_insert_break(
	cumulative_work_minutes: int,
	last_break_minutes_ago: Optional[int] = None
) -> Tuple[bool, int]:
	"""
	AI Agent Wellness: Determine if a break should be inserted
	Returns (should_insert, break_duration_minutes)
	"""
	# After 90 minutes of work, insert 10-15 minute break
	if cumulative_work_minutes >= 90:
		return (True, BREAK_AFTER_90_MIN)

	# After 50 minutes of work, insert 5-10 minute micro-break
	if cumulative_work_minutes >= 50:
		return (True, BREAK_AFTER_50_MIN)

	return (False, 0)


def create_break_event(
	start_time: datetime,
	break_duration: int,
	cumulative_work: int
) -> Dict:
	"""AI Agent: Create a break event with justification"""
	justification = (
		f'AI Agent inserted {break_duration}-minute break after '
		f'{cumulative_work} minutes of focused work to maintain cognitive health '
		f'and productivity. Research shows regular breaks improve focus and prevent burnout.'
	)

	return {
		'type': 'break',
		'description': f'Break ({break_duration} min)',
		'scheduled_time': format_iso8601(start_time),
		'duration_minutes': break_duration,
		'justification': justification,
		'cumulative_work_minutes': cumulative_work
	}


def insert_breaks_in_schedule(
	scheduled_tasks: List[Dict],
	timezone: str = 'America/Los_Angeles'
) -> List[Dict]:
	"""
	AI Agent Wellness: Insert breaks intelligently throughout the schedule
	Monitors cumulative work time and inserts breaks to maintain cognitive health
	"""
	if not scheduled_tasks:
		return []

	result = []
	cumulative_work = 0
	last_break_time: Optional[datetime] = None
	tz = pytz.timezone(timezone)

	for i, task in enumerate(scheduled_tasks):
		# Skip if this is already a break
		if task.get('type') == 'break':
			result.append(task)
			continue

		task_start = parse_iso8601(task['scheduled_time'])
		task_duration = task.get('duration_minutes', 0)

		# Check if we need a break before this task
		should_break, break_duration = should_insert_break(cumulative_work)

		if should_break and cumulative_work > 0:
			# Calculate break start time
			break_start = task_start - timedelta(minutes=break_duration)

			# Check if break would overlap with previous task
			overlaps = False
			available_gap_start = None
			available_gap_duration = 0

			if result:
				# Get the last scheduled item (could be a task or break)
				last_item = result[-1]
				if last_item.get('type') != 'break':
					# It's a task - check if break overlaps
					last_task_start = parse_iso8601(last_item['scheduled_time'])
					last_task_duration = last_item.get('duration_minutes', 0)
					last_task_end = add_minutes(last_task_start, last_task_duration)
					break_end = add_minutes(break_start, break_duration)

					# Check if break overlaps with previous task
					# Overlap occurs if: break starts before previous task ends AND break ends after previous task starts
					if break_start < last_task_end and break_end > last_task_start:
						overlaps = True
						# Check if there's a gap between last task and current task
						gap_duration = calculate_duration_minutes(last_task_end, task_start)
						if gap_duration >= break_duration:
							# There's enough space in the gap - use it
							available_gap_start = last_task_end
							available_gap_duration = gap_duration
				else:
					# Last item is a break - check if new break would overlap with it
					last_break_start = parse_iso8601(last_item['scheduled_time'])
					last_break_duration = last_item.get('duration_minutes', 0)
					last_break_end = add_minutes(last_break_start, last_break_duration)
					break_end = add_minutes(break_start, break_duration)

					# Check if break overlaps with previous break
					if break_start < last_break_end and break_end > last_break_start:
						overlaps = True
						# Check if there's a gap between last break and current task
						gap_duration = calculate_duration_minutes(last_break_end, task_start)
						if gap_duration >= break_duration:
							available_gap_start = last_break_end
							available_gap_duration = gap_duration

			# Also verify break doesn't extend past current task start
			break_end = add_minutes(break_start, break_duration)
			if break_end > task_start:
				# Break would extend into current task - this is invalid
				overlaps = True
				# Try to fit break in available gap instead
				if not available_gap_start:
					# Calculate available time before current task
					if result:
						last_item = result[-1]
						if last_item.get('type') != 'break':
							last_task_end = add_minutes(
								parse_iso8601(last_item['scheduled_time']),
								last_item.get('duration_minutes', 0)
							)
						else:
							last_task_end = add_minutes(
								parse_iso8601(last_item['scheduled_time']),
								last_item.get('duration_minutes', 0)
							)
						gap_duration = calculate_duration_minutes(last_task_end, task_start)
						if gap_duration >= break_duration:
							available_gap_start = last_task_end
							available_gap_duration = gap_duration

			# Insert break if it doesn't overlap, or if there's a suitable gap
			if not overlaps:
				# Break fits before current task without overlap
				break_event = create_break_event(
					break_start,
					break_duration,
					cumulative_work
				)
				result.append(break_event)
				last_break_time = break_start
				cumulative_work = 0  # Reset after break
			elif available_gap_start and available_gap_duration >= break_duration:
				# Insert break in the gap between previous and current task
				break_event = create_break_event(
					available_gap_start,
					break_duration,
					cumulative_work
				)
				result.append(break_event)
				last_break_time = available_gap_start
				cumulative_work = 0  # Reset after break
			# else: Break would overlap and no suitable gap - skip this break

		# Add the task
		result.append(task)

		# Update cumulative work time
		cumulative_work += task_duration

	return result

