# -*- coding: utf-8 -*-
"""
Universal menu module accessible from any point in the bot
Provides quick access to: switch protocol, emotion diary, help and hotlines
"""

from telebot import types


def get_menu_button():
    """
    Returns inline keyboard markup with menu button
    Used to provide menu access from any point in the bot
    """
    markup = types.InlineKeyboardMarkup()
    btn_menu = types.InlineKeyboardButton(
        "📱 Главное меню",
        callback_data="menu:show"
    )
    markup.add(btn_menu)
    return markup


def get_back_and_menu_buttons():
    """
    Returns inline keyboard markup with back and menu buttons
    Used in multi-step flows to provide navigation options
    """
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton(
        "⬅️ Назад",
        callback_data="go_back"
    )
    btn_menu = types.InlineKeyboardButton(
        "📱 Главное меню",
        callback_data="menu:show"
    )
    markup.row(btn_back, btn_menu)
    return markup


HELP_TEXT = (
    "Мне важно, чтобы ты был(а) в безопасности. 💛\n"
    "Если тебе сейчас очень тяжело, пожалуйста, обратись за живой поддержкой\n\n"
    "🆘 Психологическая помощь и горячие линии:\n\n"
    "☎️ Единый телефон доверия психологической помощи для взрослых и детей:\n"
    "8 (800) 100-49-94 (круглосуточно)\n\n"
    "☎️ Бесплатная кризисная линия доверия по России:\n"
    "8 (800) 333-44-34\n\n"
    "☎️ Бесплатная кризисная линия доверия по Москве:\n"
    "8 (495) 988-44-34\n\n"
    "☎️ Горячая линия Центра экстренной психологической помощи МЧС России:\n"
    "8 (495) 989-50-50\n"
    "psi.mchs.gov.ru\n\n"
    "☎️ Горячая линия психологической поддержки Благотворительного фонда «Просто люди»:\n"
    "8 (495) 025-15-35\n\n"
    "☎️ Московская служба психологической помощи населению:\n"
    "051 с городского\n"
    "8 (495) 051 с мобильного\n\n"
    "☎️ Экстренная медико-психологическая помощь в кризисных ситуациях города Москвы:\n"
    "8 (499) 791-20-50\n\n"
    "Или просто напиши близкому человеку прямо сейчас 💙"
)


async def show_change_options(bot, chat_id, user_id, username):
    """
    Show options to change goal and/or problems
    Called from 'Изменить цель/проблемы' menu button
    """
    try:
        text = "Что хочешь изменить?"

        markup = types.InlineKeyboardMarkup()

        btn_goal = types.InlineKeyboardButton(
            "🎯 Цель терапии",
            callback_data="change:goal_only"
        )
        btn_problems = types.InlineKeyboardButton(
            "🧭 Трудности",
            callback_data="change:problems_only"
        )
        btn_back = types.InlineKeyboardButton(
            "↩️ Вернуться в меню",
            callback_data="menu:show"
        )

        markup.add(btn_goal)
        markup.add(btn_problems)
        markup.add(btn_back)

        await bot.send_message(chat_id, text, reply_markup=markup)

    except Exception as e:
        print(f"Error showing change options: {e}")


async def show_main_menu(bot, chat_id, user_id, username, user_name, form_of_address='ты'):
    """
    Display the universal main menu with all options

    Args:
        bot: Telegram bot instance
        chat_id: Chat ID
        user_id: User ID
        username: Username
        user_name: User's name
        form_of_address: Form of address ('ты' or 'Вы')
    """
    try:
        text = "🧭 Главное меню"

        markup = types.InlineKeyboardMarkup()

        # Select exercise button (based on user problems)
        btn_exercise = types.InlineKeyboardButton(
            "🧭 Выбрать упражнение",
            callback_data="menu:select_exercise"
        )

        # Change goal/problems button
        btn_goal = types.InlineKeyboardButton(
            "🎯 Изменить цель/проблемы",
            callback_data="menu:set_goal"
        )

        # My progress button
        btn_progress = types.InlineKeyboardButton(
            "📖 Мой прогресс",
            callback_data="menu:my_progress"
        )

        # Mindfulness practice button
        btn_mindfulness = types.InlineKeyboardButton(
            "🌙 Майндфулнесс-практика (MBCT)",
            callback_data="menu:mindfulness"
        )

        # Emotion diary button
        btn_diary = types.InlineKeyboardButton(
            "💬 Дневник эмоций и мыслей",
            callback_data="menu:diary"
        )

        # Assess progress button
        btn_assess = types.InlineKeyboardButton(
            "📈 Оценить прогресс",
            callback_data="menu:assess_progress"
        )

        # Help and hotlines button
        btn_help = types.InlineKeyboardButton(
            "🆘 Помощь и горячие линии",
            callback_data="menu:help"
        )

        # Technical support button
        btn_support = types.InlineKeyboardButton(
            "🚧 Обращение в техподдержку",
            callback_data="menu:technical_support"
        )

        markup.row(btn_exercise)
        markup.row(btn_goal)
        markup.row(btn_progress)
        markup.row(btn_mindfulness)
        markup.row(btn_diary)
        markup.row(btn_assess)
        markup.row(btn_help)
        markup.row(btn_support)

        await bot.send_message(chat_id, text, reply_markup=markup)

    except Exception as e:
        print(f"Error showing main menu: {e}")


async def handle_menu_callback(bot, callback_query, menu_action):
    """
    Handle menu button presses

    Args:
        bot: Telegram bot instance
        callback_query: Callback query from button press
        menu_action: Action selected (select_exercise, set_goal, diary, help, show, etc.)
    """
    try:
        user_id = callback_query.from_user.id
        username = callback_query.from_user.username or 'Unknown'
        chat_id = callback_query.message.chat.id

        await bot.answer_callback_query(callback_query.id)

        if menu_action == 'show':
            # Just show the menu when menu button is clicked
            from greeting import user_states

            # Clear exercise state if user was in the middle of an exercise
            from exercise import user_exercise_states
            if user_id in user_exercise_states:
                del user_exercise_states[user_id]

            user_name = 'Друг'
            form_of_address = 'ты'
            if user_id in user_states and 'user_name' in user_states[user_id]:
                user_name = user_states[user_id]['user_name']
                form_of_address = user_states[user_id].get('form', 'ты')
            await show_main_menu(bot, chat_id, user_id, username, user_name, form_of_address)

        elif menu_action == 'select_exercise':
            # Check if user has problems defined
            from greeting import user_states
            from goal import user_goal_states

            # Check both states for existing problems
            user_problems = None
            problem_ratings = {}

            # First check persistent user_states
            if user_id in user_states:
                user_problems = user_states[user_id].get('problems')
                problem_ratings = user_states[user_id].get('problem_ratings', {})

            # If not found, check temporary goal states
            if not user_problems and user_id in user_goal_states:
                user_problems = user_goal_states[user_id].get('problems')
                problem_ratings = user_goal_states[user_id].get('problem_ratings', {})

            if user_problems:
                # User has problems - filter exercises by their problems
                from exercise import show_exercise_recommendations
                await show_exercise_recommendations(bot, chat_id, user_id, username, problem_ratings)
            else:
                # No problems defined - ask user to select problems only (not full goal setting)
                text = "Чтобы подобрать упражнения, мне нужно знать, над чем ты хочешь работать."
                markup = types.InlineKeyboardMarkup()
                btn_back = types.InlineKeyboardButton(
                    "🔙 Назад в меню",
                    callback_data="menu:show"
                )
                markup.add(btn_back)
                await bot.send_message(chat_id, text, reply_markup=markup)

                # Start goal setting process
                from goal import start_goal_setting
                await start_goal_setting(bot, chat_id, user_id, username)

        elif menu_action == 'set_goal':
            # Show change options dialog
            await show_change_options(bot, chat_id, user_id, username)

        elif menu_action == 'my_progress':
            # Show user progress
            markup = types.InlineKeyboardMarkup()
            btn_back = types.InlineKeyboardButton(
                "🔙 Назад в меню",
                callback_data="menu:show"
            )
            markup.add(btn_back)

            progress_text = "📖 Мой прогресс\n\nЭта функция будет вскоре доступна."
            await bot.send_message(chat_id, progress_text, reply_markup=markup)

        elif menu_action == 'mindfulness':
            # Show mindfulness practice
            markup = types.InlineKeyboardMarkup()
            btn_back = types.InlineKeyboardButton(
                "🔙 Назад в меню",
                callback_data="menu:show"
            )
            markup.add(btn_back)

            mindfulness_text = "🌙 Майндфулнесс-практика (MBCT)\n\nЭта функция будет вскоре доступна."
            await bot.send_message(chat_id, mindfulness_text, reply_markup=markup)

        elif menu_action == 'diary':
            # Import greeting to get user_name
            from greeting import user_states
            user_name = 'User'
            if user_id in user_states:
                user_name = user_states[user_id].get('user_name', 'User')

            # Import and call diary prompt
            from diary import show_diary_prompt
            await show_diary_prompt(bot, chat_id, user_id, username, user_name)

        elif menu_action == 'assess_progress':
            # Show assess progress
            markup = types.InlineKeyboardMarkup()
            btn_back = types.InlineKeyboardButton(
                "🔙 Назад в меню",
                callback_data="menu:show"
            )
            markup.add(btn_back)

            assess_text = "📈 Оценить прогресс\n\nЭта функция будет вскоре доступна."
            await bot.send_message(chat_id, assess_text, reply_markup=markup)

        elif menu_action == 'technical_support':
            # Show technical support contact
            markup = types.InlineKeyboardMarkup()
            btn_contact = types.InlineKeyboardButton(
                "👤 @zhuravlstrogo",
                url="https://t.me/zhuravlstrogo"
            )
            btn_back = types.InlineKeyboardButton(
                "🔙 Назад в меню",
                callback_data="menu:show"
            )
            markup.add(btn_contact)
            markup.add(btn_back)

            support_text = "🚧 Обращение в техподдержку\n\nСвяжись с нами по контакту ниже:"
            await bot.send_message(chat_id, support_text, reply_markup=markup)

        elif menu_action == 'change_goal':
            # Start goal setting to change goal only
            from goal import start_goal_setting
            from greeting import user_states

            # Clear old goal to force asking for new one
            if user_id in user_states and 'goal' in user_states[user_id]:
                del user_states[user_id]['goal']

            await start_goal_setting(bot, chat_id, user_id, username, skip_goal=False)

        elif menu_action == 'change_problems':
            # Start goal setting to change problems only (skip goal)
            from goal import start_goal_setting
            await start_goal_setting(bot, chat_id, user_id, username, skip_goal=True)

        elif menu_action == 'change_all':
            # Start goal setting from beginning
            from goal import start_goal_setting
            from greeting import user_states

            # Clear all saved data
            if user_id in user_states:
                if 'goal' in user_states[user_id]:
                    del user_states[user_id]['goal']
                if 'problems' in user_states[user_id]:
                    del user_states[user_id]['problems']
                if 'problem_ratings' in user_states[user_id]:
                    del user_states[user_id]['problem_ratings']

            await start_goal_setting(bot, chat_id, user_id, username, skip_goal=False)

        elif menu_action == 'help':
            # Create markup with back to menu button
            markup = types.InlineKeyboardMarkup()
            btn_back = types.InlineKeyboardButton(
                "🔙 Назад в меню",
                callback_data="menu:show"
            )
            markup.add(btn_back)

            await bot.send_message(chat_id, HELP_TEXT, reply_markup=markup)

    except Exception as e:
        print(f"Error handling menu callback: {e}")
        await bot.answer_callback_query(callback_query.id, "Ошибка при обработке команды", show_alert=True)


async def handle_change_callback(bot, callback_query, action):
    """
    Handle change goal/problems callbacks

    Args:
        bot: Telegram bot instance
        callback_query: Callback query from button press
        action: Action type (goal_only or problems_only)
    """
    try:
        user_id = callback_query.from_user.id
        username = callback_query.from_user.username or 'Unknown'
        chat_id = callback_query.message.chat.id

        await bot.answer_callback_query(callback_query.id)

        if action == 'goal_only':
            # Change only goal - skip to step 1 with existing goal cleared
            from goal import start_goal_setting
            await start_goal_setting(bot, chat_id, user_id, username, skip_goal=False, force_change_goal=True)

        elif action == 'problems_only':
            # Change only problems - skip to problem selection (step 2)
            from goal import start_goal_setting
            await start_goal_setting(bot, chat_id, user_id, username, skip_goal=True, force_change_problems=True)

    except Exception as e:
        print(f"Error handling change callback: {e}")
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

    @bot.callback_query_handler(func=lambda call: call.data.startswith('change:'))
    async def change_callback_handler(callback_query):
        """Handle change goal/problems buttons"""
        action = callback_query.data.split(':')[1]
        await handle_change_callback(bot, callback_query, action)
