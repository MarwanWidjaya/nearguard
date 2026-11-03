"""Agent-side wrapper: the enforcement point between an agent and its signer.

The agent (or a prompt-injected instruction inside it) proposes a payment;
the wrapper asks the check service first and enforces the verdict:

  block -> refused. The signer is never invoked.
  warn  -> paused. "NEEDS HUMAN" is printed with the reasons; nothing signs.
  allow -> handed to the signer.

Phase 1 ships only DryRunSigner: it logs the would-be transaction and sends
nothing. There are no keys in phase 1 by design.

Phase-2 signing design (see DESIGN.md): the real signer will hold ONLY a
function-call access key scoped to one receiver contract, an allowlist of
method names, and a finite allowance. An account holding only function-call
keys cannot transfer NEAR or manage keys, so a compromised agent cannot
drain the account -- and plain transfers are impossible with such a key,
which forces payments through the one owner-approved contract path.
"""

import json

from . import service, store


class DryRunSigner:
    """Stands in for a real signer; records the intent, sends nothing."""

    def sign_and_send(self, intent):
        return {"status": "dry_run_signed", "would_send": intent,
                "note": "phase 1: no keys, nothing was broadcast"}


class FunctionCallKeySigner:
    """Phase-2 placeholder. Will sign with a function-call access key only.

    Deliberately unimplemented: creating keys/accounts is a human action
    that happens outside this codebase's phase-1 scope.
    """

    def sign_and_send(self, intent):
        raise NotImplementedError(
            "phase 2: sign with a function-call key scoped to one contract")


def propose_payment(agent_id, receiver_id, amount_near, network="mainnet",
                    signer=None, log=print):
    """Run one proposed payment through the guard. Returns a result dict."""
    signer = signer or DryRunSigner()
    intent = {"agent": agent_id, "receiver": receiver_id,
              "amount_near": str(amount_near), "network": network}
    log(f"[wrapper] proposed payment: {json.dumps(intent)}")

    result = service.check(agent_id, receiver_id, network)
    log(f"[guard] verdict={result['verdict']} score={result['score']} "
        f"reasons={result['reasons']}")

    if result["verdict"] == "block":
        log("[wrapper] REFUSED -- signer never invoked")
        return {"status": "refused", "intent": intent, "check": result}
    if result["verdict"] == "warn":
        log("[wrapper] NEEDS HUMAN -- paused, nothing signed")
        return {"status": "needs_human", "intent": intent, "check": result}

    sent = signer.sign_and_send(intent)
    store.record_interaction(agent_id, receiver_id, amount_near)
    log(f"[wrapper] allowed -> signer: {sent['status']}")
    return {"status": sent["status"], "intent": intent, "check": result,
            "signer_result": sent}
