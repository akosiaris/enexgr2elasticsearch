local grafana = import 'grafonnet-lib/grafonnet/grafana.libsonnet';
local dashboard = grafana.dashboard;
local row = grafana.row;
local template = grafana.template;
local graphPanel = grafana.graphPanel;

local ds = {
  type: 'elasticsearch',
  uid: 'enexgr_electricity_market_block_orders',
};

local shared_target = grafana.elasticsearch.target(
  query='',
  timeField='DELIVERY_MTU',
  bucketAggs=[
    {
      id: '2',
      field: 'DELIVERY_MTU',
      type: 'date_histogram',
      settings: {
        interval: 'auto',
        min_doc_count: '0',
        trimEdges: '0',
        timeZone: 'Europe/Athens',
      },
    },
  ],
);

local total_quantity_side_target = shared_target {
  alias: '{{term SIDE_DESCR}}',
  metrics: [
    { id: '1', field: 'TOTAL_QUANTITY', type: 'sum', settings: { script: '_value*1000' } },
  ],
  // Doing a trick here to ensure proper order
  bucketAggs: [
    {
      id: '4',
      field: 'SIDE_DESCR',
      type: 'terms',
      settings: {
        order: 'desc',
        orderBy: '_term',
        min_doc_count: '1',
        size: '0',
      },
    },
  ] + shared_target.bucketAggs,
};

local total_quantity_category_target = shared_target {
  alias: '{{term CLASSIFICATION}}',
  metrics: [
    { id: '1', field: 'TOTAL_QUANTITY', type: 'sum', settings: { script: '_value*1000' } },
  ],
  // For some reason there are lines with 0 TOTAL_QUANTITY (and they are buy side too, weird)
  query: 'TOTAL_QUANTITY:>0',
  // Doing a trick here to ensure proper order
  bucketAggs: [
    {
      id: '4',
      field: 'CLASSIFICATION',
      type: 'terms',
      settings: {
        order: 'desc',
        orderBy: '_term',
        min_doc_count: '1',
        size: '0',
      },
    },
  ] + shared_target.bucketAggs,
};

local matched_quantity_side_target = total_quantity_side_target {
  metrics: [
    { id: '1', field: 'MATCHED_QUANTITY', type: 'sum', settings: { script: '_value*1000' } },
  ],
};

local matched_quantity_category_target = total_quantity_category_target {
  metrics: [
    { id: '1', field: 'MATCHED_QUANTITY', type: 'sum', settings: { script: '_value*1000' } },
  ],
};

local total_quantity_side = graphPanel.new(
  title='Συνολική Ενέργεια Εντολών Πακέτου ανά πλευρά',
  description='Συνολική Ενέργεια Εντολών Πακέτου ανά πλευρά',
  datasource=ds,
  format='kwatth',
  decimals=2,
  legend_alignAsTable=false,
  lines=true,
  fill=0,
  linewidth=1,
  shared_tooltip=true,
  value_type='individual',
).addTarget(total_quantity_side_target);

local total_quantity_category = graphPanel.new(
  title='Συνολική Ενέργεια Εντολών Πακέτου ανά κατηγορία',
  description='Συνολική Ενέργεια Εντολών Πακέτου ανά κατηγορία',
  datasource=ds,
  format='kwatth',
  decimals=2,
  legend_alignAsTable=false,
  lines=true,
  fill=0,
  linewidth=1,
  shared_tooltip=true,
  value_type='individual',
).addTarget(total_quantity_category_target);

local matched_quantity_side = graphPanel.new(
  title='Ενέργεια Εκπληρωμένων Εντολών Πακέτου ανά πλευρά',
  description='Ενέργεια Εκπληρωμένων Εντολών Πακέτου ανά πλευρά',
  datasource=ds,
  format='kwatth',
  decimals=2,
  legend_alignAsTable=false,
  lines=true,
  fill=0,
  linewidth=1,
  shared_tooltip=true,
  value_type='individual',
).addTarget(matched_quantity_side_target);

local matched_quantity_category = graphPanel.new(
  title='Ενέργεια Εκπληρωμένων Εντολών Πακέτου ανά κατηγορία',
  description='Ενέργεια Εκπληρωμένων Εντολών Πακέτου ανά κατηγορία',
  datasource=ds,
  format='kwatth',
  decimals=2,
  legend_alignAsTable=false,
  lines=true,
  fill=0,
  linewidth=1,
  shared_tooltip=true,
  value_type='individual',
).addTarget(matched_quantity_category_target);

local quantity_row = row.new(
  title='Ποσότητες Ενέργειας',
  showTitle=true,
);

local count_row = row.new(
  title='Πλήθη',
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
    query='auto,1h,1d,1w,1M',
    current='auto',
  )
)
                          .addPanel(
  quantity_row,
  gridPos={ x: 0, y: 0, w: 24, h: 1 }
)
                          .addPanel(
  total_quantity_side,
  gridPos={ x: 0, y: 1, w: 12, h: 9 }
)
                          .addPanel(
  total_quantity_category,
  gridPos={ x: 12, y: 1, w: 12, h: 9 }
)
                          .addPanel(
  matched_quantity_side,
  gridPos={ x: 0, y: 10, w: 12, h: 9 }
)
                          .addPanel(
  matched_quantity_category,
  gridPos={ x: 12, y: 10, w: 12, h: 9 }
);

{
  grafanaDashboards:: {
    block_orders: block_orders_dash,
  },
  grafanaDashboardFolder:: 'PP',
}
