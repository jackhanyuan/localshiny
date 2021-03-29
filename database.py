
import gc
import os
from passlib.hash import sha256_crypt
import re
import shutil
import sqlite3
import time
from token_id_gen import generate_token, generate_short_id, get_username_time_from_token


UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static/package')


# 数据库路径
DATABASE = 'db/qtshiny.db'


# 获取数据库链接以及游标
def get_db():
    db = sqlite3.connect(DATABASE)
    cur = db.cursor()
    return db, cur


# 提交事务，关闭数据库连接，游标，回收垃圾
def close_db(db, cur):
    db.commit()
    cur.close()
    db.close()
    gc.collect()
    return True


def get_data():
    # 获取数据库链接与游标
    db, cur = get_db()

    # 查询数据
    x = cur.execute("SELECT * FROM user")
    print(x.fetchall())
    y = cur.execute("SELECT * FROM package")
    print(y.fetchall())

    # 提交并关闭数据库
    close_db(db, cur)

    return True


# ------------------------------注册登陆相关--------------------------
def create_user_folder(username):
    # 属于username的package存储目录不存在，即static/package/username不存在，则创建一个这个目录
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
        hash_password = sha256_crypt.hash(password)
        # 生成id和token并插入
        userid = generate_short_id()
        token = generate_token(username)
        cur.execute("INSERT INTO user (userid, username, password, email, token) VALUES(?,?,?,?,?)", [userid, username, hash_password, email, token])

        # 提交并关闭数据库
        close_db(db, cur)

        # 创建用户package存储目录
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
        # 提交并关闭数据库
        close_db(db, cur)

        # 创建用户package存储目录
        create_user_folder(username)

        tag = 'True'

    return tag


def delete_user(username):
    # 获取数据库链接，游标
    db, cur = get_db()
    # 要删除user的存储路径
    userpath = UPLOAD_FOLDER + '/' + username

    # 路径存在，则删除该user的路径
    if os.path.exists(userpath):
        del_file(userpath)

    # 从user表中删除该user相关的信息
    cur.execute("DELETE FROM user where username = ?", [username])
    cur.execute("DELETE FROM package where pakauthor = ?", [username])
    # 提交事务，关闭数据库连接，游标，回收垃圾
    close_db(db, cur)
    return True



# ----------------------------------token相关-------------------------------
# 获取token
def get_token(username):
    # 获取数据库链接，游标
    db, cur = get_db()

    # 查询username对应的token
    token_tuple = cur.execute(
        "SELECT token FROM user where username = ?", [username]).fetchone()

    # toekn对应记录不存在，即用户名错误
    if not token_tuple:
        tag = False
    else:
        tag = token_tuple[0]

    # 提交并关闭数据库
    close_db(db, cur)

    return tag


# 更新token
def update_token(username):
    # 获取数据库链接，游标
    db, cur = get_db()

    token = generate_token(username)
    # 向package表中插入上传的package相关信息
    cur.execute(
        "UPDATE user SET token = ? where username = ?", [token, username])

    # 提交并关闭数据库
    close_db(db, cur)

    return token


# token验证：先解析出username和time，再从数据库中查询验证
def verify_token(name, token):
    try:
        username, time_str = get_username_time_from_token(token)
        if name != username:
            # username does not match
            tag = (False, 'username does not match.')
            return tag
        if float(time_str) < time.time():
            # token expired
            tag = (False, 'token expired, please copy new token and try again.')
            update_token(username)
            return tag
        token_in_database = get_token(username)
        if token != token_in_database:
            # token certification failed
            tag = (False, 'token certification failed, please copy the correct token and try again.')
            return tag
        # token certification success
        tag = (True, username)
    except:
        tag = (False, 'token does not exist, please copy the correct token and try again.')

    return tag


# ----------------------------------package相关----------------------------
def create_package_data(pakid, pakname, pakauthor, version,  pakdesc, pakos, arch, distribution, pakdate, upmethod, rversion, runcmd, filepath, fileurl):
    # 获取数据库链接，游标
    db, cur = get_db()

    # 向package表中插入上传的package相关信息
    cur.execute(
        "INSERT INTO package (pakid, pakname, pakauthor, version,  pakdesc, pakos, arch, distribution, pakdate, upmethod, rversion, runcmd, filepath, fileurl) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [pakid, pakname, pakauthor, version,  pakdesc, pakos, arch, distribution, pakdate, upmethod, rversion, runcmd, filepath, fileurl])

    # 提交事务，关闭数据库连接，游标，回收垃圾
    close_db(db, cur)

    return True


def update_package_data(pakid, pakname, pakauthor, version,  pakdesc, pakos, arch, distribution, pakdate, upmethod, rversion, runcmd, filepath, fileurl):
    # 获取数据库链接，游标
    db, cur = get_db()

    # 向package表中插入上传的package相关信息
    cur.execute(
        "UPDATE package SET pakname = ?, pakauthor = ?, version = ?,  pakdesc = ?, pakos = ?, arch = ?, distribution = ?, pakdate = ?, upmethod = ?, rversion = ?, runcmd = ?, filepath = ?, fileurl = ? where pakid = ?",
        [pakname, pakauthor, version,  pakdesc, pakos, arch, distribution, pakdate, upmethod, rversion, runcmd, filepath, fileurl, pakid])

    # 提交事务，关闭数据库连接，游标，回收垃圾
    close_db(db, cur)

    return True


def get_pakid(pakname, pakauthor):
    # 获取数据库链接，游标
    db, cur = get_db()

    # 获取要删除的pakid
    try:
        pakid = cur.execute("SELECT pakid FROM package where pakname = ? and pakauthor = ?", [pakname, pakauthor]).fetchone()[0]
        return pakid
    except:
        return False

    # 提交事务，关闭数据库连接，游标，回收垃圾
    close_db(db, cur)


def get_package_data(pakid):
    # 获取数据库链接，游标
    db, cur = get_db()
    # 查询package_data
    package_data = cur.execute("SELECT * FROM package where pakid = ?",
                                      [pakid]).fetchone()

    # 提交事务，关闭数据库连接，游标，回收垃圾
    close_db(db, cur)

    return package_data


def get_user_pakid(pakauthor):
    # 获取数据库链接，游标
    db, cur = get_db()
    pakid = cur.execute("SELECT pakid,pakname FROM package where pakauthor = ?", [pakauthor]).fetchall()
    pakid = list(pakid)

    # 提交事务，关闭数据库连接，游标，回收垃圾
    close_db(db, cur)

    return pakid


def delete_package_data(pakid):
    # 获取数据库链接，游标
    db, cur = get_db()

    # 要删除package的存储路径
    filepath = cur.execute("SELECT filepath FROM package where pakid = ?",
                                  [pakid]).fetchone()[0]

    # 路径存在，则删除该package的文件
    if os.path.exists(filepath):
        os.remove(filepath)

    # 从package表中删除该package相关的信息
    cur.execute("DELETE FROM package where pakid = ?", [pakid])

    # 提交事务，关闭数据库连接，游标，回收垃圾
    close_db(db, cur)

    return True


def is_v1_greater_than_v2(v1, v2):

    v1_check = re.match("\d+(\.\d+){0,2}", v1)
    v2_check = re.match("\d+(\.\d+){0,2}", v2)
    if v1_check is None or v2_check is None or v1_check.group() != v1 or v2_check.group() != v2:
        return "Wrong version format, the correct one should be x.x.x"
    v1_list = v1.split(".")
    v2_list = v2.split(".")
    v1_len = len(v1_list)
    v2_len = len(v2_list)
    if v1_len > v2_len:
        for i in range(v1_len - v2_len):
            v2_list.append("0")
    elif v2_len > v1_len:
        for i in range(v2_len - v1_len):
            v1_list.append("0")
    else:
        pass
    for i in range(len(v1_list)):
        if int(v1_list[i]) > int(v2_list[i]):
            return True
        if int(v1_list[i]) < int(v2_list[i]):
            return False
    return False

# ----------------------------------------文件夹相关---------------------------

# 创建app临时存储目录
def create_temp_folder(temp_path):
    # 如果不存在临时目录，则创建temp目录作为app的临时目录
    if not os.path.exists(temp_path):
        os.makedirs(temp_path, exist_ok=True)


# 删除某一目录下的所有文件或文件夹
def del_file(filepath):
    """
    删除某一目录下的所有文件或文件夹
    :param filepath: 路径
    :return:
    """
    del_list = os.listdir(filepath)
    for f in del_list:
        file_path = os.path.join(filepath, f)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    os.rmdir(filepath)


# if __name__ == '__main__':
#     delete_user('admin')
#     get_data()
#     print(get_pakid('idem3', 'admin3'))
#     print(get_user_pakid('hello'))
    # print('-' * 50)
    # user_register('haha1','test','test')
    # print('-' * 50)
    # get_data()
    # print(get_token('haha'))
    # print(update_token('admin'))
    # print(get_token('haha'))
    # print(verify_token(get_token('haha')))

