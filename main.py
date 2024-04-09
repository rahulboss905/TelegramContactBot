import logging
import sys
import os
import threading
import re
import time

import telebot
from apscheduler.schedulers.background import BackgroundScheduler
from settings import BOT_TOKEN, GROUP_ID, MAX_FLOOD_ATTEMPTS, FLOOD_DETECTION_INTERVAL, BANNED_USER_DB, LOG_FILE_PATH, LOG_MAX_SIZE, HLP_MSG, RELOAD_TIME

# configure logging to display the timestamp, log level, message, and write in a file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),  # specify the filename
        logging.StreamHandler(sys.stdout)  # print logs to the console
    ]
)

# initialize bot
bot = telebot.TeleBot(BOT_TOKEN)
logging.info('Bot initialized.')

# initialize a dictionary to keep track of banned users and timestamps for flood detection
banned_users = {}
user_timestamps = {}
flood_attempts = {}


############ FUNCTIONS ############

# check if a user is banned
def is_user_banned(user_id):
    return str(user_id) in banned_users

# flood detection module
def flood_detection(user_id):
    current_time = time.time()
    # initialize user in flood_attempts if not present
    if user_id not in flood_attempts:
        flood_attempts[user_id] = 0

    # check if the user is within the flood detection interval
    if user_id in user_timestamps and current_time - user_timestamps[user_id] <= FLOOD_DETECTION_INTERVAL:
        # increment the flood attempts
        flood_attempts[user_id] += 1
        logging.info(f'User {user_id} triggered flood. try #{flood_attempts[user_id]}.')

        # check if the user has reached the flood attempt limit
        if flood_attempts[user_id] >= MAX_FLOOD_ATTEMPTS:
            ban_user(user_id)
            # reset the counter after banning
            flood_attempts[user_id] = 0
            user_timestamps[user_id] = current_time  # update the timestamp after banning
            logging.warning(f'User {user_id} has been banned for flooding.')
    else:
        # reset the flood attempts since interval has passed and update the timestamp
        flood_attempts[user_id] = 0
        user_timestamps[user_id] = current_time
        logging.info(f'Since user {user_id} behaved correctly, flood trigger counts got cleared.')

# function to send a message to the group
def send_to_group(message, user):
    first_name = user.first_name or ''
    last_name = user.last_name or ''
    user_id = user.id
    username = f'@{user.username}' if user.username else 'No username'
    text = f'From: {first_name} {last_name}\nID: {user_id}\nHandle: {username}\n\n{message.text}'
    bot.send_message(GROUP_ID, text)
    bot.reply_to(message, 'Message relayed successfully.')
    logging.info(f'Message sent to group from user {user_id}.')

# ban a user
def ban_user(user_id):
    with open(BANNED_USER_DB, 'a') as f:
        f.write(str(user_id) + '\n')
    banned_users[str(user_id)] = True
    logging.info(f'User {user_id} banned.')

# unban a user
def unban_user(user_id):
    # remove the user ID from the banned_users dictionary
    banned_users.pop(str(user_id), None)
    # rewrite the BANNED_USER_DB file (banned.txt) without the unbanned user ID
    with open(BANNED_USER_DB, 'w') as f:
        for uid in banned_users.keys():
            f.write(uid + '\n')
    logging.info(f'User {user_id} unbanned.')

# function to refresh the banned users list, probably not needed but it's good to be there xD
def banned_users_dictionary():
    while True:
        try:
            with open(BANNED_USER_DB, 'r') as f:
                global banned_users
                banned_users = {line.strip(): True for line in f}
            logging.info('Banned users list refreshed.')
        except FileNotFoundError:
            logging.error(f'{BANNED_USER_DB} file not found.')
        time.sleep(RELOAD_TIME)

# clear dictionaries to save memory in very long run
def clear_dict():
    flood_attempts.clear()
    user_timestamps.clear()
    logging.info('Bot dictionaries got cleared.')

# trim log file so it doesn't get so big
def trim_log_file():
    # get the current size of the log file
    file_size = os.path.getsize(LOG_FILE_PATH)
    if file_size > LOG_MAX_SIZE:
        # read the entire log file into memory
        with open(LOG_FILE_PATH, 'r') as f:
            lines = f.readlines()
        # remove lines from the beginning until the file size is within limits
        while file_size > LOG_MAX_SIZE and lines:
            line_to_remove = lines.pop(0)
            file_size -= len(line_to_remove.encode())  # account for UTF-8 encoding
        # write the trimmed content back to the log file
        with open(LOG_FILE_PATH, 'w') as f:
            f.writelines(lines)


############ BACKGROUND STUFF ############

# start background thread (load & refresh banned user dict)
refresh_banned_users_thread = threading.Thread(target=banned_users_dictionary)
refresh_banned_users_thread.start()
# start background schedule (clear flood dict)
clear_schedules = BackgroundScheduler()
clear_schedules.add_job(clear_dict, 'cron', day='1', hour='1', month='*') # clear 1st day of every month @ 1AM
clear_schedules.add_job(trim_log_file, 'cron', hour=4, minute=0) # trim everyday @ 4AM
clear_schedules.start()


############ MESSAGE HANDLING LOGICS ############

# handle '/start' command
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.reply_to(message, 'Sorry, you are banned from using this bot.')
        logging.warning(f'Banned user {user_id} attempted to start.')
        return
    
    flood_detection(user_id)

    if flood_attempts[user_id] > 0:
        bot.reply_to(message, 'Please wait some seconds before sending a new message.')
        return
    else:
        bot.reply_to(message, 'Hi. You can now send text messages to admin.')
        logging.info(f'User {user_id} started the bot.')

# handle '/help' command
@bot.message_handler(commands=['help'])
def handle_help(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.reply_to(message, 'Sorry, you are banned from using this bot.')
        logging.warning(f'Banned user {user_id} attempted to start.')
        return
    
    flood_detection(user_id)

    if flood_attempts[user_id] > 1:
        bot.reply_to(message, 'Please wait some seconds before sending a new message.')
        return
    else:
        bot.reply_to(message, HLP_MSG)
        logging.info(f'User {user_id} used help command.')

# ONLY relaying text messages
@bot.message_handler(content_types=['photo', 'document', 'audio', 'video', 'video_note', 'voice', 'sticker', 'location', 'venue', 'contact', 'animation', 'game', 'dice'])
def handle_non_text_messages(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.reply_to(message, 'Sorry, you are banned from using this bot.')
        logging.warning(f'Banned user {user_id} attempted to send a message.')
        return
    
    flood_detection(user_id)

    if flood_attempts[user_id] > 1:
        bot.reply_to(message, 'Please wait some seconds before sending a new message.')
        return
    else:
        bot.reply_to(message, "Sorry, this bot can only relay text messages. please stop sending non-text stuff.")
        logging.info(f"User {user_id} tried to send non-text message.")

# handle '/ban' command from group
@bot.message_handler(func=lambda message: message.chat.id == int(GROUP_ID) and message.reply_to_message and '/ban' in message.text)
def handle_group_ban_reply(message):
    if '/ban' in message.text:
        # extract user ID from the original message
        original_message = message.reply_to_message
        user_id_pattern = re.compile(r'ID: (\d+)')
        match = user_id_pattern.search(original_message.text)
        if match:
            user_id_to_ban = match.group(1)
            ban_user(user_id_to_ban)
            bot.reply_to(message, f'User {user_id_to_ban} has been banned.')
            logging.info(f'User {user_id_to_ban} banned via reply in group by {message.from_user.first_name}.')
        else:
            bot.reply_to(message, 'Could not find the user ID to ban.')
            logging.error('Failed to extract user ID for banning.')

# handle '/unban' command from group
@bot.message_handler(func=lambda message: message.chat.id == int(GROUP_ID) and message.text.startswith('/unban'), commands=['unban'])
def handle_unban(message):
    try:
        # extract the user ID to unban from the message text
        user_id_to_unban = re.search(r'/unban (\d+)', message.text).group(1)
        if user_id_to_unban:
            unban_user(user_id_to_unban)
            bot.reply_to(message, f'User {user_id_to_unban} has been unbanned.')
            logging.info(f'Admin ({message.from_user.first_name}) unbanned user {user_id_to_unban}.')
        else:
            bot.reply_to(message, 'Please specify a user ID to unban.')
            logging.warning('Unban command missing user ID.')
    except AttributeError:
        bot.reply_to(message, 'Invalid command format. Use /unban [user_id].')
        logging.error('Invalid unban command format.')

# Reply to user in bot
@bot.message_handler(func=lambda message: message.chat.id == int(GROUP_ID))
def group_commands(message):
    # check if the message is a reply to another message
    if message.reply_to_message:
        # use regular expression to extract the user ID from the message text
        user_id_match = re.search(r'ID: (\d+)', message.reply_to_message.text)
        if user_id_match:
            original_sender_id = user_id_match.group(1)
            # extract the reply text from the message
            reply_text = "Admin Response:\n\n" + message.text
            # send the reply to the original sender
            bot.send_message(original_sender_id, reply_text, protect_content=True)
            # you can remove ", protect_content=True" from above if you want them to be able to forward your responses
            bot.reply_to(message, "Message relayed successfully.")
            logging.info(f"Reply sent to user {original_sender_id}.")
        else:
            bot.reply_to(message, "Could not find the original sender's ID in the message.")
            logging.error(f"Failed to send reply to the original sender.")

# handle text messages
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_messages(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.reply_to(message, 'Sorry, you are banned from using this bot.')
        logging.warning(f'Banned user {user_id} attempted to send a message.')
        return
    
    flood_detection(user_id)
    # if a message is more than 4096, it's going to crash and you need to split which is a hassle so F it xD
    # so check if the message is too long and reject it
    if len(message.text) > 4000:
        bot.reply_to(message, 'This message is too long. please make it shorter')
        logging.info(f'Extremely long message got rejected from {user_id}.')
        return
    # check if no flood, then the bot relays the message
    if flood_attempts[user_id] > 1:
        bot.reply_to(message, 'Please wait some seconds before sending a new message.')
        return
    else:
        send_to_group(message, message.from_user)


############ BOT POLLING FOR MESSAGES ############
try:
    logging.info('Bot is starting to poll for messages...')
    bot.infinity_polling(skip_pending=True) # ignore pending messages when bot starts, you can remove "skip_pending=True"
except Exception as e:
    logging.error(f'Bot polling failed due to an exception: {e}')
    # implement any additional error handling or recovery logic here if you added something to bot, else it will work just fine
