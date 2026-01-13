import json
import os
import asyncio
from dotenv import load_dotenv, set_key
from bilibili_api import Credential, select_client, request_settings

class AuthManager:
    def __init__(self, config_path="cookies.json"):
        self.config_path = config_path
        self.credential = None
        
    def setup(self):
        """Loads credentials and configures the API client."""
        load_dotenv()
        
        print("Configuring network client...")
        try:
            select_client("curl_cffi")
            request_settings.set("impersonate", "chrome131")
        except Exception as e:
            print(f"Warning: Failed to set up curl_cffi client: {e}")
            print("Falling back to default client, which may be more susceptible to rate limits.")

        self.credential = self._load_from_file()
        return self.credential

    def reload(self):
        """Forces a reload of credentials from the environment."""
        print("Reloading credentials...")
        load_dotenv(override=True)
        self.credential = self._load_from_file()
        return self.credential
    
    def _load_from_file(self):
        if os.getenv("SESSDATA"):
            print("Loading credentials from Environment Variables (.env)...")
            return Credential(
                sessdata=os.getenv("SESSDATA"),
                bili_jct=os.getenv("BILI_JCT") or "",
                buvid3=os.getenv("BUVID3"),
                dedeuserid=os.getenv("DEDEUSERID"),
                ac_time_value=os.getenv("AC_TIME_VALUE")
            )

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                
                cred = Credential(
                    sessdata=cookies.get("sessdata"),
                    bili_jct=cookies.get("bili_jct"),
                    buvid3=cookies.get("buvid3"),
                    dedeuserid=cookies.get("dedeuserid"),
                    ac_time_value=cookies.get("ac_time_value")
                )
                print(f"Loaded credentials for DedeUserID: {cookies.get('dedeuserid')}")
                return cred
            except Exception as e:
                print(f"Error loading {self.config_path}: {e}")
                return None
        
        print("No credentials found in .env or cookies.json.")
        print("Please copy .env.example to .env and fill in your values.")
        return None

    async def check_validity(self):
        """Async check if credentials are valid."""
        if not self.credential:
            return False
        return await self.credential.check_valid()

    async def refresh_cookies(self):
        """Attempts to refresh the session using the stored refresh token."""
        if not self.credential:
            print("No credential loaded, cannot refresh.")
            return False
            
        try:
            print("Refreshing session cookies...")
            await self.credential.refresh()
            
            print("Saving new cookies to .env...")
            env_path = ".env"
            set_key(env_path, "SESSDATA", self.credential.sessdata)
            set_key(env_path, "BILI_JCT", self.credential.bili_jct)
            set_key(env_path, "DEDEUSERID", self.credential.dedeuserid)
            set_key(env_path, "BUVID3", self.credential.buvid3)
            
            if self.credential.ac_time_value:
                set_key(env_path, "AC_TIME_VALUE", self.credential.ac_time_value)
                
            return True
        except Exception as e:
            print(f"Failed to refresh session: {e}")
            return False
