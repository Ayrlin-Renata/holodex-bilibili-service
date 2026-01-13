
import asyncio
import os
import json
import datetime
from dotenv import load_dotenv
from bilibili_api import user, live, sync, Credential

# Load environment variables
load_dotenv()

SESSDATA = os.getenv('SESSDATA')
BILI_JCT = os.getenv('BILI_JCT')
BUVID3 = os.getenv('BUVID3')
DEDEUSERID = os.getenv('DEDEUSERID')
AC_TIME_VALUE = os.getenv('AC_TIME_VALUE')

CREDENTIAL = Credential(
    sessdata=SESSDATA,
    bili_jct=BILI_JCT,
    buvid3=BUVID3,
    dedeuserid=DEDEUSERID,
    ac_time_value=AC_TIME_VALUE
)

# Test UIDs
TRACKED_UIDS = [
    286700005, # Hololive Official
    321219231  # User provided reference channel
]

async def check_live_status():
    print("Checking Live Room Status directly from UIDs...")
    
    for uid in TRACKED_UIDS:
        print(f"\n--- Checking UID: {uid} ---")
        try:
            # 1. Get User's Live Info (this links UID -> Room ID)
            u = user.User(uid, credential=CREDENTIAL)
            live_info = await u.get_live_info()
            
            # This returns a dictionary with room Status
            # Usually: { 'live_room': { ... }, ... }
            
            live_room = live_info.get('live_room', {})
            room_id = live_room.get('roomid')
            live_status = live_room.get('liveStatus') # 1 = Live, 0 = Offline
            title = live_room.get('title')
            url = live_room.get('url')
            
            print(f"User Live Info:")
            print(f"  Room ID: {room_id}")
            print(f"  Status: {'🔴 LIVE' if live_status == 1 else '⚫ Offline'} (Code: {live_status})")
            print(f"  Title: {title}")
            print(f"  URL: {url}")

            # 2. If we want deeper details (like start time), we *might* need the Room API
            # referencing the room_id we just found.
            if room_id:
                # Use the LiveRoom class to get detailed info
                room = live.LiveRoom(room_id, credential=CREDENTIAL)
                room_info = await room.get_room_info()
                room_play_info = await room.get_room_play_info()
                
                print(f"Room Detail Info:")
                # start_time is often inside room_info -> room_info -> live_start_time
                # live_start_time is usually significant only if live_status is 1
                
                inner_info = room_info.get('room_info', {})
                start_ts = inner_info.get('live_start_time')
                
                if start_ts:
                    dt_object = datetime.datetime.fromtimestamp(start_ts)
                    print(f"  Start Time: {dt_object} (TS: {start_ts})")
                
                print(f"  Key Frame: {inner_info.get('keyframe')}")

        except Exception as e:
            print(f"  Error fetching for {uid}: {e}")

if __name__ == "__main__":
    sync(check_live_status())
