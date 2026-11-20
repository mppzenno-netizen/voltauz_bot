import logging
from aiogram import Bot
from aiogram.enums import ChatMemberStatus
import database as db

logger = logging.getLogger(__name__)

async def check_user_subscriptions(bot: Bot, user_id: int) -> tuple[bool, list]:
    """
    Foydalanuvchi barcha majburiy kanallarga a'zo ekanligini tekshiradi.
    Qaytaradi: (barchasiga_azo: bool, obuna_bolinmagan_kanallar: list)
    """
    channels = await db.get_channels()
    if not channels:
        return True, []
        
    unsubscribed = []
    for ch in channels:
        channel_id = ch['channel_id']
        try:
            # Agar channel_id raqam bo'lsa int ga aylantiramiz
            chat_id = int(channel_id) if (channel_id.startswith('-') or channel_id.isdigit()) else channel_id
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
                unsubscribed.append(ch)
        except Exception as e:
            logger.warning(f"Kanal obunasi tekshirishda xatolik ({channel_id}): {e}")
            # Agar bot kanalga admin qilinmagan bo'lsa yoki xato bersa, uni o'tkazib yuboramiz yoki ko'rsatamiz
            # Obunachiga noqulaylik tug'dirmaslik uchun xatolik berganda unsubscribed ga qo'shmaymiz
            pass
            
    return (len(unsubscribed) == 0), unsubscribed
