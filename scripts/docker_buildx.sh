docker buildx build \
  --load \
  --builder colima \
  --platform linux/amd64 \
  -f ../container/Dockerfile.backend \
  -t llms/backend:$(date +%Y%m%d%H%M%S) \
  ..

docker buildx build \
  --load \
  --builder colima \
  --platform linux/amd64 \
  -f ../container/Dockerfile.frontend \
  -t llms/frontend:$(date +%Y%m%d%H%M%S) \
  ..

