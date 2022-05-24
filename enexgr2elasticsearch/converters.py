'''
Convert from Greek Energy Exchange Group xlsx files to JSON objects
ready to be POSTed to pre-specified Elasticsearch indices

Copyright Alexandros Kosiaris 2022
'''

import json
import warnings
from datetime import datetime

from pytz import timezone
from openpyxl import load_workbook as _load_workbook

from enexgr2elasticsearch.constants import ELECTRICITY_MARKETS_META_DATA, GAS_MARKETS_META_DATA

TZ = timezone('Europe/Athens')

def load_workbook(xlsx: str):
    '''
    Overriding load_workbook to catch exceptions and silence warnings
    Will raise openpyxl.utils.exceptions.InvalidFileException if trying to load
    an invalid file
    '''

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        workbook = _load_workbook(
                filename=xlsx,
                read_only=False)
    return workbook


def convert_electricity_market_results_workbook(xlsx: str) -> tuple:
    '''
    Converts the data from an enexgroup market result xlsx file to a ready for
    elasticsearch bulk API POST string
    '''

    workbook = load_workbook(xlsx)
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
    return (ret, hourly_mcps)


def calculate_electricity_hourly_daily_mcps(hourly_mcps: set) -> str:
    '''
    Calculate hourly/daily MCPs and send to dedicated index
    '''
    ret = ''
    if len(hourly_mcps) > 0:
        for mcp in hourly_mcps:
            ret += '{ "index": { "_index": "%s", "_id": "DAM-%s-MCP-HOURLY" } }' % (
                    ELECTRICITY_MARKETS_META_DATA['HOURLY_DAILY_MCPS']['index'],
                    mcp[1])
            ret += '\n{ "HOURLY_MCP": %s, "DELIVERY_MTU": "%s" }\n' % mcp
        daily_mcp = sum([x[0] for x in hourly_mcps])/len(hourly_mcps)
        dtime = min([x[1] for x in hourly_mcps])
        ret += '{ "index": { "_index": "%s", "_id": "DAM-%s-MCP-DAILY" } }' % (
                ELECTRICITY_MARKETS_META_DATA['HOURLY_DAILY_MCPS']['index'],
                dtime)
        ret += '\n{ "DAILY_MCP": %s, "DELIVERY_MTU": "%s" }\n' % (daily_mcp, dtime)
    return ret


def convert_electricity_curves_workbook(xlsx: str) -> str:
    '''
    Convert the data from an enexgroup aggregated curves result xlsx file to a
    ready for elasticsearch bulk API POST string
    '''

    workbook = load_workbook(xlsx)
    rows = workbook.active.rows

    tmp = next(rows)
    header = [x.value for x in tmp]

    ret = ''
    for row in rows:
        tmp = [x.value for x in row]
        data = dict(zip(header, tmp))
        # NOTE: Yes, the date format is inconsistent across time
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

    workbook = load_workbook(xlsx)
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


def convert_gas_workbook(xlsx: str) -> str:
    '''
    Convert the data from an enexgroup NGAS DOL result xlsx file to a
    ready for elasticsearch bulk API POST string
    '''

    workbook = load_workbook(xlsx)

    ret = ''
    for worksheet in workbook.worksheets:
        rows = worksheet.rows
        tmp = next(rows)
        # The if is there cause of empty columns with no name
        header = [x.value.strip() for x in tmp if x.value]

        for row in rows:
            tmp = [x.value for x in row if x.value]
            data = dict(zip(header, tmp))
            data['Trading Date'] = TZ.localize(data['Trading Date']).isoformat()
            ret += '{ "index": { "_index": "%s", "_id": "%s-%s-%s" } }' % (
                    GAS_MARKETS_META_DATA[worksheet.title]['index'],
                    data['Trading Date'],
                    data['Trading Series'],
                    data['Contract'])
            ret += '\n' + json.dumps(data) + '\n'
    return ret
