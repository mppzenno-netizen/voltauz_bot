import logging
from aiogram import Bot
from aiogram.enums import ChatMemberStatus
import database as db

logger = logging.getLogger(__name__)

async def check_user_subscriptions(bot: Bot, user_id: int) -> tuple[bool, list]:
    """
    Foydalanuvchi barcha majburiy kanallarga a'zo ekanligini yoki
    maxfiy kanallarga so'rov (join request) yuborganligini tekshiradi.
    Qaytaradi: (barchasiga_azo_yoki_sorov_yuborgan: bool, obuna_bolinmagan_kanallar: list)
    """
    channels = await db.get_channels()
    if not channels:
        return True, []
        
    unsubscribed = []
    for ch in channels:
        channel_id = ch['channel_id']
        is_ok = False
        
        # 1. Avval bazada so'rov (join request) yuborganmi tekshiramiz
        if await db.has_sent_join_request(user_id, channel_id):
            is_ok = True
            
        # 2. Agar bazada bo'lmasa, Telegram API orqali tekshiramiz
        if not is_ok:
            try:
                chat_id = int(channel_id) if (channel_id.startswith('-') or channel_id.isdigit()) else channel_id
                member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                # Agar obuna bo'lgan yoki admin bo'lsa
                if member.status in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED]:
                    is_ok = True
            except Exception as e:
                # Agar bot kanalda a'zolikni ko'ra olmasa yoki xato bersa, foydalanuvchini to'xtatib qo'ymaslik
                logger.warning(f"Kanal obunasini tekshirishda ogohlantirish ({channel_id}): {e}")
                
        if not is_ok:
            unsubscribed.append(ch)
            
    return (len(unsubscribed) == 0), unsubscribed
