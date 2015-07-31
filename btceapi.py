import json
import httplib
import decimal
import datetime

btce_domain = "btc-e.com"

class BTCEConnection:
    def __init__(self, timeout=30):
        self.conn = httplib.HTTPSConnection("10.99.168.35", "3128", timeout=timeout)
        self.conn.set_tunnel(btce_domain,443)
        self.cookie = None

    def close(self):
        self.conn.close()

    def getCookie(self):
        self.cookie = ""

        self.conn.request("GET", '/')
        response = self.conn.getresponse()

        setCookieHeader = response.getheader("Set-Cookie")
        match = HEADER_COOKIE_RE.search(setCookieHeader)
        if match:
            self.cookie = "__cfduid=" + match.group(1)

        match = BODY_COOKIE_RE.search(response.read())
        if match:
            if self.cookie != "":
                self.cookie += '; '
            self.cookie += "a=" + match.group(1)

    def makeRequest(self, url, extra_headers=None, params="", with_cookie=False):
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        if extra_headers is not None:
            headers.update(extra_headers)

        if with_cookie:
            if self.cookie is None:
                self.getCookie()

            headers.update({"Cookie": self.cookie})

        self.conn.request("POST", url, params, headers)
        response = self.conn.getresponse().read()

        return response

    def makeJSONRequest(self, url, extra_headers=None, params=""):
        response = self.makeRequest(url, extra_headers, params)
        return self.parseJSONResponse(response)

    def parseJSONResponse(self, response):
        def parse_decimal(var):
            return decimal.Decimal(var)

        try:
            r = json.loads(response, parse_float=parse_decimal,
                           parse_int=parse_decimal)
        except Exception as e:
            msg = "Error while attempting to parse JSON response:"\
                  " %s\nResponse:\n%r" % (e, response)
            raise Exception(msg)

        return r

class Trade(object):
    __slots__ = ('pair', 'trade_type', 'price', 'tid', 'amount', 'date')

    def __init__(self, **kwargs):
        for s in Trade.__slots__:
            setattr(self, s, kwargs.get(s))

        if type(self.date) in (int, float, decimal.Decimal):
            self.date = datetime.datetime.fromtimestamp(self.date)
        elif type(self.date) in (str, unicode):
            if "." in self.date:
                self.date = datetime.datetime.strptime(self.date,
                                                       "%Y-%m-%d %H:%M:%S.%f")
            else:
                self.date = datetime.datetime.strptime(self.date,
                                                       "%Y-%m-%d %H:%M:%S")

    def __getstate__(self):
        return dict((k, getattr(self, k)) for k in Trade.__slots__)

    def __setstate__(self, state):
        for k, v in state.items():
            setattr(self, k, v)

class Ticker(object):
    __slots__ = ('high', 'low', 'avg', 'vol', 'vol_cur', 'last', 'buy', 'sell',
                 'updated', 'server_time')

    def __init__(self, **kwargs):
        for s in Ticker.__slots__:
            setattr(self, s, kwargs.get(s))

        self.updated = datetime.datetime.fromtimestamp(self.updated)
        self.server_time = datetime.datetime.fromtimestamp(self.server_time)

    def __getstate__(self):
        return dict((k, getattr(self, k)) for k in Ticker.__slots__)

    def __setstate__(self, state):
        for k, v in state.items():
            setattr(self, k, v)

def get_fee(cnn, pair):
    fees = cnn.makeJSONRequest("/api/2/%s/fee" % pair)
    if type(fees) is not dict:
        raise TypeError("The response is not a dict.")

    trade_fee = fees.get(u'trade')
    if type(trade_fee) is not decimal.Decimal:
        raise TypeError("The response does not contain a trade fee")

    return trade_fee
            
def get_history(cnn, pair):
    history = cnn.makeJSONRequest("/api/2/%s/trades" % pair)

    if type(history) is not list:
        raise TypeError("The response is a %r, not a list." % type(history))

    result = []

    for h in history:
        h["pair"] = pair
        t = Trade(**h)
        result.append(t)
        
    return result

def get_ticker(cnn, pair):
    response = cnn.makeJSONRequest("/api/2/%s/ticker" % pair)

    if type(response) is not dict:
        raise TypeError("The response is a %r, not a dict." % type(response))

    return Ticker(**response[u'ticker'])

def get_book(cnn, pair):
    depth = cnn.makeJSONRequest("/api/2/%s/depth" % pair)
    if type(depth) is not dict:
        raise TypeError("The response is not a dict.")

    asks = depth.get(u'asks')
    if type(asks) is not list:
        raise TypeError("The response does not contain an asks list.")

    bids = depth.get(u'bids')
    if type(bids) is not list:
        raise TypeError("The response does not contain a bids list.")

    return asks, bids
