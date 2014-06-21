CoinStove
=========

cryptocurrency web wallet
runs on a server, controlled from a browser.
written in python, using the django web framework.

Currencies supported
====================

* Bitcoin
* Litecoin
* Dogecoin
* Vertcoin
* Peercoin
* Next
* Feathercoin

More to come in the future.

Abilities
=========

CoinStove is still very young. At this time, you can...

* Watch the *TC/USD value of an existing address, (i.e. 'watch only addresses')
* Watch the current exchange rate of each supported currency
* Generate a QRcode for an address or a private key.
* List all transactions for Bitcoin, Peercoin, and Litecoin wallets.

Installation
============

Make sure python 2.7 is installed. Make sure Pip is installed.

Open up the console. Enter the following commands:

    git clone https://github.com/priestc/CoinStove.git
    cd CoinStove
    pip install -r requirements.txt
    python manage.py syncdb
    python runserver

Point Firefox or Chrome to http://localhost:8000

From there, the default account is username: `banker`, password: `123456`.

Adding new currencies
=====================

Simply make a new github issue asking for that currency. To speed up the process,
include a json data source for the following:

* Current Price - Preferably for the largest/most legitimate exchange that trades that currency.
* Transactions - Given a public key (address), return all transactions.
* Wallet Amount - Given a public key (address), return the current amount.

Also helpful:
* Python library for generating new keypairs for that currency (or add to coinkit)
* Data source for historical price (for instance geting the price for a given past date)
*
