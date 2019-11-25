FROM registry.access.redhat.com/ubi8/ubi

USER root

# build scapresults-k8s
COPY scapresults /usr/local/bin/scapresults

ENTRYPOINT ["/usr/local/bin/scapresults"]
