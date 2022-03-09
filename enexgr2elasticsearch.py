'''
Populate 3 elasticsearch clusters with Greek Energy Exchange Group free data

Copyright Alexandros Kosiaris 2022
'''

import argparse
import io
import json
import logging
import os
from datetime import datetime, timedelta
from urllib.parse import urljoin

import requests
from openpyxl import load_workbook
from pytz import timezone
from requests.auth import HTTPBasicAuth

VERSION = '0.1'
ELECTRICITY_MARKETS_META_DATA = {
        'RESULTS': {
            'index': 'enexgr_electricity_market_results',
            'base_urls': {
                'DAM':   '20126/200106/%s_EL-DAM_Results_EN_v01.xlsx',
                'LIDA1': '20126/235155/%s_EL-LIDA1_Results_EN_v01.xlsx',
                'LIDA2': '20126/263261/%s_EL-LIDA2_Results_EN_v01.xlsx',
                'LIDA3': '20126/263280/%s_EL-LIDA3_Results_EN_v01.xlsx',
                'CRIDA1': '20126/853663/%s_EL-CRIDA1_Results_EN_v01.xlsx',
                'CRIDA2': '20126/853680/%s_EL-CRIDA2_Results_EN_v01.xlsx',
                'CRIDA3': '20126/853704/%s_EL-CRIDA3_Results_EN_v01.xlsx',
            },
        },
        'CURVES': {
            'index': 'enexgr_electricity_market_curves',
            'base_urls': {
                'DAM': '20126/200034/%s_EL-DAM_AggrCurves_EN_v01.xlsx',
                'CRIDA1': '20126/853660/%s_EL-CRIDA1_AggrCurves_EN_v01.xlsx',
                'CRIDA2': '20126/853695/%s_EL-CRIDA2_AggrCurves_EN_v01.xlsx',
                'CRIDA3': '20126/853701/%s_EL-CRIDA3_AggrCurves_EN_v01.xlsx',
            },
        },
        'BLOCK_ORDERS': {
            'index': 'enexgr_electricity_market_block_orders',
            'base_urls': {
                'DAM': '20126/270103/%s_EL-DAM_BLKORDRs_EN_v01.xlsx',
            },
        },
}

BULK_ENDPOINT = '/_bulk'
TZ = timezone('Europe/Athens')
DELTA = timedelta(days=1)

BASE_ENEX_URL = 'https://www.enexgroup.gr/documents'

def put_to_elastic(data: str, url: str, elastic_info: dict) -> bool:
    '''
    PUT to elasticsearch
    '''
    user = elastic_info.get('user')
    password = elastic_info.get('password')
    if user and password:
        auth=HTTPBasicAuth(user, password)
    else:
        auth=None


    response = requests.put(
        url,
        headers={
            'Content-Type': 'application/json',
        },
        data=data.encode('utf-8'),
        auth=auth)
    if response.status_code != 200:
        logging.error('Error: %s, %s', response.status_code, response.content.decode())
        return False

    logging.debug('Data PUT successfully to elasticsearch, size: %s', len(data))
    return True


def post_to_bulk_elastic(data: str, url: str, elastic_info: dict) -> bool:
    '''
    Post to elasticsearch
    '''
    user = elastic_info.get('user')
    password = elastic_info.get('password')
    if user and password:
        auth=HTTPBasicAuth(user, password)
    else:
        auth=None


    response = requests.post(
        url,
        headers={
            'Content-Type': 'application/x-ndjson',
        },
        data=data.encode('utf-8'),
        auth=auth)
    if response.status_code != 200:
        logging.error('Error: %s, %s', response.status_code, response.content.decode())
        return False

    logging.debug('Bulk data indexed succesfully, size: %s', len(data))
    return True


def fetch_new_xlsx(url: str) -> str:
    '''
    Fetch and validate a new xlsx from enexgroup.gr
    '''

    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.content
    if resp.status_code == 404 or resp.status_code == 403:
        return None
    raise RuntimeError('Failed to fetch: %s' % resp.status_code)


def convert_electricity_market_results_workbook(xlsx: str) -> str:
    '''
    Converts the data from an enexgroup market result xlsx file to a ready for
    elasticsearch bulk API POST string
    '''

    try:
        workbook = load_workbook(
                filename=xlsx,
                read_only=False)
    except Exception as exc:
        logging.error(xlsx)
        raise exc
    rows = workbook.active.rows

    tmp = next(rows)
    header = [x.value for x in tmp]

    ret = ''
    hourly_mcps = set()
    for row in rows:
        tmp = [x.value for x in row]
        data = dict(zip(header, tmp))
        delivery_timestamp = datetime.fromisoformat(data['DELIVERY_MTU'])
        data['DELIVERY_MTU'] = TZ.localize(delivery_timestamp).isoformat()
        pub_timestamp = datetime.fromisoformat(data['PUB_TIME'])
        data['PUB_TIME'] = TZ.localize(pub_timestamp).isoformat()
        ret += '{ "index": { "_index": "%s", "_id": "%s-%s-%s-%s-%s-%s-%s" } }' % (
                ELECTRICITY_MARKETS_META_DATA['RESULTS']['index'],
                data['TARGET'],
                data['BIDDING_ZONE_DESCR'],
                data['SIDE_DESCR'],
                data['DDAY'],
                data['ASSET_DESCR'],
                data['CLASSIFICATION'],
                data['DELIVERY_MTU'])
        ret += '\n' + json.dumps(data) + '\n'
        if data['TARGET'] == 'DAM':
            hourly_mcps.add((data['MCP'], data['DELIVERY_MTU']))
    if len(hourly_mcps) > 0:
        for mcp in hourly_mcps:
            ret += '{ "index": { "_index": "%s", "_id": "DAM-%s-MCP-HOURLY" } }' % (
                    ELECTRICITY_MARKETS_META_DATA['RESULTS']['index'],
                    mcp[1])
            ret += '\n{ "HOURLY_MCP": %s, "DELIVERY_MTU": "%s" }\n' % mcp
        daily_mcp = sum([x[0] for x in hourly_mcps])/len(hourly_mcps)
        dtime = min([x[1] for x in hourly_mcps])
        ret += '{ "index": { "_index": "%s", "_id": "DAM-%s-MCP-DAILY" } }' % (
                ELECTRICITY_MARKETS_META_DATA['RESULTS']['index'],
                dtime)
        ret += '\n{ "DAILY_MCP": %s, "DELIVERY_MTU": "%s" }\n' % (daily_mcp, dtime)
    return ret


def convert_electricity_curves_workbook(xlsx: str) -> str:
    '''
    Convert the data from an enexgroup aggregated curves result xlsx file to a
    ready for elasticsearch bulk API POST string
    '''

    try:
        workbook = load_workbook(
                filename=xlsx,
                read_only=False)
    except Exception as exc:
        logging.error(xlsx)
        raise exc
    rows = workbook.active.rows

    tmp = next(rows)
    header = [x.value for x in tmp]

    ret = ''
    for row in rows:
        tmp = [x.value for x in row]
        data = dict(zip(header, tmp))
        # TODO: Tell them they are inconsistent
        data['DELIVERY_MTU'] = data['DELIVERY_MTU'].replace('/', '-')
        data['PUB_TIME'] = data['PUB_TIME'].replace('/', '-')
        delivery_timestamp = datetime.fromisoformat(data['DELIVERY_MTU'])
        data['DELIVERY_MTU'] = TZ.localize(delivery_timestamp).isoformat()
        pub_timestamp = datetime.fromisoformat(data['PUB_TIME'])
        data['PUB_TIME'] = TZ.localize(pub_timestamp).isoformat()
        ret += '{ "index": { "_index": "%s", "_id": "%s-%s-%s-%s-%s" } }' % (
                ELECTRICITY_MARKETS_META_DATA['CURVES']['index'],
                data['TARGET'],
                data['SIDE_DESCR'],
                data['DDAY'],
                data['AA'],
                data['DELIVERY_MTU'])
        ret += '\n' + json.dumps(data) + '\n'
    return ret


def convert_electricity_blockorders_workbook(xlsx: str) -> str:
    '''
    Convert the data from an enexgroup block orders result xlsx file to a
    ready for elasticsearch bulk API POST string
    '''

    try:
        workbook = load_workbook(
                filename=xlsx,
                read_only=False)
    except Exception as exc:
        logging.error(xlsx)
        raise exc
    rows = workbook.active.rows

    tmp = next(rows)
    header = [x.value for x in tmp]

    ret = ''
    for row in rows:
        tmp = [x.value for x in row]
        data = dict(zip(header, tmp))
        delivery_timestamp = datetime.fromisoformat(data['DELIVERY_MTU'])
        data['DELIVERY_MTU'] = TZ.localize(delivery_timestamp).isoformat()
        pub_timestamp = datetime.fromisoformat(data['PUB_TIME'])
        data['PUB_TIME'] = TZ.localize(pub_timestamp).isoformat()
        ret += '{ "index": { "_index": "%s", "_id": "%s-%s-%s-%s-%s-%s" } }' % (
                ELECTRICITY_MARKETS_META_DATA['BLOCK_ORDERS']['index'],
                data['TARGET'],
                data['BIDDING_ZONE_DESCR'],
                data['SIDE_DESCR'],
                data['DDAY'],
                data['CLASSIFICATION'],
                data['DELIVERY_MTU'])
        ret += '\n' + json.dumps(data) + '\n'
    return ret

def main():
    '''
    Main function
    '''

    parser = argparse.ArgumentParser(
            prog='enexgr.py',
            description='Fetch DAM data and put into elastic')
    parser.add_argument('-H',
                        '--host',
                        dest='host',
                        default='http://localhost:9200',
                        help='URL pointing to the elasticsearch cluster')
    parser.add_argument('-u',
                        '--user',
                        dest='user',
                        help='Elasticsearch user to write data')
    parser.add_argument('-p',
                        '--password',
                        dest='password',
                        help='Elasticsearch user password')
    parser.add_argument('--admin-user',
                        dest='admin_user',
                        help='Elasticsearch admin user to create the indices')
    parser.add_argument('--admin-password',
                        dest='admin_password',
                        help='Elasticsearch admin user password')
    parser.add_argument('--create-indices',
                        action='store_true',
                        dest='create_indices',
                        help='Create Elasticsearch indices. Requires elasticsearch admin access')
    parser.add_argument('-s',
                        '--start',
                        dest='start',
                        default=datetime.now().date().strftime('%Y-%m-%d'),
                        help='The start date. YYYY-MM-DD format')
    parser.add_argument('-e',
                        '--end',
                        dest='end',
                        default=(datetime.now().date()+DELTA).strftime('%Y-%m-%d'),
                        help='The end date. YYYY-MM-DD format')
    parser.add_argument('-v',
                        '--verbose',
                        action='count',
                        default=0,
                        dest='verbose',
                        help='Increase verbosity. May be specified multiple times')
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s ' + VERSION)
    args = parser.parse_args()
    if args.verbose == 1:
        logging.basicConfig(level=logging.INFO)
    if args.verbose > 1:
        logging.basicConfig(level=logging.DEBUG)
    elastic_info = dict(
            host = args.host,
            user = args.user,
            password = args.password)
    elastic_admin_info = dict(
            host = args.host,
            user = args.admin_user,
            password = args.admin_password)

    if args.create_indices:
        pass

    start_date = datetime.strptime(args.start, '%Y-%m-%d')
    end_date = datetime.strptime(args.end, '%Y-%m-%d')

    day_count = (end_date - start_date).days + 1

    bulk_url = urljoin(elastic_info['host'], BULK_ENDPOINT)
    for delta in range(0, day_count):
        date = start_date + timedelta(days=delta)
        for category, data in ELECTRICITY_MARKETS_META_DATA.items():
            base_urls = data['base_urls']
            for market, base_url in base_urls.items():
                url = BASE_ENEX_URL + '/' + base_url % date.strftime('%Y%m%d')
                # In 2021-09-22 LIDAs were renamed to CRIDAs. Don't try to fetch
                # LIDAs after this time and CRIDAs before this time
                if date > datetime(2021, 9, 21) and market.startswith('LIDA'):
                    continue
                if date <= datetime(2021, 9, 21) and market.startswith('CRIDA'):
                    continue
                tmp = fetch_new_xlsx(url)
                if tmp:
                    logging.debug('Successful fetch. Date: %s, category: %s, market: %s', date, category, market)
                    xlsx = io.BytesIO(tmp)
                    if category == 'RESULTS':
                        data = convert_electricity_market_results_workbook(xlsx)
                    if category == 'CURVES':
                        data = convert_electricity_curves_workbook(xlsx)
                    if category == 'BLOCK_ORDERS':
                        data = convert_electricity_blockorders_workbook(xlsx)
                    logging.debug('Successful conversion of xlsx to json. Date: %s, category: %s, market: %s', date, category, market)
                    if post_to_bulk_elastic(data, bulk_url, elastic_info):
                        logging.info('Posted to elasticsearch. Date: %s, category: %s, market: %s', date, category, market)


if __name__ == '__main__':
    main()
