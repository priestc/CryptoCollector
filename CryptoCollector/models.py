import calendar
import json
import datetime
from collections import OrderedDict

import requests
import arrow
from django.db import models
from django.core.cache import cache
from django.conf import settings

from coinkit import (
    BitcoinKeypair, PeercoinKeypair, LitecoinKeypair, DogecoinKeypair,
    FeathercoinKeypair
)
from moneywagon import (
    CurrentPrice, HistoricalPrice, HistoricalTransactions, AddressBalance
)

from moneywagon.core import NoData

class KeyPair(models.Model):
    """
    Base methods for all types of cryptocurrency wallets
    """
    crypto = models.CharField(max_length=6)
    owner = models.ForeignKey('auth.User')
    date_created = models.DateTimeField(default=datetime.datetime.now)
    nickname = models.TextField(max_length=64, blank=True)
    address = models.TextField()
    private_key = models.TextField(null=True, blank=True)
    private_key_type = models.TextField()

    def __unicode__(self):
        return "%s - %s (%s %s)" % (
            self.owner.username, self.address, self.crypto, self.private_key_type
        )

    def get_balance(self, getter=None):
        return (getter or AddressBalance()).get_balance(self.crypto, self.address)

    def get_transactions(self, getter=None, verbose=False):
        """
        Fetch historical transactions from this address from an external block chain
        service (blockr.io or bitpay insight or whereever). All external api
        heavy lifting is done by the moneywagon module.

        The returned structore looks like this:

        {'amount': 147.58363366,
        'confirmations': 9093,
        'date': datetime.datetime(2014, 11, 16, 23, 53, 37, tzinfo=tzutc()),
        'txid': u'cb317dec84514773f34e4258cd0ff49eed6bfcf1770709b1ed07855d2e1a4aa4'}

        If `fiat` is passed in as an argument, an extra key is added. The vaue of
        that key is a lambda expression that when called evaluates to the fiat price
        at the time of transaction::

        returned = {'amount': 147.58363366,
        'confirmations': 9093,
        'historical_price': <function object>,
        'date': datetime.datetime(2014, 11, 16, 23, 53, 37, tzinfo=tzutc()),
        'txid': u'cb317dec84514773f34e4258cd0ff49eed6bfcf1770709b1ed07855d2e1a4aa4'}

        Then you call the function that has been returned:

        >>> returned['historical_price']()
        (3.2636992,
        'CRYPTOCHART/VTC x BITCOIN/BTCERUR',
        datetime.datetime(2014, 11, 13, 0, 0))
        """
        txgetter = (getter or HistoricalTransactions(verbose=verbose))
        return Transaction.from_moneywagon(
            self.crypto,
            response=txgetter.get(self.crypto, self.address),
            historical_price_service=HistoricalPrice(verbose=verbose)
        )


class Transaction(object):
    @classmethod
    def from_moneywagon(cls, crypto, response, historical_price_service=None):
        return [
            cls(crypto=crypto, historical_price_service=historical_price_service, **tx) for tx in response
        ]

    def __init__(self, txdata, historical_price_service=None):
        self.txdata = txdata
        self.hps = historical_price_service or HistoricalPrice()

    def corrected(self, fiat):
        """
        Get the amount of money transacted converted to fiat using the conversion
        rate at the time of transaction. All external calls to get the conversion
        rate are handled by the moneywagon module.
        """
        try:
            exchange, source, sample_date = self.hps.get(
                self.txdata['crypto'], self.txdata['fiat'], self.txdata['date']
            )
            fiat_amount = exchange * self.amount
        except NoData:
            fiat_amount = "??"

        l = locals()
        del l['self']
        return l

    def __repr__(self):
        polarity = '+' if self.amount > 0 else ''
        return "<TX: {} {:%Y-%m-%d} {}{}>".format(self.crypto, self.date, polarity, self.amount)

btc_external_link_template = "http://blockchain.info/tx/{0}"
ltc_external_link_template = "http://explorer.litecoin.net/tx/{0}"
doge_external_link_template = "http://dogechain.info/tx/{0}"
ppc_external_link_template = "http://bkchain.org/ppc/tx/{0}"
ftc_external_link_template = "http://explorer.feathercoin.com/tx/{0}"
vtc_external_link_template = "http://explorer.obi.vg/tx/{0}"
nxt_external_link_template = "http://nxtexplorer.com/nxt/nxt.cgi?action=2000&tra={0}"

# class SavedRecipientAddress(models.Model):
#     """
#     Represents an address the user has send money to and wants that address
#     to stick around because they may send to it again.
#     """
#     owner = models.ForeignKey('auth.User')
#     crypto_symbol = models.CharField(max_length=8)
#     name = models.TextField()
#     address = models.CharField(max_length=64)
