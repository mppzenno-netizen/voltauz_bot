import time
import uuid
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database as db
import keyboards as kb
from tolov_service import create_payment_api, check_payment_status_api, cancel_payment_api
from config import ADMIN_IDS

router = Router()

class TopUpState(StatesGroup):
    waiting_for_amount = State()

@router.message(F.text == "💳 Hisob to'ldirish")
async def menu_top_up(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "💳 <b>HISOBNI TO'LDIRISH</b>\n\n"
        "💰 <b>Qancha summa to'lov qilmoqchisiz?</b>\n"
        "<i>Minimal summa: 1 000 so'm.</i>\n\n"
        "👇 <b>Iltimos, to'ldirmoqchi bo'lgan summani faqat raqamlarda kiriting:</b>\n"
        "<i>Masalan: 10000 yoki 50000</i>"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_fsm")]
    ])
    await message.answer(text, reply_markup=markup, parse_mode="HTML")
    await state.set_state(TopUpState.waiting_for_amount)

@router.callback_query(F.data == "top_up_balance")
async def cb_top_up_balance(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        "💳 <b>HISOBNI TO'LDIRISH</b>\n\n"
        "💰 <b>Qancha summa to'lov qilmoqchisiz?</b>\n"
        "<i>Minimal summa: 1 000 so'm.</i>\n\n"
        "👇 <b>Iltimos, to'ldirmoqchi bo'lgan summani faqat raqamlarda kiriting:</b>\n"
        "<i>Masalan: 10000 yoki 50000</i>"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_fsm")]
    ])
    await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")
    await state.set_state(TopUpState.waiting_for_amount)
    await callback.answer()

@router.callback_query(F.data == "cancel_fsm")
async def cb_cancel_fsm(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Bekor qilindi.")
    await callback.message.edit_text("❌ <b>Amaliyot bekor qilindi.</b>", parse_mode="HTML")

@router.message(TopUpState.waiting_for_amount)
async def process_amount_input(message: Message, state: FSMContext, bot: Bot):
    amount_str = message.text.replace(" ", "").replace(",", "").replace(".", "").strip()
    
    if not amount_str.isdigit():
        await message.answer("⚠️ <b>Iltimos, faqat raqam kiriting!</b> (Masalan: <code>15000</code>)", parse_mode="HTML")
        return
        
    amount = int(amount_str)
    if amount < 1000:
        await message.answer("⚠️ <b>Minimal to'lov summasi 1 000 so'm!</b> Qayta kiriting:", parse_mode="HTML")
        return
        
    if amount > 10000000:
        await message.answer("⚠️ <b>Maksimal bir martalik to'lov 10 000 000 so'm!</b>", parse_mode="HTML")
        return

    await state.clear()
    
    wait_msg = await message.answer("🔄 <b>To'lov ma'lumotlari shakllantirilmoqda, iltimos kuting...</b>", parse_mode="HTML")
    
    order_id = f"ord_{message.from_user.id}_{int(time.time())}"
    
    pay_data = await create_payment_api(order_id, amount)
    
    if not pay_data.get("ok"):
        err = pay_data.get("error", "Noma'lum xatolik")
        await wait_msg.edit_text(f"❌ <b>To'lov tizimida xatolik yuz berdi:</b>\n<code>{err}</code>\nIltimos, birozdan so'ng qayta urinib ko'ring.", parse_mode="HTML")
        return
        
    payment_id = pay_data["payment_id"]
    card_number = pay_data.get("card_number", "")
    exact_amount = pay_data.get("amount", amount)
    
    # Bazaga saqlash
    await db.save_payment_record(
        payment_id=payment_id,
        order_id=order_id,
        user_id=message.from_user.id,
        amount=exact_amount,
        card_number=card_number
    )
    
    card_display = f"<code>{card_number}</code>" if card_number else "<i>Tizim tomonidan beriladi</i>"
    
    # Matn va dizayn
    bill_text = (
        "💳 <b>TO'LOV CHEKI VA KO'RSATMA:</b>\n\n"
        f"💳 <b>Karta raqami:</b>\n👉 {card_display} 👈\n"
        "<i>(Karta raqami ustiga bir marta bossangiz, o'zi nusxalanadi!)</i>\n\n"
        f"💵 <b>To'lov summasi:</b>\n👉 <code>{exact_amount:,}</code> <b>so'm</b> 👈\n\n"
        "⚠️ <b>DIQQAT! JUDA MUHIM TALAB:</b>\n"
        f"❗️ <b>Aynan ko'rsatilgan <code>{exact_amount:,}</code> so'm miqdorida to'lang!</b>\n"
        "❗️ <b>Ushbu summadan oshib ham, kamayib ham ketmasin, aks holda to'lov tizim tomonidan qabul qilinmaydi va hisobingizga tushmaydi!</b>\n\n"
        "⏳ <b>Amal qilish vaqti:</b> <i>5 daqiqa</i>\n\n"
        "<i>To'lovni amalga oshirgach, pastdagi «🔄 To'lovni tekshirish» tugmasini bosing!</i>"
    )
    
    await wait_msg.edit_text(bill_text, reply_markup=kb.get_payment_keyboard(payment_id), parse_mode="HTML")

@router.callback_query(F.data.startswith("chkpay_"))
async def cb_check_payment(callback: CallbackQuery, bot: Bot):
    payment_id = callback.data.split("_")[1]
    
    # Foydalanuvchiga darhol animatsiya
    await callback.answer("🔍 To'lov tekshirilmoqda...", show_alert=False)
    
    # Status tekshirish
    status_data = await check_payment_status_api(payment_id)
    status = status_data.get("status")
    
    if status == "paid":
        # Bazada holatni paid qilish va balans qo'shish
        is_fresh = await db.mark_payment_paid(payment_id)
        pay_record = await db.get_payment_record(payment_id)
        
        if is_fresh and pay_record:
            user_id = pay_record["user_id"]
            amount = pay_record["amount"]
            
            # Balansni oshirish
            await db.update_user_balance(user_id, amount)
            user = await db.get_user(user_id)
            
            success_text = (
                "🎉 <b>TO'LOV MUVAFFAQIYATLI AMALGA OSHIRILDI!</b>\n\n"
                f"💰 <b>Qabul qilingan summa:</b> <b>+{amount:,} so'm</b>\n"
                f"💳 <b>Yangi balansingiz:</b> <b>{user['balance']:,} so'm</b>\n\n"
                "✨ <i>Hisobingiz muvaffaqiyatli to'ldirildi. O'yinlar xarid qilishingiz mumkin!</i>"
            )
            try:
                await callback.message.edit_text(success_text, parse_mode="HTML")
            except Exception:
                await callback.message.answer(success_text, parse_mode="HTML")
                
            # Adminga bildirishnoma
            for admin_id in ADMIN_IDS:
                try:
                    admin_notice = (
                        "💰 <b>YANGI TO'LOV TUSHDI!</b>\n\n"
                        f"👤 Foydalanuvchi: {callback.from_user.mention_html()} (ID: <code>{user_id}</code>)\n"
                        f"💵 Summa: <b>{amount:,} so'm</b>\n"
                        f"🆔 To'lov ID: <code>{payment_id}</code>\n"
                        f"💳 Karta: <code>{pay_record['card_number']}</code>"
                    )
                    await bot.send_message(admin_id, admin_notice, parse_mode="HTML")
                except Exception:
                    pass
        else:
            await callback.answer("✅ Ushbu to'lov allaqachon hisobingizga qo'shilgan!", show_alert=True)
            try:
                await callback.message.delete()
            except Exception:
                pass
                
    elif status == "pending":
        await callback.answer("⏳ To'lov hali qabul qilinmadi.\nPul o'tkazgan bo'lsangiz, bank tasdiqlashi uchun 10-20 soniya kuting va qayta bosing!", show_alert=True)
        
    elif status == "cancel":
        await db.mark_payment_cancelled(payment_id)
        await callback.answer("❌ Ushbu to'lov bekor qilingan yoki muddati tugagan!", show_alert=True)
        try:
            await callback.message.edit_text("❌ <b>To'lov bekor qilingan yoki muddati (5 daqiqa) tugagan.</b>", parse_mode="HTML")
        except Exception:
            pass
    else:
        err = status_data.get("error", "Holatni aniqlab bo'lmadi")
        await callback.answer(f"⚠️ {err}", show_alert=True)

@router.callback_query(F.data.startswith("cnlpay_"))
async def cb_cancel_payment(callback: CallbackQuery):
    payment_id = callback.data.split("_")[1]
    await cancel_payment_api(payment_id)
    await db.mark_payment_cancelled(payment_id)
    await callback.answer("To'lov bekor qilindi.")
    try:
        await callback.message.edit_text("❌ <b>To'lov bekor qilindi.</b>", parse_mode="HTML")
    except Exception:
        pass
