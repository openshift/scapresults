GO=GO111MODULE=on go
PKGS=$(shell go list ./... | grep -v -E '/vendor/|/test|/examples')

all: build

.PHONY: fmt
fmt:
	@$(GO) fmt $(PKGS)

.PHONY: verify
verify: vet mod-verify gosec

.PHONY: vet
vet:
	@$(GO) vet $(PKGS)

.PHONY: mod-verify
mod-verify:
	@$(GO) mod verify

.PHONY: gosec
gosec:
	@$(GO) run github.com/securego/gosec/cmd/gosec -severity medium -confidence medium -quiet ./...

.PHONY: build
build: fmt verify
	@$(GO) build -o scapresults cmd/scapresults/main.go

.PHONY: image
image:
	podman build -f Dockerfile -t scapresults-k8s:latest
