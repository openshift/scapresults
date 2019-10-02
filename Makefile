.PHONY: image
image:
	podman build -f Dockerfile -t scapresults-k8s:latest
