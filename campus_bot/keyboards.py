from telegram import (InlineKeyboardButton,InlineKeyboardMarkup)

def menu_keyboard():

    keyboard = [
        [
            InlineKeyboardButton(
                "📖 Menu",
                callback_data="menu"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)

def login_keyboard():

    keyboard = [

        [
            InlineKeyboardButton(
                "🔐 Login",
                callback_data="login"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)

def dashboard_keyboard():

    keyboard = [

        [
            InlineKeyboardButton(
                "👤 Profile",
                callback_data="profile"
            )
        ],

        [
            InlineKeyboardButton(
                "📊 Attendance",
                callback_data="attendance"
            ),

            InlineKeyboardButton(
                "📅 Timetable",
                callback_data="timetable"
            )
        ],

        [
            InlineKeyboardButton(
                "📢 Notices",
                callback_data="notices"
            ),

            InlineKeyboardButton(
                "❓ Help",
                callback_data="help"
            )
        ],

        [
            InlineKeyboardButton(
                "🚪 Logout",
                callback_data="logout"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)