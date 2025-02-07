import asyncio
from websockets.asyncio.connection import broadcast
from websockets.asyncio.server import serve
import db_connection as db
import json


users = {}


async def handle_connect(websocket):
    async for message in websocket:
        data = json.loads(message)
        if data['purpose'] == 'connect':
            user_id = data['user_id']
            print(data)
            if len(users.keys()) < 100:
                users[user_id] = websocket
                print(users.keys())
                print(users.values())
        elif data['purpose'] == 'message':
            chat_id = data['chat_id']
            sender_id = data['sender_id']
            recipient_id = data['recipient_id']
            message_text = data['message']
            result = db.check_destination_of_message(chat_id)
            chat = []
            for i in result:
                if i[0] != sender_id:
                    socket = users.get(i[0])
                    if socket is not None:
                        chat.append(users.get(i[0]))
                else:
                    data['sender_name'] = i[1]
            print(chat)
            db.add_message(chat_id, sender_id, recipient_id, message_text)
            broadcast(chat, json.dumps(data))
            chat = []


async def main():
    async with serve(handle_connect, "192.168.1.67", 1504):
        await asyncio.Future()  # run forever

asyncio.run(main())
