FROM golang:1.27.2-bookworm AS builder
WORKDIR /src
# Copy only the SMIP-MWP submodule contents into the build context
COPY SMIP-MWP /src/SMIP-MWP
WORKDIR /src/SMIP-MWP
# SMIP-MWP/go.mod declares `go 1.27.2`. Pin the toolchain explicitly rather
# than inheriting GOTOOLCHAIN=local from the build environment, which would
# refuse to compile a module requiring a newer Go than the base image ships.
# bookworm (not alpine) because CGO_ENABLED=1 below needs gcc, and the final
# stage is already debian-based.
ENV CGO_ENABLED=1
ENV GOTOOLCHAIN=go1.27.2
RUN go mod download
RUN go build -o /out/mohawk-node ./cmd/mohawk-node

FROM debian:bookworm-slim
COPY --from=builder /out/mohawk-node /usr/local/bin/mohawk-node
WORKDIR /app
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/mohawk-node"]
