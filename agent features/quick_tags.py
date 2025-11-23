"""Quick-Tags Agent Feature"""
from typing import Dict, List, Optional, Any, Set
import logging
from src.grouper import group_tasks

logger = logging.getLogger(__name__)


def apply_quick_tags(
	tasks: List[Dict],
	tags: Optional[List[str]] = None,
	auto_detect: bool = True
) -> Dict[str, Any]:
	"""
	AI Agent Feature: Quick-Tags
	Enables instant task tagging (e.g., #email, #errand, #urgent) and auto-groups them
	for batch execution. Streamlines task organization and improves efficiency.
	
	Note: tags can be a single string (from OpenAI action_data) or a list
	"""
	# Handle single tag string (from OpenAI action_data)
	if isinstance(tags, str):
		tags = [tags]
		logger.info(f"Converted single tag string to list: {tags}")
	
	# Validate inputs
	if not tasks:
		logger.warning("apply_quick_tags called with no tasks")
		return {
			'success': False,
			'message': 'No tasks provided.',
			'reasoning': 'AI Agent: Cannot tag empty task list.'
		}
	
	# If tags provided, apply them
	if tags:
		tagged_tasks = []
		for task in tasks:
			existing_tags = task.get('tags', [])
			# Merge tags, avoiding duplicates
			new_tags = list(set(existing_tags + tags))
			tagged_task = {
				**task,
				'tags': new_tags,
				'justification': (
					f'AI Agent: Applied tags {tags}. '
					f'Task will be grouped with other tasks sharing these tags.'
				)
			}
			tagged_tasks.append(tagged_task)
		
		# Auto-group by tags
		grouped = _group_by_tags(tagged_tasks)
		
		return {
			'success': True,
			'message': f'Applied tags {tags} to {len(tagged_tasks)} task(s).',
			'reasoning': (
				f'AI Agent: Tagged {len(tagged_tasks)} tasks with {tags}. '
				f'Created {len(grouped)} tag-based groups for batch execution.'
			),
			'tagged_tasks': tagged_tasks,
			'groups': grouped
		}
	
	# Auto-detect tags from task descriptions
	if auto_detect:
		auto_tagged_tasks = []
		all_tags = set()
		
		for task in tasks:
			detected_tags = _detect_tags_from_description(task.get('description', ''))
			existing_tags = task.get('tags', [])
			merged_tags = list(set(existing_tags + detected_tags))
			
			if merged_tags:
				all_tags.update(merged_tags)
				tagged_task = {
					**task,
					'tags': merged_tags,
					'justification': (
						f'AI Agent: Auto-detected tags {detected_tags} from task description. '
						f'Task will be grouped for batch execution.'
					)
				}
				auto_tagged_tasks.append(tagged_task)
			else:
				auto_tagged_tasks.append(task)
		
		# Auto-group by tags
		grouped = _group_by_tags(auto_tagged_tasks)
		
		return {
			'success': True,
			'message': f'Auto-detected and applied {len(all_tags)} tag(s) to tasks.',
			'reasoning': (
				f'AI Agent: Auto-detected tags {sorted(all_tags)} from task descriptions. '
				f'Created {len(grouped)} tag-based groups for efficient batch execution.'
			),
			'tagged_tasks': auto_tagged_tasks,
			'groups': grouped,
			'detected_tags': sorted(all_tags)
		}
	
	return {
		'success': False,
		'message': 'No tags provided and auto-detect is disabled.',
		'reasoning': 'AI Agent: Cannot apply tags without tags or auto-detection.'
	}


def _detect_tags_from_description(description: str) -> List[str]:
	"""Detect tags from task description"""
	description_lower = description.lower()
	detected = []
	
	# Tag patterns
	tag_patterns = {
		'#email': ['email', 'mail', 'inbox', 'reply', 'respond'],
		'#errand': ['errand', 'pickup', 'store', 'shop', 'buy', 'purchase', 'grocery'],
		'#urgent': ['urgent', 'asap', 'immediate', 'critical', 'emergency'],
		'#coding': ['code', 'programming', 'debug', 'develop', 'implement', 'function'],
		'#meeting': ['meeting', 'call', 'zoom', 'conference', 'discuss'],
		'#reading': ['read', 'review', 'study', 'learn', 'research'],
		'#writing': ['write', 'draft', 'document', 'article', 'blog'],
		'#exercise': ['exercise', 'workout', 'gym', 'run', 'walk', 'fitness'],
		'#cooking': ['cook', 'meal', 'dinner', 'lunch', 'recipe'],
		'#cleaning': ['clean', 'organize', 'tidy', 'declutter']
	}
	
	for tag, keywords in tag_patterns.items():
		if any(keyword in description_lower for keyword in keywords):
			detected.append(tag)
	
	return detected


def _group_by_tags(tasks: List[Dict]) -> Dict[str, List[Dict]]:
	"""Group tasks by their tags"""
	groups = {}
	
	for task in tasks:
		tags = task.get('tags', [])
		if not tags:
			# Untagged tasks go to 'general' group
			if 'general' not in groups:
				groups['general'] = []
			groups['general'].append(task)
		else:
			# Group by primary tag (first tag)
			primary_tag = tags[0]
			if primary_tag not in groups:
				groups[primary_tag] = []
			groups[primary_tag].append(task)
	
	return groups

