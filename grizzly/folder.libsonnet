{
  folder(
    name,
    uid,
    ):: {

    apiVersion: 'grizzly.grafana.com/v1alpha1',
    kind: 'DashboardFolder',
    metadata: {
	name: uid,
    },
    spec: {
	hasAcl: false,
	title: name,
    },
   },
}
