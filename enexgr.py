import argparse
import io
import json
import os
import requests

from datetime import date, datetime, timedelta
from openpyxl import load_workbook
from pytz import timezone
from requests.auth import HTTPBasicAuth

INDEX = os.getenv('ELASTICSEARCH_INDEX')
ELASTIC_USERNAME = os.getenv('ELASTIC_USERNAME')
ELASTIC_PASSWORD = os.getenv('ELASTIC_PASSWORD')
BULK_URL = 'http://localhost:9200/_bulk/'
TZ = timezone('Europe/Athens')
DELTA = timedelta(days=1)

BASE_ENEX_URL = 'https://www.enexgroup.gr/documents'
MARKET_BASE_URLS = {
    'DAM':   '20126/200106/%s_EL-DAM_Results_EN_v01.xlsx',
    'LIDA1': '20126/235155/%s_EL-LIDA1_Results_EN_v01.xlsx',
    'LIDA2': '20126/263261/%s_EL-LIDA2_Results_EN_v01.xlsx',
    'LIDA3': '20126/263280/%s_EL-LIDA3_Results_EN_v01.xlsx',
}

def post_to_elastic(r):
    response = requests.post(
        BULK_URL,
        headers={
            'Content-Type': 'application/x-ndjson',
        },
        data=r.encode('utf-8'),
        auth=HTTPBasicAuth(ELASTIC_USERNAME, ELASTIC_PASSWORD))
    if response.status_code != 200:
        print('Error: %s, %s' % (response.status_code, response.content.decode()))
    else:
        print('Bulk data indexed succesfully, size: %s' % len(r))


def fetch_new_xlsx(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.content
    else:
        raise RuntimeError('Failed to fetch: %s' % r.status_code)


def convert_workbook(xlsx):
    wb = load_workbook(
            filename=xlsx,
            read_only=False)
    ws = wb.active
    rows = ws.rows

    tmp = next(rows)
    header = [x.value for x in tmp]

    r = ''
    for row in rows:
        tmp = [x.value for x in row]
        d = dict(zip(header, tmp))
        delivery_timestamp = datetime.fromisoformat(d['DELIVERY_MTU'])
        d['DELIVERY_MTU'] = TZ.localize(delivery_timestamp).isoformat()
        pub_timestamp = datetime.fromisoformat(d['PUB_TIME'])
        d['PUB_TIME'] = TZ.localize(pub_timestamp).isoformat()
        r += '{ "index": { "_index": "%s", "_id": "%s-%s-%s-%s-%s-%s-%s" } }' % (
                INDEX,
                d['TARGET'],
                d['BIDDING_ZONE_DESCR'],
                d['SIDE_DESCR'],
                d['DDAY'],
                d['ASSET_DESCR'],
                d['CLASSIFICATION'],
                d['DELIVERY_MTU'])
        r += '\n' + json.dumps(d) + '\n'
    return r
    print(r)


def main():
    parser = argparse.ArgumentParser(description='Fetch DAM data and put into elastic')
    parser.add_argument('--start',
                        dest='start',
                        default=datetime.now().date().strftime('%Y-%m-%d'),
                        help='The start date. YYYY-MM-DD format')
    parser.add_argument('--end',
                        dest='end',
                        default=datetime.now().date().strftime('%Y-%m-%d'),
                        help='The end date. YYYY-MM-DD format')
    args = parser.parse_args()

    start_date = datetime.strptime(args.start, '%Y-%m-%d')
    end_date = datetime.strptime(args.end, '%Y-%m-%d')

    day_count = (end_date - start_date).days + 1

    for x in range(0, day_count):
        d = start_date + timedelta(days=x)
        for market, base_url in MARKET_BASE_URLS.items():
            url = BASE_ENEX_URL + '/' + base_url % d.strftime('%Y%m%d')
            xlsx = io.BytesIO(fetch_new_xlsx(url))
            data = convert_workbook(xlsx)
            post_to_elastic(data)


if __name__ == '__main__':
    main()
