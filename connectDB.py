import sqlite3
import gc
import os
from passlib.hash import sha256_crypt
from flask import session
# UPLOAD_FOLDER = session['UPLOAD_FOLDER']
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static/app')

# 数据库路径
DATABASE = 'db/rshiny.db'


# 获取sqlite数据库链接
def connect_db():
    return sqlite3.connect(DATABASE)


# 获取数据库链接以及游标
def get_db():
    db = connect_db()
    cur = db.cursor()
    return db, cur


def create_user_folder(username):
    # 属于username的app存储目录不存在，即static/app/username不存在，则创建一个这个目录
    user_path = os.path.join(UPLOAD_FOLDER, username)
    if not os.path.exists(user_path):
        # 递归创建目录
        os.makedirs(user_path, exist_ok=True)


def user_register(username, password, email):
    # 获取数据库链接，游标
    db, cur = get_db()

    # 从user表查询获取username对应的记录
    x = cur.execute("SELECT * FROM user WHERE username = ?", [username])

    # username对应记录存在，即username已被别人注册
    if x.fetchall():
        tag = False

    # username对应记录不存在，向user表中插入username对应记录，并创建用户目录
    else:
        # 插入username等相关信息
        hash_password = sha256_crypt.encrypt(password)
        cur.execute("INSERT INTO user (username, password, email) VALUES(?,?,?)", [username, hash_password, email])

        # 提交事务，关闭数据库连接，游标，回收垃圾
        db.commit()
        cur.close()
        db.close()
        gc.collect()

        # 创建用户app存储目录
        create_user_folder(username)

        tag = True

    return tag


def verify_password(username, password):
    # 获取数据库链接与游标
    db, cur = get_db()

    # 从user表查询获取username对应的password的hash值，返回元组，只有1个元素
    password_hash_tuple = cur.execute("SELECT password FROM user WHERE username=?", [username]).fetchone()

    # 用户输入的username对应的password的hash值不存在，即username不存在，用户不存在
    if not password_hash_tuple:
        tag = 'Invalid username'

    # 用户输入的password对应的hash值与数据库中的hash值不相同，即密码错误
    elif not sha256_crypt.verify(password, password_hash_tuple[0]):
        tag = 'Invalid password'

    # 用户存在，密码正确，登录成功
    else:
        # 提交事务，关闭数据库连接，游标，回收垃圾
        db.commit()
        cur.close()
        db.close()
        gc.collect()

        # 创建用户app存储目录
        create_user_folder(username)

        tag = 'True'

    return tag


def create_app_data(app_name, app_author, app_date, app_summary, app_url, app_path):
    # 获取数据库链接，游标
    db, cur = get_db()

    # 向app表中插入上传的app相关信息
    cur.execute(
        "INSERT INTO app (app_name, app_author, app_date, app_summary, app_url, app_path) VALUES(?,?,?,?,?,?)",
        [app_name, app_author, app_date, app_summary, app_url, app_path])

    # 提交事务，关闭数据库连接，游标，回收垃圾
    db.commit()
    cur.close()
    db.close()
    gc.collect()

    return True


def update_app_data(app_name, app_author, app_date, app_summary, app_url, app_path):
    # 获取数据库链接，游标
    db, cur = get_db()

    # 向app表中插入上传的app相关信息
    cur.execute(
        "UPDATE app SET app_date = ?, app_summary = ?, app_url = ?, app_path = ? where app_name = ? and app_author = ?",
        [app_date, app_summary, app_url, app_path, app_name, app_author])

    # 提交事务，关闭数据库连接，游标，回收垃圾
    db.commit()
    cur.close()
    db.close()
    gc.collect()

    return True


def get_app_data(app_name, app_author):
    # 获取数据库链接，游标
    db, cur = get_db()
    # 查询app_data
    app_data = cur.execute("SELECT * FROM app where app_name = ? and app_author = ?",
                                      [app_name, app_author]).fetchone()

    # 提交事务，关闭数据库连接，游标，回收垃圾
    db.commit()
    cur.close()
    db.close()
    gc.collect()

    return app_data


def delete_app_data(app_name, app_author):
    # 获取数据库链接，游标
    db, cur = get_db()

    # 要删除app的存储路径
    delete_app_path = cur.execute("SELECT app_path FROM app where app_name = ? and app_author = ?",
                                  [app_name, app_author]).fetchone()[0]

    # 路径存在，则删除该app的文件
    if os.path.exists(delete_app_path):
        os.remove(delete_app_path)

    # 从app表中删除该app相关的信息
    cur.execute("DELETE FROM app where app_name = ? and app_author = ?", [app_name, app_author])

    # 提交事务，关闭数据库连接，游标，回收垃圾
    db.commit()
    cur.close()
    db.close()
    gc.collect()

    return True

