IMAGE=kubegentic-runtime
.PHONY: build
build:
	eval $(minikube docker-env)
	docker build --no-cache -t $(IMAGE) .