# Step one: build scapresults
FROM registry.access.redhat.com/ubi8/go-toolset as builder

COPY . .
RUN make

# Step two: containerize scapresults
FROM registry.access.redhat.com/ubi8/ubi

USER root

# build scapresults-k8s
COPY --from=builder /opt/app-root/src/scapresults /usr/local/bin/scapresults

ENTRYPOINT ["/usr/local/bin/scapresults"]
