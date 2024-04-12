# Simple Telegram Contact Us Bot
**A very simple Python Telegram bot written with [pyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI/) acting as a contact us solution to centralize messages from your subscribers**

## What does this bot do?
This bot will redirect all **text** messages to a private group. Group members (admin(s) of a channel for example) can answer the users by replying to the message and the bot will relay the message without revealing the identity of the group admin(s). It helps a lot in making your inbox clean.

### Other Features:
- Message flood protection - Users are permitted to send only 2 messages within a short timeframe. Attempts at spamming result in a ban after a specified duration. You can 
- Ability to ban/unban people from using the bot - You have the option to ban specific users (e.g., those who are disruptive) from sending messages. Should you wish to unban a user manually, this is also possible.
- Redirects only text messages for ease of use and security
- Writes all logs to a file

## How to run this bot
### Telegram side:
1. Create your bot and get the token from [BotFather](https://t.me/BotFather).
2. _Optional_: Customize your bot settings (eg. Name, Avatar, Commands, etc.).
3. Get your Private Group ID (it starts with "-", don't forget to use it) with the help of [Rose](https://t.me/MissRose_bot) "/id" command after adding it to your group (remove it after).
4. Add your contact bot to the private group of your choosing.
5. _Optional_: From Bot settings in BotFather, turn off the "Allow Group?" settings so no one else can add your bot to their group. you don't need to do it though, bot is going to be useless in their group anyway but I feel more safe this way.

### Code side:
1. Add the bot API token and your group ID to your .env file like this (if u using something else then do that for loading these values safely):
```
TELEGRAM_BOT_TOKEN="XXXXXXXXXX"
TELEGRAM_GROUP_ID="YYYYYYYYYYY"
```
2. Change values of the "settings.py" file as needed for help message text, flood protection values, log file location, etc.

### Server side:
- install requirements and run the script:
```
pip install -r requirements.txt
python3 main.py
```
## How to use the bot
- Answer the message: Reply to the message redirected to the group, it will be sent to that user via the bot.
- Ban a user: To ban a user, reply to their message and type "/ban" (excluding the double quotation marks), then send the message. The bot will confirm the action. The banned user will not be notified until they attempt to send a new message.
- Unban a user: DO NOT REPLY to the message. Instead, copy the User ID (the integer displayed in the message they send) and type the following: "/unban 111111111" (ignore "" and replace 11111111 with the appropriate User ID), then send the message. The bot will confirm if the action is successful.


You are done, enjoy 😊
