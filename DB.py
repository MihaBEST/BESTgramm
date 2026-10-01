import random
import sqlite3
import time
import GmailSender as gmail
import zlib
from contextlib import contextmanager


# ======================== DATABASE HELPERS ========================

@contextmanager
def get_db_connection(db_name):
    """Контекстный менеджер для работы с базой данных"""
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def execute_db(db_name, query, params=None, fetch=False, commit=False, many=False):
    """Универсальная функция для выполнения запросов"""
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()
        try:
            if many and isinstance(params, list):
                cursor.executemany(query, params)
            elif params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if commit:
                conn.commit()

            if fetch:
                result = cursor.fetchall()
                return [dict(row) for row in result] if result else []
            return cursor
        except Exception as e:
            conn.rollback()
            log_error(f"Database error: {e}\nQuery: {query}\nParams: {params}")
            raise


# ======================== ERROR HANDLING ========================

def log_error(text):
    """Логирование ошибок"""
    try:
        with open("errors.txt", "a", encoding='utf-8') as f:
            f.write(f"{time.ctime()}: {text}\n")
    except Exception as e:
        print(f"Failed to log error: {e}")


# ======================== INITIALIZATION ========================

def initialize_databases():
    """Инициализация таблиц в базах данных"""
    try:
        # Main database (sait.db)
        execute_db('sait.db', '''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                psw TEXT,
                name TEXT,
                tag TEXT UNIQUE,
                blocked_tags TEXT,
                reg_psw TEXT,
                time_reg TEXT,
                avatar_name INTEGER,
                news TEXT
            )
        ''', commit=True)

        execute_db('sait.db', '''
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dialog BOOLEAN,
                see_other BOOLEAN,
                is_close BOOLEAN,
                is_public BOOLEAN,
                chat_tag TEXT UNIQUE,
                chat_name TEXT,
                users_tag TEXT,
                count_message INTEGER,
                avatar_name INTEGER
            )
        ''', commit=True)

        # Messages database (messages.db)
        execute_db('messages.db', '''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                psw TEXT,
                file BLOB
            )
        ''', commit=True)

    except Exception as e:
        log_error(f"Initialize databases error: {e}")
        raise


# ======================== USER AUTHENTICATION ========================

def is_user(tag=None, email=None, psw=None):
    """Проверка существования пользователя"""
    try:
        if tag and tag.startswith("@bot"):
            return False

        query = ""
        params = ()

        if tag:
            query = "SELECT COUNT(*) as count FROM user WHERE tag=? AND psw=? AND reg_psw='GET'"
            params = (tag, psw)
        elif email:
            query = "SELECT COUNT(*) as count FROM user WHERE email=? AND psw=? AND reg_psw='GET'"
            params = (email, psw)
        else:
            return False

        result = execute_db('sait.db', query, params, fetch=True)
        return result[0]['count'] > 0 if result else False
    except Exception as e:
        log_error(f"is_user error: {e}")
        return False


def blocked_tags(taguser):
    """Получение списка заблокированных тегов"""
    try:
        result = execute_db('sait.db',
                            "SELECT blocked_tags FROM user WHERE tag=?",
                            (taguser,), fetch=True)

        if result and result[0]['blocked_tags']:
            return result[0]['blocked_tags'].split(";")
        return []
    except Exception as e:
        log_error(f"blocked_tags error: {e}")
        return []


def tag_exist(tag):
    """Проверка существования тега"""
    try:
        # Check in chats
        chat_result = execute_db('sait.db',
                                 "SELECT COUNT(*) as count FROM chats WHERE chat_tag=?",
                                 (tag,), fetch=True)
        if chat_result and chat_result[0]['count'] > 0:
            return True

        # Check in users
        user_result = execute_db('sait.db',
                                 "SELECT COUNT(*) as count FROM user WHERE tag=?",
                                 (tag,), fetch=True)
        return user_result[0]['count'] > 0 if user_result else False
    except Exception as e:
        log_error(f"tag_exist error: {e}")
        return False


def fast_psw():
    """Генерация временного пароля"""
    return ''.join(str(random.randint(0, 9)) for _ in range(5))


def get_status(usertag, chattag):
    """Получение статуса пользователя в чате"""
    try:
        result = execute_db('sait.db',
                            "SELECT users_tag FROM chats WHERE chat_tag=?",
                            (chattag,), fetch=True)

        if not result:
            return None

        chat_tags = result[0]['users_tag'].split(";")
        for item in chat_tags:
            parts = item.split(":")
            if parts[0] == usertag:
                return parts[1]
        return None
    except Exception as e:
        log_error(f"get_status error: {e}")
        return None


def set_news(tag, text):
    """Добавление новостей для пользователя"""
    try:
        # Получаем текущие новости
        result = execute_db('sait.db',
                            "SELECT news FROM user WHERE tag=?",
                            (tag,), fetch=True)

        if not result:
            return False

        current_news = result[0]['news'] or ""
        new_news = f"{current_news}{text}"

        execute_db('sait.db',
                   "UPDATE user SET news=? WHERE tag=?",
                   (new_news, tag), commit=True)
        return True
    except Exception as e:
        log_error(f"set_news error: {e}")
        return False


# ======================== REGISTRATION & AUTH ========================

def reg(email, psw, name, tag):
    """Регистрация нового пользователя"""
    try:
        if tag.startswith("@bot"):
            return "user tag can't start with @bot"
        if "@gmail." not in email:
            return "incorrect email"
        if tag_exist(tag):
            return "this tag exists"

        # Check if email exists
        result = execute_db('sait.db',
                            "SELECT COUNT(*) as count FROM user WHERE email=?",
                            (email,), fetch=True)
        if result and result[0]['count'] > 0:
            return "this email is registered"

        if tag.count("@") != 1:
            return "incorrect format"

        checkpsw = fast_psw()
        execute_db('sait.db', '''
            INSERT INTO user 
            (email, psw, name, tag, blocked_tags, reg_psw, time_reg, avatar_name, news) 
            VALUES (?, ?, ?, ?, '', ?, ?, NULL, '')
        ''', (email, psw, name, tag, checkpsw, str(time.time())), commit=True)

        # Send confirmation email
        email_result = gmail.send_gmail(email, checkpsw)
        if email_result != "success":
            # Rollback registration if email failed
            execute_db('sait.db', "DELETE FROM user WHERE email=?", (email,), commit=True)
            return email_result

        return "success"
    except sqlite3.IntegrityError as e:
        log_error(f"reg integrity error: {e}")
        return "tag or email already exists"
    except Exception as e:
        log_error(f"reg error: {e}")
        return "error"


def aprove_email(email, psw):
    """Подтверждение email"""
    try:
        if not psw.isdigit():
            return "incorrect password"

        # Check if user exists with this email and temp password
        result = execute_db('sait.db',
                            "SELECT COUNT(*) as count FROM user WHERE email=? AND reg_psw=?",
                            (email, psw), fetch=True)

        if result and result[0]['count'] == 1:
            # Approve email
            execute_db('sait.db',
                       "UPDATE user SET reg_psw='GET' WHERE email=? AND reg_psw=?",
                       (email, psw), commit=True)
            return "success"
        else:
            # Remove unapproved user
            execute_db('sait.db',
                       "UPDATE user SET reg_psw='NotGet' WHERE email=?",
                       (email,), commit=True)
            execute_db('sait.db',
                       "DELETE FROM user WHERE email=?",
                       (email,), commit=True)
            return "incorrect password"
    except Exception as e:
        log_error(f"aprove_email error: {e}")
        return "error"


def enter(email=None, tag=None, psw=None):
    """Авторизация пользователя"""
    try:
        if not email and not tag:
            return "incorrect data"

        query = """
            SELECT COUNT(*) as count FROM user 
            WHERE (email=? OR tag=?) AND psw=? AND reg_psw='GET'
        """
        result = execute_db('sait.db', query, (email or "", tag or "", psw), fetch=True)

        return "success" if result and result[0]['count'] == 1 else "incorrect data"
    except Exception as e:
        log_error(f"enter error: {e}")
        return "error"


# ======================== CHAT MANAGEMENT ========================

def create_chat_table(chattag):
    """Создание таблицы для чата"""
    try:
        execute_db('messages.db', f'''
            CREATE TABLE IF NOT EXISTS "{chattag}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag TEXT,
                text TEXT,
                fileurl TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''', commit=True)
        return True
    except Exception as e:
        log_error(f"create_chat_table error: {e}")
        return False


def create_chat(tag1, psw, tag2):
    """Создание диалога между двумя пользователями"""
    try:
        if not is_user(tag=tag1, psw=psw):
            return "incorrect user"
        if tag1 in blocked_tags(tag2):
            return "user blocked you"

        # Get current news for both users
        user1_news = execute_db('sait.db',
                                "SELECT news FROM user WHERE tag=?",
                                (tag1,), fetch=True)[0]['news'] or ""
        user2_news = execute_db('sait.db',
                                "SELECT news FROM user WHERE tag=?",
                                (tag2,), fetch=True)[0]['news'] or ""

        chattag = tag1 + tag2

        # Create chat record
        execute_db('sait.db', '''
            INSERT INTO chats 
            (dialog, see_other, is_close, is_public, chat_tag, chat_name, users_tag, count_message, avatar_name) 
            VALUES (TRUE, FALSE, FALSE, FALSE, ?, NULL, ?, 1, NULL)
        ''', (chattag, f"{tag1}:user;{tag2}:user"), commit=True)

        # Update user news
        execute_db('sait.db',
                   "UPDATE user SET news=? WHERE tag=?",
                   (f"{user1_news};n{chattag}:user", tag1), commit=True)
        execute_db('sait.db',
                   "UPDATE user SET news=? WHERE tag=?",
                   (f"{user2_news};n{chattag}:user", tag2), commit=True)

        # Create chat table
        if not create_chat_table(chattag):
            return "error creating chat table"

        # Add system message
        execute_db('messages.db',
                   f'INSERT INTO "{chattag}" (tag, text, fileurl) VALUES ("system", "user {tag1} wrote user {tag2}", NULL)',
                   commit=True)

        return "success"
    except Exception as e:
        log_error(f"create_chat error: {e}")
        return "error"


def create_group(admintag, adminpsw, chatname, chattag, see_other, needinvite, is_public):
    """Создание группы"""
    try:
        if chattag.startswith("@bot"):
            return "chat tag can't start with @bot"
        if not is_user(tag=admintag, psw=adminpsw):
            return "incorrect user"
        if tag_exist(chattag):
            return "that tag exists"

        if not set_news(admintag, f';n{chattag}:creater'):
            return "error setting news"

        execute_db('sait.db', '''
            INSERT INTO chats 
            (dialog, see_other, is_close, is_public, chat_tag, chat_name, users_tag, count_message, avatar_name) 
            VALUES (FALSE, ?, ?, ?, ?, ?, ?, 1, NULL)
        ''', (see_other, needinvite, is_public, chattag, chatname, f"{admintag}:creater"), commit=True)

        if not create_chat_table(chattag):
            return "error creating chat table"

        return "success"
    except Exception as e:
        log_error(f"create_group error: {e}")
        return "error"


# ======================== CHAT PARTICIPATION ========================

def enter_public(usertag, userpsw, chattag):
    """Вход в публичный чат"""
    try:
        if not is_user(tag=usertag, psw=userpsw):
            return "incorrect user"

        result = execute_db('sait.db', '''
            SELECT is_public, users_tag FROM chats 
            WHERE chat_tag=? AND is_close=FALSE
        ''', (chattag,), fetch=True)

        if not result:
            return "chat is close"

        is_public, users_tag = result[0]['is_public'], result[0]['users_tag']

        if is_public:  # Public channel
            new_count = str(int(users_tag) + 1)
            execute_db('sait.db',
                       "UPDATE chats SET users_tag=? WHERE chat_tag=?",
                       (new_count, chattag), commit=True)
        else:  # Private group
            if get_status(usertag, chattag) is not None:
                return "user already in chat"

            chat_tags = f"{users_tag};{usertag}:user"
            execute_db('sait.db',
                       "UPDATE chats SET users_tag=? WHERE chat_tag=?",
                       (chat_tags, chattag), commit=True)

        if not set_news(usertag, f';n{chattag}:user'):
            return "error"

        return "success"
    except Exception as e:
        log_error(f"enter_public error: {e}")
        return "error"


def add_user(admintag, adminpsw, chattag, usertag):
    """Добавление пользователя в чат"""
    try:
        admin_status = get_status(admintag, chattag)
        if not is_user(tag=admintag, psw=adminpsw) or admin_status not in ("admin", "creater"):
            return "incorrect user"
        if chattag in blocked_tags(usertag):
            return "user has blocked chat"
        if get_status(usertag, chattag) is not None:
            return "user is already in chat"

        result = execute_db('sait.db',
                            "SELECT users_tag FROM chats WHERE chat_tag=?",
                            (chattag,), fetch=True)
        if not result:
            return "chat not found"

        chat_tags = f"{result[0]['users_tag']};{usertag}:user"
        execute_db('sait.db',
                   "UPDATE chats SET users_tag=? WHERE chat_tag=?",
                   (chat_tags, chattag), commit=True)

        if not set_news(usertag, f';n{chattag}:user'):
            return "error"

        return "success"
    except Exception as e:
        log_error(f"add_user error: {e}")
        return "error"


def ask_meet(usertag, userpsw, chattag):
    """Запрос на вступление в чат"""
    try:
        if not is_user(tag=usertag, psw=userpsw):
            return "incorrect user"
        if get_status(usertag, chattag) is not None:
            return "user already in chat"

        result = execute_db('sait.db',
                            "SELECT users_tag FROM chats WHERE chat_tag=?",
                            (chattag,), fetch=True)
        if not result:
            return "chat not found"

        chat_tags = f"{result[0]['users_tag']};{usertag}:ask"
        execute_db('sait.db',
                   "UPDATE chats SET users_tag=? WHERE chat_tag=?",
                   (chat_tags, chattag), commit=True)

        return "success"
    except Exception as e:
        log_error(f"ask_meet error: {e}")
        return "error"


def allow_meet(admintag, adminpsw, usertag, chattag, allow):
    """Подтверждение вступления в чат"""
    try:
        admin_status = get_status(admintag, chattag)
        if not is_user(tag=admintag, psw=adminpsw) or admin_status not in ("admin", "creater"):
            return "incorrect user"
        if get_status(usertag, chattag) != "ask":
            return "user is not requesting access"

        result = execute_db('sait.db',
                            "SELECT users_tag FROM chats WHERE chat_tag=?",
                            (chattag,), fetch=True)
        if not result:
            return "chat not found"

        chat_tags = [tag for tag in result[0]['users_tag'].split(";") if not tag.startswith(f"{usertag}:")]

        if allow:
            chat_tags.append(f"{usertag}:user")
            if not set_news(usertag, f';n{chattag}:user'):
                return "error"

        execute_db('sait.db',
                   "UPDATE chats SET users_tag=? WHERE chat_tag=?",
                   (";".join(chat_tags), chattag), commit=True)

        return "success"
    except Exception as e:
        log_error(f"allow_meet error: {e}")
        return "error"


def del_admin(usertag, admintag, adminpsw, chattag):
    """Удаление пользователя из чата"""
    try:
        admin_status = get_status(admintag, chattag)
        user_status = get_status(usertag, chattag)

        if not is_user(tag=admintag, psw=adminpsw) or admin_status not in ("admin", "creater"):
            return "incorrect user"
        if user_status in ("admin", "creater") and admin_status != "creater":
            return "user status is too high"

        result = execute_db('sait.db',
                            "SELECT users_tag FROM chats WHERE chat_tag=?",
                            (chattag,), fetch=True)
        if not result:
            return "chat not found"

        chat_tags = [tag for tag in result[0]['users_tag'].split(";") if not tag.startswith(f"{usertag}:")]
        execute_db('sait.db',
                   "UPDATE chats SET users_tag=? WHERE chat_tag=?",
                   (";".join(chat_tags), chattag), commit=True)

        if not set_news(usertag, f';d{chattag}'):
            return "error"

        return "success"
    except Exception as e:
        log_error(f"del_admin error: {e}")
        return "error"


def leav_chat(usertag, userpsw, chattag):
    """Выход из чата"""
    try:
        if not is_user(tag=usertag, psw=userpsw):
            return "incorrect user"

        result = execute_db('sait.db',
                            "SELECT is_public, users_tag FROM chats WHERE chat_tag=?",
                            (chattag,), fetch=True)
        if not result:
            return "chat not found"

        is_public, users_tag = result[0]['is_public'], result[0]['users_tag']

        if is_public:  # Public channel
            new_count = str(int(users_tag) - 1)
            execute_db('sait.db',
                       "UPDATE chats SET users_tag=? WHERE chat_tag=?",
                       (new_count, chattag), commit=True)
        else:  # Private chat
            chat_tags = [tag for tag in users_tag.split(";") if not tag.startswith(f"{usertag}:")]
            execute_db('sait.db',
                       "UPDATE chats SET users_tag=? WHERE chat_tag=?",
                       (";".join(chat_tags), chattag), commit=True)

        if not set_news(usertag, f';d{chattag}'):
            return "error"

        return "success"
    except Exception as e:
        log_error(f"leav_chat error: {e}")
        return "error"


# ======================== STATUS MANAGEMENT ========================

def up_status(admintag, adminpsw, chattag, usertag):
    """Повышение статуса пользователя"""
    try:
        if not is_user(tag=admintag, psw=adminpsw):
            return "incorrect user"

        admin_status = get_status(admintag, chattag)
        if admin_status not in ("admin", "creater"):
            return "incorrect status"

        user_status = get_status(usertag, chattag)
        result = execute_db('sait.db',
                            "SELECT is_public, users_tag FROM chats WHERE chat_tag=?",
                            (chattag,), fetch=True)
        if not result:
            return "chat not found"

        is_public, users_tag = result[0]['is_public'], result[0]['users_tag']
        chat_tags = [tag for tag in users_tag.split(";") if not tag.startswith(f"{usertag}:")]

        if user_status == "user" or is_public:
            new_status = "publisher"
            news_code = f';u{chattag}:publisher'
        elif user_status == "publisher":
            new_status = "admin"
            news_code = f';u{chattag}:admin'
        elif user_status == "admin" and admin_status == "creater":
            new_status = "creater"
            # Update user status first
            execute_db('sait.db',
                       "UPDATE chats SET users_tag=? WHERE chat_tag=?",
                       (f"{';'.join(chat_tags)};{usertag}:{new_status}", chattag), commit=True)

            if not set_news(admintag, f';d{chattag}'):
                return "error"
            if not set_news(usertag, f';u{chattag}:creater'):
                return "error"

            return leav_chat(admintag, adminpsw, chattag)
        else:
            return "user incorrect status"

        chat_tags.append(f"{usertag}:{new_status}")
        execute_db('sait.db',
                   "UPDATE chats SET users_tag=? WHERE chat_tag=?",
                   (";".join(chat_tags), chattag), commit=True)

        if not set_news(usertag, news_code):
            return "error"

        return "success"
    except Exception as e:
        log_error(f"up_status error: {e}")
        return "error"


def down_status(admintag, adminpsw, chattag, usertag):
    """Понижение статуса пользователя"""
    try:
        if not is_user(tag=admintag, psw=adminpsw):
            return "incorrect user"

        admin_status = get_status(admintag, chattag)
        if admin_status not in ("admin", "creater"):
            return "incorrect status"

        user_status = get_status(usertag, chattag)
        if user_status in (None, "user"):
            return "cannot downgrade user further"
        if user_status == "creater":
            return "cannot downgrade creater"
        if user_status == "admin" and admin_status != "creater":
            return "insufficient permissions"

        result = execute_db('sait.db',
                            "SELECT users_tag FROM chats WHERE chat_tag=?",
                            (chattag,), fetch=True)
        if not result:
            return "chat not found"

        chat_tags = [tag for tag in result[0]['users_tag'].split(";") if not tag.startswith(f"{usertag}:")]

        new_status = "publisher" if user_status == "admin" else "user"
        chat_tags.append(f"{usertag}:{new_status}")

        execute_db('sait.db',
                   "UPDATE chats SET users_tag=? WHERE chat_tag=?",
                   (";".join(chat_tags), chattag), commit=True)

        if not set_news(usertag, f';u{chattag}:{new_status}'):
            return "error"

        return "success"
    except Exception as e:
        log_error(f"down_status error: {e}")
        return "error"


# ======================== MESSAGING ========================

def set_avatar(usertag, userpsw, fileid, isgroup=False, chattag=None):
    """Установка аватара"""
    try:
        if not is_user(tag=usertag, psw=userpsw):
            return "incorrect user"

        if isgroup:
            if not chattag:
                return "chat tag required"

            admin = get_status(usertag, chattag)
            if admin not in ("admin", "creater"):
                return "incorrect status"

            execute_db('sait.db',
                       "UPDATE chats SET avatar_name=? WHERE chat_tag=?",
                       (fileid, chattag), commit=True)
        else:
            execute_db('sait.db',
                       "UPDATE user SET avatar_name=? WHERE tag=?",
                       (fileid, usertag), commit=True)

        return "success"
    except Exception as e:
        log_error(f"set_avatar error: {e}")
        return "error"


def send_file(name, psw, file_data):
    """Отправка файла"""
    try:
        execute_db('messages.db', '''
            INSERT INTO files (name, psw, file) 
            VALUES (?, ?, ?)
        ''', (name, psw, file_data), commit=True)

        # Get last inserted id
        result = execute_db('messages.db',
                            "SELECT last_insert_rowid() as id",
                            fetch=True)
        return str(result[0]['id']) if result else "-1"
    except Exception as e:
        log_error(f"send_file error: {e}")
        return "-1"


def send_message(usertag, userpsw, chattag, message, fileid=None):
    """Отправка сообщения"""
    try:
        if not is_user(tag=usertag, psw=userpsw):
            return "incorrect user"

        user_status = get_status(usertag, chattag)
        if user_status is None:
            return "user not in chat"

        result = execute_db('sait.db',
                            "SELECT is_public FROM chats WHERE chat_tag=?",
                            (chattag,), fetch=True)
        if not result:
            return "chat not found"

        is_public = result[0]['is_public']
        if is_public and user_status not in ("publisher", "admin", "creater"):
            return "incorrect status"

        compressed_msg = zlib.compress(f"m;{message}".encode('utf-8'))

        if fileid:
            execute_db('messages.db',
                       f'INSERT INTO "{chattag}" (tag, text, fileurl) VALUES (?, ?, ?)',
                       (usertag, compressed_msg, fileid), commit=True)
        else:
            execute_db('messages.db',
                       f'INSERT INTO "{chattag}" (tag, text, fileurl) VALUES (?, ?, NULL)',
                       (usertag, compressed_msg), commit=True)

        if not is_public:
            result = execute_db('sait.db',
                                "SELECT users_tag FROM chats WHERE chat_tag=?",
                                (chattag,), fetch=True)
            if result:
                for user in result[0]['users_tag'].split(';'):
                    user_tag = user.split(':')[0]
                    if not set_news(user_tag, f';m{chattag}'):
                        return "error setting news"

        return "success"
    except Exception as e:
        log_error(f"send_message error: {e}")
        return "error"


# ======================== DATA RETRIEVAL ========================

def get_avatar(tag, is_group):
    """Получение аватара"""
    try:
        if is_group:
            result = execute_db('sait.db',
                                "SELECT avatar_name FROM chats WHERE chat_tag=?",
                                (tag,), fetch=True)
        else:
            result = execute_db('sait.db',
                                "SELECT avatar_name FROM user WHERE tag=?",
                                (tag,), fetch=True)

        return str(result[0]['avatar_name']) if result and result[0]['avatar_name'] is not None else "-1"
    except Exception as e:
        log_error(f"get_avatar error: {e}")
        return "-1"


def get_file(psw, file_id):
    """Получение файла"""
    try:
        result = execute_db('messages.db',
                            "SELECT file, name FROM files WHERE id=? AND psw=?",
                            (file_id, psw), fetch=True)

        if not result:
            return "No file"

        return [result[0]['file'], result[0]['name']]
    except Exception as e:
        log_error(f"get_file error: {e}")
        return "No file"


def get_chat(usertag, userpsw, chattag, count):
    """Получение сообщений из чата"""
    try:
        if not is_user(tag=usertag, psw=userpsw):
            return [["-1", "incorrect user"], []]

        if get_status(usertag, chattag) is None:
            return [["-1", "user not in chat"], []]

        # Get max message id
        result = execute_db('messages.db',
                            f'SELECT MAX(id) as max_id FROM "{chattag}"',
                            fetch=True)
        max_id = result[0]['max_id'] if result and result[0]['max_id'] else 0

        if max_id <= count:
            return [['0', "success"], []]

        # Get new messages
        messages = execute_db('messages.db',
                              f'SELECT id, tag, text, fileurl FROM "{chattag}" WHERE id > ? ORDER BY id',
                              (count,), fetch=True)

        decompressed = []
        for msg in messages:
            try:
                text = zlib.decompress(msg['text']).decode('utf-8')
            except:
                text = msg['text']
            decompressed.append((msg['id'], msg['tag'], text, msg['fileurl']))

        return [[str(max_id - count), "success"], decompressed]
    except Exception as e:
        log_error(f"get_chat error: {e}")
        return [['-1', "error"], []]


# ======================== USER MANAGEMENT ========================

def change_name(tag, psw, newname):
    """Изменение имени пользователя"""
    try:
        if not is_user(tag=tag, psw=psw):
            return "incorrect user"

        execute_db('sait.db',
                   "UPDATE user SET name=? WHERE tag=?",
                   (newname, tag), commit=True)

        return "success"
    except Exception as e:
        log_error(f"change_name error: {e}")
        return "error"


def change_psw(tag, psw, newpsw):
    """Изменение пароля"""
    try:
        if not is_user(tag=tag, psw=psw):
            return "incorrect user"

        execute_db('sait.db',
                   "UPDATE user SET psw=? WHERE tag=?",
                   (newpsw, tag), commit=True)

        return "success"
    except Exception as e:
        log_error(f"change_psw error: {e}")
        return "error"


def get_news(tag, psw):
    """Получение новостей"""
    try:
        if not is_user(tag=tag, psw=psw):
            return ["incorrect user", ""]

        result = execute_db('sait.db',
                            "SELECT news FROM user WHERE tag=?",
                            (tag,), fetch=True)

        if not result:
            return ["error", ""]

        news = result[0]['news'] or ""
        execute_db('sait.db',
                   "UPDATE user SET news='' WHERE tag=?",
                   (tag,), commit=True)

        return ["success"] + news.split(";") if news else ["success", ""]
    except Exception as e:
        log_error(f"get_news error: {e}")
        return ["error", ""]


def block_user(tag1, psw, tag2):
    """Блокировка пользователя"""
    try:
        if not is_user(tag=tag1, psw=psw):
            return "incorrect user"

        result = execute_db('sait.db',
                            "SELECT blocked_tags FROM user WHERE tag=?",
                            (tag1,), fetch=True)

        if not result:
            return "user not found"

        blocked = result[0]['blocked_tags'] or ""

        if tag2.startswith("-"):  # Unblock
            tag_to_remove = tag2[1:]
            if not blocked:
                return "no one has blocked"

            blocked_list = [t for t in blocked.split(";") if t != tag_to_remove]
            new_blocked = ";".join(blocked_list)
        else:  # Block
            if blocked and tag2 in blocked.split(";"):
                return "user already blocked"

            new_blocked = f"{blocked};{tag2}" if blocked else tag2

        execute_db('sait.db',
                   "UPDATE user SET blocked_tags=? WHERE tag=?",
                   (new_blocked, tag1), commit=True)

        return "success"
    except Exception as e:
        log_error(f"block_user error: {e}")
        return "error"


# ======================== MESSAGE MANAGEMENT ========================

def dell_message(usertag, userpsw, chattag, messagenum):
    """Удаление сообщения (помечаем как удаленное)"""
    try:
        if not is_user(tag=usertag, psw=userpsw):
            return "incorrect user"

        user_status = get_status(usertag, chattag)
        if user_status is None:
            return "user not in chat"

        # Получаем информацию о сообщении
        msg_result = execute_db('messages.db',
                                f'SELECT tag FROM "{chattag}" WHERE id=?',
                                (messagenum,), fetch=True)
        if not msg_result:
            return "message not found"

        message_author = msg_result[0]['tag']

        # Проверяем права на удаление
        if message_author != usertag and user_status not in ("admin", "creater"):
            return "insufficient permissions"

        # Добавляем системное сообщение об удалении
        execute_db('messages.db',
                   f'INSERT INTO "{chattag}" (tag, text, fileurl) VALUES ("system", ?, NULL)',
                   (f"d;{messagenum}",), commit=True)

        # Уведомляем участников чата
        chat_info = execute_db('sait.db',
                               "SELECT is_public FROM chats WHERE chat_tag=?",
                               (chattag,), fetch=True)
        if not chat_info or not chat_info[0]['is_public']:
            users_result = execute_db('sait.db',
                                      "SELECT users_tag FROM chats WHERE chat_tag=?",
                                      (chattag,), fetch=True)
            if users_result:
                for user in users_result[0]['users_tag'].split(';'):
                    user_tag = user.split(':')[0]
                    if not set_news(user_tag, f';m{chattag}'):
                        return "error setting news"

        return "success"
    except Exception as e:
        log_error(f"dell_message error: {e}")
        return "error"


def change_message(usertag, userpsw, chattag, messagenum, newmessage):
    """Изменение сообщения"""
    try:
        if not is_user(tag=usertag, psw=userpsw):
            return "incorrect user"

        user_status = get_status(usertag, chattag)
        if user_status is None:
            return "user not in chat"

        # Получаем информацию о сообщении
        msg_result = execute_db('messages.db',
                                f'SELECT tag FROM "{chattag}" WHERE id=?',
                                (messagenum,), fetch=True)
        if not msg_result:
            return "message not found"

        message_author = msg_result[0]['tag']
        if message_author != usertag:
            return "you can't change this message"

        # Добавляем системное сообщение об изменении
        compressed_msg = zlib.compress(f"u;{messagenum};{newmessage}".encode('utf-8'))
        execute_db('messages.db',
                   f'INSERT INTO "{chattag}" (tag, text, fileurl) VALUES ("system", ?, NULL)',
                   (compressed_msg,), commit=True)

        # Уведомляем участников чата
        chat_info = execute_db('sait.db',
                               "SELECT is_public FROM chats WHERE chat_tag=?",
                               (chattag,), fetch=True)
        if not chat_info or not chat_info[0]['is_public']:
            users_result = execute_db('sait.db',
                                      "SELECT users_tag FROM chats WHERE chat_tag=?",
                                      (chattag,), fetch=True)
            if users_result:
                for user in users_result[0]['users_tag'].split(';'):
                    user_tag = user.split(':')[0]
                    if not set_news(user_tag, f';m{chattag}'):
                        return "error setting news"

        return "success"
    except Exception as e:
        log_error(f"change_message error: {e}")
        return "error"


def get_chat_info(chattag):
    """Получение информации о чате"""
    try:
        result = execute_db('sait.db', '''
            SELECT dialog, see_other, is_close, is_public, chat_name, users_tag 
            FROM chats WHERE chat_tag=?
        ''', (chattag,), fetch=True)

        if not result:
            return ["not found", []]

        info = result[0]
        if not info['dialog'] and info['see_other']:
            if info['is_public']:
                return ["success", [
                    info['dialog'], info['see_other'], info['is_close'],
                    info['is_public'], info['chat_name'], info['users_tag'].split(";")[0]
                ]]
            else:
                return ["success", [
                    info['dialog'], info['see_other'], info['is_close'],
                    info['is_public'], info['chat_name'], len(info['users_tag'].split(";"))
                ]]
        return ["not get", []]
    except Exception as e:
        log_error(f"get_chat_info error: {e}")
        return ["error", []]


def getin_chat_info(tag, psw, chattag):
    """Получение информации о чате для участника"""
    try:
        if not is_user(tag=tag, psw=psw):
            return ["incorrect user", []]

        status = get_status(tag, chattag)
        result = execute_db('sait.db', '''
            SELECT dialog, is_public, chat_name, users_tag 
            FROM chats WHERE chat_tag=?
        ''', (chattag,), fetch=True)

        if not result:
            return ["chat not found", []]

        info = result[0]
        if not status and not info['is_public'] and not info['dialog']:
            return ["you not in chat", []]

        if info['is_public'] or status not in (None, "ask"):
            return ["success", [
                info['dialog'], info['is_public'], info['chat_name'],
                info['users_tag']
            ]]
        elif status == "ask":
            return ["request pending", []]
        else:
            return ["access denied", []]
    except Exception as e:
        log_error(f"getin_chat_info error: {e}")
        return ["error", []]


def get_user(tag):
    """Получение информации о пользователе"""
    try:
        result = execute_db('sait.db', '''
            SELECT name, avatar_name FROM user WHERE tag=?
        ''', (tag,), fetch=True)

        if not result:
            return ["user not found", None, None]

        return ["success", result[0]['name'], result[0]['avatar_name']]
    except Exception as e:
        log_error(f"get_user error: {e}")
        return ["error", None, None]


def find(text):
    """Поиск пользователей и чатов"""
    try:
        if text.startswith("@"):
            # Поиск по тегу
            users = execute_db('sait.db', '''
                SELECT tag, name, avatar_name FROM user 
                WHERE tag LIKE ? || '%' LIMIT 20
            ''', (text,), fetch=True)

            chats = execute_db('sait.db', '''
                SELECT chat_tag, chat_name, avatar_name FROM chats 
                WHERE chat_tag LIKE ? || '%' AND see_other=TRUE LIMIT 20
            ''', (text,), fetch=True)
        else:
            # Поиск по имени
            users = execute_db('sait.db', '''
                SELECT tag, name, avatar_name FROM user 
                WHERE name LIKE ? || '%' LIMIT 20
            ''', (text,), fetch=True)

            chats = execute_db('sait.db', '''
                SELECT chat_tag, chat_name, avatar_name FROM chats 
                WHERE chat_name LIKE ? || '%' AND see_other=TRUE LIMIT 20
            ''', (text,), fetch=True)

            if not users and not chats:
                # Если ничего не найдено, ищем вхождение строки
                users = execute_db('sait.db', '''
                    SELECT tag, name, avatar_name FROM user 
                    WHERE name LIKE '%' || ? || '%' LIMIT 20
                ''', (text,), fetch=True)

                chats = execute_db('sait.db', '''
                    SELECT chat_tag, chat_name, avatar_name FROM chats 
                    WHERE chat_name LIKE '%' || ? || '%' AND see_other=TRUE LIMIT 20
                ''', (text,), fetch=True)

        return [users, chats]
    except Exception as e:
        log_error(f"find error: {e}")
        return [[], []]


# ======================== MAIN ========================

if __name__ == "__main__":
    initialize_databases()
