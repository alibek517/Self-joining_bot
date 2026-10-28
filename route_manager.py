import asyncio
import logging
import os
import re
from typing import Optional, Tuple, List
from telethon import functions
from telethon.tl.types import (
    ChatAdminRights,
    InputChatUploadedPhoto
)
from telethon.tl.functions.channels import (
    CreateChannelRequest,
    EditAdminRequest,
    EditPhotoRequest,
    InviteToChannelRequest,
    ToggleForumRequest
)
from telethon.tl.functions.messages import CreateForumTopicRequest
from telethon.errors import RPCError
import config
import database
import bot

logger = logging.getLogger("RouteManager")
NON_FORUM_CHATS = set()

# O'zbekistonning barcha tuman va shaharlarini tegishli viloyatga biriktiruvchi xarita (Lotin va Kirill)
DISTRICT_MAP = {
    # Toshkent
    "toshkent": "toshkent", "tashkent": "toshkent", "тошкент": "toshkent", "ташкент": "toshkent",
    "chirchiq": "toshkent", "чирчиқ": "toshkent", "чирчик": "toshkent",
    "olmaliq": "toshkent", "олмалиқ": "toshkent", "алмалык": "toshkent",
    "angren": "toshkent", "ангрен": "toshkent",
    "yangiyol": "toshkent", "yangiyo'l": "toshkent", "янгийўл": "toshkent", "янгиюль": "toshkent",
    "bekobod": "toshkent", "бекобод": "toshkent",
    "parkent": "toshkent", "паркент": "toshkent",
    "bostonliq": "toshkent", "bo'stonliq": "toshkent", "бўстонлиқ": "toshkent", "газалкент": "toshkent",
    "qibray": "toshkent", "қибрай": "toshkent",
    "zangiota": "toshkent", "зангиота": "toshkent",
    "chinoz": "toshkent", "чиноз": "toshkent",
    "piskent": "toshkent", "пискент": "toshkent",
    "oqqorgon": "toshkent", "оққўрғон": "toshkent",

    # Xorazm
    "xorazm": "xorazm", "xarezm": "xorazm", "хоразм": "xorazm",
    "urganch": "xorazm", "urgench": "xorazm", "урганч": "xorazm", "ургенч": "xorazm",
    "xiva": "xorazm", "хива": "xorazm",
    "gurlan": "xorazm", "gurland": "xorazm", "гурлан": "xorazm", "гурланд": "xorazm",
    "shovot": "xorazm", "shavat": "xorazm", "шовот": "xorazm", "шават": "xorazm",
    "yangibozor": "xorazm", "yangi bozor": "xorazm", "янгибозор": "xorazm",
    "xonqa": "xorazm", "xonka": "xorazm", "хонқа": "xorazm", "хонка": "xorazm",
    "hazorasp": "xorazm", "xazorasp": "xorazm", "ҳазорасп": "xorazm", "хазорасп": "xorazm",
    "bogot": "xorazm", "bog'ot": "xorazm", "боғот": "xorazm", "богот": "xorazm",
    "qoshkopir": "xorazm", "qo'shko'pir": "xorazm", "қўшкўпир": "xorazm", "кошкупир": "xorazm",
    "pitnak": "xorazm", "питнақ": "xorazm", "питноқ": "xorazm",
    "tuproqqala": "xorazm", "тупроққалъа": "xorazm",
    "yangiariq": "xorazm", "янгиариқ": "xorazm",

    # Qoraqalpog'iston
    "nukus": "qoraqalpoq", "nokis": "qoraqalpoq", "нукус": "qoraqalpoq", "нокис": "qoraqalpoq",
    "qoraqalpoq": "qoraqalpoq", "qoraqalpogiston": "qoraqalpoq", "қорақалпоқ": "qoraqalpoq",
    "beruniy": "qoraqalpoq", "бируни": "qoraqalpoq", "беруний": "qoraqalpoq",
    "turtkul": "qoraqalpoq", "to'rtko'l": "qoraqalpoq", "тўрткўл": "qoraqalpoq", "торткул": "qoraqalpoq",
    "ellikqala": "qoraqalpoq", "элликқалъа": "qoraqalpoq",
    "xojayli": "qoraqalpoq", "xo'jayli": "qoraqalpoq", "хўжайли": "qoraqalpoq", "ходжейли": "qoraqalpoq",
    "mangit": "qoraqalpoq", "mang'it": "qoraqalpoq", "манғит": "qoraqalpoq", "мангит": "qoraqalpoq",
    "taxiatosh": "qoraqalpoq", "тахиатош": "qoraqalpoq",
    "qongirot": "qoraqalpoq", "qo'ng'irot": "qoraqalpoq", "қўнғирот": "qoraqalpoq", "kungrad": "qoraqalpoq", "кунград": "qoraqalpoq",
    "chimboy": "qoraqalpoq", "чимбой": "qoraqalpoq",
    "moynoq": "qoraqalpoq", "мўйноқ": "qoraqalpoq", "муйнак": "qoraqalpoq",
    "shumanay": "qoraqalpoq", "шуманай": "qoraqalpoq",
    "qonlikol": "qoraqalpoq", "қанликўл": "qoraqalpoq",
    "taxtakopir": "qoraqalpoq", "тахтакўпир": "qoraqalpoq",

    # Samarqand
    "samarqand": "samarqand", "samarkand": "samarqand", "самарқанд": "samarqand", "самарканд": "samarqand",
    "kattaqorgon": "samarqand", "kattaqo'rg'on": "samarqand", "каттақўрғон": "samarqand",
    "urgut": "samarqand", "ургут": "samarqand",
    "bulungur": "samarqand", "bulung'ur": "samarqand", "булунғур": "samarqand",
    "pastdargom": "samarqand", "пастдарғом": "samarqand",
    "paxtachi": "samarqand", "пахтачи": "samarqand",
    "narpay": "samarqand", "oqdaryo": "samarqand", "toyloq": "samarqand",
    "ishtixon": "samarqand", "иштихон": "samarqand",
    "jomboy": "samarqand", "жомбой": "samarqand",

    # Buxoro
    "buxoro": "buxoro", "buxara": "buxoro", "бухоро": "buxoro",
    "gijduvon": "buxoro", "g'ijduvon": "buxoro", "ғиждувон": "buxoro",
    "qorakol": "buxoro", "qorako'l": "buxoro", "қоракўл": "buxoro",
    "olot": "buxoro", "олот": "buxoro",
    "jondor": "buxoro", "жондор": "buxoro",
    "vobkent": "buxoro", "вобкент": "buxoro",
    "shofirkon": "buxoro", "шофиркон": "buxoro",
    "romitan": "buxoro", "ромитан": "buxoro",
    "kogon": "buxoro", "когон": "buxoro",

    # Qashqadaryo
    "qarshi": "qashqadaryo", "karshi": "qashqadaryo", "қарши": "qashqadaryo",
    "shahrisabz": "qashqadaryo", "shaxrisabz": "qashqadaryo", "шаҳрисабз": "qashqadaryo",
    "kitob": "qashqadaryo", "китоб": "qashqadaryo",
    "chiroqchi": "qashqadaryo", "чироқчи": "qashqadaryo",
    "koson": "qashqadaryo", "косон": "qashqadaryo",
    "muborak": "qashqadaryo", "муборак": "qashqadaryo",
    "yakkabog": "qashqadaryo", "яккабоғ": "qashqadaryo",
    "guzor": "qashqadaryo", "g'uzor": "qashqadaryo", "ғузор": "qashqadaryo",
    "qamashi": "qashqadaryo", "қамаши": "qashqadaryo",
    "qashqadaryo": "qashqadaryo", "қашқадарё": "qashqadaryo",

    # Surxondaryo
    "termiz": "surxondaryo", "термиз": "surxondaryo",
    "denov": "surxondaryo", "денов": "surxondaryo",
    "sherobod": "surxondaryo", "шеробод": "surxondaryo",
    "boysun": "surxondaryo", "бойсун": "surxondaryo",
    "qumqorgon": "surxondaryo", "қумқўрғон": "surxondaryo",
    "shorchi": "surxondaryo", "шўрчи": "surxondaryo",
    "sariosiyo": "surxondaryo", "сариосиё": "surxondaryo",
    "jarqorgon": "surxondaryo", "жарқўрғон": "surxondaryo",
    "surxondaryo": "surxondaryo", "сурхондарё": "surxondaryo",

    # Navoiy
    "navoiy": "navoiy", "navoi": "navoiy", "навоий": "navoiy",
    "zarafshon": "navoiy", "зарафшон": "navoiy",
    "karmana": "navoiy", "кармана": "navoiy",
    "qiziltepa": "navoiy", "қизилтепа": "navoiy",
    "uchquduq": "navoiy", "учқудуқ": "navoiy",
    "xatirchi": "navoiy", "хатирчи": "navoiy",

    # Jizzax
    "jizzax": "jizzax", "жиззах": "jizzax",
    "gallaorol": "jizzax", "g'allaorol": "jizzax", "ғаллаорол": "jizzax",
    "zomin": "jizzax", "зомин": "jizzax",
    "paxtakor": "jizzax", "пахтакор": "jizzax",
    "baxmal": "jizzax", "бахмал": "jizzax",

    # Sirdaryo
    "sirdaryo": "sirdaryo", "сирдарё": "sirdaryo",
    "guliston": "sirdaryo", "гулистон": "sirdaryo",
    "yangiyer": "sirdaryo", "янгиер": "sirdaryo",
    "shirin": "sirdaryo", "ширин": "sirdaryo",
    "boyovut": "sirdaryo", "боёвут": "sirdaryo",

    # Vodiy (Andijon, Namangan, Farg'ona)
    "andijon": "vodiy", "andijan": "vodiy", "андижон": "vodiy", "asaka": "vodiy", "шаҳрихон": "vodiy", "shahrixon": "vodiy",
    "namangan": "vodiy", "наманган": "vodiy", "chust": "vodiy", "чуст": "vodiy", "kosonsoy": "vodiy",
    "fargona": "vodiy", "fergana": "vodiy", "фарғона": "vodiy", "qoqon": "vodiy", "kokand": "vodiy", "қўқон": "vodiy",
    "margilon": "vodiy", "марғилон": "vodiy", "quva": "vodiy", "rishton": "vodiy", "vodiy": "vodiy", "водий": "vodiy"
}

REGION_NAMES_UZ = {
    "toshkent": "Toshkent",
    "xorazm": "Xorazm",
    "qoraqalpoq": "Qoraqalpog'iston",
    "samarqand": "Samarqand",
    "buxoro": "Buxoro",
    "qashqadaryo": "Qashqadaryo",
    "surxondaryo": "Surxondaryo",
    "navoiy": "Navoiy",
    "jizzax": "Jizzax",
    "sirdaryo": "Sirdaryo",
    "vodiy": "Vodiy"
}

def extract_regions_from_text(text: str, chat_title: str = "") -> List[str]:
    """Xabar va guruh nomidan barcha qatnashgan viloyatlarni tartib bilan ajratib oladi."""
    check_str = f"{text} {chat_title}".lower()
    found_regions = []
    
    # So'zlarni tekshirish
    words = re.findall(r"[a-zA-Zа-яА-Яʻʼ'‘]+", check_str)
    for w in words:
        clean_w = w.replace("'", "").replace("ʻ", "").replace("ʼ", "").replace("‘", "")
        # Avval to'liq so'zni tekshiramiz
        if clean_w in DISTRICT_MAP:
            reg = DISTRICT_MAP[clean_w]
            if reg not in found_regions:
                found_regions.append(reg)
            continue
        # Boshlanishini tekshirish (masalan: toshkentdan, samarqandga...)
        for kw, reg in DISTRICT_MAP.items():
            if clean_w.startswith(kw) and len(kw) >= 4:
                if reg not in found_regions:
                    found_regions.append(reg)
                break
                
    return found_regions


def get_route_key_and_title(text: str, chat_title: str = "") -> Tuple[Optional[str], Optional[str]]:
    """Xabardan yo'nalish kaliti (route_key) va chiroyli guruh nomini shakllantiradi."""
    regions = extract_regions_from_text(text, chat_title)
    
    if not regions:
        return None, None
        
    if len(regions) == 1:
        reg = regions[0]
        # Bitta viloyat ichidagi qatnov
        name = REGION_NAMES_UZ.get(reg, reg.capitalize())
        route_key = f"{reg}_ichki"
        title = f"🚕 {name} ichki Drivers"
        return route_key, title
        
    # Kamida 2 ta viloyat bor
    reg1, reg2 = regions[0], regions[1]
    
    # Bir xil yo'nalish bitta guruhga tushishi uchun alifbo tartibida birlashtirish
    sorted_regs = sorted([reg1, reg2])
    route_key = f"{sorted_regs[0]}_{sorted_regs[1]}"
    
    name1 = REGION_NAMES_UZ.get(sorted_regs[0], sorted_regs[0].capitalize())
    name2 = REGION_NAMES_UZ.get(sorted_regs[1], sorted_regs[1].capitalize())
    
    title = f"🚕 {name1} ⇄ {name2} Drivers"
    return route_key, title


def get_or_create_route_logo(route_key: str, group_title: str) -> str:
    """Har bir guruh uchun o'z nomi va yo'nalishiga mos, unikal stilli rasm qaytaradi yoki generatsiya qiladi."""
    logos_dir = os.path.join(os.path.dirname(__file__), "assets", "logos")
    os.makedirs(logos_dir, exist_ok=True)
    
    # 1. Agar oldindan tayyorlangan yuqori sifatli AI logotip bo'lsa -> darhol qaytarish
    specific_logo = os.path.join(logos_dir, f"{route_key}.jpg")
    if os.path.exists(specific_logo):
        return specific_logo

    # 2. Agar mavjud bo'lmasa -> Pillow orqali har xil rang, har xil stillar va guruh nomi bilan unikal logo yasash
    output_path = os.path.join(logos_dir, f"{route_key}.jpg")
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Unikal ranglar palitrasi (route_key xeshiga qarab har bir guruhga alohida still beradi)
        STYLE_PALETTES = [
            {"bg1": (15, 23, 42), "bg2": (30, 41, 59), "accent": (245, 158, 11), "badge": (217, 119, 6), "name": "Gold Amber"},
            {"bg1": (10, 25, 47), "bg2": (13, 71, 161), "accent": (0, 229, 255), "badge": (33, 150, 243), "name": "Cyber Cyan"},
            {"bg1": (24, 24, 27), "bg2": (63, 63, 70), "accent": (239, 68, 68), "badge": (185, 28, 28), "name": "Ruby Chrome"},
            {"bg1": (6, 78, 59), "bg2": (6, 95, 70), "accent": (250, 204, 21), "badge": (16, 185, 129), "name": "Emerald Gold"},
            {"bg1": (46, 16, 101), "bg2": (88, 28, 135), "accent": (244, 114, 182), "badge": (168, 85, 247), "name": "Neon Violet"},
            {"bg1": (67, 20, 7), "bg2": (124, 45, 18), "accent": (251, 146, 60), "badge": (234, 88, 12), "name": "Sunset Orange"}
        ]
        
        palette_idx = abs(hash(route_key)) % len(STYLE_PALETTES)
        pal = STYLE_PALETTES[palette_idx]
        
        width, height = 800, 800
        img = Image.new("RGB", (width, height), pal["bg1"])
        draw = ImageDraw.Draw(img)
        
        # Gradient fon chizish
        for y in range(height):
            ratio = y / height
            r = int(pal["bg1"][0] * (1 - ratio) + pal["bg2"][0] * ratio)
            g = int(pal["bg1"][1] * (1 - ratio) + pal["bg2"][1] * ratio)
            b = int(pal["bg1"][2] * (1 - ratio) + pal["bg2"][2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
            
        # Oltin/neon doiraviy ramka
        margin = 40
        draw.ellipse([margin, margin, width - margin, height - margin], outline=pal["accent"], width=12)
        draw.ellipse([margin + 20, margin + 20, width - margin - 20, height - margin - 20], outline=pal["badge"], width=4)
        
        # Markaziy Taxi belgisi (shashka)
        box_size = 40
        start_x, start_y = width // 2 - 80, height // 2 - 40
        for row in range(2):
            for col in range(4):
                color = pal["accent"] if (row + col) % 2 == 0 else (255, 255, 255)
                x0 = start_x + col * box_size
                y0 = start_y + row * box_size
                draw.rectangle([x0, y0, x0 + box_size, y0 + box_size], fill=color)
                
        # Guruh nomidagi matnlar
        clean_title = group_title.replace("🚕", "").replace("Drivers", "").strip()
        
        try:
            font_large = ImageFont.truetype("arial.ttf", 46)
            font_small = ImageFont.truetype("arial.ttf", 36)
            font_badge = ImageFont.truetype("arial.ttf", 30)
        except Exception:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_badge = ImageFont.load_default()
            
        # Yuqori sarlavha: TAXI
        draw.text((width // 2, 210), "TAXI DRIVERS", fill=pal["accent"], font=font_badge, anchor="mm")
        
        # O'rta-past: Guruh yo'nalishi (masalan: TOSHKENT ⇄ SAMARQAND)
        draw.text((width // 2, height // 2 + 120), clean_title.upper(), fill=(255, 255, 255), font=font_large, anchor="mm")
        
        # Pastki badge
        draw.rectangle([width // 2 - 180, height - 190, width // 2 + 180, height - 130], fill=pal["badge"])
        draw.text((width // 2, height - 160), "RASMIY GURUH", fill=(255, 255, 255), font=font_small, anchor="mm")
        
        img.save(output_path, quality=95)
        logger.info(f"🎨 Yangi guruh uchun unikal avatarka yaratildi: {output_path} (Stil: {pal['name']})")
        return output_path
        
    except Exception as e:
        logger.error(f"Avatarka yasashda xatolik: {e}")
        backup = os.path.join(logos_dir, "nukus_gurlan_urganch.jpg")
        return backup if os.path.exists(backup) else ""


_group_creation_lock = asyncio.Lock()
_topic_creation_lock = asyncio.Lock()

async def get_or_create_route_topic(client, text: str, chat_title: str = "") -> Tuple[int, Optional[int]]:
    """
    Xabar uchun mos haydovchilar guruhi va uning ichidagi MAVZU (Forum Topic) ni qaytaradi.
    Yangi yo'nalish bo'lsa yangi mavzu ochadi va bosh adminlarga feyk akkaunt orqali hisobot beradi.
    """
    # Barcha Toshkent - Xorazm buyurtmalari Asosiy Haydovchilar guruhiga yo'naltiriladi
    target_chat_id = config.DRIVERS_GROUP_ID

    if target_chat_id in NON_FORUM_CHATS:
        return target_chat_id, None

    route_key, group_title = get_route_key_and_title(text, chat_title)
    if not route_key:
        return target_chat_id, None

    # 1. Bazada mavjud mavzuni tekshirish (tezkor tekshiruv)
    existing_topic_id = database.get_forum_topic(target_chat_id, route_key)
    if existing_topic_id is not None:
        return target_chat_id, existing_topic_id

    # 2. Dublikat mavzular ochilmasligi uchun Lock
    async with _topic_creation_lock:
        existing_topic_id = database.get_forum_topic(target_chat_id, route_key)
        if existing_topic_id is not None:
            return target_chat_id, existing_topic_id

        topic_id = None

        # Bot orqali Forum mavzusi yaratish
        if bot.bot_instance:
            try:
                ft = await bot.bot_instance.create_forum_topic(chat_id=target_chat_id, name=group_title)
                topic_id = ft.message_thread_id
                logger.info(f"📌 Yangi Forum mavzusi ochildi (Bot orqali): '{group_title}' (ID: {topic_id})")
            except Exception as e:
                err_msg = str(e).lower()
                
                # Agar guruhda hali Topics (Mavzular) yoqilmagan bo'lsa, userbot orqali yoqishga urinish
                if "not a forum" in err_msg or "chat is not a forum" in err_msg:
                    try:
                        input_channel = await client.get_input_entity(target_chat_id)
                        await client(ToggleForumRequest(channel=input_channel, enabled=True, tabs=False))
                        logger.info(f"🔄 Guruhda Forum (Mavzular) rejimi muvaffaqiyatli yoqildi: {target_chat_id}")
                        await asyncio.sleep(1.0)
                        ft = await bot.bot_instance.create_forum_topic(chat_id=target_chat_id, name=group_title)
                        topic_id = ft.message_thread_id
                        logger.info(f"📌 Yangi Forum mavzusi ochildi (Qayta urinish): '{group_title}' (ID: {topic_id})")
                    except Exception:
                        NON_FORUM_CHATS.add(target_chat_id)
                else:
                    logger.debug(f"Bot orqali mavzu ochishda xatolik: {e}")

        # Agar bot ocholmasa va guruh forum bo'lmasa, userbot orqali urinish
        if topic_id is None and client and target_chat_id not in NON_FORUM_CHATS:
            try:
                import random
                input_peer = await client.get_input_entity(target_chat_id)
                res = await client(CreateForumTopicRequest(
                    peer=input_peer,
                    title=group_title,
                    random_id=random.randint(1, 2**60)
                ))
                topic_id = getattr(res, "id", None)
                if not topic_id and hasattr(res, "updates"):
                    for u in res.updates:
                        if hasattr(u, "message") and hasattr(u.message, "id"):
                            topic_id = u.message.id
                            break
                if topic_id:
                    logger.info(f"📌 Yangi Forum mavzusi ochildi (Userbot orqali): '{group_title}' (ID: {topic_id})")
            except Exception:
                NON_FORUM_CHATS.add(target_chat_id)

        # Agar mavzu muvaffaqiyatli ochilgan bo'lsa:
        if topic_id:
            database.save_forum_topic(target_chat_id, route_key, topic_id, group_title)

            # Bosh adminlarga feyk akkaunt (userbot) orqali hisobot yuborish
            all_topics = database.get_all_forum_topics(target_chat_id)
            topics_list = "\n".join([f"{i+1}. {t[2]}" for i, t in enumerate(all_topics)])
            report_msg = (
                f"🚕 <b>YANGI YO'NALISH MAVZUSI YARATILDI!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📍 <b>Mavzu nomi:</b> {group_title}\n"
                f"🆔 <b>Mavzu ID:</b> <code>{topic_id}</code>\n"
                f"👥 <b>Guruh ID:</b> <code>{target_chat_id}</code>\n\n"
                f"📊 <b>Jami ochilgan mavzular soni:</b> {len(all_topics)} ta\n"
                f"📋 <b>Barcha mavzular ro'yxati:</b>\n{topics_list}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━"
            )
            for aid in config.ADMIN_IDS:
                try:
                    await client.send_message(aid, report_msg, parse_mode="html")
                    logger.info(f"📨 Adminga ({aid}) yangi mavzu haqida hisobot userbot orqali yuborildi.")
                except Exception as ex:
                    logger.warning(f"Adminga ({aid}) hisobot yuborishda xatolik: {ex}")

        return target_chat_id, topic_id


async def get_or_create_driver_group(client, text: str, chat_title: str = "") -> int:
    """Xabar uchun mos drayver guruhini qaytaradi (Toshkent - Xorazm Asosiy guruhi)."""
    return config.DRIVERS_GROUP_ID
    async with _group_creation_lock:
        # Lock ichida qayta tekshirish (Double-checked locking)
        existing_gid = database.get_auto_driver_group(route_key)
        if existing_gid:
            return existing_gid

        # Yangi ochiladigan guruhlar soni 10 tadan oshmasligi kerak!
        all_auto_groups = database.get_all_auto_driver_groups()
        if len(all_auto_groups) >= config.MAX_AUTO_CREATED_GROUPS:
            logger.info(f"ℹ️ Yangi guruhlar soni 10 tadan oshmasligi kerak (hozirda: {len(all_auto_groups)}/{config.MAX_AUTO_CREATED_GROUPS}). Yangi guruh ochilmaydi, xabar asosiy guruhga yo'naltiriladi.")
            return config.DRIVERS_GROUP_ID
            
        # Yangi guruh yaratish kerak!
        logger.info(f"✨ Yangi yo'nalish aniqlandi ({route_key}). Userbot orqali yangi guruh ochilmoqda: {group_title}")
        
        try:
            created = await client(CreateChannelRequest(
                title=group_title,
                about=f"🚕 {group_title} — haydovchilar guruhi. Mijozlar buyurtmalari avtomatik yetkaziladi.",
                megagroup=True
            ))
            
            channel = created.chats[0]
            new_gid = int(f"-100{channel.id}")
            logger.info(f"🎉 Yangi superguruh yaratildi! ID: {new_gid}, Nomi: {group_title}")
            
            # 1. Rasm qo'yish (har bitta guruh uchun alohida rasm)
            avatar_path = get_or_create_route_logo(route_key, group_title)
            if os.path.exists(avatar_path):
                try:
                    uploaded_photo = await client.upload_file(avatar_path)
                    await client(EditPhotoRequest(channel, InputChatUploadedPhoto(uploaded_photo)))
                    logger.info(f"📸 Guruhga unikal rasm muvaffaqiyatli o'rnatildi: {group_title} ({avatar_path})")
                except Exception as e:
                    logger.warning(f"Guruhga rasm yuklashda xatolik: {e}")
                    
            # 2. To'liq adminlik huquqlari
            admin_rights = ChatAdminRights(
                change_info=True,
                post_messages=True,
                edit_messages=True,
                delete_messages=True,
                ban_users=True,
                invite_users=True,
                pin_messages=True,
                add_admins=True,
                anonymous=False,
                manage_call=True
            )
            
            # 3. Botni qo'shish va to'liq admin qilish
            if bot.bot_instance:
                try:
                    bot_info = await bot.bot_instance.get_me()
                    bot_user = await client.get_entity(bot_info.id)
                    await client(InviteToChannelRequest(channel, [bot_user]))
                    await client(EditAdminRequest(channel, bot_user, admin_rights, rank="Taxi Bot"))
                    logger.info(f"🤖 Bot ({bot_info.username}) guruhga qo'shildi va to'liq Admin huquqi berildi.")
                except Exception as be:
                    logger.warning(f"Botni guruhga qo'shishda xatolik: {be}")
                    
            # 4. Adminlarni qo'shish va ularga ham Bosh Adminlik berish
            for aid in config.ADMIN_IDS:
                try:
                    admin_ent = await client.get_entity(aid)
                    await client(InviteToChannelRequest(channel, [admin_ent]))
                    await client(EditAdminRequest(channel, admin_ent, admin_rights, rank="Bosh Admin"))
                    logger.info(f"👤 Admin ({aid}) guruhga qo'shildi va Bosh Admin huquqi berildi.")
                except Exception as ae:
                    logger.warning(f"Adminni ({aid}) guruhga qo'shishda xatolik: {ae}")
                    
            # 5. Bazaga va xotiraga saqlash
            database.save_auto_driver_group(route_key, new_gid, group_title)
            if new_gid not in config.ALL_DRIVERS_GROUP_IDS:
                config.ALL_DRIVERS_GROUP_IDS.append(new_gid)
                
            return new_gid
            
        except Exception as ex:
            logger.error(f"⚠️ Yangi guruh yaratishda xatolik: {ex}")
            return config.DRIVERS_GROUP_ID


async def set_nukus_group_photo_now(client):
    """Nukus-Gurlan-Urganch guruhiga (-1004337157604) hozir yaratilgan rasmni qo'yadi."""
    avatar_path = os.path.join(os.path.dirname(__file__), "assets", "nukus_gurlan_taxi.jpg")
    if not os.path.exists(avatar_path):
        logger.warning(f"Rasm topilmadi: {avatar_path}")
        return False
        
    gid = config.DRIVERS_LOCAL_GROUP_ID
    logger.info(f"📸 Nukus-Gurlan-Urganch guruhiga ({gid}) rasm yuklanmoqda...")
    try:
        peer = await client.get_entity(gid)
        uploaded = await client.upload_file(avatar_path)
        await client(EditPhotoRequest(peer, InputChatUploadedPhoto(uploaded)))
        logger.info("✅ Nukus-Gurlan-Urganch guruhiga rasm muvaffaqiyatli o'rnatildi!")
        return True
    except Exception as e:
        logger.error(f"Nukus guruhiga rasm yuklashda xatolik: {e}")
        return False
