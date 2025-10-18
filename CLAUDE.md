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
