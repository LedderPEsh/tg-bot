import json
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ChatMemberHandler, filters
)

BOT_TOKEN = '8068486569:AAEwxyF1k8S7qw8wUkLCi4LA7VLa_rCNnmk'
DATA_FILE = "data.json"

OWNERS = {7974136455}
ADMINS = set(OWNERS)
chats = set()
user_state = {}
pending_broadcast = {}

# === Загрузка данных ===
def load_data():
    global chats, ADMINS
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            chats.update(data.get("chats", []))
            ADMINS.update(data.get("admins", []))
load_data()

# === Сохранение данных ===
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "chats": list(chats),
            "admins": list(ADMINS)
        }, f)

# === Меню ===
def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📣 Чаты"), KeyboardButton("📢 Рассылка")],
        [KeyboardButton("⚙️ Настройки")]
    ], resize_keyboard=True)

def chats_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📋 Просмотреть чаты")],
        [KeyboardButton("➕ Добавить чат"), KeyboardButton("➖ Удалить чат")],
        [KeyboardButton("🔙 Назад")]
    ], resize_keyboard=True)

def broadcast_confirm_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("✅ Подтвердить"), KeyboardButton("🔁 Заново")]
    ], resize_keyboard=True)

def broadcast_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("✉️ Начать рассылку")],
        [KeyboardButton("🔙 Назад")]
    ], resize_keyboard=True)

def settings_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("👑 Добавить админа"), KeyboardButton("❌ Удалить админа")],
        [KeyboardButton("📜 Посмотреть админов")],
        [KeyboardButton("🔙 Назад")]
    ], resize_keyboard=True)

# === Команды ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        return
    await update.message.reply_text("Главное меню:", reply_markup=main_menu())

async def handle_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    my_member = update.my_chat_member
    if my_member and my_member.new_chat_member.status in ["member", "administrator"]:
        chats.add(chat.id)
        save_data()
        try:
            await context.bot.send_message(chat.id, f"🤖 Бот добавлен в чат {chat.title or chat.id}")
        except Exception as e:
            print(f"❌ Не удалось отправить сообщение в чат {chat.id}: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if user_id not in ADMINS:
        return

    state = user_state.get(user_id)

    if text == "📣 Чаты":
        await update.message.reply_text("Меню чатов:", reply_markup=chats_menu())

    elif text == "📢 Рассылка":
        await update.message.reply_text("Меню рассылки:", reply_markup=broadcast_menu())

    elif text == "⚙️ Настройки":
        await update.message.reply_text("Меню настроек:", reply_markup=settings_menu())

    elif text == "📋 Просмотреть чаты":
        msg = "📋 Список чатов:\n"
        if chats:
            for cid in chats:
                try:
                    chat = await context.bot.get_chat(cid)
                    title = chat.title or chat.username or "—"
                    msg += f"• {cid} | {title}\n"
                except Exception as e:
                    msg += f"• {cid} | (ошибка: {e})\n"
        else:
            msg = "📭 Чатов нет."
        await update.message.reply_text(msg, reply_markup=chats_menu())

    elif text == "➕ Добавить чат":
        user_state[user_id] = "adding_chat"
        await update.message.reply_text("Введите ID чата:")

    elif text == "➖ Удалить чат":
        user_state[user_id] = "removing_chat"
        await update.message.reply_text("Введите ID чата для удаления:")

    elif text == "✉️ Начать рассылку":
        user_state[user_id] = "writing_broadcast"
        await update.message.reply_text("Введите текст рассылки:")

    elif text == "✅ Подтвердить":
        text_to_send = pending_broadcast.get(user_id)
        success = 0
        for cid in chats:
            try:
                await context.bot.send_message(chat_id=cid, text=text_to_send)
                success += 1
            except Exception as e:
                print(f"Ошибка отправки в чат {cid}: {e}")
        await update.message.reply_text(f"📬 Отправлено: {success}", reply_markup=main_menu())
        user_state[user_id] = None
        pending_broadcast.pop(user_id, None)

    elif text == "🔁 Заново":
        user_state[user_id] = "writing_broadcast"
        await update.message.reply_text("Введите текст рассылки:")

    elif text == "👑 Добавить админа":
        user_state[user_id] = "adding_admin"
        await update.message.reply_text("Введите ID нового админа:")

    elif text == "❌ Удалить админа":
        user_state[user_id] = "removing_admin"
        await update.message.reply_text("Введите ID админа для удаления:")

    elif text == "📜 Посмотреть админов":
        msg = "📃 Список админов:\n"
        for admin_id in ADMINS:
            try:
                user = await context.bot.get_chat(admin_id)
                username = f"@{user.username}" if user.username else "—"
                name = user.first_name or "—"
                msg += f"• {admin_id} | {username} | {name}\n"
            except Exception as e:
                msg += f"• {admin_id} | (ошибка: {e})\n"
        await update.message.reply_text(msg, reply_markup=settings_menu())

    elif text == "🔙 Назад":
        await update.message.reply_text("Главное меню:", reply_markup=main_menu())
        user_state[user_id] = None

    elif state == "adding_chat":
        try:
            chat_id = int(text)
            chats.add(chat_id)
            save_data()
            await update.message.reply_text(f"✅ Чат {chat_id} добавлен.", reply_markup=chats_menu())
        except:
            await update.message.reply_text("❌ Неверный ID.", reply_markup=chats_menu())
        user_state[user_id] = None

    elif state == "removing_chat":
        try:
            chat_id = int(text)
            chats.discard(chat_id)
            save_data()
            await update.message.reply_text(f"🗑️ Чат {chat_id} удалён.", reply_markup=chats_menu())
        except:
            await update.message.reply_text("❌ Неверный ID.", reply_markup=chats_menu())
        user_state[user_id] = None

    elif state == "writing_broadcast":
        pending_broadcast[user_id] = text
        await update.message.reply_text("Подтвердите рассылку:", reply_markup=broadcast_confirm_menu())

    elif state == "adding_admin":
        try:
            admin_id = int(text)
            ADMINS.add(admin_id)
            save_data()
            await update.message.reply_text(f"✅ Админ {admin_id} добавлен.", reply_markup=settings_menu())
        except:
            await update.message.reply_text("❌ Неверный ID.", reply_markup=settings_menu())
        user_state[user_id] = None

    elif state == "removing_admin":
        try:
            admin_id = int(text)
            if admin_id in OWNERS:
                await update.message.reply_text("❌ Нельзя удалить владельца.", reply_markup=settings_menu())
            else:
                ADMINS.discard(admin_id)
                save_data()
                await update.message.reply_text(f"🗑️ Админ {admin_id} удалён.", reply_markup=settings_menu())
        except:
            await update.message.reply_text("❌ Неверный ID.", reply_markup=settings_menu())
        user_state[user_id] = None

# === Запуск ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatMemberHandler(handle_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Бот запущен...")
    app.run_polling()
