import asyncio
import logging
import sys

# Windows konsolida emojilarni xatosiz chiqarish uchun
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import config
import database
import userbot
import group_joiner
import group_cleaner
import bot

# Loglarni sozlash (konsolga va bot.log fayliga)
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", mode="a", encoding="utf-8")
    ]
)

# Telethon va aiogram kutubxonalarining shovqinli (updates, polling, network) loglarini o'chirish
for noisy_lib in [
    "telethon",
    "telethon.client.updates",
    "telethon.network",
    "telethon.network.mtprotosender",
    "telethon.client.users",
    "aiogram",
    "aiogram.dispatcher",
    "aiogram.event",
    "asyncio",
    "urllib3"
]:
    logging.getLogger(noisy_lib).setLevel(logging.WARNING)

logger = logging.getLogger("MainRunner")

async def run_userbot():
    """Telethon Userbotini ishga tushirish (avtomatik qayta ulanish bilan)."""
    scheduler_task = None
    cleaner_task = None
    is_first_run = True

    while True:
        try:
            logger.info("Telegram Userbotiga ulanmoqda...")
            if not userbot.client.is_connected():
                await userbot.client.connect()

            if not await userbot.client.is_user_authorized():
                await userbot.client.start(phone=lambda: config.PHONE_NUMBER)

            me = await userbot.client.get_me()
            if is_first_run:
                print("\n" + "=" * 55)
                print("✅ Telegram hisobiga muvaffaqiyatli kirildi!")
                print(f"👤 Ism: {me.first_name} {me.last_name or ''}".strip())
                print(f"🆔 Telegram ID: {me.id}")
                print(f"🔗 Username: @{me.username}" if me.username else "🔗 Username: Yo'q")
                print(f"📞 Telefon raqam: +{me.phone}")
                print(f"🚕 Asosiy Haydovchilar guruhi (Voha) ID: {config.DRIVERS_GROUP_ID}")
                print(f"🚕 Vodiy Haydovchilar guruhi ID: {config.DRIVERS_VODIY_GROUP_ID}")
                print(f"🚕 Nukus-Gurlan-Urganch guruhi ID: {config.DRIVERS_LOCAL_GROUP_ID}")
                print("=" * 55 + "\n")

                # Dastlabki mavjud guruhlarni bazaga saqlab olish (yangi deb hisoblamaslik uchun)
                await userbot.sync_initial_groups()

                # Haydovchilar guruhini bir marta tekshirib olish
                await userbot.resolve_drivers_peer_once()

                # Barcha guruhlar, kanallar va botlarni birma-bir MUTE qilish (fon rejimida)
                asyncio.create_task(userbot.mute_all_groups_channels_and_bots(userbot.client))
                is_first_run = False
            else:
                logger.info("✅ Telegram Userboti qayta ulandi!")

            # Kunlik guruhlarga a'zo bo'luvchi va noaktiv guruhlarni tozalovchi foniy vazifalarni yoqish
            if scheduler_task is None or scheduler_task.done():
                scheduler_task = asyncio.create_task(group_joiner.auto_join_scheduler(userbot.client))
            if cleaner_task is None or cleaner_task.done():
                cleaner_task = asyncio.create_task(group_cleaner.auto_cleaner_scheduler(userbot.client))

            # Userbot xabarlarni tinglashi uchun kutish rejimiga o'tadi
            await userbot.client.run_until_disconnected()

        except (ConnectionError, OSError, asyncio.TimeoutError) as net_err:
            logger.warning(f"⚠️ Internet uzildi yoki aloqa yo'qoldi: {net_err}. 10 soniyadan so'ng qayta ulanadi...")
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"⚠️ Userbotda kutilmagan xatolik yuz berdi: {e}. 10 soniyadan so'ng qayta uriniladi...")
            await asyncio.sleep(10)


async def main():
    # 1. Ma'lumotlar bazasini ishga tushirish
    database.init_db()
    logger.info("SQLite ma'lumotlar bazasi tayyor.")

    tasks = [run_userbot()]

    # 2. Agar Telegram Bot Token kiritilgan bo'lsa, mijozlar botini ham ishga tushiramiz
    if config.BOT_TOKEN:
        logger.info("BOT_TOKEN aniqlandi! Mijozlar uchun buyurtma boti ham ishga tushirilmoqda...")
        tasks.append(bot.run_bot())
    else:
        print("\n" + "!" * 55)
        print("💡 ESLATMA: .env faylida BOT_TOKEN kiritilmagan.")
        print("Userbot (guruhlarni qidirish, qo'shilish va xabarlarni tutib")
        print("haydovchilarga yuborish) to'liq ishlamoqda.")
        print("Mijozlar @BotFather orqali start bosishi uchun .env ga BOT_TOKEN qo'shing.")
        print("!" * 55 + "\n")

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n[!] Dastur to'xtatildi.")
