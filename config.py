import os
import re
from dotenv import load_dotenv, set_key

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

API_ID_RAW = os.getenv("API_ID", "39546630").strip()
API_HASH = os.getenv("API_HASH", "64da72bc284091ed1449582bb13abcb6").strip()
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "+998335800514").strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

RAW_DRIVERS_GROUP_ID = os.getenv("DRIVERS_GROUP_ID", "-5551747003").strip()
try:
    DRIVERS_GROUP_ID = int(RAW_DRIVERS_GROUP_ID)
except ValueError:
    DRIVERS_GROUP_ID = -5551747003

RAW_DRIVERS_VODIY_GROUP_ID = os.getenv("DRIVERS_VODIY_GROUP_ID", "-5532619599").strip()
try:
    DRIVERS_VODIY_GROUP_ID = int(RAW_DRIVERS_VODIY_GROUP_ID)
except ValueError:
    DRIVERS_VODIY_GROUP_ID = -5532619599

RAW_DRIVERS_LOCAL_GROUP_ID = os.getenv("DRIVERS_LOCAL_GROUP_ID", "-1004337157604").strip()
try:
    DRIVERS_LOCAL_GROUP_ID = int(RAW_DRIVERS_LOCAL_GROUP_ID)
except ValueError:
    DRIVERS_LOCAL_GROUP_ID = -1004337157604

ALL_DRIVERS_GROUP_IDS = [DRIVERS_GROUP_ID, DRIVERS_VODIY_GROUP_ID, DRIVERS_LOCAL_GROUP_ID]

ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "7748145808,8092817993").strip()
ADMIN_IDS = []
for aid in ADMIN_IDS_RAW.split(","):
    aid = aid.strip()
    if aid.isdigit():
        ADMIN_IDS.append(int(aid))
if not ADMIN_IDS:
    ADMIN_IDS = [7748145808, 8092817993]

ADMIN_ID = ADMIN_IDS[0]

# Guruhlarga xavfsiz va barqaror qo'shilish tezligi: har 10 soniyada yangi sikl
GROUPS_PER_CYCLE = 3
CYCLE_INTERVAL_SECONDS = 10

# Yangi ochiladigan drayver guruhlarining maksimal soni: 10 tadan oshmasin
MAX_AUTO_CREATED_GROUPS = 10

API_ID = int(API_ID_RAW)
SESSION_NAME = "userbot_session"

def update_drivers_group_id(new_id: int):
    """Haydovchilar guruhi ID sini xotirada va .env faylida yangilaydi."""
    global DRIVERS_GROUP_ID
    DRIVERS_GROUP_ID = new_id
    try:
        set_key(ENV_PATH, "DRIVERS_GROUP_ID", str(new_id))
    except Exception:
        try:
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open(ENV_PATH, "w", encoding="utf-8") as f:
                found = False
                for line in lines:
                    if line.startswith("DRIVERS_GROUP_ID="):
                        f.write(f"DRIVERS_GROUP_ID={new_id}\n")
                        found = True
                    else:
                        f.write(line)
                if not found:
                    f.write(f"\nDRIVERS_GROUP_ID={new_id}\n")
        except Exception:
            pass

# =====================================================================
# USTUVOR YO'NALISHLAR: TOSHKENT - XORAZM (FAQAT VA FAQAT SHU YO'NALISH)
# =====================================================================
TIER_TOSHKENT_XORAZM = [
    # 1. Toshkent - Xorazm asosiy
    "Toshkent Xorazm taxi", "Xorazm Toshkent taxi", "Тошкент Хоразм такси", "Хоразм Тошкент такси",
    "Toshkent Xorazm taksi", "Xorazm Toshkent taksi", "Toshkent Xorazm poputi", "Xorazm Toshkent poputi",
    "Toshkent Xorazm pitak", "Xorazm Toshkent pitak", "Toshkent Xorazm", "Xorazm Toshkent",
    "Тошкент Хоразм", "Хоразм Тошкент", "Toshkent Xorazm pochta", "Xorazm Toshkent pochta",
    "Toshkent Xorazm qatnov", "Xorazm Toshkent qatnov", "Toshkent Xorazm reys", "Xorazm Toshkent reys",
    "Toshkent Xorazm kirekash", "Xorazm Toshkent kirekash", "Tashkent Khorezm taxi", "Khorezm Tashkent taxi",
    "Toshkent Xorazm haydovchilar", "Xorazm Toshkent haydovchilar", "Toshkent Xorazm passajir", "Xorazm Toshkent passajir",

    # 2. Toshkent - Urganch (Urganch - Toshkent)
    "Toshkent Urganch taxi", "Urganch Toshkent taxi", "Тошкент Урганч такси", "Урганч Тошкент такси",
    "Toshkent Urganch taksi", "Urganch Toshkent taksi", "Toshkent Urganch poputi", "Urganch Toshkent poputi",
    "Toshkent Urganch pitak", "Urganch Toshkent pitak", "Toshkent Urganch", "Urganch Toshkent",
    "Тошкент Урганч", "Урганч Тошкент", "Tashkent Urgench taxi", "Urgench Tashkent taxi",
    "Toshkent Urganch pochta", "Urganch Toshkent pochta", "Toshkent Urganch qatnov", "Urganch Toshkent qatnov",
    "Toshkent Urganch reys", "Urganch Toshkent reys", "Toshkent Urganch haydovchilar", "Urganch Toshkent haydovchilar",
    "Urganch Toshkent passajir", "Toshkent Urganch passajir", "Urgench Tashkent", "Tashkent Urgench",

    # 3. Toshkent - Xiva (Xiva - Toshkent)
    "Toshkent Xiva taxi", "Xiva Toshkent taxi", "Тошкент Хива такси", "Хива Тошкент такси",
    "Toshkent Xiva taksi", "Xiva Toshkent taksi", "Toshkent Xiva", "Xiva Toshkent",
    "Toshkent Xiva poputi", "Xiva Toshkent poputi", "Toshkent Xiva pitak", "Xiva Toshkent pitak",
    "Toshkent Xiva pochta", "Xiva Toshkent pochta", "Toshkent Xiva qatnov", "Xiva Toshkent qatnov",

    # 4. Toshkent - Gurlan (Gurlan - Toshkent)
    "Toshkent Gurlan taxi", "Gurlan Toshkent taxi", "Тошкент Гурлан такси", "Гурлан Тошкент такси",
    "Toshkent Gurlan taksi", "Gurlan Toshkent taksi", "Toshkent Gurlan", "Gurlan Toshkent",
    "Toshkent Gurlan poputi", "Gurlan Toshkent poputi", "Toshkent Gurlan pitak", "Gurlan Toshkent pitak",
    "Toshkent Gurlan pochta", "Gurlan Toshkent pochta",

    # 5. Toshkent - Shovot (Shovot - Toshkent)
    "Toshkent Shovot taxi", "Shovot Toshkent taxi", "Тошкент Шовот такси", "Шовот Тошкент такси",
    "Toshkent Shovot taksi", "Shovot Toshkent taksi", "Toshkent Shovot poputi", "Shovot Toshkent poputi",
    "Toshkent Shovot pitak", "Shovot Toshkent pitak", "Toshkent Shovot pochta", "Shovot Toshkent pochta",

    # 6. Toshkent - Hazorasp (Hazorasp - Toshkent)
    "Toshkent Hazorasp taxi", "Hazorasp Toshkent taxi", "Тошкент Ҳазорасп такси", "Ҳазорасп Тошкент такси",
    "Toshkent Hazorasp taksi", "Hazorasp Toshkent taksi", "Toshkent Hazorasp", "Hazorasp Toshkent",
    "Toshkent Hazorasp poputi", "Hazorasp Toshkent poputi", "Toshkent Hazorasp pitak",

    # 7. Toshkent - Xonqa (Xonqa - Toshkent)
    "Toshkent Xonqa taxi", "Xonqa Toshkent taxi", "Тошкент Хонқа такси", "Хонқа Тошкент такси",
    "Toshkent Xonqa taksi", "Xonqa Toshkent taksi", "Toshkent Xonqa", "Xonqa Toshkent",

    # 8. Toshkent - Qoshkopir, Bogot, Yangibozor, Pitnak, Yangiariq
    "Toshkent Qoshkopir taxi", "Qoshkopir Toshkent taxi", "Тошкент Қўшкўпир такси", "Қўшкўпир Тошкент такси",
    "Toshkent Bogot taxi", "Bogot Toshkent taxi", "Тошкент Боғот такси", "Боғот Тошкент такси",
    "Toshkent Yangibozor taxi", "Yangibozor Toshkent taxi", "Тошкент Янгибозор такси", "Янгибозор Тошкент такси",
    "Toshkent Pitnak taxi", "Pitnak Toshkent taxi", "Toshkent Yangiariq taxi", "Yangiariq Toshkent taxi",

    # 9. Xorazm umumiy taksi va pitak guruhlari
    "Xorazm taksi", "Xorazm taxi", "Хоразм такси", "Xorazm pitak", "Хоразм питак",
    "Urganch taksi", "Urganch taxi", "Урганч такси", "Urganch pitak", "Урганч питак",
    "Xorazm poputi", "Urganch poputi", "Xorazm pochta", "Urganch pochta",
    "Xiva taksi", "Gurlan taksi", "Shovot taksi", "Hazorasp taksi", "Xonqa taksi"
]

# Hozirda faqat va faqat Toshkent - Xorazm yo'nalishlari qidiriladi
SEARCH_QUERIES = TIER_TOSHKENT_XORAZM

# O'zbekistonning barcha viloyat/shahar/tumanlari (Lotin va Kirill)
LOCATIONS = [
    # Toshkent
    "toshkent", "tashkent", "chirchiq", "olmaliq", "yangiyol", "bekobod", "parkent", "piskent",
    "тошкент", "ташкент", "чирчиқ", "олмалиқ", "янгийўл", "бекобод", "паркент",
    # Xorazm
    "xorazm", "xarezm", "urganch", "xiva", "hazorasp", "xazorasp", "shovot", "gurlan",
    "xonqa", "bogot", "bog'ot", "qoshkopir", "qo'shko'pir", "yangibozor", "yangi bozor", "pitnak", "tuproqqala",
    "хоразм", "урганч", "хива", "ҳазорасп", "хазорасп", "шовот", "гурлан", "хонқа", "хонка", "боғот", "богот",
    "қўшкўпир", "кошкупир", "янгибозор", "янги бозор", "питнақ", "питноқ", "тупроққалъа", "янгиариқ", "yangiariq",
    # Qoraqalpog'iston
    "mangit", "mang'it", "nukus", "beruniy", "turtkul", "to'rtko'l", "ellikqala", "xojayli",
    "xo'jayli", "qongirot", "qo'ng'irot", "chimboy", "moynoq", "shumanay", "qonlikol", "nokis",
    "манғит", "мангит", "нукус", "нокис", "беруний", "бируни", "тўрткўл", "торткул", "элликқалъа", "хўжайли", "ходжейли", "қўнғирот", "чимбой", "тахиатош", "taxiatosh",
    # Buxoro
    "buxoro", "buxara", "gijduvon", "g'ijduvon", "qorakol", "qorako'l", "olot", "jondor",
    "vobkent", "shofirkon", "romitan", "peshku", "qorovulbozor",
    "бухоро", "ғиждувон", "қоракўл", "олот", "жондор", "вобкент", "шофиркон",
    # Samarqand
    "samarqand", "samarkand", "kattaqorgon", "kattaqo'rg'on", "bulungur", "bulung'ur", "urgut",
    "pastdargom", "paxtachi", "narpay", "oqdaryo", "toyloq", "ishtixon", "qo'shrabot",
    "самарқанд", "каттақўрғон", "булунғур", "ургут", "пастдарғом", "пахтачи",
    # Navoiy
    "navoiy", "navoi", "zarafshon", "karmana", "qiziltepa", "uchquduq", "xatirchi", "nurota",
    "навоий", "зарафшон", "кармана", "қизилтепа", "учқудуқ", "хатирчи",
    # Jizzax va Sirdaryo
    "jizzax", "gallaorol", "g'allaorol", "zomin", "paxtakor", "forish", "baxmal", "zarbdor",
    "sirdaryo", "guliston", "yangiyer", "shirin", "boyovut", "baxt",
    "жиззах", "ғаллаорол", "зомин", "сирдарё", "гулистон", "янгиер",
    # Andijon
    "andijon", "andijan", "xonobod", "qorasuv", "qorgontepa", "qo'rg'ontepa", "jalaquduq",
    "asaka", "shahrixon", "paxtaobod", "marhamat", "oltinkol", "boz", "buloqboshi", "izboskan",
    "андижон", "хонобод", "қорасув", "қўрғонтепа", "жалақудуқ", "асака", "шаҳрихон",
    # Namangan
    "namangan", "chust", "pop", "kosonsoy", "uchqorgon", "toraqorgon", "chortoq", "yangiqorgon",
    "наманган", "чуст", "поп", "косонсой", "учқўрғон", "тўрақўрғон", "чортоқ",
    # Farg'ona
    "fargona", "fergana", "margilon", "qoqon", "kokand", "quva", "quvasoy", "rishton",
    "oltiariq", "bogdod", "uchkoprik", "beshariq", "yazyavon",
    "фарғона", "марғилон", "қўқон", "қува", "қувасой", "риштон", "олтиариқ",
    # Qashqadaryo
    "qarshi", "karshi", "shahrisabz", "kitob", "chiroqchi", "koson", "nishon", "kasbi",
    "muborak", "yakkabog", "guzor", "dehkonobod", "qamashi",
    "қарши", "шаҳрисабз", "китоб", "чироқчи", "косон", "муборак", "яккабоғ", "ғузор",
    # Surxondaryo
    "termiz", "denov", "sherobod", "boysun", "qumqorgon", "shorchi", "sariosiyo", "jarqorgon",
    "термиз", "денов", "шеробод", "бойсун", "қумқўрғон", "шўрчи", "сариосиё",
    # Umumiy
    "vodiy", "водий", "voha", "воҳа"
]

# FAQAT YO'LOVCHI / MIJOZGA XOS SIGNALLAR (Lotin va Kirill)
PASSENGER_PATTERNS = [
    # Odam / kishi bor
    r"\b(?:odam|odom|adam|kishi|yo[\'ʻʼ]?lovchi|одам|одом|адам|киши|йўловчи)\s+(?:bor|bar|бор|бар)\b",
    r"\b\d+\s*(?:ta|та)?\s*(?:odam|odom|adam|kishi|одам|киши)\s*(?:bor|bar|бор|бар|ketamiz|кетамиз|bormi|борми)\b",
    r"\b\d+\s*(?:ta|та)\s*(?:odam|odom|adam|kishi|одам|киши)\b",
    # Pochta / yuk bor
    r"\b(?:pochta|poshta|pochto|yuk|sumka|hujjat|pasilka|почта|пошта|почто|юк|сумка|посылка|ҳужжат)\s+(?:bor|бор|bormi|борми)\b",
    r"\b(?:pochta|poshta|почта|пошта)\s+(?:oladigan|оладиган)\s+(?:bormi|bor|борми|бор)\b",
    # Ketaman / boraman (faqat shaxsiy birlikda: ketaman, boraman, ketmoqchiman)
    r"\b(?:ketaman|boraman|ketmoqchiman|кетмоқчиман|кетаман|бораман)\b",
    # Taksi / mashina kerak / bormi
    r"\b(?:taxi|taksi|moshina|mashina|moshin|такси|мошина|машина|мошин)\s+(?:kerak|garak|bormi|bormikan|bormakan|kk|k-k|keremi|керак|гарак|борми|бормикин|бормакан|кк|к-к)\b",
    r"\b(?:bormi|bormikan|bormakan|борми|бормикин)\s+(?:taxi|taksi|moshina|mashina|moshin|такси|мошина|машина|мошин)\b",
    # Pitak bormi
    r"\b(?:pitak|питак)\s+(?:bormi|борми|qayerda|қаерда)\b",
    # Kim bor / kim ketadi
    r"\b(?:kim\s+bor|kim\s+ketadi|bormi\??|bormikin|ким\s+бор|ким\s+кетади|бормикин)\b",
    # Olib ketasizmi / ketadigan bormi
    r"\b(?:ol[i]?b\s+ketasizmi|opketasizmi|olib\s+ketadigan\s+bormi|олиб\s+кетасизми|олиб\s+кетадиган\s+борми)\b",
    r"\b(?:ketadigan|кетган)\s+(?:bormi|bor|борми|бор)\b",
    r"\bsaloni?\s+(?:olamiz|qancha|nechpul|қанча|нечпул)\b"
]

# HAYDOVCHILARNING REKLAMA PATTERNLARI (MUTLAQO RAD ETILADI - LOTIN VA KIRILL)
DRIVER_PATTERNS = [
    # Moshina bor / mashinada (faqat agar savol bo'lmasa! masalan 'moshina bormi' rad etilmaydi)
    r"(?:moshin[a-z]*|mashin[a-z]*|мошин[а-я]*|машин[а-я]*)\s*[:\.\-]?\s*(?:bor\b(?!\s*(?:mi|mikan|makan))|бор\b(?!\s*(?:ми|микан|макан))|tayyor|тайёр|toza|тоза|yaxshi|яхши)",
    r"(?:moshin[a-z]*da|mashin[a-z]*da|мошинда|машинда)\b",
    # Mashina modellari (barcha turlari va shevalari)
    r"(?:cobalt|kobalt|jentra|gentra|jentir|gentir|trekker|tracker|malibu|lasetti|lacetti|damas|nexia|onix|monza|spark|matiz|k\s*i\s*a|kia|byd)[a-z]*",
    r"(?:кобальт|кобильт|коблт|кабальт|каболт|коболт|жентра|жентир|жентира|жентиро|ласетти|ласети|дамас|нексия|некся|оникс|трекер|трекир|малибу|киа|бйд|спарк|матиз|монза)[а-я]*",
    # Shaharga ketamiz / yuramiz / chiqamiz (haydovchilar eloni: URGANCH KETAMIZ va h.k.)
    r"(?<!(?:bor|bar|бор|бар)\s)(?<!\d\s)(?<!ta\s)(?<!та\s)\b(?:ketami[zs]|yurami[zs]|chiqami[zs]|borami[zs]|jurami[zs]|кетами[зс]|юрами[зс]|чиками[зс]|чиқами[зс]|борами[зс]|журами[зс]|йурами[зс])\b(?!\s*(?:bormi|bor\?|борми))",
    # Srochni / to'lsa ketamiz
    r"\b(?:srochni|srochno|srochna|срочно|срошни|срошний|срочна)\b",
    # Haydovchilar jo'nash jadvali (ERTAGA 06:00 DA SAMARQANDGA KETAMIZ, soat 6 - 6 yarimda ketamiz va h.k.)
    r"\b(?:ertaga|bugun|soat|ertalab|kechki|kechga|obid|obed|эртага|бугун|соат|эрталаб|кечки|кечга|обед)\s*(?:soat\s*)?\d{1,2}(?:[:\.]\d{2})?(?:\s*[-–\s]\s*\d{1,2}(?:[:\.]\d{2})?)?\s*(?:yarim[a-z]*|ярим[а-я]*|da|да|ga|га|lar[a-z]*|лар[а-я]*)?[\s\S]*?\b(?:yurami[zs]|ketami[zs]|chiqami[zs]|borami[zs]|jurami[zs]|юрами[зс]|кетами[зс]|чиками[зс]|чиқами[зс]|борами[зс]|журами[зс]|йурами[зс])\b",
    # Ko'p kishi ketaman degan haydovchilar (2 KISHI ... KETAMAN, 3 ODAM ... YURAMAN)
    r"\b[2-8]\s*(?:ta\s*)?(?:kishi|odam|joy|mesta|киши|одам|жой|места)\b[\s\S]*?\b(?:ketaman|yuraman|chiqaman|кетаман|юраман|чиқаман)\b",
    # Qatnaymiz / reys / har kuni / murojaat uchun / sifatli va arzon
    r"\b(?:qatnaymi[zs]|gatnaymi[zs]|қатнайми[зс]|катнайми[зс]|гатнайми[зс]|qatnaydi|қатнайди)\b",
    r"\b(?:har\s+kuni|xar\s+kuni|ҳар\s+куни|хар\s+куни|har\s+kungi|ҳар\s+кунги)\b",
    r"\b(?:reys|reysi|reyslar|рейс|рейси|рейслар)\b",
    r"(?:murojaat|murojat|мурожаат|мурожат)\s+(?:uchun|qiling|қилинг|учун)",
    r"\b(?:istalgan\s+vaqtda|har\s+vaqtda|любой\s+ва[қк]тда|любой\s+пайтда|24\s*soat|24\s*соат|24/7)\b",
    r"(?:arzon|sifatli|ishonchli|арзон|сифатли|ишончли)\s+(?:va\s+)?(?:arzon|sifatli|ishonchli|арзон|сифатли|ишончли|xizmat|хизмат)",
    r"\b(?:tel|тел)\s*(?:qilinglar[a-z]*|килинглар[а-я]*|қилинглар[а-я]*|клингlar[а-я]*|килилар[а-я]*|қилингизлар|килингизлар)\b",
    # Odam kerak / olamiz / kam
    r"(?:odam|odom|adam|kishi|yo[\'ʻʼ]?lovchi|одам|одом|адам|киши|йўловчи)\s+(?:kerak|garak|karak|gerak|olami[zs]|olamz|kk|керак|гарак|карак|олами[зс]|кк)",
    r"\d+\s*(?:ta|та|\.)?\s*(?:odam|odom|adam|kishi|yo[\'ʻʼ]?lovchi|одам|одом|адам|киши)?\s*(?:kerak|garak|karak|gerak|olami[zs]|olamz|kam|kk|керак|карак|олами[зс]|кам|кк)",
    # Kam odam / joy kam qoldi
    r"\b(?:\d+|bitta|ikkita|uchta|to[\'ʻʼ]?rtta|битта|иккита|учта|тўртта)\s*(?:ta|та|\.)?\s*(?:kam|кам)\b",
    r"(?:kam|joy|кам|жой)\s*(?:qoldi|қолди)",
    # Pochta / yuk olamiz (pochtayam, yuk olamis...)
    r"(?:pocht[ao][a-z]*|posht[ao][a-z]*|yuk[a-z]*|почт[ао][а-я]*|пошт[ао][а-я]*|юк[а-я]*)\s*(?:yam|ham|xam|ям|ҳам|хам)?\s*(?:olami[zs]|olamz|olaman|yetkazami[zs]|b[o|u]lsa[m]?|opketami[zs]|xizmati|олами[зс]|оломан|етказами[зс]|б[о|ў]лса|опкетами[зс])",
    r"(?:пошталар|почталар)\s*олами[зс]",
    r"(?:ishonchli\s+pocht[ao]|ишончли\s+почта)",
    # Olib ketamiz / alib ketamiz / olip ketaman / getamiz (barcha shevalar: alib, alip, olib, olip)
    r"(?:[оа]ли[бп]|[оа]л[бп]|op|ob|оп|об|al[i]?[bp]|ol[i]?[bp])\s*(?:ketam[a-z]*|getam[a-z]*|beram[a-z]*|кет[а-я]*|гет[а-я]*|бер[а-я]*)",
    r"(?:opketaman|opketami[zs]|опкетаман|опкетами[зс]|обкетаман|обкетами[зс])",
    # Pochta / pocta / adam / ketuvchi bo'lsa (barcha shevalar: bulsa, buso, busa, бусо, булса, болса, боса...)
    r"(?:pocht[ao][a-z]*|posht[ao][a-z]*|poct[ao][a-z]*|yuk[a-z]*|odam|odom|adam|kishi|ketuvchi[a-z]*|yo[\'ʻʼ]?lovchi[a-z]*|klient[a-z]*|mijoz[a-z]*|почт[ао][а-я]*|пошт[ао][а-я]*|поцт[ао][а-я]*|юк[а-я]*|одам|одом|адам|киши|кетувчи[а-я]*|й[уў]ловчи[а-я]*|клиент[а-я]*|мижоз[а-я]*)\s*(?:b[u|o]lsa[m]?|b[u|o]s[ao]|б[у|о]лса[м]?|б[у|о]со|б[о|у]са|болса)",
    r"(?:b[u|o]lsa[m]?|b[u|o]s[ao]|б[у|о]лса[м]?|б[у|о]со|б[о|у]са|болса)\s+(?:[оа]ли[бп]|op|ob|оп|об|ketami[zs]|ketaman|кетами[зс]|кетаман|al[i]?[bp]|ol[i]?[bp])",
    r"(?:adam|odam|odom|kishi|адам|одам|одом|киши)\s+(?:pocht[ao]|posht[ao]|poct[ao]|почт[ао]|пошт[ао]|поцт[ао])",
    r"(?:kuday\s*kalese|quday\s*qalese|кудай\s*калесе|кудай\s*каласа)",
    r"(?:olaman|оломан|оламан)\b",
    # Manzildan manzilgacha
    r"(?:manzil(?:dan)?\s+(?:manzilgacha|yetkazamiz|olib)|манзилдан\s+манзилгача)",
    # Qulayliklar va sharoitlar
    r"(?:conditsioner|konditsioner|kandior|kondior|kanditsaner|kandisaner|кондиционер|кандитсанер|кандиционер)",
    r"(?:wifi|wfi|vayfay|вайфай)",
    r"(?:komfort|konfort|comfort|lux|lyuks|комфорт|камфорт|люкс)",
    r"(?:тонировка|круговая\s+тонировка|опытный\s+водитель|хорошая\s+музыка|приятная\s+атмосфера)",
    # Joy / orindiq / mesta
    r"(?:mesta|joy|orindiq|места|жой)\s+(?:bo[\'ʻʼ]?sh|bosh|bor|бўш|буш|бор)",
    r"(?:том\s*багаж|клик\s*бор|кликбор)",
    # Ayol / xotin-qiz bor (haydovchilar ayol yo'lovchilarni jalb qilish uchun yozadi) - emojilar va belgilar bilan ham
    r"(?:ayol|xotin[\s-]?qiz(?:lar)?|аёл|айол|аел|қизбола|кизбола)[\s\W\d_]*(?:kishi|киши)?[\s\W\d_]*(?:bor|bar|бор|бар)",
    r"(?:kishi|киши)?[\s\W\d_]*(?:ayol|xotin[\s-]?qiz(?:lar)?|аёл|айол|аел|қизбола|кизбола)[\s\W\d_]*(?:bor|bar|бор|бар)",
    r"\b(?:ketami[zs]|yurami[zs]|borami[zs]|кетами[зс]|юрами[зс]|борами[зс]|чиками[зс]|чиқами[зс])\b[\s\S]{0,40}\b(?:olami[zs]|олами[зс])\b",
    r"(?:galishtirib|келишилган\s+нархларда)",
    r"(?:zakaz|klient|mijoz|заказ|клиент)\s+(?:olamiz|olamis|оламиз|оламис)"
]

COMPILED_PASSENGERS = [re.compile(p, re.IGNORECASE) for p in PASSENGER_PATTERNS]
COMPILED_DRIVERS = [re.compile(p, re.IGNORECASE) for p in DRIVER_PATTERNS]

RAW_KEYWORDS = os.getenv(
    "KEYWORDS",
    "adam bar,kishi bor,odam bor,1 odam bor,1odam bor,2 odam bor,3 odam bor,ikki odam ketadi,jolovshi bor,taksi kerak,taksi kk,taxi kerak,tax kk,тах кк,такси кк,taksi bormi,taksi bormikan,taksi bormakan,taxi bormikan,mashina kerak,moshin kerak,mashin kerak,mashina kerk,moshin bormikan,mashina bormi,мошина керак,мошин керак,машин керак,poputi moshin kerak,pochta bor,pochto bor,pochta bor edi,pasilka bor,почта бор,почто бор,klient lichkasi,klient lich,klent lichkasi,klent lich,taksi narxi,taksi puli qancha,taksi necha som,taksi necha so'm,taksi nechi pul,taksi aqisi qancha,taxi puli qancha,neshe sum,neşe sum,neşe som,nicha som,nicha so'm,qansha aqi,proyezd qancha,проезд канча,такси нечи пул,нича сом,toshkentdan xorazmga qancha,toshkentdan xorazmga necha som,toshkentdan xorazmga necha so'm,toshkentdan urganchga qancha,xorazmdan toshkentga qancha,toshkentdan xorazmga 2 odam bor"
)
USER_KEYWORDS = [k.strip().lower() for k in RAW_KEYWORDS.split(",") if k.strip()]

PHONE_PATTERN = re.compile(r"(?:\+?998[\s-]?)?(?:9[0-9]|33|88|77|99|97|98|95|94|93|91|90)[\s-]?[0-9]{3}[\s-]?[0-9]{2}[\s-]?[0-9]{2}")

# =====================================================================
# TAQIQLANGAN / CHIQARIB TASHLANGAN YO'NALISHLAR (FOYDALANUVCHI TALABI)
# 1. Gurlan - Guliston (va Guliston - Gurlan)
# 2. Qarshi - Toshkent (va Qashqadaryo - Toshkent)
# 3. Surxondaryo - Buxoro - Termiz
# =====================================================================

EXCLUDED_ROUTE_GURLAN_GULISTON = re.compile(
    r"(?:gurlan|gurland|гурлан|гурланд)[\s\S]{0,60}(?:guliston|sirdaryo|гулистон|сирдарё)|"
    r"(?:guliston|sirdaryo|гулистон|сирдарё)[\s\S]{0,60}(?:gurlan|gurland|гурлан|гурланд)",
    re.IGNORECASE
)

EXCLUDED_ROUTE_QARSHI_TOSHKENT = re.compile(
    r"(?:qarshi|karshi|қарши|koson|косон|kasbi|касби|nishon|нишон|gres|грэс|shahrisabz|шаҳрисабз|qashqadaryo|қашқадарё)[\s\S]{0,60}(?:toshkent|tashkent|тошкент|ташкент)|"
    r"(?:toshkent|tashkent|тошкент|ташкент)[\s\S]{0,60}(?:qarshi|karshi|қарши|koson|косон|kasbi|касби|nishon|нишон|gres|грэс|shahrisabz|шаҳрисабз|qashqadaryo|қашқадарё)",
    re.IGNORECASE
)

EXCLUDED_ROUTE_SURXON_BUXORO = re.compile(
    r"(?:surxondaryo|сурхондарё|surxon|сурхон|termiz|термиз|denov|денов|sherobod|шеробод|boysun|бойсун)[\s\S]{0,60}(?:buxoro|бухоро|buxara|gijduvon|ғиждувон)|"
    r"(?:buxoro|бухоро|buxara|gijduvon|ғиждувон)[\s\S]{0,60}(?:surxondaryo|сурхондарё|surxon|сурхон|termiz|термиз|denov|денов|sherobod|шеробод|boysun|бойсун)",
    re.IGNORECASE
)

EXCLUDED_ROUTE_MANGIT_URGANCH = re.compile(
    r"(?:mang[\'ʻʼ]?it|манғит|мангит)[\s\S]{0,60}(?:urganch|urgench|урганч|ургенч)|"
    r"(?:urganch|urgench|урганч|ургенч)[\s\S]{0,60}(?:mang[\'ʻʼ]?it|манғит|мангит)",
    re.IGNORECASE
)

EXCLUDED_ROUTE_BERUNIY_NUKUS = re.compile(
    r"(?:beruniy|бируни|беруний|biruni)[\s\S]{0,60}(?:nukus|nokis|нукус|нокис)|"
    r"(?:nukus|nokis|нукус|нокис)[\s\S]{0,60}(?:beruniy|бируни|беруний|biruni)",
    re.IGNORECASE
)

EXCLUDED_ROUTE_JARQURGON = re.compile(
    r"\b(?:jarqurgon|jarqo[\'ʻʼ]?rg[\'ʻʼ]?on|jarqorgon|jarqurgan|жарқўрғон|жаркурган|жаркургон|жаркоргон)\w*\b",
    re.IGNORECASE
)

EXCLUDED_ROUTE_SHOVOT_URGANCH = re.compile(
    r"(?:shovot|shavat|шовот|шават)[\s\S]{0,60}(?:urganch|urgench|урганч|ургенч)|"
    r"(?:urganch|urgench|урганч|ургенч)[\s\S]{0,60}(?:shovot|shavat|шовот|шават)",
    re.IGNORECASE
)

EXCLUDED_ROUTE_BOSTON_URGANCH = re.compile(
    r"(?:bo[\'ʻʼ]?ston|boston|бостон|бўстон)(?!liq|лиқ)[\s\S]{0,60}(?:urganch|urgench|урганч|ургенч)|"
    r"(?:urganch|urgench|урганч|ургенч)[\s\S]{0,60}(?:bo[\'ʻʼ]?ston|boston|бостон|бўстон)(?!liq|лиқ)",
    re.IGNORECASE
)

EXCLUDED_ROUTE_KEGEYLI = re.compile(
    r"\b(?:kegeyli|kegayli|кегейли|кегайли)\w*\b",
    re.IGNORECASE
)

EXCLUDED_ROUTE_CAMFORT = re.compile(
    r"\b(?:camfort|kamfort)\b",
    re.IGNORECASE
)

EXCLUDED_ROUTE_NUROBOD = re.compile(
    r"\b(?:nurobod|нуробод)\w*\b",
    re.IGNORECASE
)

def is_excluded_group_title(title: str) -> bool:
    """Guruh nomi taqiqlangan yo'nalishlarga tegishli ekanligini tekshiradi."""
    if not title:
        return False
    lower = title.lower()

    # 1. Gurlan - Guliston
    if ("gurlan" in lower or "гурлан" in lower) and ("guliston" in lower or "гулистон" in lower or "sirdaryo" in lower or "сирдарё" in lower):
        return True

    # 2. Mang'it - Urganch (va Urganch - Mang'it)
    is_mangit = any(k in lower for k in ["mangit", "mang'it", "мангит", "манғит"])
    is_urganch = any(k in lower for k in ["urganch", "urgench", "урганч", "ургенч"])
    if is_mangit and is_urganch:
        return True

    # 3. Beruniy - Nukus (va Nukus - Beruniy)
    is_beruniy = any(k in lower for k in ["beruniy", "беруний", "бируни", "biruni"])
    is_nukus = any(k in lower for k in ["nukus", "nokis", "нукус", "нокис"])
    if is_beruniy and is_nukus:
        return True

    # 4. Jarqo'rg'on yo'nalishi (MUTLAQO TAQIQLANGAN)
    JARQURGON_KEYWORDS = [
        "jarqurgon", "jarqo'rg'on", "jarqorgon", "jarqoʻrgʻon", "jarqurgan",
        "жарқўрғон", "жаркурган", "жаркургон", "жаркоргон", "jarqurghon"
    ]
    if any(k in lower for k in JARQURGON_KEYWORDS):
        return True

    # 5. Shovot - Urganch (va Urganch - Shovot) - MUTLAQO TAQIQLANGAN
    is_shovot = any(k in lower for k in ["shovot", "shavat", "шовот", "шават"])
    if is_shovot and is_urganch:
        # Agar Toshkent yoki Samarqand kabi viloyatlararo uzoq yo'nalish bo'lmasa, chiqarib tashlanadi
        if not any(k in lower for k in ["toshkent", "тошкент", "tashkent", "ташкент", "samarqand", "самарқанд"]):
            return True

    # 6. Camfort / Kamfort guruhlari (MUTLAQO TAQIQLANGAN)
    if "camfort" in lower or "kamfort" in lower:
        return True

    # 7. Kegeyli yo'nalishi (MUTLAQO TAQIQLANGAN)
    KEGEYLI_KEYWORDS = ["kegeyli", "кегейли", "kegayli", "кегайли"]
    if any(k in lower for k in KEGEYLI_KEYWORDS):
        return True

    # 8. Urganch - Bo'ston (va Bo'ston - Urganch) - MUTLAQO TAQIQLANGAN
    is_boston = any(k in lower for k in ["bo'ston", "boston", "бостон", "бўстон", "boʻston", "boʼston"])
    if is_boston and is_urganch:
        if not any(k in lower for k in ["toshkent", "тошкент", "tashkent", "ташкент", "samarqand", "самарқанд"]):
            return True

    # 9. Nurobod yo'nalishi (MUTLAQO TAQIQLANGAN)
    if "nurobod" in lower or "нуробод" in lower:
        return True

    # Agar guruh umumiy ko'p viloyatli bo'lsa (bir nechta boshqa viloyatlar qatnashgan bo'lsa),
    # guruhning o'zini butunlay o'chirmaymiz (faqat ichidagi xabarlari filtrlanadi)
    ALL_REG_KEYS = ["vodiy", "водий", "andijon", "андижон", "namangan", "наманган", "fargona", "фарғона", "xorazm", "хоразм", "urganch", "урганч", "nukus", "нукус", "samarqand", "самарқанд", "toshkent", "тошкент"]
    multi_count = sum(1 for r in ALL_REG_KEYS if r in lower)
    if multi_count >= 2:
        return False

    # 10. Qarshi / Qashqadaryo - Toshkent
    is_qashqa = any(k in lower for k in ["qarshi", "karshi", "қарши", "koson", "косон", "kasbi", "касби", "nishon", "нишон", "gres", "грэс", "qashqadaryo", "қашқадарё"])
    is_tosh = any(k in lower for k in ["toshkent", "tashkent", "тошкент", "ташкент"])
    if is_qashqa and is_tosh:
        return True

    # 11. Surxondaryo / Termiz - Buxoro
    is_surxon = any(k in lower for k in ["surxon", "сурхон", "termiz", "термиз", "denov", "денов"])
    is_buxoro = any(k in lower for k in ["buxor", "бухор", "buxara"])
    if is_surxon and is_buxoro:
        return True

    return False

def is_excluded_route(text: str, chat_title: str = "") -> bool:
    """Foydalanuvchi talabiga ko'ra chiqarib tashlangan yo'nalishlar (Gurlan-Guliston, Mang'it-Urganch, Beruniy-Nukus, Jarqo'rg'on, Shovot-Urganch, Bo'ston-Urganch, Kegeyli, Camfort, Nurobod, Qarshi-Toshkent, Surxondaryo-Buxoro-Termiz)."""
    if not text and not chat_title:
        return False

    # A) Guruh nomida ushbu yo'nalish bo'lsa
    if chat_title and is_excluded_group_title(chat_title):
        return True

    # B) Xabar matnida ushbu yo'nalishlar bo'lsa
    if text:
        if EXCLUDED_ROUTE_GURLAN_GULISTON.search(text):
            return True
        if EXCLUDED_ROUTE_MANGIT_URGANCH.search(text):
            return True
        if EXCLUDED_ROUTE_BERUNIY_NUKUS.search(text):
            return True
        if EXCLUDED_ROUTE_JARQURGON.search(text):
            return True
        if EXCLUDED_ROUTE_SHOVOT_URGANCH.search(text):
            return True
        if EXCLUDED_ROUTE_BOSTON_URGANCH.search(text):
            return True
        if EXCLUDED_ROUTE_KEGEYLI.search(text):
            return True
        if EXCLUDED_ROUTE_CAMFORT.search(text):
            return True
        if EXCLUDED_ROUTE_NUROBOD.search(text):
            return True
        if EXCLUDED_ROUTE_QARSHI_TOSHKENT.search(text):
            return True
        if EXCLUDED_ROUTE_SURXON_BUXORO.search(text):
            return True

    return False

TOSHKENT_KEYWORDS = [
    "toshkent", "tashkent", "тошкент", "ташкент"
]

XORAZM_KEYWORDS = [
    "xorazm", "xarezm", "хоразм",
    "urganch", "urgench", "урганч", "ургенч",
    "xiva", "хива",
    "gurlan", "gurland", "гурлан", "гурланд",
    "shovot", "shavat", "шовот", "шават",
    "hazorasp", "xazorasp", "ҳазорасп", "хазорасп",
    "xonqa", "xonka", "хонқа", "хонка",
    "bogot", "bog'ot", "боғот", "богот",
    "yangibozor", "янгибозор",
    "qoshkopir", "qo'shko'pir", "қўшкўпир", "кошкупир",
    "pitnak", "питнақ", "питноқ",
    "yangiariq", "янгиариқ",
    "tuproqqala", "тупроққалъа"
]

def is_toshkent_xorazm_route(text: str, chat_title: str = "") -> bool:
    """Xabar va/yoki guruh FAQAT Toshkent ⇄ Xorazm (va uning tumanlari) yo'nalishiga tegishli ekanligini qat'iy tekshiradi."""
    lower_text = text.lower() if text else ""
    lower_chat = chat_title.lower() if chat_title else ""

    has_toshkent = any(t in lower_text for t in TOSHKENT_KEYWORDS) or any(t in lower_chat for t in TOSHKENT_KEYWORDS)
    has_xorazm = any(x in lower_text for x in XORAZM_KEYWORDS) or any(x in lower_chat for x in XORAZM_KEYWORDS)

    # Ikkala tomon ham (Toshkent va Xorazm viloyati) qatnashgan bo'lishi shart!
    return has_toshkent and has_xorazm

def is_taxi_lead(text: str, chat_title: str = "") -> bool:
    """Xabar FAQAT VA FAQAT Toshkent ⇄ Xorazm yo'lovchi mijozi ekanligini qat'iy tekshiradi."""
    if not text:
        return False

    # 0. Chiqarib tashlangan / taqiqlangan yo'nalishlar -> ZUDLIK BILAN RAD ETILADI!
    if is_excluded_route(text, chat_title):
        return False

    # 1. Faqat va faqat TOSHKENT ⇄ XORAZM yo'nalishi bo'lishi SHART!
    if not is_toshkent_xorazm_route(text, chat_title):
        return False

    lower_text = text.lower()

    # 2. Haydovchi reklamasi bo'lsa -> ZUDLIK BILAN RAD ETILADI!
    for driver_regex in COMPILED_DRIVERS:
        if driver_regex.search(text):
            return False

    # 3. Kalit so'zlar tekshiruvi:
    # A) Maxsus KEYWORDS ro'yxatidan qidirish
    has_user_keyword = any(kw in lower_text for kw in USER_KEYWORDS)
    # B) Yoki umumiy yo'lovchi regexlari
    has_regex_keyword = any(pass_regex.search(text) for pass_regex in COMPILED_PASSENGERS)

    if not (has_user_keyword or has_regex_keyword):
        return False

    return True

def extract_phone(text: str) -> str:
    match = PHONE_PATTERN.search(text)
    return match.group(0).strip() if match else ""

# Vodiy hududi belgilari (Andijon, Namangan, Farg'ona) - Aniq so'z chegaralari bilan
VODIY_PATTERNS = [
    r"andijon[a-z]*", r"andijan[a-z]*", r"андижон[а-я]*",
    r"asaka[a-z]*", r"асака[а-я]*",
    r"shahrixon[a-z]*", r"shaxrixon[a-z]*", r"шаҳрихон[а-я]*", r"шахрихон[а-я]*",
    r"xonobod[a-z]*", r"хонобод[а-я]*",
    r"qorasuv[a-z]*", r"қорасув[а-я]*",
    r"qorgontepa[a-z]*", r"qo[\'ʻʼ]?rg[\'ʻʼ]?ontepa[a-z]*", r"қўрғонтепа[а-я]*",
    r"jalaquduq[a-z]*", r"жалақудуқ[а-я]*",
    r"paxtaobod[a-z]*", r"marhamat[a-z]*", r"oltinko[\'ʻʼ]?l[a-z]*",
    r"buloqboshi[a-z]*", r"izboskan[a-z]*",
    r"farg[\'ʻʼ]?ona[a-z]*", r"fergana[a-z]*", r"фарғона[а-я]*", r"фаргона[а-я]*",
    r"qo[\'ʻʼ]?qon[a-z]*", r"kokand[a-z]*", r"қўқон[а-я]*", r"коканд[а-я]*",
    r"marg[\'ʻʼ]?ilon[a-z]*", r"марғилон[а-я]*", r"маргилан[а-я]*",
    r"quva[a-z]*", r"quvasoy[a-z]*", r"қува[а-я]*", r"қувасой[а-я]*",
    r"rishton[a-z]*", r"риштон[а-я]*",
    r"oltiariq[a-z]*", r"олтиариқ[а-я]*",
    r"bog[\'ʻʼ]?dod[a-z]*", r"uchko[\'ʻʼ]?prik[a-z]*", r"beshariq[a-z]*", r"yazyavon[a-z]*",
    r"namangan[a-z]*", r"наманган[а-я]*",
    r"chust[a-z]*", r"чуст[а-я]*",
    r"pop\s+tuman[a-z]*", r"popga\b", r"popdan\b", r"попга\b", r"попдан\b", r"поп\s+туман[а-я]*",
    r"kosonsoy[a-z]*", r"косонсой[а-я]*",
    r"uchqo[\'ʻʼ]?rg[\'ʻʼ]?on[a-z]*", r"учқўрғон[а-я]*",
    r"to[\'ʻʼ]?raqo[\'ʻʼ]?rg[\'ʻʼ]?on[a-z]*", r"тўрақўрғон[а-я]*",
    r"chortoq[a-z]*", r"чортоқ[а-я]*",
    r"yangiqo[\'ʻʼ]?rg[\'ʻʼ]?on[a-z]*",
    r"vodiy[a-z]*", r"водий[а-я]*"
]

VODIY_REGEX = re.compile(r"\b(?:" + "|".join(VODIY_PATTERNS) + r")\b", re.IGNORECASE)

VODIY_LOCATIONS = [
    "andijon", "andijan", "андижон", "asaka", "асака", "shahrixon", "shaxrixon", "шаҳрихон",
    "xonobod", "хонобод", "qorasuv", "қорасув", "qorgontepa", "қўрғонтепа", "jalaquduq", "жалақудуқ",
    "fargona", "fergana", "фарғона", "фаргона", "qoqon", "kokand", "қўқон", "коканд",
    "margilon", "марғилон", "маргилан", "quva", "қува", "rishton", "риштон", "oltiariq", "олтиариқ",
    "namangan", "наманган", "chust", "чуст", "popga", "popdan", "kosonsoy", "косонсой",
    "uchqorgon", "учқўрғон", "chortoq", "чортоқ", "vodiy", "водий"
]

# Nukus - Gurlan - Urganch yo'nalishi uchun maxsus regex va filterlar:
NUKUS_REGEX = re.compile(r"\b(?:nukus|nokis|нукус|нокис)\w*\b", re.IGNORECASE)
URGANCH_REGEX = re.compile(r"\b(?:urganch|urgench|урганч|ургенч)\w*\b", re.IGNORECASE)
GURLAN_REGEX = re.compile(r"\b(?:gurlan|gurland|гурлан|гурланд)\w*\b", re.IGNORECASE)

# Oradagi kichik tumanlar (bular aralashsa, yangi guruhga EMAS, Voha guruhiga o'tadi)
EXCLUDED_LOCAL_DISTRICTS = [
    r"shovot\w*", r"шовот\w*", r"shavat\w*", r"шават\w*",
    r"yangibozor\w*", r"янгибозор\w*",
    r"xiva\w*", r"хива\w*",
    r"xonqa\w*", r"хонқа\w*", r"хонка\w*",
    r"hazorasp\w*", r"ҳазорасп\w*", r"xazorasp\w*", r"хазорасп\w*",
    r"bog[\'ʻʼ]?ot\w*", r"боғот\w*", r"богот\w*",
    r"qo[\'ʻʼ]?shko[\'ʻʼ]?pir\w*", r"қўшкўпир\w*", r"кошкупир\w*",
    r"beruniy\w*", r"беруний\w*", r"бируни\w*",
    r"to[\'ʻʼ]?rtko[\'ʻʼ]?l\w*", r"тўрткўл\w*", r"торткул\w*",
    r"ellikqala\w*", r"элликқалъа\w*",
    r"xo[\'ʻʼ]?jayli\w*", r"хўжайли\w*", r"ходжейли\w*",
    r"pitnak\w*", r"питнақ\w*", r"питноқ\w*",
    r"tuproqqala\w*", r"тупроққалъа\w*",
    r"yangiariq\w*", r"янгиариқ\w*",
    r"mang[\'ʻʼ]?it\w*", r"манғит\w*", r"мангит\w*",
    r"chimboy\w*", r"чимбой\w*",
    r"moynoq\w*", r"мўйноқ\w*", r"муйнак\w*",
    r"shumanay\w*", r"шуманай\w*",
    r"qonliko[\'ʻʼ]?l\w*", r"қанликўл\w*",
    r"taxtako[\'ʻʼ]?pir\w*", r"тахтакўпир\w*",
    r"taxiatosh\w*", r"тахиатош\w*",
    r"qo[\'ʻʼ]?ng[\'ʻʼ]?irot\w*", r"қўнғирот\w*", r"kungrad\w*", r"кунград\w*", r"kongrat\w*", r"конграт\w*"
]
EXCLUDED_LOCAL_DISTRICTS_REGEX = re.compile(r"\b(?:" + "|".join(EXCLUDED_LOCAL_DISTRICTS) + r")\b", re.IGNORECASE)

# Tashqi viloyatlar (Voha, Toshkent va b. - bular ham Voha guruhiga tushadi)
VOHA_EXTERNAL_REGIONS = [
    r"toshkent\w*", r"тошкент\w*", r"tashkent\w*", r"ташкент\w*",
    r"samarqand\w*", r"самарқанд\w*", r"самарканд\w*", r"samarkand\w*",
    r"buxoro\w*", r"бухоро\w*", r"buxara\w*",
    r"navoiy\w*", r"навоий\w*", r"navoi\w*", r"zarafshon\w*", r"зарафшон\w*",
    r"qarshi\w*", r"қарши\w*", r"karshi\w*", r"shahrisabz\w*", r"шаҳрисабз\w*",
    r"qashqadaryo\w*", r"қашқадарё\w*",
    r"termiz\w*", r"термиз\w*", r"denov\w*", r"денов\w*",
    r"surxondaryo\w*", r"сурхондарё\w*",
    r"jizzax\w*", r"жиззах\w*", r"sirdaryo\w*", r"сирдарё\w*",
    r"guliston\w*", r"гулистон\w*"
]
VOHA_EXTERNAL_REGEX = re.compile(r"\b(?:" + "|".join(VOHA_EXTERNAL_REGIONS) + r")\b", re.IGNORECASE)

def is_nukus_gurlan_urganch_route(text: str, chat_title: str = "") -> bool:
    """Xabar faqat Nukus, Gurlan (Gurland), Urganch orasidagi yo'nalish ekanligini tekshiradi."""
    # 1. Agar xabarda Toshkent / Samarqand / Buxoro kabi voha shaharlari bo'lsa -> False (Vohaga boradi)
    if VOHA_EXTERNAL_REGEX.search(text):
        return False

    # 2. Agar oradagi kichik tumanlar (Shovot, Xiva, Beruniy va h.k.) bo'lsa -> False (Vohaga boradi)
    if EXCLUDED_LOCAL_DISTRICTS_REGEX.search(text):
        return False

    # 3. Avval matnning o'zini tekshiramiz (eng ustuvor)
    has_nukus_text = bool(NUKUS_REGEX.search(text))
    has_urganch_text = bool(URGANCH_REGEX.search(text))
    has_gurlan_text = bool(GURLAN_REGEX.search(text))

    direct_pairs = (
        (has_nukus_text and has_urganch_text) or
        (has_nukus_text and has_gurlan_text) or
        (has_urganch_text and has_gurlan_text)
    )
    if direct_pairs:
        return True

    # 4. Agar matnda faqat bittasi bo'lsa, guruh nomiga qaraymiz (agar guruh tashqi bo'lmasa)
    if not VOHA_EXTERNAL_REGEX.search(chat_title) and not EXCLUDED_LOCAL_DISTRICTS_REGEX.search(chat_title):
        has_nukus_chat = bool(NUKUS_REGEX.search(chat_title))
        has_urganch_chat = bool(URGANCH_REGEX.search(chat_title))
        has_gurlan_chat = bool(GURLAN_REGEX.search(chat_title))

        has_nukus = has_nukus_text or has_nukus_chat
        has_urganch = has_urganch_text or has_urganch_chat
        has_gurlan = has_gurlan_text or has_gurlan_chat

        combined_pairs = (
            (has_nukus and has_urganch) or
            (has_nukus and has_gurlan) or
            (has_urganch and has_gurlan)
        )
        if combined_pairs:
            return True

    return False

def get_target_drivers_group_id(text: str, chat_title: str = "") -> int:
    """Toshkent - Xorazm yo'nalishi bo'yicha barcha buyurtmalar Asosiy Haydovchilar guruhiga yuboriladi."""
    return DRIVERS_GROUP_ID
