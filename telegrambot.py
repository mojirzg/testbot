#!/usr/bin/env python
# -*- coding: utf-8 -*-
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from io import BytesIO
from PIL import Image
import database
import telegram
import logging
import config
import time
import sys
import os


# region logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARNING,)
logger = logging.getLogger(__name__)
# endregion


def start(bot, update):
    chatid = str(update.message.chat_id)
    if database.get_username(chatid) is None:
        update.message.reply_text("""برای شما یوزرنیم ثبت نشده
لطفا با ارسال /username برای خود یکی بسازید""")
        return
    username = database.get_username(chatid)
    bot.send_message(chat_id=update.message.chat_id, text="یوزرنیم شما:" + username + "\nمیتوانید توییت خود را بفرستید...")


# region username functions
def make_username(bot, update):
    chatid=update.message.chat_id
    if database.get_username(chatid) is None:
        update.message.reply_text("""لطفا یک یوزرنیم انتخاب کنید
این یوزرنیم زیر پست هاتون نوشته میشه
حتما # بذارین اولش
برای ارسال یوزرنیم از دستور /set استفاده کنید
برای پاک کردن یوزرنیم از /del استفاده کنید
""")
        update.message.reply_text("""مثال:
/set #رضا_خوشحال
/del #رضا_ناراحت""")
    else:
        username = database.get_username(chatid)
        bot.send_message(chat_id=update.message.chat_id,
                         text="یوزرنیم شما:" + username + "\nمیتوانید توییت خود را بفرستید")
        update.message.reply_text("""برای پاک کردن یوزرنیم از /del استفاده کنید""")
        update.message.reply_text("""مثال:
        /del #رضا_ناراحت""")

def set(bot, update, args, chat_data):
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        given_username = str(args[0])
        if database.get_username(given_username) == given_username:
                update.message.reply_text("این یوزرنیم قبلا استفاده شده")
        elif given_username.startswith("#"):
                if database.get_username(chat_id) is None:
                    database.add_shit(chat_id, given_username)
                    update.message.reply_text("یوزرنیم شما ذخیره شد، میتوانید توییت بفرستید")
                    telusername = update.message.from_user.username
                    logger.info("telusername = " + str(telusername) + "---chatid =" +
                         str(chat_id) + " and username = " + str(given_username) + " added to database")
                    print("telusername = " + str(telusername) + "---chatid =" +
                         str(chat_id) + " and username = " + str(given_username) + " added to database")
                    return
        else:
            update.message.reply_text('حتما باید با # شروع شه')
            return

    except (IndexError, ValueError):
        update.message.reply_text("""مثال:
        /set #حمید_رضایی""")


def delete(bot, update, args, chat_data):
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        given_username = str(args[0])
        username = database.get_username(chat_id)
        if username == given_username:
            database.delete_shit(given_username)
            update.message.reply_text("یوزرنیم شما پاک شد، برای فرستادن توییت با ارسال /username برای خود یوزرنیم بسازید ")
            telusername = update.message.from_user.username
            logger.info("telusername = " + telusername + "---chatid =" + str(chat_id) + " and username = " + given_username +
                  " deleted from database")
            return

        else:
                update.message.reply_text("""برای شما یوزرنیم ثبت نشده
                لطفا با ارسال /username برای خود یکی بسازید""")
                return

    except (IndexError, ValueError):
        update.message.reply_text("""مثال:
        /del #حمید_رضایی""")

# endregion


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
        menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
        if header_buttons:
            menu.insert(0, header_buttons)
        if footer_buttons:
            menu.append(footer_buttons)
        return menu


def callback_likes(bot, update):
    chatid = int(update.callback_query.from_user.id)
    msgid = int(update.callback_query.message.message_id)
    if database.liked(chatid, msgid) is None:
        if update.callback_query.data == "like":
            likes = database.add_likes(update.callback_query.message.message_id)
            button_list = [
                InlineKeyboardButton("👎🏻   " + str(likes[1]), callback_data="dislike"),
                InlineKeyboardButton("👍🏻   " + str(likes[0]), callback_data="like"),
            ]
            reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
            bot.edit_message_reply_markup(chat_id=config.channelid, message_id=update.callback_query.message.message_id,
                                          reply_markup=reply_markup)
        elif update.callback_query.data == "dislike":
            likes = database.add_dislikes(update.callback_query.message.message_id)
            button_list = [
                InlineKeyboardButton("👎🏻   " + str(likes[0]), callback_data="dislike"),
                InlineKeyboardButton("👍🏻   " + str(likes[1]), callback_data="like"),
            ]
            reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
            bot.edit_message_reply_markup(chat_id=config.channelid, message_id=update.callback_query.message.message_id,
                                          reply_markup=reply_markup)
    else:
        bot.answer_callback_query(update.callback_query.id, text="یه بار میشه لایک یا دیسلایک کرد", show_alert=True)


def twiiter(bot, update):
    #region likes and dislikes
    dislikes = 0
    likes = 0

    button_list = [
        InlineKeyboardButton("👎🏻   " + str(dislikes), callback_data="dislike"),
        InlineKeyboardButton("👍🏻   " + str(likes), callback_data="like"),
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))

    #endregion
    chatid = update.message.chat_id
    blocked = database.get_blocked_id(chatid)
    username = database.get_username(chatid)
    telusername = update.message.from_user.username
    if blocked is None:
        if database.get_username(chatid) is None:
            update.message.reply_text('اول برای خود با ارسال /username یوزرنیم بسازید')
        elif update.message.photo:
            caption = update.message.caption +"\n\n" + username + "\n@twitter66bot"
            msgid = bot.send_photo(chat_id=config.channelid, photo=update.message.photo[-1].file_id,
                                   caption=caption, reply_markup=reply_markup)
            bot.send_message(chat_id=update.message.chat_id, text="توییت در کانال قرار گرفت",
                             reply_markup=telegram.ReplyKeyboardMarkup([['/edit_caption'], ['/delete']],
                                                                resize_keyboard=True))
            logger.info(username + " Sendphoto: --caption " + update.message.caption + " -- chatid = " +
                        str(chatid) + " -- TelUsername: " + telusername)
            print(username + " Sendphoto: --caption " + update.message.caption + " -- chatid = " +
                  str(chatid) + " -- TelUsername: " + telusername)
            database.add_message_id(chatid, msgid)
            database.add_like_msgid(update.message.chat_id, msgid.message_id)
            get_hashtags(update.message.caption)
            database.add_message_id(chatid, msgid)
        elif update.message.document:
            caption = str(update.message.caption) + "\n\n" + username + "\n@twitter66bot"
            msgid = bot.send_document(chat_id=config.channelid, document=update.message.document.file_id,
                                      caption=caption, reply_markup=reply_markup)
            bot.send_message(chat_id=update.message.chat_id, text="توییت در کانال قرار گرفت",
                              reply_markup=telegram.ReplyKeyboardMarkup([['/edit_caption'], ['/delete']],
                                                                 resize_keyboard=True))
            logger.info(username + " SendGIF: --caption " + update.message.caption + " -- chatid = " +
                       str(chatid) + " -- TelUsername: " + telusername)
            print(username + " SendGif: --caption " + update.message.caption + " -- chatid = " +
                  str(chatid) + " -- TelUsername: " + telusername)
            database.add_message_id(chatid, msgid)
            database.add_like_msgid(update.message.chat_id, msgid.message_id)
            get_hashtags(update.message.caption)
            database.add_message_id(chatid, msgid)
        else:
            msgtext = update.message.text
            if len(msgtext) > 300:
                update.message.reply_text('توییت شما طولانی تر از حد مجاز 300 کاراکتر است')
            else:
                words = database.get_all_blocked_words()
                if any(word in msgtext for word in words):
                    update.message.reply_text('توییت شما حاوی کلمات غیرمجاز است')
                else:
                    telusername = update.message.from_user.username

                    bot.send_message(chat_id=update.message.chat_id, text="توییت در کانال قرار گرفت",
                                     reply_markup=telegram.ReplyKeyboardMarkup([['/edit'], ['/delete']],
                                                                               resize_keyboard=True))
                    msgid = bot.send_message(chat_id=config.channelid, text=msgtext +
                                     "\n\n" + username + "\n@twitter66bot", reply_markup=reply_markup)
                    database.add_like_msgid(update.message.chat_id, msgid.message_id)
                    get_hashtags(msgtext)
                    logger.info(username + " twited: " + msgtext + " -- chatid = " + str(chatid) + " -- TelUsername: " + telusername)
                    print(username + " twited: " + msgtext + " -- chatid = " + str(chatid) + " -- TelUsername: " + telusername)
                    database.add_message_id(chatid, msgid)
    else:
        update.message.reply_text("شما از طرف ادمین بلاک شدید")


def twitt_photo(bot, update):
    pass


def trend(bot, update):
    msg = database.get_trending()
    if msg is None:
        update.message.reply_text("هشتگ موجود نمیباشد")
    else:
        bot.send_message(chat_id=update.message.chat_id, text="هشتگ هایی ک بیشترین استفاده رو داشتن:" + "\nهشتگ: --" +
                                                           " تعداد: " + "\n" + msg[0][0] + " -- " + str(msg[0][1]) +
                                                           "\n" + msg[1][0] + " -- " + str(msg[1][1]) +
                                                           "\n" + msg[2][0] + " -- " + str(msg[2][1]) +
                                                           "\n" + msg[3][0] + " -- " + str(msg[3][1]) +
                                                           "\n" + msg[4][0] + " -- " + str(msg[4][1]))


def get_hashtags(message):
    if '#' in message:
        x = message.index('#')
        if ' ' in message[x:]:
            y = message[x:].index(' ')
            y = y + x
            if not message[x:y] == '#':
                hashtag = message[x:y]
                database.add_hashtag(hashtag)

        else:
            hashtag = message[x:]
            database.add_hashtag(hashtag)

        get_hashtags(message[x+1:])


def see_blocked_words(bot, update):
    words = str(database.get_all_blocked_words())
    if words is None:
        update.message.reply_text("هنوز کلمه ای اضافه نشده")
    else:
        update.message.reply_text(words)


def help_msg(bot, update):
    update.message.reply_text("""دستورات موجود در بات و توضیحات آنان
    /start :
    شروع ربات
    /username :
    برای اظافه کردن یا پاک کردن یوزرنیم 
    /trend :
    برای دیدن پنج هشتگی که بیشترین استفاده را داشتند
    /blockwords :
    برای دیدن کلمات غیرمجاز
    /help :
    توضیحات دستورات
    /adminhelp :
    برای دیدن توضیحات دستورات مربوط به ادمین"""
                              )


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def test(bot, update):
    print(update)


# region Editing an deleting messages

def edit_last_post(bot, update):
    update.message.reply_text("""متن ادیت شده پیامتان را بفرستید
    برای انصراف /cancel را ارسال کنید
    توجه داشته باشید ک فقط ادیت اخرین پیام شما تا 48 ساعت ممکن است """)
    return editmsg


def editmsg(bot, update):
    chatid = update.message.chat_id
    text = update.message.text
    username = database.get_username(update.message.chat_id)
    message_id = database.get_message_id(update.message.chat_id)
    if message_id is None:
        update.message.reply_text("پیام شما قابل ادیت شدن نمی باشد")
    else:
        likes = database.get_like_dislike(message_id)
        button_list = [
            InlineKeyboardButton("👎🏻   " + str(likes[1]), callback_data="dislike"),
            InlineKeyboardButton("👍🏻   " + str(likes[0]), callback_data="like"),
        ]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
        bot.edit_message_text(chat_id=config.channelid, message_id=message_id, text=text +
                              "\n\n" + username + "\n@twitter66bot", reply_markup=reply_markup)
        update.message.reply_text("پیام شما با موفقیت ادیت شد")
        logger.info(str(database.get_username(chatid)) + " Edited his/hers message -- " + " new text is : " + text +
                    " -- chatid = " + str(chatid) + " -- TelUsername: " + str(update.message.from_user.username))
        print(str(database.get_username(chatid)) + " Edited his/hers message -- " + " new text is : " + text +
                    " -- chatid = " + str(chatid) + " -- TelUsername: " + str(update.message.from_user.username))
    return ConversationHandler.END


def cancel(bot, update):
    update.message.reply_text('ادیت پیام متوقف شد، میتوانید توییت خود را ارسال کنید')
    return ConversationHandler.END


def delete_last_post(bot, update):
    chatid = update.message.chat_id
    messageid = database.get_message_id(chatid)
    if messageid is None:
        update.message.reply_text("پیام شما یافت نشد")
    else:
        bot.delete_message(chat_id=config.channelid, message_id=messageid)
        bot.send_message(chat_id=chatid, text="پیام شما با موفقیت پاک شد", reply_markup=telegram.ReplyKeyboardRemove())
        logger.info(str(database.get_username(chatid)) + " deletet his/hers message: " +
                    " -- chatid = " + str(chatid) + " -- TelUsername: " + str(update.message.from_user.username))
        print(str(database.get_username(chatid)) + " deletet his/hers message: " +
                    " -- chatid = " + str(chatid) + " -- TelUsername: " + str(update.message.from_user.username))
        database.delete_liked_message(messageid)


def edit_caption(bot, update):
    update.message.reply_text("""متن ادیت شده کپشن را بفرستید
    برای انصراف /cancel را ارسال کنید
    توجه داشته باشید ک فقط ادیت اخرین پیام شما تا 48 ساعت ممکن است """)
    return editmsg_captopn


def editmsg_captopn(bot, update):
    chatid = update.message.chat_id
    text = update.message.text
    username = database.get_username(update.message.chat_id)
    message_id = database.get_message_id(update.message.chat_id)
    if message_id is None:
        update.message.reply_text("پیام شما قابل ادیت شدن نمی باشد")
    else:
        likes = database.get_like_dislike(message_id)
        button_list = [
            InlineKeyboardButton("👎🏻   " + str(likes[1]), callback_data="dislike"),
            InlineKeyboardButton("👍🏻   " + str(likes[0]), callback_data="like"),
        ]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
        bot.edit_message_caption(chat_id=config.channelid, message_id=message_id, caption=text +
                                                                                    "\n\n" + username + "\n@twitter66bot",
                              reply_markup=reply_markup)
        update.message.reply_text("پیام شما با موفقیت ادیت شد")
        logger.info(str(database.get_username(chatid)) + " Edited his/hers message caption -- " + " new text is : " + text +
                    " -- chatid = " + str(chatid) + " -- TelUsername: " + str(update.message.from_user.username))
        print(str(database.get_username(chatid)) + " Edited his/hers message Caption -- " + " new text is : " + text +
              " -- chatid = " + str(chatid) + " -- TelUsername: " + str(update.message.from_user.username))
    return ConversationHandler.END

# endregion


#region admin functions

def blacklist(bot, update, args, chat_data):
    chatid = str(update.message.chat_id)
    if chatid != config.admin_chatid:
        update.message.reply_text('برای انجام این عمل باید ادمین باشید')
        return
    else:
        try:
            # args[0] should contain the time for the timer in seconds
            given_username = str(args[0])
            bchatid = database.get_chatid(given_username)
            username = str(database.get_username(bchatid))
            if username == given_username:
                id_to_block = database.get_chatid(username)
                database.add_blocked_id(id_to_block)
                bot.send_message(chat_id=update.message.chat_id, text=username + "  ADDED to blackllist")
                logger.info(username + " with the chat_id of: " + id_to_block + " ADDED to blacklist")
                print(username + " with the chat_id of: " + id_to_block + " ADDED to blacklist")
                return

            else:
                update.message.reply_text('این یوزرنیم در سرور موجود نیست')
                return

        except (IndexError, ValueError):
            update.message.reply_text("یچیو اشتباه نوشتی")


def unblacklist(bot, update, args, chat_data):
    chatid = str(update.message.chat_id)
    if chatid != config.admin_chatid:
        update.message.reply_text('برای انجام این عمل باید ادمین باشید')
        return
    else:
        try:
            # args[0] should contain the time for the timer in seconds
            given_username = str(args[0])
            bchatid = database.get_chatid(given_username)
            username = database.get_username(bchatid)
            if username == given_username:
                id_to_unblock = database.get_chatid(username)
                database.unblock(id_to_unblock)
                bot.send_message(chat_id=update.message.chat_id, text=username + "  REMOVED from blackllist")
                logger.info(username + " with the chat_id of: " + id_to_unblock + " REMOVED from"
                                                                            " blacklist")
                print(str(username) + " with the chat_id of: " + str(id_to_unblock) + " REMOVED from"
                                                                            " blacklist")
                return

            else:
                update.message.reply_text('این یوزرنیم در سرور موجود نیست')
                return

        except (IndexError, ValueError):
            update.message.reply_text("یچیو اشتباه نوشتی")


def add_blocked_word(bot, update, args, chat_data):
    chatid = str(update.message.chat_id)
    if chatid != config.admin_chatid:
        update.message.reply_text('برای انجام این عمل باید ادمین باشید')
        return
    else:
        try:
            # args[0] should contain the time for the timer in seconds
            word = str(args[0])
            if word == database.get_blocked_word(word):
                update.message.reply_text('این کلمه در دیتابیس موجود است')
                return

            else:
                database.add_blocked_word(word)
                update.message.reply_text('کلمه با موفقیت به لیست سیاه اضافه شد')

        except (IndexError, ValueError):
            update.message.reply_text("یچیو اشتباه نوشتی")


def delete_blocked_word(bot, update, args, chat_data):
    chatid = str(update.message.chat_id)
    if chatid != config.admin_chatid:
        update.message.reply_text('برای انجام این عمل باید ادمین باشید')
        return
    else:
        try:
            # args[0] should contain the time for the timer in seconds
            word = str(args[0])
            words = database.get_all_blocked_words()
            if word in words:
                database.delete_blocked_word(word)
                update.message.reply_text('کلمه با موفقیت از لیست سیاه حذف شد')
                return
            else:
                update.message.reply_text('این کلمه در دیتابیس موجود نیست')
                return

        except (IndexError, ValueError):
            update.message.reply_text("یچیو اشتباه نوشتی")


def sendtrend(bot, update):
    chatid = str(update.message.chat_id)
    if chatid != config.admin_chatid:
        update.message.reply_text('برای انجام این عمل باید ادمین باشید')
        return
    else:
        msg = database.get_trending()
        if msg is None:
            update.message.reply_text("هشتگ موجود نمیباشد")
        else:
            msg = database.get_trending()
            bot.send_message(chat_id=config.channelid, text="هشتگ هایی ک بیشترین استفاده رو داشتن:" + "\nهشتگ: --" +
                                                              " تعداد: " + "\n" + msg[0][0] + " -- " + str(msg[0][1]) +
                                                              "\n" + msg[1][0] + " -- " + str(msg[1][1]) +
                                                              "\n" + msg[2][0] + " -- " + str(msg[2][1]) +
                                                              "\n" + msg[3][0] + " -- " + str(msg[3][1]) +
                                                              "\n" + msg[4][0] + " -- " + str(msg[4][1]))


def droptrend (bot, update):
    chatid = str(update.message.chat_id)
    if chatid != config.admin_chatid:
        update.message.reply_text('برای انجام این عمل باید ادمین باشید')
        return
    else:
        update.message.reply_text('دیتابیس با موفقیت دراپ شد')
        database.DROPTABLEtrend()
        database.setup()


def dropblockedword(bot, update):
    chatid = str(update.message.chat_id)
    if chatid != config.admin_chatid:
        update.message.reply_text('برای انجام این عمل باید ادمین باشید')
        return
    else:
        update.message.reply_text('دیتابیس با موفقیت دراپ شد')
        database.DROPTABLEblockedwords()
        database.setup()


def restart(bot, update):#todo reset bot
    bot.send_message(update.message.chat_id, "Bot is restarting...")
    time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)


def most_liked(bot, update):
    chatid = str(update.message.chat_id)
    if chatid != config.admin_chatid:
        update.message.reply_text('برای انجام این عمل باید ادمین باشید')
        return
    else:
        data = database.get_most_liked()
        class topmsg:
            def __init__(self, chatid, msgid, likes, dislikes):
                self.chatid = chatid
                self.msgid = msgid
                self.likes = likes
                self.dislikes = dislikes

            def __repr__(self):
                return repr((self.chatid, self.msgid, self.likes, self.dislikes))

        def getkey(topmsg):
            return topmsg.likes

        list = [
            topmsg(data[0][0], data[0][1], data[0][2], data[0][3]),
            topmsg(data[1][0], data[1][1], data[1][2], data[1][3]),
            topmsg(data[2][0], data[2][1], data[2][2], data[2][3]),
            topmsg(data[3][0], data[3][1], data[3][2], data[3][3]),
            topmsg(data[4][0], data[4][1], data[4][2], data[4][3])]
        list.sort(key=getkey)
        bot.send_message(chat_id=config.channelid, text=" کسانی که بیشترین تعداد لایک را در یک پیام داشتند:")
        for x in range(4, -1, -1):
            msgtext = "\nUsername: " + database.get_username(list[x].chatid) + \
                      "\nLikes: " + str(list[x].likes) + "\nDislikes: " + str(list[x].dislikes)
            bot.send_message(chat_id=config.channelid, reply_to_message_id=list[x].msgid, text=msgtext)


def admin_help(bot, update):
    chatid = str(update.message.chat_id)
    if chatid != config.admin_chatid:
        update.message.reply_text('برای انجام این عمل باید ادمین باشید')
        return
    else:
        update.message.reply_text("""/blacklist <username> :
برای بلاک کردن شخص از ارسال پیام به کانال(ارسال به لیست سیاه)
/unblacklist <username> :
برای آنبلاک کردن شخص(بیرون آوردن از لیست سیاه)
/blockword <word> :
اضافه کردن کلمه ی غیر مجاز که هر متن حاوی آن کلمه ارسال نخواهد شد
/unblockword <word> :
پاک کردن کلمه ی غیر مجاز
/sendtrend :
ارسال پیام حاوی پنج هشتگی که بیشترین استفاده را داشته اند به کانال
/mostliked:
 پنج پیامی که بیشترین تعداد لایک را داشتند در کانال تعیین میشوند
/reset :
ریستارت کردن بات
/DroptrenD :
برای پاک کردن لیست هشتگ های پرمصرف
/DropblockedworD :
پاک کردن لیست کلمات غیرمجاز""")
#endregion


def main():
    database.setup()

    # Create the EventHandler and pass it your bot's token.
    updater = Updater(config.token)
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # region Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("username", make_username))
    dp.add_handler(CommandHandler("set", set, pass_args=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("del", delete, pass_args=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("trend", trend))
    dp.add_handler(CommandHandler("blockwords", see_blocked_words))
    dp.add_handler(CommandHandler("delete", delete_last_post))
    dp.add_handler(CommandHandler("help", help_msg))
    dp.add_handler(CommandHandler("test" ,test))
    dp.add_handler(telegram.ext.CallbackQueryHandler(callback=callback_likes))
    # region admin's handlers
    dp.add_handler(CommandHandler("blacklist", blacklist, pass_args=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("unblacklist", unblacklist, pass_args=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("blockword", add_blocked_word, pass_args=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("unblockword", delete_blocked_word, pass_args=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("sendtrend", sendtrend))
    dp.add_handler(CommandHandler("DroptrenD", droptrend))
    dp.add_handler(CommandHandler("DropblockedworD", dropblockedword))
    dp.add_handler(CommandHandler("reset", restart))
    dp.add_handler(CommandHandler("mostliked", most_liked))
    dp.add_handler(CommandHandler("adminhelp", admin_help))
    # endregion

    # region edit message conversation handler

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('edit', edit_last_post)],

        states={
            editmsg: [MessageHandler(Filters.text, editmsg)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
    conv_handler2 = ConversationHandler(
        entry_points=[CommandHandler('edit_caption', edit_caption)],

        states={
            editmsg_captopn: [MessageHandler(Filters.text, editmsg_captopn)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(conv_handler2)
    dp.add_handler(MessageHandler(Filters.all, twiiter))  # twits the text given to the channel
    # endregion
    # endregion handlers
    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
