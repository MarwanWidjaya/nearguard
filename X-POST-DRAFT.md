# X post drafts — NearGuard (NEAR Hackathon)

For Marwan to post himself. Attach `demo-video.mp4` to the post (variant A)
or to the first post of the thread (variant B).
Repository: https://github.com/MarwanWidjaya/nearguard
Status of the project: local demo. Checks against public NEAR RPC are
read-only; no transaction has been signed or sent.

---

## Variant A — single post (≤280 chars, URL counted as 23)

NearGuard: a pre-signing counterparty check for AI agents that pay on NEAR.
It scores the receiver from public RPC data and a blocklist, returns
allow / warn / block with reasons, and stops a prompt-injected payment
before signing. https://github.com/MarwanWidjaya/nearguard

## Variant B — thread (3 posts, each ≤280 chars, URL counted as 23)

**1/3**
An AI agent pays whoever its context tells it to pay — including a prompt
injection planted in a document it read. NearGuard is a counterparty check
for NEAR that runs before anything is signed. Built for the Build Beyond
Boundaries hackathon (AI Security & Defense track).

**2/3**
Scores come from public NEAR RPC data — account age (lower bound), code
changes in ~90 days, balance — plus a local blocklist and interaction
history. Verdict: allow, warn, or block, with every reason listed. On
block the signer is never invoked; on warn, a human decides.

**3/3**
Demo: an invoice note tells the agent to send 5 NEAR to a blocklisted
testnet account and skip verification. Verdict: block (score 100);
payment refused. Phase-2 signing: function-call access keys only — one
contract, named methods, capped allowance.
https://github.com/MarwanWidjaya/nearguard

---

Notes for posting:
- The demo video is a capture of a real terminal run. Playback timing is
  compressed; the video states this in an on-screen caption.
- The blocklisted account in the demo is a fixture entry in the local
  blocklist shipped with the repository.
