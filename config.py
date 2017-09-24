import os

token = os.environ['TELEGRAM_TOKEN']
channelid = os.environ['CHANNEL_ID']
admin_chatid = os.environ['ADMIN_CHAT_ID']
'''
TOKEN = config.token
PORT = int(os.environ.get('PORT', '5000'))
updater.start_webhook(listen="0.0.0.0",
                      port=PORT,
                      url_path=TOKEN)
updater.bot.set_webhook("https://mrzgbottest.herokuapp.com/" + TOKEN)
'''
