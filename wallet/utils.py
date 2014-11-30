import requests

def fetch_url(*args, **kwargs):
    """
    Wrapper for requests.get with app specific headers
    """
    headers = kwargs.pop('headers', None)
    custom = {'User-Agent': "CoinCollector 0.8"}
    if headers:
        headers.update(custom)
        kwargs['headers'] = headers
    else:
        kwargs['headers'] = custom

    print "making external request... %s" % args[0]
    ret = requests.get(*args, **kwargs)
    print "...done"
    return ret
