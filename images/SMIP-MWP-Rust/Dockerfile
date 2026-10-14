FROM rust:1.95-bullseye AS builder
WORKDIR /src
COPY SMIP-MWP-Rust /src/SMIP-MWP-Rust
WORKDIR /src/SMIP-MWP-Rust
# Upstream cli/src/main.rs already declares `let mut forwarder`, so the old
# in-image sed patch was a silent no-op. The build asserts it instead of
# quietly patching: a mutable borrow is required by process_batch(&mut ...).
RUN grep -q 'let mut forwarder' cli/src/main.rs
RUN cargo build --release --workspace

FROM debian:bookworm-slim
# The built binary is named `mohawk-node` in target/release
COPY --from=builder /src/SMIP-MWP-Rust/target/release/mohawk-node /usr/local/bin/mohawk-node-rust
WORKDIR /app
ENTRYPOINT ["/usr/local/bin/mohawk-node-rust"]
