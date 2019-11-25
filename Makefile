.PHONY: build
build:
	go build -o scapresults cmd/scapresults/main.go

.PHONY: image
image: build
	podman build -f Dockerfile -t scapresults-k8s:latest
