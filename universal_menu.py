# -*- coding: utf-8 -*-
"""
Universal menu module accessible from any point in the bot
Provides quick access to: switch protocol, emotion diary, help and hotlines
"""

from telebot import types


HELP_TEXT = (
    "Мне важно, чтобы ты был(а) в безопасности.\n"
    "Если тебе сейчас очень тяжело, пожалуйста, обратись за живой поддержкой 💛\n\n"
    "🆘 Психологическая помощь и горячие линии\n\n"
    "Помощь психолога: https://napopravku.ru/moskva/uslugi/online-konsultaciya-psihologa/\n\n"
    "Или просто напиши близкому человеку прямо сейчас 💙"
)


async def show_main_menu(bot, chat_id, user_id, username, user_name):
    """
    Display the universal main menu with all options

    Args:
        bot: Telegram bot instance
        chat_id: Chat ID
        user_id: User ID
        username: Username
        user_name: User's name
    """
    try:
        text = "🧭 Главное меню"

        markup = types.InlineKeyboardMarkup()

        # Change protocol button
        btn_protocol = types.InlineKeyboardButton(
            "🧭 Сменить протокол",
            callback_data="menu:switch_protocol"
        )

        # Emotion diary button
        btn_diary = types.InlineKeyboardButton(
            "💬 Дневник эмоций и мыслей",
            callback_data="menu:diary"
        )

        # Help and hotlines button
        btn_help = types.InlineKeyboardButton(
            "🆘 Помощь и горячие линии",
            callback_data="menu:help"
        )

        markup.row(btn_protocol)
        markup.row(btn_diary)
        markup.row(btn_help)

        await bot.send_message(chat_id, text, reply_markup=markup)

    except Exception as e:
        print(f"Error showing main menu: {e}")


async def handle_menu_callback(bot, callback_query, menu_action):
    """
    Handle menu button presses

    Args:
        bot: Telegram bot instance
        callback_query: Callback query from button press
        menu_action: Action selected (switch_protocol, diary, help, show)
    """
    try:
        user_id = callback_query.from_user.id
        username = callback_query.from_user.username or 'Unknown'
        chat_id = callback_query.message.chat.id

        await bot.answer_callback_query(callback_query.id)

        if menu_action == 'show':
            # Just show the menu when menu button is clicked
            from greeting import user_states
            user_name = 'Друг'
            if user_id in user_states and 'user_name' in user_states[user_id]:
                user_name = user_states[user_id]['user_name']
            await show_main_menu(bot, chat_id, user_id, username, user_name)

        elif menu_action == 'switch_protocol':
            # Show protocol choice buttons (same as in greeting)
            text = "Ты уже знаешь, какой протокол тебе нужен?"

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

            # Add back to menu button
            btn_back = types.InlineKeyboardButton(
                "🔙 Назад в меню",
                callback_data="menu:show"
            )
            markup.add(btn_back)

            await bot.send_message(chat_id, text, reply_markup=markup)

        elif menu_action == 'diary':
            # Import greeting to get user_name
            from greeting import user_states
            user_name = 'User'
            if user_id in user_states:
                user_name = user_states[user_id].get('user_name', 'User')

            # Import and call diary prompt
            from diary import show_diary_prompt
            await show_diary_prompt(bot, chat_id, user_id, username, user_name)

        elif menu_action == 'help':
            # Create markup with back to menu button
            markup = types.InlineKeyboardMarkup()
            btn_back = types.InlineKeyboardButton(
                "📱 Главное меню",
                callback_data="menu:show"
            )
            markup.add(btn_back)

            await bot.send_message(chat_id, HELP_TEXT, reply_markup=markup)

    except Exception as e:
        print(f"Error handling menu callback: {e}")
        await bot.answer_callback_query(callback_query.id, "Ошибка при обработке команды", show_alert=True)


def register_menu_handlers(bot):
    """
    Register universal menu handlers

    Args:
        bot: Telegram bot instance
    """
    @bot.callback_query_handler(func=lambda call: call.data.startswith('menu:'))
    async def menu_callback_handler(callback_query):
        """Handle menu button clicks"""
        action = callback_query.data.split(':')[1]
        await handle_menu_callback(bot, callback_query, action)
