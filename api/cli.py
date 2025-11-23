"""AI Agent CLI"""
import sys
import json
import argparse
from typing import Dict, Any
from src.processor import process_schedule_request


def main():
	"""AI Agent Command Interface: Process JSON input and output structured JSON"""
	parser = argparse.ArgumentParser(
		description='AI Agent Task Scheduler - CLI Interface'
	)
	parser.add_argument(
		'input_file',
		nargs='?',
		type=argparse.FileType('r'),
		default=sys.stdin,
		help='Input JSON file (default: stdin)'
	)
	parser.add_argument(
		'-o', '--output',
		type=argparse.FileType('w'),
		default=sys.stdout,
		help='Output JSON file (default: stdout)'
	)

	args = parser.parse_args()

	try:
		# Read input JSON
		input_data = json.load(args.input_file)

		# Validate required fields
		required_keys = ['tasks', 'calendar_free']
		if not all(key in input_data for key in required_keys):
			print(
				'Error: Input must contain "tasks" and "calendar_free" fields',
				file=sys.stderr
			)
			sys.exit(1)

		# Process with AI agent
		result = process_schedule_request(input_data)

		# Output JSON
		json.dump(result, args.output, indent=2, ensure_ascii=False)

		# Output validation summary to stderr
		validation_summary = result.get('validation_summary', '')
		if validation_summary:
			print(f'\nValidation: {validation_summary}', file=sys.stderr)

	except json.JSONDecodeError as e:
		print(f'Error: Invalid JSON input: {e}', file=sys.stderr)
		sys.exit(1)
	except Exception as e:
		print(f'Error: {e}', file=sys.stderr)
		sys.exit(1)


if __name__ == '__main__':
	main()

