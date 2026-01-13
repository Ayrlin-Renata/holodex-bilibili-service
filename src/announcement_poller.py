import asyncio
import time
import json
import re
from datetime import datetime, timezone, timedelta
from bilibili_api import user

class AnnouncementPoller:
    def __init__(self, auth_manager):
        self.auth = auth_manager
        self.seen_dynamic_ids = set()
        
    async def check_channel(self, uid):
        """
        Check specific channel dynamics for stream announcements using V2 API.
        Returns a generator of announcement events.
        """
        if True:
            print(f"[Announce] Polling channel {uid}...")
            u = user.User(uid=uid, credential=self.auth.credential)
            data = await u.get_dynamics_new()
            
            if 'items' not in data:
                return

            for item in data['items']:
                dynamic_id = item.get('id_str')
                
                if dynamic_id in self.seen_dynamic_ids:
                    continue
                self.seen_dynamic_ids.add(dynamic_id)

                modules = item.get('modules', {})
                module_dynamic = modules.get('module_dynamic', {})
                module_author = modules.get('module_author', {})
                pub_ts = module_author.get('pub_ts', int(time.time()))

                additional = module_dynamic.get('additional')
                if additional and additional.get('type') == 'ADDITIONAL_TYPE_RESERVE':
                    reserve = additional.get('reserve')
                    start_ts = reserve.get('stime')
                    
                    # text format like "预计2024-05-03 12:00发布" (UTC+8)
                    desc_text = ""
                    if not start_ts:
                         desc1 = reserve.get('desc1', {}).get('text', '')
                         desc2 = reserve.get('desc2', {}).get('text', '')
                         desc_text = f"{desc1} {desc2}"
                         
                         match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', desc_text)
                         if match:
                             dt_str = match.group(1)
                             try:
                                 dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                                 tz = timezone(timedelta(hours=8))
                                 dt = dt.replace(tzinfo=tz)
                                 start_ts = int(dt.timestamp())
                             except Exception as e:
                                 print(f"[Announce] Failed to parse date '{dt_str}': {e}")

                    now_ts = int(time.time())
                    if start_ts and start_ts < (now_ts - 86400):
                         print(f"[Announce] Ignoring old reservation: {reserve.get('title')} (TS: {start_ts})")
                         continue

                    yield {
                        'event_type': 'RESERVATION',
                        'uid': uid,
                        'dynamic_id': dynamic_id,
                        'timestamp': pub_ts,
                        'details': {
                            'title': reserve.get('title'),
                            'start_ts': start_ts,
                            'description': desc_text or reserve.get('desc1', {}).get('text', ''),
                            'total_count': reserve.get('stotal'),
                        },
                        'raw_data': item
                    }
                    continue

                major = module_dynamic.get('major')
                if major and major.get('type') == 'MAJOR_TYPE_LIVE_RCMD':
                    live_rcmd = major.get('live_rcmd')
                    content = json.loads(live_rcmd.get('content', '{}'))
                    live_info = content.get('live_play_info', {})
                    
                    yield {
                        'event_type': 'ANNOUNCEMENT_LIVE_START',
                        'uid': uid,
                        'dynamic_id': dynamic_id,
                        'timestamp': pub_ts,
                        'details': {
                            'title': live_info.get('title'),
                            'room_id': live_info.get('room_id'),
                            'live_status': live_info.get('live_status'),
                            'link': live_info.get('link'),
                        },
                        'raw_data': item
                    }
                    continue
