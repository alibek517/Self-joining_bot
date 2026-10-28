import sqlite3
import datetime
from typing import List, Tuple, Optional

DB_FILE = "taxi_system.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, timeout=60.0)
    try:
        conn.execute("PRAGMA busy_timeout = 60000;")
        conn.execute("PRAGMA synchronous = NORMAL;")
    except Exception:
        pass
    return conn

def init_db():
    # WAL rejimini faqat bir marta xavfsiz sozlash (agar OneDrive yoki tizim band bo'lsa xato bermasligi uchun)
    try:
        with sqlite3.connect(DB_FILE, timeout=60.0) as temp_conn:
            temp_conn.execute("PRAGMA journal_mode=WAL;")
            temp_conn.execute("PRAGMA synchronous = NORMAL;")
            temp_conn.execute("PRAGMA busy_timeout = 60000;")
    except Exception:
        pass

    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Akkaunt a'zo bo'lgan guruhlar jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                title TEXT,
                username TEXT,
                is_initial INTEGER DEFAULT 0,
                joined_at TEXT
            )
        """)
        
        # Qayta ishlanib yuborilgan xabarlar (takrorlanishni oldini olish)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seen_messages (
                msg_id INTEGER,
                chat_id INTEGER,
                created_at TEXT,
                PRIMARY KEY (msg_id, chat_id)
            )
        """)
        
        # Kunlik yangi guruhlarga qo'shilish hisobi
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_joins (
                join_date TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            )
        """)
        
        # Bot orqali kelgan buyurtmalar jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                full_name TEXT,
                username TEXT,
                phone TEXT,
                direction TEXT,
                district TEXT,
                passengers TEXT,
                comment TEXT,
                created_at TEXT
            )
        """)
        
        # Topilgan mijozlar xabarlari (Reply paytida lichkasiga yozish uchun)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_records (
                user_id INTEGER PRIMARY KEY,
                chat_id INTEGER,
                msg_id INTEGER,
                access_hash INTEGER DEFAULT 0,
                chat_access_hash INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        
        # Avtomatik yo'nalishlar bo'yicha yaratilgan drayver guruhlari
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auto_driver_groups (
                route_key TEXT PRIMARY KEY,
                group_id INTEGER,
                title TEXT,
                created_at TEXT
            )
        """)
        
        # Guruh ichidagi Forum Mavzulari (Topics)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forum_topics (
                chat_id INTEGER,
                route_key TEXT,
                topic_id INTEGER,
                title TEXT,
                created_at TEXT,
                PRIMARY KEY (chat_id, route_key)
            )
        """)

        # Chiqib ketilgan va qayta qo'shilmasligi shart bo'lgan guruhlar (Blacklist)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS left_groups (
                group_id INTEGER PRIMARY KEY,
                title TEXT,
                username TEXT,
                reason TEXT,
                left_at TEXT
            )
        """)
        
        conn.commit()

def save_lead_record(user_id: int, chat_id: int, msg_id: int, access_hash: int = 0, chat_access_hash: int = 0):
    now = datetime.datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO lead_records (user_id, chat_id, msg_id, access_hash, chat_access_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, chat_id, msg_id, access_hash or 0, chat_access_hash or 0, now))
        conn.commit()

def get_lead_record(user_id: int) -> Optional[Tuple[int, int, int, int]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id, msg_id, access_hash, chat_access_hash FROM lead_records WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return (row[0], row[1], row[2] or 0, row[3] or 0) if row else None

# --- Guruhlar bo'yicha funksiyalar ---

def is_initial_sync_done() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM groups WHERE is_initial = 1")
        count = cursor.fetchone()[0]
        return count > 0

def save_initial_groups(groups: List[Tuple[int, str, Optional[str]]]):
    """Dastlab mavjud bo'lgan guruhlarni bazaga saqlaydi (is_initial=1 qilib)"""
    now = datetime.datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        for gid, title, uname in groups:
            cursor.execute("""
                INSERT OR IGNORE INTO groups (group_id, title, username, is_initial, joined_at)
                VALUES (?, ?, ?, 1, ?)
            """, (gid, title, uname, now))
        conn.commit()

def normalize_group_id(gid: int) -> int:
    gid_str = str(gid)
    if gid_str.startswith("-100"):
        return int(gid_str[4:])
    elif gid_str.startswith("-"):
        return int(gid_str[1:])
    return abs(gid)

def is_group_saved(group_id: int) -> bool:
    norm = normalize_group_id(group_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM groups 
            WHERE group_id = ? OR group_id = ? OR group_id = ?
        """, (norm, -norm, -int(f"100{norm}")))
        return cursor.fetchone() is not None

def remove_group(group_id: int):
    norm = normalize_group_id(group_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM groups 
            WHERE group_id = ? OR group_id = ? OR group_id = ?
        """, (norm, -norm, -int(f"100{norm}")))
        conn.commit()

def add_left_group(group_id: int, title: str = "", username: Optional[str] = None, reason: str = ""):
    """Guruhni tark etilganlar (Blacklist) ro'yxatiga qo'shadi."""
    now = datetime.datetime.now().isoformat()
    norm = normalize_group_id(group_id)
    uname = username.lower().replace("@", "") if username else None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO left_groups (group_id, title, username, reason, left_at)
            VALUES (?, ?, ?, ?, ?)
        """, (norm, title, uname, reason, now))
        conn.commit()

def is_group_left(group_id: int, username: Optional[str] = None) -> bool:
    """Guruh avval tark etilganmi yoki qora ro'yxatdami tekshiradi (hech qachon qayta qo'shilmaslik uchun)."""
    norm = normalize_group_id(group_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM left_groups 
            WHERE group_id = ? OR group_id = ? OR group_id = ?
        """, (norm, -norm, -int(f"100{norm}")))
        if cursor.fetchone() is not None:
            return True
        if username:
            clean_uname = username.lower().replace("@", "")
            cursor.execute("SELECT 1 FROM left_groups WHERE LOWER(username) = ?", (clean_uname,))
            if cursor.fetchone() is not None:
                return True
        return False

def get_left_groups_count() -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM left_groups")
        return cursor.fetchone()[0]

def add_joined_group(group_id: int, title: str, username: Optional[str] = None):
    now = datetime.datetime.now().isoformat()
    norm = normalize_group_id(group_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO groups (group_id, title, username, is_initial, joined_at)
            VALUES (?, ?, ?, 0, ?)
        """, (norm, title, username, now))
        conn.commit()

def get_total_groups_count() -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM groups")
        return cursor.fetchone()[0]

def get_today_join_count() -> int:
    today = datetime.date.today().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count FROM daily_joins WHERE join_date = ?", (today,))
        row = cursor.fetchone()
        return row[0] if row else 0

def increment_today_join_count():
    today = datetime.date.today().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO daily_joins (join_date, count)
            VALUES (?, 1)
            ON CONFLICT(join_date) DO UPDATE SET count = count + 1
        """, (today,))
        conn.commit()

# --- Xabarlar dublikatini oldini olish ---

def is_message_seen(msg_id: int, chat_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM seen_messages WHERE msg_id = ? AND chat_id = ?", (msg_id, chat_id))
        return cursor.fetchone() is not None

def mark_message_seen(msg_id: int, chat_id: int):
    now = datetime.datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO seen_messages (msg_id, chat_id, created_at)
            VALUES (?, ?, ?)
        """, (msg_id, chat_id, now))
        conn.commit()

# --- Buyurtmalar ---

def save_order(user_id: int, full_name: str, username: Optional[str], phone: str, 
               direction: str, district: str, passengers: str, comment: str) -> int:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders (user_id, full_name, username, phone, direction, district, passengers, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, full_name, username, phone, direction, district, passengers, comment, now))
        conn.commit()
        return cursor.lastrowid

def get_user_last_phone(user_id: int) -> Optional[str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT phone FROM orders WHERE user_id = ? AND phone != '' ORDER BY id DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None


# --- Avtomatik yaratilgan drayver guruhlari ---

def save_auto_driver_group(route_key: str, group_id: int, title: str):
    now = datetime.datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO auto_driver_groups (route_key, group_id, title, created_at)
            VALUES (?, ?, ?, ?)
        """, (route_key, group_id, title, now))
        conn.commit()

def get_auto_driver_group(route_key: str) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT group_id FROM auto_driver_groups WHERE route_key = ?", (route_key,))
        row = cursor.fetchone()
        return row[0] if row else None

def get_all_auto_driver_groups() -> List[Tuple[str, int, str]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT route_key, group_id, title FROM auto_driver_groups")
        return cursor.fetchall()


# --- Guruh ichidagi Forum Mavzulari (Topics) ---

def save_forum_topic(chat_id: int, route_key: str, topic_id: int, title: str):
    now = datetime.datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO forum_topics (chat_id, route_key, topic_id, title, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (chat_id, route_key, topic_id, title, now))
        conn.commit()

def get_forum_topic(chat_id: int, route_key: str) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT topic_id FROM forum_topics WHERE chat_id = ? AND route_key = ?", (chat_id, route_key))
        row = cursor.fetchone()
        return row[0] if row else None

def get_all_forum_topics(chat_id: Optional[int] = None) -> List[Tuple[str, int, str]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if chat_id:
            cursor.execute("SELECT route_key, topic_id, title FROM forum_topics WHERE chat_id = ?", (chat_id,))
        else:
            cursor.execute("SELECT route_key, topic_id, title FROM forum_topics")
        return cursor.fetchall()


