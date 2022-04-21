local datasource = import 'datasource.libsonnet';
local folder = import 'folder.libsonnet';

local username = 'foo';
local password = 'bar';
local folders = [
  { name: 'Ηλεκτρική Ενέργεια', uid: 'power', },
  { name: 'Φυσικό Αέριο', uid: 'gas', },
];
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
  datasources: [
    datasource.datasource(d['name'], username, password, d['timeField'], d['timeInterval']) for d in datasources
  ],
  folders: [
    folder.folder(f['name'], f['uid']) for f in folders
  ],
}
