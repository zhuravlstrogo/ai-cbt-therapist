# -*- coding: utf-8 -*-
"""
Greeting module for AI Psychologist bot
Handles first interaction with users after /start command
"""

import os
import asyncio
from datetime import datetime
from openpyxl import load_workbook, Workbook
from telebot import types
import protocol_known

# Store user states to track where they are in the greeting process
# Format: {user_id: {'stage': 'awaiting_name'|'awaiting_protocol_choice', 'user_name': str}}
user_states = {}

# Excel file path
EXCEL_FILE = 'messages.xlsx'


def init_greeting_excel_file():
    """Initialize Excel file with headers for greeting data"""
    if not os.path.exists(EXCEL_FILE):
        wb = Workbook()
        ws = wb.active
        ws.title = 'Messages'
        ws['A1'] = 'User ID'
        ws['B1'] = 'Username'
        ws['C1'] = 'User Name'
        ws['D1'] = 'Message Text'
        ws['E1'] = 'Message Type'
        ws['F1'] = 'Protocol Choice'
        ws['G1'] = 'Date Time'
        wb.save(EXCEL_FILE)


def update_excel_headers():
    """Update existing Excel file to include new columns if they don't exist"""
    try:
        if os.path.exists(EXCEL_FILE):
            wb = load_workbook(EXCEL_FILE)
            ws = wb.active

            # Check if headers exist, if not add them
            if ws['A1'].value is None:
                ws['A1'] = 'User ID'
            if ws['C1'].value != 'User Name':
                ws['C1'] = 'User Name'
            if ws['E1'].value != 'Message Type':
                ws['E1'] = 'Message Type'
            if ws['F1'].value != 'Protocol Choice':
                ws['F1'] = 'Protocol Choice'

            wb.save(EXCEL_FILE)
    except Exception as e:
        print(f"Error updating Excel headers: {e}")


def save_user_name_to_excel(user_id, username, user_name, message_type='greeting'):
    """Save user name and greeting message to Excel file"""
    try:
        if os.path.exists(EXCEL_FILE):
            wb = load_workbook(EXCEL_FILE)
            ws = wb.active
        else:
            init_greeting_excel_file()
            wb = load_workbook(EXCEL_FILE)
            ws = wb.active

        # Find next empty row
        next_row = ws.max_row + 1

        # Add greeting data
        ws[f'A{next_row}'] = user_id
        ws[f'B{next_row}'] = username
        ws[f'C{next_row}'] = user_name
        ws[f'D{next_row}'] = f"User provided name: {user_name}"
        ws[f'E{next_row}'] = message_type
        ws[f'G{next_row}'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Save workbook
        wb.save(EXCEL_FILE)
        print(f"User name saved to Excel: {username} - {user_name}")
    except Exception as e:
        print(f"Error saving user name to Excel: {e}")


def save_protocol_choice_to_excel(user_id, username, protocol_choice):
    """Save protocol choice to Excel file"""
    try:
        if os.path.exists(EXCEL_FILE):
            wb = load_workbook(EXCEL_FILE)
            ws = wb.active

            # Find the last row for this user
            for row in range(ws.max_row, 0, -1):
                if ws[f'A{row}'].value == user_id:
                    ws[f'F{row}'] = protocol_choice
                    break

            wb.save(EXCEL_FILE)
            print(f"Protocol choice saved to Excel: {username} - {protocol_choice}")
    except Exception as e:
        print(f"Error saving protocol choice to Excel: {e}")


async def send_greeting_messages(bot, chat_id, user_id, username):
    """Send initial greeting messages to user"""
    try:
        # Message 1: Main greeting
        greeting_text = (
            "Привет 👋\n\n"
            "Я — твой ИИ-психолог, и работаю по принципам когнитивно-поведенческой терапии (КБТ).\n"
            "Моя задача — помочь тебе разобраться с трудностями, изменить автоматические мысли "
            "и подобрать упражнения, которые реально работают."
        )
        await bot.send_message(chat_id, greeting_text)

        # Wait 7 seconds before sending disclaimer
        await asyncio.sleep(3)

        # Message 2: Disclaimer
        disclaimer_text = (
            "⚠️ Важно:\n\n"
            "Бот Aide не является заменой профессиональной психотерапевтической помощи, "
            "не предназначен для лечения тяжелых расстройств и помощи в критических, "
            "жизнеугрожающих ситуациях."
        )
        await bot.send_message(chat_id, disclaimer_text)

        # Wait 3 seconds before asking for name
        await asyncio.sleep(3)

        # Message 3: Ask for name
        name_question = "Как могу к тебе обращаться?"
        await bot.send_message(chat_id, name_question)

        # Set user state to awaiting name input
        user_states[user_id] = {'stage': 'awaiting_name'}

        print(f"Greeting messages sent to user {username} (ID: {user_id})")
    except Exception as e:
        print(f"Error sending greeting messages: {e}")


async def handle_name_input(bot, message, user_id, username):
    """Handle user name input and send protocol selection message"""
    try:
        user_name = message.text.strip()

        if not user_name or len(user_name) < 1:
            await bot.send_message(message.chat.id, "Пожалуйста, введите ваше имя.")
            return False

        # Save user name to Excel
        save_user_name_to_excel(user_id, username, user_name, 'greeting_name_input')

        # Update user state
        user_states[user_id] = {
            'stage': 'awaiting_protocol_choice',
            'user_name': user_name
        }

        # Message 4: Ask about protocol choice with buttons
        protocol_question = f"Отлично, {user_name}! Ты уже знаешь, какой протокол тебе нужен?"

        # Create inline keyboard with two buttons
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(
            "🧭 Я знаю, какой протокол мне нужен",
            callback_data="protocol_choice_yes"
        )
        btn2 = types.InlineKeyboardButton(
            "🔍 Я не знаю — помоги подобрать",
            callback_data="protocol_choice_help"
        )
        markup.add(btn1)
        markup.add(btn2)

        # Add menu button for users who want to explore
        btn_menu = types.InlineKeyboardButton(
            "📱 Главное меню",
            callback_data="menu:show"
        )
        markup.add(btn_menu)

        await bot.send_message(message.chat.id, protocol_question, reply_markup=markup)

        print(f"Protocol choice buttons sent to user {username}")
        return True

    except Exception as e:
        print(f"Error handling name input: {e}")
        return False


async def handle_protocol_choice(bot, callback_query, user_id, username):
    """Handle protocol choice selection"""
    try:
        choice = callback_query.data

        if choice == "protocol_choice_yes":
            protocol_text = "🧭 Я знаю, какой протокол мне нужен"
            save_protocol_choice_to_excel(user_id, username, protocol_text)

            # Send protocol selection buttons from protocol_known module
            await bot.answer_callback_query(callback_query.id)
            await protocol_known.send_protocol_selection(bot, callback_query.message.chat.id)

            # Update state and return early (no need to send additional message)
            if user_id in user_states:
                user_states[user_id]['stage'] = 'selecting_protocol'

            print(f"Protocol choice registered for user {username}: {choice}")
            return
        elif choice == "protocol_choice_help":
            protocol_text = "🔍 Я не знаю — помоги подобрать"
            save_protocol_choice_to_excel(user_id, username, protocol_text)

            # Start questionnaire from protocol_unknown module
            import protocol_unknown
            user_name = user_states[user_id].get('user_name', username)
            await bot.answer_callback_query(callback_query.id)
            await protocol_unknown.start_questionnaire(bot, callback_query.message.chat.id, user_id, username, user_name)

            # Update state
            if user_id in user_states:
                user_states[user_id]['stage'] = 'questionnaire_started'

            print(f"Started questionnaire for user {username}")
            return
        else:
            response = "Неизвестный выбор. Пожалуйста, выберите один из предложенных вариантов."

        # Update state
        if user_id in user_states:
            user_states[user_id]['stage'] = 'protocol_selected'

        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.message.chat.id, response)

        print(f"Protocol choice registered for user {username}: {choice}")

    except Exception as e:
        print(f"Error handling protocol choice: {e}")


def reset_user_greeting_state(user_id):
    """Reset user greeting state when /start is called again"""
    if user_id in user_states:
        del user_states[user_id]
    print(f"User greeting state reset for user ID: {user_id}")
