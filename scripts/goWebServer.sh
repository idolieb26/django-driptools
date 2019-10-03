#!/bin/sh
if [ "$VIRTUAL_ENV" != "$GF_VIRTUAL_ENV" ]
then
    printf "NOT running inside 'gf' virtualenv\nRun: 'workon gf'\n\n"
    exit
fi
echo "Browse to: localhost:8000 or <ip address>:8000 on other systems\n"
cd $GF_ROOT
./manage.py runserver 0:8000
#./manage.py runserver 0:8080 --noreload
