# -*- coding: utf-8 -*-
"""
Diary module for emotion and thought recording
Allows users to record free-form emotional reflections and saves to Excel
"""

import os
from datetime import datetime
from telebot import types
from openpyxl import load_workbook, Workbook

# Path to the diary data file
DIARY_FILE = 'diary.xlsx'

# Store user diary states
# Format: {user_id: {'awaiting_entry': bool, 'user_name': str, 'username': str}}
user_diary_states = {}


def init_diary_file():
    """Initialize diary Excel file with headers if it doesn't exist"""
    try:
        if not os.path.exists(DIARY_FILE):
            wb = Workbook()
            ws = wb.active
            ws.title = 'Diary'

            # Add headers
            ws['A1'] = 'User ID'
            ws['B1'] = 'Username'
            ws['C1'] = 'User Name'
            ws['D1'] = 'Entry Type'
            ws['E1'] = 'Entry Text'
            ws['F1'] = 'Date Time'

            wb.save(DIARY_FILE)
            print(f"Diary file initialized: {DIARY_FILE}")
    except Exception as e:
        print(f"Error initializing diary file: {e}")


def save_diary_entry(user_id, username, user_name, entry_text):
    """
    Save diary entry to Excel file

    Args:
        user_id (int): Telegram user ID
        username (str): Telegram username
        user_name (str): User's name (from greeting)
        entry_text (str): The diary entry text
    """
    try:
        if not os.path.exists(DIARY_FILE):
            init_diary_file()

        wb = load_workbook(DIARY_FILE)
        ws = wb.active

        # Find next empty row
        next_row = ws.max_row + 1

        # Add diary entry
        ws[f'A{next_row}'] = user_id
        ws[f'B{next_row}'] = username
        ws[f'C{next_row}'] = user_name
        ws[f'D{next_row}'] = 'diary_entry'
        ws[f'E{next_row}'] = entry_text
        ws[f'F{next_row}'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        wb.save(DIARY_FILE)
        print(f"Diary entry saved for user {username}: {entry_text[:50]}...")

    except Exception as e:
        print(f"Error saving diary entry: {e}")


async def show_diary_prompt(bot, chat_id, user_id, username, user_name):
    """
    Show diary entry prompt to user

    Args:
        bot: Telegram bot instance
        chat_id: Chat ID
        user_id: User ID
        username: Username
        user_name: User's name
    """
    try:
        # Store state
        user_diary_states[user_id] = {
            'awaiting_entry': True,
            'user_name': user_name,
            'username': username
        }

        text = (
            "📖 Дневник: Эмоции и мысли\n\n"
            "Напиши, что ты думаешь или чувствуешь прямо сейчас. "
            "Это может быть несколько слов или целый рассказ - всё в свободной форме. "
            "Твоя запись будет сохранена для последующей работы. 💭\n\n"
            "Отправь своё сообщение:"
        )

        await bot.send_message(chat_id, text)

    except Exception as e:
        print(f"Error showing diary prompt: {e}")


async def handle_diary_entry(bot, message):
    """
    Handle incoming diary entry from user

    Args:
        bot: Telegram bot instance
        message: Telegram message object
    """
    try:
        user_id = message.from_user.id

        if user_id not in user_diary_states or not user_diary_states[user_id]['awaiting_entry']:
            return

        entry_text = message.text
        state = user_diary_states[user_id]

        # Save to Excel
        save_diary_entry(
            user_id,
            state['username'],
            state['user_name'],
            entry_text
        )

        # Clear state
        del user_diary_states[user_id]

        # Send confirmation
        await bot.send_message(
            message.chat.id,
            "✅ Твоя запись сохранена в дневнике 💭\n\n"
            "Спасибо, что делишься своими чувствами. "
            "Это первый шаг к лучшему пониманию себя."
        )

        # Show main menu again
        from universal_menu import show_main_menu
        await show_main_menu(bot, message.chat.id, user_id, state['username'], state['user_name'])

    except Exception as e:
        print(f"Error handling diary entry: {e}")
