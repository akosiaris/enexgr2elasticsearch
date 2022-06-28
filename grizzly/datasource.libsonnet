{
  datasource(
    name,
    user,
    password,
    timeField,
    timeInterval,
    url='http://elasticsearch:9200',
    ):: {
    apiVersion: 'grizzly.grafana.com/v1alpha1',
    kind: 'Datasource',
    metadata: {
        name: name,
    },
    spec: {
        access: 'proxy',
        basicAuth: true,
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
        readOnly: false,
        secureJsonData: {
            basicAuthPassword: password,
        },
        type: 'elasticsearch',
        typeLogoUrl: '',
        url: url,
        user: '',
        withCredentials: false,
     },
  },
}
