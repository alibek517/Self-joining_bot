import asyncio
import logging
import re
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat, User, InputPeerUser, InputPeerChannel
from telethon.errors import RPCError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import datetime
from telethon.tl.functions.account import UpdateNotifySettingsRequest
from telethon.tl.types import (
    InputNotifyPeer,
    InputPeerNotifySettings,
    InputNotifyChats,
    InputNotifyBroadcasts,
    InputNotifyUsers
)
import config
import database
import bot
import route_manager

logger = logging.getLogger("Userbot")

async def mute_peer(client, peer) -> bool:
    """Guruh, kanal yoki bot bildirishnomalarini (notification va so'rovnomalarni) butunlay o'chirib qo'yadi (MUTE)."""
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
        return True
    except Exception as e:
        logger.warning(f"Mute qilishda xatolik: {e}")
        return False

async def mute_all_groups_channels_and_bots(client):
    """
    1. Telegram hisobining umumiy sozlamalarida guruhlar, kanallar va botlar bildirishnomalarini butunlay o'chiradi (Global Mute).
    2. Akkauntdagi barcha mavjud guruhlar, kanallar va botlarni birma-bir MUTE qiladi.
    """
    logger.info("🔕 Akkauntdagi barcha guruhlar, kanallar va botlarni MUTE qilish boshlandi...")
    far_future = datetime.datetime(2038, 1, 1)
    silent_settings = InputPeerNotifySettings(
        mute_until=far_future,
        silent=True,
        show_previews=False
    )
    
    # 1. Global mute - yangi qo'shiladigan barcha guruhlar va kanallar standart jim (mute) bo'ladi
    for n_type in [InputNotifyChats(), InputNotifyBroadcasts(), InputNotifyUsers()]:
        try:
            await client(UpdateNotifySettingsRequest(peer=n_type, settings=silent_settings))
        except Exception:
            pass

    # 2. Mavjud dialoglarni birma-bir MUTE qilish
    muted_count = 0
    try:
        async for dialog in client.iter_dialogs():
            # Asosiy adminlar lichkasini mute qilmaymiz
            if dialog.is_user and dialog.id in config.ADMIN_IDS:
                continue

            entity = dialog.entity
            is_bot = getattr(entity, "bot", False)
            
            # Guruh, superguruh, kanal yoki bot bo'lsa -> MUTE!
            if dialog.is_group or dialog.is_channel or is_bot:
                try:
                    inp = await client.get_input_entity(dialog.input_entity)
                    await client(UpdateNotifySettingsRequest(
                        peer=InputNotifyPeer(inp),
                        settings=silent_settings
                    ))
                    muted_count += 1
                    await asyncio.sleep(0.02)
                except Exception:
                    pass
        logger.info(f"🔇 Barcha guruhlar, kanallar va botlar muvaffaqiyatli MUTE qilindi! Jami: {muted_count} ta.")
    except Exception as ex:
        logger.error(f"Dialoglarni mute qilishda xatolik: {ex}")

client = TelegramClient(
    config.SESSION_NAME,
    config.API_ID,
    config.API_HASH,
    connection_retries=None,
    retry_delay=2,
    auto_reconnect=True,
    flood_sleep_threshold=120,
    request_retries=10,
    timeout=45
)

_resolved_drivers_peers = {}  # {group_id: entity}
LEAD_ENTITIES = {}  # {user_id: entity} - Reply qilinganda to'g'ridan-to'g'ri lichkaga yozish uchun kesh

async def resolve_drivers_peer_once():
    """Startup paytida barcha dialoglarni yuklab, haydovchilar guruhlarini 100% aniqlaydi."""
    global _resolved_drivers_peers
    try:
        dialogs = await client.get_dialogs()
        dialog_ids = {d.id for d in dialogs}

        # Bazadagi avtomatik ochilgan guruhlarni faqat userbot a'zo bo'lsa yuklaymiz
        auto_groups = database.get_all_auto_driver_groups()
        for rk, agid, atitle in auto_groups:
            if agid in dialog_ids and agid not in config.ALL_DRIVERS_GROUP_IDS:
                config.ALL_DRIVERS_GROUP_IDS.append(agid)

        # Dialoglar xotiraga yuklanadi
        logger.info(f"Akkauntning {len(dialogs)} ta dialogi xotiraga yuklandi.")
        for gid in config.ALL_DRIVERS_GROUP_IDS:
            gid_clean = str(abs(gid)).replace("100", "")
            resolved = False
            for d in dialogs:
                d_id_str = str(abs(d.id)).replace("100", "")
                if gid == d.id or gid_clean == d_id_str or gid_clean in str(abs(d.id)):
                    _resolved_drivers_peers[gid] = d.input_entity
                    logger.info(f"✅ Haydovchilar guruhi aniqlandi: {d.title} (ID: {d.id})")
                    resolved = True
                    break
            if not resolved:
                for tid in [gid, int(f"-100{gid_clean}"), -int(gid_clean)]:
                    try:
                        ent = await client.get_entity(tid)
                        _resolved_drivers_peers[gid] = ent
                        logger.info(f"✅ Haydovchilar guruhi get_entity orqali aniqlandi: {getattr(ent, 'title', '')} (ID: {gid})")
                        resolved = True
                        break
                    except Exception:
                        continue

            if not resolved:
                logger.warning(f"⚠️ Userbot akkaunti haydovchilar guruhida (ID: {gid}) a'zo emas! Forward ishlashi uchun akkaunt ushbu guruhda bo'lishi kerak.")
    except Exception as ex:
        logger.error(f"Guruhlarni aniqlashda xatolik: {ex}")


async def sync_initial_groups():
    """Akkauntda hozir a'zo bo'lgan guruhlarni bazaga saqlaydi."""
    if database.is_initial_sync_done():
        logger.info("Akkauntning dastlabki guruhlari allaqachon ro'yxatga olingan.")
        return

    logger.info("Akkauntning mavjud guruhlari ro'yxatga olinmoqda...")
    initial_list = []
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                uname = getattr(dialog.entity, "username", None)
                initial_list.append((dialog.id, dialog.title, uname))
        
        database.save_initial_groups(initial_list)
        logger.info(f"✅ Akkauntda mavjud {len(initial_list)} ta guruh bazaga saqlandi.")
    except Exception as e:
        logger.error(f"Dastlabki guruhlarni olishda xatolik: {e}")


@client.on(events.NewMessage(incoming=True))
async def group_message_watcher(event):
    """Barcha guruhlardagi yangi xabarlarni kuzatadi va Toshkent-Xorazm taxi buyurtmalarini ushlaydi."""
    try:
        await _process_group_message(event)
    except Exception as ge:
        logger.error(f"group_message_watcher da kutilmagan xatolik: {ge}", exc_info=True)


async def _process_group_message(event):
    if not event.is_group:
        return

    # Haydovchilar guruhlaridagi xabarlarni chetlab o'tish
    for d_gid in config.ALL_DRIVERS_GROUP_IDS:
        if event.chat_id == d_gid or str(abs(d_gid)) in str(event.chat_id):
            return

    # Dublikat xabarlarni tekshirish
    if database.is_message_seen(event.id, event.chat_id):
        return
    database.mark_message_seen(event.id, event.chat_id)

    text = event.raw_text or ""
    if not text:
        return

    chat = None
    try:
        chat = await event.get_chat()
    except Exception:
        pass
    chat_title = getattr(chat, "title", "Guruh") if chat else "Guruh"
    chat_username = getattr(chat, "username", None) if chat else None

    if not config.is_taxi_lead(text, chat_title):
        return

    # Foydalanuvchi ma'lumotlarini olish
    sender = None
    try:
        sender = await event.get_sender()
    except Exception:
        sender = None

    if sender is None and event.sender_id:
        try:
            sender = await client.get_entity(event.sender_id)
        except Exception:
            pass

    # Botlar va reklama avtopost hisoblarini chetlab o'tish
    if sender:
        if getattr(sender, "bot", False):
            return
        s_uname = (getattr(sender, "username", "") or "").lower()
        if s_uname.endswith("bot"):
            return
        s_fname = (getattr(sender, "first_name", "") or getattr(sender, "title", "") or "").lower()
        if any(w in s_fname for w in ["avto post", "autopost", "avtopost", "reklama"]):
            return

    # Guruhdagi xabarga to'g'ridan-to'g'ri havola
    if chat_username:
        message_link = f"https://t.me/{chat_username}/{event.id}"
    else:
        clean_cid = str(event.chat_id).replace("-100", "").replace("-", "")
        message_link = f"https://t.me/c/{clean_cid}/{event.id}"

    raw_sender_id = getattr(sender, "id", None) or event.sender_id
    if not raw_sender_id and getattr(event, "from_id", None):
        raw_sender_id = getattr(event.from_id, "user_id", None) or getattr(event.from_id, "channel_id", None)

    sender_id_str = str(raw_sender_id) if raw_sender_id else "Noma'lum"

    # Mijoz entitysini keshga va bazaga saqlash (reply qilinganda lichkaga yozish uchun)
    input_sender = None
    try:
        input_sender = await event.get_input_sender()
    except Exception:
        input_sender = None

    input_chat = None
    try:
        input_chat = await event.get_input_chat()
    except Exception:
        input_chat = None

    sender_access_hash = getattr(input_sender, "access_hash", 0) or 0
    chat_access_hash = getattr(input_chat, "access_hash", 0) or 0
    if not sender_access_hash and sender:
        sender_access_hash = getattr(sender, "access_hash", 0) or 0
    if not chat_access_hash and getattr(event, "chat", None):
        chat_access_hash = getattr(event.chat, "access_hash", 0) or 0

    if raw_sender_id:
        try:
            raw_id_int = int(raw_sender_id)
            if input_sender:
                LEAD_ENTITIES[raw_id_int] = input_sender
            elif sender:
                LEAD_ENTITIES[raw_id_int] = sender
            database.save_lead_record(raw_id_int, event.chat_id, event.id, sender_access_hash, chat_access_hash)
        except (ValueError, TypeError):
            pass

    first_name = getattr(sender, "first_name", "") or ""
    last_name = getattr(sender, "last_name", "") or ""
    full_name = f"{first_name} {last_name}".strip()
    if not full_name and sender:
        full_name = getattr(sender, "title", "") or ""
    if not full_name:
        full_name = f"Foydalanuvchi ({sender_id_str})"

    username = getattr(sender, "username", None)
    username_str = f"@{username}" if username else "Yo'q"

    # Mijoz profiliga (lichkaga) to'g'ri havola
    is_valid_user = False
    try:
        if raw_sender_id and int(raw_sender_id) > 0:
            is_valid_user = True
    except (ValueError, TypeError):
        pass

    if username:
        user_contact_url = f"https://t.me/{username}"
    elif is_valid_user:
        user_contact_url = f"tg://user?id={raw_sender_id}"
    else:
        user_contact_url = message_link

    phone_found = config.extract_phone(text)
    if not phone_found:
        profile_phone = getattr(sender, "phone", None)
        if profile_phone:
            profile_phone = str(profile_phone).strip()
            if not profile_phone.startswith("+"):
                profile_phone = f"+{profile_phone}"
            phone_str = f"<code>{profile_phone}</code> (Profil raqami)"
        else:
            phone_str = "Matnda ko'rsatilmagan"
    else:
        phone_str = f"<code>{phone_found}</code>"

    # Xavfsiz HTML formatlash (maxsus belgilar buzib qo'ymasligi uchun)
    import html
    safe_title = html.escape(chat_title)
    safe_name = html.escape(full_name)
    safe_user = html.escape(username_str)
    safe_text = html.escape(text)

    # Yuboruvchi ismini formatlash
    if username:
        sender_mention = f'<a href="https://t.me/{username}">{safe_name}</a>'
    else:
        sender_mention = safe_name

    # Haydovchilar guruhiga xabar matni (HTML formatda)
    alert_lines = [
        "🚕 <b>YANGI BUYURTMA / MIJOZ TOPILDI!</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"📍 <b>Guruh:</b> {safe_title}",
        f"👤 <b>Yuboruvchi:</b> {sender_mention} ({safe_user})",
        f"🆔 <b>Telegram ID:</b> <code>{sender_id_str}</code>",
        f"📞 <b>Telefon:</b> {phone_str}\n",
        f"💬 <b>Xabar matni:</b>\n<i>{safe_text}</i>",
        "━━━━━━━━━━━━━━━━━━━━━━"
    ]
    if username:
        alert_lines.append(f'👉 <a href="https://t.me/{username}">Mijoz profiliga o\'tish (Lichkasi)</a>')
    else:
        alert_lines.append("💡 <i>(Mijoz profiliga o'tish uchun yuqoridagi forward qilingan xabarga bosing)</i>")
    alert_lines.append("✍️ <i>(Lichkasiga xabar yozish uchun ushbu xabarga «Reply / Javob» qiling)</i>")
    alert_lines.append(f'🔗 <a href="{message_link}">Guruhdagi asl xabarni ochish</a>')

    alert_text = "\n".join(alert_lines)

    # Tugmalar (Inline keyboard)
    buttons = []
    if username:
        buttons.append([InlineKeyboardButton(text="💬 Mijozga yozish (Lichka)", url=f"https://t.me/{username}")])
    buttons.append([InlineKeyboardButton(text="↗️ Guruhdagi asl xabarni ochish", url=message_link)])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    # Mos haydovchilar guruhi va uning ichidagi MAVZU (Topic) ni aniqlash
    target_main_gid, topic_id = await route_manager.get_or_create_route_topic(client, text, chat_title)
    if target_main_gid == config.DRIVERS_VODIY_GROUP_ID:
        target_label = f"Vodiy guruhi ({config.DRIVERS_VODIY_GROUP_ID})"
    elif target_main_gid == config.DRIVERS_LOCAL_GROUP_ID:
        target_label = f"Nukus-Gurlan-Urganch guruhi ({config.DRIVERS_LOCAL_GROUP_ID})"
    elif target_main_gid == config.DRIVERS_GROUP_ID:
        target_label = f"Voha guruhi ({config.DRIVERS_GROUP_ID})"
    else:
        target_label = f"Haydovchilar guruhi ({target_main_gid})"

    if topic_id:
        target_label += f" [Mavzu ID: {topic_id}]"

    # Haydovchilar guruhi peer'ini aniqlash
    target_userbot_peer = _resolved_drivers_peers.get(target_main_gid)
    if target_userbot_peer is None:
        gid_clean = str(abs(target_main_gid)).replace("100", "")
        for tid in [target_main_gid, int(f"-100{gid_clean}"), -int(gid_clean)]:
            try:
                target_userbot_peer = await client.get_entity(tid)
                _resolved_drivers_peers[target_main_gid] = target_userbot_peer
                break
            except Exception:
                pass

    # 1-QADAM: Mijozning asl xabarini haydovchilar guruhiga FORWARD qilish
    if target_userbot_peer is not None:
        forwarded = False
        if topic_id:
            try:
                await client.forward_messages(target_userbot_peer, event.message, reply_to=topic_id)
                forwarded = True
                logger.info(f"✅ Mijoz asl xabari haydovchilar guruhiga FORWARD qilindi! ({target_label} - Mavzu: {topic_id})")
            except Exception as fwd_err:
                logger.warning(f"Mavzuga forward qilishda xatolik ({fwd_err}), asosiy guruhga forward qilinmoqda...")

        if not forwarded:
            try:
                await client.forward_messages(target_userbot_peer, event.message)
                logger.info(f"✅ Mijoz asl xabari haydovchilar guruhiga (asosiy) FORWARD qilindi! ({target_label})")
            except Exception as ex:
                logger.warning(f"Asl xabarni forward qilishda xatolik: {ex}")
    else:
        logger.warning(f"⚠️ Forward qilinmadi: Userbot akkaunti haydovchilar guruhida ({target_main_gid}) yo'q!")

    # 2-QADAM: Bot orqali to'liq ma'lumot kartasini yuborish
    sent_via_bot = False
    if bot.bot_instance:
        target_group_ids = [
            target_main_gid,
            int(f"-100{abs(target_main_gid)}"),
            int(str(target_main_gid).replace("-100", "-"))
        ]
        
        for gid in target_group_ids:
            sent_this = False
            if topic_id:
                try:
                    await bot.bot_instance.send_message(
                        chat_id=gid,
                        text=alert_text,
                        reply_markup=kb,
                        parse_mode="HTML",
                        message_thread_id=topic_id
                    )
                    sent_this = True
                    sent_via_bot = True
                    logger.info(f"✅ Lead bot orqali {target_label}ga yetkazildi! (Mavzu: {topic_id})")
                    break
                except Exception as b_err:
                    logger.warning(f"Bot orqali mavzuga yuborishda xatolik ({gid}): {b_err}, asosiy guruhga yuborilmoqda...")

            if not sent_this:
                try:
                    await bot.bot_instance.send_message(
                        chat_id=gid,
                        text=alert_text,
                        reply_markup=kb,
                        parse_mode="HTML"
                    )
                    sent_via_bot = True
                    logger.info(f"✅ Lead bot orqali {target_label}ga yetkazildi! (Guruh: {chat_title})")
                    break
                except Exception as e:
                    logger.warning(f"Bot orqali yuborishda xatolik ({gid}): {e}")

    # Agar bot orqali yuborilmagan bo'lsa, userbot orqali matn shaklida yetkazamiz
    if not sent_via_bot and target_userbot_peer is not None:
        sent_userbot = False
        if topic_id:
            try:
                await client.send_message(target_userbot_peer, alert_text, parse_mode="html", link_preview=False, reply_to=topic_id)
                sent_userbot = True
                logger.info(f"✅ Lead userbot orqali matn shaklida mavzuga yetkazildi! ({target_label})")
            except Exception as ue1:
                logger.warning(f"Userbot orqali mavzuga yuborishda xatolik: {ue1}")

        if not sent_userbot:
            try:
                await client.send_message(target_userbot_peer, alert_text, parse_mode="html", link_preview=False)
                logger.info(f"✅ Lead userbot orqali matn shaklida yetkazildi! ({target_label})")
            except Exception as e:
                logger.error(f"Haydovchilar guruhiga matn yuborishda xatolik: {e}")


# --- Akkaunt buyruqlari ---

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.id$"))
async def my_id_cmd(event):
    """Guruhda .id yozsangiz, o'sha guruhning haqiqiy ID sini chiqaradi."""
    await event.edit(f"🆔 **Ushbu chat ID si:** `{event.chat_id}`")


@client.on(events.NewMessage(outgoing=True, pattern=r"^\.ping$"))
async def ping_cmd(event):
    await event.edit("🏓 **Userbot faol ishlamoqda!**")


@client.on(events.NewMessage(outgoing=True, pattern=r"^\.setpic$"))
async def setpic_cmd(event):
    """Guruhda .setpic yozsangiz, o'sha guruhga generatsiya qilingan taxi logotipini o'rnatadi."""
    import os
    from telethon.tl.functions.channels import EditPhotoRequest
    from telethon.tl.types import InputChatUploadedPhoto
    avatar_path = os.path.join(os.path.dirname(__file__), "assets", "nukus_gurlan_taxi.jpg")
    if not os.path.exists(avatar_path):
        await event.edit("⚠️ Rasm fayli topilmadi!")
        return
    try:
        await event.edit("📸 Guruh rasmi o'rnatilmoqda...")
        uploaded = await client.upload_file(avatar_path)
        chat_input = await event.get_input_chat()
        await client(EditPhotoRequest(chat_input, InputChatUploadedPhoto(uploaded)))
        await event.edit("✅ **Guruh rasmi muvaffaqiyatli o'rnatildi!**")
    except Exception as e:
        await event.edit(f"❌ **Xatolik yuz berdi:** {e}")


@client.on(events.NewMessage(outgoing=True, pattern=r"^\.status$"))
async def status_cmd(event):
    today_joins = database.get_today_join_count()
    await event.edit(
        f"📊 **Userbot Holati:**\n\n"
        f"✅ Bugun qo'shilgan yangi taxi guruhlar: **{today_joins}/3**\n"
        f"🚕 Voha guruhi: `{config.DRIVERS_GROUP_ID}`\n"
        f"🚕 Vodiy guruhi: `{config.DRIVERS_VODIY_GROUP_ID}`\n"
        f"🚕 Nukus-Gurlan-Urganch guruhi: `{config.DRIVERS_LOCAL_GROUP_ID}`\n"
        f"📡 Guruhlarni nazorat qilish: **Faol**"
    )


@client.on(events.NewMessage(outgoing=True, pattern=r"^\.clean$"))
async def clean_cmd(event):
    """Noaktiv va o'lik guruhlarni tozalash buyrug'i."""
    await event.edit("🧹 **Noaktiv va o'lik guruhlarni tekshirish va tozalash boshlandi...**")
    try:
        import group_cleaner
        left = await group_cleaner.clean_inactive_and_dead_groups(client, max_leave=40)
        await event.edit(f"✅ **Tozalash yakunlandi!**\n🚪 Chiqilgan noaktiv guruhlar soni: **{left} ta**\n✨ Yangi faol guruhlar uchun bo'sh joy ochildi.")
    except Exception as e:
        await event.edit(f"❌ **Tozalashda xatolik:** {e}")


# --- Haydovchilar guruhida Reply qilinganda mijoz lichkasiga yozish ---

@client.on(events.NewMessage())
async def handle_drivers_group_reply(event):
    """Haydovchilar guruhida lead xabariga reply qilib biror narsa yozilsa, face akkount mijoz lichkasiga yozadi."""
    if not event.is_group or not event.is_reply:
        return

    # Barcha haydovchilar guruhlarini (Xorazm va Vodiy) tekshirish
    is_drivers_group = any(
        event.chat_id == d_gid or str(abs(d_gid)) in str(event.chat_id)
        for d_gid in config.ALL_DRIVERS_GROUP_IDS
    )
    if not is_drivers_group:
        return

    try:
        reply_msg = await event.get_reply_message()
        if not reply_msg:
            return

        target_peer = None
        customer_name = "Mijoz"

        # 1. Forward qilingan xabar bo'lsa
        if reply_msg.forward:
            if reply_msg.forward.sender_id:
                target_peer = reply_msg.forward.sender_id
            elif reply_msg.forward.from_id:
                target_peer = getattr(reply_msg.forward.from_id, "user_id", None)

        # 2. Xabar matnidan Telegram ID qidirish (Bot yoki userbot yuborgan alert)
        msg_text = reply_msg.raw_text or reply_msg.text or ""
        if not target_peer and msg_text:
            # Telegram ID: 123456789
            id_match = re.search(r"Telegram ID:\s*([0-9]{5,15})", msg_text)
            if id_match:
                target_peer = int(id_match.group(1))

        # 3. Agar ID topilmasa, tg://user?id= havola qidirish
        if not target_peer and msg_text:
            tg_link_match = re.search(r"tg://user\?id=([0-9]{5,15})", msg_text)
            if tg_link_match:
                target_peer = int(tg_link_match.group(1))

        # 4. Agar hali ham topilmasa, @username qidirish (botnikidan tashqari)
        if not target_peer and msg_text:
            u_matches = re.findall(r"@([a-zA-Z0-9_]{4,})", msg_text)
            for u in u_matches:
                if "bot" not in u.lower():
                    target_peer = u
                    break

        if not target_peer:
            return

        # Mijozning to'liq entity ob'ektini olish (access_hash bilan)
        target_entity = None

        # Agar reply to'g'ridan-to'g'ri forward qilingan xabarga berilgan bo'lsa
        if reply_msg.forward:
            try:
                target_entity = await reply_msg.get_input_sender()
            except Exception:
                pass

        if not target_entity and isinstance(target_peer, int):
            # 1. Bazadan (lead_records) guruh va xabar ma'lumotlarini olish
            db_record = database.get_lead_record(target_peer)
            if db_record:
                c_id, m_id, a_hash, c_a_hash = db_record
                try:
                    clean_cid = int(str(c_id).replace("-100", "").replace("-", ""))
                    input_channel = InputPeerChannel(channel_id=clean_cid, access_hash=c_a_hash) if c_a_hash else clean_cid

                    # A. Guruh a'zolaridan to'liq User entity olish (GetParticipantRequest - to'liq access_hash bilan)
                    from telethon.tl.functions.channels import GetParticipantRequest
                    p_res = await client(GetParticipantRequest(channel=input_channel, participant=target_peer))
                    if p_res and getattr(p_res, "users", None):
                        target_entity = p_res.users[0]
                except Exception as ex:
                    logger.debug(f"GetParticipantRequest orqali entity olinmadi: {ex}")

                # B. Guruhdagi asl xabardan entity olish
                if not target_entity:
                    try:
                        clean_cid = int(str(c_id).replace("-100", "").replace("-", ""))
                        input_channel = InputPeerChannel(channel_id=clean_cid, access_hash=c_a_hash) if c_a_hash else clean_cid
                        orig = await client.get_messages(input_channel, ids=m_id)
                        if orig:
                            target_entity = await orig.get_input_sender() or await orig.get_sender()
                    except Exception as ex:
                        logger.debug(f"Bazadagi xabardan entity olishda xatolik: {ex}")

            # 2. LEAD_ENTITIES keshidan tekshirish
            if not target_entity and target_peer in LEAD_ENTITIES:
                target_entity = LEAD_ENTITIES[target_peer]

            # 3. Telethon get_entity / get_input_entity
            if not target_entity:
                try:
                    target_entity = await client.get_entity(target_peer)
                except Exception:
                    try:
                        target_entity = await client.get_input_entity(target_peer)
                    except Exception:
                        pass

        # 4. Xabar ichidagi havolalardan qidirish
        if not target_entity:
            candidate_urls = []
            if reply_msg.entities:
                for ent in reply_msg.entities:
                    url = getattr(ent, "url", None)
                    if url:
                        candidate_urls.append(url)
            if msg_text:
                candidate_urls.append(msg_text)

            for u_str in candidate_urls:
                link_match = re.search(r"t\.me/(?:c/(\d+)|([a-zA-Z0-9_]+))/(\d+)", u_str)
                if link_match:
                    cid_raw, uname, mid = link_match.groups()
                    try:
                        chat_peer = int(f"-100{cid_raw}") if cid_raw else uname
                        orig_msg = await client.get_messages(chat_peer, ids=int(mid))
                        if orig_msg:
                            target_entity = await orig_msg.get_input_sender() or await orig_msg.get_sender()
                            if target_entity:
                                break
                    except Exception as ex:
                        logger.debug(f"Entities dagi havola orqali entity olishda xatolik: {ex}")

        if not target_entity:
            warn_msg = await event.reply("⚠️ Ushbu mijoz profili maxfiy yoki topilmadi. Iltimos, forward qilingan xabar ustiga bosib yoki «↗️ Guruhdagi asl xabarni ochish» orqali bog'laning.")
            await asyncio.sleep(10)
            try:
                await warn_msg.delete()
            except Exception:
                pass
            return

        # Haydovchi reply qilib yozgan matnni olish
        reply_user_text = (event.raw_text or event.text or "").strip()

        # Agar oddiy belgilash bo'lsa (., +, ok, olaman va h.k.) standart taklif yuboriladi
        if not reply_user_text or reply_user_text.lower() in [".", "+", "ok", "xa", "ha", "olaman", "men", "gaplash"]:
            message_to_customer = (
                "Assalomu Alaykum! Taxi kerak deb yozibsiz, +998975002086 shu raqamga bog'laning."
            )
        else:
            # Agar haydovchi o'z taklifini (narx, telefon) yozgan bo'lsa, o'sha matn yuboriladi
            message_to_customer = reply_user_text

        try:
            # Face akkount orqali mijoz lichkasiga yuborish
            await client.send_message(target_entity, message_to_customer)
            logger.info(f"✅ Face akkount mijozga ({target_peer}) xabar yubordi.")

            # Guruhdagi reply qilgan odamga tasdiq
            confirm_msg = await event.reply("✅ Face akkount orqali mijoz lichkasiga xabar yuborildi (+998975002086)!")
            await asyncio.sleep(8)
            try:
                await confirm_msg.delete()
            except Exception:
                pass

        except RPCError as rpc_err:
            logger.warning(f"Mijoz ({target_peer}) lichkasiga yozishda RPC xatolik: {rpc_err}")
            err_str = str(rpc_err).lower()
            if any(k in err_str for k in ["invalid peer", "peer_id_invalid", "privacy", "restricted"]):
                user_msg = "⚠️ Ushbu mijoz Telegram sozlamalarida lichkaga yozishni cheklab qo'ygan (maxfiy). Iltimos, forward qilingan xabar ustiga bosib yoki guruhdagi asl xabari orqali bog'laning."
            elif "flood" in err_str:
                user_msg = "⚠️ Telegram limiti tufayli biroz kutib qayta urinib ko'ring."
            else:
                user_msg = f"⚠️ Mijoz lichkasiga yozib bo'lmadi: {rpc_err}"

            err_msg = await event.reply(user_msg)
            await asyncio.sleep(12)
            try:
                await err_msg.delete()
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Mijoz lichkasiga yozishda umumiy xatolik: {e}")


# --- Mijozdan kelgan javoblarni Adminlarga forward qilish ---

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handle_private_customer_reply(event):
    """Mijoz Face akkount lichkasiga yozsa, darhol ADMIN_IDS ga forward qiladi."""
    sender = await event.get_sender()
    if getattr(sender, "bot", False):
        return

    sender_id = event.sender_id
    # Agar xabar adminning o'zidan bo'lsa, forward qilmaymiz
    if sender_id in config.ADMIN_IDS:
        return

    sender_name = getattr(sender, "first_name", "") or ""
    last_name = getattr(sender, "last_name", "") or ""
    full_name = f"{sender_name} {last_name}".strip() or "Mijoz"
    username = getattr(sender, "username", None)
    username_str = f"@{username}" if username else "Yo'q"

    if username:
        profile_link = f"👉 <a href='https://t.me/{username}'>Mijoz profiliga o'tish</a>\n"
    else:
        profile_link = "💡 <i>(Mijoz profiliga o'tish uchun quyidagi forward qilingan xabarga bosing)</i>\n"

    alert_header = (
        f"📩 <b>MIJOZDAN JAVOB KELDI!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Yuboruvchi:</b> {full_name} ({username_str})\n"
        f"🆔 <b>Telegram ID:</b> <code>{sender_id}</code>\n"
        f"{profile_link}"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⬇️ <i>Mijoz yozgan xabar quyida:</i>"
    )

    for admin_id in config.ADMIN_IDS:
        try:
            await client.send_message(admin_id, alert_header, parse_mode="html")
            await client.forward_messages(admin_id, event.message)
            logger.info(f"✅ Mijoz xabari adminga ({admin_id}) forward qilindi.")
        except Exception as e:
            logger.warning(f"Adminga ({admin_id}) forward qilishda xatolik: {e}")


@client.on(events.NewMessage(outgoing=True, pattern=r"^\.muteall$"))
async def manual_mute_all_cmd(event):
    """Feyk akkauntdan istalgan chatda .muteall deb yozilsa, barcha guruh, kanal va botlarni mute qiladi."""
    await event.edit("🔕 **Barcha guruhlar, kanallar va botlar MUTE qilinmoqda...**")
    await mute_all_groups_channels_and_bots(client)
    await event.edit("✅ **Barcha guruhlar, kanallar va botlar butunlay MUTE qilindi!**\nSo'rovnomalar va bildirishnomalar endi bezovta qilmaydi.")


