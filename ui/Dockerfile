# Build React UI
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html vite.config.js ./
COPY src ./src
RUN npm run build

# Serve with nginx and proxy /api to FastAPI
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# Nginx config to proxy /api -> api:8000 (Docker service name)
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
