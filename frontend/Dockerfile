# ── Build stage ───────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm i
COPY . .
RUN npm run build

# ── Serve stage ───────────────────────────────────────────────
FROM nginx:1.27-alpine

# Copy React build
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx template — NOTE: stored as .template so nginx does NOT load it directly.
# Our entrypoint runs envsubst to produce the real default.conf at container start.
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Default — overridable at runtime via -e BACKEND_URL=http://...
# In K8s Phase 1 (same node):  http://backend:5000   (ClusterIP Service name)
# In docker-compose:            http://backend:5000   (service name)
# For local testing standalone: http://host.docker.internal:5000
ENV BACKEND_URL=http://backend:5000

EXPOSE 80

# nginx official image automatically runs envsubst on /etc/nginx/templates/*.template
# and writes the result to /etc/nginx/conf.d/ — no custom script needed.
CMD ["nginx", "-g", "daemon off;"]