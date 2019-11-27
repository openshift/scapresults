scapresults
===========

This is deployed as a workload for the 
[compliance-operator](https://github.com/openshift/compliance-operator/), and
is used in order to collect the logs of the OpenSCAP checks for the nodes in
the cluster.

This is a small script that uploads a file to a ConfigMap, optionally gzipping
it to fit within the etc 1MB file limit.

TODO
====

- [ ] Handle duplicated ConfigMaps: What happens when the ConfigMap that this
  tool is trying to create already exists? Should it overwrite, ignore or fail?

- [ ] Lock down the container
