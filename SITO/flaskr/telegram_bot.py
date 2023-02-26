# -*- coding: utf-8 -*-
"""
This Example will show you how to use register_next_step handler.
"""
import hashlib

import requests

import telebot
from telebot import types

bot = telebot.TeleBot("2108740213:AAEEwQSPHs6zDsVq1-EAtWt-ZQeRnc4CWIo")
# server_ip = "172.20.10.11:5000"
server_ip = "127.0.0.1:5000"
# response = {}

# Handle '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    msg = bot.reply_to(message, """\
Salve, sono il bot Findog.
Qual è la tua mail d'accesso ?
""")
    bot.register_next_step_handler(msg, greetings_email)


def greetings_email(message):
    email = message.text
    global global_message
    global_message = message
    msg = bot.reply_to(message, """\
    Inserisci la tua password 
    """)
    bot.register_next_step_handler(msg, greetings_password, email)

    '''response = requests.get(f'http://{server_ip}/get_user', params={'uuid': uuid, 'chat_id': chat_id})
    if response.text != "Nessun Risultato":
        
    else:
        bot.reply_to(message, f'Mi dispiace, non esiste nessun cane con questo uuid')
'''


def greetings_password(message, email):
    password = message.text
    chat_id = message.chat.id
    bot.delete_message(message.chat.id, message.id)
    password = hashlib.sha256(password.encode()).hexdigest()
    user = requests.post(f'http://{server_ip}/telegram_login',
                         data={'email': email, 'password': password, 'chat_id': chat_id})

    if user.text == 'auth_error':
        bot.send_message(chat_id, "Email o password errati")
    else:
        bot.send_message(chat_id, f'Ciao {user.text}!')


def dog_found(address, telegram_chat_id):
    bot.send_message(telegram_chat_id,
                     f"Il tuo cane è stato trovato nei pressi della casa dell'utente con indirizzo {address}")


def walk_keyboard():
    return types.InlineKeyboardMarkup(
        keyboard=[
            [
                types.InlineKeyboardButton(
                    text="SI",
                    callback_data="SI"
                )
                ,

                types.InlineKeyboardButton(
                    text="NO",
                    callback_data="NO"
                )
            ]
        ]

    )


def walk_handler_v3(chat_id, uuid):
    requests.post(f'http://{server_ip}/set_dog', data={'uuid': uuid, 'attribute': 'state', 'val': 'W'})
    bot.send_message(chat_id, 'Sei a fare una passeggiata con il tuo cane ?', reply_markup=walk_keyboard())


@bot.callback_query_handler(func=lambda c: c.data == 'SI')
def si_callback(call: types.CallbackQuery):
    dog_uuid = (requests.get('http://127.0.0.1:5000/get_dog_uuid', params={'chat_id': call.message.chat.id})).text
    requests.post(f'http://{server_ip}/set_dog', data={'uuid': dog_uuid, 'attribute': 'state', 'val': 'P'})
    requests.post(f'http://{server_ip}/new_walk', data={'uuid': dog_uuid})
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text='Buona passeggiata!')


@bot.callback_query_handler(func=lambda c: c.data == 'NO')
def no_callback(call: types.CallbackQuery):
    dog_uuid = (requests.get('http://127.0.0.1:5000/get_dog_uuid', params={'chat_id': call.message.chat.id})).text
    name = (
        requests.get(f'http://{server_ip}/get_dog', params={'uuid': dog_uuid, 'attribute': 'name'})).text.capitalize()
    requests.post(f'http://{server_ip}/set_dog', data={'uuid': dog_uuid, 'attribute': 'state', 'val': 'S'})
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f'Il tuo cane {name} è scappato!')


if __name__ == "__main__":
    # Enable saving next step handlers to file "./.handlers-saves/step.save".
    # Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
    # saving will hapen after delay 2 seconds.
    print("Bot online")
    bot.enable_save_next_step_handlers(delay=2)

    # Load next_step_handlers from save file (default "./.handlers-saves/step.save")
    # WARNING It will work only if enable_save_next_step_handlers was called!
    bot.load_next_step_handlers()

    bot.infinity_polling()
