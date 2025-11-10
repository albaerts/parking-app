# Frontend multi-stage Dockerfile: build React app and serve with nginx

# Build stage
FROM node:18-alpine AS build
WORKDIR /app
ARG COMMIT_SHA=dev
ENV REACT_APP_COMMIT_SHA=$COMMIT_SHA
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# Production stage
FROM nginx:stable-alpine
COPY --from=build /app/build /usr/share/nginx/html
# Bake commit version marker into the image for easy verification
ARG COMMIT_SHA=dev
RUN echo "$COMMIT_SHA" > /usr/share/nginx/html/version.txt
# default nginx config is fine for a SPA that uses client-side routing (try_files already in default image)
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
