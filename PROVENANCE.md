# Provenance — read this before drawing any conclusion

This document states exactly what is real and what is synthetic in this
worked example. Hard honesty is the point: the artifact is worthless if its
provenance is fuzzy.

## What is real

- `action_ref` is derived exactly per `action-ref-v1`
  ([argentum-core/docs/spec/action-ref.md](https://github.com/giskard09/argentum-core/blob/master/docs/spec/action-ref.md)):
  SHA-256 of the RFC 8785 JCS canonicalization of the four preimage fields
  (`agent_id`, `action_type`, `scope`, `timestamp`). The value in
  `artifacts/manifest.json` was independently cross-checked against
  argentum-core's own reference implementation
  (`plugins/agt_evidence_anchor/action_ref.py`) and matches byte-for-byte.
- The request and result shapes are modeled on `okx/onchainos-skills`'s
  own public source, not invented:
  - [`skills/okx-agent-payments-protocol/SKILL.md`](https://github.com/okx/onchainos-skills/blob/main/skills/okx-agent-payments-protocol/SKILL.md)
    documents the primary success path for an `accepts`-based x402 402:
    `onchainos payment quote <url>` → confirm → `onchainos payment pay
    --payment-id --yes`, which "signs, replays, and returns the settled
    receipt" and reports `txHash` on success (Step B, "Success path...
    report txHash").
  - [`references/accepts-schemes.md`](https://github.com/okx/onchainos-skills/blob/main/skills/okx-agent-payments-protocol/references/accepts-schemes.md)
    documents the `exact` scheme's settlement semantics — "Settles
    immediately. `status` / `transaction` / `amount` / `payer` are
    final." — the shape modeled for `result` below. The same file's
    Security section states plainly: "This reference only **signs** —
    settlement happens on-chain when the recipient / facilitator redeems
    the authorization."
  - `network: eip155:8453` (Base), `scheme: exact`, and the challenge
    fields (`asset`, `payTo`, `amount`) follow the standard x402
    `accepts[]` shape SKILL.md itself reads from (Step A3: "Network /
    Token / Amount / Pay to" — `option.network` / `option.asset` /
    `option.amount` / `option.payTo`).
- The on-chain anchor is a real transaction on Base mainnet, sent via
  `giskard-signer` (owner wallet, policy-gated, key never touched by this
  session): tx `<TX_HASH>`, block `<BLOCK>`, `status: 1 (success)`. The
  tx hash and block are independently checkable by anyone via
  `verifier/verify.py`, which was run and produced `ALL CHECKS PASS`
  against public Base RPC (`mainnet.base.org`) after the transaction
  confirmed.

## What is synthetic — declared

- **No running agent session, real OKX-hosted 402 resource, or real
  on-chain settlement was involved.** `agent_id`, `timestamp`, `params`,
  and `result` are all constructed in `scripts/produce.py`, not captured
  from a live `payment pay` call, a real resource server issuing a 402,
  or any actual EIP-3009/x402 authorization redeemed on-chain.
- **`params.payTo`, `params.resource`, `result.txHash`, and `result.payer`
  are obviously-synthetic placeholders** — a burn-style hex address
  (`0x00…00BEEFEE`), an `.invalid` resource URL, and a zero-padded fake
  tx hash (`0x00…00BEEF`). Nothing here was submitted to OKX's actual
  API, and no real facilitator ever redeemed anything.

## What this therefore does and does not show

- **Does show:** the `action_ref` derivation applies unchanged to
  `onchainos-skills`' own documented `payment pay` settlement shape —
  same four fields, same JCS + SHA-256 path used by every other emitter
  in the spec's cross-reference list, and the same envelope pattern
  already anchored for Binance (`giskard09/binance-onchain-pay-action-ref-anchor`),
  Turnkey, Keycard, Dapr, SCITT, pay-kit, `wdk-mcp-toolkit`, and
  `agent-toolkit`. It also surfaces a distinction specific to this skill:
  `accepts-schemes.md` itself draws the line between signing and
  settlement ("this reference only signs — settlement happens on-chain
  when the recipient / facilitator redeems the authorization"), but the
  CLI's own `status: success` + `txHash` report to the calling agent is
  the operator's own account of the outcome — nothing about that report
  format makes it independently checkable by a third party without
  querying the chain (or trusting the CLI/OKX's own logs) for whether the
  authorization was in fact redeemed as reported. `action_ref` does not
  settle that question either — it gives a third party a content-addressed
  identifier for the declared request/result pair, and an
  operator-independent anchor timestamp, regardless of whether the
  underlying settlement it describes was accurately reported.
- **Does not show:** that `onchainos-skills` or OKX has integrated,
  endorsed, or adopted `action_ref`. It is our worked example applying a
  public spec to `onchainos-skills`' public source. No claim of "OKX
  integrated us," no claim of on-chain adoption.
