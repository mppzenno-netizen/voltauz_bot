# 🎮 O'yinlar Vizlom Telegram Bot (Premium & Fast)

Professional darajada tayyorlangan, xavfsiz va tezkor vizlom (mod) o'yinlar do'koni boti.

---

## 🌟 Bot Imkoniyatlari:

### 👤 Foydalanuvchilar uchun:
1. **Majburiy kanallarga a'zo bo'lish**:
   - Botga start bosganda admin qo'shgan kanallarga obuna bo'lish so'raladi.
   - Maxfiy yoki ochiq havolalar qo'llab-quvvatlanadi.
   - «✅ Obunani tekshirish» orqali bir zumda tekshiruv.
2. **💎 Pullik vizlom o'yinlar bo'limi**:
   - 3x2 (bir tomonda 3 ta, bu tomonda 3 ta) zamonaviy inline tugmalar.
   - Sahifalash (Oldingi / Keyingi navigatsiyasi).
   - O'yin rasmi, to'liq tavsifi, narxi va yuklanishlar soni.
   - Hisobida mablag' yetarli bo'lsa xarid qilish va o'yin faylini olish.
   - Yetarli bo'lmasa to'ldirish taklifi.
3. **🎁 Tekin vizlom o'yinlar bo'limi**:
   - 3x2 panjara ko'rinishidagi ro'yxat.
   - Har bir o'yin haqida ma'lumot va mutlaqo bepul yuklab olish.
4. **👤 Profil**:
   - Foydalanuvchi ismi, @username, Telegram ID.
   - Hozirgi balansi (so'mda).
   - Xarid qilingan o'yinlar soni va ro'yxatdan o'tgan sana.
5. **💳 Hisob to'ldirish (TolovAPI integratsiyasi)**:
   - Foydalanuvchi istalgan summani kiritadi (masalan: `10000`).
   - TolovAPI orqali karta raqami va aniq summa ko'rsatiladi.
   - **Karta raqami ustiga bir marta bosganda darhol nusxalanadi (`<code>` tegi bilan)**.
   - Summa qat'iy ogohlantirish bilan beriladi.
   - **🔄 To'lovni tekshirish** va **❌ Bekor qilish** tugmalari.
   - **Avtomatik fon tekshiruvchisi (Background task)**: Foydalanuvchi tekshirishni bosmasa ham har 15 soniyada to'lov tekshirilib, pul tushgach avtomatik balansi oshiriladi!
6. **🎮 Sotib olgan o'yinlarim**:
   - Foydalanuvchi shu paytgacha xarid qilgan barcha o'yinlar ro'yxati.
   - Istalgan vaqtda qayta bepul yuklab olish imkoniyati.

---

### 👑 Administrator uchun (`/admin` yoki «👑 Admin Panel» tugmasi):
1. **📊 To'liq statistika**:
   - Jami foydalanuvchilar soni.
   - Bugun qo'shilganlar.
   - To'lov qilgan va faqat tekin foydalanganlar soni.
   - Shu oyda va jami aylanma pul (tushum) summasi.
   - Jami o'yinlar va yuklab olishlar soni.
2. **🎮 O'yin qo'shish (FSM orqali oson)**:
   - Turi: Pullik yoki Tekin.
   - Nomi, tavsifi, rasmi, narxi (pullik bo'lsa) va fayli (APK, zip, doc).
3. **🗑 O'yinlarni o'chirish**:
   - Ro'yxatdan bitta bosish orqali keraksiz o'yinlarni o'chirish.
4. **📢 Majburiy kanallar boshqaruvi**:
   - Yangi kanal qo'shish (Havola, ko'rinadigan nom, Kanal ID). Maxfiy havolalarni ham ulay olasiz!
   - Mavjud kanallarni o'chirish.
5. **✉️ Reklama va xabar yuborish (Broadcast)**:
   - Barcha bot a'zolariga rasm, video, matn yoki havola bilan xabar yuborish.
   - Yakuniy hisobot (yetkazilganlar va bloklaganlar).
6. **💰 Foydalanuvchi balansini boshqarish**:
   - Telegram ID orqali istalgan foydalanuvchi balansiga pul qo'shish yoki ayirish.

---

## 🚀 Botni ishga tushirish:

### 1-usul (Juda oson):
Papka ichidagi `run_bot.bat` fayliga 2 marta bosing!

### 2-usul (Terminal / PowerShell orqali):
```bash
python main.py
```
