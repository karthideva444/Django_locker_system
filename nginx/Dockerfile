FROM jkilbride/nginx-alpine

RUN apk add --update --no-cache \
    bash \
    curl

RUN rm -v /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/nginx.conf
