"""Scoring: turn a signal set into a verdict.

Verdicts: "allow" / "warn" / "block". Rules are deliberately transparent --
every point is returned in `reasons` so the decision can be audited from the
log alone. See DESIGN.md for the full rule table and rationale.
"""

from .signals import collect_signals

BLOCK_THRESHOLD = 50
WARN_THRESHOLD = 25
DUST_BALANCE_NEAR = 0.1


def evaluate(signals):
    reasons = []
    score = 0

    # Hard overrides first.
    if signals.get("blocklisted"):
        entry = signals.get("blocklist_entry") or {}
        reasons.append(
            f"BLOCKLISTED: {entry.get('reason', 'reported')} "
            f"(evidence: {entry.get('evidence', 'n/a')}, "
            f"reported by {entry.get('reported_by', 'unknown')})")
        return {"verdict": "block", "score": 100, "reasons": reasons,
                "signals": signals}
    if signals.get("exists") is False:
        reasons.append("account does not exist on this network")
        return {"verdict": "block", "score": 100, "reasons": reasons,
                "signals": signals}
    if signals.get("exists") is None:
        reasons.append(
            "on-chain signals unavailable (RPC unreachable) -- cannot verify")
        return {"verdict": "warn", "score": WARN_THRESHOLD,
                "reasons": reasons, "signals": signals}

    # Scored signals.
    if signals.get("code_changed_recently"):
        score += 40
        reasons.append("contract code changed within the last ~90 days (+40)")
    age = signals.get("age_lower_bound_days")
    if age is not None:
        if age < 30:
            score += 35
            reasons.append("account is younger than ~30 days (+35)")
        elif age < 90:
            score += 15
            reasons.append("account age is only proven to ~30-90 days (+15)")
    if signals.get("first_interaction"):
        score += 20
        reasons.append("first interaction between this agent and receiver (+20)")
    if signals.get("is_contract"):
        score += 10
        reasons.append("receiver is a contract account (+10)")
    balance = signals.get("balance_near")
    if balance is not None and balance < DUST_BALANCE_NEAR:
        score += 5
        reasons.append("receiver balance is dust (< 0.1 NEAR) (+5)")

    if score >= BLOCK_THRESHOLD:
        verdict = "block"
    elif score >= WARN_THRESHOLD:
        verdict = "warn"
    else:
        verdict = "allow"
    if not reasons:
        reasons.append("no risk signals fired")
    return {"verdict": verdict, "score": score, "reasons": reasons,
            "signals": signals}


def check(agent_id, receiver_id, network="mainnet"):
    """Full check: collect signals for (agent, receiver) and score them."""
    return evaluate(collect_signals(agent_id, receiver_id, network))
