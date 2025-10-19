# -*- coding: utf-8 -*-
"""
Greeting module for AI Psychologist bot
Handles first interaction with users after /start command
New flow: Form of address (ты/Вы) → Name input → Motivation message
"""

import os
import asyncio
from datetime import datetime
from openpyxl import load_workbook, Workbook
from telebot import types

# Store user states to track where they are in the greeting process
# Format: {user_id: {'stage': 'awaiting_form_choice'|'awaiting_name'|'ready_to_start', 'form': 'ты'|'Вы', 'user_name': str}}
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
        ws['F1'] = 'Form of Address'  # 'ты' or 'Вы'
        ws['G1'] = 'Protocol Choice'
        ws['H1'] = 'Date Time'
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
            if ws['F1'].value != 'Form of Address':
                ws['F1'] = 'Form of Address'
            if ws['G1'].value != 'Protocol Choice':
                ws['G1'] = 'Protocol Choice'

            wb.save(EXCEL_FILE)
    except Exception as e:
        print(f"Error updating Excel headers: {e}")


def save_form_of_address_to_excel(user_id, username, form_of_address):
    """Save form of address (ты/Вы) to Excel file"""
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

        # Add form of address data
        ws[f'A{next_row}'] = user_id
        ws[f'B{next_row}'] = username
        ws[f'F{next_row}'] = form_of_address
        ws[f'E{next_row}'] = 'form_of_address_choice'
        ws[f'H{next_row}'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Save workbook
        wb.save(EXCEL_FILE)
        print(f"Form of address saved to Excel: {username} - {form_of_address}")
    except Exception as e:
        print(f"Error saving form of address to Excel: {e}")


def get_form_of_address_from_excel(user_id):
    """Get form of address for user from Excel file (for subsequent /start calls)"""
    try:
        if os.path.exists(EXCEL_FILE):
            wb = load_workbook(EXCEL_FILE)
            ws = wb.active

            # Find the last row for this user with form of address
            for row in range(ws.max_row, 0, -1):
                if ws[f'A{row}'].value == user_id and ws[f'F{row}'].value in ['ты', 'Вы']:
                    return ws[f'F{row}'].value

            return None
    except Exception as e:
        print(f"Error getting form of address from Excel: {e}")
        return None


def save_user_name_to_excel(user_id, username, user_name):
    """Save user name to Excel file"""
    try:
        if os.path.exists(EXCEL_FILE):
            wb = load_workbook(EXCEL_FILE)
            ws = wb.active
        else:
            init_greeting_excel_file()
            wb = load_workbook(EXCEL_FILE)
            ws = wb.active

        # Find the last row for this user and update it with the name
        for row in range(ws.max_row, 0, -1):
            if ws[f'A{row}'].value == user_id:
                ws[f'C{row}'] = user_name
                ws[f'D{row}'] = f"User provided name: {user_name}"
                ws[f'E{row}'] = 'name_input'
                ws[f'H{row}'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                break

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

            # Find the last row for this user and update protocol choice
            for row in range(ws.max_row, 0, -1):
                if ws[f'A{row}'].value == user_id:
                    ws[f'G{row}'] = protocol_choice
                    break

            wb.save(EXCEL_FILE)
            print(f"Protocol choice saved to Excel: {username} - {protocol_choice}")
    except Exception as e:
        print(f"Error saving protocol choice to Excel: {e}")


async def send_greeting_messages(bot, chat_id, user_id, username):
    """Send initial greeting message with form of address selection"""
    try:
        # Always send greeting text
        greeting_text = (
            "Привет 👋\n\n"
            "Я — твой ИИ-психолог, работающий по принципам когнитивно-поведенческой терапии (КБТ).\n"
            "Моя задача — помочь тебе разобраться с трудностями, изменить автоматические мысли "
            "и подобрать упражнения, которые реально работают.\n\n"
            "Как я могу к тебе обращаться — на ты или на Вы?"
        )

        # Create inline keyboard with form of address options
        markup = types.InlineKeyboardMarkup()
        btn_ty = types.InlineKeyboardButton(
            "Можно на ты",
            callback_data="form_address:ty"
        )
        btn_vy = types.InlineKeyboardButton(
            "Можно на Вы",
            callback_data="form_address:vy"
        )
        markup.add(btn_ty)
        markup.add(btn_vy)

        await bot.send_message(chat_id, greeting_text, reply_markup=markup)

        # Set user state to awaiting form choice
        user_states[user_id] = {'stage': 'awaiting_form_choice'}

        print(f"Greeting message with form choice sent to user {username} (ID: {user_id})")
    except Exception as e:
        print(f"Error sending greeting messages: {e}")


async def ask_for_user_name(bot, chat_id, user_id, username, form_of_address):
    """Ask user for their name based on form of address"""
    try:
        if form_of_address == 'ты':
            name_question = "Как тебя называть в диалоге? 📝 Напиши имя или ник."
        else:  # Вы
            name_question = "Как Вас называть в диалоге? 📝 Напишите имя или ник."

        # Add menu button for accessibility
        from universal_menu import get_menu_button
        markup = get_menu_button()

        await bot.send_message(chat_id, name_question, reply_markup=markup)

        # Set user state to awaiting name input
        user_states[user_id] = {
            'stage': 'awaiting_name',
            'form': form_of_address
        }

        print(f"Name question sent to user {username} with form: {form_of_address}")
    except Exception as e:
        print(f"Error asking for user name: {e}")


async def send_motivation_message(bot, chat_id, user_id, username, form_of_address, user_name):
    """Send motivation message with 'Ready to start?' button"""
    try:
        if form_of_address == 'ты':
            motivation_text = (
                f"Отлично, {user_name}! 🎯\n\n"
                "От того, насколько серьёзно ты подойдёшь к выполнению заданий, "
                "будет зависеть скорость достижения цели ⭐️\n\n"
                "Рекомендую уделить время себе и не отвлекаться до завершения упражнения — "
                "так глубже погрузишься и быстрее заметишь эффект.\n\n"
                "Готов(а) начать?"
            )
        else:  # Вы
            motivation_text = (
                f"Отлично, {user_name}! 🎯\n\n"
                "От того, насколько серьёзно Вы подойдёте к выполнению заданий, "
                "будет зависеть скорость достижения цели ⭐️\n\n"
                "Рекомендую уделить время себе и не отвлекаться до завершения упражнения — "
                "так глубже погрузитесь и быстрее заметите эффект.\n\n"
                "Готовы начать?"
            )

        # Create inline keyboard with button
        markup = types.InlineKeyboardMarkup()
        btn_ready = types.InlineKeyboardButton(
            "Да, поехали",
            callback_data="ready_to_start"
        )
        markup.add(btn_ready)

        await bot.send_message(chat_id, motivation_text, reply_markup=markup)

        # Set user state to ready to start
        user_states[user_id] = {
            'stage': 'ready_to_start',
            'form': form_of_address
        }

        print(f"Motivation message sent to user {username}")
    except Exception as e:
        print(f"Error sending motivation message: {e}")


async def handle_form_of_address_choice(bot, callback_query, user_id, username):
    """Handle form of address (ты/Вы) selection"""
    try:
        choice = callback_query.data

        if choice == "form_address:ty":
            form_of_address = 'ты'
        elif choice == "form_address:vy":
            form_of_address = 'Вы'
        else:
            response = "Неизвестный выбор. Пожалуйста, выберите один из предложенных вариантов."
            await bot.answer_callback_query(callback_query.id)
            await bot.send_message(callback_query.message.chat.id, response)
            return

        # Save form of address to Excel
        save_form_of_address_to_excel(user_id, username, form_of_address)

        # Answer callback and ask for name
        await bot.answer_callback_query(callback_query.id)
        print(f"DEBUG: About to ask for name for user {username}")
        await ask_for_user_name(bot, callback_query.message.chat.id, user_id, username, form_of_address)

        print(f"Form of address registered for user {username}: {form_of_address}")

    except Exception as e:
        print(f"Error handling form of address choice: {e}")


async def handle_name_input(bot, message, user_id, username):
    """Handle user name input and send motivation message"""
    try:
        user_name = message.text.strip()

        if not user_name or len(user_name) < 1:
            if user_id in user_states and user_states[user_id]['form'] == 'ты':
                error_msg = "Пожалуйста, введи своё имя или ник."
            else:
                error_msg = "Пожалуйста, введите своё имя или ник."
            from universal_menu import get_menu_button
            markup = get_menu_button()
            await bot.send_message(message.chat.id, error_msg, reply_markup=markup)
            return False

        # Get form of address from state
        form_of_address = user_states[user_id].get('form', 'ты')

        # Save user name to Excel
        save_user_name_to_excel(user_id, username, user_name)

        # Send motivation message
        await send_motivation_message(bot, message.chat.id, user_id, username, form_of_address, user_name)

        # Update state with user_name
        user_states[user_id] = {
            'stage': 'awaiting_motivation_response',
            'form': form_of_address,
            'user_name': user_name
        }

        print(f"User name saved and motivation message sent to {username}: {user_name}")
        return True

    except Exception as e:
        print(f"Error handling name input: {e}")
        return False


async def handle_ready_to_start(bot, callback_query, user_id, username):
    """Handle 'Ready to start?' button click - display how we work message and then protocol selection"""
    try:
        how_we_work_text = (
            "🎯 Как мы работаем:\n\n"
            "📌 Определим цель и повестку\n\n"
            "🔍 Подберём релевантные упражнения\n\n"
            "📊 Пройдём их пошагово с поддержкой\n\n"
            "💬 В конце — обратная связь, подытожим и (по желанию) включим напоминания для закрепления прогресса\n\n"
            "Мы вместе формулируем и проверяем гипотезы, поддерживаем обратную связь, суммируем услышанное; "
            "при твоём согласии можем вовлечь близких для поддержки."
        )

        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.message.chat.id, how_we_work_text)

        # Small delay for better UX
        await asyncio.sleep(1)

        # Start goal setting process
        import goal
        await goal.start_goal_setting(bot, callback_query.message.chat.id, user_id, username)

        # Update state
        if user_id in user_states:
            user_states[user_id]['stage'] = 'started'

        print(f"'How we work' message sent to user {username}, protocol selection initiated")

    except Exception as e:
        print(f"Error handling ready to start: {e}")


def reset_user_greeting_state(user_id):
    """Reset user greeting state when /start is called again"""
    if user_id in user_states:
        del user_states[user_id]
    print(f"User greeting state reset for user ID: {user_id}")
