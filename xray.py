#!/usr/bin/env python3

import os
import subprocess
import random
import json
import uuid
import base64
import requests

def check_root():
    if os.geteuid() != 0:
        print("Error: This script must be run as root!")
        exit(1)

def update_system():
    print("正在更新系统和安装依赖...")
    if os.path.exists("/usr/bin/apt"): # Changed from apt-get to apt
        subprocess.run(["apt", "update", "-y"]) # Changed from apt-get to apt
        subprocess.run(["apt", "upgrade", "-y"]) # Changed from apt-get to apt
        subprocess.run(["apt", "install", "-y", "gawk", "curl"]) # Changed from apt-get to apt
    else:
        subprocess.run(["dnf", "update", "-y"]) # Changed from yum to dnf
        subprocess.run(["dnf", "upgrade", "-y"]) # Changed from yum to dnf
        subprocess.run(["dnf", "install", "-y", "epel-release", "gawk", "curl"]) # Changed from yum to dnf

def get_vless_tcp_port():
    return 25801 # Fixed port for vless-tcp-reality

def install_xray():
    subprocess.run(["curl", "-Lo", "install-release.sh", "https://github.com/XTLS/Xray-install/raw/main/install-release.sh"])
    subprocess.run(["bash", "install-release.sh"])

def generate_keys():
    x25519 = subprocess.check_output(["/usr/local/bin/xray", "x25519"]).decode().splitlines()
    private_key = x25519[0].split()[2]
    public_key = x25519[1].split()[2]
    return private_key, public_key

def get_host_ip():
    try:
        ip = requests.get("http://www.cloudflare.com/cdn-cgi/trace").text
        for line in ip.splitlines():
            if line.startswith("ip="):
                return line.split('=')[1]
    except:
        pass

    try:
        ip = requests.get("http://www.cloudflare.com/cdn-cgi/trace", timeout=5).text
        for line in ip.splitlines():
            if line.startswith("ip="):
                return line.split('=')[1]
    except:
        pass
    return ""

def get_country(ip):
    try:
        return requests.get(f"http://ipinfo.io/{ip}/country").text.strip()
    except:
        return ""

def write_config(port, uuid_str, private_key, public_key): # Modified to only take one port
    config = {
        "log": {"loglevel": "warning"},
        "inbounds": [
            {
                "port": port,
                "protocol": "vless",
                "settings": {
                    "clients": [{"id": uuid_str, "flow": "xtls-rprx-vision"}], # Only xtls-rprx-vision for vless-tcp-reality
                    "decryption": "none",
                    "fallbacks": []
                },
                "streamSettings": {
                    "network": "tcp", # Fixed to tcp
                    "security": "reality",
                    "realitySettings": {
                        "show": False,
                        "dest": "www.tesla.com:443", # Retained original dest for consistency
                        "xver": 0,
                        "serverNames": ["www.tesla.com"], # Retained original serverNames
                        "privateKey": private_key,
                        "shortIds": ["123abc"], # Retained original shortIds
                        "fingerprint": "chrome" # Retained original fingerprint
                    }
                },
                "sniffing": {
                    "enabled": True,
                    "destOverride": ["http", "tls", "quic"]
                }
            }
        ],
        "outbounds": [{"protocol": "freedom", "tag": "direct"}]
    }

    os.makedirs("/usr/local/etc/xray", exist_ok=True)
    with open("/usr/local/etc/xray/config.json", "w") as f:
        json.dump(config, f, indent=2)

def save_client_config(host_ip, port, uuid_str, public_key, country): # Modified to only take one port
    with open("/usr/local/etc/xray/config.txt", "w") as f:
        vless_tcp_reality = (
            f"vless-tcp-reality\n"
            f"vless://{uuid_str}@{host_ip}:{port}?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.tesla.com&" # Retained original dest and serverNames for consistency
            f"fp=chrome&pbk={public_key}&sid=123abc&type=tcp&headerType=none#{country}\n" # Retained original shortIds and fingerprint
        )
        f.write(vless_tcp_reality)

def cleanup():
    try:
        os.remove("install-release.sh")
    except FileNotFoundError:
        pass

    try:
        os.remove(os.path.abspath(__file__))
    except FileNotFoundError:
        pass

def main():
    check_root()
    update_system()

    port = get_vless_tcp_port() # Get the fixed port

    install_xray()

    uuid_str = str(uuid.uuid4())
    private_key, public_key = generate_keys()

    write_config(port, uuid_str, private_key, public_key) # Pass only one port

    subprocess.run(["systemctl", "enable", "xray"])
    subprocess.run(["systemctl", "restart", "xray"])

    host_ip = get_host_ip()
    country = get_country(host_ip)
    save_client_config(host_ip, port, uuid_str, public_key, country) # Pass only one port

    print("Xray 安装完成\n")
    with open("/usr/local/etc/xray/config.txt") as f:
        print(f.read())

    cleanup()

if __name__ == "__main__":
    main()
