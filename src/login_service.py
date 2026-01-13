import asyncio
import os
from bilibili_api import login_v2
import qrcode
from dotenv import set_key

ENV_PATH = ".env"

async def main():
    print("Initializing QR Code Login...")
    
    qr_login = login_v2.QrCodeLogin()
    
    await qr_login.generate_qrcode()
    
    try:
        url = qr_login._QrCodeLogin__qr_link
        
        img = qrcode.make(url)
        img_filename = "login_qrcode.png"
        img.save(img_filename)
        print(f"QR Code saved to {img_filename}")
        
        os.startfile(img_filename)
        print("Opening QR code in default image viewer...")
        
    except Exception as e:
        print(f"Failed to open image viewer: {e}")
        try:
            qr_terminal = qr_login.get_qrcode_terminal()
            print("\nPlease scan the QR code below with your Bilibili App:\n")
            print(qr_terminal)
        except:
             pass
    
    print("Waiting for scan...")
    while True:
        status = await qr_login.check_state()
        
        if status == login_v2.QrCodeLoginEvents.SCAN:
            pass
        elif status == login_v2.QrCodeLoginEvents.CONF:
            print("Scanned! Please confirm login on your phone.")
        elif status == login_v2.QrCodeLoginEvents.DONE:
            print("\nLogin Successful!")
            cred = qr_login.get_credential()
            break
        elif status == login_v2.QrCodeLoginEvents.TIMEOUT:
            print("QR Code expired. Please restart the script.")
            return
            
        await asyncio.sleep(2)
        
    print("Saving credentials to .env...")
    if not os.path.exists(ENV_PATH):
        with open(ENV_PATH, "w") as f:
            f.write("")
            
    try:
        if cred.sessdata: set_key(ENV_PATH, "SESSDATA", cred.sessdata)
        if cred.bili_jct: set_key(ENV_PATH, "BILI_JCT", cred.bili_jct)
        if cred.buvid3: set_key(ENV_PATH, "BUVID3", cred.buvid3)
        if cred.dedeuserid: set_key(ENV_PATH, "DEDEUSERID", str(cred.dedeuserid))
        
        if cred.ac_time_value:
             set_key(ENV_PATH, "AC_TIME_VALUE", cred.ac_time_value)
             print(f"Saved Refresh Token (AC_TIME_VALUE): {cred.ac_time_value[:10]}...")
             
        print("\nCredentials saved successfully! You can now run main.py.")
        
    except Exception as e:
        print(f"Error saving to .env: {e}")
        print("Please manually save these values:")
        print(f"SESSDATA={cred.sessdata}")
        print(f"BILI_JCT={cred.bili_jct}")
        print(f"BUVID3={cred.buvid3}")
        print(f"DEDEUSERID={cred.dedeuserid}")
        print(f"AC_TIME_VALUE={cred.ac_time_value}")

if __name__ == "__main__":
    asyncio.run(main())
