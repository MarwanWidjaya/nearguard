"""NearGuard -- counterparty check service for agents that pay.

Phase 1: read-only on-chain signals + local blocklist/history, a scoring
service, and an enforcing wrapper with a dry-run signer. See DESIGN.md.
"""

__all__ = ["rpc", "store", "signals", "service", "wrapper", "cli"]
