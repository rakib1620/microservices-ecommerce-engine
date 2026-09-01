FROM nginx:1.27-alpine

# Patch OS-level packages to their latest available fixed versions.
# Base image tags can lag behind newly discovered CVEs even within
# the same nginx version — this keeps the image current.
RUN apk update && apk upgrade --no-cache

# Remove default nginx static content and config
RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf

# Copy our config and static site
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    # Run as non-root — nginx:alpine already ships an 'nginx' user
    && chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/run \
    && touch /var/run/nginx.pid \
    && chown nginx:nginx /var/run/nginx.pid

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s
