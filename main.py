import asyncio
import os
import io
from datetime import datetime
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import speech_recognition as sr
from pydub import AudioSegment
from dotenv import load_dotenv
from openpyxl import Workbook, load_workbook
from greeting import (
    send_greeting_messages,
    handle_name_input,
    handle_protocol_choice,
    reset_user_greeting_state,
    user_states,
    update_excel_headers
)
import protocol_known
import protocol_unknown
import universal_menu
from diary import init_diary_file, handle_diary_entry

# Load environment variables
load_dotenv()

# Initialize bot
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = AsyncTeleBot(BOT_TOKEN)

# Initialize speech recognizer
recognizer = sr.Recognizer()

# Excel file path
EXCEL_FILE = 'messages.xlsx'


def init_excel_file():
    """Initialize Excel file with headers if it doesn't exist"""
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
    else:
        # Update headers if file exists but doesn't have new columns
        update_excel_headers()


def save_message_to_excel(username, text, user_id=None, message_type='user_message'):
    """Save message to Excel file"""
    try:
        # Load existing workbook or create new one
        if os.path.exists(EXCEL_FILE):
            wb = load_workbook(EXCEL_FILE)
            ws = wb.active
        else:
            init_excel_file()
            wb = load_workbook(EXCEL_FILE)
            ws = wb.active

        # Find next empty row
        next_row = ws.max_row + 1

        # Add message data with new columns
        ws[f'A{next_row}'] = user_id
        ws[f'B{next_row}'] = username
        ws[f'D{next_row}'] = text
        ws[f'E{next_row}'] = message_type
        ws[f'G{next_row}'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Save workbook
        wb.save(EXCEL_FILE)
        print(f"Message saved to Excel: {username} - {text[:50]}...")
    except Exception as e:
        print(f"Error saving message to Excel: {e}")


async def process_voice_message(message):
    """Process voice message and return transcribed text"""
    try:
        # Get voice file
        file_info = await bot.get_file(message.voice.file_id)
        voice_file = await bot.download_file(file_info.file_path)

        # Convert voice to wav format
        audio = AudioSegment.from_ogg(io.BytesIO(voice_file))
        wav_data = io.BytesIO()
        audio.export(wav_data, format="wav")
        wav_data.seek(0)

        # Recognize speech
        with sr.AudioFile(wav_data) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language='ru-RU')
            return text
    except Exception as e:
        print(f"Error processing voice message: {e}")
        return ""


@bot.message_handler(commands=['start'])
async def start(message):
    """Handle /start command - initiate greeting sequence"""
    user_id = message.from_user.id
    username = message.from_user.username or 'Unknown'

    # Reset user state if they were in the middle of greeting process
    reset_user_greeting_state(user_id)

    # Send greeting messages
    await send_greeting_messages(bot, message.chat.id, user_id, username)


@bot.message_handler(commands=['menu'])
async def menu_command(message):
    """Handle /menu command - show main menu"""
    user_id = message.from_user.id
    username = message.from_user.username or 'Unknown'

    # Get user name from greeting state or use default
    from greeting import user_states
    user_name = 'Друг'
    if user_id in user_states and 'user_name' in user_states[user_id]:
        user_name = user_states[user_id]['user_name']

    # Show universal menu
    await universal_menu.show_main_menu(bot, message.chat.id, user_id, username, user_name)



@bot.message_handler(content_types=['text'])
async def handle_text(message):
    """Handle text messages"""
    text = message.text
    user_id = message.from_user.id
    username = message.from_user.username or 'Unknown'

    # Check if user is in greeting process (awaiting name input)
    if user_id in user_states and user_states[user_id].get('stage') == 'awaiting_name':
        # Handle name input for greeting
        success = await handle_name_input(bot, message, user_id, username)
        if success:
            return

    # Check if user is in diary entry mode
    from diary import user_diary_states
    if user_id in user_diary_states and user_diary_states[user_id].get('awaiting_entry'):
        # Handle diary entry
        await handle_diary_entry(bot, message)
        return

    # Regular message handling
    print(f"Text message from {username}: {text}")
    save_message_to_excel(username, text, user_id)
    await bot.send_message(message.chat.id, f"Получено текстовое сообщение: {text}")


@bot.message_handler(content_types=['voice'])
async def handle_voice(message):
    """Handle voice messages"""
    try:
        transcribed_text = await process_voice_message(message)
        username = message.from_user.username or 'Unknown'

        if transcribed_text:
            print(f"Voice message from {username} transcribed to: {transcribed_text}")
            save_message_to_excel(username, transcribed_text, message.from_user.id, 'voice_message')
            await bot.send_message(message.chat.id, f"Распознано голосовое сообщение: {transcribed_text}")
        else:
            print(f"Error transcribing voice message from {username}")
            await bot.send_message(message.chat.id, "Ошибка при распознавании голосового сообщения")
    except Exception as e:
        print(f"Error handling voice message: {e}")
        await bot.send_message(message.chat.id, "Произошла ошибка при обработке голосового сообщения")


@bot.callback_query_handler(func=lambda call: call.data.startswith('protocol_choice_'))
async def handle_protocol_selection(call):
    """Handle protocol choice button clicks"""
    user_id = call.from_user.id
    username = call.from_user.username or 'Unknown'

    # Process the protocol choice
    await handle_protocol_choice(bot, call, user_id, username)


@bot.callback_query_handler(func=lambda call: call.data.startswith('ps:'))
async def handle_specific_protocol_selection(call):
    """Handle specific protocol selection from the list"""
    user_id = call.from_user.id
    username = call.from_user.username or 'Unknown'

    # Extract protocol ID from callback data (ps:p1, ps:p2, etc.)
    protocol_id = call.data.replace('ps:', '')

    # Process the selected protocol
    await protocol_known.handle_protocol_selection(bot, call, protocol_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('ex_start:'))
async def handle_exercise_start(call):
    """Handle exercise start button click"""
    # Parse callback data: ex_start:protocol_id:exercise_index
    parts = call.data.split(':')
    if len(parts) == 3:
        protocol_id = parts[1]
        exercise_index = parts[2]
        await protocol_known.handle_exercise_start(bot, call, protocol_id, exercise_index)


@bot.callback_query_handler(func=lambda call: call.data.startswith('ex_skip:'))
async def handle_exercise_skip(call):
    """Handle exercise skip button click"""
    # Parse callback data: ex_skip:protocol_id:exercise_index
    parts = call.data.split(':')
    if len(parts) == 3:
        protocol_id = parts[1]
        exercise_index = parts[2]
        await protocol_known.handle_exercise_skip(bot, call, protocol_id, exercise_index)


async def main():
    """Main function to run the bot"""
    print("Starting bot in polling mode...")
    init_excel_file()
    init_diary_file()

    # Register handlers from protocol_unknown module
    protocol_unknown.register_handlers(bot)

    # Register universal menu handlers
    universal_menu.register_menu_handlers(bot)

    await bot.infinity_polling()


if __name__ == '__main__':
    asyncio.run(main())
