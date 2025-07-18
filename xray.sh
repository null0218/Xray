#!/bin/bash


# 检查root权限并更新系统
root() {
    # 检查root权限
    if [[ ${EUID} -ne 0 ]]; then
        echo "Error: This script must be run as root!" 1>&2
        exit 1
    fi
    
    # 更新系统和安装基础依赖
    echo "正在更新系统和安装依赖"
    if [ -f "/usr/bin/apt" ]; then # Changed from apt-get to apt
        apt update -y && apt upgrade -y # Changed from apt-get to apt
        apt install -y gawk curl # Changed from apt-get to apt
    else
        dnf update -y && dnf upgrade -y # Changed from yum to dnf
        dnf install -y epel-release gawk curl # Changed from yum to dnf
    fi
}

# 获取随机端口
port() {    
    PORT1=25801 # Fixed port for vless-tcp-reality
}

# 配置和启动Xray
xray() {
    # 安装Xray内核
    bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
    # 生成所需参数
    shid=$(openssl rand -hex 8) # path is not needed for tcp-reality, but keep shid for reality settings
    uuid=$(/usr/local/bin/xray uuid)
    X25519Key=$(/usr/local/bin/xray x25519)
    PrivateKey=$(echo "${X25519Key}" | head -1 | awk '{print $3}')
    PublicKey=$(echo "${X25519Key}" | tail -n 1 | awk '{print $3}')

    # 配置config.json
    cat >/usr/local/etc/xray/config.json <<EOF
{
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "port": "${PORT1}",
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "${uuid}",
            "flow": "xtls-rprx-vision"
          }
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "dest": "updates.cdn-apple.com:443",
          "serverNames": [
            "updates.cdn-apple.com"
          ],
          "privateKey": "${PrivateKey}",
          "shortIds": [
            "${shid}"
          ]
        }
      },
      "sniffing": {
        "enabled": true,
        "destOverride": [
          "http",
          "tls",
          "quic"
        ]
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom",
      "tag": "direct"
    }
  ]
}
EOF

    # 启动Xray服务
    systemctl enable xray.service && systemctl restart xray.service
    if ! systemctl is-active --quiet xray.service; then
      echo "Xray 启动失败"
      exit 1
    fi
    
    # 获取IP并生成客户端配置
    HOST_IP=$(curl -s -4 http://www.cloudflare.com/cdn-cgi/trace | grep "ip" | awk -F "[=]" '{print $2}')
    if [[ -z "${HOST_IP}" ]]; then
        HOST_IP=$(curl -s -6 http://www.cloudflare.com/cdn-cgi/trace | grep "ip" | awk -F "[=]" '{print $2}')
    fi
    
    # 获取IP所在国家
    IP_COUNTRY=$(curl -s http://ipinfo.io/${HOST_IP}/country)
    
    # 生成并保存客户端配置
    cat << EOF > /usr/local/etc/xray/config.txt

vless-tcp-reality
vless://${uuid}@${HOST_IP}:${PORT1}?encryption=none&flow=xtls-rprx-vision&security=reality&sni=updates.cdn-apple.com&fp=chrome&pbk=${PublicKey}&sid=${shid}&type=tcp&headerType=none#${IP_COUNTRY}
EOF

    echo "Xray 安装完成"
    cat /usr/local/etc/xray/config.txt
}

# 主函数
main() {
    root
    port
    xray
}

# 执行脚本
main
