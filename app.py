from flask import Flask, request
from werkzeug.utils import secure_filename
from waitress import serve
import db_connection
import json

UPLOAD_FOLDER = '/static/user_avatars'

HOST = "192.168.0.102"
PORT = 1500

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route("/register", methods=['POST'])
def register():
    data = request.data.decode().split(';')
    phone = data[0]
    password = data[1]
    result = db_connection.add_user(phone, password)
    return result


@app.route("/login", methods=['POST'])
def login():
    data = request.data.decode().split(';')
    phone = data[0]
    password = data[1]
    result = db_connection.auth_user(phone, password)
    return result


@app.route("/user_info", methods=['POST'])
def user_info():
    user_id = request.data.decode()
    result = db_connection.show_selected_user(user_id)
    return result


@app.route('/upload_image', methods=['POST'])
def upload_image():
    image = request.files['file']
    directory = "C:/Users/admin/PycharmProjects/ASMessenger_Server/static/users_avatars/"
    file_name = secure_filename(image.filename)
    file = directory + file_name
    image.save(file)
    return file_name


@app.route('/save_user_data', methods=['POST'])
def save_user_data():
    user_data = request.data.decode()
    user_data = json.loads(user_data)
    user_id = user_data['user_id']
    user_avatar = user_data['path_to_image']
    user_nickname = user_data['user_nickname']
    result = db_connection.update_user_data(user_id, user_avatar, user_nickname)
    return result


@app.route("/get_chat_id", methods=['POST'])
def get_chat_id():
    user_data = request.data.decode()
    user_data = json.loads(user_data)
    first_member_id = user_data['first_id']
    second_member_id = user_data['second_id']
    result = db_connection.get_chat_id(first_member_id, second_member_id)
    return result


@app.route("/create_chat", methods=['POST'])
def create_chat():
    user_data = request.data.decode()
    user_data = json.loads(user_data)
    first_member_id = user_data['first_id']
    second_member_id = user_data['second_id']
    result = db_connection.create_chat(first_member_id, second_member_id)
    return result


@app.route("/get_partner_info", methods=['POST'])
def get_partner_info():
    user_data = request.data.decode()
    user_data = json.loads(user_data)
    partner_id = user_data['partner_id']
    result = db_connection.get_partner_info(partner_id)
    return result


@app.route("/get_messages", methods=['POST'])
def get_messages():
    user_data = request.data.decode()
    user_data = json.loads(user_data)
    chat_id = user_data['chat_id']
    user_id = user_data['user_id']
    page = user_data['page']
    result = db_connection.get_messages(chat_id, user_id, page)
    return result


@app.route("/show_chat_list", methods=['POST'])
def show_chat_list():
    user_id = int(request.data.decode())
    result = db_connection.get_chat_list(user_id)
    return result


@app.route("/get_foreign_profile", methods=['POST'])
def get_foreign_profile():
    user_id = int(request.data.decode())
    result = db_connection.get_foreign_profile(user_id)
    return result


@app.route("/search_users_by_phone", methods=['POST'])
def search_users_by_phone():
    search_string = request.data.decode()
    result = db_connection.search_users_by_phone(search_string)
    return result


serve(app, host=HOST, port=PORT)
