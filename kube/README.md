# Kube integration

Want to run migrations as kubernetes jobs using automig so that you don't have to manually define `up` and `down` steps? You're in the right place.

The stuff in this folder should guide you through attaching automig to your git repo & kube cluster.

## This is a beta

This kube-based migration in production use at cloudprogress, but that doesn't mean that it's safe or ready for public consumption. Bear in mind:

1. Warts are to be expected, raise issues if these docs are incomplete / unclear / wrong
1. That being said, such support is not guaranteed
1. Loss of data or undesired extra data are among the many possible bad outcomes of using this

## Details

Prerequisites:

1. Be familiar with kustomize (the kube-native helm replacement)
1. Be using postgres -- the toolchain will need some tweaks to work with mysql

Initial setup:

1. Set up your repo to build a docker image for migration
	- add automig.Dockerfile to your project repo (it's named that way to avoid colliding with your existing `Dockerfile`)
	- add migrate.sh in the same folder
	- edit the `COPY schema schema/` line in automig.Dockerfile to the folder where you store your SQL schema file(s)
	- update your CI spec to write to your container registry (there's a sample .gitlab-ci.yml in this folder)
1. Wire up kustomize
	- in theory this will work whether or not you're currently using kustomize, but no promises
	- in kustomization.yml, edit `name` and `newTag` to match your image name
	- in migrate.yml, edit `image` to match your image name
	- still in migrate.yml, update the names of the secrets to match what you're using
		- `database-credentials` is a secret that has a postgres connection string (`postgres://` or whatever) in the libpq-url key
		- `regcred` has a dockerconfigjson for your container registry; you may not need this if your registry is integrated with your cloud host
1. in migrate.yml, update `AUTOMIG_GLOB` to whatever you're using. Note the weird quoting convention: `"'schema/*.sql'"` prevents your shell from resolving the star too early.
	- In fact this doesn't matter because kube doesn't execute through a shell, but migrate.sh uses `eval` to simulate a shell so it's compatible with both kube and laptop mode.
	- If you don't have a wildcard in your glob, the quoting shouldn't matter
1. Run kustomize to apply this to your cluster, fix / report any errors

Running your initial migration:

(Todo: add instructions for attaching automig to an existing database).

1. In migrate.yml, change the `--update` flag in the `command` to `--init`
1. In migrate.yml, change the value of the `TARGET` env var to the sha where you want your migration history to start
1. Run kustomize to apply this to your cluster
1. Run a copy of the migration job with: `kubectl create job mig-$(shell whoami)-$(shell date -u +%Y%m%d-%H%M) --from=cronjob/migrate`
1. Use `kubectl get job` and `kubectl logs job/whatever -f` to wait for success
1. **Important**: once this works, change `--init` back to `--update` and rerun kustomize

Running subsequent migrations:

1. In kustomize.yml, change `newTag` to your desired sha
1. In migrate.yml, change the value of `TARGET` to your desired sha (if you leave it out, it may be able to infer `HEAD`, but I'm not sure)
1. Run customize to apply this to your cluster
1. Run and watch the migration job with steps 4 & 5 above
