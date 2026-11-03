"""Minimal read-only JSON-RPC client for NEAR public endpoints.

Endpoints are the official public ones (docs.near.org/api/rpc/providers),
live-verified 2026-11-03. Only read methods are implemented: `query`
(view_account / view_code) and `block`. There is no transaction support
anywhere in this project -- phase 1 never signs or sends anything.
"""

import random
import time

import requests

ENDPOINTS = {
    "mainnet": {
        "rpc": "https://rpc.mainnet.near.org",
        "archival": "https://archival-rpc.mainnet.near.org",
    },
    "testnet": {
        "rpc": "https://rpc.testnet.near.org",
        "archival": "https://archival-rpc.testnet.near.org",
    },
}

TIMEOUT_SECONDS = 20

# The archival endpoint is officially "severely rate limited" (docs.near.org),
# and a single transient failure used to null out the whole age signal.
# Archival queries therefore get a bounded retry: at most ARCHIVAL_ATTEMPTS
# tries with exponential backoff + jitter. Definitive answers (success, or
# UNKNOWN_ACCOUNT) are never retried. If every attempt fails, the RpcError
# propagates and the caller keeps its honest "unknown" (None) behaviour.
ARCHIVAL_ATTEMPTS = 3
ARCHIVAL_BACKOFF_BASE = 1.5  # seconds; attempt n waits base * 2**n + jitter


class RpcError(Exception):
    """Transport failure or a JSON-RPC error that is not a known cause."""

    def __init__(self, message, cause_name=None):
        super().__init__(message)
        self.cause_name = cause_name


class UnknownAccount(RpcError):
    """The queried account does not exist (at the queried height)."""


def _post(url, method, params):
    try:
        resp = requests.post(
            url,
            json={"jsonrpc": "2.0", "id": "nearguard", "method": method, "params": params},
            timeout=TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        body = resp.json()
    except requests.RequestException as exc:
        raise RpcError(f"RPC transport failure ({url}): {exc}") from exc
    if "error" in body:
        err = body["error"]
        cause = (err.get("cause") or {}).get("name")
        if cause == "UNKNOWN_ACCOUNT":
            raise UnknownAccount(err.get("data") or "account does not exist", cause)
        raise RpcError(err.get("data") or str(err), cause)
    return body["result"]


class NearRpc:
    def __init__(self, network="mainnet"):
        if network not in ENDPOINTS:
            raise ValueError(f"unknown network: {network!r}")
        self.network = network
        self.urls = ENDPOINTS[network]

    def latest_height(self):
        """Height of the latest final block (via the `block` method)."""
        result = _post(self.urls["rpc"], "block", {"finality": "final"})
        return result["header"]["height"]

    def view_account(self, account_id, block_id=None):
        """Account state now (finality=final) or at a historical height.

        Historical queries go to the archival endpoint; regular nodes answer
        GARBAGE_COLLECTED_BLOCK for old heights. Raises UnknownAccount if the
        account did not exist at that point.
        """
        if block_id is None:
            params = {"request_type": "view_account", "finality": "final",
                      "account_id": account_id}
            return _post(self.urls["rpc"], "query", params)
        params = {"request_type": "view_account", "block_id": block_id,
                  "account_id": account_id}
        last_error = None
        for attempt in range(ARCHIVAL_ATTEMPTS):
            try:
                return _post(self.urls["archival"], "query", params)
            except UnknownAccount:
                raise  # a definitive answer, not a transient failure
            except RpcError as exc:
                last_error = exc
                if attempt + 1 < ARCHIVAL_ATTEMPTS:
                    delay = (ARCHIVAL_BACKOFF_BASE * 2 ** attempt
                             + random.uniform(0, 1.0))
                    time.sleep(delay)
        raise last_error

    def view_code_hash(self, account_id):
        """Current contract code hash, or None if the account has no contract.

        Raises UnknownAccount if the account itself does not exist.
        """
        params = {"request_type": "view_code", "finality": "final",
                  "account_id": account_id}
        try:
            result = _post(self.urls["rpc"], "query", params)
        except RpcError as exc:
            if exc.cause_name == "NO_CONTRACT_CODE":
                return None
            raise
        return result["hash"]
