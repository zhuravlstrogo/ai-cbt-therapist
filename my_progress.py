# -*- coding: utf-8 -*-
"""
My progress module for viewing user's therapy progress
Provides statistics from exercises and diaries with AI-generated summaries
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
import pandas as pd
from telebot import types
from openrouter import OpenRouterClient
from config import MODEL_SIMPLE, TEMPERATURE, TOP_P, TOP_K

# Set pandas options for better handling of Excel files
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# Cache for LLM responses (in memory cache with TTL)
llm_cache = {}
CACHE_TTL_HOURS = 24  # Cache for 24 hours


def get_cache_key(user_id, data_type, data_hash):
    """Generate cache key for LLM responses"""
    return f"{user_id}_{data_type}_{data_hash}"


def get_cached_response(cache_key):
    """Get cached LLM response if still valid"""
    if cache_key in llm_cache:
        cached_data = llm_cache[cache_key]
        # Check if cache is still valid
        if datetime.now() - cached_data['timestamp'] < timedelta(hours=CACHE_TTL_HOURS):
            return cached_data['response']
    return None


def set_cached_response(cache_key, response):
    """Store LLM response in cache"""
    llm_cache[cache_key] = {
        'response': response,
        'timestamp': datetime.now()
    }


def count_completed_exercises(user_id):
    """
    Count number of completed exercises for a user
    Returns: tuple (count, list of exercise data)
    """
    try:
        if not os.path.exists('exercises.xlsx'):
            return 0, []

        df = pd.read_excel('exercises.xlsx')

        # Filter by user_id
        user_exercises = df[df['User ID'] == user_id]

        # Group by exercise name and get unique exercises
        if len(user_exercises) > 0:
            # Get unique exercise completions
            exercises_list = []
            for _, row in user_exercises.iterrows():
                exercises_list.append({
                    'name': row.get('Exercise Name', 'Unknown'),
                    'problem': row.get('Problem', ''),
                    'rating': row.get('Problem Rating', 0),
                    'date': row.get('Date Time', ''),
                    'text': row.get('Exercise Text', '')
                })

            # Count unique exercise names
            unique_exercises = user_exercises['Exercise Name'].nunique() if 'Exercise Name' in user_exercises.columns else len(user_exercises)
            return unique_exercises, exercises_list

        return 0, []

    except Exception as e:
        print(f"Error counting exercises: {e}")
        return 0, []


def count_diary_entries(user_id):
    """
    Count number of diary entries for a user
    Returns: tuple (count, list of diary data)
    """
    try:
        if not os.path.exists('diary.xlsx'):
            return 0, []

        df = pd.read_excel('diary.xlsx')

        # Filter by user_id
        user_diaries = df[df['User ID'] == user_id]

        if len(user_diaries) > 0:
            diaries_list = []
            for _, row in user_diaries.iterrows():
                diaries_list.append({
                    'type': row.get('Entry Type', 'Unknown'),
                    'text': row.get('Entry Text', ''),
                    'date': row.get('Date Time', '')
                })

            return len(user_diaries), diaries_list

        return 0, []

    except Exception as e:
        print(f"Error counting diary entries: {e}")
        return 0, []


def generate_diary_summary(diary_data, user_problems=None, user_id=None):
    """
    Generate summary of diary entries using LLM
    """
    try:
        if not diary_data:
            return "Пока нет записей в дневнике для анализа."

        # Create data hash for caching (include problems in hash for personalization)
        cache_data = {
            'data': diary_data,
            'problems': user_problems or []
        }
        data_str = json.dumps(cache_data, ensure_ascii=False, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()[:8]
        cache_key = get_cache_key(user_id or 'unknown', 'diary_summary', data_hash)

        # Check cache
        cached = get_cached_response(cache_key)
        if cached:
            print(f"Using cached diary summary for user {user_id}")
            return cached

        # Prepare diary entries for analysis
        entries_text = ""
        for entry in diary_data:
            date_str = entry.get('date', 'Без даты')
            if isinstance(date_str, pd.Timestamp):
                date_str = date_str.strftime('%d.%m.%Y')
            entries_text += f"\n- {date_str}: [{entry.get('type', '')}] {entry.get('text', '')}"

        problems_text = ""
        if user_problems:
            problems_text = f"Изначальные проблемы клиента: {', '.join(user_problems)}\n\n"

        system_prompt = """Ты опытный психолог по когнитивно-поведенческой терапии с 15-летним стажем.
Твоя задача - проанализировать дневниковые записи клиента и дать краткое профессиональное саммари.

Важно:
- Отражай и валидируй переживания клиента
- Нормализуй без обесценивания
- Будь эмпатичным и поддерживающим
- Отмечай позитивную динамику, если она есть
- Формулируй кратко (3-4 предложения)"""

        user_prompt = f"""{problems_text}Проанализируй дневниковые записи клиента:
{entries_text}

Оцени:
1. Динамику состояния (улучшение/стабильно/ухудшение)
2. Основные темы и паттерны
3. Эмоциональную окраску записей
4. Прогресс в работе с проблемами

Дай краткое саммари (3-4 предложения), отражая и валидируя переживания."""

        client = OpenRouterClient()
        response, usage = client.get_simple_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=MODEL_SIMPLE,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            top_k=TOP_K
        )

        # Cache the response
        set_cached_response(cache_key, response.strip())
        print(f"Cached diary summary for user {user_id}")

        return response.strip()

    except Exception as e:
        print(f"Error generating diary summary: {e}")
        return "Не удалось создать анализ дневниковых записей."


def generate_exercise_summary(exercise_data, user_id=None):
    """
    Generate summary of completed exercises using LLM
    """
    try:
        if not exercise_data:
            return "Пока нет выполненных упражнений для анализа."

        # Create data hash for caching
        data_str = json.dumps(exercise_data, ensure_ascii=False, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()[:8]
        cache_key = get_cache_key(user_id or 'unknown', 'exercise_summary', data_hash)

        # Check cache
        cached = get_cached_response(cache_key)
        if cached:
            print(f"Using cached exercise summary for user {user_id}")
            return cached

        # Prepare exercise data for analysis
        exercises_text = ""
        for ex in exercise_data:
            date_str = ex.get('date', 'Без даты')
            if isinstance(date_str, pd.Timestamp):
                date_str = date_str.strftime('%d.%m.%Y')
            exercises_text += f"\n- {date_str}: {ex.get('name', 'Упражнение')} для проблемы '{ex.get('problem', '')}' (важность: {ex.get('rating', 0)}/3)"

        system_prompt = """Ты опытный психолог по когнитивно-поведенческой терапии с 15-летним стажем.
Твоя задача - проанализировать выполненные клиентом упражнения и дать краткое профессиональное саммари.

Важно:
- Подчеркивай достижения и усилия клиента
- Отмечай вовлеченность в процесс
- Будь поддерживающим и мотивирующим
- Формулируй кратко (2-3 предложения)"""

        user_prompt = f"""Проанализируй выполненные упражнения:
{exercises_text}

Оцени:
1. Регулярность выполнения
2. Разнообразие проработанных тем
3. Вовлеченность в процесс терапии

Дай краткое саммари (2-3 предложения), подчеркивая сильные стороны и достижения."""

        client = OpenRouterClient()
        response, usage = client.get_simple_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=MODEL_SIMPLE,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            top_k=TOP_K
        )

        # Cache the response
        set_cached_response(cache_key, response.strip())
        print(f"Cached exercise summary for user {user_id}")

        return response.strip()

    except Exception as e:
        print(f"Error generating exercise summary: {e}")
        return "Не удалось создать анализ упражнений."


def generate_motivational_phrase(user_name, diary_summary, exercise_summary, stats):
    """
    Generate personalized motivational phrase using LLM
    """
    try:
        # Create data hash for caching
        data_str = f"{user_name}{diary_summary}{exercise_summary}{stats}"
        data_hash = hashlib.md5(data_str.encode()).hexdigest()[:8]
        cache_key = get_cache_key(user_name, 'motivation', data_hash)

        # Check cache (shorter TTL for motivational phrases)
        if cache_key in llm_cache:
            cached_data = llm_cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < timedelta(hours=12):
                return cached_data['response']

        system_prompt = """Ты опытный психолог по когнитивно-поведенческой терапии.
Твоя задача - создать персонализированную мотивирующую фразу для клиента.

Требования к фразе:
- Персонализированная (учитывает прогресс клиента)
- Позитивно-реалистичная (не токсично позитивная)
- Поддерживающая дальнейшую работу
- Краткая (1 предложение, максимум 15-20 слов)
- Теплая и искренняя"""

        context = ""
        if stats['exercises'] > 0 or stats['diaries'] > 0:
            context = f"Клиент выполнил {stats['exercises']} упражнений и сделал {stats['diaries']} записей в дневнике. "

        user_prompt = f"""Имя клиента: {user_name}
{context}
Анализ дневника: {diary_summary}
Анализ упражнений: {exercise_summary}

Создай одну короткую мотивирующую фразу (1 предложение), которая:
- Отражает текущий прогресс
- Поддерживает продолжение работы
- Звучит тепло и персонально"""

        client = OpenRouterClient()
        response, usage = client.get_simple_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=MODEL_SIMPLE,
            temperature=TEMPERATURE + 0.2,  # Slightly higher temperature for creativity
            top_p=TOP_P,
            top_k=TOP_K
        )

        # Cache the response
        set_cached_response(cache_key, response.strip())

        return response.strip()

    except Exception as e:
        print(f"Error generating motivational phrase: {e}")
        return "Каждый шаг вперед - это твоя победа, продолжай двигаться в своем темпе."


async def show_my_progress(bot, chat_id, user_id, username):
    """
    Main function to show user's progress
    """
    try:
        # Get user name from greeting states
        from greeting import user_states
        user_name = 'Друг'
        user_problems = []

        if user_id in user_states:
            user_name = user_states[user_id].get('user_name', 'Друг')
            user_problems = user_states[user_id].get('problems', [])
        else:
            # Try to get user name from diary.xlsx as fallback (take the latest entry)
            try:
                if os.path.exists('diary.xlsx'):
                    df = pd.read_excel('diary.xlsx')
                    user_rows = df[df['User ID'] == user_id]
                    if len(user_rows) > 0 and 'User Name' in df.columns:
                        # Get the last (most recent) non-empty name
                        for idx in range(len(user_rows) - 1, -1, -1):
                            name_from_diary = user_rows.iloc[idx]['User Name']
                            if pd.notna(name_from_diary) and name_from_diary and name_from_diary != 'User':
                                user_name = name_from_diary
                                print(f"Got user name from diary: {user_name}")
                                break
            except Exception as e:
                print(f"Could not get name from diary: {e}")

        # Count exercises and diaries
        exercise_count, exercise_data = count_completed_exercises(user_id)
        diary_count, diary_data = count_diary_entries(user_id)

        # Prepare statistics
        stats = {
            'exercises': exercise_count,
            'diaries': diary_count
        }

        # STEP 1: Send statistics immediately
        stats_text = f"📊 **Твой прогресс, {user_name}**\n\n"
        stats_text += "📈 **Статистика:**\n"
        stats_text += f"✅ Выполнено упражнений: {exercise_count}\n"
        stats_text += f"📖 Записей в дневнике: {diary_count}\n"

        await bot.send_message(
            chat_id,
            stats_text,
            parse_mode='Markdown'
        )

        # STEP 2: Send loading message if there's data to analyze
        if exercise_count > 0 or diary_count > 0:
            loading_text = "Провожу анализ... ⌛"
            await bot.send_message(chat_id, loading_text)

            # STEP 3: Generate analysis and send as separate message
            analysis_text = ""

            # Generate summaries only if there is data
            if diary_count > 0:
                analysis_text += "💭 **Анализ дневника:**\n"
                diary_summary = generate_diary_summary(diary_data, user_problems, user_id)
                analysis_text += f"{diary_summary}\n\n"
            else:
                diary_summary = ""

            if exercise_count > 0:
                analysis_text += "🎯 **Анализ упражнений:**\n"
                exercise_summary = generate_exercise_summary(exercise_data, user_id)
                analysis_text += f"{exercise_summary}\n\n"
            else:
                exercise_summary = ""

            # Generate motivational phrase
            motivational = generate_motivational_phrase(
                user_name,
                diary_summary or "Нет записей",
                exercise_summary or "Нет упражнений",
                stats
            )
            analysis_text += f"💪 **Напутствие:**\n{motivational}"

            # Add navigation buttons
            markup = types.InlineKeyboardMarkup()
            btn_back = types.InlineKeyboardButton(
                "🔙 Назад в меню",
                callback_data="menu:show"
            )
            markup.add(btn_back)

            # Send analysis with back button
            await bot.send_message(
                chat_id,
                analysis_text,
                reply_markup=markup,
                parse_mode='Markdown'
            )

        else:
            # No data - show starter message with action buttons
            starter_text = "💪 **С чего начать:**\n"
            starter_text += "Попробуй выполнить первое упражнение или записать свои мысли в дневник - каждый маленький шаг важен!"

            markup = types.InlineKeyboardMarkup()

            btn_exercise = types.InlineKeyboardButton(
                "🎯 Выбрать упражнение",
                callback_data="menu:select_exercise"
            )
            markup.add(btn_exercise)

            btn_diary = types.InlineKeyboardButton(
                "📝 Открыть дневник",
                callback_data="menu:diary"
            )
            markup.add(btn_diary)

            btn_back = types.InlineKeyboardButton(
                "🔙 Назад в меню",
                callback_data="menu:show"
            )
            markup.add(btn_back)

            await bot.send_message(
                chat_id,
                starter_text,
                reply_markup=markup,
                parse_mode='Markdown'
            )

    except Exception as e:
        print(f"Error showing progress: {e}")

        # Fallback message
        markup = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton(
            "🔙 Назад в меню",
            callback_data="menu:show"
        )
        markup.add(btn_back)

        error_text = "Не удалось загрузить прогресс. Попробуй позже."
        await bot.send_message(chat_id, error_text, reply_markup=markup)