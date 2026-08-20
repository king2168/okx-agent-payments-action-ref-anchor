# okx-agent-payments-action-ref-anchor

A worked example that derives an **`action_ref`** — a deterministic,
content-addressed identifier for an agent action
([`action-ref-v1`](https://github.com/giskard09/argentum-core/blob/master/docs/spec/action-ref.md)) —
for a synthetic `exact`-scheme x402 payment settlement against the
**OKX Agent Payments Protocol** dispatcher (as documented in
[`okx/onchainos-skills`](https://github.com/okx/onchainos-skills), the
skill an AI agent uses to pay when it hits an HTTP 402 / x402 challenge),
and anchors it permissionlessly on-chain, giving it a property the call
does not have on its own: an **externally verifiable, third-party-checkable
record of what was requested and (reportedly) settled**, independent of
the CLI/facilitator's own account of the outcome.

The timestamp of the anchor is the point. This is not outreach and not a
claim of adoption — it is a worked example, byte-exact against the public
spec and `onchainos-skills`' own public source
(`skills/okx-agent-payments-protocol/SKILL.md` and
`references/accepts-schemes.md`).

> **Provenance, up front (read `PROVENANCE.md` for the full statement).**
> The `action_ref` here is derived exactly per `action-ref-v1` and
> cross-checked against argentum-core's own reference implementation. The
> request / result shapes are modeled on `onchainos-skills`'s **public
> source** — but it was **NOT produced by a live agent session or a real
> OKX-hosted 402 resource**: no real payment challenge, no real
> facilitator, no real on-chain settlement. All addresses and the tx hash
> in the fixture are obviously-synthetic placeholders. Nothing here — on-
> chain or in this repo — implies that `onchainos-skills` or OKX
> integrated, endorsed, or participated. It is our worked example applying
> a public spec to their public source.

## Why now

OKX shipped `okx-agent-payments-protocol` inside `onchainos-skills` — a
unified x402 / MPP / a2a-pay dispatcher, part of the broader OKX.AI /
OnchainOS agent infrastructure launch (beta since 2026-06-30). The skill's
own docs are unusually explicit about the boundary between signing and
settlement: `references/accepts-schemes.md`'s Security section states
"this reference only **signs** — settlement happens on-chain when the
recipient / facilitator redeems the authorization." The CLI still reports
`status: success` + `txHash` straight to the calling agent on the primary
success path — an admitted architectural boundary in the docs, not
self-declared by us. `action_ref` does not close that boundary either — it
answers a narrower, adjacent question: given a declared request/result
pair, can a third party recompute a content-addressed identifier for it
and confirm an independent, operator-external timestamp of when it was
anchored, regardless of whether the underlying settlement was accurately
reported? That is orthogonal to the sign/settle boundary, and this repo
does not claim to close it — only the separate one of externally-checkable
record-keeping for a single payment dispatch.

## The idea

The `payment pay --payment-id --yes` success path's own documented
interface (`SKILL.md` Step A3 / Step B, `references/accepts-schemes.md`)
declares fields (`scheme`, `network`, `asset`, `payTo`, `amount`) and,
once settled, the documented result (`status`, `txHash`, `amount`,
`payer`) is the CLI's own account of the outcome — it lives only in the
CLI's return value and whatever the facilitator's own systems retain.
`action_ref` closes part of that gap: a content-addressed identifier any
party can recompute from four declared fields (`agent_id`, `action_type`,
`scope`, `timestamp`) — no trust in the emitting system required. This
repo extends that with an **envelope** carrying `params_digest` (the
declared 402 challenge) and `result_digest` (the declared settlement
result) — hashes of the exact context a verifier would need to confirm
what was requested and reported, independently recomputable from the
declared JSON.

```
   OKX Agent Payments `payment pay`          public chain (Base)
   ┌───────────────────────────┐            ┌────────────────────────┐
   │ agent_id, action_type,     │  JCS+SHA256│ AnchorRegistry         │
   │ scope, timestamp           │───────────▶│  anchor(bytes32 ref)   │
   │ + params/result digests    │  action_ref│  Anchored(ref,by,time) │
   │   (envelope)                │            └────────────────────────┘
   └───────────────────────────┘             operator-independent
        no external record                   timestamp / finality
```

## Doctrine: spec-agnostic to OKX's format

We derive `action_ref` from the four canonical fields only. We do **not**
ask OKX or `onchainos-skills` to adopt any anchoring infrastructure,
change their API, or emit any new fields. The integration lives entirely
in how a `payment pay` settlement *could* be shaped and anchored; the
skill's documented source is the input, the anchor is the added property.

## What's here

| Path | What it is |
|------|-----------|
| `scripts/produce.py` | Derives `action_ref` per `action-ref-v1` (JCS RFC 8785 + SHA-256) for a synthetic `exact`-scheme payment settlement, plus the `params_digest`/`result_digest` envelope. |
| `verifier/verify.py` | Independent (stdlib-only) verifier: recomputes both digests from the declared JSON and confirms the matching `Anchored` event on Base mainnet. |
| `artifacts/` | The canonical instance: `manifest.json` (preimage, digests, envelope) and `anchor.json` (tx/block, once anchored). |
| `scripts/anchor.sh` | The exact `cast`-equivalent call used to anchor `action_ref`. |
| `PROVENANCE.md` | Exactly what is and isn't real about this artifact. Read it. |

**Looking for a tool to run against your own payment dispatches, not this
fixed instance?** The scripts here are pinned to one synthetic
request/response pair. The parametrized version — takes any real
request/response JSON, derives `action_ref` for it, and checks any
`action_ref` against the chain — is submitted as a new skill to
`okx/onchainos-skills`:
[okx/onchainos-skills#PR](https://github.com/okx/onchainos-skills/pulls)
(update this link once opened).

## Reproduce

```bash
# 1. derive action_ref + the envelope digests
python3 scripts/produce.py artifacts

# 2. anchor action_ref on Base mainnet (see scripts/anchor.sh)

# 3. independently verify the derivation and the on-chain anchor
python3 verifier/verify.py
```

## The anchor

- **Registry:** `0x49fEcA52bC634a9Ab773226D16619deC547794aa` (same CREATE2
  address on Base 8453, Arbitrum One 42161, Ink 57073).
- **Function:** `anchor(bytes32 ref)` — permissionless, no owner/roles/funds.
- **Event:** `Anchored(bytes32 indexed ref, address indexed anchoredBy, uint256 timestamp)`.
- Tx `0x3c5ddb7d1757c72f9949362ae1c3e574de8abfafc1cd72938bd12143dcd7d63d`,
  block `50236856`, Base mainnet. `artifacts/anchor.json`
  has the full record; `verifier/verify.py` confirms it independently
  against public RPC.

## Related worked examples

Same pattern, other formats: [`binance-onchain-pay-action-ref-anchor`](https://github.com/giskard09/binance-onchain-pay-action-ref-anchor)
(Binance Onchain-Pay), [`turnkey-action-ref-anchor`](https://github.com/giskard09/turnkey-action-ref-anchor)
(Turnkey), [`keycard-action-ref-anchor`](https://github.com/giskard09/keycard-action-ref-anchor)
(Keycard), [`dapr-history-anchor`](https://github.com/giskard09/dapr-history-anchor)
(Dapr Verifiable Execution), [`scitt-capsule-anchor`](https://github.com/giskard09/scitt-capsule-anchor)
(SCITT Agent Action Capsule), [`pay-kit-action-ref-anchor`](https://github.com/giskard09/pay-kit-action-ref-anchor)
(Solana Foundation pay-kit), [`wdk-action-ref-anchor`](https://github.com/giskard09/wdk-action-ref-anchor)
(Tether WDK MCP toolkit), [`paypal-action-ref-anchor`](https://github.com/giskard09/paypal-action-ref-anchor)
(PayPal agent-toolkit).

## License

MIT.
