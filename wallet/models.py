import calendar
import json
import datetime
from functools import wraps
from collections import OrderedDict

import requests
import arrow
from django.db import models
from django.core.cache import cache
from django.conf import settings

from coinkit import (BitcoinKeypair, PeercoinKeypair, LitecoinKeypair,
    DogecoinKeypair,FeathercoinKeypair)

def fetch_url(*args, **kwargs):
    """
    Wrapper for requests.get with app specific headers
    """
    headers = kwargs.pop('headers', None)
    custom = {'User-Agent': "CoinStove 0.8"}
    if headers:
        headers.update(custom)
        kwargs['headers'] = headers
    else:
        kwargs['headers'] = custom

    print "making external request..."
    ret = requests.get(*args, **kwargs)
    print "...done"
    return ret

def bypassable_cache(func):
    """
    Cache decorator that caches the output of the function, but allows for the
    ability to bypass the cache by pasing in the 'bypass_cache' kwarg to be true.
    Also you can pass in 'hard_refresh' that will never read from cache, but
    will write it's output to cache.
    """
    @wraps(func)
    def lil_wayne(*args, **kwargs):
        hard_refresh = kwargs.pop('hard_refresh', False)
        bypass_cache = kwargs.pop('bypass_cache', False)

        key = '%s%s%s' % (func.__name__, str(args), str(kwargs))
        key = key.replace(' ', '') # to avoid bug in memcached

        if bypass_cache:
            print "bypass", key
            return func(*args, **kwargs)

        if hard_refresh:
            ret = func(*args, **kwargs)
            cache.set(key, ret)
            print "hard refresh", key
            return ret

        hit = cache.get(key)
        if hit is not None:
            print "return hit", key
            return hit

        print "hitting because of a miss", key
        ret = func(*args, **kwargs)
        cache.set(key, ret)
        return ret
    return lil_wayne

class CryptoWallet(models.Model):
    """
    Base methods for all types of cryptocurrency wallets
    """
    owner = models.ForeignKey('auth.User')
    date_created = models.DateTimeField(default=datetime.datetime.now)
    name = models.TextField(max_length=64, blank=True)
    public_key = models.TextField()
    private_key = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return "%s - %s" % (self.owner.username, self.public_key)

    def has_private_key(self):
        return bool(self.private_key)

    def price_json(self, hard_refresh=False):
        """
        Return a json encoded dict of price info. This data format is used for
        various things on the front end.
        """
        try:
            value = self.get_value(hard_refresh=hard_refresh)
        except:
            raise Exception("Can't get address value: %s" % self.symbol)

        return json.dumps({
            'wallet_value': value,
            'crypto_symbol': self.symbol.upper(),
            'price_source': self.price_source,
        })

    @classmethod
    def exchange_rate_json(cls, fiat_symbol='usd', hard_refresh=False):
        """
        Returns a json encoded string that describes the currency's exchange rate.
        A class method because it doesn't need any private keys.
        """
        if cls.symbol.lower() == fiat_symbol.lower():
            exchange = 1.0
        else:
            exchange = cls.get_fiat_exchange(fiat_symbol, hard_refresh=hard_refresh)

        return json.dumps({
            'fiat_symbol': fiat_symbol.upper(),
            'crypto_symbol': cls.symbol.upper(),
            'exchange_rate': exchange,
            'price_source': cls.price_source
        })

    def js_id(self):
        """
        This is how the front end (javascript) identifies wallets.
        """
        return "%s-%s" % (self.symbol.lower(), self.pk)

    def get_fiat_value(self, fiat='usd'):
        """
        Multiply a crypto amunt by the returned number to get the value of that
        crypto amount in local currency. For instance a bitcoin wallet with
        2.3 bitcoins can be converted to USD by:
        >>> btc = BitcoinWallet()
        >>> fiat_conversion = btc.get_fiat_value('usd')
        >>> 2.3 * fiat_conversion
        1894.4 # 2.3 bitcoins == 1894.4 USD
        """
        try:
            val = self.get_value()
        except Exception as exc:
            raise Exception("ACK")
            exc.message = "Failed to get address value rate for %s" % self.private_key
            raise exc

        try:
            exchange = self.get_fiat_exchange(fiat)
        except Exception as exc:
            raise Exception("ACK")
            exc.message = "Failed to get exchange rate for %s/%s" % (fiat, self.symbol)
            raise exc

        return val * exchange

    def get_value(self):
        """
        Get the total amount of currency units that this wallet holds.
        Get from the blockchain. Either through an external service or
        through a locally running *coind
        """
        raise NotImplementedError()

    def send_to_address(self, address, amount):
        """
        Create a transaction of passed in amount to passed in address and send
        off to the coin network. Done either through an external service
        or through locally ran *coind.
        """
        raise NotImplementedError()

    def get_transactions(self):
        """
        Make a call to an external service and get all transactions for this
        address.
        """
        raise NotImplementedError("No external source defined for listing %s transactions" % self.symbol)

    @classmethod
    def get_historical_price(self, date, fiat_symbol='usd'):
        url = "http://%s/price_for_date?fiat=%s&crypto=%s&date=%s"
        url = url % (settings.HISTORICAL_DOMAIN, fiat_symbol, self.symbol, date.isoformat())
        response = fetch_url(url)
        print url, response.content
        ret = response.json()
        return [ret[0], ret[1], arrow.get(ret[2]).datetime]

    @classmethod
    @bypassable_cache
    def get_fiat_exchange(cls, fiat_symbol='usd'):
        url="http://www.cryptocoincharts.info/v2/api/tradingPair/%s_%s" % (
            cls.symbol, fiat_symbol
        )
        response = fetch_url(url).json()
        return float(response['price'])

    @classmethod
    def generate_new_keypair(cls):
        raise NotImplementedError()

    class Meta:
        abstract = True


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

    def historical_price(self, fiat_symbol):
        """
        Using the local cache, get the fiat price at the time of
        transaction.
        """
        @bypassable_cache
        def _historical_price(crypto_symbol, fiat_symbol, date):
            """
            Written as a decorated inner function because the other function's
            __repr__ messes up the decorator's automatic cache key generation. Here
            the three arguments are straightforward and make a great cache key.
            """
            Wallet = wallet_classes[crypto_symbol]
            return Wallet.get_historical_price(date, fiat_symbol=fiat_symbol)

        flattened_date = self.date.replace(minute=0, second=0, microsecond=0)
        return _historical_price(self.crypto_symbol, fiat_symbol, flattened_date)

class BitcoinWallet(CryptoWallet):
    symbol = 'BTC'
    full_name = 'Bitcoin'
    price_source = 'coinbase.com'
    tx_external_link_template = "http://blockchain.info/tx/{0}"

    @bypassable_cache
    def get_value(self):
        url = "http://blockchain.info/address/%s?format=json"
        response = fetch_url(url % self.public_key)
        return float(response.json()['final_balance']) * 1e-8

    @classmethod
    def generate_new_keypair(cls):
        keypair = BitcoinKeypair()
        return keypair.address(), keypair.private_key()

    def send_to_address(self, address, amount):
        """
        Make call to bitcoind through rpc.
        """
        raise NotImplementedError()

    @bypassable_cache
    def get_transactions(self):
        url = 'http://btc.blockr.io/api/v1/address/txs/' + self.public_key
        response = requests.get(url)
        txs = response.json()['data']['txs']
        transactions = []
        for tx in txs:
            t = Transaction()
            t.date = arrow.get(tx['time_utc']).datetime
            t.amount = tx['amount']
            t.crypto_symbol = 'btc'
            t.txid = tx['tx']
            t.confirmations = tx['confirmations']
            transactions.append(t)
        return transactions


class LitecoinWallet(CryptoWallet):
    symbol = "LTC"
    full_name = 'Litecoin'
    price_source = "btc-e"
    tx_external_link_template = "http://explorer.litecoin.net/tx/{0}"

    @bypassable_cache
    def get_value(self):
        url = "http://ltc.blockr.io/api/v1/address/balance/"
        response = fetch_url(url + self.public_key)
        return float(response.json()['data']['balance'])

    def send_to_address(self, address, amount):
        raise NotImplementedError()

    @classmethod
    def generate_new_keypair(cls):
        keypair = LitecoinKeypair()
        return keypair.address(), keypair.private_key()

    @bypassable_cache
    def get_transactions(self):
        url = 'http://ltc.blockr.io/api/v1/address/txs/' + self.public_key
        response = fetch_url(url)
        txs = response.json()['data']['txs']
        transactions = []
        for tx in txs:
            t = Transaction()
            t.date = arrow.get(tx['time_utc']).datetime
            t.amount = tx['amount']
            t.crypto_symbol = 'ltc'
            t.txid = tx['tx']
            t.confirmations = tx['confirmations']
            transactions.append(t)
        return transactions

class DogecoinWallet(CryptoWallet):
    symbol = "DOGE"
    full_name = 'Dogecoin'
    price_source = 'dogeapi.com'
    tx_external_link_template = 'http://dogechain.info/tx/{0}'

    @bypassable_cache
    def get_value(self):
        url = "https://dogechain.info/chain/Dogecoin/q/addressbalance/"
        response = fetch_url(url + self.public_key)
        return float(response.content)

    def send_to_address(self, address, amount):
        raise NotImplementedError()

    @classmethod
    def generate_new_keypair(cls):
        keypair = DogecoinKeypair()
        return keypair.address(), keypair.private_key()

    def get_transactions(self):
        """
        This is what gets returned and iterated over from chain.so
        [
            {
             u'script_hex': u'76a91425877fec61fa9f74592ccfc43cd7430862171fd588ac',
             u'script_asm': u'OP_DUP OP_HASH160 25877fec61fa9f74592ccfc43cd7430862171fd5 OP_EQUALVERIFY OP_CHECKSIG',
             u'value': u'98995.00000000',
             u'txid': u'b6bd31a9d4db7a6d54a64086a0a51432336fb18338bece3f8382faa79728fbfc',
             u'confirmations': 16424,
             u'time': 1402876124,
             u'output_no': 1
            }
        ]
        """
        url = "https://chain.so/api/v2/get_tx_unspent/DOGE/"
        response = fetch_url(url + self.public_key)

        txs = response.json()['data']['txs']
        transactions = []
        for tx in txs:
            t = Transaction()
            t.date = arrow.get(tx['time']).datetime
            t.amount = tx['value']
            t.crypto_symbol = 'doge'
            t.txid = tx['txid']
            t.confirmations = tx['confirmations']
            transactions.append(t)
        return transactions


class PeercoinWallet(CryptoWallet):
    symbol = "PPC"
    full_name = 'Peercoin'
    price_source = 'btc-e'
    tx_external_link_template = "http://bkchain.org/ppc/tx/{0}"

    @bypassable_cache
    def get_value(self):
        url = "http://ppc.blockr.io/api/v1/address/balance/"
        response = fetch_url(url + self.public_key)
        return float(response.json()['data']['balance'])

    def send_to_address(self, address, amount):
        raise NotImplementedError()

    @classmethod
    def generate_new_keypair(cls):
        keypair = PeercoinKeypair()
        return keypair.address(), keypair.private_key()

    @bypassable_cache
    def get_transactions(self):
        """
        [
            {
             u'time_utc': u'2014-06-16T00:07:10Z',
             u'amount': 103.98,
             u'confirmations': 2152,
             u'amount_multisig': 0,
             u'tx': u'6dddc4deb0806d987844b429e73b20ce5f0355407cce220130b5eac8fa13970e'
            }
        ]
        """
        url = 'http://ppc.blockr.io/api/v1/address/txs/' + self.public_key
        response = fetch_url(url)
        txs = response.json()['data']['txs']
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

class FeathercoinWallet(CryptoWallet):
    symbol = 'FTC'
    full_name = 'Feathercoin'
    price_source = 'api.feathercoin.com'
    tx_external_link_template = "http://explorer.feathercoin.com/tx/{0}"

    @bypassable_cache
    def get_value(self):
        url= "http://api.feathercoin.com/?output=balance&address=%s&json=1" % self.public_key
        response = fetch_url(url)
        try:
            return float(response.json()['balance'])
        except:
            return 0

    @classmethod
    def generate_new_keypair(cls):
        keypair = FeathercoinKeypair()
        return keypair.address(), keypair.private_key()


class VertcoinWallet(CryptoWallet):
    symbol = 'VTC'
    full_name = 'Vertcoin'
    price_source = 'cryptocoincharts.info'
    tx_external_link_template = "http://explorer.obi.vg/tx/{0}"

    @bypassable_cache
    def get_value(self):
        url = "https://explorer.vertcoin.org/chain/Vertcoin/q/addressbalance/"
        response = fetch_url(url + self.public_key)
        return float(response.content)


class NextWallet(CryptoWallet):
    symbol = 'NXT'
    full_name = 'Next'
    price_source = 'cryptocoincharts.info'
    tx_external_link_template = "http://nxtexplorer.com/nxt/nxt.cgi?action=2000&tra={0}"

    @bypassable_cache
    def get_value(self):
        url='http://nxtportal.org/nxt?requestType=getAccount&account=' + self.public_key
        response = fetch_url(url)
        return float(response.json()['balanceNQT']) * 1e-8

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
    price_source = 'cryptocoincharts.info'
    tx_external_link_template = "{0}"
    addres = 'XrbZsLp9QDSf8usYYMPhmKWA8u1kQ26rQJ'

    def get_value(self, **k):
        return 15.0


class ReddcoinWallet(CryptoWallet):
    symbol = 'RDD'
    full_name = 'Reddcoin'
    price_source = 'cryptocoincharts.info'
    tx_external_link_template = "{0}"
    addres = 'RbHsU84Eo5tUBj7HDNEb9ZSw2fFhU1NKgD'

    def get_value(self, **k):
        return 1000000


class MyriadcoinWallet(CryptoWallet):
    symbol = 'MYR'
    full_name = 'Myriadcoin'
    price_source = 'cryptocoincharts.info'
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
