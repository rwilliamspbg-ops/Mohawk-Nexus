FROM golang:1.26.1 AS builder
WORKDIR /src
# Copy only the SMIP-MWP submodule contents into the build context
COPY SMIP-MWP /src/SMIP-MWP
WORKDIR /src/SMIP-MWP
ENV CGO_ENABLED=1
RUN go mod download
RUN go build -o /out/mohawk-node ./cmd/mohawk-node

FROM debian:bookworm-slim
COPY --from=builder /out/mohawk-node /usr/local/bin/mohawk-node
WORKDIR /app
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/mohawk-node"]
