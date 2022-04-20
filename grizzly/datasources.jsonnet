local username = 'foo';
local password = 'bar';
local datasources = [
  { name: 'enexgr_electricity_market_block_orders', timeField: 'DELIVERY_MTU', timeInterval: '1h', },
  { name: 'enexgr_electricity_market_curves', timeField: 'DELIVERY_MTU', timeInterval: '1h', },
  { name: 'enexgr_electricity_market_hourly_daily_mcps', timeField: 'DELIVERY_MTU', timeInterval: '1h', },
  { name: 'enexgr_electricity_market_results', timeField: 'DELIVERY_MTU', timeInterval: '1h', },
  { name: 'enexgr_gas_market_announcements', timeField: 'Trading Date', timeInterval: '1d', },
  { name: 'enexgr_gas_market_details', timeField: 'Trading Date', timeInterval: '1d', },
  { name: 'enexgr_gas_market_results', timeField: 'Trading Date', timeInterval: '1d', },
];


{
  local datasource(
    name,
    user,
    password,
    timeField,
    timeInterval,
    url='http://elasticsearch:9200',
    ) = {
    apiVersion: 'grizzly.grafana.com/v1alpha1',
    kind: 'Datasource',
    metadata: {
        name: name,
    },
    spec: {
        access: 'proxy',
        basicAuth: true,
        basicAuthPassword: password,
        basicAuthUser: user,
        database: name,
        isDefault: false,
        jsonData: {
            esVersion: '7.10.0',
            includeFrozen: false,
            logLevelField: '',
            logMessageField: '',
            maxConcurrentShardRequests: 5,
            timeField: timeField,
            timeInterval: timeInterval,
            xpack: true,
        },
        name: name,
        orgId: 1,
        password: '',
        readOnly: false,
        secureJsonFields: {
            basicAuthPassword: true,
        },
        type: 'elasticsearch',
        typeLogoUrl: '',
        url: url,
        user: '',
        withCredentials: false,
     },
  },
  datasources: [
    datasource(d['name'], username, password, d['timeField'], d['timeInterval']) for d in datasources
  ]
}
