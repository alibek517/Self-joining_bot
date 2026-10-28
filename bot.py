import asyncio
import datetime
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter, MEMBER, ADMINISTRATOR
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
import config
import database

logger = logging.getLogger("PassengerBot")

class OrderStates(StatesGroup):
    waiting_for_phone = State()

dp = Dispatcher()
bot_instance: Bot = None

DIRECTIONS = ["🚖 Toshkent ➡️ Xorazm", "🚖 Xorazm ➡️ Toshkent", "📦 Pochta / Yuk yuborish"]

def get_direction_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚖 Toshkent ➡️ Xorazm"), KeyboardButton(text="🚖 Xorazm ➡️ Toshkent")],
            [KeyboardButton(text="📦 Pochta / Yuk yuborish")]
        ],
        resize_keyboard=True
    )

def get_phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="🔙 Bosh menyu")]
        ],
        resize_keyboard=True
    )


async def send_order_to_drivers(bot: Bot, direction: str, phone: str, user: types.User):
    """Buyurtmani bazaga saqlaydi, Haydovchilar guruhiga hamda barcha Adminlarga yuboradi."""
    import html
    full_name = user.full_name or "Mijoz"
    username = f"@{user.username}" if user.username else "Yo'q"
    user_id = user.id
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Bazaga saqlash
    database.save_order(
        user_id=user_id,
        full_name=full_name,
        username=user.username,
        phone=phone,
        direction=direction,
        district="",
        passengers="",
        comment=""
    )

    safe_name = html.escape(full_name)
    safe_direction = html.escape(direction)
    safe_phone = html.escape(phone)
    safe_username = html.escape(username)

    if user.username:
        user_link = f'<a href="https://t.me/{user.username}">{safe_name}</a> ({safe_username})'
    else:
        user_link = f'<a href="tg://user?id={user_id}">{safe_name}</a>'

    alert_text = (
        "🚨 <b>YANGI BUYURTMA! (Bot orqali keldi)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Yo'nalish:</b> {safe_direction}\n"
        f"📞 <b>Telefon:</b> <code>{safe_phone}</code>\n"
        f"👤 <b>Mijoz:</b> {user_link}\n"
        f"🆔 <b>Telegram ID:</b> <code>{user_id}</code>\n"
        f"⏰ <b>Vaqt:</b> {now_str}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 <a href=\"tg://user?id={user_id}\">Mijoz profilini ochish (Lichka)</a>"
    )

    if user.username:
        contact_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="💬 Mijozga yozish", url=f"https://t.me/{user.username}")]]
        )
    else:
        contact_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="💬 Profilni ochish", url=f"tg://user?id={user_id}")]]
        )

    # 1. Haydovchilar guruhiga yuborish
    target_group_ids = [
        config.DRIVERS_GROUP_ID,
        int(f"-100{abs(config.DRIVERS_GROUP_ID)}"),
        int(str(config.DRIVERS_GROUP_ID).replace("-100", "-"))
    ]

    sent_to_group = False
    for gid in target_group_ids:
        try:
            await bot.send_message(
                chat_id=gid,
                text=alert_text,
                reply_markup=contact_kb,
                parse_mode="HTML"
            )
            logger.info(f"✅ Yangi buyurtma haydovchilar guruhiga ({gid}) yuborildi!")
            sent_to_group = True
            break
        except Exception as ge:
            logger.warning(f"Haydovchilar guruhiga ({gid}) yuborishda xatolik: {ge}")

    # 2. BARCHA ADMINLARGA TO'G'RIDAN-TO'G'RI YUBORISH
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=alert_text,
                reply_markup=contact_kb,
                parse_mode="HTML"
            )
            logger.info(f"✅ Yangi buyurtma adminga ({admin_id}) to'g'ridan-to'g'ri yuborildi!")
        except Exception as ae:
            logger.warning(f"Adminga ({admin_id}) buyurtmani yuborishda xatolik: {ae}")

    return sent_to_group


# --- Guruh ID sini avtomatik aniqlash va sozlash ---

@dp.message(Command("id"))
async def get_id_command(message: types.Message):
    chat = message.chat
    if chat.type in ["group", "supergroup"]:
        text = (
            f"📍 Guruh nomi: **{chat.title}**\n"
            f"🆔 Ushbu Guruh ID si: `{chat.id}`\n\n"
            f"🚕 Asosiy Haydovchilar guruhi (Voha): `{config.DRIVERS_GROUP_ID}`\n"
            f"🚕 Vodiy Haydovchilar guruhi: `{config.DRIVERS_VODIY_GROUP_ID}`\n"
            f"🚕 Nukus-Gurlan-Urganch guruhi: `{config.DRIVERS_LOCAL_GROUP_ID}`"
        )
        await message.reply(text, parse_mode="Markdown")
    else:
        await message.reply(f"Sizning shaxsiy Telegram ID: `{message.from_user.id}`", parse_mode="Markdown")


@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER | ADMINISTRATOR))
async def on_bot_added_to_group(event: types.ChatMemberUpdated, bot: Bot):
    if event.chat.type in ["group", "supergroup"]:
        logger.info(f"Bot guruhga qo'shildi: {event.chat.title} (ID: {event.chat.id})")
        try:
            await bot.send_message(
                chat_id=event.chat.id,
                text=(
                    f"🚕 **Assalomu alaykum! Taxi boti guruhga muvaffaqiyatli ulandi!**\n\n"
                    f"📍 **Guruh:** {event.chat.title}\n"
                    f"🆔 **Guruh ID:** `{event.chat.id}`\n"
                    f"✅ Topilgan mijozlar buyurtmalari avtomatik tarzda yetkazib beriladi."
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Guruhga salom xabari yuborishda xatolik: {e}")


# --- Buyurtma jarayoni ---

@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    if message.chat.type != "private":
        return

    await state.clear()
    text = (
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        "🚕 **Toshkent — Xorazm** taxi xizmatiga xush kelibsiz!\n\n"
        "Qaysi yo'nalishda taksi kerak? Quyidagi tugmalardan birini tanlang:"
    )
    await message.answer(text, reply_markup=get_direction_kb(), parse_mode="Markdown")


@dp.message(F.text == "🔙 Bosh menyu")
async def back_to_start(message: types.Message, state: FSMContext):
    await start_handler(message, state)


# HAR QANDAY VAQTDA yo'nalish tugmasi bosilganda ishlaydi
@dp.message(F.text.in_(DIRECTIONS))
async def process_direction_always(message: types.Message, state: FSMContext, bot: Bot):
    if message.chat.type != "private":
        return

    direction = message.text
    user_id = message.from_user.id
    await state.update_data(direction=direction)

    # Foydalanuvchining avvalgi telefon raqami bazada bormi?
    saved_phone = database.get_user_last_phone(user_id)

    if saved_phone:
        # Raqam ma'lum bo'lsa, srazi buyurtma qilib haydovchilar guruhiga jo'natamiz!
        await send_order_to_drivers(bot, direction, saved_phone, message.from_user)
        
        reply_text = (
            "✅ **Buyurtmangiz qabul qilindi!**\n\n"
            f"📍 Yo'nalish: **{direction}**\n"
            f"📞 Telefon: `{saved_phone}`\n\n"
            "🚖 **Haydovchilar tez orada bog'lanadi!**\n\n"
            "_(Boshqa raqam kiritmoqchi bo'lsangiz, yangi raqamingizni yozib yuboring)_"
        )
        await message.answer(reply_text, reply_markup=get_direction_kb(), parse_mode="Markdown")
        await state.set_state(OrderStates.waiting_for_phone)
    else:
        # Yangi foydalanuvchi bo'lsa, telefon raqamini so'raymiz
        await message.answer(
            "Siz bilan bog'lanish uchun telefon raqamingizni yuboring:\n\n"
            "_(Pastdagi «📱 Telefon raqamni yuborish» tugmasini bosing yoki raqamingizni yozib yuboring)_",
            reply_markup=get_phone_kb(),
            parse_mode="Markdown"
        )
        await state.set_state(OrderStates.waiting_for_phone)


# Telefon raqami kelganda (tugma yoki yozilgan raqam orqali)
@dp.message(OrderStates.waiting_for_phone)
@dp.message(F.contact)
async def process_phone(message: types.Message, state: FSMContext, bot: Bot):
    if message.chat.type != "private":
        return

    if message.text == "🔙 Bosh menyu":
        await start_handler(message, state)
        return

    if message.contact:
        phone = message.contact.phone_number
        if not phone.startswith("+"):
            phone = f"+{phone}"
    else:
        phone = message.text.strip() if message.text else ""

    data = await state.get_data()
    direction = data.get("direction", "🚖 Toshkent ➡️ Xorazm")

    # Haydovchilar guruhiga jo'natish
    await send_order_to_drivers(bot, direction, phone, message.from_user)

    # Mijozga javob
    reply_text = (
        "✅ **Buyurtmangiz qabul qilindi!**\n\n"
        f"📍 Yo'nalish: **{direction}**\n"
        f"📞 Telefon: `{phone}`\n\n"
        "🚖 **Haydovchilar tez orada bog'lanadi!**"
    )
    await message.answer(reply_text, reply_markup=get_direction_kb(), parse_mode="Markdown")
    await state.clear()


async def run_bot():
    """Botni ishga tushirish funksiyasi (avtomatik qayta ulanish bilan)."""
    global bot_instance
    if not config.BOT_TOKEN:
        logger.warning("BOT_TOKEN ko'rsatilmagan. Bot faqat userbot rejimida ishlaydi.")
        return

    session = AiohttpSession(timeout=60.0)
    bot_instance = Bot(token=config.BOT_TOKEN, session=session)
    logger.info("Mijozlar uchun tezkor Taxi boti faol ishga tushmoqda...")
    try:
        await bot_instance.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass

    while True:
        try:
            await dp.start_polling(bot_instance, polling_timeout=20, handle_signals=False)
        except (ConnectionError, OSError, asyncio.TimeoutError) as net_err:
            logger.warning(f"⚠️ Mijozlar botida tarmoq uzilishi: {net_err}. 2 soniyadan so'ng qayta ulanadi...")
            await asyncio.sleep(2)
        except Exception as e:
            err_msg = str(e)
            if "Request timeout error" in err_msg or "timeout" in err_msg.lower():
                logger.warning("⚠️ Telegram tarmog'ida vaqtinchalik kechikish. 2 soniyadan so'ng qayta ulanmoqda...")
            else:
                logger.error(f"⚠️ Mijozlar botida xatolik: {e}. 3 soniyadan so'ng qayta ishga tushiriladi...")
            await asyncio.sleep(2)
