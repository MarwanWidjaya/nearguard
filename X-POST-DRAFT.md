# X post drafts — NearGuard (NEAR Hackathon)

For Marwan to post himself. Attach `demo-video.mp4` to the post/thread
opener. Replace `[REPO_URL]` with the public repo link once it exists.
Claims are honest: local/testnet demo, read-only mainnet checks, no real
transactions were signed or sent.

---

## Variant A — single post (≤280 chars)

Built NearGuard for the NEAR Build Beyond Boundaries hackathon
(security track): a pre-signing check that gives a paying AI agent
allow / warn / block before it pays — and refuses a prompt-injected
payment to a drainer before the signer is touched. Demo 👇 [REPO_URL]

(Character count verified: 279 including a t.co-shortened URL counted as
23 chars — inside the 280 limit.)

## Variant B — thread (3 posts)

**1/3**
Your AI agent will pay whoever its prompt tells it to pay — including a
prompt injection hiding in a document it just read.

For the NEAR Build Beyond Boundaries hackathon (security track) I built
NearGuard: an independent counterparty check an agent must pass *before*
signing anything. 🧵

**2/3**
NearGuard scores the receiver from on-chain facts (account age lower
bound, contract code changes, balance) + a shared blocklist + interaction
history, and answers allow / warn / block with every reason shown.

Block = the signer is never invoked. Warn = a human decides.

**3/3**
Demo: a poisoned invoice note tells the agent to send 5 NEAR to a drainer
and "skip verification". NearGuard blocks it cold.

The agent's key design matters too: function-call access keys only — one
contract, allowlisted methods, capped allowance. A leaked key can't drain
the account.

Code + reproducible local demo: [REPO_URL]
Read-only checks against public NEAR RPC; no mainnet transactions were
performed.

---

Notes for posting:
- Attach `demo-video.mp4` to post 1 (thread) or the single post.
- The video is a real captured terminal run (timing compressed, labeled
  on-screen as such).
