Service file:

/etc/systemd/system/telegram-bot-redcursive-registration.service
----------------------------------------------------------------
[Unit]
Description=Telegram Bot for RedCursive - Registration.
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/telegram/bot/RedCursive/Registration/bot
ExecStart=/root/telegram/bot/RedCursive/Registration/venv/bin/python3.13 /root/telegram/bot/RedCursive/Registration/bot/main.py
Restart=always
RestartSec=10s 
StandardOutput=append:/var/log/telegram-bot-redcursive-registration.log
StandardError=append:/var/log/telegram-bot-redcursive-registration.log

[Install]
WantedBy=multi-user.target
----------------------------------------------------------------

sudo systemctl daemon-reload
sudo systemctl restart telegram-bot-redcursive-registration
sudo systemctl status telegram-bot-redcursive-registration

sudo systemctl enable telegram-bot-redcursive-registration
sudo systemctl start telegram-bot-redcursive-registration
sudo systemctl stop telegram-bot-redcursive-registration


Starting to the bot (Python 3.13+ if Debian):
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-venv

python3.13 -m venv venv

Enter to the console:

source venv/bin/activate

pip install -r requirements.txt

Needs to be finished:
Set timezones on Moscow.

Before running the bot, edit the .env file

TOKEN - Telegram API token for bot.
ADMINS - List of administrator.
DB_LINK - Location where the database file will be placed.
BOT_NAME - Name bot, this is NOT name from Telegram.
FEEDBACK_CHAT_ID - ID of the telegram channel where the bot will send messages.
VERSION - system variables from developer. Not change, please.


## License

[Apache License 2.0](LICENSE)