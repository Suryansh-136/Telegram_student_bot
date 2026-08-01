from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.ext import CallbackQueryHandler
from keyboards import (login_keyboard,dashboard_keyboard,menu_keyboard,back_keyboard)
import requests
import os
import django
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "campus_bot.settings"
)

django.setup()
from django.contrib.auth.models import User
from Gakusei.models import StudentProfile, TelegramUser, Attendance, Notice, Timetable
from asgiref.sync import sync_to_async
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


USERNAME, PASSWORD = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        """
🎓 Welcome to Campus Buddy

Use menu to see available commands.
        """,
     reply_markup = menu_keyboard()
    )

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    try:

        telegram_user = await sync_to_async(

            TelegramUser.objects.select_related(

                "student",
                "student__user"
            ).get
    )(
        telegram_id=update.effective_user.id
    )

        student = telegram_user.student

        message = (
            f"👤 Name: {student.user.first_name} {student.user.last_name}\n"
            f"🎓 Enrollment: {student.enrollment_no}\n"
            f"🏫 Branch: {student.branch}\n"
            f"📚 Semester: {student.semester}"
        )
           
        if query:
            await query.edit_message_text(
                text = message,
                reply_markup = back_keyboard()
        )
        else:
            await update.message.reply_text(
                message,
                reply_markup = back_keyboard()
        )

    except TelegramUser.DoesNotExist:
        
        if query:
            await query.edit_message_text(
                text = "Please Login first using /login",
                reply_markup = login_keyboard()
            )

        else:
            await update.message.reply_text(
                "Please Login first using /login",
                reply_markup = login_keyboard()
            )

       
async def attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    try:

        telegram_user = await sync_to_async(
            TelegramUser.objects.select_related(
                "student"
            ).get
        )(
            telegram_id=update.effective_user.id
        )

        attendance_records = await sync_to_async(
            list
        )(
            Attendance.objects.filter(
                student=telegram_user.student
            )
        )

        if not attendance_records:
            if query:
                await query.edit_message_text(
                    text="No records found",
                    reply_markup=back_keyboard()
                )
            
            else:
                await update.message.reply_text(
                    "No records found",
                    reply_markup=back_keyboard()
                )
           
            return

        message = "📊 Attendance\n\n"

        for record in attendance_records:

            percentage = record.attendance_percentage()

            message += (
                f"📘 {record.subject_name}\n"
                f"{record.attended_classes}/{record.total_classes}"
                f" ({percentage}%)\n\n"
            )

        if query:
            await query.edit_message_text(
                text = message,
                reply_markup = back_keyboard()
            )

        else:
            await update.message.reply_text(
                message,
                reply_markup = back_keyboard()
            )

    except TelegramUser.DoesNotExist:

        if query:     
            await query.edit_message_text(
            text = "Please login first using /login",
            reply_markup = login_keyboard()
        )

        else:
            await update.message.reply_text(
                "Please Login first using /login",
                reply_markup = login_keyboard()
            )

async def notices(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.callback_query:
        reply = update.callback_query.message

    else:
        reply = update.message
        
    notices_list = await sync_to_async(list)(
        Notice.objects.order_by(
            "-created_at"
        )[:5]
    )

    if not notices_list:

        await reply.reply_text(
            "No notices available.",
            reply_markup = back_keyboard()
            )

        return
    message = "📢 Latest Notices\n\n"
        
    for notice in notices_list:

        message += (
            f"📌{notice.title}\n"
            f"{notice.content}\n\n"
            )
    await reply.reply_text(message,
    reply_markup = back_keyboard())


async def timetable(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.callback_query:
        reply = update.callback_query.message

    else:
        reply = update.message

    try:

        telegram_user = await sync_to_async(
            TelegramUser.objects.select_related(
            "student"
        ).get
    )(
        telegram_id=update.effective_user.id
    )

        student = telegram_user.student

        timetable_records = await sync_to_async(list)(
        Timetable.objects.filter(
            semester=student.semester
        ).order_by(
            "day",
            "start_time"
        )
    )

        if not timetable_records:
            await reply.reply_text(
            "No timetable found.",
            reply_markup = back_keyboard()
        )
            return

        message = "📅 Timetable\n\n"

        current_day = ""

        for record in timetable_records:
            if current_day != record.day:
                current_day = record.day
                message += f"\n📌 {current_day}\n"

            message += (
                f"{record.start_time.strftime('%H:%M')} - "
                f"{record.end_time.strftime('%H:%M')} | "
                f"{record.subject_name}\n"
            )

        await reply.reply_text(message,
        reply_markup = back_keyboard())

    except TelegramUser.DoesNotExist:

        await reply.reply_text(
            "Please login first using /login"
        )    



async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        reply = update.callback_query.message
    else: 
        reply = update.message

    await reply.reply_text(
        "Enter username:"
    )
    return USERNAME

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["username"] = update.message.text
    
    if update.callback_query:
        reply = update.callback_query.message

    else:
        reply = update.message

    await reply.reply_text(
        "Enter password:"
    )
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["password"] = update.message.text

    username = context.user_data["username"]
    password = context.user_data["password"]

    response = requests.post(
        "http://127.0.0.1:8000/token-login/",
        json={
            "username": username,
            "password": password
        }
    )

    if response.status_code == 200:

        user = await sync_to_async(
            User.objects.get
        )(username=username)

        student = await sync_to_async(
            StudentProfile.objects.get
        )(user=user)

        await sync_to_async(
            TelegramUser.objects.update_or_create
        )(
            telegram_id=update.effective_user.id,
            defaults={
                "student": student
            }
        )

        await update.message.reply_text(
            "Login successful ✅"
        )

    else:
        await update.message.reply_text(
            "Invalid username or password ❌"
        )

    return ConversationHandler.END

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.callback_query:
        reply = update.callback_query.message

    else:
        reply = update.message

    try:

        telegram_user = await sync_to_async(
            TelegramUser.objects.get
        )(
            telegram_id=update.effective_user.id
        )

        await sync_to_async(
            telegram_user.delete
        )()

        await reply.reply_text(
            "Logged out successfully ✅"
        )

    except TelegramUser.DoesNotExist:

        await reply.reply_text(
            "You are not logged in."
        )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    logged_in = await sync_to_async(
        TelegramUser.objects.filter(
            telegram_id=update.effective_user.id
        ).exists
    )()

    # Decide kis object se reply bhejna hai
    if update.callback_query:
        reply = update.callback_query.message
    else:
        reply = update.message

    if logged_in:

        await reply.reply_text(
            "🎓 Campus Buddy Dashboard",
            reply_markup=dashboard_keyboard()
        )

    else:

        await reply.reply_text(
            "🔐 Please login first.",
            reply_markup=login_keyboard()
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.data == "menu":
        await menu(update, context)

    elif query.data == "profile":
        await profile(update, context)

    elif query.data == "attendance":
        await attendance(update, context)

    elif query.data == "timetable":
        await timetable(update, context)

    elif query.data == "notices":
        await notices(update, context)

    elif query.data == "back":
        await back(update,context)

    elif query.data == "logout":
        await logout(update, context)




def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CommandHandler("profile", profile))

    app.add_handler(CommandHandler("attendance", attendance))

    app.add_handler(CommandHandler("notice", notices))

    app.add_handler(CommandHandler("timetable", timetable))

    app.add_handler(login_handler)

    app.add_handler(CommandHandler("logout", logout))

    app.add_handler(CommandHandler("menu", menu))

    app.add_handler(CallbackQueryHandler(button_handler,
pattern="^(menu|profile|attendance|notices|timetable|logout)$"
))
    
    print("Bot is running...")

    app.run_polling()


login_handler = ConversationHandler(
   entry_points=[
    CommandHandler("login", login),
    CallbackQueryHandler(login, pattern="^login$")
],

    states={
        USERNAME: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                get_username
            )
        ],

        PASSWORD: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                get_password
            )
        ],
    },

    fallbacks=[],
)



if __name__ == "__main__":
    main()