'''
Populate elasticsearch with Greek Energy Exchange Group free data

Copyright Alexandros Kosiaris 2024
'''

import argparse
import sys

from datetime import datetime, timedelta

import structlog

from enexgr2elasticsearch.constants import VERSION
from enexgr2elasticsearch.logsetup import setup_logging
from enexgr2elasticsearch.elasticsearch import create_elasticsearch_indices
from enexgr2elasticsearch.enexgr import process_enexgr_days


DELTA = timedelta(days=1)

def main():
    '''
    Main function
    '''

    parser = argparse.ArgumentParser(
            prog='enexgr.py',
            description='Fetch enexgroup.gr data and put into Elasticsearch')
    parser.add_argument('-H',
                        '--host',
                        dest='host',
                        default='http://localhost:9200',
                        help='URL pointing to the elasticsearch cluster')
    parser.add_argument('--api-key',
                        dest='apikey',
                        help='Elasticsearch API key to write data. If specified, takes precedence over user/password')
    parser.add_argument('-u',
                        '--user',
                        dest='user',
                        help='Elasticsearch user to write data')
    parser.add_argument('-p',
                        '--password',
                        dest='password',
                        help='Elasticsearch user password')
    parser.add_argument('--admin-api-key',
                        dest='admin_apikey',
                        help='Elasticsearch API key to create the indices. If specified, takes precedence over admin_user/admin_password')
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
    parser.add_argument('--create-indices-shards',
                        default=1,
                        dest='shards',
                        help='''Number of shards for each newly created
                        Elasticsearch index. Used only when creating indices.
                        Defaults to 1. Requires elasticsearch admin access''')
    parser.add_argument('--create-indices-replicas',
                        default=0,
                        dest='replicas',
                        help='''Number of replicas for each newly created
                        Elasticsearch index. Used only when creating indices.
                        Defaults to 0. Requires elasticsearch admin access''')
    parser.add_argument('-s',
                        '--start',
                        dest='start',
                        default=(datetime.now().date()-DELTA).strftime('%Y-%m-%d'),
                        help='The start date. YYYY-MM-DD format. Defaults to yesterday')
    parser.add_argument('-e',
                        '--end',
                        dest='end',
                        default=(datetime.now().date()+DELTA).strftime('%Y-%m-%d'),
                        help='The end date. YYYY-MM-DD format. Defaults to tomorrow')
    parser.add_argument('-c',
                        '--cache',
                        dest='cache',
                        help='Directory to be used as R/W cache for .xlsx files')
    parser.add_argument('-v',
                        '--verbose',
                        action='count',
                        default=0,
                        dest='verbose',
                        help='Increase verbosity. May be specified multiple times')
    parser.add_argument('--ecs-logging',
                        action='store_true',
                        default=False,
                        dest='ecs_logging',
                        help='''Use Elastic Common Schema logging. If
                        --ecs-logging-endpoint is also configured, logs will be
                        sent there via Elasticsearch REST index API. Otherwise,
                        stdout will be used''')
    parser.add_argument('--ecs-logging-endpoint',
                        dest='ecs_logging_endpoint',
                        help='''An ECS compatible Elasticsearch index endpoint,
                        without the scheme (e.g. http://). A valid value would be
                        "localhost:9200/logs-enexgr2elasticsearch-1/"
                        which uses the post 7.16 built-in elasticsearch
                        "logs-*-*" Data Stream.
                        WARNING: The behavior is very simplistic and crude. If you want proper
                        handling of logs, invest in a proper log collector''')
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s ' + VERSION)
    args = parser.parse_args()

    # Let's setup logging first
    setup_logging(args)
    logger = structlog.get_logger(__name__)

    elastic_info = dict(
            host = args.host,
            apikey = args.apikey,
            user = args.user,
            password = args.password)
    elastic_admin_info = dict(
            host = args.host,
            apikey = args.admin_apikey,
            user = args.admin_user,
            password = args.admin_password)

    if args.create_indices:
        if not create_elasticsearch_indices(
            elastic_admin_info,
            args.shards,
            args.replicas):
            logger.critical('Failed to create indices despite being asked to',
                    shards=args.shards,
                    replicas=args.replicas)
            sys.exit(1)

    start_date = datetime.strptime(args.start, '%Y-%m-%d')
    end_date = datetime.strptime(args.end, '%Y-%m-%d')

    process_enexgr_days(elastic_info, start_date, end_date, args.cache)


if __name__ == '__main__':
    main()
