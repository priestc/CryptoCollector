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

        if pair == 'ppc_usd':
            # since bter doesn't support usd_ppc,we need to make 2 calls and
            # do the math ourselvs. Th extra http request isn't a problem because
            # of caching that happens upstream
            url = "http://data.bter.com/api/1/ticker/ppc_btc"
            response = fetch_url(url).json()
            ppc_btc = float(response['last'] or 0)

            url = "http://data.bter.com/api/1/ticker/btc_usd"
            response = fetch_url(url).json()
            btc_usd = float(response['last'] or 0)

            return btc_usd * ppc_btc, 'bter'

        if pair == 'vtc_usd':
            # since bter doesn't support usd_vtc, we need to make 2 calls and
            # do the math ourselvs. Th extra http request isn't a problem because
            # of caching that happens upstream
            url = "http://data.bter.com/api/1/ticker/vtc_btc"
            response = fetch_url(url).json()
            vtc_btc = float(response['last'] or 0)

            url = "http://data.bter.com/api/1/ticker/btc_usd"
            response = fetch_url(url).json()
            btc_usd = float(response['last'] or 0)

            return btc_usd * vtc_btc, 'bter'

        if pair == 'ftc_usd':
            # since bter doesn't support usd_ftc, we need to make 2 calls and
            # do the math ourselvs. Th extra http request isn't a problem because
            # of caching that happens upstream
            url = "http://data.bter.com/api/1/ticker/ftc_btc"
            response = fetch_url(url).json()
            ftc_btc = float(response['last'] or 0)

            url = "http://data.bter.com/api/1/ticker/btc_usd"
            response = fetch_url(url).json()
            btc_usd = float(response['last'] or 0)

            return btc_usd * ftc_btc, 'bter'

        url = "http://data.bter.com/api/1/ticker/%s" % pair
        response = fetch_url(url).json()
        return float(response['last'] or 0), 'bter'
