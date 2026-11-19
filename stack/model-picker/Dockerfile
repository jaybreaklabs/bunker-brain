# syntax=docker/dockerfile:1
FROM --platform=$BUILDPLATFORM node:22-bookworm AS frontend
WORKDIR /src
ADD https://github.com/open-webui/open-webui.git#b0e6098e940942281d9c83f3529ea117287a3a22 .
RUN npm ci --force --ignore-scripts --no-audit --no-fund
COPY open-webui.patch /tmp/open-webui.patch
RUN git apply /tmp/open-webui.patch
COPY picker.mjs src/lib/components/chat/ModelSelector/picker.mjs
# The runtime image already contains the matching Pyodide packages.
RUN npm run crypto:verify && \
    APP_BUILD_HASH=$(cat /tmp/open-webui.patch src/lib/components/chat/ModelSelector/picker.mjs | sha256sum | cut -d' ' -f1) \
    node --max-old-space-size=6144 node_modules/vite/bin/vite.js build

FROM ghcr.io/open-webui/open-webui:v0.13.3
COPY --from=frontend /src/build/_app/ /app/build/_app/
COPY --from=frontend /src/build/index.html /app/build/index.html
COPY --from=frontend /src/backend/open_webui/main.py /app/backend/open_webui/main.py
COPY --from=frontend /src/backend/open_webui/utils/models.py /app/backend/open_webui/utils/models.py
