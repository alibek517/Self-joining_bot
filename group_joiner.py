import asyncio
import datetime
import logging
import random
import time
from telethon import functions
from telethon.tl.types import Channel, Chat, InputMessagesFilterEmpty, InputPeerEmpty
from telethon.errors import FloodWaitError, UserAlreadyParticipantError, RPCError
from telethon.tl.functions.account import UpdateNotifySettingsRequest
from telethon.tl.types import InputNotifyPeer, InputPeerNotifySettings
import config
import database
import bot

logger = logging.getLogger("GroupJoiner")

async def mute_peer(client, peer) -> bool:
    """Yangi guruh bildirishnomalarini (notification va so'rovnomalarni) butunlay o'chirib qo'yadi (MUTE)."""
    try:
        input_peer = await client.get_input_entity(peer)
        far_future = datetime.datetime(2038, 1, 1)
        await client(UpdateNotifySettingsRequest(
            peer=InputNotifyPeer(input_peer),
            settings=InputPeerNotifySettings(
                mute_until=far_future,
                silent=True,
                show_previews=False
            )
        ))
        logger.info(f"🔕 Guruh muvaffaqiyatli MUTE qilindi!")
        return True
    except Exception as e:
        logger.warning(f"Guruhni mute qilishda xatolik: {e}")
        return False


TAXI_INDICATORS = [
    "taxi", "taksi", "такси",
    "pochta", "почта", "пошто", "poshta", "пошта",
    "yo'l", "yol", "йул", "йўл", "qatnov", "қатнов", "катнов",
    "poputka", "попутка", "poputi", "попути",
    "transport", "транспорт", "pitak", "питак", "pyatak", "пятак",
    "kirakash", "киракаш", "reys", "рейс",
    "mashina", "moshina", "машина", "мошина"
]

# Mutlaqo to'xtatilgan / kirmaslik kerak bo'lgan yo'nalishlar (Faqat Chet el)
EXTERNAL_EXCLUDED = [
    "moskva", "москва", "rossiya", "россия", "piter", "питер", "sankt", "санкт",
    "qozogiston", "казахстан", "krasnodar", "краснодар", "novosibirsk", "новосибирск",
    "turkiya", "турция", "dubay", "дубай"
]

# O'zbekiston Respublikasining barcha viloyat, shahar va tumanlari:
TARGET_CITIES = [
    # 1. Asosiy ustuvor: Toshkent, Xorazm, Samarqand
    "toshkent", "тошкент", "tashkent", "ташкент",
    "xorazm", "хоразм", "xarezm", "urganch", "урганч", "ургенч",
    "gurlan", "гурлан", "gurland", "гурланд",
    "samarqand", "самарқанд", "самарканд", "samarkand", "kattaqorgon", "каттақўрғон",

    # 2. Qoraqalpog'iston va ichki tumanlar
    "nukus", "нукус", "nokis", "нокис", "qoraqalpoq", "қорақалпоқ",
    "mangit", "манғит", "мангит", "shovot", "шовот", "shavat", "шават",
    "xiva", "хива", "xonqa", "хонқа", "qoshkopir", "қўшкўпир",
    "beruniy", "беруний", "turtkul", "тўрткўл", "ellikqala", "элликқалъа",
    "xojayli", "хўжайли", "taxiatosh", "тахиатош", "pitnak", "питнақ", "yangiariq", "янгиариқ",
    "qongirot", "қўнғирот", "kungrad", "chimboy", "чимбой",

    # 3. Voha viloyatlari
    "voha", "воҳа", "воха",
    "buxoro", "бухоро", "buxara", "gijduvon", "ғиждувон", "qorakol", "қоракўл", "olot", "олот",
    "navoiy", "навоий", "zarafshon", "зарафшон", "karmana", "кармана", "uchquduq", "учқудуқ",
    "qarshi", "қарши", "karshi", "shahrisabz", "шаҳрисабз", "qashqadaryo", "қашқадарё",
    "termiz", "термиз", "denov", "денов", "surxondaryo", "сурхондарё",
    "jizzax", "жиззах", "sirdaryo", "сирдарё", "guliston", "гулистон",

    # 4. Vodiy viloyatlari
    "andijon", "андижон", "andijan", "asaka", "асака", "shahrixon", "шаҳрихон",
    "namangan", "наманган", "chust", "чуст",
    "fargona", "фарғона", "fergana", "qoqon", "қўқон", "коканд", "margilon", "марғилон",
    "vodiy", "водий"
]

query_cursor = 0
contacts_flood_wait_until = 0.0


def get_next_query_batch(batch_size: int = 5):
    """Barcha Toshkent - Xorazm qidiruv so'rovlarini aylanma (round-robin) tartibda qaytaradi."""
    global query_cursor
    queries = config.SEARCH_QUERIES
    if not queries:
        return []
    total = len(queries)
    batch = []
    for _ in range(batch_size):
        batch.append(queries[query_cursor % total])
        query_cursor = (query_cursor + 1) % total
    return batch


# Mahalliy mayda bozor, mahalla va qishloq yo'nalishlari (MUTLAQO RAD ETILADI)
LOCAL_MICRO_EXCLUDED = [
    "bozor", "bozorgacha", "bozordan", "бозор", "бозоргача", "бозордан", "bozorga", "бозорга",
    "mahalla", "mahallasigacha", "маҳалла", "махалла", "махалласигача",
    "qishloq", "қишлоқ", "ovul", "овул", "avul", "авул",
    "damas", "дамас", "marshrutka", "маршрутка", "damaslar", "дамаслар"
]

# Teskari va qat'iy taqiqlangan yo'nalishlar (Urgut-Toshkent, Bog'ot, Dmitrov, Komuna, Bog'olon, Uchqo'rg'on, Uychi, Chortoq)
REVERSE_AND_UNWANTED_EXCLUDED = [
    "urgut", "ургут",
    "dmitrov", "дмитров", "komuna", "коммуна", "комmuna",
    "bog'olon", "bogolon", "боғолон", "боголон",
    "uchqorgon", "uchqo'rg'on", "учқўрғон", "uchkurgon",
    "uychi", "уйчи", "chortoq", "чортоқ",
    "kegeyli", "кегейли", "kegayli", "кегайли",
    "camfort", "kamfort",
    "nurobod", "нуробод"
]

def is_relevant_group_title(title: str) -> bool:
    """Guruh nomi yo'nalishga mosligini tekshiradi."""
    if not title:
        return False

    # 0. Foydalanuvchi taqiqlagan yo'nalishlar (Gurlan-Guliston, Qarshi-Toshkent, Surxondaryo-Buxoro-Termiz)
    if config.is_excluded_group_title(title):
        return False

    lower = title.lower()

    # 1. Mayda mahalla / bozor / damas guruhlari mutlaqo RAD ETILADI!
    if any(micro in lower for micro in LOCAL_MICRO_EXCLUDED):
        return False

    # 2. Begona yo'nalishlar (Rossiya va h.k.) mutlaqo RAD ETILADI!
    if any(ext in lower for ext in EXTERNAL_EXCLUDED):
        return False

    # 3. Teskari va noo'rin yo'nalishlar mutlaqo RAD ETILADI!
    if any(unwanted in lower for unwanted in REVERSE_AND_UNWANTED_EXCLUDED):
        return False

    # 4. Ichki teskari yo'nalishlarni filtrlash (Bog'ot, Yangibozor, Qarshi-Buxoro, Qarshi-Navoiy, Zarafshon-Navoiy)
    has_long_distance = any(far in lower for far in ["toshkent", "тошкент", "samarqand", "самарқанд"])

    # Bog'ot yoki Yangibozor ichki yo'nalishlari
    if any(b in lower for b in ["bogot", "богот", "боғот", "yangibozor", "янгибозор"]) and not has_long_distance:
        return False

    # Hazorasp-Urganch ichki
    if any(h in lower for h in ["hazorasp", "xozarasp", "ҳазорасп", "хазорасп"]) and any(u in lower for u in ["urganch", "shovot", "урганч", "ургенч"]) and not has_long_distance:
        return False

    # Qarshi-Buxoro-Navoiy ichki
    is_qarshi = any(q in lower for q in ["qarshi", "қарши", "karshi"])
    is_buxoro = any(b in lower for b in ["buxoro", "бухоро", "buxara"])
    is_navoiy = any(n in lower for n in ["navoiy", "навоий", "navoi"])
    is_zarafshon = any(z in lower for z in ["zarafshon", "зарафшон"])

    if is_qarshi and is_buxoro and not has_long_distance:
        return False
    if is_qarshi and is_navoiy and not has_long_distance:
        return False
    if is_zarafshon and is_navoiy and not has_long_distance:
        return False

    # 5. Toshkent - Xorazm yo'nalishi tekshiruvi (Foydalanuvchi talabi)
    TOSHKENT_TARGETS = [
        "toshkent", "тошкент", "tashkent", "ташкент"
    ]
    XORAZM_TARGETS = [
        "xorazm", "хоразм", "xarezm",
        "urganch", "урганч", "ургенч", "urgench",
        "xiva", "хива",
        "gurlan", "гурлан", "gurland", "гурланд",
        "xonqa", "хонқа", "хонка",
        "hazorasp", "ҳазорасп", "xazorasp", "хазорасп",
        "shovot", "шовот", "shavat", "шават",
        "yangibozor", "янгибозор",
        "qoshkopir", "қўшкўпир", "кошкупир",
        "bogot", "боғот", "богот",
        "pitnak", "питнақ", "питноқ",
        "yangiariq", "янгиариқ",
        "tuproqqala", "тупроққалъа"
    ]

    has_toshkent = any(t in lower for t in TOSHKENT_TARGETS)
    has_xorazm = any(x in lower for x in XORAZM_TARGETS)

    # Guruh nomida Xorazm (yoki Xorazm tumanlari) bo'lishi SHART!
    if not has_xorazm:
        return False

    # A) Agar Toshkent va Xorazm ikkalasi ham bo'lsa -> 100% Toshkent-Xorazm yo'nalishi!
    if has_toshkent and has_xorazm:
        return True

    # B) Agar Xorazm va taxi/pitak/poputi/pochta indikatori bo'lsa -> mos
    has_taxi = any(ind in lower for ind in TAXI_INDICATORS)
    if has_taxi:
        return True

    return False


async def notify_admin_about_joined_group(client, chat_title: str, username: str, chat_id: int, members_count: int, route_name: str = "Toshkent - Xorazm yo'nalishi"):
    """Adminlarga yangi aktiv guruhga qo'shilganlik haqida hisobot yuboradi."""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_groups = database.get_total_groups_count()
    username_str = f"@{username}" if username else "Mavjud emas (Yopiq)"
    members_str = f"{members_count:,} ta".replace(",", " ") if members_count else "Ko'rsatilmadi"

    report_text = (
        "📢 **YANGI AKTIV TAXI GURUHIGA QO'SHILINDI!**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 **Guruh nomi:** {chat_title}\n"
        f"🔄 **Yo'nalish:** {route_name}\n"
        f"👥 **A'zolar soni:** {members_str} (Aktiv)\n"
        f"🔗 **Havola:** {username_str}\n"
        f"🆔 **Guruh ID si:** `{chat_id}`\n"
        f"⏰ **Vaqt:** {now_str}\n"
        f"📊 **Bazadagi jami guruhlar:** {total_groups} ta\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )

    for admin_id in config.ADMIN_IDS:
        sent = False
        try:
            await client.send_message(admin_id, report_text)
            sent = True
            logger.info(f"✅ Yangi guruh hisoboti adminga ({admin_id}) userbot orqali yuborildi.")
        except Exception:
            pass

        if not sent and bot.bot_instance:
            try:
                await bot.bot_instance.send_message(
                    chat_id=admin_id,
                    text=report_text,
                    parse_mode="Markdown"
                )
                sent = True
                logger.info(f"✅ Yangi guruh hisoboti adminga ({admin_id}) bot orqali yuborildi.")
            except Exception:
                pass


async def find_and_join_groups(client):
    """Guruhlarni qidiradi va tezkorlik bilan a'zo bo'ladi."""
    global contacts_flood_wait_until
    queries_to_try = get_next_query_batch(batch_size=4)

    logger.debug(f"🎯 [Toshkent - Xorazm yo'nalishlari] {len(queries_to_try)} ta so'rov bo'yicha qidiruv boshlandi: {', '.join(queries_to_try)}")

    candidates = []
    seen_chat_ids = set()

    use_contacts = (time.time() >= contacts_flood_wait_until)
    for query in queries_to_try:
        chats_found = []
        if use_contacts:
            try:
                res = await client(functions.contacts.SearchRequest(q=query, limit=30))
                chats_found = getattr(res, "chats", [])
                await asyncio.sleep(2.0)
            except FloodWaitError as fwe:
                contacts_flood_wait_until = time.time() + fwe.seconds
                use_contacts = False
                logger.debug(f"ℹ️ Contacts qidiruvi vaqtinchalik cheklangan ({fwe.seconds}s), Global Messages qidiruviga o'tilmoqda...")

        if not chats_found:
            try:
                res = await client(functions.messages.SearchGlobalRequest(
                    q=query,
                    filter=InputMessagesFilterEmpty(),
                    min_date=None,
                    max_date=None,
                    offset_rate=0,
                    offset_peer=InputPeerEmpty(),
                    offset_id=0,
                    limit=20
                ))
                chats_found = getattr(res, "chats", [])
                await asyncio.sleep(2.0)
            except FloodWaitError as fwe:
                wait_mins = round(fwe.seconds / 60, 1)
                logger.warning(f"⏳ Telegram global qidiruvda FloodWait berdi: {fwe.seconds} soniya ({wait_mins} daqiqa).")
                await asyncio.sleep(min(fwe.seconds, 30))
                break
            except Exception as e:
                logger.error(f"Global qidiruvda xatolik ({query}): {e}")

        for chat in chats_found:
            is_group = False
            if isinstance(chat, Channel) and chat.megagroup:
                is_group = True
            elif isinstance(chat, Chat):
                is_group = True

            if not is_group:
                continue

            username = getattr(chat, "username", None)
            if chat.id in seen_chat_ids or database.is_group_saved(chat.id) or database.is_group_left(chat.id, username):
                continue

            if not is_relevant_group_title(chat.title):
                continue

            members = getattr(chat, "participants_count", 0) or 0
            # A'zolar soni kamida 50 ta bo'lishi shart (kichik aktiv pitak guruhlarini ham qamrab oladi)
            if members < 50:
                continue

            seen_chat_ids.add(chat.id)
            candidates.append((chat, members))

        # Agar yetarlicha nomzodlar topilgan bo'lsa, qidiruvni to'xtatib qo'shilishga o'tamiz
        if len(candidates) >= 5:
            break

    # Agar ushbu navbatdagi so'rovlarda yangi guruh chiqmasa, keyingi qidiruvda boshqa so'rovlar olinadi
    if not candidates:
        logger.debug("ℹ️ Ushbu so'rovlar bo'yicha yangi guruh topilmadi, keyingi so'rovlarga o'tilmoqda...")
        return

    # A'zosi ko'p guruhlarni birinchi o'ringa qo'yish
    candidates.sort(key=lambda x: x[1], reverse=True)

    joined_count = 0
    for chat, members in candidates:
        if joined_count >= config.GROUPS_PER_CYCLE:
            break

        if members < 50:
            logger.info(f"🚫 Guruhda a'zolar soni 50 tadan kam ({members} ta), qo'shilmaydi: {chat.title}")
            continue

        username = getattr(chat, "username", None)
        if database.is_group_left(chat.id, username):
            logger.info(f"🚫 Guruh qora ro'yxatda (avval chiqib ketilgan), qo'shilmaydi: {chat.title}")
            continue

        logger.info(f"Guruhga qo'shilmoqda: {chat.title} (@{username or 'yopiq'}) [A'zolar: {members}]")

        try:
            if username:
                await client(functions.channels.JoinChannelRequest(username))
            else:
                await client(functions.channels.JoinChannelRequest(chat))

            database.add_joined_group(chat.id, chat.title, username)
            database.increment_today_join_count()
            joined_count += 1

            # Guruh bildirishnomalarini darhol o'chirib qo'yish (Mute)
            await mute_peer(client, chat)

            logger.info(f"✅ Guruhga muvaffaqiyatli qo'shilindi va MUTE qilindi! ({joined_count}/{config.GROUPS_PER_CYCLE}): {chat.title} (A'zolar: {members})")

            # Adminga yangi guruh xabarini berish
            await notify_admin_about_joined_group(client, chat.title, username, chat.id, members, "Toshkent - Xorazm yo'nalishi")

            # Ketma-ket qo'shilishda Telegram limitiga tushmaslik uchun qisqa xavfsiz tanaffus (4 soniya)
            await asyncio.sleep(4)

        except UserAlreadyParticipantError:
            database.add_joined_group(chat.id, chat.title, username)
            await mute_peer(client, chat)
            logger.info(f"ℹ️ Akkaunt allaqachon bu guruh a'zosi: {chat.title} (MUTE qilindi)")
        except FloodWaitError as e:
            wait_mins = round(e.seconds / 60, 1)
            logger.warning(f"⏳ Telegram guruhga a'zo bo'lishga vaqtinchalik FloodWait berdi: {e.seconds} soniya ({wait_mins} daqiqa).")
            logger.info("ℹ️ Userbot mavjud guruhlardagi mijozlarni ushlashda to'xtovsiz davom etadi. Cheklov tugagach yangi guruhlarga qo'shilish davom etadi.")
            rem = e.seconds
            while rem > 0:
                step = min(60, rem)
                await asyncio.sleep(step)
                rem -= step
                if rem > 0:
                    logger.info(f"⏳ Telegram tanaffusi: yana {round(rem/60, 1)} daqiqa qoldi...")
            logger.info("✅ Telegram tanaffusi tugadi! Yangi guruhlarga a'zo bo'lish davom etadi.")
            break
        except RPCError as e:
            logger.warning(f"Guruhga qo'shilishda Telegram xatosi ({chat.title}): {e}")
            database.add_joined_group(chat.id, chat.title, username)


async def auto_join_scheduler(client):
    """Har 10 soniyada yangi guruhlarga tezkor a'zo bo'lib boruvchi fon jarayoni."""
    await asyncio.sleep(2)

    while True:
        try:
            if not client.is_connected():
                await asyncio.sleep(5)
                continue
            await find_and_join_groups(client)
            logger.debug(f"Tezkor qidiruv davom etmoqda: keyingi sikl {config.CYCLE_INTERVAL_SECONDS} soniyadan so'ng...")
            await asyncio.sleep(config.CYCLE_INTERVAL_SECONDS)
        except Exception as e:
            logger.error(f"Joiner scheduler xatosi: {e}")
            await asyncio.sleep(10)
