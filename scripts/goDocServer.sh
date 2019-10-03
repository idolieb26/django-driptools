#!/bin/sh
if [ "$VIRTUAL_ENV" != "$GF_VIRTUAL_ENV" ]
then
    printf "NOT running inside 'gf' virtualenv\nRun: 'workon gf'\n\n"
    exit
fi
echo "To view documentation: localhost:8003/setup.html\n"
cd $GF_ROOT/docs
sphinx-autobuild . _build_html  -p 8003
