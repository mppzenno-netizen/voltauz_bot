import math
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
import database as db
import keyboards as kb
from config import ADMIN_IDS

router = Router()

PER_PAGE = 6

async def show_games_list(chat_id: int, bot: Bot, category: str, page: int = 1, message_to_edit: Message = None):
    total_count = await db.count_games(category)
    total_pages = math.ceil(total_count / PER_PAGE) if total_count > 0 else 1
    
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
        
    games = await db.get_games_paginated(category, page, PER_PAGE)
    
    cat_title = "💎 <b>PULLIK VIZLOM O'YINLAR KATALOGI</b>" if category == "paid" else "🎁 <b>TEKIN VIZLOM O'YINLAR KATALOGI</b>"
    
    if not games:
        empty_text = (
            f"{cat_title}\n\n"
            "😔 <i>Hozircha bu bo'limda o'yinlar mavjud emas. Tez orada yangi o'yinlar qo'shiladi!</i>"
        )
        if message_to_edit:
            await message_to_edit.edit_text(empty_text, parse_mode="HTML")
        else:
            await bot.send_message(chat_id, empty_text, parse_mode="HTML")
        return

    text = (
        f"{cat_title}\n\n"
        f"📊 Jami o'yinlar: <b>{total_count} ta</b> | Sahifa: <b>{page}/{total_pages}</b>\n\n"
        "👇 <i>O'zingizga ma'qul kelgan o'yin nomiga bosing va u haqida to'liq ma'lumot oling:</i>"
    )
    
    markup = kb.get_games_grid_keyboard(games, category, page, total_pages)
    
    if message_to_edit:
        try:
            await message_to_edit.edit_text(text, reply_markup=markup, parse_mode="HTML")
        except Exception:
            await bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
    else:
        await bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

@router.message(F.text == "💎 Pullik vizlom o'yinlar")
async def menu_paid_games(message: Message, bot: Bot):
    await show_games_list(message.chat.id, bot, category="paid", page=1)

@router.message(F.text == "🎁 Tekin vizlom o'yinlar")
async def menu_free_games(message: Message, bot: Bot):
    await show_games_list(message.chat.id, bot, category="free", page=1)

@router.callback_query(F.data.startswith("nav_"))
async def cb_navigate_games(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    category = parts[1]
    page = int(parts[2])
    await show_games_list(callback.message.chat.id, bot, category, page, message_to_edit=callback.message)
    await callback.answer()

@router.callback_query(F.data.startswith("back_games_"))
async def cb_back_to_games(callback: CallbackQuery, bot: Bot):
    category = callback.data.split("_")[2]
    await show_games_list(callback.message.chat.id, bot, category, page=1)
    await callback.answer()

@router.callback_query(F.data.startswith("game_"))
async def cb_show_game_details(callback: CallbackQuery, bot: Bot):
    game_id = int(callback.data.split("_")[1])
    game = await db.get_game(game_id)
    
    if not game:
        await callback.answer("⚠️ Ushbu o'yin topilmadi yoki o'chirilgan!", show_alert=True)
        return
        
    is_purchased = await db.has_user_purchased(callback.from_user.id, game_id)
    
    price_info = f"💰 <b>Narxi:</b> <b>{game['price']:,} so'm</b>\n" if game['category'] == "paid" else "💰 <b>Narxi:</b> <b>Mutlaqo BEPUL! 🎁</b>\n"
    
    caption = (
        f"🎮 <b>O'YIN:</b> <b>{game['title']}</b>\n\n"
        f"📝 <b>Ma'lumot:</b>\n{game['description']}\n\n"
        f"{price_info}"
        f"📥 <b>Yuklab olishlar soni:</b> <b>{game['downloads_count']} marta</b>\n\n"
        "⚡️ <i>O'yinni olish uchun quyidagi tugmani bosing:</i>"
    )
    
    markup = kb.get_game_details_keyboard(game_id, game['category'], game['price'], is_purchased)
    
    await callback.answer()
    
    if game['photo_file_id']:
        try:
            await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=game['photo_file_id'],
                caption=caption,
                reply_markup=markup,
                parse_mode="HTML"
            )
            return
        except Exception:
            pass
            
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=caption,
        reply_markup=markup,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("buy_"))
async def cb_buy_game(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    game_id = int(callback.data.split("_")[1])
    
    game = await db.get_game(game_id)
    if not game:
        await callback.answer("⚠️ Ushbu o'yin topilmadi!", show_alert=True)
        return
        
    user = await db.get_user(user_id)
    if not user:
        await db.add_or_update_user(user_id, callback.from_user.username or "", callback.from_user.full_name or "")
        user = await db.get_user(user_id)
        
    # Oldin sotib olinganmi?
    if await db.has_user_purchased(user_id, game_id):
        await callback.answer("✅ Siz bu o'yinni oldin sotib olgansiz! Fayl yuborilmoqda...", show_alert=False)
        await send_game_file(callback.message.chat.id, bot, game)
        return
        
    price = game['price']
    balance = user['balance']
    
    if balance < price:
        diff = price - balance
        error_text = (
            "⚠️ <b>HISOBINGIZDA MABLAG' YETARLI EMAS!</b>\n\n"
            f"🎮 O'yin nomi: <b>{game['title']}</b>\n"
            f"💰 O'yin narxi: <b>{price:,} so'm</b>\n"
            f"💳 Sizning balansingiz: <b>{balance:,} so'm</b>\n"
            f"❗️ Yetishmayotgan summa: <b>{diff:,} so'm</b>\n\n"
            "<i>Iltimos, avval hisobingizni to'ldiring:</i>"
        )
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Hisobni to'ldirish", callback_data="top_up_balance")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"game_{game_id}")]
        ])
        await callback.message.answer(error_text, reply_markup=markup, parse_mode="HTML")
        await callback.answer()
        return
        
    # Balansdan pul yechish
    await db.update_user_balance(user_id, -price)
    await db.add_purchase(user_id, game_id, price)
    await db.increment_game_downloads(game_id)
    
    user_after = await db.get_user(user_id)
    
    success_text = (
        "🎉 <b>TABRIKLAYMIZ! XARIDINGIZ MUVAFFAQIYATLI AMALGA OSHIRILDI!</b>\n\n"
        f"🎮 O'yin: <b>{game['title']}</b>\n"
        f"💸 To'langan summa: <b>{price:,} so'm</b>\n"
        f"💰 Yangi balansingiz: <b>{user_after['balance']:,} so'm</b>\n\n"
        "📥 <i>O'yin fayli quyida yuborilmoqda. Maroqli o'yin tilaymiz!</i>"
    )
    await callback.message.answer(success_text, parse_mode="HTML")
    await callback.answer("Xaridingiz uchun rahmat!", show_alert=False)
    
    # Faylni yuborish
    await send_game_file(callback.message.chat.id, bot, game)
    
    # Adminga xabarnoma
    for admin_id in ADMIN_IDS:
        try:
            admin_msg = (
                "🛍 <b>YANGI XARID AMALGA OSHIRILDI!</b>\n\n"
                f"👤 Foydalanuvchi: {callback.from_user.mention_html()} (ID: <code>{user_id}</code>)\n"
                f"🎮 O'yin: <b>{game['title']}</b>\n"
                f"💰 Narxi: <b>{price:,} so'm</b>"
            )
            await bot.send_message(admin_id, admin_msg, parse_mode="HTML")
        except Exception:
            pass

@router.callback_query(F.data.startswith("download_"))
async def cb_download_game(callback: CallbackQuery, bot: Bot):
    game_id = int(callback.data.split("_")[1])
    game = await db.get_game(game_id)
    if not game:
        await callback.answer("⚠️ Ushbu o'yin topilmadi!", show_alert=True)
        return
        
    # Tekin bo'lsa xaridlar tarixiga qo'shish (agar bo'lmasa)
    if not await db.has_user_purchased(callback.from_user.id, game_id):
        await db.add_purchase(callback.from_user.id, game_id, 0)
        
    await db.increment_game_downloads(game_id)
    await callback.answer("📥 O'yin fayli yuborilmoqda...", show_alert=False)
    await send_game_file(callback.message.chat.id, bot, game)

async def send_game_file(chat_id: int, bot: Bot, game):
    caption = (
        f"🎮 <b>{game['title']}</b> vizlom o'yini!\n\n"
        "✅ O'yin muvaffaqiyatli yuklandi.\n"
        "Maroqli hordiq tilaymiz!"
    )
    try:
        await bot.send_document(
            chat_id=chat_id,
            document=game['game_file_id'],
            caption=caption,
            parse_mode="HTML"
        )
    except Exception as e:
        # Agar fayl doc emas, boshqa tipda bo'lsa
        try:
            await bot.send_video(chat_id=chat_id, video=game['game_file_id'], caption=caption, parse_mode="HTML")
        except Exception:
            await bot.send_message(chat_id, f"⚠️ Faylni yuborishda xatolik yuz berdi. Iltimos adminga murojaat qiling.\nFayl ID: {game['game_file_id']}")
