# UserInfo Bot (Python)

Ushbu bot Telegram foydalanuvchilari, guruhlar va kanallarning IDlarini olishga yordam beradi. Rasmda ko'rsatilgan barcha funksiyalar (User, Premium, Bot, Group, Channel, Forum va boshqalar) qo'shilgan.

## O'rnatish va Ishga tushirish

1. Virtual muhitni faollashtiring (agar hali qilinmagan bo'lsa):
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. Kerakli kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```

3. `.env` faylida o'zingizning bot tokeningizni yozing:
   ```env
   BOT_TOKEN=7279...:AAFjg...
   ```
   *Eslatma: Tokenni [@BotFather](https://t.me/BotFather) orqali olish mumkin.*

4. Botni ishga tushiring:
   ```bash
   python main.py
   ```

## Funksiyalar
- **👤 User**: Foydalanuvchi IDsi.
- **🌟 Premium**: Premium foydalanuvchi IDsi.
- **👽 Bot**: Bot IDsi.
- **👥 Group**: Guruh IDsi.
- **📢 Channel**: Kanal IDsi.
- **💬 Forum**: Mavzulari bor guruh IDsi.
- **👥 My Group/Channel/Forum**: Siz admin bo'lgan chatlarni tanlash.
- **Nusxalash**: IDni ustiga bossangiz, nusxa olish osonlashishi uchun monospace (`code`) ko'rinishida yuboriladi.
