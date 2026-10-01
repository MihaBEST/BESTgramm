import DB as db
import sqlite3
import time
import random

def Set(text):
    connection = sqlite3.connect('bots.db')
    cursor = connection.cursor()
    cursor.execute(text)
    connection.commit()
    connection.close()

def Get(text):
    connection = sqlite3.connect('bots.db')
    cursor = connection.cursor()
    cursor.execute(text)
    connection.close()
    return cursor.fetchall()

#=============================БАЗА ДАННЫХ================================

Set('''create table if not exists bots (
id integer primary key autoincrement,
owner_tag,
bot_tag text,
name text,
psw text,
bot_key text,
chats text)
''')

#=============================ПРОВЕРКИ===================================

def DoError(text):
    with open("errors.txt","r") as fin:
        with open("errors.txt","w") as fout:
            fout.write(str(fin.read())+"\n"+text)

def count_bots(usertag):
    try:
        return Get(f'select count(*) from bots where owner_tag="{usertag}"')[0][0]
    except Exception as e:
        DoError(f"Error in bot count_bots: {e}")
        return "10"

def bot_exists(tag="",key="",psw=""):
    try:
        if tag == "":
            return int(Get(f'select count(*) from bots where bot_key="{key}" and psw = "{psw}"')[0][0])==1

        return int(Get(f'select count(*) from bots where bot_tag="{tag}" and psw = "{psw}"')[0][0]) == 1
    except Exception as e:
        DoError(f"Error in bot bot_exists: {e}")
        return "error"

def create_key():
    key = ""
    for i in range(20):
        if random.randint(0,3)==0:
            key += str(random.randint(0,10))
        elif random.randint(0,2)==0:
            key += chr(random.randint(ord('a'), ord('z')))
        else:
            key+=chr(random.randint(ord('A'),ord('Z')))
    if int(Get(f'select count(*) from bots where bot_key="{key}"')[0][0]) != 0:
        key = create_key()
    return key

#=============================СОЗДАНИЕ БОТА==============================

def create_bot(usertag,userpsw,email,bottag,botpsw,botname):
    try:
        if db.is_user(tag=usertag,psw=userpsw):
            if int(count_bots(usertag)[0][0])!=10:
                if not db.tag_exist(bottag) and bottag[:4]=="@bot":
                    db.Set(f'insert into user (email, psw, name, tag, time_reg) values ("{email}","{botpsw}","{botname}","{bottag}","{time.time()}")')
                    key = create_key()
                    Set(f'insert into bots (owner_tag, bot_tag,name,psw,bot_key,chats) values ("{usertag}","{bottag}","{botname}","{botpsw}","{key}","")')
                    return "success, your key is: "+key
                return "tag exists or incorrect tag"
            return "you have 10 bots"
        return "incorrect user"
    except Exception as e:
        DoError(f"Error in bot create_bot: {e}")
        return "error"

#============================ПОЛУЧЕНИЕ СООБЩЕНИЙ=========================

def get_chat(botkey,bottag,botpsw):
    try:
        if bot_exists(key=botkey,psw=botpsw):
            result = []
            updusers = ""
            for i in Get(f'select users from bots where bot_key="{botkey}"')[0][0].split(";"):
                i=i.split(":")
                get = db.get_chat(bottag,botpsw,i[0],i[1])
                if get[0][0]==0:
                    updusers += f'{i[0]}:{i[1]};'
                    continue
                updusers += f'{i[0]}:{int(i[1]) + int(get[0][0])};'
                result.append(get[1])
            Set(f'update bots set users="{updusers}" where bot_tag="{bottag}"')
            return result[:len(result)-2]
        return ["incorrect bot"]
    except Exception as e:
        DoError(f"Error in bot get_chat: {e}")
        return ["error"]

#============================ОТПРАВКА СООБЩЕНИЙ=========================

def send_message(botkey,bottag,botpsw,chattag,message):
    try:
        if bot_exists(key=botkey, psw=botpsw):
            return db.send_message(bottag,botpsw,chattag,message)
        return "incorrect bot"
    except Exception as e:
        DoError(f"Error in bot send_message: {e}")
        return "error"

def send_file(botkey, bottag, botpsw, chattag,file_psw, file_data, filename):
    try:
        if bot_exists(key=botkey, psw=botpsw):
            chat_users = Get(f'select users_tag from chats where chat_tag="{chattag}"')[0][0]
            if f"{bottag}:" not in chat_users:
                return "bot not in chat"

            file_id = db.send_file(filename, file_psw, file_data)
            if file_id == "-1":
                return "file upload error"

            result = db.send_message(bottag, botpsw, chattag, f"file:{filename}", file_id)
            return result
        return "incorrect bot"
    except Exception as e:
        DoError(f"Error in bot send_file: {e}")
        return "error"
