FROM golang:1.23.6-bookworm AS build
ARG MINIO_VERSION=RELEASE.2025-02-07T23-21-09Z
WORKDIR /src
RUN curl -fSL --retry 3 "https://codeload.github.com/minio/minio/tar.gz/refs/tags/${MINIO_VERSION}" -o /tmp/minio.tar.gz && tar -xzf /tmp/minio.tar.gz --strip-components=1 -C /src
RUN CGO_ENABLED=0 go build -trimpath -o /minio .

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl && rm -rf /var/lib/apt/lists/*
COPY --from=build /minio /usr/local/bin/minio
COPY --from=build /src/LICENSE /licenses/MINIO-LICENSE
ENTRYPOINT ["minio"]
