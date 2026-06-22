'''
Fetch Greek Energy Exchange Group free data

Copyright Alexandros Kosiaris 2024
'''

import io
import os

from datetime import datetime, timedelta
from urllib.parse import urljoin

import requests
import structlog

from enexgr2elasticsearch.constants import \
    BASE_ENEX_URL, \
    ELECTRICITY_MARKETS_META_DATA, \
    GAS_MARKETS_META_DATA

from enexgr2elasticsearch.elasticsearch import \
    post_to_bulk_elastic, \
    BULK_ENDPOINT

from enexgr2elasticsearch.converters import \
    convert_electricity_market_results_workbook, \
    calculate_electricity_hourly_daily_mcps, \
    convert_electricity_curves_workbook, \
    convert_electricity_blockorders_workbook, \
    convert_gas_workbook


TIMEOUT = 10 # seconds before we give up fetching data

logger = structlog.get_logger(__name__)

def fetch_new_xlsx(url: str) -> str:
    '''
    Fetch and validate a new xlsx from enexgroup.gr
    '''

    resp = requests.get(url, timeout=TIMEOUT)
    if resp.status_code == 200:
        return resp.content
    if resp.status_code in (403, 404):
        return None
    raise RuntimeError(f'Failed to fetch: {resp.status_code}')


def get_xlsx(cache: str, filepath: str) -> io.BytesIO:
    '''
    Get xlsx from cache or fetch from internet
    '''
    url = BASE_ENEX_URL + '/' + filepath
    _, filename = os.path.split(filepath)
    cache_path = None
    if cache:
        cache_path = os.path.join(cache, filename)
        try:
            tmp = open(cache_path, 'rb').read()
            logger.info('Cache-hit', xlsx=filename)
            return io.BytesIO(tmp)
        except FileNotFoundError:
            logger.info('Cache-miss', xlsx=filename)
    tmp = fetch_new_xlsx(url)
    if tmp:
        logger.info('Successful download', xlsx=filename)
        # Write to cache if enabled
        if cache_path:
            with open(cache_path, 'wb') as cache_file:
                cache_file.write(tmp)
        return io.BytesIO(tmp)
    return None


def process_enexgr_days(elastic_info: dict,
        start_date: datetime,
        end_date: datetime,
        cache: str=None):
    '''
    Process enexgr data
    '''
    day_count = (end_date - start_date).days + 1

    bulk_url = urljoin(elastic_info['host'], BULK_ENDPOINT)
    for delta in range(0, day_count):
        date = start_date + timedelta(days=delta)
        markets_meta_data = {}
        markets_meta_data.update(ELECTRICITY_MARKETS_META_DATA)
        markets_meta_data.update(GAS_MARKETS_META_DATA)
        for category, data in markets_meta_data.items():
            local_log = logger.bind(
                xlsx_date=date.isoformat(),
                category=category)
            try:
                base_urls = data['base_urls']
            except KeyError:
                local_log.debug('Category missing base_urls, skipping')
                continue
            for market, base_url in base_urls.items():
                local_log = local_log.bind(market=market)
                # In 2021-09-22 LIDAs were renamed to CRIDAs. Don't try to fetch
                # LIDAs after this time and CRIDAs before this time
                if date > datetime(2021, 9, 21) and market.startswith('LIDA'):
                    continue
                if date <= datetime(2021, 9, 21) and market.startswith('CRIDA'):
                    continue
                # And in 2024-06-14 again renamed to IDAs
                if date > datetime(2024, 6, 13) and market.startswith('CRIDA'):
                    continue
                if date <= datetime(2024, 6, 13) and market.startswith('IDA'):
                    continue

                filepath = base_url % date.strftime('%Y%m%d')
                xlsx = get_xlsx(cache, filepath)
                if xlsx:
                    local_log.info('Successful xlsx fetch')
                    if category == 'RESULTS':
                        data, hourly_mcps = convert_electricity_market_results_workbook(xlsx)
                        data = data + calculate_electricity_hourly_daily_mcps(hourly_mcps)
                    if category == 'CURVES':
                        data = convert_electricity_curves_workbook(xlsx)
                    if category == 'BLOCK_ORDERS':
                        data = convert_electricity_blockorders_workbook(xlsx)
                    if category == 'NGAS_Results':
                        data = convert_gas_workbook(xlsx)
                    local_log.info('xlsx to json done')
                    if not data:
                        local_log.warn('No data, skipping post')
                        continue
                    if post_to_bulk_elastic(data, bulk_url, elastic_info):
                        local_log.info('Posted to bulk API')
