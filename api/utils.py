"""AI Agent Utilities"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pytz
from dateutil import parser


def parse_iso8601(date_string: str, timezone: str = 'America/Los_Angeles') -> datetime:
	"""Parse ISO8601 date string to timezone-aware datetime"""
	tz = pytz.timezone(timezone)
	try:
		dt = parser.isoparse(date_string)
		if dt.tzinfo is None:
			dt = tz.localize(dt)
		return dt
	except (ValueError, parser.ParserError) as e:
		raise ValueError(f'Invalid ISO8601 format: {date_string}') from e


def format_iso8601(dt: datetime) -> str:
	"""Format datetime to ISO8601 string"""
	if dt.tzinfo is None:
		raise ValueError('Datetime must be timezone-aware')
	return dt.isoformat()


def calculate_duration_minutes(start: datetime, end: datetime) -> int:
	"""Calculate duration in minutes between two datetimes"""
	if start > end:
		raise ValueError('Start time must be before end time')
	delta = end - start
	return int(delta.total_seconds() / 60)


def add_minutes(dt: datetime, minutes: int) -> datetime:
	"""Add minutes to a datetime"""
	return dt + timedelta(minutes=minutes)


def is_overdue(deadline: Optional[str], current_time: Optional[datetime] = None) -> bool:
	"""Check if a deadline is overdue"""
	if not deadline:
		return False
	if current_time is None:
		current_time = datetime.now(pytz.UTC)
	# Parse deadline with UTC timezone to match current_time
	deadline_dt = parse_iso8601(deadline, timezone='UTC')
	# Ensure both are in UTC for comparison
	if deadline_dt.tzinfo is None:
		deadline_dt = pytz.UTC.localize(deadline_dt)
	elif deadline_dt.tzinfo != pytz.UTC:
		deadline_dt = deadline_dt.astimezone(pytz.UTC)
	return current_time > deadline_dt


def validate_json_structure(data: Dict[str, Any], required_keys: list) -> bool:
	"""Validate JSON structure has required keys"""
	return all(key in data for key in required_keys)

