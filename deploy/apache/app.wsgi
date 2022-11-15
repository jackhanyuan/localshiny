# 激活python虚拟环境
activate_this = '/home/centos/.virtualenvs/localshiny/bin/activate_this.py'
with open(activate_this) as file_:
	exec(file_.read(), dict(__file__=activate_this))
 
import sys
sys.path.insert(0, '/var/www/localshiny.org/LocalShinyWeb')
from main import app as application