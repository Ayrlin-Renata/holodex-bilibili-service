
import asyncio
import os
import json
from dotenv import load_dotenv
from bilibili_api import user, sync, Credential

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

async def fetch_and_dump():
    print("Fetching dynamics using get_dynamics_new()...")
    
    all_data = []

    for uid in TRACKED_UIDS:
        print(f"Fetching for UID: {uid}")
        u = user.User(uid, credential=CREDENTIAL)
        try:
            # get_dynamics_new takes offset string, defaults to empty for first page
            data = await u.get_dynamics_new()
            
            # The structure usually has a 'items' list
            items = data.get('items', [])
            print(f"  Found {len(items)} items.")
            
            for item in items:
                # Add UID for context
                item['_debug_uid'] = uid
                all_data.append(item)
                
        except Exception as e:
            print(f"  Error fetching for {uid}: {e}")

    # Dump to file
    output_file = "debug_dynamics_new.json"
    print(f"Dumping {len(all_data)} items to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print("Done. Please inspect debug_dynamics_new.json for 'reserve' or '预约'.")

if __name__ == "__main__":
    sync(fetch_and_dump())
