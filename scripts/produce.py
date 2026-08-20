#!/usr/bin/env python3
"""
Produces an action_ref for a synthetic OKX Agent Payments Protocol `exact`
scheme x402 payment settlement (as documented in okx/onchainos-skills, the
skill an AI agent uses to dispatch payment when it hits an HTTP 402 / x402
challenge), following action-ref-v1 (argentum-core, JCS RFC 8785 +
SHA-256) byte-for-byte, and emits the artifacts needed to anchor +
independently verify it.

PROVENANCE: this is NOT captured from a running agent session, a real
OKX-hosted resource server, or a real on-chain settlement. The
request/result shapes are modeled on okx/onchainos-skills' own public
source (skills/okx-agent-payments-protocol/SKILL.md and
references/accepts-schemes.md): the `accepts[]` 402 challenge entry
(scheme, network, asset, payTo, maxAmountRequired/amount, extra) and the
documented settlement result read from `payment pay --payment-id --yes`
(status, txHash, amount, payer per scheme table "exact: Settles
immediately. status/transaction/amount/payer are final."). No claim that
OKX or onchainos-skills emits action_ref today, and no claim of
integration, adoption, or endorsement by OKX.
"""
import hashlib
import json
import os
import sys

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "artifacts"
os.makedirs(OUT_DIR, exist_ok=True)


def jcs(obj):
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


# --- 1. The four required action-ref-v1 preimage fields --------------------
# Per argentum-core/docs/spec/action-ref.md: only these four fields enter the
# hash. action_type mirrors the CLI subcommand SKILL.md itself names for the
# success path ("onchainos payment pay --payment-id --yes"); scope carries
# the scheme + network the settlement targets (exact / Base — SKILL.md's own
# scheme-table entry for `exact`: "Settles immediately.").
timestamp = "2026-08-20T21:30:00.000Z"
preimage = {
    "agent_id": "worked-example.okx-agent-payments-action-ref-anchor",
    "action_type": "okx.agent_payments_protocol.payment.pay",
    "scope": "okx:agent-payments-protocol:x402:exact:network:base",
    "timestamp": timestamp,
}
jcs_payload = jcs(preimage)
action_ref = sha256_hex(jcs_payload)

# --- 2. Additive envelope fields — payment-dispatch-specific context -------
# These do NOT enter the action_ref hash (per action-ref-v1: only the 4
# preimage fields are hashed). They travel alongside as declared context a
# downstream verifier can check independently:
#   params  — the 402 `accepts[]` challenge entry's own declared fields, per
#             SKILL.md Step A3 ("Network / Token / Amount / Pay to" —
#             option.network / option.asset / option.amount /
#             option.payTo) and references/accepts-schemes.md's `exact`
#             scheme (EIP-3009 authorization: from, to, value, nonce,
#             validAfter, validBefore).
#   result  — the settlement result SKILL.md documents for the `exact`
#             scheme on the primary Path A success path ("Settles
#             immediately. status / transaction / amount / payer are
#             final." + SKILL.md Step B "Success path... report txHash").
#
# The gap this closes: okx-agent-payments-protocol's own security note
# states plainly, of the signing step, "this reference only signs —
# settlement happens on-chain when the recipient/facilitator redeems the
# authorization" (references/accepts-schemes.md, Security section). The
# CLI reports `status: success` + `txHash` directly to the calling agent,
# but that report is the operator's own account of the outcome — nothing
# about the CLI's output format makes it independently checkable by a
# third party without querying the chain (or trusting the CLI/OKX's own
# logs) for whether the authorization was in fact redeemed as reported.
# action_ref does not settle that question either — it gives a third
# party a content-addressed identifier for the declared request/result
# pair, and an operator-independent anchor timestamp, regardless of
# whether the underlying settlement it describes was accurately reported.
#
# payTo/from/asset addresses, txHash, and the payment resource URL are
# OBVIOUSLY-SYNTHETIC placeholders — no real OKX-hosted 402 resource, no
# real wallet, no real on-chain settlement was involved.
params = {
    "endpoint": "onchainos payment pay --payment-id <id> --yes",
    "resource": "https://worked-example.invalid/paid-resource",
    "x402Version": 2,
    "scheme": "exact",
    "network": "eip155:8453",
    "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "payTo": "0x00000000000000000000000000000000BEEFEE",
    "amount": "1000000",
    "assetTransferMethod": "eip3009",
}
params_digest = sha256_hex(jcs(params))

# Result — mirrors SKILL.md's documented settlement read for the `exact`
# scheme + Step B's success-path report ("report txHash").
result = {
    "status": "success",
    "scheme": "exact",
    "txHash": "0x0000000000000000000000000000000000000000000000000000000000BEEF",
    "amount": "1000000",
    "payer": "0x00000000000000000000000000000000C0FFEE",
}
result_digest = sha256_hex(jcs(result))

envelope = {
    "packet_version": "1.0",
    "action_ref": action_ref,
    "hash_algo": "sha256",
    "preimage_format": "jcs-rfc8785-v1",
    "preimage": preimage,
    "capability": "agent-payments-protocol.payment.pay.exact",
    "params_digest": params_digest,
    "result_digest": result_digest,
    "generated_at_utc": timestamp,
}

manifest = {
    "fixture_id": "okx-agent-payments-protocol-exact-pay-worked-example",
    "spec": "action-ref-v1 (argentum-core, docs/spec/action-ref.md)",
    "preimage": preimage,
    "jcs_payload": jcs_payload,
    "action_ref": action_ref,
    "anchor_ref_bytes32": "0x" + action_ref,
    "anchor_registry": "0x49fEcA52bC634a9Ab773226D16619deC547794aa",
    "anchor_chain": "Base mainnet (chainId 8453)",
    "envelope": envelope,
    "params": params,
    "result": result,
    "provenance": (
        "Synthetic worked example. Request/result shapes modeled on "
        "okx/onchainos-skills' own public source "
        "(skills/okx-agent-payments-protocol/SKILL.md and "
        "references/accepts-schemes.md): the accepts[] 402 challenge "
        "entry (scheme, network, asset, payTo, amount) and the documented "
        "exact-scheme settlement result (status, txHash, amount, payer). "
        "NOT captured from a running agent session, a real OKX-hosted "
        "402 resource, or any real on-chain settlement. payTo, asset "
        "holder addresses, and txHash are synthetic placeholders. No "
        "claim that OKX or onchainos-skills emits action_ref today, and "
        "no claim of integration, adoption, or endorsement by OKX."
    ),
}

with open(os.path.join(OUT_DIR, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2, sort_keys=True)
    f.write("\n")

print("=== okx-agent-payments-action-ref-anchor : producer ===")
print(f"jcs_payload = {jcs_payload}")
print(f"action_ref  = {action_ref}")
print(f"anchor ref (bytes32) = 0x{action_ref}")
print(f"wrote {OUT_DIR}/manifest.json")
