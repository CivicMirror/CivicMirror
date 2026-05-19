# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --prefer-offline
COPY . .
ARG VITE_API_URL=https://api.civicmirror.welshrd.com
ENV VITE_API_URL=$VITE_API_URL
ARG VITE_CIVIC_API_URL=https://civicmirror-backend-866677508588.us-central1.run.app
ENV VITE_CIVIC_API_URL=$VITE_CIVIC_API_URL
ARG VITE_CIVIC_API_KEY=
ENV VITE_CIVIC_API_KEY=$VITE_CIVIC_API_KEY
RUN npm run build

# ── Stage 2: Serve with nginx ─────────────────────────────────────────────────
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
