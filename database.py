import sqlite3
import logging


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARNING)
logger = logging.getLogger(__name__)

conn = sqlite3.connect("twiiterdb.sqlite", check_same_thread=False)
cursor = conn.cursor()


def setup():  # start database
        stmt1 = "CREATE TABLE IF NOT EXISTS tusername (CHAT_ID text NOT NULL,username text NOT NULL ," \
                "PRIMARY key (CHAT_ID))"
        stmt2 = "CREATE TABLE IF NOT EXISTS blockedchat (blocked_id text NOT NULL,PRIMARY key (blocked_id))"
        stmt3 = "CREATE TABLE IF NOT EXISTS trending(hashtags text NOT NULL,trendnum INTEGER NOT NULL)"
        stmt4 = "CREATE TABLE IF NOT EXISTS blockedwords(words text NOT NULL)"
        stmt5 = "CREATE TABLE IF NOT EXISTS messegs(chat_id INTEGER NOT NULL , message_id INTEGER NOT NULL)"
        stmt6 = "CREATE TABLE IF NOT EXISTS like_messegs(chat_id INTEGER, message_id INTEGER NOT NULL," \
                "likes INTEGER NOT NULL , dislikes INTEGER NOT NULL)"
        stmt7 = "CREATE TABLE IF NOT EXISTS who_liked(chatid INTEGER, message_id INTEGER NOT NULL)"
        cursor.execute(stmt1)
        cursor.execute(stmt2)
        cursor.execute(stmt3)
        cursor.execute(stmt4)
        cursor.execute(stmt5)
        cursor.execute(stmt6)
        cursor.execute(stmt7)
        conn.commit()
        logger.info("Database is UP and RUNNING")
        print("Database is UP and RUNNING")

#region username and chat id
def add_shit(chatid, username):
    stmt = "INSERT INTO tusername (CHAT_ID, username) VALUES (?,?)"
    args = (chatid, username)
    cursor.execute(stmt, args)
    conn.commit()


def delete_shit(username):
    stmt = "DELETE FROM tusername WHERE username = (?)"
    args = (username,)
    cursor.execute(stmt, args)
    conn.commit()


def get_username(chatid):
    stmt = "SELECT username FROM tusername WHERE CHAT_ID=?"
    args = (chatid,)
    cursor.execute(stmt, args)
    exist = cursor.fetchone()
    if exist is None:
        return None
    else:
        return exist[0]


def get_chatid(username):
    stmt = "SELECT CHAT_ID FROM tusername WHERE username = ?"
    args = (username,)
    cursor.execute(stmt, args)
    exist = cursor.fetchone()
    if exist is None:
        return None
    else:
        return exist[0]
# endregion


# region messages and message ids likes and dislikes
def add_message_id(chat_id, msgid):
    stmt = "SELECT message_id FROM messegs WHERE chat_id=?"
    args = (chat_id,)
    cursor.execute(stmt, args)
    exist = cursor.fetchone()
    if exist is None:
        stmt = "INSERT INTO messegs (chat_id,message_id) VALUES (?,?)"
        args = (chat_id, msgid.message_id,)
        cursor.execute(stmt, args)
        conn.commit()
    else:
        stmt = "UPDATE messegs SET message_id=? WHERE chat_id=?"
        args = (msgid.message_id, chat_id,)
        cursor.execute(stmt, args)
        conn.commit()


def get_message_id(chatid):
    stmt = "SELECT message_id FROM messegs WHERE chat_id=?"
    args = (chatid,)
    cursor.execute(stmt, args)
    exist = cursor.fetchone()
    if exist is None:
        return None
    else:
        return exist[0]


def add_like_msgid(chatid, msgid):
    stmt = "INSERT INTO like_messegs(chat_id, message_id, likes, dislikes) VALUES (?,?,?,?)"
    args = (chatid, msgid, 0, 0,)
    cursor.execute(stmt, args)
    conn.commit()


def add_likes(msgid):
    stmt = "SELECT likes FROM like_messegs WHERE message_id=?"
    args = (msgid,)
    cursor.execute(stmt, args)
    exist = cursor.fetchone()
    stmt = "SELECT dislikes FROM like_messegs WHERE message_id=?"
    args = (msgid,)
    cursor.execute(stmt, args)
    exist2 = cursor.fetchone()
    if exist is None:
        return [0,0]
    else:
        stmt = "UPDATE like_messegs SET likes=? WHERE message_id=?"
        args = (exist[0]+1, msgid,)
        cursor.execute(stmt, args)
        conn.commit()
        return exist[0]+1, exist2[0]


def add_dislikes(msgid):
    stmt = "SELECT dislikes FROM like_messegs WHERE message_id=?"
    args = (msgid,)
    cursor.execute(stmt, args)
    exist = cursor.fetchone()
    stmt = "SELECT likes FROM like_messegs WHERE message_id=?"
    args = (msgid,)
    cursor.execute(stmt, args)
    exist2 = cursor.fetchone()
    if exist[0] is None:
        return 0
    else:
        stmt = "UPDATE like_messegs SET dislikes=? WHERE message_id=?"
        args = (exist[0]+1, msgid,)
        cursor.execute(stmt, args)
        conn.commit()
        return exist[0]+1, exist2[0]


def liked(chatid, msgid):
    stmt = "SELECT chatid FROM who_liked WHERE message_id=?"
    args = (msgid,)
    cursor.execute(stmt, args)
    exist = cursor.fetchall()
    if exist is None:
        stmt = "INSERT INTO who_liked (chatid, message_id) VALUES (?,?)"
        args = (chatid, msgid,)
        cursor.execute(stmt, args)
        conn.commit()
        return None

    else:
        for x in range(0, len(exist)):
            if chatid == exist[x][0]:
                return True
        stmt = "INSERT INTO who_liked (chatid, message_id) VALUES (?,?)"
        args = (chatid, msgid,)
        cursor.execute(stmt, args)
        conn.commit()
        return None


def get_like_dislike(msgid):
    stmt = "SELECT likes FROM like_messegs WHERE message_id=?"
    args = (msgid,)
    cursor.execute(stmt, args)
    exist = cursor.fetchone()
    stmt = "SELECT dislikes FROM like_messegs WHERE message_id=?"
    args = (msgid,)
    cursor.execute(stmt, args)
    exist2 = cursor.fetchone()
    return exist[0], exist2[0]


def get_most_liked():
    stmt = "SELECT * FROM like_messegs ORDER BY likes DESC"
    cursor.execute(stmt)
    exist = cursor.fetchmany(5)
    if exist is None:
        return None
    else:
        return exist


def delete_liked_message(messageid):
    stmt = "DELETE FROM like_messegs WHERE message_id = (?)"
    args = (messageid,)
    cursor.execute(stmt, args)
    conn.commit()
# endregion



# region block username
def add_blocked_id(chatid):
    stmt = "INSERT INTO blockedchat (blocked_id) VALUES (?)"
    args = (chatid, )
    cursor.execute(stmt, args)
    conn.commit()


def get_blocked_id(chatid):
    stmt = "SELECT blocked_id FROM blockedchat WHERE blocked_id=?"
    args = (chatid,)
    cursor.execute(stmt, args)
    exist = cursor.fetchone()
    if exist is None:
        return None
    else:
        return exist[0]


def unblock(chatid):
    stmt = "DELETE FROM blockedchat WHERE blocked_id = (?)"
    args = (chatid,)
    cursor.execute(stmt, args)
    conn.commit()
# endregion


# region hashtag trending
def add_hashtag(hashtag):
        stmt = "SELECT hashtags FROM trending WHERE hashtags=?"
        args = (hashtag,)
        cursor.execute(stmt, args)
        exist = cursor.fetchone()
        if exist is None:
            stmt = "INSERT INTO trending (hashtags,trendnum) VALUES (?,?)"
            args = (hashtag, 1,)
            cursor.execute(stmt, args)
            conn.commit()
        else:
            stmt = "SELECT trendnum FROM trending WHERE hashtags=?"
            args = (hashtag,)
            cursor.execute(stmt, args)
            trendnum = cursor.fetchone()
            trendnum = trendnum[0] + 1
            stmt = "UPDATE trending SET trendnum=? WHERE hashtags=?"
            args = (trendnum, hashtag,)
            cursor.execute(stmt, args)
            conn.commit()


def get_trending():
    stmt = "SELECT * FROM trending ORDER BY trendnum DESC"
    cursor.execute(stmt)
    exist = cursor.fetchall()
    if exist is None:
        return None
    else:
        return exist

# endregion


# region blocked words
def add_blocked_word(blocked_word):
    stmt = "INSERT INTO blockedwords (words) VALUES (?)"
    args = (blocked_word, )
    cursor.execute(stmt, args)
    conn.commit()


def get_all_blocked_words():
    stmt = "SELECT words FROM blockedwords"
    cursor.execute(stmt)
    conn.row_factory = lambda cursor, row: row[0]
    words = cursor.execute(stmt).fetchall()
    COLUMN = 0
    column = [elt[COLUMN] for elt in words]
    if column is None:
        return None
    else:
        return column


def get_blocked_word(word):
    stmt = "SELECT words FROM blockedwords WHERE words = ?"
    args = (word, )
    cursor.execute(stmt, args)
    exist = cursor.fetchone()
    if exist is None:
        return None
    else:
        return exist[0]


def delete_blocked_word(word):
    stmt = "DELETE FROM blockedwords WHERE words = (?)"
    args = (word,)
    cursor.execute(stmt, args)
    conn.commit()
# endregion


# dropping tables

def DROPTABLEusername():
    stmt = "DROP TABLE tusername"
    cursor.execute(stmt)
    logger.info("tusername table dropped")
    print("tusername table dropped")


def DROPTABLEtrend():
    stmt = "DROP TABLE trending"
    cursor.execute(stmt)
    logger.info("trending table dropped")
    print("trending table dropped")


def DROPTABLEblockedwords():
    stmt = "DROP TABLE blockedwords"
    cursor.execute(stmt)
    logger.info("bloskedwords table dropped")
    print("bloskedwords table dropped")


def DROPTABLElike_messages():
    stmt = "DROP TABLE who_liked"
    cursor.execute(stmt)
    logger.info("messages table dropped")
    print("messages table dropped")