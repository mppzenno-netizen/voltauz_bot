import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, ADMIN_IDS
import database as db
from handlers.user_handlers import router as user_router
from handlers.games_handlers import router as games_router
from handlers.payment_handlers import router as payment_router
from handlers.admin_handlers import router as admin_router
from tolov_service import check_payment_status_api

# Log sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def background_payment_checker(bot: Bot):
    """
    Orqa fonda har 15 soniyada pending to'lovlarni avtomatik tekshiruvchi funksiya.
    Foydalanuvchi tekshirish tugmasini bosmasa ham, to'lov tushishi bilan
    avtomatik ravishda balansi to'ldiriladi!
    """
    logger.info("Avtomatik to'lov tekshiruvchi fon xizmati ishga tushdi.")
    while True:
        try:
            pending_list = await db.get_pending_payments()
            for pay in pending_list:
                payment_id = pay["payment_id"]
                user_id = pay["user_id"]
                amount = pay["amount"]
                
                status_res = await check_payment_status_api(payment_id)
                status = status_res.get("status")
                
                if status == "paid":
                    is_fresh = await db.mark_payment_paid(payment_id)
                    if is_fresh:
                        await db.update_user_balance(user_id, amount)
                        user = await db.get_user(user_id)
                        
                        # Foydalanuvchiga xabar
                        try:
                            msg = (
                                "🎉 <b>HISOBINGIZ TO'LDIRILDI!</b>\n\n"
                                f"💰 <b>To'lov summasi:</b> <b>+{amount:,} so'm</b>\n"
                                f"💳 <b>Yangi balansingiz:</b> <b>{user['balance']:,} so'm</b>\n\n"
                                "✨ <i>Endi o'yinlar bo'limiga o'tib, xohlagan vizlom o'yiningizni xarid qilishingiz mumkin!</i>"
                            )
                            await bot.send_message(user_id, msg, parse_mode=ParseMode.HTML)
                        except Exception as e:
                            logger.error(f"Foydalanuvchiga xabar yuborishda xatolik: {e}")
                            
                        # Adminga bildirishnoma
                        for admin_id in ADMIN_IDS:
                            try:
                                admin_notice = (
                                    "⚡️ <b>[AVTO-TOLOV] Yangi to'lov tushdi!</b>\n\n"
                                    f"👤 Foydalanuvchi ID: <code>{user_id}</code>\n"
                                    f"💵 Summa: <b>{amount:,} so'm</b>\n"
                                    f"🆔 To'lov ID: <code>{payment_id}</code>"
                                )
                                await bot.send_message(admin_id, admin_notice, parse_mode=ParseMode.HTML)
                            except Exception:
                                pass
                                
                elif status == "cancel":
                    await db.mark_payment_cancelled(payment_id)
                    
        except Exception as e:
            logger.error(f"Background payment checker xatosi: {e}")
            
        await asyncio.sleep(15)

async def main():
    # Bazani ishga tushirish
    await db.init_db()
    logger.info("Ma'lumotlar bazasi muvaffaqiyatli ishga tushdi.")
    
    # Bot va Dispatcher yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Routerlarni ulash
    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(games_router)
    dp.include_router(payment_router)
    
    # Orqa fon to'lov tekshiruvchisini ishga tushirish
    asyncio.create_task(background_payment_checker(bot))
    
    # Bot ma'lumotlarini olish
    bot_info = await bot.get_me()
    logger.info(f"Bot muvaffaqiyatli ishga tushdi: @{bot_info.username} (ID: {bot_info.id})")
    
    # Pollingni boshlash
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
