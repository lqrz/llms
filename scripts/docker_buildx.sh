docker buildx build \
  --load \
  --builder colima \
  --platform linux/amd64 \
  -f ../container/Dockerfile.backend \
  -t llms:$(date +%Y%m%d%H%M%S) \
  ..

docker buildx build \
  --load \
  --builder colima \
  --platform linux/amd64 \
  -f ../container/Dockerfile.frontend \
  -t llms:$(date +%Y%m%d%H%M%S) \
  ..

