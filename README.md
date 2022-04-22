# LocalShiny Web

**[LocalShiny Web](https://www.localshiny.org/)** is a platform for developers to share [Shiny applications](https://shiny.rstudio.com/gallery/) built in R. 
With the LocalShiny package, developers create clones of applications and share the applications in the LocalShiny Web easily.

## About LocalShiny

[LocalShiny Website](https://www.localshiny.org/)

[LocalShiny Documentation](https://localshiny.github.io/)

[LocalShiny Github](https://github.com/localshiny)


## Required Environments

- OS: Linux server (>= 18.04)
- Python3 (>= 3.6)

## Deploy LocalShiny Web

### Install Dependencies

Create working directory `localshiny.org` and change permissions, then enter `localshiny.org`.

```shell script
sudo mkdir -p /var/www/localshiny.org 
sudo chown -R $USER:$USER /var/www/localshiny.org 
sudo chmod -R 755 /var/www/localshiny.org
cd /var/www/localshiny.org
```

Clone the [`WebServe`](https://github.com/localshiny/WebServer) repository then change name to `LocalShinyWeb`.

```shell script
git clone git@github.com:localshiny/WebServer.git
mv WebServer LocalShinyWeb
```

Install `virtualenv` and set environment variables.

```shell script
pip install virtualenv
pip install virtualenvwrapper
sudo vim ~/.bashrc
```

> Add the following three lines in `~/.bashrc`.
```
VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
export WORKON_HOME=$HOME/.virtualenvs
source ~/.local/bin/virtualenvwrapper.sh
```

```shell script
:wq    
source ~/.bashrc
```

Create and enter `localshiny virtual environment`.

```shell script
mkvirtualenv -p python3 localshiny
workon localshiny
```

Install `Redis` and start redis service.

```shell script
sudo apt update
sudo apt install redis-server
sudo service redis restart
redis-cli
```

Install other Python packages.

> LocalShiny Web requires the following python packages.
```
email-validator==1.1.2
Flask==1.1.2
Flask-Session==0.3.2
passlib==1.7.4
redis==3.5.3
Werkzeug==1.0.1
WTForms==2.3.3
uwsgi==2.0.18
```

> Use the command `pip install -r requirements.txt` to install them.

[Install Nginx](http://nginx.org/en/linux_packages.html)

```shell script
sudo apt update
sudo apt install nginx
```

### Nginx configuration

Copy the SSL certificate to the Nginx directory.

```shell script
cp -r cert /etc/nginx/cert
```

Copy nginx.conf to the Nginx directory.

```shell script
cp nginx.conf /etc/nginx/
```

### Firewall settings

```shell script
sudo ufw app list
sudo ufw allow 'Nginx Full' # allow 80 and 443 port
```

### Start LocalShiny Web

Start uwsgi

```shell script
uwsgi --ini uwsgi.ini
```

Start Nginx service

```shell script
sudo service nginx restart
```

Now, you can visit `www.localshiny.org` in your browser.

## Appendix

### About Directory

- LocalShinyWeb directory: `/var/www/localshiny.org/LocalShinyWeb`
- SSL file: `LocalShinyWeb/cert`
- logs: `LocalShinyWeb/logs`
- uwsgi configuration file: `LocalShinyWeb/uwsgi.ini`
- Nginx configuration file: `/etc/nginx`

### About uwsgi

```shell script
cd /var/www/localshiny.org/LocalShinyWeb/
uwsgi --ini uwsgi.ini # start uwsgi 
uwsgi --reload uwsgi.pid # reload uwsgi.ini
uwsgi --stop uwsgi.pid # stop uwsgi
sudo pkill -f uwsgi -9 # force kill uwsgi
```

### About Nginx

```shell script
sudo nginx -t # check nginx.conf syntax errors
sudo nginx # start nginx
sudo nginx -s reload # reload nginx.conf
```

### About Nginx service

```shell script
sudo service nginx start # start nginx service 
sudo service nginx status # check nginx service status
sudo service nginx stop # stop nginx service
sudo service nginx restart # restart nginx service
```

---