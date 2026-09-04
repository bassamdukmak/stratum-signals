"""Pull the Supabase rows the dashboard reads and return them as the SNAPSHOT object.
Mirrors the page's own queries (fetchSignals, fetchStoredBars, fetchCadenceArchives,
fetchCongressArchiveRaw). Credentials come from the environment only."""
import json, os, re, urllib.request
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

BASE = os.environ['SUPABASE_URL'].rstrip('/') + '/rest/v1/'
KEY = os.environ['SUPABASE_SERVICE_KEY']
PAGE = 1000


def get(path, extra=None):
    headers = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, **(extra or {})}
    with urllib.request.urlopen(urllib.request.Request(BASE + path, headers=headers)) as r:
        return r.headers, r.read()


def paged(query):
    rows = []
    for off in range(0, 10**7, PAGE):
        page = json.loads(get(query + '&limit=%d&offset=%d' % (PAGE, off))[1])
        rows += page
        if len(page) < PAGE:
            return rows


def version(table, col):
    h, _ = get(table + '?select=' + col, {'Prefer': 'count=exact', 'Range': '0-0'})
    return h['content-range'].split('/')[1]


def capture(page_html):
    """page_html is the template; the column list and benchmark ETFs are read from it
    so the capture cannot drift from what the page queries."""
    cols = re.search(r"var SIGNAL_COLUMNS = \[(.*?)\]\.join", page_html, re.S).group(1)
    cols = ','.join(re.findall(r"'([a-z0-9_]+)'", cols))
    bench_block = page_html[page_html.index('var DEFAULT_BENCHMARKS'):page_html.index('function benchmarkForTicker')]
    benchmarks = set(re.findall(r"'([A-Z]+)'", bench_block))

    tables = {
        'signal_outcome': paged('signal_outcome?select=' + cols + '&order=report_date.desc,id.asc'),
        'daily_archive': paged('daily_archive?select=report_date,csv_data,report_text&order=report_date.asc'),
        'weekly_archive': json.loads(get('weekly_archive?select=week_key,created_at,weekly_scores,report_text&order=week_key.desc&limit=200')[1]),
        'monthly_archive': json.loads(get('monthly_archive?select=month_key,generated_at,monthly_scores,report_text&order=month_key.desc&limit=200')[1]),
        'congress_trade': paged('congress_trade?select=*&order=filing_date.desc'),
    }
    empty = [name for name, rows in tables.items() if not rows]
    assert not empty, 'empty tables: ' + ', '.join(empty)

    # Same symbol set and start date the page computes for itself (signal tickers,
    # their benchmarks, congress tickers; a week before the earliest signal).
    tickers = {r['ticker'] for r in tables['signal_outcome'] + tables['congress_trade']
               if r.get('ticker') and re.fullmatch(r'[A-Z0-9.-]{1,10}', r['ticker'])}
    symbols = sorted(tickers | benchmarks)
    earliest = min(r['report_date'] for r in tables['signal_outcome'])
    bar_from = (date.fromisoformat(earliest) - timedelta(days=7)).isoformat()
    bars = {}
    for i in range(0, len(symbols), 60):
        rows = paged('price_history_daily?select=symbol,session_date,close&symbol=in.(' + ','.join(symbols[i:i + 60])
                     + ')&session_date=gte.' + bar_from + '&order=symbol.asc,session_date.asc')
        for r in rows:
            bars.setdefault(r['symbol'], []).append([r['session_date'], float(r['close'])])
    assert bars, 'no price bars'

    return {
        'capturedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'today': datetime.now(ZoneInfo('America/New_York')).date().isoformat(),
        'versions': {'signal_outcome': version('signal_outcome', 'id'), 'price_history_daily': version('price_history_daily', 'symbol')},
        'tables': tables,
        'bars': bars,
    }
