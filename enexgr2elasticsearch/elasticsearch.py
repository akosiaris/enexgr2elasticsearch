'''
Simple functions to POST/PUT to elasticsearch. Possibly can be replaced by using
the elasticsearch python package in the future

Copyright Alexandros Kosiaris 2024
'''

import json
from urllib.parse import urljoin

import requests
import structlog
from requests.auth import HTTPBasicAuth, AuthBase

from enexgr2elasticsearch.constants import ELECTRICITY_MARKETS_META_DATA, GAS_MARKETS_META_DATA

BULK_ENDPOINT = '/_bulk'
TIMEOUT = 30
logger = structlog.get_logger(__name__)

class APIKeyAuth(AuthBase):
    '''Attaches Elasticsearch API Key Authentication to the given Request object.'''

    def __init__(self, apikey):
        self.apikey= apikey

    def __eq__(self, other):
        return self.apikey== getattr(other, 'apikey', None)

    def __ne__(self, other):
        return not self == other

    def __call__(self, r):
        r.headers['Authorization'] = 'ApiKey ' + self.apikey
        return r


def put_to_elastic(data: str, url: str, elastic_info: dict) -> bool:
    '''
    PUT to elasticsearch
    '''
    apikey = elastic_info.get('apikey')
    user = elastic_info.get('user')
    password = elastic_info.get('password')
    if apikey:
        auth=APIKeyAuth(apikey)
    elif user and password:
        auth=HTTPBasicAuth(user, password)
    else:
        auth=None

    logger.debug('Data to be PUT to elasticsearch', data=data)
    try:
        response = requests.put(
            url,
            headers={
                'Content-Type': 'application/json',
            },
            data=data.encode('utf-8'),
            auth=auth,
            timeout=TIMEOUT)
        if response.status_code != 200:
            logger.error('Elasticsearch error response',
                    status_code=response.status_code,
                    body=response.content.decode())
            return False
    except requests.exceptions.ConnectionError as exc:
        logger.error('Connection failed', exc_info=exc)

    logger.debug('Data PUT successfully to elasticsearch', size=len(data))
    return True


def post_to_bulk_elastic(data: str, url: str, elastic_info: dict) -> bool:
    '''
    Post to elasticsearch
    '''
    apikey = elastic_info.get('apikey')
    user = elastic_info.get('user')
    password = elastic_info.get('password')
    if apikey:
        auth=APIKeyAuth(apikey)
    elif user and password:
        auth=HTTPBasicAuth(user, password)
    else:
        auth=None

    logger.debug('Data to be POSTed to elasticsearch', data=data)
    try:
        response = requests.post(
            url,
            headers={
                'Content-Type': 'application/x-ndjson',
            },
            data=data.encode('utf-8'),
            auth=auth,
            timeout=TIMEOUT)
        if response.status_code != 200:
            logger.error('Elasticsearch error response',
                    status_code=response.status_code,
                    body=response.content.decode())
            return False
    except requests.exceptions.ConnectionError as exc:
        logger.error('Connection failed', exc_info=exc)

    logger.debug('Bulk data indexed succesfully', size=len(data))
    return True


def create_elasticsearch_indices(elastic_admin_info: dict, shards: int,
        replicas: int) -> bool:
    '''
    Create the elasticsearch indices alongside mappings
    '''

    electricity_indices = map(lambda x: x[1]['index'], ELECTRICITY_MARKETS_META_DATA.items())
    gas_indices = map(lambda x: x[1]['index'], GAS_MARKETS_META_DATA.items())
    settings = {
        "settings": {
            "number_of_shards": shards,
            "number_of_replicas": replicas,
        }
    }
    indices = list(electricity_indices) + list(gas_indices)
    for idx in indices:
        # TODO: Fix finding the index files
        with open(f'{idx}.index', 'r', encoding='utf-8') as fil:
            # Load the mappings
            data = json.load(fil)
            data.update(settings)
            url = urljoin(elastic_admin_info['host'], idx)
            if put_to_elastic(json.dumps(data), url, elastic_admin_info):
                logger.info('index created succesfully', index=idx)
            else:
                logger.warning('index creation failed', index=idx)
                return False
    return True
