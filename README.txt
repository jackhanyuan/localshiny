使用说明：

1、使用annconda的python环境
	自行配置即可


2、安装库
	Package          	Version
	---------------- 	-------
	cachelib         	0.1.1
	click            	7.1.2
	Flask            	1.1.2
	flask-blueprint  	1.3.0
	Flask-Script     	2.0.6
	Flask-Session   	0.3.2
	Flask-SQLAlchemy 	2.4.4
	Flask-Tus        	0.7.1
	itsdangerous     	1.1.0
	Jinja2           	2.11.2
	MarkupSafe       	1.1.1
	passlib          	1.7.2
	pip              	20.2.3
	redis            	3.5.3
	setuptools       	49.2.0
	SQLAlchemy       	1.3.18
	Werkzeug         	1.0.1
	WTForms          	2.3.1
	pip install email_validator


3、sqlite3数据库配置
	python环境默认安装sqlite3的库
	打开项目路径下的 sqlite3 目录，把 sqlite3.def、sqlite.dll拷贝到annconda的dlls目录下


4、redis数据库配置
	1、运行项目前，在项目路径下的 redis 目录下打开命令行，运行 redis-server 命令，启动redis数据库
	
	2、再打开一个命令行，运行redis-cli -h 127.0.0.1 -p 6379，然后输入flushall，刷新整个数据库，完成初始化


5、启动项目服务器
	在项目路径下运行 python app.py 命令，启动服务器