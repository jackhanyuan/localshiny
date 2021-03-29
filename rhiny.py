from wtforms import Form, StringField, PasswordField, BooleanField, validators
import os
import shutil


# 定义注册表单form，使用flask-WTF表单系统
class RegistrationForm(Form):
    # username，文本类型，必填项，最少4位，最多20位, 匹配单词字符(单词 数字 下划线)
    username = StringField(u'Username', [validators.DataRequired(),
                                         validators.Length(min=4, max=20, message=u"Username can only be 4-20 characters."),
                                         validators.Regexp('^[\w]+$', message="Username can only contain words, numbers, underscores.")])
    # email，文本类型，必填项，最少6位，最多35位
    email = StringField(u'Email', validators=[validators.DataRequired(message=u'Email can not be empty'),
                                              validators.Length(6, 35),
                                              validators.Email(message=u'Please enter a valid email address, such as: username@domain.com')])
    # password，密码类型，必填项
    password = PasswordField(u'Password', [validators.DataRequired(message=u'Password can not be empty.')])
    # confirm password，密码类型，必填项，必须与password值相同，负责返回错误消息message
    confirm = PasswordField(u'Repeat Password',
                            [validators.DataRequired(), validators.EqualTo('password', message='Password must match.')])
    # I accept it，布尔类型，必填项，✔后值为True
    accept_tos = BooleanField(u"I accept the site rules", [validators.DataRequired()])


# 定义app类，每个对象对应app表中的一个记录
class RShinyApp:
    def __init__(self, app_name, app_author, app_date, app_summary, app_url, app_path):
        self.app_name = app_name
        self.app_author = app_author
        self.app_date = app_date
        self.app_summary = app_summary
        self.app_url = app_url
        self.app_path = app_path


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
