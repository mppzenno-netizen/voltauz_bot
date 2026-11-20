import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_IDS
import database as db
import keyboards as kb

router = Router()

# Admin filtri: faqat admin_ids dagi foydalanuvchilar
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# FSM holatlari: O'yin qo'shish
class AddGameFSM(StatesGroup):
    category = State()
    title = State()
    description = State()
    photo = State()
    price = State()
    file = State()

# FSM holatlari: Kanal qo'shish
class AddChannelFSM(StatesGroup):
    url = State()
    title = State()
    channel_id = State()

# FSM holatlari: Reklama tarqatish
class BroadcastFSM(StatesGroup):
    message = State()

# FSM holatlari: Balans boshqarish
class BalanceFSM(StatesGroup):
    user_id = State()
    amount = State()

@router.message(Command("admin"))
@router.message(F.text == "👑 Admin Panel")
async def admin_panel_home(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    text = (
        "👑 <b>Xush kelibsiz, Bosh Administrator!</b>\n\n"
        "⚡️ <i>Quyidagi boshqaruv panelidan kerakli bo'limni tanlang:</i>"
    )
    await message.answer(text, reply_markup=kb.get_admin_main_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "admin_home")
async def cb_admin_home(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    text = (
        "👑 <b>Boshqaruv paneli:</b>\n\n"
        "<i>Kerakli amalni tanlang:</i>"
    )
    try:
        await callback.message.edit_text(text, reply_markup=kb.get_admin_main_keyboard(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb.get_admin_main_keyboard(), parse_mode="HTML")
    await callback.answer()

# --- 1. STATISTIKA ---
@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer("Statistika hisoblanmoqda...")
    
    stats = await db.get_system_statistics()
    
    text = (
        "📊 <b>BOTNING TO'LIQ STATISTIKASI:</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> <b>{stats['total_users']} nafar</b>\n"
        f"📈 <b>Bugun qo'shilganlar:</b> <b>+{stats['today_users']} nafar</b>\n"
        f"💳 <b>To'lov qilgan foydalanuvchilar:</b> <b>{stats['paid_users_count']} nafar</b>\n"
        f"🎁 <b>Faqat tekin o'yin yuklaganlar:</b> <b>{stats['free_users_count']} nafar</b>\n\n"
        f"💰 <b>Shu oyda aylangan pul:</b> <b>{stats['monthly_income']:,} so'm</b>\n"
        f"💵 <b>Jami umumiy aylanma pul:</b> <b>{stats['total_income']:,} so'm</b>\n\n"
        f"🎮 <b>Jami bazadagi o'yinlar:</b> <b>{stats['total_games']} ta</b>\n"
        f"   • 💎 Pullik o'yinlar: <b>{stats['paid_games']} ta</b>\n"
        f"   • 🎁 Tekin o'yinlar: <b>{stats['free_games']} ta</b>\n"
        f"📥 <b>Jami amalga oshirilgan xaridlar:</b> <b>{stats['total_purchases']} marta</b>\n\n"
        "⚡️ <i>Ma'lumotlar real vaqt rejimida yangilanadi.</i>"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_home")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")

# --- 2. O'YIN QO'SHISH ---
@router.callback_query(F.data == "admin_add_game")
async def cb_admin_add_game(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💎 Pullik o'yin", callback_data="addcat_paid"),
            InlineKeyboardButton(text="🎁 Tekin o'yin", callback_data="addcat_free")
        ],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_home")]
    ])
    await callback.message.edit_text("🎮 <b>Qo'shmoqchi bo'lgan o'yiningiz turini tanlang:</b>", reply_markup=markup, parse_mode="HTML")
    await state.set_state(AddGameFSM.category)
    await callback.answer()

@router.callback_query(AddGameFSM.category, F.data.startswith("addcat_"))
async def process_game_category(callback: CallbackQuery, state: FSMContext):
    cat = callback.data.split("_")[1]
    await state.update_data(category=cat)
    
    await callback.message.edit_text(
        "📝 <b>1-Qadam:</b> O'yin nomini kiriting:\n<i>(Masalan: GTA San Andreas Mod / PUBG Vizlom)</i>",
        reply_markup=kb.get_cancel_admin_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AddGameFSM.title)
    await callback.answer()

@router.message(AddGameFSM.title)
async def process_game_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer(
        "📄 <b>2-Qadam:</b> O'yin haqida to'liq ma'lumot (tavsif) yuboring:\n<i>(Versiyasi, xususiyatlari, cheksiz puli va h.k.)</i>",
        reply_markup=kb.get_cancel_admin_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AddGameFSM.description)

@router.message(AddGameFSM.description)
async def process_game_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await message.answer(
        "🖼 <b>3-Qadam:</b> O'yin uchun rasm (banner) yuboring:\n<i>(Rasm formatida yuboring)</i>",
        reply_markup=kb.get_cancel_admin_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AddGameFSM.photo)

@router.message(AddGameFSM.photo, F.photo)
async def process_game_photo(message: Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo=photo_file_id)
    
    data = await state.get_data()
    if data["category"] == "paid":
        await message.answer(
            "💰 <b>4-Qadam:</b> Ushbu pullik o'yin narxini so'mda kiriting:\n<i>(Faqat son, masalan: 15000 yoki 30000)</i>",
            reply_markup=kb.get_cancel_admin_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(AddGameFSM.price)
    else:
        await state.update_data(price=0)
        await message.answer(
            "📦 <b>Oxirgi qadam:</b> O'yin faylini (APK, zip, rar, doc) yuboring:",
            reply_markup=kb.get_cancel_admin_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(AddGameFSM.file)

@router.message(AddGameFSM.price)
async def process_game_price(message: Message, state: FSMContext):
    price_str = message.text.replace(" ", "").replace(",", "").strip()
    if not price_str.isdigit() or int(price_str) <= 0:
        await message.answer("⚠️ Iltimos, musbat raqam kiriting (masalan: 15000):")
        return
        
    await state.update_data(price=int(price_str))
    await message.answer(
        "📦 <b>Oxirgi qadam:</b> O'yin faylini (APK, zip, rar, document) yuboring:",
        reply_markup=kb.get_cancel_admin_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AddGameFSM.file)

@router.message(AddGameFSM.file, F.document | F.video | F.audio)
async def process_game_file(message: Message, state: FSMContext):
    if message.document:
        file_id = message.document.file_id
    elif message.video:
        file_id = message.video.file_id
    else:
        file_id = message.audio.file_id
        
    data = await state.get_data()
    
    # Bazaga yozish
    game_id = await db.add_game(
        title=data["title"],
        description=data["description"],
        category=data["category"],
        price=data["price"],
        photo_file_id=data["photo"],
        game_file_id=file_id
    )
    await state.clear()
    
    cat_name = "💎 Pullik" if data["category"] == "paid" else "🎁 Tekin"
    price_str = f"{data['price']:,} so'm" if data["category"] == "paid" else "Tekin"
    
    success_text = (
        "✅ <b>O'YIN MUVAFFAQIYATLI QO'SHILDI!</b>\n\n"
        f"🆔 ID: <b>{game_id}</b>\n"
        f"🎮 Nomi: <b>{data['title']}</b>\n"
        f"📂 Turi: <b>{cat_name}</b>\n"
        f"💰 Narxi: <b>{price_str}</b>\n\n"
        "<i>Foydalanuvchilar darhol bot orqali ushbu o'yinni ko'rishlari va olishlari mumkin.</i>"
    )
    await message.answer(success_text, reply_markup=kb.get_admin_main_keyboard(), parse_mode="HTML")

# --- 3. O'YINLARNI O'CHIRISH ---
@router.callback_query(F.data == "admin_delete_game_list")
async def cb_delete_game_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    # Oxirgi 20 ta o'yinni chiqarish
    paid_games = await db.get_games_paginated("paid", 1, 10)
    free_games = await db.get_games_paginated("free", 1, 10)
    
    all_games = list(paid_games) + list(free_games)
    if not all_games:
        await callback.answer("⚠️ Hozircha bazada o'yinlar mavjud emas!", show_alert=True)
        return
        
    inline_keyboard = []
    for g in all_games:
        cat_p = "💎" if g["category"] == "paid" else "🎁"
        inline_keyboard.append([
            InlineKeyboardButton(text=f"🗑 {cat_p} {g['title']}", callback_data=f"delgame_{g['id']}")
        ])
    inline_keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_home")])
    
    await callback.message.edit_text(
        "🗑 <b>O'chirmoqchi bo'lgan o'yin ustiga bosing:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delgame_"))
async def cb_delete_game_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    game_id = int(callback.data.split("_")[1])
    game = await db.get_game(game_id)
    if game:
        await db.delete_game(game_id)
        await callback.answer(f"✅ '{game['title']}' muvaffaqiyatli o'chirildi!", show_alert=True)
    else:
        await callback.answer("O'yin topilmadi.", show_alert=True)
    await cb_delete_game_list(callback)

# --- 4. MAJBURİY KANALLAR BOSHQARUVI ---
@router.callback_query(F.data == "admin_channels")
async def cb_admin_channels(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    channels = await db.get_channels()
    text = (
        "📢 <b>MAJBURIY OBUNA KANALLARI</b>\n\n"
        f"Ulangan kanallar soni: <b>{len(channels)} ta</b>\n\n"
        "<i>Eslatma: Bot ushbu kanallarda admin bo'lishi shart! Maxfiy kanallarni ham invite link orqali ulasangiz bo'ladi.</i>"
    )
    await callback.message.edit_text(text, reply_markup=kb.get_admin_channels_keyboard(channels), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("del_channel_"))
async def cb_delete_channel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    ch_id = callback.data.replace("del_channel_", "")
    await db.delete_channel(ch_id)
    await callback.answer("✅ Kanal olib tashlandi!", show_alert=True)
    channels = await db.get_channels()
    await callback.message.edit_reply_markup(reply_markup=kb.get_admin_channels_keyboard(channels))

@router.callback_query(F.data == "add_new_channel")
async def cb_add_channel_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "🔗 <b>1-Qadam:</b> Kanalning havolasini (URL yoki Maxfiy havola) yuboring:\n"
        "<i>(Masalan: https://t.me/+AbCdEfGhIjKlMnOp yoki https://t.me/kanal_nomi)</i>",
        reply_markup=kb.get_cancel_admin_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AddChannelFSM.url)
    await callback.answer()

@router.message(AddChannelFSM.url)
async def process_channel_url(message: Message, state: FSMContext):
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("⚠️ Iltimos, to'liq havola yuboring (https://t.me/...):")
        return
    await state.update_data(url=url)
    await message.answer(
        "🏷 <b>2-Qadam:</b> Tugmada ko'rinadigan kanal nomini kiriting:\n<i>(Masalan: Bizning rasmiy kanal)</i>",
        reply_markup=kb.get_cancel_admin_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AddChannelFSM.title)

@router.message(AddChannelFSM.title)
async def process_channel_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer(
        "🆔 <b>3-Qadam:</b> Kanalning ID raqamini yoki username'ini kiriting:\n\n"
        "• Agar ochiq kanal bo'lsa: <code>@kanal_username</code> yoki <code>-100...</code>\n"
        "• Agar maxfiy kanal bo'lsa: uning chat ID raqamini kiriting (masalan: <code>-1002345678901</code>)\n\n"
        "⚠️ <i>Muhim: Bot o'sha kanalda administrator qilingan bo'lishi kerak!</i>",
        reply_markup=kb.get_cancel_admin_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AddChannelFSM.channel_id)

@router.message(AddChannelFSM.channel_id)
async def process_channel_id(message: Message, state: FSMContext, bot: Bot):
    ch_id = message.text.strip()
    data = await state.get_data()
    
    # Bot adminligini tekshirishga urinib ko'ramiz
    try:
        chat_val = int(ch_id) if (ch_id.startswith('-') or ch_id.isdigit()) else ch_id
        chat = await bot.get_chat(chat_val)
        me = await bot.get_chat_member(chat_val, (await bot.get_me()).id)
        ch_title = data["title"] or chat.title
    except Exception as e:
        # Xatolik bersa ham admin istagan bo'lsa qabul qilamiz
        ch_title = data["title"]
        
    await db.add_channel(channel_id=ch_id, title=ch_title, url=data["url"])
    await state.clear()
    
    text = (
        "✅ <b>KANAL MUVAFFAQIYATLI QO'SHILDI!</b>\n\n"
        f"📢 Nomi: <b>{ch_title}</b>\n"
        f"🔗 Havola: {data['url']}\n"
        f"🆔 ID: <code>{ch_id}</code>\n\n"
        "<i>Endi barcha yangi foydalanuvchilar ushbu kanalga a'zo bo'lmaguncha botdan foydalana olmaydilar.</i>"
    )
    await message.answer(text, reply_markup=kb.get_admin_main_keyboard(), parse_mode="HTML")

# --- 5. REKLAMA / BROADCAST ---
@router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text(
        "✉️ <b>REKLAMA VA XABAR YUBORISH</b>\n\n"
        "<i>Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring (matn, rasm, video, havola):</i>",
        reply_markup=kb.get_cancel_admin_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(BroadcastFSM.message)
    await callback.answer()

@router.message(BroadcastFSM.message)
async def process_broadcast_message(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    users = await db.get_all_users()
    
    status_msg = await message.answer(f"🚀 Xabar yuborish boshlandi... Jami: {len(users)} nafar foydalanuvchi.")
    
    success = 0
    blocked = 0
    
    for u in users:
        u_id = u["user_id"]
        try:
            await bot.copy_message(chat_id=u_id, from_chat_id=message.chat.id, message_id=message.message_id)
            success += 1
            await asyncio.sleep(0.05) # Telegram flood control uchun
        except Exception:
            blocked += 1
            
    await status_msg.edit_text(
        "✅ <b>XABAR YUBORISH YAKUNLANDI!</b>\n\n"
        f"👥 Jami qamrov: <b>{len(users)} ta</b>\n"
        f"✅ Muvaffaqiyatli yetkazildi: <b>{success} ta</b>\n"
        f"❌ Yetib bormadi (bloklagan): <b>{blocked} ta</b>",
        parse_mode="HTML"
    )

# --- 6. BALANS BOSHQARUVI ---
@router.callback_query(F.data == "admin_balance")
async def cb_admin_balance(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text(
        "💰 <b>FOYDALANUVCHI BALANSINI BOSHQARISH</b>\n\n"
        "<i>Balansini o'zgartirmoqchi bo'lgan foydalanuvchining Telegram ID raqamini kiriting:</i>",
        reply_markup=kb.get_cancel_admin_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(BalanceFSM.user_id)
    await callback.answer()

@router.message(BalanceFSM.user_id)
async def process_balance_user_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Iltimos, to'g'ri ID raqamini kiriting:")
        return
    target_id = int(message.text)
    user = await db.get_user(target_id)
    if not user:
        await message.answer("⚠️ Ushbu ID ga ega foydalanuvchi bot bazasida topilmadi. Qayta urinib ko'ring:")
        return
        
    await state.update_data(target_id=target_id)
    await message.answer(
        f"👤 Foydalanuvchi: <b>{user['full_name']}</b> (<code>{user['user_id']}</code>)\n"
        f"💰 Hozirgi balansi: <b>{user['balance']:,} so'm</b>\n\n"
        "<i>Qo'shmoqchi bo'lgan summani kiriting (agar ayirmoqchi bo'lsangiz - belgisi bilan, masalan: 50000 yoki -20000):</i>",
        reply_markup=kb.get_cancel_admin_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(BalanceFSM.amount)

@router.message(BalanceFSM.amount)
async def process_balance_amount(message: Message, state: FSMContext, bot: Bot):
    amt_str = message.text.replace(" ", "").strip()
    try:
        amt = int(amt_str)
    except ValueError:
        await message.answer("⚠️ Raqam kiriting:")
        return
        
    data = await state.get_data()
    target_id = data["target_id"]
    
    await db.update_user_balance(target_id, amt)
    user_after = await db.get_user(target_id)
    await state.clear()
    
    sign = "+" if amt >= 0 else ""
    await message.answer(
        f"✅ Foydalanuvchi (ID: <code>{target_id}</code>) balansi <b>{sign}{amt:,} so'm</b>ga o'zgartirildi!\n"
        f"💰 Yangi balansi: <b>{user_after['balance']:,} so'm</b>",
        reply_markup=kb.get_admin_main_keyboard(),
        parse_mode="HTML"
    )
    
    # Foydalanuvchiga xabar berish
    try:
        await bot.send_message(
            target_id,
            f"💰 <b>Administrator tomonidan hisobingiz {sign}{amt:,} so'mga to'ldirildi!</b>\n"
            f"Yangi balansingiz: <b>{user_after['balance']:,} so'm</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass
