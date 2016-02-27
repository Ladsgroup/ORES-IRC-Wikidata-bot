import pydle
import pywikibot
import urllib.request
import time
import json

site = pywikibot.Site('wikidata', fam='wikidata')
url = "http://ores.wmflabs.org/scores/wikidatawiki/?models=reverted&revids="


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i+n]


def close_loop(client):
    client.connection.eventloop.io_loop._running = False
    client.disconnect()
    print('yay')


def recent_changes_gen(site):
    params = {
        'action': 'query',
        'list': 'recentchanges',
        'rcshow': '!bot|!patrolled',
        'rclimit': 100,
        'rctype': 'edit',
        'rctoponly': '1',
        'rcprop': 'ids',
        'rcnamespace': '0',
    }
    res = pywikibot.data.api.Request(site=site, **params).submit()
    for case in res['query']['recentchanges']:
        yield str(case['revid'])


class Ghaher69Bot(pywikibot.Bot):
    """docstring for Ghaher69Bot"""
    def __init__(self, gen, site):
        super(Ghaher69Bot, self).__init__()
        self.gen = gen
        self.site = site
        self._cache = {}
        self.site.login()

    def run(self):
        revs = list(self.cache_filter())
        ids = {}
        for chunk in chunks(revs, 50):
            self.url = url + u'|'.join(chunk)
            res = json.loads(
                urllib.request.urlopen(self.url).read().decode('utf-8'))
            for revid in res:
                self._cache[revid] = res[revid]['reverted']
                if 'probability' not in res[revid]['reverted']:
                    continue
                d_score = res[revid]['reverted']['probability']['true']
                if d_score > 0.95:
                    ids[revid] = d_score

        self.flush_away(ids)

    def cache_filter(self):
        for rev in self.gen(self.site):
            if rev not in self._cache:
                yield rev

    def flush_away(self, res):
        client = MyClient('Dexbot', res)
        try:
            client.connect('irc.freenode.net', tls=True)
        except ValueError:
            time.sleep(300)
            self.flush_away(res)
        print('Trying to connect')
        client.connection.setup_handlers()
        client.connection.eventloop.io_loop.add_timeout(
            time.time() + 20, close_loop, client)
        client.connection.eventloop.run()


class MyClient(pydle.Client):
    def __init__(self, name, res):
        super(MyClient, self).__init__(name)
        self.res = res

    def on_connect(self):
        super().on_connect()
        self.join('#wikidata-vandalism')
        for revid in self.res:
            message = 'https://www.wikidata.org/w/index.php?diff={revid} : ' \
                'Score = {score}'.format(revid=revid, score=self.res[revid])
            self.message(target='#wikidata-vandalism', message=message)


bot = Ghaher69Bot(recent_changes_gen, site)
while True:
    bot.run()
    print('Done')
    time.sleep(360)
