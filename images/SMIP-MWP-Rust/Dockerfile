FROM rust:1.95-bullseye AS builder
WORKDIR /src
COPY SMIP-MWP-Rust /src/SMIP-MWP-Rust
WORKDIR /src/SMIP-MWP-Rust
# Apply a temporary in-image patch to fix mutable borrow error in cli main
# This avoids requiring a push to the external SMIP-MWP-Rust repo from CI
RUN sed -i 's/let forwarder =/let mut forwarder =/' cli/src/main.rs || true
RUN cargo build --release --workspace

FROM debian:bookworm-slim
# The built binary is named `mohawk-node` in target/release
COPY --from=builder /src/SMIP-MWP-Rust/target/release/mohawk-node /usr/local/bin/mohawk-node-rust
WORKDIR /app
ENTRYPOINT ["/usr/local/bin/mohawk-node-rust"]
