local grafana = import 'grafonnet-lib/grafonnet/grafana.libsonnet';
local dashboard = grafana.dashboard;
local row = grafana.row;
local template = grafana.template;
local graphPanel = grafana.graphPanel;

local ds = {
  'type': 'elasticsearch',
  'uid': 'enexgr_electricity_market_block_orders',
};

local shared_target = grafana.elasticsearch.target(
  query='',
  timeField='DELIVERY_MTU',
  metrics=[
    { 'id': '1', 'field': 'TOTAL_QUANTITY', 'type': 'sum', 'settings': { 'script': '_value*1000'}},
  ],
  bucketAggs=[
    { 'id': '2',
      'field': 'DELIVERY_MTU',
      'type': 'date_histogram',
      'settings': {
	'interval': 'auto',
	'min_doc_count': '0',
	'trimEdges': '0',
	'timeZone': 'Europe/Athens',
      },
    },
  ],
);

local block_orders_target = shared_target + {
  # Doing a trick here to ensure proper order
  bucketAggs: [
    { 'id': '4',
      'field': 'SIDE_DESCR',
      'type': 'terms',
      'settings': {
	'order': 'desc',
	'orderBy': '_term',
	'min_doc_count': '1',
	'size': '0',
      },
    },
    ] + shared_target.bucketAggs,
};

local block_orders = graphPanel.new(
  title='Ενέργεια Εντολών Πακέτου',
  description='Ενέργεια Εντολών Πακέτου',
  datasource=ds,
  format='kwatth',
  decimals=2,
  legend_alignAsTable=false,
  lines=true,
  fill=0,
  linewidth=1,
  shared_tooltip=true,
  value_type='individual',
).addTarget(block_orders_target);

local energy_quatity_row = row.new(
    title='Ποσότητες Ενέργειας',
    showTitle=true,
);

local block_orders_dash = dashboard.new(
  title='Εντολές Πακέτου',
  editable=false,
  timezone='browser',
  time_from='now-1y',
  time_to='now',
  schemaVersion=36,
  graphTooltip='shared_tooltip',
  tags=['grizzly'],
)
.addTemplate(
  template.interval(
    name='interval',
    hide='all',
    auto_min='30s',
    query='auto,1m,2m,5m,10m,20m',
    current='auto',
  )
)
.addPanel(
  energy_quatity_row,
  gridPos={'x':0, 'y':0, 'w':24, 'h':1}
)
.addPanel(
  block_orders,
  gridPos={'x':0, 'y':1, 'w':12, 'h':9}
);

{
  grafanaDashboards:: {
    'block_orders': block_orders_dash,
  },
  grafanaDashboardFolder:: 'PP',
}
