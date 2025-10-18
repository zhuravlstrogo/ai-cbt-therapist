# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Telegram Message Handler** - A lightweight bot that captures text and voice messages, converts voice to text via Google Speech Recognition API (Russian language), and echoes the results back to users.

## Quick Start

### Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies (macOS)
brew install ffmpeg portaudio

# Ubuntu/Debian
sudo apt-get install ffmpeg portaudio19-dev

# Create .env file with:
BOT_TOKEN=your_telegram_bot_token
```

### Run Application
```bash
python main.py
```

The bot starts in polling mode and listens for incoming messages on Telegram.

## Architecture

### Project Structure
- **main.py** - Single file containing all bot logic: initialization, message handlers, and voice transcription
- **requirements.txt** - Python dependencies (minimal set: 4 packages)
- **.env** - Configuration file with BOT_TOKEN (not in repo)

### Technology Stack
- **Telegram**: pyTelegramBotAPI (async)
- **Speech Recognition**: Google Speech Recognition API via SpeechRecognition library (Russian language: `ru-RU`)
- **Audio Processing**: pydub for OGG to WAV conversion
- **Environment**: python-dotenv for configuration
- **Concurrency**: asyncio for full async/await implementation

### Core Processing Pipeline

```
User sends message
    ↓
[Message type: text or voice?]
    ↓
Text:  Extract and echo back

Voice: Download OGG → Convert to WAV → Google Speech API (ru-RU) → Echo transcribed text
    ↓
Send response to user
```

### Key Functions

**`process_voice_message(message)`** (main.py:21-41)
- Downloads voice file from Telegram servers
- Converts OGG format to WAV using pydub
- Calls Google Speech Recognition API with Russian language
- Returns transcribed text or empty string on error

**Message Handlers**
- `handle_text()` (main.py:44-51) - Captures text messages, logs to console, sends echo
- `handle_voice()` (main.py:54-69) - Captures voice messages, calls `process_voice_message()`, sends transcribed text
- `start()` (main.py:72-79) - `/start` command handler that displays Chat ID and instructions

**`main()`** (main.py:82-85)
- Entry point that starts the bot in polling mode
- Uses `bot.infinity_polling()` to listen for messages indefinitely

## Dependencies

All 4 dependencies are required and minimal:
- `pyTelegramBotAPI` - Telegram Bot API wrapper (async support)
- `python-dotenv` - Load BOT_TOKEN from .env file
- `SpeechRecognition` - Google Speech API client
- `pydub` - Audio format conversion (requires FFmpeg and PortAudio system packages)

## Change Goal/Problems Flow

### Overview
Users can modify their therapy goal and/or problems from the main menu button "🎯 Изменить цель/проблемы". This flow allows selective updates with validation and recommendations refresh.

### Architecture

#### Menu Entry Point (universal_menu.py:66-96)
**`show_change_options()`** - Displays change menu with options:
- 🎯 Цель терапии (Change goal only)
- 🧭 Трудности (Change problems only)
- ↩️ Вернуться в меню (Return to menu)

#### Callback Handler (universal_menu.py:365-393)
**`handle_change_callback()`** - Routes to goal setting with change flags:
- `change:goal_only` → `start_goal_setting(..., force_change_goal=True)`
- `change:problems_only` → `start_goal_setting(..., skip_goal=True, force_change_problems=True)`

### Goal Setting Changes (goal.py:77-153)

**`start_goal_setting()` - Updated Parameters:**
- `force_change_goal=False` - Force changing goal (clear existing, ask for new)
- `force_change_problems=False` - Force changing problems (clear existing)

**State Management:**
- `is_changing` flag set when `force_change_goal` or `force_change_problems` enabled
- Preserves existing data unless explicitly forcing change
- Initializes to correct step based on change type:
  - Force goal: Step 1 (ask for goal)
  - Force problems: Step 2 (select problems)

### Workflow: Change Goal Only
1. User clicks "🎯 Цель терапии"
2. `start_goal_setting(..., force_change_goal=True)` called
3. Step 1: Bot asks "Какую цель терапии ты перед собой ставишь?"
4. User enters new goal text
5. Preview shown: "📝 Твоя цель: {goal_text}"
6. Options: ✅ Подтвердить / ✏️ Изменить
7. **If confirmed → Skip to problem rating (Step 3)** with existing problems
8. After rating: Final preview and **Show exercise recommendations**

### Workflow: Change Problems Only
1. User clicks "🧭 Трудности"
2. `start_goal_setting(..., skip_goal=True, force_change_problems=True)` called
3. Step 2: Show full problem list (ALL problems, not just existing ones)
4. User selects problems (toggle multiple)
5. Click ➡️ Продолжить
6. Step 3: Rate each selected problem (0-3 scale)
7. Final preview with all ratings
8. After confirmation: **Show exercise recommendations**

### Key Implementation Details

**Problem Rating Cleanup** (goal.py:375-379)
- When transitioning from Step 2 to Step 3:
  - Remove ratings for deselected problems
  - Preserve ratings for problems kept from previous selection
  - Ensures clean state for change operation

**Clear Ratings on Change** (goal.py:253-257)
- When entering problem selection in change mode:
  - Check `is_changing` flag
  - Clear all problem ratings
  - Forces re-rating of all problems during this change operation

**Final Preview Improvement** (goal.py:512-560)
- Shows "Проблемы не выбраны" if problems list is empty
- Button text: ✅ Подтвердить (instead of "Да, верно")

### State Persistence Flow
```
User Goal/Problem Change
    ↓
show_change_options() → Present change menu
    ↓
[User selects: Goal or Problems]
    ↓
handle_change_callback() → Call start_goal_setting with flags
    ↓
start_goal_setting(force_change_goal/force_change_problems=True)
    ↓
[User makes changes through normal goal flow]
    ↓
handle_preview_confirm(action="yes")
    ↓
[Save to user_states in greeting.py]
    ↓
show_exercise_recommendations() → Display updated exercises
```

### Registration
Handlers registered in `main.py:420`:
```python
universal_menu.register_menu_handlers(bot)
```

This automatically registers both:
- `menu:` callback handler (existing menu callbacks)
- `change:` callback handler (new change goal/problems callbacks)

## Exercise Completion Flow

### Overview
After a user completes all steps and answers the final questions for an exercise, the following sequence occurs:

1. **Final Questions** (exercise.py:624-652)
   - Three questions asked sequentially:
     - "Какой инсайт ты получил?" (What insight did you get?)
     - "Что было полезно?" (What was useful?)
     - "Что вызвало трудность?" (What was difficult?)

2. **Completion Marker** (exercise.py:665-692)
   - After all questions answered, user sees: "Отлично! Ты ответил(а) на все вопросы."
   - Button "✅ Отметить как завершённое" appears
   - Callback: `ex_mark_complete`

3. **Exercise Finish** (exercise.py:695-722)
   - Saves all final answers to exercises.xlsx
   - Shows completion message: "Спасибо! Я записал(а) твой опыт. Это отличная работа! 💪"
   - Calls `show_next_exercise_options()`

4. **Next Exercise Options** (exercise.py:725-767)
   - Detects if more exercises remain in the recommendation list
   - Shows buttons:
     - "➡️ Следующее упражнение" (if more exercises available)
     - "📍 Главное меню" (always shown)
   - State persists for seamless transition to next exercise

### Key Functions

**`show_exercise_completion_options()`** (exercise.py:665-692)
- Displays completion message and mark-complete button
- Triggered after final question answered

**`handle_mark_exercise_complete()`** (exercise.py:1162-1182)
- Callback handler for "✅ Отметить как завершённое" button
- Calls `finish_exercise()` to save and proceed

**`finish_exercise()`** (exercise.py:695-722)
- Saves final answers to Excel
- Shows completion confirmation
- Transitions to next exercise options

**`show_next_exercise_options()`** (exercise.py:725-767)
- Determines next exercise in list
- Displays appropriate buttons based on remaining exercises
- Preserves state for next exercise selection

**`handle_exercise_select()`** (exercise.py:455-508)
- Resets execution state when new exercise selected
- Clears: steps, current_step_idx, final_answers, awaiting flags
- Ensures clean state for next exercise

### State Management

- Exercise state stored in `user_exercise_states[user_id]`
- State cleared when:
  - User returns to main menu (`universal_menu.py:91-94`)
  - User selects new exercise after completion
- State preserved when transitioning to next exercise for seamless UX

## How to Extend

### Adding a New Message Type Handler
1. Add handler function with decorator: `@bot.message_handler(content_types=['type'])`
2. Process the message (use `await` for async Telegram API calls)
3. Send response via `await bot.send_message(message.chat.id, response_text)`

Example:
```python
@bot.message_handler(content_types=['photo'])
async def handle_photo(message):
    """Handle photo messages"""
    # Your code here
    await bot.send_message(message.chat.id, "Photo received")
```

### Modifying Voice Recognition Language
- In `process_voice_message()` line 37, change `language='ru-RU'` to desired language code (e.g., `'en-US'`)
- Verify Google Speech API supports the language

### Adding Console Logging
- Current implementation uses `print()` statements
- Messages are logged when received (line 50, 62)
- Consider replacing with proper logging module for production

## Known Limitations

- Depends on Google Speech Recognition API (internet connection required)
- No database persistence (messages not stored)
- No error recovery - failures logged to console only
- Voice recognition limited to Google API capabilities and language support
- No rate limiting or message queuing
- FFmpeg and PortAudio must be installed as system packages

## Troubleshooting

**Voice Recognition Fails**
- Ensure FFmpeg is installed: `ffmpeg -version`
- Ensure PortAudio is installed
- Check internet connection (Google API requires it)
- Verify audio file is valid OGG format from Telegram

**Bot Doesn't Respond**
- Check BOT_TOKEN in .env is valid
- Verify bot is running: check console for "Starting bot in polling mode..."
- Look for error messages in console output

**Import Errors**
- Run `pip install -r requirements.txt`
- Verify Python 3.7+ installed (asyncio with full async/await support)
