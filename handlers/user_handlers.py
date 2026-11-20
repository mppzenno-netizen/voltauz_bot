from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
import database as db
import keyboards as kb
from utils import check_user_subscriptions

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name or ""
    
    await db.add_or_update_user(user_id, username, full_name)
    
    # Obuna tekshirish
    is_subbed, unsubscribed = await check_user_subscriptions(bot, user_id)
    if not is_subbed:
        text = (
            "👋 <b>Assalomu alaykum, hurmatli foydalanuvchi!</b>\n\n"
            "⚠️ <b>Botimizdan to'liq foydalanish uchun quyidagi rasmiy homiy kanallarimizga obuna bo'lishingiz shart:</b>\n\n"
            "<i>Iltimos, kanallarga a'zo bo'lib, so'ng «✅ Obunani tekshirish» tugmasini bosing!</i>"
        )
        await message.answer(text, reply_markup=kb.get_subscription_keyboard(unsubscribed), parse_mode="HTML")
        return

    welcome_text = (
        f"👋 <b>Assalomu alaykum, {message.from_user.mention_html()}!</b>\n\n"
        "🎮 <b>Eng zo'r va so'nggi Vizlom (Mod) O'yinlar olamiga xush kelibsiz!</b>\n\n"
        "✨ <i>Bizning bot orqali siz:</i>\n"
        "• 💎 <b>Eng sara premium va pullik vizlom o'yinlarni qulay narxda xarid qilishingiz;</b>\n"
        "• 🎁 <b>Ommabop tekin vizlom o'yinlarni bir zumda yuklab olishingiz;</b>\n"
        "• 💳 <b>Hisobingizni xavfsiz va tezkor to'ldirishingiz;</b>\n"
        "• 🎮 <b>Xarid qilgan o'yinlaringizni istalgan vaqtda qayta yuklab olishingiz mumkin!</b>\n\n"
        "👇 <b>Quyidagi menyulardan birini tanlang:</b>"
    )
    await message.answer(welcome_text, reply_markup=kb.get_main_keyboard(user_id), parse_mode="HTML")

@router.callback_query(F.data == "check_subscription")
async def cb_check_subscription(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    is_subbed, unsubscribed = await check_user_subscriptions(bot, user_id)
    
    if not is_subbed:
        await callback.answer("⚠️ Hali barcha kanallarga obuna bo'lmadingiz! Iltimos, a'zo bo'ling.", show_alert=True)
        try:
            await callback.message.edit_reply_markup(reply_markup=kb.get_subscription_keyboard(unsubscribed))
        except Exception:
            pass
        return
        
    await callback.answer("✅ Obuna tasdiqlandi! Xush kelibsiz!", show_alert=False)
    await callback.message.delete()
    
    welcome_text = (
        f"🎉 <b>Ajoyib! Obuna muvaffaqiyatli tasdiqlandi.</b>\n\n"
        "🎮 <b>Botdan to'liq foydalanishingiz mumkin! Quyidagi menyudan kerakli bo'limni tanlang:</b>"
    )
    await callback.message.answer(welcome_text, reply_markup=kb.get_main_keyboard(user_id), parse_mode="HTML")

@router.message(F.text == "👤 Profil")
async def menu_profile(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.add_or_update_user(message.from_user.id, message.from_user.username or "", message.from_user.full_name or "")
        user = await db.get_user(message.from_user.id)
        
    purchased_count = await db.count_user_purchases(message.from_user.id)
    
    username_str = f"@{user['username']}" if user['username'] else "Mavjud emas"
    
    profile_text = (
        "👤 <b>SIZNING SHAXSIY PROFILINGIZ</b>\n\n"
        f"🏷 <b>Ismingiz:</b> {user['full_name']}\n"
        f"🔗 <b>Username:</b> {username_str}\n"
        f"🆔 <b>ID raqamingiz:</b> <code>{user['user_id']}</code>\n"
        f"💰 <b>Balansingiz:</b> <b>{user['balance']:,} so'm</b>\n"
        f"🎮 <b>Xarid qilingan o'yinlar:</b> <b>{purchased_count} ta</b>\n"
        f"📅 <b>Ro'yxatdan o'tgan:</b> <i>{user['created_at'][:10]}</i>\n\n"
        "⚡️ <i>Hisobingizni to'ldirish yoki o'yinlaringizni ko'rish uchun quyidagi tugmalardan foydalaning:</i>"
    )
    await message.answer(profile_text, reply_markup=kb.get_profile_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "my_games_inline")
async def cb_my_games(callback: CallbackQuery):
    purchases = await db.get_user_purchases_list(callback.from_user.id)
    if not purchases:
        await callback.answer("⚠️ Siz hali hech qanday o'yin xarid qilmadingiz!", show_alert=True)
        return
        
    text = (
        "🎮 <b>SIZNING XARID QILGAN O'YINLARINGIZ RO'YXATI:</b>\n\n"
        f"Jami: <b>{len(purchases)} ta o'yin</b>\n\n"
        "<i>Quyidagi o'yinlardan birini tanlang va uni bir zumda qayta yuklab oling:</i>"
    )
    await callback.message.answer(text, reply_markup=kb.get_my_games_keyboard(purchases), parse_mode="HTML")
    await callback.answer()

@router.message(F.text == "🎮 Sotib olgan o'yinlarim")
async def menu_my_games(message: Message):
    purchases = await db.get_user_purchases_list(message.from_user.id)
    if not purchases:
        text = (
            "🎮 <b>SOTIB OLGAN O'YINLARINGIZ</b>\n\n"
            "<i>Siz hali birorta o'yin xarid qilmadingiz yoki yuklab olmadingiz.</i>\n\n"
            "💎 <b>«Pullik vizlom o'yinlar»</b> yoki 🎁 <b>«Tekin vizlom o'yinlar»</b> bo'limidan o'zingizga yoqqan o'yinlarni tanlang!"
        )
        await message.answer(text, reply_markup=kb.get_main_keyboard(message.from_user.id), parse_mode="HTML")
        return
        
    text = (
        "🎮 <b>SIZNING XARID QILGAN O'YINLARINGIZ RO'YXATI:</b>\n\n"
        f"Jami: <b>{len(purchases)} ta o'yin</b>\n\n"
        "<i>Istalgan o'yin ustiga bosing va uni qayta yuklab oling:</i>"
    )
    await message.answer(text, reply_markup=kb.get_my_games_keyboard(purchases), parse_mode="HTML")

@router.callback_query(F.data == "back_to_main")
async def cb_back_to_main(callback: CallbackQuery):
    await callback.answer()
    welcome_text = "🏠 <b>Bosh menyudasiz:</b>"
    await callback.message.answer(welcome_text, reply_markup=kb.get_main_keyboard(callback.from_user.id), parse_mode="HTML")
