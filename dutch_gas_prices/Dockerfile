#https://github.com/hassio-addons/addon-base-python/pkgs/container/base-python%2Farmv7
ARG BUILD_FROM=ghcr.io/hassio-addons/base-python/amd64:11.0.4
FROM ${BUILD_FROM}

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Setup base system
ARG BUILD_ARCH=amd64

#copy the app
COPY rootfs/app /app
COPY rootfs/run.sh /

#install packages
RUN \
    apk add --no-cache --virtual .build-dependencies \
        tesseract-ocr \
        tesseract-ocr-dev \
        jpeg-dev \
        libjpeg \
        zlib-dev \
        gcc \
        libc-dev

#infra
RUN \
        mkdir -p /app \
        && mkdir -p /app/cache

#pillow
RUN \
         pip3 install Pillow

#requirements
RUN \
        pip3 install requests \
        requests[socks] \
        requests[security] \
        fake_headers \
        pytesseract \
        geopy \
        jsonschema \
        paho-mqtt

#copy traineddata
COPY rootfs/traineddata /usr/share/tessdata

#make it run
RUN \
        chmod a+x /run.sh

WORKDIR /app/
CMD [ "/run.sh" ]

# Build arguments
ARG BUILD_ARCH
ARG BUILD_DATE
ARG BUILD_DESCRIPTION
ARG BUILD_NAME
ARG BUILD_REF
ARG BUILD_REPOSITORY
ARG BUILD_VERSION

# Labels
LABEL \
    io.hass.name="${BUILD_NAME}" \
    io.hass.description="${BUILD_DESCRIPTION}" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
    maintainer="Kevin Temming" \
    org.opencontainers.image.title="${BUILD_NAME}" \
    org.opencontainers.image.description="${BUILD_DESCRIPTION}" \
    org.opencontainers.image.authors="Kevin Temming" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://addons.community" \
    org.opencontainers.image.source="https://github.com/${BUILD_REPOSITORY}" \
    org.opencontainers.image.documentation="https://github.com/${BUILD_REPOSITORY}/blob/main/README.md" \
    org.opencontainers.image.created=${BUILD_DATE} \
    org.opencontainers.image.revision=${BUILD_REF} \
    org.opencontainers.image.version=${BUILD_VERSION}