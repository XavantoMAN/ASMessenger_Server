# -*- coding: utf-8 -*-
import ast
import contextlib
from typing import Any
import os
import sqlite3
from werkzeug import security
from dotenv import load_dotenv

load_dotenv()


class CursorDB:

    def __init__(self):
        try:
            self.connection = sqlite3.connect('asmessenger.db', check_same_thread=False)
        except Exception as e:
            print(f'Во время подключения возникла ошибка: {e}')

        self.cursor = self.connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()

    def __del__(self):
        self.connection.close()


@contextlib.contextmanager
def get_cursor():
    with CursorDB() as cursor:
        yield cursor


def add_user(phone_number: str, password: str) -> str:
    with get_cursor() as cur:
        psw_hash = security.generate_password_hash(password)
        query = f'''
            INSERT INTO users (phone_number, password) 
            VALUES('{phone_number}', '{psw_hash}')
            '''
        try:
            cur.cursor.execute(query)
            cur.cursor.execute("SELECT LAST_INSERT_ID()")
            last_id = cur.cursor.fetchone()[0]
            query = f'''
                    INSERT INTO user_info (user_id, nickname, user_tag) VALUES({last_id}, 'user{last_id}', 'user{last_id}')
                    '''
            cur.cursor.execute(query)
            print("user added")
            return f"{last_id}"
        except Exception as e:
            if 'duplicate entry' in str(e).lower():
                print("Пользователь уже существует: ", e)
                return "user already exist"
            else:
                print("Возникло исключение во время выполнения запроса:", e)
                return "bad request"


def auth_user(phone_number: str, password: str) -> str:
    with get_cursor() as cur:
        query = f'''
                SELECT id, password FROM users WHERE phone_number = '{phone_number}'
                '''
        try:
            cur.cursor.execute(query)
            result = cur.cursor.fetchone()
            psw_bd = result[1]
            if psw_bd is not None:
                if security.check_password_hash(psw_bd, password):
                    return f"{result[0]};{result[2]}\n"
                else:
                    return "Wrong password\n"
            else:
                return "User not registered\n"
        except Exception as e:
            print("Возникло исключение во время выполнения запроса:", e)
            return "Not registered\n"


def show_selected_user(user_id: str) -> str:
    with get_cursor() as cur:
        query = f'''
                SELECT user_info.nickname, user_info.avatar_url, users.phone_number
                FROM user_info
                LEFT JOIN users ON (user_info.user_id = users.id)
                WHERE user_info.user_id = {user_id} 
                '''
        try:
            cur.cursor.execute(query)
            result = cur.cursor.fetchone()
            data = ""
            if result is not None:
                for i in result:
                    if i is not None:
                        data += i + ","
                    else:
                        data += ","
                data += "\n"
                return data
            else:
                return "Bad request"
        except Exception as e:
            print("Возникло исключение во время выполнения запроса:", e)
            return "Bad request"


def update_user_data(user_id: int, user_avatar: str, user_nickname: str) -> str:
    with get_cursor() as cur:
        query = f'''
                UPDATE user_info
                SET nickname = '{user_nickname}', avatar_url = '{user_avatar}'
                WHERE user_id = {user_id}
                '''
        try:
            cur.cursor.execute(query)
            print("info updated")
            return "OK"
        except Exception as e:
            print("Возникло исключение во время выполнения запроса:", e)
            return "Bad request"


def get_chat_id(first_member_id: int, second_member_id: int) -> str:
    with get_cursor() as cur:
        query = f'''
                SELECT
                    chat_id
                FROM
                    chat_members
                WHERE
                    user_id = {first_member_id}
                INTERSECT
                SELECT
                    chat_id
                FROM
                    chat_members
                WHERE
                    user_id = {second_member_id}
                '''
        try:
            cur.cursor.execute(query)
            try:
                result = str(cur.cursor.fetchone()[0])
                return result
            except TypeError as e:
                print("None нельзя проиндексировать: ", e)
                return "null"
        except Exception as e:
            print("Возникло исключение во время выполнения запроса:", e)
            return "Bad request"


def create_chat(first_member_id: int, second_member_id: int) -> str:
    with get_cursor() as cur:
        query = '''
                INSERT INTO chat
                VALUES(null)
                '''
        try:
            cur.cursor.execute(query)
            cur.cursor.execute('SELECT LAST_INSERT_ID()')
            last_id = cur.cursor.fetchone()[0]
            query = f'''
                    INSERT INTO chat_members
                    VALUES({last_id}, {first_member_id}, 1)
                    '''
            cur.cursor.execute(query)
            query = f'''
                    INSERT INTO chat_members
                    VALUES({last_id}, {second_member_id}, 1)
                    '''
            cur.cursor.execute(query)
            return str(last_id)
        except Exception as e:
            print("Возникло исключение во время выполнения запроса:", e)
            return "Bad request"


def get_partner_info(partner_id: int) -> tuple | str:
    with get_cursor() as cur:
        query = f'''
                SELECT nickname, avatar_url
                FROM user_info
                WHERE user_id = {partner_id}
                '''
        try:
            cur.cursor.execute(query)
            result = cur.cursor.fetchone()
            return result
        except Exception as e:
            print("Возникло исключение во время выполнения запроса:", e)
            return "Bad request"


def get_messages(chat_id: int, recipient_id: int, p: int) -> list | str:
    # (p-1) * N -> формула для расчета кол-ва пропускаемых записей таблицы где p - это номер страницы,
    # а N - число записей которые мы хотим получить из таблицы
    with get_cursor() as cur:
        N = 30
        query = f'''
                SELECT message.message_id, sender_id, content, message_datetime, status_id
                FROM message
                LEFT JOIN chat_messages ON message.message_id = chat_messages.message_id
                WHERE chat_id = {chat_id} AND chat_messages.recipient_id != {recipient_id}
                ORDER BY message_id DESC
                LIMIT {N} OFFSET {(p-1) * N}
                '''
        try:
            cur.cursor.execute(query)
            result = cur.cursor.fetchall()
            new_data = []
            for i in range(len(result)):
                temp = []
                for j in range(len(result[i])):
                    if j == 3:
                        lst = str(result[i][j]).split(' ')
                        temp.append(lst[0])
                        lst[1] = lst[1][0:5]
                        temp.append(lst[1])
                    else:
                        temp.append(result[i][j])
                new_data.append(temp)
            return new_data
        except Exception as e:
            print("Возникло исключение во время выполнения запроса:", e)
            return "Bad request"


def check_destination_of_message(chat_id: int):
    # Функция проверяет кому предназначено сообщение и возвращает список id этих пользователей
    with get_cursor() as cur:
        query = f'''
                SELECT chat_members.user_id, user_info.nickname
                FROM chat_members
                LEFT JOIN user_info ON chat_members.user_id = user_info.user_id
                WHERE chat_id = {chat_id}
                '''
        try:
            cur.cursor.execute(query)
            result = cur.cursor.fetchall()
            return result
        except Exception as e:
            print("Возникло исключение во время выполнения запроса:", e)
            return False


def add_message(chat_id: int, sender_id: int, recipient_id: int, message_text: str) -> int | str:
    with get_cursor() as cur:
        query = f'''
                INSERT INTO message(chat_id, sender_id, content_type_id, content)
                VALUES({chat_id}, {sender_id}, 1, '{message_text}')
                '''
        try:
            cur.cursor.execute(query)
            message_id = cur.cursor.lastrowid
            query = f'''
                    INSERT INTO chat_messages(message_id, recipient_id, status_id, is_sender)
                    VALUES ({message_id}, {sender_id}, 3, 1), ({message_id}, {recipient_id}, 1, 0)
                    '''
            cur.cursor.execute(query)
            return message_id
        except Exception as e:
            print("Возникло исключение во время выполнения запроса:", e)
            return "Bad request"


def change_message_status_to_delivered(recipient_id: int) -> str:
    with get_cursor() as cur:
        query = f'''
                UPDATE chat_messages
                SET status_id = 2
                WHERE status_id = 1 AND recipient_id = {recipient_id}
                '''
        try:
            cur.cursor.execute(query)
            return "OK"
        except Exception as e:
            print("Возникло исключение во время выполнения запроса:", e)
            return "Bad request"


def change_message_status_to_read(chat_id: int, recipient_id: int) -> str:
    with get_cursor() as cur:
        query = f'''
                SELECT message_id
                FROM chat_messages
                WHERE recipient_id = {recipient_id} AND status_id = 2 OR status_id = 1
                INTERSECT
                SELECT message_id
                FROM message
                WHERE chat_id = {chat_id}
                '''
        try:
            cur.cursor.execute(query)
            messages = cur.cursor.fetchall()
            for message in messages:
                message_id = message[0]
                query = f'''
                        UPDATE chat_messages
                        SET status_id = 3
                        WHERE message_id = {message_id} AND recipient_id = {recipient_id}
                        '''
                cur.cursor.execute(query)
            return "OK"
        except Exception as e:
            print("Возникло исключение во время выполнения запроса:", e)
            return "Bad request"


def get_chat_list(user_id: int) -> list | str:
    with get_cursor() as cur:
        query = f'''
                SELECT chat_id 
                FROM chat_members
                WHERE user_id = {user_id}
                '''
        try:
            cur.cursor.execute(query)
            result = cur.cursor.fetchall()
            chats = []
            for lst in result:
                for chat_id in lst:
                    query = f'''
                            SELECT 
                                chat_id, 
                                user_info.user_id, 
                                nickname, 
                                avatar_url,
                                (SELECT 
                                    content
                                FROM 
                                    message 
                                WHERE 
                                    chat_id = {chat_id} 
                                ORDER BY 
                                    message_id DESC LIMIT 1) as last_message, 
                                (SELECT 
                                    sender_id 
                                FROM 
                                    message 
                                WHERE 
                                    chat_id = {chat_id}
                                ORDER BY 
                                    message_id DESC LIMIT 1) as sender
                            FROM user_info
                            LEFT JOIN chat_members ON chat_members.user_id = user_info.user_id
                            WHERE user_info.user_id != {user_id} AND chat_id = {chat_id}
                            '''
                    cur.cursor.execute(query)
                    chat_data = cur.cursor.fetchone()
                    chats.append(chat_data)
            return chats
        except Exception as e:
            print("Возникло исключение во время выполнения запроса:", e)
            return "Bad request"


def get_foreign_profile(user_id: int) -> list | str:
    with get_cursor() as cur:
        query = f'''
                SELECT nickname, avatar_url, phone_number
                FROM user_info
                LEFT JOIN users ON users.id = user_info.user_id
                WHERE user_info.user_id = {user_id}            
                '''
        try:
            cur.cursor.execute(query)
            result = cur.cursor.fetchone()
            user_data = [result]
            return user_data
        except Exception as e:
            print("Возникло исключение во время выполнения запроса:", e)
            return "Bad request"


def search_users_by_phone(phone: str) -> list | str:
    with get_cursor() as cur:
        query = f'''
                SELECT user_info.user_id, user_info.nickname, user_info.avatar_url
                FROM user_info
                LEFT JOIN users ON users.id = user_info.user_id
                WHERE users.phone_number LIKE "%{phone}%"  
                '''
        try:
            cur.cursor.execute(query)
            result = cur.cursor.fetchall()
            return result
        except Exception as e:
            print("Возникло исключение во время выполнения запроса:", e)
            return "Bad request"
