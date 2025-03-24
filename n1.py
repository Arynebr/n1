import requests
import random
import string
import json
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters
from datetime import datetime
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask import Flask, request

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# توکن و آیدی ادمین
TELEGRAM_TOKEN = "8137194776:AAE8ykPUbwtSZELn6tXdXdlOt6EYgOgi7U4"
ADMIN_CHAT_ID = 5739020477

# دیکشنری‌ها
user_emails = {}
user_info = {}
user_language = {}
last_message_count = {}

# تنظیم Flask
flask_app = Flask(__name__)

# ترجمه‌ها (مشابه قبل)
translations = {
    "en": {
        "welcome": "✨ *Welcome to TempMail Bot!* ✨\n\nI can create and manage temporary emails for you! Use the buttons below:",
        "create_success": "🎉 *Email Created Successfully!* 🎉\n\n📧 *Email:* `{email}`\n🔑 *Password:* `{password}`\n⏰ *Created At:* {created_at}\n\nWhat would you like to do next?",
        "no_emails": "⚠️ *No Emails Found!* Create one first.",
        "inbox_empty": "📭 Inbox Empty! No messages yet for `{email}`.",
        "select_inbox": "📬 *Select an Email to Check Its Inbox*:",
        "email_list": "📋 *Your Email List*:\n\nSelect an email for details or delete it:",
        "deleted_all": "🗑️ *All Emails Deleted!* What’s next?",
        "limit_reached": "⚠️ *Limit Reached!* You can have up to 5 emails. Delete one to create a new one.",
        "new_email_notification": "📩 *New Email Received!* Check your inbox for `{email}`.",
        "admin_unauthorized": "❌ *Unauthorized Access!* You are not allowed to use this command.",
        "admin_no_users": "ℹ️ *No Users Yet!* No emails have been created.",
        "admin_panel": "👨‍💼 *Admin Panel* 👨‍💼\n══════════════════════\n🌟 *Users and Their Emails* 🌟\n\n",
        "admin_user_info": "👤 *User Info*\n   🆔 *ID:* `{user_id}`\n   📛 *Name:* `{name}`\n   @ *Username:* `{username}`\n   📧 *Emails:*\n",
        "admin_email_info": "      {idx}. `{email}`\n         🔑 `{password}`\n         ⏰ `{created_at}`\n",
        "admin_check_inboxes": "📬 *All Users' Inboxes* 📬\n══════════════════════\n",
        "admin_no_emails_to_check": "ℹ️ *No Emails to Check!* No emails have been created yet.",
        "admin_inbox_empty": "      📧 `{email}`: *Inbox Empty*\n",
        "admin_login_failed": "      📧 `{email}`: *Login Failed*\n",
        "admin_inbox_message": "      📧 `{email}` ({count} messages):\n",
        "admin_message_details": "         ✨ *{idx}. Message*\n            ✉️ *From:* `{from_address}`\n            📑 *Subject:* `{subject}`\n            👀 *Preview:* `{intro}`\n            📅 *Date:* `{date}`\n",
        "admin_exit": "🔙 *Exit Admin Panel*"
    },
    "fa": {
        "welcome": "✨ *به ربات تمپ‌میل خوش اومدی!* ✨\n\nمی‌تونم برات ایمیل موقت بسازم و مدیریتش کنم! از دکمه‌های زیر استفاده کن:",
        "create_success": "🎉 *ایمیل با موفقیت ساخته شد!* 🎉\n\n📧 *ایمیل:* `{email}`\n🔑 *رمز عبور:* `{password}`\n⏰ *زمان ساخت:* {created_at}\n\nحالا چیکار می‌خوای بکنی؟",
        "no_emails": "⚠️ *هیچ ایمیلی پیدا نشد!* اول یکی بساز.",
        "inbox_empty": "📭 اینباکس خالیه! هنوز پیامی برای `{email}` نیومده.",
        "select_inbox": "📬 *یه ایمیل انتخاب کن تا اینباکسش رو ببینی*:",
        "email_list": "📋 *لیست ایمیل‌هات*:\n\nیه ایمیل انتخاب کن یا حذفش کن:",
        "deleted_all": "🗑️ *همه ایمیل‌ها حذف شدن!* حالا چیکار می‌خوای؟",
        "limit_reached": "⚠️ *به حد مجاز رسیدی!* فقط 5 تا ایمیل می‌تونی داشته باشی. یکی رو پاک کن تا جدید بسازی。",
        "new_email_notification": "📩 *ایمیل جدید دریافت شد!* اینباکس `{email}` رو چک کن.",
        "admin_unauthorized": "❌ *دسترسی غیرمجاز!* شما اجازه استفاده از این دستور رو ندارید。",
        "admin_no_users": "ℹ️ *هنوز کاربری وجود نداره!* هیچ ایمیلی ساخته نشده.",
        "admin_panel": "👨‍💼 *پنل ادمین* 👨‍💼\n══════════════════════\n🌟 *کاربران و ایمیل‌هاشون* 🌟\n\n",
        "admin_user_info": "👤 *اطلاعات کاربر*\n   🆔 *شناسه:* `{user_id}`\n   📛 *نام:* `{name}`\n   @ *نام کاربری:* `{username}`\n   📧 *ایمیل‌ها:*\n",
        "admin_email_info": "      {idx}. `{email}`\n         🔑 `{password}`\n         ⏰ `{created_at}`\n",
        "admin_check_inboxes": "📬 *اینباکس همه کاربران* 📬\n══════════════════════\n",
        "admin_no_emails_to_check": "ℹ️ *هیچ ایمیلی برای چک کردن وجود نداره!* هنوز کاربری ایمیل نساخته.",
        "admin_inbox_empty": "      📧 `{email}`: *اینباکس خالی*\n",
        "admin_login_failed": "      📧 `{email}`: *ورود ناموفق*\n",
        "admin_inbox_message": "      📧 `{email}` ({count} پیام):\n",
        "admin_message_details": "         ✨ *{idx}. پیام*\n            ✉️ *از:* `{from_address}`\n            📑 *موضوع:* `{subject}`\n            👀 *پیش‌نمایش:* `{intro}`\n            📅 *تاریخ:* `{date}`\n",
        "admin_exit": "🔙 *خروج از پنل ادمین*"
    }
}

# تنظیم Session
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429])
session.mount('https://', HTTPAdapter(max_retries=retries))

# توابع کمکی
def get_available_domain():
    try:
        response = session.get("https://api.mail.tm/domains", timeout=5)
        return response.json()["hydra:member"][0]["domain"]
    except:
        return "mail.tm"

def generate_random_email():
    name = random.choice(["john", "emma", "david", "sophia"])
    random_suffix = ''.join(random.choices(string.digits, k=3))
    domain = get_available_domain()
    return f"{name}{random_suffix}@{domain}"

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(characters, k=length))

def get_auth_token(email, password):
    try:
        response = session.post(
            "https://api.mail.tm/token",
            json={"address": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        return response.json().get("token")
    except:
        return None

def escape_markdown(text):
    if not text:
        return "N/A"
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

# منوها
def get_main_menu(chat_id):
    lang = user_language.get(chat_id, "en")
    keyboard = [
        [InlineKeyboardButton("📧 " + ("Create Email" if lang == "en" else "ساخت ایمیل"), callback_data='create_email')],
        [InlineKeyboardButton("📬 " + ("Check Inbox" if lang == "en" else "چک اینباکس"), callback_data='select_inbox'),
         InlineKeyboardButton("📋 " + ("Show Emails" if lang == "en" else "نمایش ایمیل‌ها"), callback_data='show_emails')],
        [InlineKeyboardButton("ℹ️ " + ("Email Info" if lang == "en" else "اطلاعات ایمیل"), callback_data='info'),
         InlineKeyboardButton("🗑️ " + ("Delete All" if lang == "en" else "حذف همه"), callback_data='delete_all')],
        [InlineKeyboardButton("🌐 " + ("Change Language" if lang == "en" else "تغییر زبان"), callback_data='change_language')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_email_list_menu(chat_id):
    lang = user_language.get(chat_id, "en")
    if chat_id not in user_emails or not user_emails[chat_id]:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 " + ("Back" if lang == "en" else "برگشت"), callback_data='back')]])
    keyboard = []
    for idx, email_data in enumerate(user_emails[chat_id]):
        email = email_data["email"]
        keyboard.append([
            InlineKeyboardButton(f"{email}", callback_data=f"info_{idx}"),
            InlineKeyboardButton("🗑️", callback_data=f"delete_{idx}"),
            InlineKeyboardButton("📋", callback_data=f"copy_{idx}")
        ])
    keyboard.append([InlineKeyboardButton("🔙 " + ("Back" if lang == "en" else "برگشت"), callback_data='back')])
    return InlineKeyboardMarkup(keyboard)

def get_inbox_selection_menu(chat_id):
    lang = user_language.get(chat_id, "en")
    if chat_id not in user_emails or not user_emails[chat_id]:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 " + ("Back" if lang == "en" else "برگشت"), callback_data='back')]])
    keyboard = [[InlineKeyboardButton(email_data["email"], callback_data=f"inbox_{idx}")] for idx, email_data in enumerate(user_emails[chat_id])]
    keyboard.append([InlineKeyboardButton("🔙 " + ("Back" if lang == "en" else "برگشت"), callback_data='back')])
    return InlineKeyboardMarkup(keyboard)

def get_admin_menu(chat_id):
    lang = user_language.get(chat_id, "en")
    keyboard = [
        [InlineKeyboardButton("📬 " + ("Check All Inboxes" if lang == "en" else "چک کردن همه اینباکس‌ها"), callback_data='admin_check_inboxes')],
        [InlineKeyboardButton("🔙 " + ("Exit Admin Panel" if lang == "en" else "خروج از پنل ادمین"), callback_data='admin_exit')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ارسال یا ویرایش پیام
async def send_or_edit_message(chat_id, text, context, reply_markup, message_id=None):
    if message_id:
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup, parse_mode='Markdown')
            return message_id
        except:
            pass
    message = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='Markdown')
    return message.message_id

# دستورات
async def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user = update.message.from_user
    user_info[chat_id] = {"name": user.first_name, "username": user.username or "N/A"}
    user_language[chat_id] = user_language.get(chat_id, "en")
    lang = user_language[chat_id]
    message_id = await send_or_edit_message(chat_id, translations[lang]["welcome"], context, get_main_menu(chat_id))
    context.user_data["last_message_id"] = message_id

async def create_email(chat_id, context: CallbackContext):
    lang = user_language.get(chat_id, "en")
    if chat_id in user_emails and len(user_emails[chat_id]) >= 5:
        message_id = context.user_data.get("last_message_id")
        new_message_id = await send_or_edit_message(chat_id, translations[lang]["limit_reached"], context, get_email_list_menu(chat_id), message_id)
        context.user_data["last_message_id"] = new_message_id
        return

    email = generate_random_email()
    password = generate_random_password()
    response = session.post("https://api.mail.tm/accounts", json={"address": email, "password": password}, headers={"Content-Type": "application/json"})
    response.raise_for_status()

    if chat_id not in user_emails:
        user_emails[chat_id] = []
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_emails[chat_id].append({"email": email, "password": password, "created_at": created_at})
    last_message_count[email] = 0

    message = translations[lang]["create_success"].format(email=escape_markdown(email), password=escape_markdown(password), created_at=created_at)
    message_id = context.user_data.get("last_message_id")
    new_message_id = await send_or_edit_message(chat_id, message, context, get_main_menu(chat_id), message_id)
    context.user_data["last_message_id"] = new_message_id

async def check_inbox(chat_id, context: CallbackContext, email_idx):
    lang = user_language.get(chat_id, "en")
    user_data = user_emails[chat_id][email_idx]
    token = get_auth_token(user_data["email"], user_data["password"])
    if not token:
        message_id = context.user_data.get("last_message_id")
        new_message_id = await send_or_edit_message(chat_id, "❌ *Login Failed!*", context, get_main_menu(chat_id), message_id)
        context.user_data["last_message_id"] = new_message_id
        return

    messages_response = session.get("https://api.mail.tm/messages", headers={"Authorization": f"Bearer {token}"}, timeout=5)
    messages_response.raise_for_status()
    messages = messages_response.json().get("hydra:member", [])

    if not messages:
        msg = translations[lang]["inbox_empty"].format(email=user_data["email"])
        message_id = context.user_data.get("last_message_id")
        new_message_id = await send_or_edit_message(chat_id, msg, context, get_main_menu(chat_id), message_id)
    else:
        msg = f"📬 *{'Inbox for' if lang == 'en' else 'اینباکس برای'} `{user_data['email']}`* ({min(5, len(messages))} {'messages' if lang == 'en' else 'پیام آخر'}):\n\n"
        keyboard = []
        for i, msg_data in enumerate(messages[:5], 1):
            from_address = msg_data.get("from", {}).get("address", "Unknown")
            subject = msg_data.get("subject", "No Subject")
            intro = msg_data.get("intro", "No Preview")
            date = msg_data.get("createdAt", "Unknown Time")[:10]
            msg += (
                f"✨ *{i}. {'Message' if lang == 'en' else 'پیام'}*\n"
                f"   ✉️ *{'From' if lang == 'en' else 'از'}:* `{from_address}`\n"
                f"   📑 *{'Subject' if lang == 'en' else 'موضوع'}:* `{subject}`\n"
                f"   👀 *{'Preview' if lang == 'en' else 'پیش‌نمایش'}:* `{intro}`\n"
                f"   📅 *{'Date' if lang == 'en' else 'تاریخ'}:* `{date}`\n\n"
            )
            keyboard.append([InlineKeyboardButton(f"📥 {'Download' if lang == 'en' else 'دانلود'} {i}", callback_data=f"download_{email_idx}_{msg_data['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 " + ("Back" if lang == "en" else "برگشت"), callback_data='back')])
        message_id = context.user_data.get("last_message_id")
        new_message_id = await send_or_edit_message(chat_id, msg, context, InlineKeyboardMarkup(keyboard), message_id)
    context.user_data["last_message_id"] = new_message_id

async def download_email(chat_id, context: CallbackContext, email_idx, message_id):
    user_data = user_emails[chat_id][email_idx]
    token = get_auth_token(user_data["email"], user_data["password"])
    if not token:
        message_id = context.user_data.get("last_message_id")
        new_message_id = await send_or_edit_message(chat_id, "❌ *Login Failed!*", context, get_main_menu(chat_id), message_id)
        context.user_data["last_message_id"] = new_message_id
        return

    file_name = None
    try:
        response = session.get(f"https://api.mail.tm/messages/{message_id}", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        response.raise_for_status()
        email_content = response.json()
        subject = email_content.get("subject", "No Subject")
        html_content = email_content.get("text") or email_content.get("html", "No content available")
        
        file_name = f"{subject[:20]}.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(html_content)
        with open(file_name, "rb") as f:
            await context.bot.send_document(chat_id=chat_id, document=f, filename=file_name)
        message_id = context.user_data.get("last_message_id")
        new_message_id = await send_or_edit_message(chat_id, "✅ *Downloaded!*", context, get_main_menu(chat_id), message_id)
        context.user_data["last_message_id"] = new_message_id
    finally:
        if file_name and os.path.exists(file_name):
            os.remove(file_name)

async def check_inboxes_periodically(context: CallbackContext):
    for chat_id, emails in user_emails.items():
        lang = user_language.get(chat_id, "en")
        for email_data in emails:
            token = get_auth_token(email_data["email"], email_data["password"])
            if token:
                try:
                    response = session.get("https://api.mail.tm/messages", headers={"Authorization": f"Bearer {token}"}, timeout=5)
                    messages = response.json().get("hydra:member", [])
                    current_count = len(messages)
                    last_count = last_message_count.get(email_data["email"], 0)
                    if current_count > last_count:
                        await context.bot.send_message(chat_id=chat_id, text=translations[lang]["new_email_notification"].format(email=email_data["email"]), parse_mode='Markdown')
                    last_message_count[email_data["email"]] = current_count
                except:
                    pass

async def admin_panel(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    lang = user_language.get(chat_id, "en")
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text(translations[lang]["admin_unauthorized"], parse_mode='Markdown')
        return
    if not user_emails:
        await update.message.reply_text(translations[lang]["admin_no_users"], parse_mode='Markdown')
        return
    admin_msg = translations[lang]["admin_panel"]
    for user_id, emails in user_emails.items():
        name = user_info.get(user_id, {}).get("name", "Unknown")
        username = user_info.get(user_id, {}).get("username", "N/A")
        admin_msg += translations[lang]["admin_user_info"].format(user_id=user_id, name=escape_markdown(name), username=escape_markdown(username))
        for idx, email_data in enumerate(emails):
            admin_msg += translations[lang]["admin_email_info"].format(idx=idx + 1, email=escape_markdown(email_data['email']), password=escape_markdown(email_data['password']), created_at=email_data['created_at'])
    message_id = await send_or_edit_message(chat_id, admin_msg, context, get_admin_menu(chat_id))
    context.user_data["last_message_id"] = message_id

async def admin_check_inboxes(chat_id, context: CallbackContext):
    lang = user_language.get(chat_id, "en")
    if chat_id != ADMIN_CHAT_ID:
        return
    if not user_emails:
        message_id = context.user_data.get("last_message_id")
        new_message_id = await send_or_edit_message(chat_id, translations[lang]["admin_no_emails_to_check"], context, get_admin_menu(chat_id), message_id)
        context.user_data["last_message_id"] = new_message_id
        return

    inbox_msg = translations[lang]["admin_check_inboxes"]
    for user_id, emails in user_emails.items():
        name = user_info.get(user_id, {}).get("name", "Unknown")
        username = user_info.get(user_id, {}).get("username", "N/A")
        inbox_msg += translations[lang]["admin_user_info"].format(user_id=user_id, name=escape_markdown(name), username=escape_markdown(username))
        for email_data in emails:
            token = get_auth_token(email_data["email"], email_data["password"])
            if not token:
                inbox_msg += translations[lang]["admin_login_failed"].format(email=email_data["email"])
                continue
            try:
                messages_response = session.get("https://api.mail.tm/messages", headers={"Authorization": f"Bearer {token}"}, timeout=5)
                messages = messages_response.json().get("hydra:member", [])
                if not messages:
                    inbox_msg += translations[lang]["admin_inbox_empty"].format(email=email_data["email"])
                else:
                    inbox_msg += translations[lang]["admin_inbox_message"].format(email=email_data["email"], count=len(messages))
                    for i, msg_data in enumerate(messages[:5], 1):
                        from_address = msg_data.get("from", {}).get("address", "Unknown")
                        subject = msg_data.get("subject", "No Subject")
                        intro = msg_data.get("intro", "No Preview")
                        date = msg_data.get("createdAt", "Unknown Time")[:10]
                        inbox_msg += translations[lang]["admin_message_details"].format(idx=i, from_address=from_address, subject=subject, intro=intro, date=date)
            except:
                inbox_msg += translations[lang]["admin_inbox_empty"].format(email=email_data["email"])
    message_id = context.user_data.get("last_message_id")
    new_message_id = await send_or_edit_message(chat_id, inbox_msg, context, get_admin_menu(chat_id), message_id)
    context.user_data["last_message_id"] = new_message_id

# Webhook Handler
@flask_app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(force=True), app.bot)
    await app.process_update(update)
    return '', 200

# تابع اصلی
app = None
async def main():
    global app
    # ساخت Application
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # ثبت Handlerها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button))

    # اطمینان از اینکه Application کاملاً ساخته شده
    await app.initialize()
    await app.start()

    # تنظیم Job برای چک کردن اینباکس‌ها
    if app.job_queue is None:
        logger.error("Job Queue is None! Initializing job queue...")
        app.job_queue = app.create_job_queue()  # ایجاد job_queue در صورت نیاز
    app.job_queue.run_repeating(check_inboxes_periodically, interval=300, first=10)

    # تنظیم Webhook
    port = int(os.environ.get("PORT", 8443))  # Render پورت رو از محیط می‌گیره
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook"  # آدرس Render
    await app.bot.set_webhook(url=webhook_url)

    # اجرای Flask
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    asyncio.run(main())
