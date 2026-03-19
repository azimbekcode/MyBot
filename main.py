import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from database import Database

# Logging set up
logging.basicConfig(level=logging.INFO)

# Load environment
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8279101815"))

# Database settings
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "userinfobot")

DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Initialize DB
db = Database(DB_URL)

dp = Dispatcher()
# Inject db into handlers
dp["db"] = db

# States for Admin Panel
class AdminStates(StatesGroup):
    wait_setting_news = State()
    wait_setting_welcome = State()
    wait_broadcast_msg = State()
    wait_delete_userid = State()

# --- Keyboards ---

def get_main_kb():
    builder = ReplyKeyboardBuilder()
    
    # User Request Buttons
    builder.add(types.KeyboardButton(text="👤 User", request_users=types.KeyboardButtonRequestUsers(request_id=1, user_is_bot=False)))
    builder.add(types.KeyboardButton(text="🌟 Premium", request_users=types.KeyboardButtonRequestUsers(request_id=2, user_is_premium=True)))
    builder.add(types.KeyboardButton(text="👽 Bot", request_users=types.KeyboardButtonRequestUsers(request_id=3, user_is_bot=True)))
    
    builder.add(types.KeyboardButton(text="👥 Group", request_chat=types.KeyboardButtonRequestChat(request_id=4, chat_is_channel=False)))
    builder.add(types.KeyboardButton(text="📢 Channel", request_chat=types.KeyboardButtonRequestChat(request_id=5, chat_is_channel=True)))
    builder.add(types.KeyboardButton(text="💬 Forum", request_chat=types.KeyboardButtonRequestChat(request_id=6, chat_is_channel=False, chat_is_forum=True)))
    
    # My Admin rows
    rights = types.ChatAdministratorRights(
        can_manage_chat=True, is_anonymous=False, can_post_messages=True, can_edit_messages=True, 
        can_delete_messages=True, can_manage_video_chats=True, can_restrict_members=True, 
        can_promote_members=True, can_change_info=True, can_invite_users=True, 
        can_post_stories=True, can_edit_stories=True, can_delete_stories=True
    )
    
    builder.add(types.KeyboardButton(text="👥 My Group", request_chat=types.KeyboardButtonRequestChat(request_id=7, chat_is_channel=False, user_administrator_rights=rights)))
    builder.add(types.KeyboardButton(text="📢 My Channel", request_chat=types.KeyboardButtonRequestChat(request_id=8, chat_is_channel=True, user_administrator_rights=rights)))
    builder.add(types.KeyboardButton(text="💬 My Forum", request_chat=types.KeyboardButtonRequestChat(request_id=9, chat_is_channel=False, chat_is_forum=True, user_administrator_rights=rights)))
    
    # Admin row
    # (Optional: only show if user is admin)
    
    builder.adjust(3)
    return builder.as_markup(resize_keyboard=True)

def get_id_keyboard(content_id):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=f"Copy {content_id}", callback_data=f"copy_{content_id}"))
    builder.row(types.InlineKeyboardButton(text="🚀 Share ID", switch_inline_query=str(content_id)))
    return builder.as_markup()

def get_admin_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Statistika", callback_data="admin_stats")
    builder.button(text="⚙️ Sozlamalar", callback_data="admin_settings")
    builder.button(text="👥 Foydalanuvchilar", callback_data="admin_users")
    builder.button(text="📢 Xabar yuborish", callback_data="admin_broadcast")
    builder.adjust(2)
    return builder.as_markup()

def get_settings_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="News Channel o'zgartirish", callback_data="set_news")
    builder.button(text="Welcome Text o'zgartirish", callback_data="set_welcome")
    builder.button(text="⬅️ Orqaga", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()

# --- Handlers ---

@dp.message(Command("start"))
async def start_handler(message: types.Message, db: Database):
    user_id = message.from_user.id
    # Add user to DB
    await db.add_user(user_id, message.from_user.username, message.from_user.full_name)
    
    settings = await db.get_settings()
    news_channel = settings.get('bot_news', '@AzimbekDeveloper')
    welcome_msg = settings.get('welcome_text', 'Botga xush kelibsiz!')
    
    resp_text = f"🔔 Bot News : {news_channel}\n\n{welcome_msg}\n\nYour ID : <code>{user_id}</code>"
    await message.answer(resp_text, parse_mode="HTML", reply_markup=get_main_kb())
    await message.answer(f"Your ID : <code>{user_id}</code>", parse_mode="HTML", reply_markup=get_id_keyboard(user_id))

@dp.message(Command("admin"))
async def admin_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return # Normal users can't see this
    
    await message.answer("🛠 Admin paneliga xush kelibsiz! Kerakli bo'limni tanlang:", reply_markup=get_admin_kb())

# --- Admin Callbacks ---

@dp.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: types.CallbackQuery, db: Database):
    count = await db.get_user_count()
    await callback.message.edit_text(f"📊 Jami foydalanuvchilar: {count}", reply_markup=get_admin_kb())

@dp.callback_query(F.data == "admin_settings")
async def admin_settings_callback(callback: types.CallbackQuery):
    await callback.message.edit_text("⚙️ Sozlamalar bo'limi:", reply_markup=get_settings_kb())

@dp.callback_query(F.data == "admin_users")
async def admin_users_callback(callback: types.CallbackQuery, db: Database):
    users = await db.get_all_users()
    text = "👥 Oxirgi 10 ta foydalanuvchi:\n\n"
    for u in users[:10]:
        text += f"ID: <code>{u['user_id']}</code> | @{u['username'] if u['username'] else 'Nomaslum'}\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Foydalanuvchini o'chirish", callback_data="admin_delete_user")
    builder.button(text="⬅️ Orqaga", callback_data="admin_back")
    builder.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "admin_back")
async def admin_back_callback(callback: types.CallbackQuery):
    await callback.message.edit_text("🛠 Admin paneli:", reply_markup=get_admin_kb())

# --- Settings Edit ---

@dp.callback_query(F.data == "set_news")
async def set_news_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Kanal nomini yuboring (masalan: @Kanal)")
    await state.set_state(AdminStates.wait_setting_news)
    await callback.answer()

@dp.message(AdminStates.wait_setting_news)
async def process_set_news(message: types.Message, db: Database, state: FSMContext):
    await db.update_setting('bot_news', message.text)
    await message.answer(f"✅ News channel {message.text} ga o'zgartirildi!")
    await state.clear()
    await admin_handler(message)

@dp.callback_query(F.data == "set_welcome")
async def set_welcome_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Yangi xush kelibsiz matnini yuboring:")
    await state.set_state(AdminStates.wait_setting_welcome)
    await callback.answer()

@dp.message(AdminStates.wait_setting_welcome)
async def process_set_welcome(message: types.Message, db: Database, state: FSMContext):
    await db.update_setting('welcome_text', message.text)
    await message.answer("✅ Xush kelibsiz matni o'zgartirildi!")
    await state.clear()
    await admin_handler(message)

# --- Broadcast ---

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Hamma foydalanuvchilarga yuborilishi kerak bo'lgan xabarni yuboring:")
    await state.set_state(AdminStates.wait_broadcast_msg)
    await callback.answer()

@dp.message(AdminStates.wait_broadcast_msg)
async def process_broadcast(message: types.Message, db: Database, state: FSMContext, bot: Bot):
    users = await db.get_all_users()
    success = 0
    fail = 0
    for u in users:
        try:
            await bot.send_message(u['user_id'], message.html_text, parse_mode="HTML")
            success += 1
        except Exception:
            fail += 1
    
    await message.answer(f"✅ Xabar yuborildi!\n✅ Muvaffaqiyatli: {success}\n❌ Xato: {fail}")
    await state.clear()
    await admin_handler(message)

# --- Delete User ---

@dp.callback_query(F.data == "admin_delete_user")
async def admin_delete_user_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("O'chirilishi kerak bo'lgan foydalanuvchi ID raqamini yuboring:")
    await state.set_state(AdminStates.wait_delete_userid)
    await callback.answer()

@dp.message(AdminStates.wait_delete_userid)
async def process_delete_user(message: types.Message, db: Database, state: FSMContext):
    try:
        user_id = int(message.text)
        await db.delete_user(user_id)
        await message.answer(f"🗑 Foydalanuvchi {user_id} bazadan o'chirildi!")
    except ValueError:
        await message.answer("❌ ID raqam xato! Faqat raqamlardan foydalaning.")
    
    await state.clear()
    await admin_handler(message)

# --- Original ID Handlers ---

@dp.message(F.users_shared)
async def users_shared_handler(message: types.Message):
    shared_users = message.users_shared.users
    for shared_user in shared_users:
        user_id = shared_user.user_id
        await message.answer(f"🔶 User ID : <code>{user_id}</code>", parse_mode="HTML", reply_markup=get_id_keyboard(user_id))

@dp.message(F.chat_shared)
async def chat_shared_handler(message: types.Message):
    chat_id = message.chat_shared.chat_id
    await message.answer(f"🔹 Chat ID : <code>{chat_id}</code>", parse_mode="HTML", reply_markup=get_id_keyboard(chat_id))

@dp.callback_query(F.data.startswith("copy_"))
async def copy_callback_handler(callback_query: types.CallbackQuery):
    content_id = callback_query.data.split("_")[1]
    await callback_query.answer(f"ID: {content_id}", show_alert=False)

async def main():
    if not TOKEN:
        print("BOT_TOKEN topilmadi! .env faylni tekshiring.")
        return
    
    await db.connect()
    bot = Bot(token=TOKEN)
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot to'xtatildi!")
