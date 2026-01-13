import asyncio
import json
import os
import random
from auth_manager import AuthManager
from announcement_poller import AnnouncementPoller
from live_monitor import LiveMonitor
from scheduler import Scheduler, GlobalRateLimiter
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_DIR, "output", "stream_events.jsonl")

# target cycle to check all channel live status (seconds)
TARGET_CYCLE_INTERVAL = 300
# target cycle to check all channel announcement (seconds)
ANNOUNCEMENT_CYCLE_INTERVAL = 1800
# min delay between API requests (seconds) (probably dont go lower than 1)
MIN_REQUEST_DELAY = 5 
# jitter for requests
JITTER = 3.0

_uids_str = os.getenv("TRACKED_UIDS", "")
TRACKED_UIDS = [int(u.strip()) for u in _uids_str.split(",") if u.strip().isdigit()] if _uids_str else []
if not TRACKED_UIDS:
    print("Warning: TRACKED_UIDS is empty in .env") 

async def event_handler(event):
    """Callback for handling events from Poller and Monitor."""
    log_msg = f"[{event['event_type']}] Room/UID: {event.get('room_id') or event.get('uid')} - TS: {event.get('timestamp')}"
    print(log_msg)
    
    if event['event_type'] == 'RESERVATION':
        details = event.get('details', {})
        print(f"  Scheduled: {details.get('title')} @ {details.get('description')} (TS: {details.get('start_ts')})")
        
    elif event['event_type'] == 'ANNOUNCEMENT_LIVE_START':
        details = event.get('details', {})
        print(f"  Live Announcement: {details.get('title')} (Room: {details.get('room_id')})")

    elif event['event_type'] == 'STREAM_START':
        details = event.get('details', {})
        print(f"  🔴 Stream Begin: {details.get('title')} (Room: {details.get('room_id')})")

    elif event['event_type'] == 'STREAM_END':
        details = event.get('details', {})
        print(f"  ⚫ Stream End: {details.get('title')} (Room: {details.get('room_id')})")

    elif event['event_type'] == 'TITLE_CHANGE':
        details = event.get('details', {})
        print(f"  Title Updated: '{details.get('old_title')}' -> '{details.get('new_title')}'")

    elif event['event_type'] == 'STATE_SYNC':
        details = event.get('details', {})
        status = "🔴 LIVE" if details.get('live_status') == 1 else "⚫ Offline"
        print(f"  State Sync: {status} | Title: {details.get('title')}")

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

async def main():
    print("Starting Bilibili Stream Tracker PoC...")
    
    auth = AuthManager()
    cred = auth.setup()
    if not cred:
        print("Authentication failed or config missing. Exiting.")
        return

    poller = AnnouncementPoller(auth)
    monitor = LiveMonitor(auth)
    
    live_scheduler = Scheduler(TRACKED_UIDS, interval=TARGET_CYCLE_INTERVAL, min_delay=MIN_REQUEST_DELAY, jitter=JITTER)
    announce_scheduler = Scheduler(TRACKED_UIDS, interval=ANNOUNCEMENT_CYCLE_INTERVAL, min_delay=MIN_REQUEST_DELAY, jitter=JITTER)
    
    global_limiter = GlobalRateLimiter(min_delay=MIN_REQUEST_DELAY)

    is_monitoring = False
    
    async def start_monitoring():
        nonlocal is_monitoring
        if not is_monitoring:
            print("Starting live monitor (polling mode)...")
            is_monitoring = True

    async def stop_monitoring():
        nonlocal is_monitoring
        if is_monitoring:
            print("Pausing live monitor...")
            await monitor.stop()
            is_monitoring = False

    if await auth.check_validity():
        await start_monitoring()
    else:
        print("Warning: Cookies are invalid at startup. Waiting for updates...")
    
    print("Service running. Press Ctrl+C to stop.")
    
    async def cookie_watchdog():
        while True:
            await asyncio.sleep(60) 
            try:
                if not await auth.check_validity():
                    print("⚠️ Cookies Invalid/Expired! Attempting auto-refresh...")
                    if await auth.refresh_cookies():
                         print("✅ Cookies refreshed automatically via refresh_token!")
                    else:
                        print("❌ Auto-refresh failed. Please login using login_service.py")
                        await stop_monitoring()
                        
                        while not await auth.check_validity():
                            await asyncio.sleep(10)
                            auth.reload()
                        
                        print("✅ Cookies updated and valid! Resuming...")
                        await start_monitoring()
            except Exception as e:
                print(f"Error in cookie watchdog: {e}")

    async def live_loop():
        while True:
            uid = await live_scheduler.next_uid()
            if not uid: continue
            
            try:
                await global_limiter.wait()
                
                if is_monitoring:
                    async for event in monitor.check_channel(uid):
                        await event_handler(event)
                    global_limiter.report_success()
                else:
                    await asyncio.sleep(5)
            except Exception as e:
                err_str = str(e)
                if "412" in err_str or "429" in err_str:
                     global_limiter.trigger_backoff()
                else:
                    print(f"[Monitor] Error checking live status for {uid}: {e}")

    async def announce_loop():
        while True:
            uid = await announce_scheduler.next_uid()
            if not uid: continue
            
            try:
                await global_limiter.wait()
                
                async for ann in poller.check_channel(uid):
                    await event_handler(ann)
                global_limiter.report_success()
            except Exception as e:
                err_str = str(e)
                if "412" in err_str or "429" in err_str:
                     global_limiter.trigger_backoff()
                else:
                    print(f"[Announce] Error polling channel {uid}: {e}")

    try:
        await asyncio.gather(
            cookie_watchdog(),
            live_loop(),
            announce_loop()
        )
    except KeyboardInterrupt:
        print("Stopping service...")
    finally:
        await monitor.stop()
        print("Service stopped.")

if __name__ == "__main__":
    asyncio.run(main())
