from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from config import ADMIN_IDS

def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """Asosiy menyu klaviaturasi (qalin va chiroyli emojilar bilan)"""
    keyboard = [
        [
            KeyboardButton(text="💎 Pullik vizlom o'yinlar"),
            KeyboardButton(text="🎁 Tekin vizlom o'yinlar")
        ],
        [
            KeyboardButton(text="👤 Profil"),
            KeyboardButton(text="💳 Hisob to'ldirish")
        ],
        [
            KeyboardButton(text="🎮 Sotib olgan o'yinlarim")
        ]
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([KeyboardButton(text="👑 Admin Panel")])
        
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_subscription_keyboard(channels: list) -> InlineKeyboardMarkup:
    """Majburiy kanallarga obuna bo'lish tugmalari"""
    inline_keyboard = []
    for idx, ch in enumerate(channels, 1):
        title = ch['title'] or f"Kanal #{idx}"
        inline_keyboard.append([
            InlineKeyboardButton(text=f"📢 {title}", url=ch['url'])
        ])
    inline_keyboard.append([
        InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_subscription")
    ])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def get_games_grid_keyboard(games: list, category: str, page: int, total_pages: int) -> InlineKeyboardMarkup:
    """
    3x2 panjara ko'rinishidagi o'yinlar klaviaturasi:
    Bir tomonda 3 ta, bu tomonda 3 ta (har qatorda 2 tadan).
    Pastida: navigatsiya tugmalari.
    """
    inline_keyboard = []
    
    # 2 tadan guruhlash (3 qator x 2 ustun = 6 ta)
    row = []
    for game in games:
        # Pullik bo'lsa narx belgisi, tekin bo'lsa sovg'a
        prefix = "💎" if category == "paid" else "🎁"
        # Tugma matnini qisqartirish (juda uzun bo'lsa)
        title = game['title']
        if len(title) > 16:
            title = title[:14] + ".."
        btn = InlineKeyboardButton(
            text=f"{prefix} {title}",
            callback_data=f"game_{game['id']}"
        )
        row.append(btn)
        if len(row) == 2:
            inline_keyboard.append(row)
            row = []
    if row:
        inline_keyboard.append(row)
        
    # Navigatsiya qatori
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"nav_{category}_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages or 1}", callback_data="noop"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"nav_{category}_{page+1}"))
        
    inline_keyboard.append(nav_buttons)
    inline_keyboard.append([InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def get_game_details_keyboard(game_id: int, category: str, price: int, is_purchased: bool = False) -> InlineKeyboardMarkup:
    """O'yin ma'lumoti ostidagi inline tugmalar"""
    inline_keyboard = []
    if category == "paid":
        if is_purchased:
            inline_keyboard.append([
                InlineKeyboardButton(text="📥 Qayta yuklab olish", callback_data=f"download_{game_id}")
            ])
        else:
            inline_keyboard.append([
                InlineKeyboardButton(text=f"🛒 Sotib olish ({price:,} so'm)", callback_data=f"buy_{game_id}")
            ])
    else:
        inline_keyboard.append([
            InlineKeyboardButton(text="📥 Bepul yuklab olish", callback_data=f"download_{game_id}")
        ])
        
    inline_keyboard.append([
        InlineKeyboardButton(text="🔙 O'yinlar ro'yxatiga qaytish", callback_data=f"back_games_{category}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def get_my_games_keyboard(purchased_games: list) -> InlineKeyboardMarkup:
    """Sotib olingan o'yinlar ro'yxati inline tugmalari"""
    inline_keyboard = []
    for item in purchased_games:
        title = item['title']
        inline_keyboard.append([
            InlineKeyboardButton(text=f"📥 {title} (Yuklab olish)", callback_data=f"download_{item['id']}")
        ])
    inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def get_payment_keyboard(payment_id: str) -> InlineKeyboardMarkup:
    """To'lov sahifasidagi tekshirish va bekor qilish tugmalari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 To'lovni tekshirish", callback_data=f"chkpay_{payment_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"cnlpay_{payment_id}")]
    ])

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Profil menyusi inline tugmalari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Hisobni to'ldirish", callback_data="top_up_balance")],
        [InlineKeyboardButton(text="🎮 O'yinlarim", callback_data="my_games_inline")],
        [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="back_to_main")]
    ])

# --- Admin Klaviaturasi ---
def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
            InlineKeyboardButton(text="🎮 O'yin qo'shish", callback_data="admin_add_game")
        ],
        [
            InlineKeyboardButton(text="🗑 O'yinni o'chirish", callback_data="admin_delete_game_list"),
            InlineKeyboardButton(text="📢 Majburiy kanallar", callback_data="admin_channels")
        ],
        [
            InlineKeyboardButton(text="✉️ Xabar yuborish (Reklama)", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="💰 Balans boshqaruvi", callback_data="admin_balance")
        ],
        [
            InlineKeyboardButton(text="🔙 Asosiy menyuga qaytish", callback_data="back_to_main")
        ]
    ])

def get_admin_channels_keyboard(channels: list) -> InlineKeyboardMarkup:
    inline_keyboard = []
    for ch in channels:
        inline_keyboard.append([
            InlineKeyboardButton(text=f"❌ O'chirish: {ch['title']}", callback_data=f"del_channel_{ch['channel_id']}")
        ])
    inline_keyboard.append([
        InlineKeyboardButton(text="➕ Yangi kanal qo'shish", callback_data="add_new_channel")
    ])
    inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Admin panelga qaytish", callback_data="admin_home")
    ])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def get_cancel_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_home")]
    ])
