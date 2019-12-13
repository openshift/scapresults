# Step one: build scapresults
FROM registry.access.redhat.com/ubi8/go-toolset as builder

ENV GOFLAGS=-mod=vendor
COPY . .
RUN make

# Step two: containerize scapresults
FROM registry.access.redhat.com/ubi8/ubi

USER root

# build scapresults
COPY --from=builder /opt/app-root/src/scapresults /usr/local/bin/scapresults

ENTRYPOINT ["/usr/local/bin/scapresults"]
