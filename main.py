from datetime import timedelta, datetime
from flask import Flask, render_template, request, session, redirect, abort, jsonify, send_from_directory
from flask_session import Session
import os
import redis
import shutil
from tus.flask_tus import tus_manager
from werkzeug.utils import secure_filename
from connectDB import get_db, user_register, verify_password, create_app_data, update_app_data, get_app_data, delete_app_data
from rhiny import RegistrationForm, RShinyApp, create_temp_folder, del_file

# 配置参数
app = Flask(__name__)
app.debug = True

# 最大有效负载限制为 200MB (文件上传限制200M)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

# --------------------session设置----------------------------------- #
# 密钥随机产生24位
app.config['SECRET_KEY'] = os.urandom(24)
# 密钥存活时间为7天
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# 这里session使用redis的配置，可以解决session变量值更改后不生效bug
# 指明保存到redis中
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.StrictRedis(host="127.0.0.1", port=6379)
Session(app)
# ----------------------------------------------------------------- #

# 常量参数设置
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static/app')
TEMP_FOLDER = os.path.join(os.path.dirname(__file__), 'temp')
ALLOWED_EXTENSIONS = set(['zip'])
HOST = 'http://127.0.0.1:5000'


# 存储所有app信息的字典
app_dict = {}
# 存储已登录用户的所有app信息的字典  1
my_app_dict = {}

# tus文件断点续传
# upload_url: 客户端利用TUS协议上传的URL，客户端的TUS指向这个URL
# upload_folder: 存储上传文件的临时目录
tus_manager(app, upload_url='/file-upload', upload_folder='temp')


# 初始化所有app，以及已登录用户的所有app信息
def init_apps():
    try:
        # 获取数据库链接，游标
        db, cur = get_db()

        # 清空原来内容
        app_dict.clear()
        my_app_dict.clear()

        # 用来给app编号，同时给前端的app设定页码
        i = 1
        # 从app表查询获取所有app的信息
        all_app = cur.execute("SELECT * FROM app").fetchall()
        for one_app in all_app:
            app_dict[i] = RShinyApp(one_app[0], one_app[1], one_app[2], one_app[3], one_app[4], one_app[5])
            i += 1

        # 编号
        i = 1
        # 从app表查询获取已登录用户所有app的信息
        all_my_app = cur.execute("SELECT * FROM app where app_author = ?", [session.get('username')]).fetchall()
        for one_app in all_my_app:
            my_app_dict[i] = RShinyApp(one_app[0], one_app[1], one_app[2], one_app[3], one_app[4], one_app[5])
            i += 1

        # 提交事务，关闭数据库连接，游标，并回收垃圾
        db.commit()
        cur.close()
        db.close()
        gc.collect()
    except Exception as e:
        return str(e)


# Home页面相关
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


# About页面相关
@app.route('/about')
def about():
    return render_template('about.html')


# Documentation页面相关
@app.route('/doc')
def doc():
    return render_template('doc.html')


# RShinyApps页面相关
@app.route('/apps')
def apps():
    # 先初始化所有app的信息，参数传给apps.html，再渲染页面
    init_apps()
    return render_template('apps.html', app_dict=app_dict)


# 用户app页面相关
@app.route('/myapps')
def myapps():
    # 先初始化已登录用户所有app的信息，参数传给myapps.html，再渲染页面
    init_apps()
    return render_template('myapps.html', my_app_dict=my_app_dict)


# register页面相关
@app.route('/register', methods=['POST', 'GET'])
def register():
    try:
        # 存储错误信息
        error = None

        # 获取客户端提交的form注册表单
        form = RegistrationForm(request.form)
        # POST请求，且form注册表单验证通过，合法
        if request.method == 'POST' and form.validate():
            # 获取username、email
            username = form.username.data
            email = form.email.data
            password = str(form.password.data)

            # 用户注册成功
            if user_register(username, password, email):

                # 通过session设置用户登录成功，并保存登录信息username
                session['logged_in'] = True
                session['username'] = username

                # 登录成功后，返回到用户app的页面
                return redirect('/myapps')

            # 用户username已被注册
            else:
                error = "That username is already taken, please choose another."

        # GET请求、username已被注册，全部返回到注册页面
        return render_template('register.html', form=form, error=error)
    except Exception as error:
        return str(error)


@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        username = request.json.get('username')
        email = request.json.get('email')
        password = request.json.get('password')
        if username is None or password is None or email is None:
            return (jsonify({'result': 0, 'description': 'username & email & password can not be empty.'}), 400)
        if user_register(username, password, email):
            return (jsonify({'result': 1, 'description': username + ' register successful.'}), 201 )
        else:
            return (jsonify({'result': 0, 'description': 'existing user.'}), 200)
    except Exception as error:
        return (jsonify({'error': str(error)}), 400)


# login页面相关
@app.route('/login', methods=['POST', 'GET'])
def login():
    try:
        # 已登录则跳转到用户app的页面
        logged_in = session.get('logged_in')
        if logged_in:
            return redirect('/myapps')

        # 存储错误信息，用来反馈给前端
        error = None

        # POST请求，即请求登录
        if request.method == 'POST':
            # 获取username、password
            username = request.form.get('username')
            password = request.form.get('password')

            # 密码校验
            login_tag = verify_password(username, password)

            # 密码正确
            if login_tag == 'True':
                # 通过session设置用户登录成功，并保存登录信息username
                session['logged_in'] = True
                session['username'] = username
                # session以cookies方式存在客户端
                # 如果设置了session的permanent属性为True，那么过期时间是31天
                # 如果没有指定session的过期时间，那么默认是浏览器关闭就自动结束，
                session.permanent = True

                # 登录成功后，返回到用户app的页面
                return redirect('/myapps')

            # 用户不存在或密码错误
            else:
                error = login_tag

        # GET请求、用户不存在、密码错误，全部返回到登录页面
        return render_template('login.html', error=error)
    except Exception as error:
        return str(error)


@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        # 存储错误信息
        error = None
        # 获取用户名密码
        username = request.json.get('username')
        password = request.json.get('password')
        # 密码校验
        login_tag = verify_password(username, password)
        # 密码正确
        if login_tag == 'True':
            # 通过session设置用户登录成功，并保存登录信息username
            session['logged_in'] = True
            session['username'] = username
            session.permanent = True
            return (jsonify({'result': 1, 'description': str(session.get('username')) + ' Login successful.'}), 200)
        # 用户不存在或密码错误
        else:
            error = login_tag
            return (jsonify({'result': 0, 'description': 'Login failed, ' + login_tag + '.'}), 401)
    except Exception as error:
        return (jsonify({'error': error}), 400)


@app.route('/api/status', methods=['POST'])
def api_login_status():
    logged_in = session.get('logged_in')
    if logged_in:
        return (jsonify({'result': 1, 'description': str(session.get('username')) + ' already logged in.'}), 200)
    else:
        return (jsonify({'result': 0, 'description': 'No user logged in.'}), 200)


# logout相关
@app.route('/logout')
def logout():
    # 删除session中所有的值(默认更改为None）
    session.clear()
    # 返回到Home页面
    return redirect('/')


@app.route('/api/logout', methods=['POST'])
def api_logout():
    username = str(session.get('username'))
    if session.get('logged_in'):
        # 退出登陆，删除session变量值
        # session.pop('logged_in', None)
        # session.pop('username', None)
        session.clear()
        return (jsonify({'result': 1,'description': username + ' Logout successful.'}), 200)
    else:
        return (jsonify({'result': 0, 'description': 'No user logged in.'}), 200)


# 已登录用户上传app相关
@app.route('/upload', methods=['POST', 'GET'])
def upload():
    try:
        # 存储错误信息
        error = None
        # 创建app临时存储目录
        create_temp_folder(TEMP_FOLDER)
        # POST请求，即上传app
        if request.method == 'POST':

            # 获取上传的app相关信息
            app_name = secure_filename(request.form.get('app_name'))
            # 获取作者，即已登录用户的username
            app_author = str(session.get('username'))
            # 生成上传时间
            app_date = datetime.now().strftime('%Y-%m-%d')
            app_summary = str(request.form.get('app_summary'))

            # 获取文件名
            filename = str(request.form.get('filename'))

            # 获取app临时存储路径
            temp_path = os.path.join(TEMP_FOLDER, filename)

            # 最终app存储名字
            file_save_name = app_name + "." + filename.rsplit('.')[-1]
            # 最终app的存储路径，即 static/app/app_author/file_save_name
            app_path = os.path.join(os.path.join(UPLOAD_FOLDER, app_author), file_save_name)
            # 获取app_url
            app_url = HOST + "/static/app/" + app_author + '/' + file_save_name
            # app的存储路径不存在且临时存储目录存在，表示app的文件已上传到临时目录，但没有转移到用户目录下
            if not os.path.exists(app_path) and os.path.exists(temp_path):
                # 把app的文件从临时目录中剪切到用户目录下
                shutil.move(temp_path, app_path)
                # 清空临时存储目录
                del_file(TEMP_FOLDER)
                # 把app数据写入数据库
                create_app_data(app_name, app_author, app_date, app_summary, app_url, app_path)
                # 上传成功后，返回到用户app的页面
                return redirect('/myapps')
            # app的存储路径已存在，或者临时目录中不存在已上传的文件（基本不存在），表示app已存在
            else:
                error = "app exists, please upload again"

        # GET请求、app已存在，全部返回到上传页面
        return render_template('upload.html', error=error)
    except Exception as e:
        return str(e)


@app.route('/api/upload', methods=['POST'])
def api_upload():
    if session.get('logged_in'):
        pakinfo = eval(request.form.to_dict()['info'])
        pakname = pakinfo['pakname']
        pakauthor = session.get('username')
        version = pakinfo['version']
        pakdesc = pakinfo['pakdesc']
        # 变量名不能设置为os，否则会冲突
        pakos = pakinfo['os']
        # check if the post request has the file part
        if 'file' not in request.files:
            resp = jsonify({'result': 0, 'description' : 'No file part in the request'})
            resp.status_code = 400
            return resp
        file = request.files['file']
        if file.filename == '':
            resp = jsonify({'result': 0, 'description' : 'No file selected for uploading'})
            resp.status_code = 400
            return resp
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(TEMP_FOLDER, filename))
            resp = jsonify({'result': 1, 'description' : 'File successfully uploaded'})
            resp.status_code = 201
            return resp
        else:
            resp = jsonify({'result': 0, 'description' : 'Allowed file types can only be zip'})
            resp.status_code = 400
            return resp
    else:
        resp = jsonify({'result': 0, 'description' : 'Authentication failed'})
        resp.status_code = 401
        return resp

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/package/file/<int:pakid>', methods = ['GET','POST'])
def api_get_package(pakid):
    """Download a file."""
    try:
        return send_from_directory(TEMP_FOLDER, 'file_name.zip', attachment_filename= 'file_name.zip', as_attachment=True)
    except:
        abort(404)
        # resp = jsonify({'result': 0, 'description' : str(error)})
        # resp.status_code = 404
        # return resp


@app.route('/api/package/info/<int:pakid>', methods = ['GET','POST'])
def api_get_package_info(pakid):
    # app_data = get_app_data(pakid)
    # if len(app_data):
    if pakid < 10:
        resp = jsonify({'result': 0, 'description' : 'No file part in the request'})
        resp.status_code = 400
        return resp
    else:
        resp = jsonify({'result': 1, 'app_author': '', 'pakname': '', 'pakdesc': '', 'version': '', 'os': '', 'update': ''})
        resp.status_code = 200
        return resp



# 已登录用户更新app相关
# app_name：要更新app的app_name
@app.route('/update/<app_name>', methods=['POST', 'GET'])
def update_app(app_name):
    try:
        # 存储错误信息
        error = None
        # 创建app临时存储目录
        create_temp_folder(TEMP_FOLDER)
        # GET请求，查找要更新app的相关信息
        if request.method == 'GET':
            # 获取当前已登录用户的username，即app_author
            app_author = session.get('username')
            # 获取app_data
            app_data = get_app_data(app_name, app_author)
            app_summary = app_data[3]
            app_path = app_data[5]

            # 把获取的信息返回给update.html中，方便用户更新
            return render_template('update.html', app_name=app_name, app_summary=app_summary, app_old_path = app_path)

        # POST请求，用户更新app
        if request.method == 'POST':
            # 获取作者，即已登录用户的username
            app_author = str(session.get('username'))
            # 生成修改时间
            app_date = datetime.now().strftime('%Y-%m-%d')
            app_summary = str(request.form.get('app_summary'))
            # 获取app_old_path
            app_old_path = str(request.form.get('app_old_path'))
            app_old_url = HOST + "/static/app/" + app_author + '/' + app_old_path.rsplit('/')[-1]

            # 获取上传文件的文件名
            filename = str(request.form.get('filename'))
            # 文件名不为空，表示用户在更新app时上传文了件，即更新文件，需要覆盖原来的文件
            if filename != "":
                # 获取app临时存储路径
                temp_path = os.path.join(TEMP_FOLDER, filename)
                # 最终app存储名字
                file_save_name = app_name + "." + filename.rsplit('.')[-1]
                # 最终app的存储路径，即 static/app/app_author/file_save_name
                app_path = os.path.join(os.path.join(UPLOAD_FOLDER, app_author), file_save_name)
                app_url = HOST + "/static/app/" + app_author + '/' + file_save_name
                # app的存储路径存在且上传文件的临时存储路径存在，覆盖原文件
                if os.path.exists(app_old_path) and os.path.exists(temp_path):
                    # 在用户目录下删除app原本的文件
                    os.remove(app_old_path)
                    # 把更新的文件从临时目录中剪切到用户目录下
                    shutil.move(temp_path, app_path)
                    # 清空临时存储目录
                    del_file(TEMP_FOLDER)
                    # 更新app_data
                    update_app_data(app_name, app_author, app_date, app_summary, app_url, app_path)
                    # 更新成功后，返回到用户app的页面
                    return redirect('/myapps')
            # 文件名为空，用户没有上传文件，只更新app_summary，修改即可
            else:
                update_app_data(app_name, app_author, app_date, app_summary, app_old_url, app_old_path)
                # 更新成功后，返回到用户app的页面
                return redirect('/myapps')
    except Exception as e:
        return str(e)


# 已登录用户删除app相关
# app_name：要删除app的app_name
@app.route('/delete_app/<app_name>')
def delete_app(app_name):
    try:
        # 获取当前已登录用户的username，即app_author
        app_author = session.get('username')
        # 从数据库删除app_data
        delete_app_data(app_name, app_author)
        # 删除成功后，返回到用户app的页面
        return redirect('/myapps')
    except Exception as e:
        return str(e)


# --host=0.0.0.0 --port=5000    表明局域网内可以访问服务器，端口号为5000
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
