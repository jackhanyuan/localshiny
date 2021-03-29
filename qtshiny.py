from wtforms import Form, StringField, PasswordField, BooleanField, validators


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
    def __init__(self, pakid, pakname, pakauthor, version,  pakdesc, pakos, arch, distribution, pakdate, upmethod, title, rversion, runcmd, filepath, fileurl, paktag):
        self.pakid = pakid
        self.pakname = pakname
        self.pakauthor = pakauthor
        self.version = version
        self.pakdesc = pakdesc
        self.pakos = pakos
        self.arch = arch
        self.distribution = distribution
        self.pakdate = pakdate
        self.upmethod = upmethod
        self.title = title
        self.rversion = rversion
        self.runcmd = runcmd
        self.filepath = filepath
        self.fileurl = fileurl
        self.paktag = paktag

