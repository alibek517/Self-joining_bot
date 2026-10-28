import asyncio
import datetime
import logging
from telethon.tl.types import Channel, Chat
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.errors import FloodWaitError, RPCError
import config
import database

logger = logging.getLogger("GroupCleaner")

# Taksi mijoz faolligini bildiruvchi kalit belgilar (bu so'zlar bo'lsa guruh faol hisoblanadi)
ACTIVE_TAXI_KEYWORDS = [
    "odam", "adam", "kishi", "yo'lovchi", "yolovchi", "taksi", "taxi",
    "pochta", "poshta", "yuk", "bor", "bar", "kerak", "kk", "bormi",
    "ketamiz", "ketaman", "boramiz", "pitak", "reys", "mashina", "moshin",
    "одам", "адам", "киши", "йўловчи", "такси", "почта", "юк", "бор", "бар", "керак", "кк"
]

def is_protected_group(group_id: int) -> bool:
    """Haydovchilar guruhlaridan aslo chiqmaslik uchun himoya tekshiruvi."""
    for gid in config.ALL_DRIVERS_GROUP_IDS:
        if group_id == gid or str(abs(gid)) in str(group_id) or str(abs(group_id)) in str(abs(gid)):
            return True
    return False


async def clean_inactive_and_dead_groups(client, max_leave: int = 40) -> int:
    """Oxirgi xabar yozilganiga 1 haftadan ko'p bo'lgan yoki taksi yo'lovchilari yozmaydigan guruhlarni tark etadi."""
    logger.info("🧹 Noaktiv va o'lik guruhlarni tozalash jarayoni boshlandi...")
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    one_week_ago = now_utc - datetime.timedelta(days=7)
    
    dialogs = await client.get_dialogs()
    logger.info(f"Akkauntda jami {len(dialogs)} ta dialog mavjud.")
    
    left_count = 0
    checked_count = 0
    
    for d in reversed(dialogs):
        if left_count >= max_leave:
            break
            
        if not (d.is_group or d.is_channel):
            continue
            
        # Asosiy haydovchilar guruhlarini aslo tark etmaslik!
        if is_protected_group(d.id):
            continue
            
        checked_count += 1
        
        # 1. Oxirgi xabar vaqtini tekshirish
        last_msg_date = None
        if d.date:
            last_msg_date = d.date
            
        is_dead = False
        is_useless = False
        participants_count = getattr(d.entity, "participants_count", None)

        # 0. Taqiqlangan / chiqarib tashlangan yo'nalishlar (Gurlan-Guliston, Qarshi-Toshkent, Surxondaryo-Buxoro-Termiz)
        if config.is_excluded_group_title(d.title):
            is_useless = True
            reason = "Taqiqlangan yo'nalish (Gurlan-Guliston, Qarshi-Toshkent yoki Surxondaryo-Buxoro-Termiz)"
        # 1. Guruh a'zolari soni 100 tadan kam bo'lsa -> Darhol tark etish!
        elif participants_count is not None and participants_count < 100:
            is_useless = True
            reason = f"Guruh a'zolari soni 100 tadan kam ({participants_count} ta)"
        # 2. Agar oxirgi xabarning o'zi 7 kundan eski bo'lsa -> O'lik guruh!
        elif last_msg_date and last_msg_date < one_week_ago:
            days_inactive = (now_utc - last_msg_date).days
            is_dead = True
            reason = f"7 kundan ortiq ({days_inactive} kun) xabar yozilmagan"

        # Agar guruh o'lik yoki foydasiz bo'lsa -> Guruhdan chiqish
        if is_dead or is_useless:
            uname = getattr(d.entity, "username", None)
            logger.info(f"🚪 Guruhdan chiqilmoqda: '{d.title}' (ID: {d.id}) | Sabab: {reason}")
            try:
                if isinstance(d.entity, Channel):
                    await client(LeaveChannelRequest(d.entity))
                else:
                    await client.delete_dialog(d.entity)
                    
                database.add_left_group(d.id, d.title, uname, reason)
                database.remove_group(d.id)
                left_count += 1
                await asyncio.sleep(1.5)
            except FloodWaitError as fwe:
                logger.warning(f"⏳ Telegram FloodWait: {fwe.seconds} soniya.")
                break
            except RPCError as rpc:
                logger.warning(f"Guruhdan chiqishda xatolik ({d.title}): {rpc}")
                database.add_left_group(d.id, d.title, uname, f"{reason} | Xato: {rpc}")
                database.remove_group(d.id)
            except Exception as e:
                logger.error(f"Guruhdan chiqishda kutilmagan xatolik: {e}")

    logger.info(f"✅ Tozalash yakunlandi: {left_count} ta noaktiv/o'lik guruh tark etildi va yangi guruhlar uchun bo'sh joy ochildi!")
    return left_count


async def auto_cleaner_scheduler(client):
    """Guruhlar soni to'lib qolmasligi uchun har 2 soatda avtomatik tozalovchi foniy jarayon."""
    await asyncio.sleep(60)  # Startup dan 1 daqiqa o'tgach birinchi tekshiruv
    
    while True:
        try:
            if not client.is_connected():
                await asyncio.sleep(10)
                continue
                
            dialogs = await client.get_dialogs()
            groups_count = sum(1 for d in dialogs if (d.is_group or d.is_channel) and not is_protected_group(d.id))
            
            # Agar guruhlar soni 440 tadan oshsa yoki har 2 soatda profilaktik tozalash
            if groups_count >= 440:
                logger.info(f"⚠️ Akkaunt guruhlari soni {groups_count}/500 ga yetdi! Faol bo'lmagan guruhlar tozalanmoqda...")
                await clean_inactive_and_dead_groups(client, max_leave=50)
            else:
                # Oddiy profilaktik tozalash (har safar 10-15 tagacha eng noaktiv guruhlardan chiqish)
                await clean_inactive_and_dead_groups(client, max_leave=15)
                
            # Keyingi tekshiruv 2 soatdan so'ng (7200 soniya)
            await asyncio.sleep(7200)
            
        except Exception as e:
            logger.error(f"Auto cleaner xatosi: {e}")
            await asyncio.sleep(300)
