scapresults-k8s
===============

This is a small script that uploads a file to a configMap, optionally gzipping
it to fit within the etc 1MB file limit.

Normally one would deploy this as a sidecar in a pod, where this container would
wait until a results file exists, then upload it.

The script was very heavily inspired by 
[github.com/JAORMX/selinux-k8s](https://github.com/JAORMX/selinux-k8s).

TODO
====

- [ ] Handle duplicated ConfigMaps: What happens when the ConfigMap that this
  tool is trying to create already exists? Should it overwrite, ignore or fail?

- [ ] Use UBI as a base, not fedora

- [ ] Lock down the container
