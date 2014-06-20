CoinStove
=========

cryptocurrency web wallet
runs on a server, controlled from a browser.
written in python, using the django web framework.

Installation
============

Open up the console. Enter the following commands:

    git clone https://github.com/priestc/CoinStove.git
    cd CoinStove
    pip install -r requirements.txt
    python manage.py syncdb
    python runserver

Point Firefox or Chrome to http://localhost:8000

From there, the default account is username: `banker`, password: `123456`.
