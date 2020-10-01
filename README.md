CryptoCollector
=========

CryptoCollector is cryptocurrency web wallet, supporting Bitcoin and a large number of Altcoins.
It runs on a server, and is controlled from a web browser.
Written in python, using the django web framework.

Currencies supported
====================

* Bitcoin
* Litecoin
* Dogecoin
* Vertcoin
* Peercoin
* Next
* Feathercoin
* Darkcoin
* Reddcoin
* Myriadcoin

More to come in the future.


Installation
============

Make sure python 2.7 is installed. Make sure Pip is installed.

Open up the console. Enter the following commands:

    git clone https://github.com/priestc/CryptoCollector.git
    cd CryptoCollector
    pip install -r requirements.txt
    python manage.py syncdb
    python runserver

Point Firefox or Chrome to http://localhost:8000

From there, the default account is username: `banker`, password: `123456`.
