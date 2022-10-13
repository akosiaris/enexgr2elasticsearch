local grafana = import 'grafonnet-lib/grafonnet/grafana.libsonnet';
local dashboard = grafana.dashboard;
local row = grafana.row;
local template = grafana.template;
local graphPanel = grafana.graphPanel;

local ds = {
  type: 'elasticsearch',
  uid: 'enexgr_electricity_market_block_orders',
};

/* Some shared targets */
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

local side_shared_target = shared_target {
  alias: '{{term SIDE_DESCR}}',
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

local category_shared_target = shared_target {
  alias: '{{term CLASSIFICATION}}',
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

local total_quantity_shared_target = {
  metrics: [
    { id: '1', field: 'TOTAL_QUANTITY', type: 'sum', settings: { script: '_value*1000' } },
  ],
};

local matched_quantity_shared_target = {
  metrics: [
    { id: '1', field: 'MATCHED_QUANTITY', type: 'sum', settings: { script: '_value*1000' } },
  ],
};

local non_matched_quantity_shared_target = {
  metrics: [
    {
      id: '1',
      field: 'MATCHED_QUANTITY',
      hide: true,
      settings: {
        script: '_value * 1000',
      },
      type: 'sum',
    },
    {
      field: 'TOTAL_QUANTITY',
      hide: true,
      id: '3',
      settings: {
        script: '_value * 1000',
      },
      type: 'sum',
    },
    {
      id: '5',
      pipelineVariables: [
        {
          name: 'matched',
          pipelineAgg: '1',
        },
        {
          name: 'total',
          pipelineAgg: '3',
        },
      ],
      settings: {
        script: 'params.total - params.matched',
      },
      type: 'bucket_script',
    },
  ],
};

local total_orders_shared_target = {
  metrics: [
    { id: '1', field: 'TOTAL_ORDERS', type: 'sum', settings: { script: '_value*1000' } },
  ],
};

local matched_orders_shared_target = {
  metrics: [
    { id: '1', field: 'MATCHED_ORDERS', type: 'sum', settings: { script: '_value*1000' } },
  ],
};


local non_matched_orders_shared_target = {
  metrics: [
    {
      id: '1',
      field: 'MATCHED_ORDERS',
      hide: true,
      settings: {
        script: '_value * 1000',
      },
      type: 'sum',
    },
    {
      field: 'TOTAL_ORDERS',
      hide: true,
      id: '3',
      settings: {
        script: '_value * 1000',
      },
      type: 'sum',
    },
    {
      id: '5',
      pipelineVariables: [
        {
          name: 'matched',
          pipelineAgg: '1',
        },
        {
          name: 'total',
          pipelineAgg: '3',
        },
      ],
      settings: {
        script: 'params.total - params.matched',
      },
      type: 'bucket_script',
    },
  ],
};

/* Now the quantity targets */

local total_quantity_side_target = side_shared_target + total_quantity_shared_target;
local total_quantity_category_target = category_shared_target + total_quantity_shared_target + {
  // For some reason there are lines with 0 TOTAL_QUANTITY (and they are buy side too, weird)
  query: 'TOTAL_QUANTITY:>0',
};

local matched_quantity_side_target = side_shared_target + matched_quantity_shared_target;
local matched_quantity_category_target = category_shared_target + matched_quantity_shared_target + {
  // For some reason there are lines with 0 TOTAL_QUANTITY (and they are buy side too, weird)
  query: 'TOTAL_QUANTITY:>0',
};

local non_matched_quantity_side_target = side_shared_target + non_matched_quantity_shared_target;
local non_matched_quantity_category_target = category_shared_target + non_matched_quantity_shared_target + {
  // For some reason there are lines with 0 TOTAL_QUANTITY (and they are buy side too, weird)
  query: 'TOTAL_QUANTITY:>0',
};

/* Now the order targets */

local total_orders_side_target = side_shared_target + total_orders_shared_target;
local total_orders_category_target = category_shared_target + total_orders_shared_target + {
  // For some reason there are lines with 0 TOTAL_orders (and they are buy side too, weird)
  query: 'TOTAL_ORDERS:>0',
};

local matched_orders_side_target = side_shared_target + matched_orders_shared_target;
local matched_orders_category_target = category_shared_target + matched_orders_shared_target + {
  // For some reason there are lines with 0 TOTAL_orders (and they are buy side too, weird)
  query: 'TOTAL_ORDERS:>0',
};

local non_matched_orders_side_target = side_shared_target + non_matched_orders_shared_target;
local non_matched_orders_category_target = category_shared_target + non_matched_orders_shared_target + {
  // For some reason there are lines with 0 TOTAL_orders (and they are buy side too, weird)
  query: 'TOTAL_ORDERS:>0',
};

/* Finally the panels */

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

local non_matched_quantity_side = graphPanel.new(
  title='Ενέργεια Μη Εκπληρωμένων Εντολών Πακέτου ανά πλευρά',
  description='Ενέργεια Μη Εκπληρωμένων Εντολών Πακέτου ανά πλευρά',
  datasource=ds,
  format='kwatth',
  decimals=2,
  legend_alignAsTable=false,
  lines=true,
  fill=0,
  linewidth=1,
  shared_tooltip=true,
  value_type='individual',
).addTarget(non_matched_quantity_side_target);

local non_matched_quantity_category = graphPanel.new(
  title='Ενέργεια Μη Εκπληρωμένων Εντολών Πακέτου ανά κατηγορία',
  description='Ενέργεια Μη Εκπληρωμένων Εντολών Πακέτου ανά κατηγορία',
  datasource=ds,
  format='kwatth',
  decimals=2,
  legend_alignAsTable=false,
  lines=true,
  fill=0,
  linewidth=1,
  shared_tooltip=true,
  value_type='individual',
).addTarget(non_matched_quantity_category_target);

/* The order panels too */
local total_orders_side = graphPanel.new(
  title='Εντολές Πακέτου ανά πλευρά',
  description='Εντολές Πακέτου ανά πλευρά',
  datasource=ds,
  format='short',
  decimals=0,
  legend_alignAsTable=false,
  lines=true,
  fill=0,
  linewidth=1,
  shared_tooltip=true,
  value_type='individual',
).addTarget(total_orders_side_target);

local total_orders_category = graphPanel.new(
  title='Εντολές Πακέτου ανά κατηγορία',
  description='Εντολές Πακέτου ανά κατηγορία',
  datasource=ds,
  format='short',
  decimals=0,
  legend_alignAsTable=false,
  lines=true,
  fill=0,
  linewidth=1,
  shared_tooltip=true,
  value_type='individual',
).addTarget(total_orders_category_target);

local matched_orders_side = graphPanel.new(
  title='Εκπληρωμένες Εντολές Πακέτου ανά πλευρά',
  description='Εκπληρωμένες Εντολές Πακέτου ανά πλευρά',
  datasource=ds,
  format='short',
  decimals=0,
  legend_alignAsTable=false,
  lines=true,
  fill=0,
  linewidth=1,
  shared_tooltip=true,
  value_type='individual',
).addTarget(matched_orders_side_target);

local matched_orders_category = graphPanel.new(
  title='Εκπληρωμένες Εντολές Πακέτου ανά κατηγορία',
  description='Εκπληρωμένες Εντολές Πακέτου ανά κατηγορία',
  datasource=ds,
  format='short',
  decimals=0,
  legend_alignAsTable=false,
  lines=true,
  fill=0,
  linewidth=1,
  shared_tooltip=true,
  value_type='individual',
).addTarget(matched_orders_category_target);

local non_matched_orders_side = graphPanel.new(
  title='Μη Εκπληρωμένες Εντολές Πακέτου ανά πλευρά',
  description='Μη Εκπληρωμένες Εντολές Πακέτου ανά πλευρά',
  datasource=ds,
  format='short',
  decimals=0,
  legend_alignAsTable=false,
  lines=true,
  fill=0,
  linewidth=1,
  shared_tooltip=true,
  value_type='individual',
).addTarget(non_matched_orders_side_target);

local non_matched_orders_category = graphPanel.new(
  title='Μη Εκπληρωμένες Εντολές Πακέτου ανά κατηγορία',
  description='Μη Εκπληρωμένες Εντολές Πακέτου ανά κατηγορία',
  datasource=ds,
  format='short',
  decimals=0,
  legend_alignAsTable=false,
  lines=true,
  fill=0,
  linewidth=1,
  shared_tooltip=true,
  value_type='individual',
).addTarget(non_matched_orders_category_target);

/* Rows */
local quantity_row = row.new(
  title='Ποσότητες Ενέργειας',
  showTitle=true,
);

local orders_row = row.new(
  title='Πλήθη',
  showTitle=true,
);

/* And let's assemble finally the dashboard */
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
)
                          .addPanel(
  non_matched_quantity_side,
  gridPos={ x: 0, y: 19, w: 12, h: 9 }
)
                          .addPanel(
  non_matched_quantity_category,
  gridPos={ x: 12, y: 19, w: 12, h: 9 }
)
                          .addPanel(
  orders_row,
  gridPos={ x: 0, y: 28, w: 24, h: 1 }
)
                          .addPanel(
  total_orders_side,
  gridPos={ x: 0, y: 29, w: 12, h: 9 }
)
                          .addPanel(
  total_orders_category,
  gridPos={ x: 12, y: 29, w: 12, h: 9 }
)
                          .addPanel(
  matched_orders_side,
  gridPos={ x: 0, y: 38, w: 12, h: 9 }
)
                          .addPanel(
  matched_orders_category,
  gridPos={ x: 12, y: 38, w: 12, h: 9 }
)
                          .addPanel(
  non_matched_orders_side,
  gridPos={ x: 0, y: 47, w: 12, h: 9 }
)
                          .addPanel(
  non_matched_orders_category,
  gridPos={ x: 12, y: 47, w: 12, h: 9 }
);


{
  grafanaDashboards:: {
    block_orders: block_orders_dash,
  },
  grafanaDashboardFolder:: 'PP',
}
