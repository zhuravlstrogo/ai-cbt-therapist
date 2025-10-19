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

### Important: Callback Timeout Prevention
All callback handlers in the change flow answer the Telegram callback query **immediately** with `show_alert=False`:

```python
# Answer callback IMMEDIATELY to avoid timeout
await bot.answer_callback_query(callback_query.id, show_alert=False)
```

This prevents "query is too old" errors by ensuring responses are sent within Telegram's 30-second timeout window, while processing continues asynchronously. Applied to:
- `handle_problem_selection()` (goal.py:312)
- `handle_problems_done()` (goal.py:350)
- `handle_problem_rating()` (goal.py:444)
- `handle_rating_back()` (goal.py:482)
- `handle_preview_change()` (goal.py:623)

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

## Mindfulness-Based Cognitive Therapy (MBCT) Practices

### Overview
Added full MBCT (Mindfulness-Based Cognitive Therapy) practices module accessible from the main menu button "🌙 Майндфулнесс-практика (MBCT)". Users can select from 6 guided mindfulness practices, complete them, provide feedback, and track their sessions.

### Available Practices

1. **3-минутная дыхательная пауза (Breathing Space)** 🌬️
   - Short "reboot": notice what is, focus on breathing, expand attention

2. **Сканирование тела (Body Scan)** 🧘
   - Attention travels from head to toes, notice sensations without judgment, develop grounding

3. **Осознанное дыхание (Mindful Breathing)** 🫁
   - Observe in-breath and out-breath, gently return attention (2–5 minutes)

4. **Осознанная ходьба/движение (Mindful Walking)** 🚶
   - Notice bodily sensations with each step, train presence in movement

5. **Мысли как мысли (Decentering)** ☁️
   - Perceive thoughts as mental events (clouds/leaves on water), don't merge with them

6. **Повернуться к трудности (Turning Toward Difficulty)** 💛
   - Gently meet unpleasant sensations/emotions, breathe nearby, expand attention

### Architecture

#### Core Files

**`mvst.py`** - Main mindfulness practice module (687 lines)
- Defines 6 MBCT practices with descriptions and emojis
- Manages user practice states during sessions
- Handles practice selection, input, and feedback

**Key Functions:**
- `show_mindfulness_practices()` - Display practice cards with selection buttons
- `handle_practice_select()` - Handle practice selection and show description
- `handle_practice_text_input()` - Process user input during practice
- `show_final_questions()` - Display 3 feedback questions after practice
- `show_next_practice_options()` - Show remaining practices or return to menu
- `save_practice_to_excel()` - Store practice data in mvst.xlsx

#### Data Storage

**`mvst.xlsx`** - Excel file tracking practice sessions with columns:
- User ID, Username, Practice Name, Practice Type
- Practice Start Time, User Input During Practice
- What Was Noticed, What Was Useful, What Was Difficult
- Date/Time

#### Integration Points

**`universal_menu.py`** (Line 258-261)
- Updated mindfulness button handler to call `show_mindfulness_practices()`
- Previously showed "coming soon" placeholder

**`main.py`**
- Line 203-211: Added text message handler for mindfulness practice input
- Line 486-495: Register MVST handlers on bot startup
- Initializes mvst.xlsx on first run

### User Flow

```
User clicks "🌙 Майндфулнесс-практика (MBCT)" in menu
    ↓
[Show all 6 practice cards with descriptions and selection buttons]
    ↓
User selects a practice → "Начать: [Practice Name]"
    ↓
[Display practice description with emoji and full details]
    ↓
User can enter notes during practice (optional)
    ↓
[Show 3 sequential feedback questions:]
  1. "Что ты заметил(а) в ходе практики?" (What did you notice?)
  2. "Что было полезно?" (What was useful?)
  3. "Что вызвало сложности?" (What was difficult?)
    ↓
User confirms each answer (preview: "📝 Вот что ты написал(а)...")
    ↓
[Show completion button: "✅ Отметить как завершённое"]
    ↓
[Show remaining practices or "All completed!" message]
    ↓
User selects next practice OR returns to menu via "📍 Главное меню"
```

### Key Features

**Practice Selection**
- All 6 practices shown as individual cards with emoji, name, and full description
- Each practice has a dedicated "Начать: [Name]" button
- Menu button always available for navigation

**User Input**
- Optional text input during practice (store in mvst.xlsx column F)
- Optional text input for each feedback question
- Preview system: "📝 Вот что ты написал(а):" with Edit/Confirm buttons
- Lenient validation: empty answers allowed for mindfulness practices

**Session Tracking**
- Practice selection logged with timestamp (column E)
- All feedback answers saved to Excel
- Completed practices tracked in session state
- Option to do multiple practices in one session

**Navigation**
- Menu button (📱 Главное меню) accessible from any practice screen
- After practice: show next practices with buttons, or main menu button
- Track completed practices to avoid repetition in same session

### State Management

**`user_mvst_states[user_id]`** tracks:
- `practices` - List of all 6 practices (dict)
- `selected_practice` - Current practice being done
- `completed_practices` - List of practice IDs completed in session
- `username` - User identifier for Excel logging
- `awaiting_practice_input` - Flag for text input during practice
- `awaiting_final_answer` - Flag for feedback question response
- `pending_practice_input` - Temporary storage for user input
- `pending_final_answer` - Temporary storage for answer preview
- `final_answers` - Dict storing 3 feedback answers (0=noticed, 1=useful, 2=difficult)
- `current_final_question` - Index of current question (0-2)
- `current_step` - Flow state (selection, practice, questions, completion)

### Callback Handlers

All callback data formats:
- `mvst_select:{practice_id}` - Select practice (IDs 1-6)
- `mvst_input_confirm:{action}` - Confirm practice input (yes/edit)
- `mvst_answer_confirm:{action}` - Confirm feedback answer (yes/edit)
- `mvst_mark_complete` - Mark practice completed

All callbacks registered in `register_mvst_handlers()` function

### Important: Callback Timeout Prevention
All callback handlers answer the Telegram callback query **immediately**:
```python
await bot.answer_callback_query(callback_query.id, "message", show_alert=False)
```
This prevents "query is too old" errors within Telegram's 30-second timeout window.

### Excel Logging

Practice data persists in `mvst.xlsx` with automatic file initialization:
- Headers created on first run by `init_mvst_excel()`
- Each practice session creates new row
- User input and feedback answers added to same row
- Timestamps recorded for practice start and session completion
