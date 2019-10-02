FROM fedora

USER root

# script dependencies
RUN dnf -y install \
        python3-kubernetes \
    && rm -rf /var/cache/yum

# build scapresults-k8s
WORKDIR /tmp
COPY scapresults/ scapresults/scapresults/
COPY setup.py scapresults/
WORKDIR /tmp/scapresults
RUN python3 setup.py install
WORKDIR /

# Clean up
RUN rm -rf /tmp/scapresults/

ENTRYPOINT ["/usr/local/bin/scapresults"]
