# telegram__bot_to_monitor_linux_system
This repository helps you configure a simple monitoring Python script that sends notifications and manages Linux system services through a Telegram bot

**Configuratiion - Linux**
**Install python and pip**
#yum install python3 python3-pip -y

**Install python-telegram-bot using pip**
#pip install python-telegram-bot

**Add a user with limited privilages to manage the defind service in the script**
#adduser ansible

**Provide privilages under sudoers**
#/etc/sudoers.d/ansible

ansible ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx, /usr/bin/systemctl restart docker

**Run the python script**
#python3 telegram_system_monitor_bot.py

**Configuration - Telegram**

create Telegarm bot using botfather
Add the required Telegram details in the script. After starting the script, you can use the commands below to manage the services. We will also receive Telegram alert notifications when the system temperature/Memory reaches 80% or 85%.

    "uptime": "uptime",
    "disk": "df -h",
    "memory": "free -h",
    "cpu": "top -bn1 | head -10",
    "services": "systemctl list-units --type=service --state=running | head -20",
    "restart_nginx": "sudo systemctl restart nginx",
    "restart_docker": "sudo systemctl restart docker",
