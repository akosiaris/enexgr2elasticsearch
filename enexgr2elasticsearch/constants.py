'''
Some enexgr2elasticsearch constants
'''

VERSION = '0.0.1'
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
    'HOURLY_DAILY_MCPS': {
        # The hourly_daily_mcp index is a derivative one, so we only have a name
        'index': 'enexgr_electricity_market_hourly_daily_mcps',
    },
}

GAS_MARKETS_META_DATA = {
    'NGAS_Results': {
        'index': 'enexgr_gas_market_results',
        'base_urls': {
            'NGAS_DOL': '20126/997118/%s_NGAS_DOL_EN_v01.xlsx',
        },
    },
    'Auctions_Details': {
        'index': 'enexgr_gas_market_details',
    },
    'Announcements': {
        'index': 'enexgr_gas_market_announcements',
    },
}

BASE_ENEX_URL = 'https://www.enexgroup.gr/documents'
