GO=GOFLAGS=-mod=vendor GO111MODULE=auto go
PKGS=github.com/openshift/scapresults/cmd/scapresults
APP_NAME=scapresults
NAMESPACE?=openshift-compliance

# Container image variables
# =========================
IMAGE_REPO?=quay.io/jhrozek
IMAGE_TAG?=latest
# Image path to use. Set this if you want to use a specific path for building
# or your e2e tests. This is overwritten if we bulid the image and push it to
# the cluster or if we're on CI.
IMAGE_PATH?=$(IMAGE_REPO)/$(APP_NAME)
RUNTIME?=podman

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
	@$(GO) run github.com/securego/gosec/cmd/gosec -severity medium -confidence medium -quiet $(PKGS)

.PHONY: build
build:
	$(GO) build -o scapresults cmd/scapresults/main.go

.PHONY: image
image:
	podman build -f Dockerfile -t $(IMAGE_PATH):$(IMAGE_TAG)


# This checks if we're in a CI environment by checking the IMAGE_FORMAT
# environmnet variable. if we are, lets ues the image from CI and use this
# operator as the component.
#
# The IMAGE_FORMAT variable comes from CI. It is of the format:
#     <image path in CI registry>:${component}
# Here define the `component` variable, so, when we overwrite the
# IMAGE_PATH variable, it'll expand to the component we need.
.PHONY: check-if-ci
check-if-ci:
ifdef IMAGE_FORMAT
	@echo "IMAGE_FORMAT variable detected. We're in a CI enviornment."
	$(eval component = $(APP_NAME))
	$(eval IMAGE_PATH = $(IMAGE_FORMAT))
else
	@echo "IMAGE_FORMAT variable missing. We're in local enviornment."
endif

# If IMAGE_FORMAT is not defined, it means that we're not running on CI, so we
# probably want to push the compliance-operator image to the cluster we're
# developing on. This target exposes temporarily the image registry, pushes the
# image, and remove the route in the end.
.PHONY: image-to-cluster
ifdef IMAGE_FORMAT
image-to-cluster:
	@echo "We're in a CI environment, skipping image-to-cluster target."
else
image-to-cluster: namespace openshift-user image
	@echo "Temporarily exposing the default route to the image registry"
	@oc patch configs.imageregistry.operator.openshift.io/cluster --patch '{"spec":{"defaultRoute":true}}' --type=merge
	@echo "Pushing image $(IMAGE_PATH):$(IMAGE_TAG) to the image registry"
	IMAGE_REGISTRY_HOST=$$(oc get route default-route -n openshift-image-registry --template='{{ .spec.host }}'); \
		$(RUNTIME) login --tls-verify=false -u $(OPENSHIFT_USER) -p $(shell oc whoami -t) $${IMAGE_REGISTRY_HOST}; \
		$(RUNTIME) push --tls-verify=false $(IMAGE_PATH):$(IMAGE_TAG) $${IMAGE_REGISTRY_HOST}/$(NAMESPACE)/$(APP_NAME):$(IMAGE_TAG)
	@echo "Removing the route from the image registry"
	@oc patch configs.imageregistry.operator.openshift.io/cluster --patch '{"spec":{"defaultRoute":false}}' --type=merge
	$(eval IMAGE_PATH = image-registry.openshift-image-registry.svc:5000/$(NAMESPACE)/$(APP_NAME):$(TAG))
endif

.PHONY: namespace
namespace:
	@echo "Creating '$(NAMESPACE)' namespace/project"
	@oc create namespace $(NAMESPACE) || true

.PHONY: openshift-user
openshift-user:
ifeq ($(shell oc whoami 2> /dev/null),kube:admin)
	$(eval OPENSHIFT_USER = kubeadmin)
else
	$(eval OPENSHIFT_USER = $(oc whoami))
endif
