# =======================
# Project : BeeScout
# File    : nginx/Dockerfile
# Function: Reverse proxy & security gateway
# =======================
FROM nginx:1.27-alpine

# Remove the default catch-all server block
RUN rm /etc/nginx/conf.d/default.conf

# Copy template files — the official nginx image processes these automatically
# via envsubst on container start, outputting to /etc/nginx/conf.d/
COPY templates/ /etc/nginx/templates/
