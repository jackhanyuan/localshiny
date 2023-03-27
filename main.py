from datetime import timedelta, datetime
from flask import Flask, render_template, request, session, redirect, abort, jsonify, send_from_directory
from flask_session import Session
import os
import redis
import shutil
from tus.flask_tus import tus_manager
from werkzeug.utils import secure_filename
from database import get_db, user_register, verify_password, create_package_data, update_package_data, get_pakid, get_user_pakid, get_package_data, delete_package_data, is_v1_greater_than_v2, create_temp_folder, del_file, get_token, verify_token, update_token
from localshiny import RegistrationForm, RShinyApp
from token_id_gen import generate_short_id
from xml_gen import generate_xml

# 配置参数
app = Flask(__name__)
# app.debug = True

# 最大有效负载限制为 200MB (文件上传限制200M)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

# --------------------session设置----------------------------------- #
# 密钥随机产生24位
app.config['SECRET_KEY'] = os.urandom(24)
# 密钥存活时间为7天
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=2)

# 这里session使用redis的配置，可以解决session变量值更改后不生效bug
# 指明保存到redis中
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.StrictRedis(host="127.0.0.1", port=6379)
Session(app)
# ----------------------------------------------------------------- #

# 常量参数设置
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static/package')
TEMP_FOLDER = os.path.join(os.path.dirname(__file__), 'temp')
ALLOWED_EXTENSIONS = set(['zip'])
HOST = 'https://www.localshiny.org'
LIMIT_PACKAGES_NUMBER = 10


# 存储所有app信息的字典
package_dict = {}
# 存储已登录用户的所有app信息的字典  1
my_package_dict = {}

# tus文件断点续传
# upload_url: 客户端利用TUS协议上传的URL，客户端的TUS指向这个URL
# upload_folder: 存储上传文件的临时目录
tus_manager(app, upload_url='/file-upload', upload_folder=TEMP_FOLDER)


# 初始化所有app，以及已登录用户的所有app信息
def init_apps(installed_apps):
    try:
        # 获取数据库链接，游标
        db, cur = get_db()

        # 清空原来内容
        package_dict.clear()
        my_package_dict.clear()

        # 用来给app编号，同时给前端的app设定页码
        i = 1
        # 从app表查询获取所有app的信息
        all_package = cur.execute("SELECT * FROM package").fetchall()
        for one_package in all_package:
            pakid = one_package[0]
            if pakid in installed_apps.keys():
                version = one_package[3]
                installed_version = installed_apps.get(pakid)
                if is_v1_greater_than_v2(version, installed_version):
                    pakstatus = 'upgradeable'
                else:
                    pakstatus = 'installed'
            else:
                pakstatus = 'notinstall'
            package_dict[i] = RShinyApp(one_package[0], one_package[1], one_package[2], one_package[3], one_package[4], one_package[5], one_package[6], one_package[7], one_package[8], one_package[9], one_package[10], one_package[11], one_package[12], one_package[13], one_package[14], one_package[15], pakstatus)
            i += 1

        # 编号
        i = 1
        # 从app表查询获取已登录用户所有app的信息
        all_my_package = cur.execute("SELECT * FROM package where pakauthor = ?", [session.get('username')]).fetchall()
        for one_package in all_my_package:
            pakid = one_package[0]
            if pakid in installed_apps.keys():
                version = one_package[3]
                installed_version = installed_apps.get(pakid)
                if is_v1_greater_than_v2(version, installed_version):
                    pakstatus = 'upgradeable'
                else:
                    pakstatus = 'installed'
            else:
                pakstatus = 'notinstall'
            my_package_dict[i] = RShinyApp(one_package[0], one_package[1], one_package[2], one_package[3], one_package[4], one_package[5], one_package[6], one_package[7], one_package[8], one_package[9], one_package[10], one_package[11], one_package[12], one_package[13], one_package[14], one_package[15], pakstatus)
            i += 1

        # 提交事务，关闭数据库连接，游标，并回收垃圾
        db.commit()
        cur.close()
        db.close()
        gc.collect()
    except Exception as e:
        return str(e)


def is_localshiny_request():
    ua_str = str(request.user_agent)
    if 'LocalShiny' in ua_str:
        return True
    return False


def get_installed_apps():
    ua_tag = 0
    installed_apps = {}
    if is_localshiny_request():
        # ua_str = 'LocalShiny/qy59BctD-1.0.0,ZfEKirv7-0.99,'
        ua_str = str(request.user_agent)
        ua_tag = 1
        ls = ua_str.split(' ')[-1]
        apps = ls.split('/')[-1].split(',')
        apps = list(filter(None, set(apps)))  # 去重去空
        ua_tag = 1
        for app in apps:
            pid, version = app.split('-')
            installed_apps[pid] = version

    return ua_tag, installed_apps


@app.before_request
def before_request():
    session['myspace'] = None
    if is_localshiny_request():
        session['myspace'] = True
    # print(is_localshiny_request(), session['myspace'])


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
    # 获取已安装app信息
    ua_tag, installed_apps = get_installed_apps()
    # 先初始化所有app的信息，参数传给apps.html，再渲染页面
    init_apps(installed_apps)
    return render_template('apps.html', package_dict=package_dict, host = HOST, ua_tag = ua_tag)


# 用户app页面相关
@app.route('/myapps')
def myapps():
    # 获取已安装app信息
    ua_tag, installed_apps = get_installed_apps()
    # 先初始化已登录用户所有app的信息，参数传给myapps.html，再渲染页面
    init_apps(installed_apps)
    # print(my_package_dict)
    user_token = None
    logged_in = session.get('logged_in')
    if logged_in:
        username = session.get('username')
        user_token = get_token(username)
        return render_template('myapps.html', my_package_dict=my_package_dict, host = HOST, token = user_token, ua_tag = ua_tag)
    else:
        return redirect('/login')


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
                error = "username is already taken, please choose another."

        # GET请求、username已被注册，全部返回到注册页面
        return render_template('register.html', form=form, error=error)
    except Exception as error:
        return str(error)


# @app.route('/api/register', methods=['POST'])
# def api_register():
#     try:
#         username = request.json.get('username')
#         email = request.json.get('email')
#         password = request.json.get('password')
#         if username is None or password is None or email is None:
#             return (jsonify({'result': 0, 'description': 'username & email & password can not be empty.'}), 400)
#         if user_register(username, password, email):
#             return (jsonify({'result': 1, 'description': username + ' register successful.'}), 201 )
#         else:
#             return (jsonify({'result': 0, 'description': 'existing user.'}), 200)
#     except Exception as error:
#         return (jsonify({'error': str(error)}), 400)


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
        # 已经登录
        logged_in = session.get('logged_in')
        if logged_in:
            return (jsonify({'result': 1, 'description': str(session.get('username')) + ' already logged in.'}), 200)

        # 存储错误信息
        error = None

        # 获取name和token
        name_token = request.headers.environ['HTTP_TOKEN']
        name = name_token.rsplit('-')[0]
        token = name_token.rsplit('-')[1]
        # 验证token
        tag = verify_token(name, token)
        login_tag = tag[0]
        error = tag[1]

        # token验证成功
        if login_tag == True:
            username = error
            # 通过session设置用户登录成功，并保存登录信息username
            session['logged_in'] = True
            session['username'] = username
            session.permanent = True
            return (jsonify({'result': 1, 'description': username + ' login successful.'}), 200)
        # token验证失败
        else:
            return (jsonify({'result': 0, 'description': 'login failed, ' + error }), 401)
    except Exception as error:
        return (jsonify({'error': error}), 400)


# @app.route('/api/status', methods=['POST'])
# def api_login_status():
#     logged_in = session.get('logged_in')
#     if logged_in:
#         return (jsonify({'result': 1, 'description': str(session.get('username')) + ' already logged in.'}), 200)
#     else:
#         return (jsonify({'result': 0, 'description': 'no user logged in.'}), 200)


# logout相关
@app.route('/logout')
def logout():
    # 删除session中所有的值(默认更改为None）
    session.clear()
    # session.pop('logged_in', None)
    # session.pop('username', None)
    # 返回到Home页面
    return redirect('/')


@app.route('/api/logout', methods=['POST'])
def api_logout():
    username = str(session.get('username'))
    if session.get('logged_in'):
        # 退出登陆，删除session变量值
        update_token(username)
        session.clear()
        return (jsonify({'result': 1,'description': username + ' logout successful.'}), 200)
    else:
        return (jsonify({'result': 0, 'description': 'no user logged in.'}), 200)


# 已登录用户上传app相关
@app.route('/upload', methods=['POST', 'GET'])
def upload():
    try:
        # 如果没有登陆，跳至登陆页面
        logged_in = session.get('logged_in')
        if not logged_in:
            return redirect('/login')

        # 存储错误信息
        error = None

        # POST请求，即上传app
        if request.method == 'POST':
            # 获取上传的app相关信息
            pakid = str(request.form.get('pakid'))
            pakname = secure_filename(request.form.get('pakname'))
            pakauthor = str(session.get('username')) # app作者，即已登录用户的username
            version = str(request.form.get('version'))
            pakdesc = str(request.form.get('pakdesc'))
            pakos = str(request.form.get('pakos'))
            arch = str(request.form.get('arch'))
            distribution = 'None'
            pakdate = datetime.now().strftime('%Y-%m-%d')# 生成上传时间
            upmethod = 'web'
            rversion = 'None'
            runcmd = 'None'

            count_package = len(get_user_pakid(pakauthor))
            if get_pakid(pakname, pakauthor):
                error = 'App name exists, please change it and try again.'
            elif count_package >= LIMIT_PACKAGES_NUMBER:
                error = 'You have more than {0} packages.'.format(LIMIT_PACKAGES_NUMBER)
            else:
                # 获取文件名
                temp_name = str(request.form.get('filename'))
                # 获取app临时存储路径
                temp_path = os.path.join(TEMP_FOLDER, temp_name)
                # 最终app存储名字
                file_save_name = secure_filename(pakname + '-v' +version + '-' + pakos + '-' + arch +"." + temp_name.rsplit('.')[-1])
                # 最终app的存储路径，即 static/package/pakauthor/file_save_name
                filepath = os.path.join(os.path.join(UPLOAD_FOLDER, pakauthor), file_save_name)
                # 获取fileurl
                fileurl = "/api/package/xml/" + pakid
                # app的存储路径不存在且临时存储目录存在，表示app的文件已上传到临时目录，但没有转移到用户目录下
                if not os.path.exists(filepath) and os.path.exists(temp_path):
                    # 把app的文件从临时目录中剪切到用户目录下
                    shutil.move(temp_path, filepath)
                    # 清空临时存储目录
                    del_file(TEMP_FOLDER)
                    # 把app数据写入数据库
                    create_package_data(pakid, pakname, pakauthor, version,  pakdesc, pakos, arch, distribution, pakdate, upmethod, rversion, runcmd, filepath, fileurl)
                    # 上传成功后，返回到用户app的页面
                    return redirect('/myapps')
                # app的存储路径已存在，或者临时目录中不存在已上传的文件（基本不存在），表示app已存在
                else:
                    error = "App exists, please upload again."

        # 生成当前app的id
        pakid = generate_short_id()
        # 创建app临时存储目录
        create_temp_folder(TEMP_FOLDER)
        # GET请求、app已存在，全部返回到上传页面
        return render_template('upload.html', error=error, pakid = pakid)
    except Exception as e:
        return str(e)


@app.route('/api/upload', methods=['POST'])
def api_upload():
    try:
        if session.get('logged_in'):
            pakinfo = eval(request.form.to_dict()['info'])
            pakname = pakinfo['pakname']
            pakauthor = session.get('username')
            # exist package
            if get_pakid(pakname, pakauthor):
                pakid = get_pakid(pakname, pakauthor)
                package_data = get_package_data(pakid)
                package_old_path = package_data[13]
                tag = 1
            # not exist package
            else:
                pakid = generate_short_id()
                tag = 0
            count_package = len(get_user_pakid(pakauthor))
            if count_package > LIMIT_PACKAGES_NUMBER:
                resp = jsonify({'result': 0, 'description' : 'You have more than {0} packages.'.format(LIMIT_PACKAGES_NUMBER)})
                resp.status_code = 400
                return resp
            version = pakinfo['version']
            pakdesc = pakinfo['pakdesc']
            # 变量名不能设置为os，否则会冲突
            pakos = pakinfo['os']
            arch = 'script'
            distribution = 'None'
            pakdate = datetime.now().strftime('%Y-%m-%d')# 生成上传时间
            upmethod = 'api'
            rversion = pakinfo['rversion']
            runcmd = pakinfo['runcmd']
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
                temp_name = secure_filename(file.filename)
                file_save_name = secure_filename(pakname + '-v' +version + '-' + pakos + '-' + arch +"." + temp_name.rsplit('.')[-1])
                filepath = os.path.join(os.path.join(UPLOAD_FOLDER, pakauthor), file_save_name)
                fileurl = "/api/package/xml/" + pakid

                # upload package
                if tag==0:
                    create_package_data(pakid, pakname, pakauthor, version,  pakdesc, pakos, arch, distribution, pakdate, upmethod, rversion, runcmd, filepath, fileurl)
                    file.save(filepath)
                    resp = jsonify({'result': 1, 'description' : 'File successfully uploaded.', 'pakid': pakid})
                    resp.status_code = 201
                    return resp

                # update package
                elif tag==1:
                    # 在用户目录下删除package原文件
                    os.remove(package_old_path)
                    # 存储更新的文件
                    file.save(filepath)
                    # 更新package_data
                    update_package_data(pakid, pakname, pakauthor, version,  pakdesc, pakos, arch, distribution, pakdate, upmethod, rversion, runcmd, filepath, fileurl)
                    resp = jsonify({'result': 1, 'description' : pakname + ' successfully updated.', 'pakid': pakid})
                    resp.status_code = 201
                    return resp
            else:
                resp = jsonify({'result': 0, 'description' : 'Allowed file types can only be zip.'})
                resp.status_code = 400
                return resp
        else:
            resp = jsonify({'result': 0, 'description' : 'Authentication failed.'})
            resp.status_code = 401
            return resp
    except:
        resp = jsonify({'result': 0, 'description' : 'Incorrect request format.'})
        resp.status_code = 400
        return resp


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/package/file/<pakid>', methods = ['GET','POST'])
def api_get_package(pakid):
    try:
        package_data = get_package_data(pakid)
        filepath = package_data[-3]
        filename = filepath.rsplit('/')[-1]
        folder = UPLOAD_FOLDER + '/' + package_data[2]
        return send_from_directory(folder, filename, attachment_filename= filename, as_attachment=True)
    except Exception as error:
        # abort(404)
        resp = jsonify({'result': 0, 'description': 'Package was not found'})
        resp.status_code = 404
        return resp
        # return str(error)


@app.route('/api/package/info/<pakid>', methods=['GET', 'POST', 'HEAD'])
def api_get_package_info(pakid):
    try:
        package_data = get_package_data(pakid)
        resp = jsonify({'result': 1, 'pakid': package_data[0], 'pakname': package_data[1], 'pakauthor': package_data[2], 'version': package_data[3], 'pakdesc': package_data[4], 'os': package_data[5], 'arch': package_data[6], 'pakdate': package_data[8], 'upmethod': package_data[9], 'Rversion': package_data[11]})
        resp.status_code = 200
        return resp
    except Exception as error:
        resp = jsonify({'result': 0, 'description' : 'Package was not found'})
        resp.status_code = 404
        return resp


@app.route('/api/package/xml/<pakid>', methods = ['GET','POST'])
def api_get_xml(pakid):
    try:
        package_data = get_package_data(pakid)
        pakname = package_data[1]
        pakauthor = package_data[2]
        version = package_data[3]
        pakdesc = package_data[4]
        pakos = package_data[5]
        arch = package_data[6]
        pakdate = package_data[8]
        upmethod = package_data[9]
        rversion = package_data[11]
        runcmd = package_data[12]
        filepath = package_data[-3]
        fileurl = HOST +'/api/package/file/' + pakid

        generate_xml(pakid, pakname, pakauthor, version, pakdesc, pakos, pakdate, upmethod, rversion, runcmd, fileurl)
        xmlname = pakid + '.xml'
        return send_from_directory(UPLOAD_FOLDER, 'result.xml', attachment_filename= xmlname, as_attachment=True)
    except Exception as error:
        # abort(404)
        resp = jsonify({'result': 0, 'description' : 'XML was not found'})
        resp.status_code = 404
        return resp


@app.route('/api/package/gen-xml', methods = ['POST'])
def api_gen_xml():
    try:
        pakinfo = eval(request.form.to_dict()['info'])
        pakname = pakinfo['pakname']
        pakauthor = pakinfo['authorname']
        version = pakinfo['version']
        pakdesc = pakinfo['pakdesc']
        pakos = pakinfo['os']
        arch = 'script'
        distribution = 'None'
        pakdate = datetime.now().strftime('%Y-%m-%d')
        upmethod = 'api'
        rversion = pakinfo['rversion']
        runcmd = pakinfo['runcmd']
        pakid = generate_short_id()
        fileurl = ''
        generate_xml(pakid, pakname, pakauthor, version, pakdesc, pakos, pakdate, upmethod, rversion, runcmd, fileurl)
        xmlname = pakid + '.xml'
        return send_from_directory(UPLOAD_FOLDER, 'result.xml', attachment_filename= xmlname, as_attachment=True)
    except Exception as error:
        # abort(404)
        resp = jsonify({'result': 0, 'description' : 'error'})
        resp.status_code = 404
        return resp


# 已登录用户更新app相关
# pakname：要更新app的pakname
@app.route('/update/<pakid>', methods=['POST', 'GET'])
def update_package(pakid):
    try:
        # 获取package_data
        package_data = get_package_data(pakid)
        pakauthor = package_data[2]

        # 如果app对应的用户没有登陆，跳至登陆页面
        logged_in_username = session.get('username')
        if logged_in_username != pakauthor:
            return redirect('/login')

        # 存储错误信息
        error = None
        # 创建app临时存储目录
        create_temp_folder(TEMP_FOLDER)
        # GET请求，查找要更新app的相关信息
        if request.method == 'GET':
            # 把获取的信息返回给update.html中，方便用户更新
            return render_template('update.html', pakid = package_data[0], pakname = package_data[1], pakauthor =package_data[2] , version = package_data[3], pakdesc=package_data[4], pakos = package_data[5], arch = package_data[6], rversion = package_data[11], runcmd = package_data[12])

        # POST请求，用户更新app
        if request.method == 'POST':
            # 获取更新后的app相关信息
            pakname = str(request.form.get('pakname'))
            pakauthor = str(session.get('username')) # app作者，即已登录用户的username
            version = str(request.form.get('version'))
            pakdesc = str(request.form.get('pakdesc'))
            # pakos = str(request.form.get('pakos'))
            # arch = str(request.form.get('arch'))
            pakos = package_data[5]
            arch = 'script'
            distribution = package_data[7]
            pakdate = datetime.now().strftime('%Y-%m-%d')# 生成上传时间
            upmethod = package_data[9]
            # rversion = package_data[11]
            # runcmd = package_data[12]
            rversion = str(request.form.get('rversion'))
            runcmd = str(request.form.get('runcmd'))
            package_old_path = package_data[13]
            fileurl = package_data[14]

            # 获取文件名
            temp_name = str(request.form.get('filename'))

            # 文件名不为空，表示用户在更新app时上传文了件，即更新文件，需要覆盖原来的文件
            if temp_name != "":
                # 获取app临时存储路径
                temp_path = os.path.join(TEMP_FOLDER, temp_name)
                # 最终app存储名字
                file_save_name = secure_filename(pakname + '-v' +version + '-' + pakos + '-' + arch +"." + temp_name.rsplit('.')[-1])
                # 最终app的存储路径，即 static/package/pakauthor/file_save_name
                filepath = os.path.join(os.path.join(UPLOAD_FOLDER, pakauthor), file_save_name)

                # app的存储路径存在且上传文件的临时存储路径存在，覆盖原文件
                if os.path.exists(package_old_path) and os.path.exists(temp_path):
                    # 在用户目录下删除app原本的文件
                    os.remove(package_old_path)
                    # 把更新的文件从临时目录中剪切到用户目录下
                    shutil.move(temp_path, filepath)
                    # 清空临时存储目录
                    del_file(TEMP_FOLDER)
            # 文件名为空，用户没有上传文件，更新package信息
            else:
                # 最终app存储名字
                file_save_name = secure_filename(pakname + '-v' +version + '-' + pakos + '-' + arch +"." + package_old_path.rsplit('.')[-1])
                filepath = os.path.join(os.path.join(UPLOAD_FOLDER, pakauthor), file_save_name)
                # 更新package存储路径
                shutil.move(package_old_path, filepath)

            # 更新package_data
            update_package_data(pakid, pakname, pakauthor, version,  pakdesc, pakos, arch, distribution, pakdate, upmethod, rversion, runcmd, filepath, fileurl)
            # 更新成功后，返回到用户app的页面
            return redirect('/myapps')
    except Exception as e:
        return str(e)


@app.route('/api/update/<pakid>', methods=['POST'])
def api_update(pakid):
    try:
        if session.get('logged_in'):
            # 获取package_data
            package_data = get_package_data(pakid)
            pakauthor = package_data[2]
            package_old_path = package_data[13]
            fileurl = package_data[14]

            # 如果package对应的用户与当前登陆用户不一致
            logged_in_username = session.get('username')
            if logged_in_username != pakauthor:
                resp = jsonify({'result': 0, 'description' : 'Authentication failed, you are forbidden to modify this package.'})
                resp.status_code = 401
                return resp
            else:
                pakinfo = eval(request.form.to_dict()['info'])
                pakname = pakinfo['pakname']
                pakauthor = session.get('username')
                version = pakinfo['version']
                pakdesc = pakinfo['pakdesc']
                # 变量名不能设置为os，否则会冲突
                pakos = pakinfo['os']
                arch = 'script'
                distribution = 'None'
                pakdate = datetime.now().strftime('%Y-%m-%d')# 生成上传时间
                upmethod = 'api'
                rversion = pakinfo['rversion']
                runcmd = pakinfo['runcmd']

                # check if the post request has the file part
                if 'file' not in request.files:
                    # 最终app存储名字
                    file_save_name = secure_filename(pakname + '-v' +version + '-' + pakos + '-' + arch +"." + package_old_path.rsplit('.')[-1])
                    filepath = os.path.join(os.path.join(UPLOAD_FOLDER, pakauthor), file_save_name)
                    # 更新package存储路径
                    shutil.move(package_old_path, filepath)
                    # 更新package_data
                    update_package_data(pakid, pakname, pakauthor, version,  pakdesc, pakos, arch, distribution, pakdate, upmethod, rversion, runcmd, filepath, fileurl)
                    resp = jsonify({'result': 1, 'description' : pakname + ' successfully updated.', 'pakid': pakid})
                    resp.status_code = 201
                    return resp

                file = request.files['file']
                if file.filename == '':
                    resp = jsonify({'result': 0, 'description' : 'no file selected for uploading'})
                    resp.status_code = 400
                    return resp
                if file and allowed_file(file.filename):
                    temp_name = secure_filename(file.filename)
                    file_save_name = secure_filename(pakname + '-v' +version + '-' + pakos + '-' + arch +"." + temp_name.rsplit('.')[-1])
                    filepath = os.path.join(os.path.join(UPLOAD_FOLDER, pakauthor), file_save_name)

                    # 在用户目录下删除package原文件
                    os.remove(package_old_path)
                    # 存储更新的文件
                    file.save(filepath)
                    # 更新package_data
                    update_package_data(pakid, pakname, pakauthor, version,  pakdesc, pakos, arch, distribution, pakdate, upmethod, rversion, runcmd, filepath, fileurl)
                    resp = jsonify({'result': 1, 'description' : pakname + ' successfully updated.', 'pakid': pakid})
                    resp.status_code = 201

                    return resp
                else:
                    resp = jsonify({'result': 0, 'description' : 'Allowed file types can only be zip.'})
                    resp.status_code = 400
                    return resp
        else:
            resp = jsonify({'result': 0, 'description' : 'Authentication failed.'})
            resp.status_code = 401
            return resp
    except:
        resp = jsonify({'result': 0, 'description' : 'Incorrect request format or Package was not found.'})
        resp.status_code = 400
        return resp


# 已登录用户删除app相关
# pakname：要删除app的pakname
@app.route('/delete/<pakid>')
def delete_package(pakid):
    try:
        # 获取package_data
        package_data = get_package_data(pakid)
        pakauthor = package_data[2]
        logged_in_username = session.get('username')

        # 如果app对应的用户和当前登陆用户一致则执行删除操作
        if logged_in_username == pakauthor:
            # 从数据库删除package_data
            delete_package_data(pakid)
        return redirect('/myapps')
    except Exception as e:
        return str(e)


# @app.route('/api/delete/<pakid>', methods=['POST'])
# def api_delete(pakid):
#     try:
#         if session.get('logged_in'):
#             # 获取package_data
#             package_data = get_package_data(pakid)
#             pakname = package_data[1]
#             pakauthor = package_data[2]
#             logged_in_username = session.get('username')
#
#             # 如果app对应的用户和当前登陆用户一致则执行删除操作
#             if logged_in_username == pakauthor:
#                 # 从数据库删除package_data
#                 delete_package_data(pakid)
#                 resp = jsonify({'result': 1, 'description' : pakname + ' successfully deleted.', 'pakid': pakid})
#                 resp.status_code = 201
#             else:
#                 resp = jsonify({'result': 0, 'description' : 'Authentication failed, you are forbidden to delete this package.'})
#                 resp.status_code = 401
#             return resp
#         # 用户未登录
#         else:
#             resp = jsonify({'result': 0, 'description' : 'Authentication failed.'})
#             resp.status_code = 401
#             return resp
#     except Exception as error:
#         # abort(404)
#         resp = jsonify({'result': 0, 'description' : 'Package was not found.'})
#         resp.status_code = 404
#         return resp


@app.route('/api/delete/<pakname>', methods=['POST'])
def api_delete_by_pakname(pakname):
    try:
        if session.get('logged_in'):
            # 获取package_data
            logged_in_username = session.get('username')
            pakid = get_pakid(pakname, logged_in_username)
            if pakid:
                delete_package_data(pakid)
                resp = jsonify({'result': 1, 'description' : pakname + ' successfully deleted.', 'pakid': pakid})
                resp.status_code = 201
            else:
                resp = jsonify({'result': 0, 'description' : 'Package was not found.'})
                resp.status_code = 404
            return resp
        # 用户未登录
        else:
            resp = jsonify({'result': 0, 'description' : 'Authentication failed.'})
            resp.status_code = 401
            return resp
    except Exception as error:
        # abort(404)
        resp = jsonify({'result': 0, 'description' : error})
        resp.status_code = 404
        return resp


# --host=0.0.0.0 --port=5000    表明局域网内可以访问服务器，端口号为5000
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
