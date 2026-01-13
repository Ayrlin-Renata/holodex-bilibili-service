import asyncio
import time
from bilibili_api import user, live

class LiveMonitor:
    def __init__(self, auth_manager):
        self.auth = auth_manager
        self.states = {}
        
    async def check_channel(self, uid):
        """
        Polls live room status for the Single UID and yields events.
        """
        if True:
            print(f"[Monitor] Checking UID {uid}...")
            
            u = user.User(uid, credential=self.auth.credential)
            info = await u.get_live_info()
            
            live_room = info.get('live_room', {})
            room_id = live_room.get('roomid')
            
            if not room_id:
                print(f"[Monitor]  -> No room ID found for {uid}")
                return
                
            curr_status = live_room.get('liveStatus')
            curr_title = live_room.get('title')
            curr_url = live_room.get('url')
            
            prev_state = self.states.get(uid, {})
            prev_status = prev_state.get('live_status')
            prev_title = prev_state.get('title')
            
            if uid not in self.states:
                self.states[uid] = {
                    'room_id': room_id,
                    'live_status': curr_status,
                    'title': curr_title
                }
                status_str = "🔴 LIVE" if curr_status == 1 else "⚫ Offline"
                print(f"[Monitor]  -> Initialized {uid}: {status_str} (Room {room_id})")
                
                yield {
                    'event_type': 'STATE_SYNC',
                    'uid': uid,
                    'room_id': room_id,
                    'timestamp': int(time.time()),
                    'details': {
                        'title': curr_title,
                        'live_status': curr_status,
                        'link': curr_url
                    }
                }
                return

            events_to_yield = []

            if curr_status != prev_status:
                if curr_status == 1:
                    print(f"[Monitor]  -> {uid} went LIVE!")
                    events_to_yield.append({
                        'event_type': 'STREAM_START',
                        'uid': uid,
                        'room_id': room_id,
                        'timestamp': int(time.time()),
                        'details': {
                            'title': curr_title,
                            'room_id': room_id,
                            'link': curr_url
                        }
                    })
                else:
                    print(f"[Monitor]  -> {uid} went OFFLINE")
                    events_to_yield.append({
                        'event_type': 'STREAM_END',
                        'uid': uid,
                        'room_id': room_id,
                        'timestamp': int(time.time()),
                        'details': {
                            'title': curr_title,
                            'room_id': room_id
                        }
                    })
            
            if curr_title != prev_title:
                print(f"[Monitor]  -> Title changed for {uid}")
                events_to_yield.append({
                    'event_type': 'TITLE_CHANGE',
                    'uid': uid,
                    'room_id': room_id,
                    'timestamp': int(time.time()),
                    'details': {
                        'old_title': prev_title,
                        'new_title': curr_title,
                        'room_id': room_id
                    }
                })

            if not events_to_yield:
                print(f"[Monitor]  -> No changes for {uid}")

            if curr_status != prev_status or curr_title != prev_title:
                    self.states[uid] = {
                    'room_id': room_id,
                    'live_status': curr_status,
                    'title': curr_title
                }
            
            for ev in events_to_yield:
                yield ev

    async def stop(self):
        self.states.clear()
