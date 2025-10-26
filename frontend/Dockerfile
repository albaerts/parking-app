# Frontend multi-stage Dockerfile: build React app and serve with nginx

# Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# Production stage
FROM nginx:stable-alpine
COPY --from=build /app/build /usr/share/nginx/html
# default nginx config is fine for a SPA that uses client-side routing (try_files already in default image)
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
