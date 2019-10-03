#!/bin/sh
echo "\?        # help"
echo "\l        # show available dbs"
printf "\c hct    # connect to hct database\n"
echo "\dt       # show tables"
echo "\du       # show users and roles"
echo "SELECT * FROM hct_user;"
echo ""

sudo psql --username=gfbob --dbname=gf
