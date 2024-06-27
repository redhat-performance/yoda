## Build
```
## Build the image
podman build -f Containerfile -t=YOUR_IMAGE_TAG .

## Push the image
podman push YOUR_IMAGE_TAG
```

## Deploy on openshift AI cluster
```
## Change to assets directory
cd assets

## Cleanup if resources already exist
kustomize build . | envsubst | oc delete -f -

## Deploy resources
export HF_TOKEN="YOUR_TOKEN"
export VQA_IMAGE="YOUR_IMAGE_TAG"
kustomize build . | envsubst | oc apply -f -
```