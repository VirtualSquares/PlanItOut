"""OpenAI Client for AI Agent - Refactored"""
import json
import re
import logging
from typing import Dict, List, Optional, Any
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# OpenAI Configuration
try:
    import openai
    from openai import OpenAI, APIError, RateLimitError, APIConnectionError
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OpenAI = None
    APIError = Exception
    RateLimitError = Exception
    APIConnectionError = Exception
    OPENAI_AVAILABLE = False

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

from src.scheduler import schedule_tasks
from src.features import get_features
from src.prioritizer import calculate_priority_score
from src.agent_features import (
    create_deep_block,
    negotiate_deadline,
    snooze_task,
    apply_quick_tags
)


def _format_tasks_for_prompt(tasks: List[Dict]) -> str:
    """Format tasks for prompt"""
    if not tasks:
        return 'No tasks provided'
    
    formatted = []
    for task in tasks:
        desc = task.get('description', '')
        duration = task.get('duration_minutes', 0)
        deadline = task.get('deadline_iso', 'No deadline')
        importance = task.get('importance', 50)
        formatted.append(f"- {desc} ({duration} min, importance: {importance}, deadline: {deadline})")
    
    return '\n'.join(formatted)


def _format_calendar_for_prompt(calendar_free: List[Dict]) -> str:
    """Format calendar slots for prompt"""
    if not calendar_free:
        return 'No free time slots available'
    
    formatted = []
    for slot in calendar_free:
        start = slot.get('start_iso', '')
        end = slot.get('end_iso', '')
        formatted.append(f"- {start} to {end}")
    
    return '\n'.join(formatted)


def _format_habits_for_prompt(habits: List[Dict]) -> str:
    """Format habits for prompt"""
    if not habits:
        return 'No habits'
    
    formatted = []
    for habit in habits:
        name = habit.get('name', '')
        duration = habit.get('duration_minutes', 0)
        formatted.append(f"- {name} ({duration} min)")
    
    return '\n'.join(formatted)


def _build_agent_system_prompt() -> str:
    """Build system prompt for the AI agent"""
    features = get_features()
    features_text = '\n'.join([
        f"- {f['name']}: {f['purpose']}"
        for f in features
    ])
    
    return f"""You are an AI Task Scheduling and Habit Management Agent. You help users manage their tasks, schedule their time, and build productive habits.

## Your Capabilities

### Core Features:
1. **Task Prioritization**: Calculate priority scores using deadline (50%), importance (40%), effort (-10%), and overdue bonus (+30%)
2. **Task Grouping**: Semantically group similar tasks (emails, errands, coding, meetings) for batch execution
3. **Intelligent Scheduling**: Fit tasks into calendar slots, split large tasks, insert breaks after 90 min work blocks
4. **Habit Management**: Process up to 3 active habits/day, analyze sentiment, provide motivational messages

### Advanced Features:
{features_text}

## Your Rules

### Prioritization Logic:
- Score = deadline_factor * 0.5 + importance_norm * 0.4 + effort_factor * -0.1 + overdue_bonus
- Deadline factor: Closer deadline = higher (normalized inverse of time until deadline)
- Importance: User-declared importance scaled to [0,1]
- Effort factor: Longer tasks get slightly lower score (prefer quick wins)
- Overdue bonus: +0.3 if task is overdue

### Scheduling Rules:
- Prefer morning slots (8 AM - 12 PM) for deep-focus work
- Cluster similar tasks together
- Schedule meetings with 30-minute buffer before/after
- Insert breaks: 10-15 min after 90 min work, 5-10 min after 50 min
- If task duration > available slot, split across multiple slots
- If total duration exceeds free time, suggest rescheduling or splitting

### Habit Rules:
- Maximum 3 active habits per day
- Analyze sentiment of importance statement to determine importance (0-100)
- Set notification time at earliest free slot after 08:00 local time
- Provide motivational messages with MLA-formatted citations

## Response Format

When users ask questions or request actions, respond in JSON format:
{{
  "response": "Your conversational response to the user",
  "reasoning": "AI Agent reasoning for the action/response",
  "action": "action_type",  // One of: "schedule", "deep_block", "snooze", "tag", "deadline", "habit", "info", "none"
  "action_data": {{}},  // Data for the action (if applicable)
  "quick_actions": ["action1", "action2"],  // Suggested quick actions
  "schedule_updates": []  // Updated schedule items (if action affects schedule)
}}

Always provide clear reasoning for your decisions and suggest helpful next actions."""


def _parse_json_response(response_text: str) -> Optional[Dict[str, Any]]:
    """Parse JSON from OpenAI response with multiple fallback strategies"""
    if not response_text:
        return None
    
    # Strategy 1: Try direct JSON parse
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract JSON from markdown code blocks
    json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_block_match:
        try:
            return json.loads(json_block_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Strategy 3: Extract JSON object from text
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    return None


def _execute_action(
    action: str,
    action_data: Dict[str, Any],
    tasks: Optional[List[Dict]],
    calendar_free: Optional[List[Dict]],
    timezone: str
) -> Dict[str, Any]:
    """Execute agent action and return schedule updates"""
    schedule_updates = []
    result_data = {}
    
    try:
        if action == 'deep_block' and tasks and calendar_free:
            duration = action_data.get('duration_minutes', 120)
            if not isinstance(duration, int) or duration <= 0:
                duration = 120
            logger.info(f"Executing deep_block action with duration: {duration}")
            deep_block_result = create_deep_block(tasks, calendar_free, duration, timezone)
            if deep_block_result.get('success'):
                schedule_updates = deep_block_result.get('schedule_updates', [])
                result_data['reasoning'] = deep_block_result.get('reasoning', '')
        
            elif action == 'snooze' and tasks and calendar_free:
                task_id = action_data.get('task_id')
                # Handle both 'hours' and 'snooze_minutes' parameters
                hours = action_data.get('hours')
                snooze_minutes = action_data.get('snooze_minutes', 30)
                
                if hours:
                    # Convert hours to minutes
                    if not isinstance(hours, (int, float)) or hours <= 0:
                        hours = 24
                    snooze_minutes = int(hours * 60)
                elif not isinstance(snooze_minutes, (int, float)) or snooze_minutes <= 0:
                    snooze_minutes = 30
                else:
                    snooze_minutes = int(snooze_minutes)
                
                logger.info(f"Executing snooze action for task: {task_id}, minutes: {snooze_minutes}")
                snooze_result = snooze_task(tasks, calendar_free, task_id, snooze_minutes, timezone)
            if snooze_result.get('success'):
                schedule_updates = snooze_result.get('schedule_updates', [])
                result_data['reasoning'] = snooze_result.get('reasoning', '')
        
            elif action == 'tag':
                tag = action_data.get('tag', '')
                tags = action_data.get('tags', [])
                # Handle both single tag and tags list
                if tag:
                    tags_to_apply = [tag] if isinstance(tag, str) else tag if isinstance(tag, list) else []
                elif tags:
                    tags_to_apply = tags if isinstance(tags, list) else [tags] if isinstance(tags, str) else []
                else:
                    tags_to_apply = []
                
                if not tags_to_apply:
                    logger.warning("Tag action called without tag or tags")
                    return {'schedule_updates': [], 'result_data': {}}
                logger.info(f"Executing tag action with tags: {tags_to_apply}")
                tagged_result = apply_quick_tags(tasks or [], tags_to_apply)
            if tagged_result.get('success'):
                result_data['tagged_tasks'] = tagged_result.get('tagged_tasks', [])
                result_data['reasoning'] = tagged_result.get('reasoning', '')
        
        elif action == 'deadline' and tasks:
            task_id = action_data.get('task_id')
            new_deadline = action_data.get('new_deadline')
            if not task_id or not new_deadline:
                logger.warning("Deadline action called without task_id or new_deadline")
                return {'schedule_updates': [], 'result_data': {}}
            logger.info(f"Executing deadline negotiation for task: {task_id}")
            deadline_result = negotiate_deadline(tasks, task_id, new_deadline, timezone)
            if deadline_result.get('success'):
                result_data['deadline_analysis'] = deadline_result.get('deadline_analysis', {})
                result_data['email_template'] = deadline_result.get('email_template')
                result_data['reasoning'] = deadline_result.get('reasoning', '')
        
    except Exception as e:
        logger.error(f"Error executing action {action}: {str(e)}", exc_info=True)
    
    return {'schedule_updates': schedule_updates, 'result_data': result_data}


def _call_openai_with_retry(
    client: OpenAI,
    messages: List[Dict[str, str]],
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> str:
    """Call OpenAI API with retry logic"""
    last_error = None
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=messages,
                temperature=0.7,
                response_format={'type': 'json_object'},
                timeout=30.0
            )
            return response.choices[0].message.content or ''
        
        except RateLimitError as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                import time
                time.sleep(wait_time)
            else:
                raise
        
        except APIConnectionError as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(f"Connection error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                import time
                time.sleep(wait_time)
            else:
                raise
        
        except APIError as e:
            last_error = e
            # Don't retry on client errors (4xx)
            if e.status_code and 400 <= e.status_code < 500:
                raise
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(f"API error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                import time
                time.sleep(wait_time)
            else:
                raise
        
        except Exception as e:
            last_error = e
            logger.error(f"Unexpected error calling OpenAI: {str(e)}")
            raise
    
    if last_error:
        raise last_error
    
    return ''


def chat_with_agent(
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    tasks: Optional[List[Dict]] = None,
    calendar_free: Optional[List[Dict]] = None,
    habits: Optional[List[Dict]] = None,
    timezone: str = 'America/Los_Angeles'
) -> Dict[str, Any]:
    """
    AI Agent Conversational Interface: Chat with the AI agent using OpenAI
    Understands natural language and routes to appropriate agent functions
    """
    if not OPENAI_API_KEY or not OPENAI_AVAILABLE:
        logger.error("OpenAI not configured: API_KEY={}, AVAILABLE={}".format(
            bool(OPENAI_API_KEY), OPENAI_AVAILABLE
        ))
        return {
            'success': False,
            'response': 'AI Agent is not configured. Please set OPENAI_API_KEY in your environment variables.',
            'reasoning': 'AI Agent: OpenAI API key not available or openai package not installed.',
            'action': 'none',
            'action_data': {},
            'quick_actions': ['Schedule Tasks', 'Add Habit', 'View Calendar'],
            'schedule_updates': []
        }
    
    try:
        # Build context
        context_parts = []
        
        if tasks:
            context_parts.append(f"Current Tasks:\n{_format_tasks_for_prompt(tasks)}")
        
        if calendar_free:
            context_parts.append(f"Available Calendar Slots:\n{_format_calendar_for_prompt(calendar_free)}")
        
        if habits:
            context_parts.append(f"Current Habits:\n{_format_habits_for_prompt(habits)}")
        
        context = '\n\n'.join(context_parts) if context_parts else 'No tasks, calendar, or habits provided.'
        
        # Build conversation history for OpenAI
        messages = [
            {
                'role': 'system',
                'content': _build_agent_system_prompt() + f'\n\n## Current Context\n\n{context}\n\nTimezone: {timezone}'
            }
        ]
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role in ['user', 'assistant']:
                    messages.append({
                        'role': role,
                        'content': content
                    })
        
        # Add current user message
        messages.append({
            'role': 'user',
            'content': f"{user_message}\n\nProvide your response as JSON following the format specified in the system prompt. Be helpful, explain your reasoning, and suggest appropriate actions."
        })
        
        # Call OpenAI API with retry logic
        logger.info(f"Sending chat request to OpenAI (message length: {len(user_message)})")
        client = OpenAI(api_key=OPENAI_API_KEY)
        response_text = _call_openai_with_retry(client, messages)
        
        # Parse JSON from response
        result = _parse_json_response(response_text)
        
        if not result:
            # Fallback: return text response if JSON parsing fails
            logger.warning("Failed to parse JSON from OpenAI response, using text response")
            return {
                'success': True,
                'response': response_text,
                'reasoning': 'AI Agent: Provided conversational response (JSON parsing failed).',
                'action': 'none',
                'action_data': {},
                'quick_actions': ['Schedule Tasks', 'Add Habit', 'View Calendar'],
                'schedule_updates': []
            }
        
        # Execute action if specified
        action = result.get('action', 'none')
        action_data = result.get('action_data', {})
        
        if action != 'none' and action_data:
            execution_result = _execute_action(
                action,
                action_data,
                tasks,
                calendar_free,
                timezone
            )
            result['schedule_updates'] = execution_result['schedule_updates']
            # Merge result data (reasoning, tagged_tasks, etc.)
            for key, value in execution_result['result_data'].items():
                if value:  # Only update if value is not empty
                    result[key] = value
        
        # Ensure required fields
        result['success'] = True
        result.setdefault('quick_actions', ['Schedule Tasks', 'Add Habit', 'View Calendar'])
        result.setdefault('schedule_updates', [])
        result.setdefault('action_data', {})
        result.setdefault('reasoning', 'AI Agent: Processed request successfully.')
        
        logger.info(f"Chat request completed successfully (action: {action})")
        return result
    
    except RateLimitError as e:
        logger.error(f"OpenAI rate limit error: {str(e)}")
        return {
            'success': False,
            'response': 'I\'m currently experiencing high demand. Please wait a moment and try again.',
            'reasoning': f'AI Agent: Rate limit error - {str(e)}',
            'action': 'none',
            'action_data': {},
            'quick_actions': ['Schedule Tasks', 'Add Habit', 'View Calendar'],
            'schedule_updates': []
        }
    
    except APIConnectionError as e:
        logger.error(f"OpenAI connection error: {str(e)}")
        return {
            'success': False,
            'response': 'I\'m having trouble connecting to the AI service. Please check your internet connection and try again.',
            'reasoning': f'AI Agent: Connection error - {str(e)}',
            'action': 'none',
            'action_data': {},
            'quick_actions': ['Schedule Tasks', 'Add Habit', 'View Calendar'],
            'schedule_updates': []
        }
    
    except APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return {
            'success': False,
            'response': f'I encountered an API error: {str(e)}. Please try again or use the quick actions.',
            'reasoning': f'AI Agent: API error - {str(e)}',
            'action': 'none',
            'action_data': {},
            'quick_actions': ['Schedule Tasks', 'Add Habit', 'View Calendar'],
            'schedule_updates': []
        }
    
    except Exception as e:
        logger.error(f"Unexpected error in chat_with_agent: {str(e)}", exc_info=True)
        return {
            'success': False,
            'response': f'I encountered an unexpected error: {str(e)}. Please try again or use the quick actions.',
            'reasoning': f'AI Agent: Unexpected error - {str(e)}',
            'action': 'none',
            'action_data': {},
            'quick_actions': ['Schedule Tasks', 'Add Habit', 'View Calendar'],
            'schedule_updates': []
        }
