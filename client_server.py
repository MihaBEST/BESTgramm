#!/usr/bin/env python3
import cgi
import DB as db
import BotManager as bot
import hashlib

def check_tag(text):
    if text.count("@") == 1 and text[0] == "@" and text.count(".")==0 and len(text)<21:
        return text
    return ''

def Hash(text):
    if len(text) < 8 or len(text) > 25:
        return ""
    salt = "saminadegniparol"
    return hashlib.pbkdf2_hmac('sha256', text.encode(), salt.encode(), 100000).hex()

def main():

    #=========================ПОЛУЧЕНИЕ ПАРАМЕТРОВ===================

    params = cgi.FieldStorage()
    #print('Content-type: text/html\n\n')

    request = str(params.getfirst('request',''))
    if request == '':
        print("incorrect request")

    #=========================ПРИНЯТИЕ===============================

    elif request=="reg":
        email = str(params.getfirst('email',''))
        psw = str(params.getfirst('psw',''))
        psw=Hash(psw)
        name = str(params.getfirst('name',''))
        tag  = str(params.getfirst('tag',''))
        tag = check_tag(tag)
        if not psw == "" and not tag == "":
            print(db.reg(email,psw,name,tag))
        if psw == "":
            print("incorrect password")
        if tag == "":
            print("incorrect tag")

    elif request == "change_name":
        tag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw', ''))
        psw = Hash(psw)
        newname = str(params.getfirst('newname',''))
        print(db.change_name(tag,psw,newname))

    elif request == "aprove_email":
        email = str(params.getfirst('email',''))
        psw = str(params.getfirst('psw',''))
        print(db.aprove_email(email,psw))

    elif request == "enter":
        email = str(params.getfirst('email',''))
        tag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        print(db.enter(email,tag,psw))

    elif request == "create_chat":
        tag1 = str(params.getfirst('tag1',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        tag2 = str(params.getfirst('tag2',''))
        print(db.create_chat(tag1, psw, tag2))

    elif request == "create_group":
        admintag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        chatname = str(params.getfirst('name',''))
        chattag = str(params.getfirst('chat_tag',''))
        see_other = str(params.getfirst('see_other','0'))=='1'
        needinvite = str(params.getfirst('need_invite','0'))=='1'
        is_public = str(params.getfirst('is_public','0'))=='1'
        if not chattag == "":
            print(db.create_group(admintag, psw, chatname, chattag, see_other, needinvite, is_public))
        if chattag == "":
            print("incorrect tag")

    elif request == "enter_public":
        usertag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        chattag = str(params.getfirst('chat_tag',''))
        print(db.enter_public(usertag, psw, chattag))

    elif request == "add_user":
        admintag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        chattag = str(params.getfirst('chat_tag',''))
        usertag = str(params.getfirst('user_tag',''))
        print(db.add_user(admintag, psw, chattag, usertag))

    elif request == "ask_meet":
        usertag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        chattag = str(params.getfirst('chat_tag',''))
        print(db.ask_meet(usertag, psw, chattag))

    elif request == "allow_meet":
        admintag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        usertag = str(params.getfirst('user_tag',''))
        chattag = str(params.getfirst('chat_tag',''))
        allow = str(params.getfirst('allow',''))
        print(db.allow_meet(admintag, psw, usertag, chattag, allow))

    elif request == "del_admin":
        usertag = str(params.getfirst('user_tag',''))
        admintag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        chattag = str(params.getfirst('chat_tag',''))
        print(db.del_admin(usertag, admintag, psw, chattag))

    elif request == "leav_chat":
        usertag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        chattag = str(params.getfirst('chat_tag',''))
        print(db.leav_chat(usertag, psw, chattag))

    elif request == "up_status":
        admintag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        chattag = str(params.getfirst('chat_tag',''))
        usertag = str(params.getfirst('user_tag',''))
        print(db.up_status(admintag, psw, chattag, usertag))

    elif request == "down_status":
        admintag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        chattag = str(params.getfirst('chat_tag',''))
        usertag = str(params.getfirst('user_tag',''))
        print(db.down_status(admintag, psw, chattag, usertag))

    elif request == "set_avatar":
        usertag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        fileid = str(params.getfirst('file_id',''))
        isgroup = str(params.getfirst('is_group','0'))=='1'
        chattag = str(params.getfirst('chat_tag',''))
        print(db.set_avatar(usertag, psw, fileid, isgroup, chattag))

    elif request == "send_file":
        name = str(params.getfirst('name',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        file_data = params.getfirst('file','')
        print(db.send_file(name, psw, file_data))

    elif request == "block_user":
        tag1 = str(params.getfirst('tag1',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        tag2 = str(params.getfirst('tag2',''))
        print(db.block_user(tag1, psw, tag2))

    elif request == "dell_message":
        usertag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        chattag = str(params.getfirst('chat_tag',''))
        messagenum = str(params.getfirst('message_id',''))
        print(db.dell_message(usertag, psw, chattag, messagenum))

    elif request == "change_message":
        usertag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        chattag = str(params.getfirst('chat_tag',''))
        messagenum = str(params.getfirst('message_id',''))
        newmessage = str(params.getfirst('message_new',''))
        print(db.change_message(usertag, psw, chattag, messagenum, newmessage))

    elif request=="change_psw":
        tag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw', ''))
        psw = Hash(psw)
        newpsw = str(params.getfirst('newpsw',''))
        newpsw = Hash(newpsw)
        if not newpsw == "":
            print(db.change_psw(tag,psw,newpsw))
        else:
            print("incorrect psw")

    elif request=="get_news":
        tag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        print(db.get_news(tag,psw))

    elif request=="send_message":
        tag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        chattag = str(params.getfirst('chat_tag', ''))
        message =  str(params.getfirst('message', ''))
        fileid = str(params.getfirst('fileid', None))
        print(db.send_message(tag,psw,chattag,message,fileid))

    #=========================ОТДАЧА=================================

    elif request == "get_avatar":
        tag = str(params.getfirst('tag',''))
        is_group = str(params.getfirst('is_group',''))
        print(db.get_avatar(tag, is_group))

    elif request == "get_file":
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        file_id = str(params.getfirst('file_id',''))
        print(db.get_file(psw, file_id))

    elif request == "get_chat":
        usertag = str(params.getfirst('tag',''))
        psw = str(params.getfirst('psw',''))
        psw = Hash(psw)
        chattag = str(params.getfirst('chat_tag',''))
        count = str(params.getfirst('count',''))
        print(db.get_chat(usertag, psw, chattag, count))

    elif request == "get_chat_info":
        chattag = str(params.getfirst('chat_tag',''))
        print(db.get_chat_info(chattag))

    elif request == "getin_chat_info":
        tag = str(params.getfirst('tag', ''))
        psw = str(params.getfirst('psw', ''))
        psw = Hash(psw)
        chattag = str(params.getfirst('chat_tag', ''))
        print(db.getin_chat_info(tag,psw,chattag))

    elif request == "get_user":
        tag = str(params.getfirst('tag', ''))
        print(db.get_user(tag))

    elif request == "find":
        text = str(params.getfirst('text', ''))
        print(db.find(text))

    #=========================БОТЫ===================================

    elif request == "create_bot":
        usertag = str(params.getfirst('user_tag',''))
        userpsw = str(params.getfirst('user_psw',''))
        userpsw = Hash(userpsw)
        email = str(params.getfirst('email',''))
        bottag = str(params.getfirst('bot_tag',''))
        bottag = check_tag(bottag)
        botpsw = str(params.getfirst('bot_psw',''))
        botpsw = Hash(botpsw)
        botname = str(params.getfirst('bot_name',''))
        if not botpsw == "" and not bottag == "":
            print(bot.create_bot(usertag,userpsw,email,bottag,botpsw,botname))
        if botpsw == "":
            print("incorrect password")
        if bottag == "":
            print("incorrect tag")

    elif request == "get_chat_bot":
        botkey = str(params.getfirst('key',''))
        bottag = str(params.getfirst('bot_tag',''))
        botpsw = str(params.getfirst('bot_psw',''))
        botpsw = Hash(botpsw)
        print(bot.get_chat(botkey,bottag,botpsw))

    elif request == "send_message_bot":
        botkey = str(params.getfirst('bot_key',''))
        bottag = str(params.getfirst('bot_tag',''))
        botpsw = str(params.getfirst('bot_psw',''))
        botpsw = Hash(botpsw)
        chattag = str(params.getfirst('chat_tag',''))
        message = str(params.getfirst('message',''))
        print(bot.send_message(botkey,bottag,botpsw,chattag,message))

    elif request=="send_file_bot":
        botkey = str(params.getfirst('bot_key',''))
        bottag = str(params.getfirst('bot_tag',''))
        botpsw = str(params.getfirst('bot_psw',''))
        botpsw = Hash(botpsw)
        chattag = str(params.getfirst('chat_tag',''))
        file_psw = str(params.getfirst('file_psw',''))
        file_psw = Hash(file_psw)
        file_data = str(params.getfirst('file_data',''))
        filename = str(params.getfirst('file_name',''))
        print(bot.send_file(botkey, bottag, botpsw, chattag,file_psw, file_data, filename))

    else:
        print("request error")

#=========================ЗАПУСК КАК CGI==========================

if __name__ == '__main__':
    main()