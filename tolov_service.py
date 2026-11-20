import aiohttp
from config import TOLOV_API_URL, SHOP_ID, SHOP_KEY

async def _api_request(path: str, params: dict, method: str = "POST") -> dict:
    """TolovAPI ga so'rov yuborish (Asinxron)"""
    body = {"shop_id": SHOP_ID, **params}
    headers = {"X-Shop-Key": SHOP_KEY}
    url = TOLOV_API_URL.rstrip("/") + "/" + path.lstrip("/")
    
    try:
        async with aiohttp.ClientSession() as session:
            if method.upper() == "GET":
                async with session.get(url, params=body, headers=headers, timeout=15) as resp:
                    return await resp.json()
            else:
                async with session.post(url, json=body, headers=headers, timeout=15) as resp:
                    return await resp.json()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

async def create_payment_api(order_id: str, amount: int) -> dict:
    """
    To'lov yaratish.
    Javob:
    {
        "ok": True,
        "payment_id": "...",
        "amount": 50000,
        "card_number": "8600...",
        "card_last4": "1234",
        "expires_at": 169...
    }
    yoki agar error_code == "amount_busy" bo'lsa:
    {"ok": False, "error_code": "amount_busy", "suggested_amount": 50001}
    """
    res = await _api_request("payment/create", {"amount": amount, "order_id": order_id})
    if res.get("error_code") == "amount_busy" and "suggested_amount" in res:
        # Summa band bo'lsa, avtomatik taklif qilingan summa bilan yaratishga urinib ko'rish
        suggested = res["suggested_amount"]
        res2 = await _api_request("payment/create", {"amount": suggested, "order_id": order_id})
        if res2.get("ok"):
            res2["was_busy_suggested"] = True
            return res2
    return res

async def check_payment_status_api(payment_id: str) -> dict:
    """
    Holatni tekshirish:
    status: pending (kutilmoqda) | paid (to'landi) | cancel (bekor)
    """
    return await _api_request("payment/status", {"payment_id": payment_id}, method="GET")

async def cancel_payment_api(payment_id: str) -> dict:
    """To'lovni bekor qilish"""
    return await _api_request("payment/cancel", {"payment_id": payment_id})
