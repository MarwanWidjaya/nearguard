# NearGuard — hackathon submission text (DRAFT, not submitted)

Prepared for the NEAR Hackathon "Build Beyond Boundaries". This text has
not been submitted anywhere. It is the copy Marwan reviews and approves
before any submission form is filled in.

---

**Project name:** NearGuard

**Track:** AI Security & Defense (`security`)

**One-line summary:** A pre-signing counterparty check for AI agents that
pay on NEAR: every proposed payment is scored from public RPC data and a
local blocklist, and returned as `allow`, `warn`, or `block` with reasons
before anything is signed.

**Problem.** An AI agent holding a wallet pays whoever its context tells
it to pay. That context can be poisoned: a document, web page, or tool
result the agent reads during a legitimate job can contain an injected
instruction that redirects a payment to an attacker's account and tells
the agent to skip verification. A model cannot reliably distinguish an
injected instruction from a genuine one, so the payment decision cannot
rest on the prompt.

**Solution.** NearGuard takes the decision out of the prompt. An agent-side
wrapper intercepts every proposed payment and asks the check service
first. The service scores the receiver and returns a verdict with the
reason for every point. The wrapper enforces the verdict: on `block` the
signer is never invoked; on `warn` the payment pauses for a human
decision; on `allow` it proceeds to the signer.

**How it works.** Seven signals per (agent, receiver) pair:

- Blocklist membership — local shared list; reports require evidence.
- Account existence, contract status, and balance — public NEAR JSON-RPC
  (`view_account`, `view_code`).
- Contract code change within ~90 days and an account-age lower bound
  (~30 / ~90 / ~365-day ladder) — archival RPC, comparing historical
  account state. Ages are reported as proven lower bounds, not exact
  ages; NEAR block heights are converted at ≈86,400 blocks/day.
- Prior interactions between this agent and the receiver — local history.

Scoring is fixed and published in the repository: blocklist membership or
a non-existent receiver is an automatic `block`; risk points (code change
+40, account younger than ~30 days +35, first interaction +20, contract
+10, dust balance +5) map to verdicts at ≥50 `block`, 25–49 `warn`,
<25 `allow`. If the RPC cannot be reached, the verdict is at best `warn` —
a payment is never allowed on signals that could not be retrieved.

Signing is designed around function-call access keys only: one receiver
contract, an allowlist of method names, and a capped gas allowance. Such
a key cannot transfer NEAR or manage keys, so a leaked agent key cannot
drain the account. In this submission the real signer is a stub by
design; the shipped signer is a dry-run that logs intent and sends
nothing.

**What was tested** (recorded runs in `runs/` and `runs/phase2/` of the
repository):

| Test | Result |
|---|---|
| `check wrap.near` (mainnet, live RPC) | `allow`, score 10 — contract (+10); `code_changed_recently=false`; `age_lower_bound_days=365` |
| `check drain-vault.testnet` (testnet; fixture entry in the local blocklist) | `block`, score 100 — blocklist match |
| Attack demo, scene 1: prompt-injected instruction to pay the blocklisted account 5 NEAR, "skip verification" | Payment `refused`; signer never invoked (script asserts this and exits non-zero otherwise) |
| Attack demo, scene 2: agent with no history pays `wrap.near` | `warn`, score 30 (first interaction +20, contract +10); outcome `needs_human`, nothing signed |
| Attack demo, scene 3: agent with prior history pays `wrap.near` | `allow`, score 10; dry-run signer logs the intent, nothing broadcast |

**Data sources.** Public NEAR JSON-RPC only: `rpc.mainnet.near.org`,
`rpc.testnet.near.org`, `archival-rpc.mainnet.near.org`,
`archival-rpc.testnet.near.org` (official endpoints, per
docs.near.org/api/rpc/providers). No indexer is used. Archival queries
use a bounded retry (max 3 attempts, exponential backoff with jitter)
because the archival endpoint is rate-limited; a signal that still cannot
be retrieved stays unknown and scores no points.

**Limitations.**

- Age and activity signals are proxies. True transaction history and a
  first-seen timestamp require an indexer API; that is a TODO-VERIFY item
  for a later phase, not used here.
- The blocklist is a local JSON file. An on-chain registry contract that
  agents on different machines could share is planned, not built.
- No real signing. No accounts were created and no keys exist in this
  project; the function-call-key signer is an unimplemented stub, and key
  creation is a human step outside this codebase.
- The `warn` path pauses and reports; a human approval callback that
  releases a payment once is not built yet.

**Repository:** https://github.com/MarwanWidjaya/nearguard

**Demo video:** `demo-video.mp4` (in the repository). It is a capture of
a real terminal run of the checks and the attack demo; playback timing is
compressed and the video states this in an on-screen caption.
