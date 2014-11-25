from CryptoCoinChartsApi import API as CCCAPI
from utils import fetch_url

class PriceGetter(object):
    def get_price(self, crypto_symbol, fiat_symbol):
        """
        Makes call to external service, and returns the price for given
        fiat/crypto pair. Returns two item tuple: (price, best_market)
        """

class OldCryptoCoinChartsPriceGetter(PriceGetter):
    """
    Using raw rest API (broken apparently)
    """
    def get_price(self, crypto_symbol, fiat_symbol):
        url = "http://api.cryptocoincharts.info/tradingPairs/%s_%s" % (
            crypto_symbol, fiat_symbol
        )
        response = fetch_url(url).json()
        print response
        return float(response['price'] or 0), response['best_market']

class CryptoCoinChartsPriceGetter(PriceGetter):
    """
    Using fancy API client library (currently broken)
    """
    def get_price(self, crypto_symbol, fiat_symbol):
        api = CCCAPI()
        tradingpair = api.tradingpair("%s_%s" % (crypto_symbol, fiat_symbol))
        return tradingpair.price, tradingpair.best_market

class BTERPriceGetter(PriceGetter):
    def get_price(self, crypto_symbol, fiat_symbol):
        pair = ("%s_%s" % (crypto_symbol, fiat_symbol)).lower()
        url = "http://data.bter.com/api/1/ticker/%s" % pair

        response = fetch_url(url).json()
        print response

        if response['result'] == 'false': # bter api returns this as string
            # bter doesn't support this pair, we need to make 2 calls and
            # do the math ourselves. The extra http request isn't a problem because
            # of caching that happens upstream. BTER only has USD, BTC and CNY
            # markets, so any other fiat will likely fail.

            url = "http://data.bter.com/api/1/ticker/%s_btc" % crypto_symbol
            response = fetch_url(url).json()
            altcoin_btc = float(response['last'] or 0)

            url = "http://data.bter.com/api/1/ticker/btc_%s" % fiat_symbol
            response = fetch_url(url).json()
            print response
            btc_fiat = float(response['last'] or 0)

            return btc_fiat * altcoin_btc, 'bter (calculated)'

        return float(response['last'] or 0), 'bter'


class CryptonatorPriceGetter(PriceGetter):
    def get_price(self, crypto_symbol, fiat_symbol):
        pair = ("%s-%s" % (crypto_symbol, fiat_symbol)).lower()
        url = "https://www.cryptonator.com/api/ticker/%s" % pair
        response = fetch_url(url).json()
        return float(response['ticker']['price']), 'cryptonator'
