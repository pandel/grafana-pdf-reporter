# Build stage
FROM node:23-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM nginx:stable-alpine AS production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy startup scripts
WORKDIR /
COPY 90-customize_env.sh /docker-entrypoint.d/ 
COPY generate_env-config.sh .
RUN chmod 777 /docker-entrypoint.d/90-customize_env.sh generate_env-config.sh

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
