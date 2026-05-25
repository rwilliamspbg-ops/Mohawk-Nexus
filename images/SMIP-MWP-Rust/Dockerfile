FROM rust:1.95-bullseye AS builder
WORKDIR /src
COPY SMIP-MWP-Rust /src/SMIP-MWP-Rust
WORKDIR /src/SMIP-MWP-Rust
RUN cargo build --release --workspace

FROM debian:bookworm-slim
# The built binary is named `mohawk-node` in target/release
COPY --from=builder /src/SMIP-MWP-Rust/target/release/mohawk-node /usr/local/bin/mohawk-node-rust
WORKDIR /app
ENTRYPOINT ["/usr/local/bin/mohawk-node-rust"]
