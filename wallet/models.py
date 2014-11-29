import calendar
import json
import datetime
from collections import OrderedDict

import requests
import arrow
from django.db import models
from django.core.cache import cache
from django.conf import settings

from coinkit import (BitcoinKeypair, PeercoinKeypair, LitecoinKeypair,
    DogecoinKeypair,FeathercoinKeypair)

from moneywagon import CurrentPrice, HistoricalPrice
from utils import fetch_url

class KeyPair(models.Model):
    """
    Base methods for all types of cryptocurrency wallets
    """
    crypto = models.CharField(max_length=6)
    owner = models.ForeignKey('auth.User')
    date_created = models.DateTimeField(default=datetime.datetime.now)
    nickname = models.TextField(max_length=64, blank=True)
    public_key = models.TextField()
    private_key = models.TextField(null=True, blank=True)
    private_key_type = models.TextField()

    def __unicode__(self):
        return "%s - %s (%s)" % (self.owner.username, self.public_key, self.private_key_type)


class Transaction(object):
    """
    Like a model class, but not a django model because transactions are
    always sourced from external data sources (never in local db). All
    cryptocurrencies will use this class for displaying/dealing wth transactions.
    """
    crypto_symbol = '' #  btc, ltc, doge, etc.
    cardinal = 0 # first, second, third transaction for an address... expressed as int
    txid = '' # long hash that this tx is indexed by in the blockchain
    amount = 0.0 # positive float for recieved transaction, negative for send
    other_address = '' # either the sender or the recipient's public key/address
    confirmations = ''
    date = '' # date of transaction (a datetime instance)

    def historical_price(self, fiat, getter=None):
        """
        Using the local cache, get the fiat price at the time of
        transaction.
        """
        if not getter:
            getter = HistoricalCryptoPrice(useragent='CoinStove 1.0')
        return getter.get_historical(fiat=fiat, crypto=self.crypto)


class BitcoinWallet(CryptoWallet):
    symbol = 'BTC'
    full_name = 'Bitcoin'
    tx_external_link_template = "http://blockchain.info/tx/{0}"

    @classmethod
    def generate_new_keypair(cls):
        keypair = BitcoinKeypair()
        return keypair.address(), keypair.private_key()

    def send_to_address(self, address, amount):
        """
        Make call to bitcoind through rpc.
        """
        raise NotImplementedError()


class LitecoinWallet(CryptoWallet):
    symbol = "LTC"
    full_name = 'Litecoin'
    tx_external_link_template = "http://explorer.litecoin.net/tx/{0}"


    def send_to_address(self, address, amount):
        raise NotImplementedError()

    @classmethod
    def generate_new_keypair(cls):
        keypair = LitecoinKeypair()
        return keypair.address(), keypair.private_key()

class DogecoinWallet(CryptoWallet):
    symbol = "DOGE"
    full_name = 'Dogecoin'
    tx_external_link_template = 'http://dogechain.info/tx/{0}'

    def send_to_address(self, address, amount):
        raise NotImplementedError()

    @classmethod
    def generate_new_keypair(cls):
        keypair = DogecoinKeypair()
        return keypair.address(), keypair.private_key()


class PeercoinWallet(CryptoWallet):
    symbol = "PPC"
    full_name = 'Peercoin'
    tx_external_link_template = "http://bkchain.org/ppc/tx/{0}"

    def send_to_address(self, address, amount):
        raise NotImplementedError()

    @classmethod
    def generate_new_keypair(cls):
        keypair = PeercoinKeypair()
        return keypair.address(), keypair.private_key()


class FeathercoinWallet(CryptoWallet):
    symbol = 'FTC'
    full_name = 'Feathercoin'
    tx_external_link_template = "http://explorer.feathercoin.com/tx/{0}"

    @classmethod
    def generate_new_keypair(cls):
        keypair = FeathercoinKeypair()
        return keypair.address(), keypair.private_key()


class VertcoinWallet(CryptoWallet):
    symbol = 'VTC'
    full_name = 'Vertcoin'
    tx_external_link_template = "http://explorer.obi.vg/tx/{0}"


class NextWallet(CryptoWallet):
    symbol = 'NXT'
    full_name = 'Next'
    tx_external_link_template = "http://nxtexplorer.com/nxt/nxt.cgi?action=2000&tra={0}"

    

    def get_transactions(self):
        raise NotImplementedError()
        url = 'http://nxtportal.org/transactions/account/%s?num=50' % self.public_key
        response = fetch_url(url)
        import debug
        txs = response.json()

        transactions = []
        for tx in txs:
            t = Transaction()
            t.date = arrow.get(tx['time_utc']).datetime
            t.amount = tx['amount']
            t.crypto_symbol = 'ppc'
            t.txid = tx['tx']
            t.confirmations = tx['confirmations']
            transactions.append(t)
        return transactions

class DarkcoinWallet(CryptoWallet):
    symbol = 'DRK'
    full_name = 'Darkcoin'
    tx_external_link_template = "{0}"
    address = 'XrbZsLp9QDSf8usYYMPhmKWA8u1kQ26rQJ'

    def get_value(self, **k):
        url ="http://chainz.cryptoid.info/drk/api.dws?q=getbalance&a=%s" % self.address
        return float(fetch_url(url).content)


class ReddcoinWallet(CryptoWallet):
    symbol = 'RDD'
    full_name = 'Reddcoin'
    tx_external_link_template = "{0}"
    addres = 'RbHsU84Eo5tUBj7HDNEb9ZSw2fFhU1NKgD'

    def get_value(self, **k):
        return 1000000


class MyriadcoinWallet(CryptoWallet):
    symbol = 'MYR'
    full_name = 'Myriadcoin'
    tx_external_link_template = "{0}"
    address = 'MHEipvGqerT3XDp2hq62xtnCujS4qL67DZ'

    def get_value(self, **kwargs):
        return 100000

wallet_classes = OrderedDict((
    ('btc', BitcoinWallet),
    ('ltc', LitecoinWallet),
    ('doge', DogecoinWallet),
    ('ppc', PeercoinWallet),
    ('drk', DarkcoinWallet),
    ('rdd', ReddcoinWallet),
    ('vtc', VertcoinWallet),
    ('myr', MyriadcoinWallet),
    ('ftc', FeathercoinWallet),
    ('nxt', NextWallet),
))

# class SavedRecipientAddress(models.Model):
#     """
#     Represents an address the user has send money to and wants that address
#     to stick around because they may send to it again.
#     """
#     owner = models.ForeignKey('auth.User')
#     crypto_symbol = models.CharField(max_length=8)
#     name = models.TextField()
#     address = models.CharField(max_length=64)
