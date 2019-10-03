#!/bin/sh
echo "
Production Server
Commands to consider:

$ cd /opt/glassfrogg       
$ ./manage collectstatic   <-- put all static files into /static

# gunicorn is running
$ sudo systemctl status gunicorn  <-- serves django project to nginx from <project>/gf/wsgi.py
$ sudo journalctl -u gunicorn.service  <-- shows errors

# nginx is running
$ sudo systemctl status nginx     <-- communicates with gunicorn via <project>/gf.sock
$ tail -f /var/log/nginx/error.log   <-- shows error

# make sure DJANGO_DEV_ENVIRONMENT is NOT set!
$ echo \$DJANGO_DEV_ENVIRONMENT

"
