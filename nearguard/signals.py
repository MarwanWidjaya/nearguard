"""Signal collection for one (agent, receiver) pair.

On-chain signals come from public NEAR RPC (see DESIGN.md for the exact call
behind each). Local signals come from the stores. If the RPC is unreachable,
on-chain signals degrade to "unavailable" instead of failing the check --
the service treats that as a reason to warn, never to silently allow.
"""

from . import store
from .rpc import NearRpc, RpcError, UnknownAccount

# NEAR produces ~1 block/sec; ages are reported as approximations (DESIGN.md).
BLOCKS_PER_DAY = 86_400
AGE_LADDER = [  # (label, approx days, blocks back from latest)
    ("30d", 30, 30 * BLOCKS_PER_DAY),
    ("90d", 90, 90 * BLOCKS_PER_DAY),
    ("365d", 365, 365 * BLOCKS_PER_DAY),
]
CODE_CHANGE_WINDOW = 90 * BLOCKS_PER_DAY  # ~90 days back


def _age_lower_bound_days(rpc, account_id, latest_height):
    """Largest ladder window the account provably existed at, else 0.

    Probes oldest-first is wasteful; probe newest-first and stop at the
    first UNKNOWN_ACCOUNT: existence at every older rung is then unproven,
    existence at every newer rung follows from the newest success... in
    practice we walk down the ladder and keep the deepest success.
    Returns None if the archival endpoint cannot answer at all.
    """
    proven = 0
    answered = False
    for _label, days, back in AGE_LADDER:
        height = latest_height - back
        if height <= 0:
            continue
        try:
            rpc.view_account(account_id, block_id=height)
            answered = True
            proven = days  # existed this far back; try the next, older rung
        except UnknownAccount:
            answered = True
            break  # did not exist yet at this height; older rungs are moot
        except RpcError:
            break  # archival unavailable / rate limited: keep what we have
    return proven if answered else None


def collect_signals(agent_id, receiver_id, network="mainnet"):
    signals = {"network": network, "receiver": receiver_id}

    # Local signals always evaluate.
    entry = store.blocklist_entry(receiver_id)
    signals["blocklisted"] = entry is not None
    signals["blocklist_entry"] = entry
    interaction = store.get_interaction(agent_id, receiver_id)
    signals["prior_interactions"] = interaction["count"] if interaction else 0
    signals["first_interaction"] = interaction is None

    # On-chain signals.
    rpc = NearRpc(network)
    try:
        account = rpc.view_account(receiver_id)
    except UnknownAccount:
        signals["exists"] = False
        return signals
    except RpcError as exc:
        signals["exists"] = None
        signals["rpc_error"] = str(exc)
        return signals

    signals["exists"] = True
    signals["balance_near"] = int(account["amount"]) / 10**24
    signals["storage_usage_bytes"] = account["storage_usage"]
    code_hash_now = account["code_hash"]

    try:
        signals["is_contract"] = rpc.view_code_hash(receiver_id) is not None
    except RpcError:
        signals["is_contract"] = None

    latest = account["block_height"]
    signals["code_changed_recently"] = None
    signals["age_lower_bound_days"] = None
    if signals.get("is_contract"):
        try:
            old = rpc.view_account(
                receiver_id, block_id=latest - CODE_CHANGE_WINDOW)
            signals["code_changed_recently"] = old["code_hash"] != code_hash_now
        except UnknownAccount:
            signals["code_changed_recently"] = True  # deployed within window
        except RpcError:
            pass  # stays None = unknown
    signals["age_lower_bound_days"] = _age_lower_bound_days(
        rpc, receiver_id, latest)
    return signals
