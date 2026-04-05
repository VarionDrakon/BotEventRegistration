<div align="center">

<img src="res/logo.svg" alt="res/logo.svg" width="300" height="300">

# Event Registration Bot

</div>

A bot for registration and event management in Telegram.


### Just information about project in badges:

[![APACHE2][APACHE2-badge]][APACHE2-url]
[![PYTHON][PYTHON-badge]][PYTHON-url]
[![TELEGRAM][TELEGRAM-badge]][TELEGRAM-url]
[![DEBIAN][DEBIAN-badge]][DEBIAN-url]

[comment]: <> (Links block:)

[APACHE2-badge]: https://img.shields.io/badge/Apache-D22128?logo=apache&logoColor=fff&style=for-the-badge
[APACHE2-url]: https://www.apache.org/licenses/LICENSE-2.0

[PYTHON-badge]: https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff&style=for-the-badge
[PYTHON-url]: https://www.python.org/downloads/release/python-3130/

[TELEGRAM-badge]: https://img.shields.io/badge/Telegram-26A5E4?logo=telegram&logoColor=fff&style=for-the-badge
[TELEGRAM-url]: https://core.telegram.org/bots/api

[DEBIAN-badge]: https://img.shields.io/badge/Debian-A81D33?logo=debian&logoColor=fff&style=for-the-badge
[DEBIAN-url]: https://www.debian.org/releases/trixie/

## Run Locally

Starting to the bot (Python 3.13):

Install necessary packages:

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-venv
```
Go to the future working directory where the bot will work:
```bash
python3.13 -m venv venv
```
And enter to the console for installing dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

Before running the bot, copy .env.example file to the .env file in root directory bots, then edit this variables:

* TOKEN - Telegram API token for bot.
* ADMINS - List of administrator (ID tg users).
* DB_LINK - Location where the database file will be placed (Example - database.db).
* BOT_NAME - Name bot, this is NOT name from Telegram.
* FEEDBACK_CHAT_ID - ID of the telegram channel where the bot will send messages.
* VERSION - system variables from developer. Not change, please. This string is temporary...

After preparing the files bots, create a service file:
Example:
```bash
nano /etc/systemd/system/telegram-bot-registration.service
```
And paste this content:
```bash
[Unit]
Description=Telegram Bot for registration.
After=network.target

[Service]
Type=simple
User=(Example - root)
WorkingDirectory=(Example - /root/telegram/bot/Registration/bot)
ExecStart=(Example - /root/telegram/bot/Registration/venv/bin/python3.13 /root/telegram/bot/Registration/bot/main.py)
Restart=always
RestartSec=10s 
StandardOutput=append:(Example - /var/log/telegram-bot-registration.log)
StandardError=append:(Example - /var/log/telegram-bot-registration.log)

[Install]
WantedBy=multi-user.target
```
Then start services:

```bash
sudo systemctl daemon-reload
sudo systemctl restart telegram-bot-registration
sudo systemctl status telegram-bot-registration

sudo systemctl enable telegram-bot-registration
sudo systemctl start telegram-bot-registration
sudo systemctl stop telegram-bot-registration
```
And this starting the server.


## License

[Apache License 2.0](LICENSE)

