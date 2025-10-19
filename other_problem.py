# -*- coding: utf-8 -*-
"""
Module for handling custom "other problems" in the goal setting process
Allows users to describe problems in free text and get LLM suggestions
"""

from typing import List, Tuple
from telebot import types
from openrouter import OpenRouterClient

# Initialize OpenRouter client
openrouter_client = OpenRouterClient()

# Store user states for other problem flow
# Format: {user_id: {'step': str, 'text': str, 'suggestions': [str], 'selected_problems': [str], 'selected_suggestions': [str], 'other_count': int}}
user_other_problem_states = {}

# Maximum number of "other problems" a user can add
MAX_OTHER_PROBLEMS = 3

# Import PROBLEMS list from goal.py for reference
from goal import PROBLEMS

# Map problem IDs to display names for easy lookup
PROBLEM_MAP = {p_id: display_name for display_name, p_id in PROBLEMS}


async def classify_user_problem(user_text: str) -> List[Tuple[str, str]]:
    """
    Use LLM to classify user's problem text into 1-3 categories from PROBLEMS
    Returns list of tuples (display_name, problem_id)
    """
    try:
        # Create JSON schema for structured response
        json_schema = {
            "name": "problem_classification",
            "schema": {
                "type": "object",
                "properties": {
                    "suggested_problems": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "problem_id": {
                                    "type": "string",
                                    "enum": [p_id for _, p_id in PROBLEMS if p_id != "other"],
                                    "description": "Problem ID from the predefined list"
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                    "description": "Confidence score for this classification"
                                }
                            },
                            "required": ["problem_id", "confidence"],
                            "additionalProperties": False
                        },
                        "minItems": 1,
                        "maxItems": 3,
                        "description": "1-3 most relevant problems from the list"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why these categories were chosen"
                    }
                },
                "required": ["suggested_problems", "reasoning"],
                "additionalProperties": False
            }
        }

        # Create system message for context
        system_message = """You are a psychological assistant helping to categorize user problems.
        The user will describe their problem in Russian, and you need to suggest 1-3 most relevant categories.
        Focus on the core psychological issue, not surface symptoms.
        Return categories ordered by relevance (highest confidence first)."""

        # Create user prompt
        prompt = f"""Пользователь описал свою проблему: "{user_text}"

Проанализируй текст и предложи 1-3 наиболее подходящие категории из списка:
- anxiety: Тревога, беспокойство
- apathy: Потеря интереса, апатия / Сниженное настроение
- mood: Пониженное настроение
- sleep: Проблемы со сном
- procrastination: Прокрастинация, снижение сил/мотивации
- communication: Трудности в общении
- self_criticism: Самокритичность, чувство вины
- anger: Раздражительность, вспышки гнева
- ocd: Навязчивые мысли, действия (ОКР)
- panic: Панические атаки
- social_anxiety: Неуверенность в компаниях людей (социальная тревога)
- perfectionism: Перфекционизм
- loss: Переживание утраты / жизненные перемены
- burnout: Стресс, усталость, выгорание
- resilience: Хочу укрепить устойчивость

Выбери категории, которые лучше всего описывают суть проблемы пользователя."""

        # Get structured response from LLM
        response, _ = openrouter_client.get_structured_response(
            prompt=prompt,
            json_schema=json_schema,
            system_message=system_message
        )

        # Convert response to list of tuples
        suggestions = []
        for item in response.get("suggested_problems", []):
            problem_id = item["problem_id"]
            if problem_id in PROBLEM_MAP:
                display_name = PROBLEM_MAP[problem_id]
                suggestions.append((display_name, problem_id))

        # Return at least one suggestion, fallback to general anxiety if empty
        if not suggestions:
            suggestions = [(PROBLEM_MAP["anxiety"], "anxiety")]

        return suggestions[:3]  # Ensure max 3 suggestions

    except Exception as e:
        print(f"Error classifying problem: {e}")
        # Return default suggestion on error
        return [(PROBLEM_MAP["anxiety"], "anxiety")]


async def start_other_problem_flow(bot, chat_id, user_id, username):
    """
    Start the "other problem" flow when user selects "➕ Другая проблема"
    """
    try:
        # Check if user has already added max number of other problems
        if user_id in user_other_problem_states:
            other_count = user_other_problem_states[user_id].get('other_count', 0)
            if other_count >= MAX_OTHER_PROBLEMS:
                await bot.send_message(
                    chat_id,
                    f"Ты уже добавил(а) максимальное количество дополнительных проблем ({MAX_OTHER_PROBLEMS}).\n"
                    "Нажми 'Готово', чтобы продолжить."
                )
                return False

        # Initialize or update user state
        if user_id not in user_other_problem_states:
            user_other_problem_states[user_id] = {
                'step': 'awaiting_text',
                'username': username,
                'text': '',
                'suggestions': [],
                'selected_problems': [],
                'selected_suggestions': [],  # Track which suggestions are selected
                'other_count': 0
            }
        else:
            user_other_problem_states[user_id]['step'] = 'awaiting_text'
            user_other_problem_states[user_id]['selected_suggestions'] = []  # Reset selections

        # Request problem description from user
        from universal_menu import get_menu_button
        markup = get_menu_button()

        await bot.send_message(
            chat_id,
            "Пиши свою проблему или трудность своими словами:",
            reply_markup=markup
        )

        return True

    except Exception as e:
        print(f"Error starting other problem flow: {e}")
        return False


async def handle_other_problem_text(bot, message):
    """
    Handle user's text input describing their problem
    """
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id

        # Check if user is in other problem flow
        if user_id not in user_other_problem_states:
            return False

        state = user_other_problem_states[user_id]

        if state['step'] != 'awaiting_text' and state['step'] != 'awaiting_custom_name':
            return False

        text = message.text.strip()

        if state['step'] == 'awaiting_text':
            # Store user's problem description
            state['text'] = text

            # Show typing indicator while processing
            await bot.send_chat_action(chat_id, 'typing')

            # Get LLM suggestions
            suggestions = await classify_user_problem(text)
            state['suggestions'] = suggestions

            # Create response message
            response_text = f"Спасибо, я услышал(а): {text}\n\nПохоже на (можешь выбрать несколько):"

            # Create inline keyboard with suggestions and actions
            markup = types.InlineKeyboardMarkup()

            # Add suggested problem buttons with checkmarks for selected items
            for display_name, problem_id in suggestions:
                # Check if this suggestion is already selected
                is_selected = problem_id in state.get('selected_suggestions', [])
                button_text = f"{'✓ ' if is_selected else ''}{display_name}"

                btn = types.InlineKeyboardButton(
                    button_text,
                    callback_data=f"other_suggest:{problem_id}"
                )
                markup.add(btn)

            # Add action buttons
            # Only show "Confirm selected" if at least one suggestion is selected
            if state.get('selected_suggestions'):
                btn_confirm_selected = types.InlineKeyboardButton(
                    "✅ Подтвердить выбранные",
                    callback_data="other_confirm_selected:confirm"
                )
                markup.add(btn_confirm_selected)

                btn_custom = types.InlineKeyboardButton(
                    "✏️ Указать своё название проблемы",
                    callback_data="other_custom:name"
                )
                markup.add(btn_custom)
            else:
                # Show navigation options only when nothing is selected
                btn_custom = types.InlineKeyboardButton(
                    "✏️ Указать своё название проблемы",
                    callback_data="other_custom:name"
                )
                btn_another = types.InlineKeyboardButton(
                    "➕ Другая проблема",
                    callback_data="other_another:add"
                )
                btn_done = types.InlineKeyboardButton(
                    "✅ Готово",
                    callback_data="other_done:finish"
                )

                markup.add(btn_custom)
                markup.add(btn_another)
                markup.add(btn_done)

            # Add menu button at the bottom
            btn_menu = types.InlineKeyboardButton(
                "📱 Главное меню",
                callback_data="menu:show"
            )
            markup.add(btn_menu)

            await bot.send_message(chat_id, response_text, reply_markup=markup)

            # Update step
            state['step'] = 'choosing_option'

        elif state['step'] == 'awaiting_custom_name':
            # Handle custom problem name
            custom_name = text

            # Add to selected problems
            if 'selected_problems' not in state:
                state['selected_problems'] = []
            state['selected_problems'].append(custom_name)

            # Increment other problem count
            state['other_count'] = state.get('other_count', 0) + 1

            # Show confirmation and next options
            await show_problem_added_options(bot, chat_id, user_id, custom_name)

        return True

    except Exception as e:
        print(f"Error handling other problem text: {e}")
        return False


async def handle_other_problem_callback(bot, callback_query, action, data):
    """
    Handle callbacks for other problem flow
    """
    try:
        user_id = callback_query.from_user.id
        username = callback_query.from_user.username or 'Unknown'
        chat_id = callback_query.message.chat.id

        # Answer callback immediately
        await bot.answer_callback_query(callback_query.id, show_alert=False)

        if user_id not in user_other_problem_states:
            return

        state = user_other_problem_states[user_id]

        if action == "other_suggest":
            # Toggle selection of the suggested problem
            problem_id = data

            # Initialize selected_suggestions if not exists
            if 'selected_suggestions' not in state:
                state['selected_suggestions'] = []

            # Toggle the selection
            if problem_id in state['selected_suggestions']:
                state['selected_suggestions'].remove(problem_id)
            else:
                state['selected_suggestions'].append(problem_id)

            # Update the message to show current selection state
            await update_suggestion_buttons(bot, callback_query, state)

        elif action == "other_confirm_selected":
            # User confirmed selected suggestions
            if 'selected_suggestions' in state and state['selected_suggestions']:
                # Add all selected problems to the selected_problems list
                if 'selected_problems' not in state:
                    state['selected_problems'] = []

                for problem_id in state['selected_suggestions']:
                    if problem_id in PROBLEM_MAP:
                        display_name = PROBLEM_MAP[problem_id]
                        if display_name not in state['selected_problems']:
                            state['selected_problems'].append(display_name)

                # Increment other problem count
                state['other_count'] = state.get('other_count', 0) + 1

                # Show confirmation
                selected_names = [PROBLEM_MAP[p_id] for p_id in state['selected_suggestions'] if p_id in PROBLEM_MAP]
                await show_problems_added_options(bot, chat_id, user_id, selected_names)

        elif action == "other_custom":
            # User wants to specify custom name
            state['step'] = 'awaiting_custom_name'

            from universal_menu import get_menu_button
            markup = get_menu_button()

            await bot.send_message(
                chat_id,
                "Введи своё название проблемы (можешь использовать эмодзи):",
                reply_markup=markup
            )

        elif action == "other_another":
            # User wants to add another problem
            # Check limit
            other_count = state.get('other_count', 0)
            if other_count >= MAX_OTHER_PROBLEMS:
                await bot.send_message(
                    chat_id,
                    f"Ты уже добавил(а) максимальное количество дополнительных проблем ({MAX_OTHER_PROBLEMS}).\n"
                    "Нажми 'Готово', чтобы продолжить."
                )
            else:
                # Always start a new full problem flow
                # This will ask "Пиши свою проблему или трудность своими словами:"
                # and show suggestions based on the user's input
                await start_other_problem_flow(bot, chat_id, user_id, username)

        elif action == "other_done":
            # Finish other problem flow and return to main goal flow
            await finish_other_problem_flow(bot, chat_id, user_id)

    except Exception as e:
        print(f"Error handling other problem callback: {e}")


async def update_suggestion_buttons(bot, callback_query, state):
    """
    Update the suggestion buttons to reflect current selection state
    """
    try:
        chat_id = callback_query.message.chat.id
        message_id = callback_query.message.message_id

        # Recreate the markup with updated selection state
        markup = types.InlineKeyboardMarkup()

        # Add suggested problem buttons with checkmarks for selected items
        for display_name, problem_id in state.get('suggestions', []):
            is_selected = problem_id in state.get('selected_suggestions', [])
            button_text = f"{'✓ ' if is_selected else ''}{display_name}"

            btn = types.InlineKeyboardButton(
                button_text,
                callback_data=f"other_suggest:{problem_id}"
            )
            markup.add(btn)

        # Add action buttons
        # Only show "Confirm selected" if at least one suggestion is selected
        if state.get('selected_suggestions'):
            btn_confirm_selected = types.InlineKeyboardButton(
                "✅ Подтвердить выбранные",
                callback_data="other_confirm_selected:confirm"
            )
            markup.add(btn_confirm_selected)

            btn_custom = types.InlineKeyboardButton(
                "✏️ Указать своё название проблемы",
                callback_data="other_custom:name"
            )
            markup.add(btn_custom)
        else:
            # Show navigation options only when nothing is selected
            btn_custom = types.InlineKeyboardButton(
                "✏️ Указать своё название проблемы",
                callback_data="other_custom:name"
            )
            btn_another = types.InlineKeyboardButton(
                "➕ Другая проблема",
                callback_data="other_another:add"
            )
            btn_done = types.InlineKeyboardButton(
                "✅ Готово",
                callback_data="other_done:finish"
            )

            markup.add(btn_custom)
            markup.add(btn_another)
            markup.add(btn_done)

        # Add menu button at the bottom (for both cases)
        btn_menu = types.InlineKeyboardButton(
            "📱 Главное меню",
            callback_data="menu:show"
        )
        markup.add(btn_menu)

        # Update the message
        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup
        )

    except Exception as e:
        print(f"Error updating suggestion buttons: {e}")


async def show_problems_added_options(bot, chat_id, user_id, problem_names):
    """
    Show options after problems have been added (supports multiple)
    """
    try:
        state = user_other_problem_states.get(user_id)
        if not state:
            return

        other_count = state.get('other_count', 0)
        remaining = MAX_OTHER_PROBLEMS - other_count

        # Format message for single or multiple problems
        if isinstance(problem_names, list):
            problems_text = '\n'.join([f"  • {p}" for p in problem_names])
            message = f"✅ Добавлены проблемы:\n{problems_text}\n\n"
        else:
            # Backward compatibility for single problem
            message = f"✅ Добавлена проблема: {problem_names}\n\n"

        if remaining > 0:
            message += f"Ты можешь добавить ещё {remaining} проблем(у)."
        else:
            message += "Ты добавил(а) максимальное количество проблем."

        # Create buttons
        markup = types.InlineKeyboardMarkup()

        if remaining > 0:
            btn_another = types.InlineKeyboardButton(
                "➕ Добавить ещё проблему",
                callback_data="other_another:add"
            )
            markup.add(btn_another)

        btn_done = types.InlineKeyboardButton(
            "✅ Готово",
            callback_data="other_done:finish"
        )
        markup.add(btn_done)

        # Add menu button at the bottom
        btn_menu = types.InlineKeyboardButton(
            "📱 Главное меню",
            callback_data="menu:show"
        )
        markup.add(btn_menu)

        await bot.send_message(chat_id, message, reply_markup=markup)

        # Reset step for potential next problem
        state['step'] = 'choosing_option'
        # Clear selected suggestions for next round
        state['selected_suggestions'] = []

    except Exception as e:
        print(f"Error showing problems added options: {e}")


async def show_problem_added_options(bot, chat_id, user_id, problem_name):
    """
    Show options after a single problem has been added
    Wrapper for backward compatibility
    """
    await show_problems_added_options(bot, chat_id, user_id, problem_name)


async def finish_other_problem_flow(bot, chat_id, user_id):
    """
    Finish the other problem flow and return to main goal flow
    """
    try:
        from goal import user_goal_states
        from greeting import user_states

        if user_id not in user_other_problem_states:
            return

        state = user_other_problem_states[user_id]
        selected_problems = state.get('selected_problems', [])

        # Add selected problems to goal state
        if user_id in user_goal_states and selected_problems:
            goal_state = user_goal_states[user_id]

            # Add to problems list
            if 'problems' not in goal_state:
                goal_state['problems'] = []

            # Track if we have standard problems
            has_standard_problems = False
            standard_problems = []

            for problem in selected_problems:
                if problem not in goal_state['problems']:
                    goal_state['problems'].append(problem)
                    # Check if this is a standard problem from PROBLEMS list
                    if problem in [display_name for display_name, _ in PROBLEMS]:
                        has_standard_problems = True
                        standard_problems.append(problem)

            # Show confirmation
            problems_text = '\n'.join([f"✓ {p}" for p in selected_problems])
            await bot.send_message(
                chat_id,
                f"Добавлены проблемы:\n{problems_text}"
            )

            # Get username for both cases
            username = state.get('username', 'Unknown')

            # If we have standard problems, automatically set ratings and go to exercises
            if has_standard_problems:
                # Set default ratings for new standard problems (2 = medium)
                if 'problem_ratings' not in goal_state:
                    goal_state['problem_ratings'] = {}

                for problem in standard_problems:
                    if problem not in goal_state['problem_ratings']:
                        goal_state['problem_ratings'][problem] = 2  # Default medium rating

                # Save to persistent user states
                if user_id not in user_states:
                    user_states[user_id] = {'username': username}

                user_states[user_id]['goal'] = goal_state.get('goal', '')
                user_states[user_id]['problems'] = goal_state['problems']
                user_states[user_id]['problem_ratings'] = goal_state['problem_ratings']

                # Import and show exercise recommendations
                from exercise import show_exercise_recommendations

                # Show exercise recommendations for problems with ratings
                await show_exercise_recommendations(
                    bot, chat_id, user_id, username,
                    goal_state['problem_ratings']
                )
            else:
                # For custom problems without exercises, show main menu directly
                from universal_menu import show_main_menu
                from greeting import user_states

                # Save to persistent user states
                if user_id not in user_states:
                    user_states[user_id] = {'username': username}

                user_states[user_id]['goal'] = goal_state.get('goal', '')
                user_states[user_id]['problems'] = goal_state['problems']
                # Custom problems don't need ratings, so we can skip that
                user_states[user_id]['problem_ratings'] = goal_state.get('problem_ratings', {})

                # Get user display info
                user_name = user_states[user_id].get('user_name', 'User')
                form_of_address = user_states[user_id].get('form', 'ты')

                # Show main menu with menu button
                from universal_menu import get_menu_button
                markup = get_menu_button()

                await bot.send_message(
                    chat_id,
                    "✅ Мы добавили проблему в работу 👩‍🔧 Теперь ты можешь использовать другие функции бота.",
                    reply_markup=markup
                )

        # Clean up state
        del user_other_problem_states[user_id]

    except Exception as e:
        print(f"Error finishing other problem flow: {e}")


def register_handlers():
    """
    Register message and callback handlers for other problem flow
    Called from main.py
    """
    # This function will be called from goal.py when needed
    pass
