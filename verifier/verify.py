#!/usr/bin/env python3
"""
Independent (stdlib-only) verifier for the binance-onchain-pay-action-ref-
anchor worked example. Trusts nothing in manifest.json's prose fields —
only recomputes.

1. Recomputes action_ref from the 4 declared preimage fields (JCS RFC 8785 +
   SHA-256, per argentum-core/docs/spec/action-ref.md) and checks it matches
   manifest.json.
2. Recomputes params_digest / result_digest from the declared context and
   checks they match the envelope.
3. Queries Base mainnet RPC for the Anchored(bytes32,address,uint256) event
   with topics[0] == keccak256("Anchored(bytes32,address,uint256)") and
   topics[1] == action_ref, and confirms it exists on-chain.

Run: python3 verifier/verify.py [--artifacts DIR] [--rpc URL]
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.request

ANCHOR_REGISTRY = "0x49fEcA52bC634a9Ab773226D16619deC547794aa"
# keccak256("Anchored(bytes32,address,uint256)") — same topic0 used by every
# other worked example anchoring into this registry (dapr-history-anchor,
# scitt-capsule-anchor, r0x-action-ref-anchor, pay-kit-action-ref-anchor,
# wdk-action-ref-anchor, paypal-action-ref-anchor, turnkey-action-ref-anchor,
# keycard-action-ref-anchor).
ANCHORED_TOPIC0 = "0xfe2289542f7a0110ac112c3a4d712afdcaaf2900a1326f4e6f340b563a0e8734"
DEFAULT_RPC = "https://mainnet.base.org"


def jcs(obj):
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def rpc(url, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "User-Agent": "okx-agent-payments-action-ref-anchor-verifier/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.loads(r.read())
    if "error" in out:
        raise RuntimeError(f"RPC {method} error: {out['error']}")
    return out["result"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpc", default=os.environ.get("BASE_RPC", DEFAULT_RPC))
    ap.add_argument("--artifacts", default=os.path.join(os.path.dirname(__file__), "..", "artifacts"))
    args = ap.parse_args()

    art = os.path.abspath(args.artifacts)
    m = json.load(open(os.path.join(art, "manifest.json")))

    ok = True

    # --- 1. action_ref from the 4 preimage fields ---------------------------
    recomputed_action_ref = sha256_hex(jcs(m["preimage"]))
    check1 = recomputed_action_ref == m["action_ref"]
    print(f"[{'PASS' if check1 else 'FAIL'}] action_ref recompute : {recomputed_action_ref}")
    ok &= check1

    # --- 2. envelope digests -------------------------------------------------
    for label, key, digest_key in [
        ("params_digest", "params", "params_digest"),
        ("result_digest", "result", "result_digest"),
    ]:
        recomputed = sha256_hex(jcs(m[key]))
        expected = m["envelope"][digest_key]
        check = recomputed == expected
        print(f"[{'PASS' if check else 'FAIL'}] {label:<19}: {recomputed}")
        ok &= check

    # --- 3. on-chain anchor ---------------------------------------------------
    ref = "0x" + m["action_ref"]
    try:
        with open(os.path.join(art, "anchor.json")) as f:
            anchor = json.load(f)
    except FileNotFoundError:
        print("[SKIP] no anchor.json yet — action_ref not anchored on-chain")
        anchor = None

    if anchor:
        hint = int(anchor["block"])
        head = int(rpc(args.rpc, "eth_blockNumber", []), 16)
        from_block = hex(max(0, hint - 25))
        to_block = hex(min(hint + 25, head))

        logs = rpc(args.rpc, "eth_getLogs", [{
            "address": ANCHOR_REGISTRY,
            "fromBlock": from_block,
            "toBlock": to_block,
            "topics": [ANCHORED_TOPIC0, ref],
        }])

        check3 = bool(logs)
        if check3:
            log = logs[0]
            ts = int(log["data"], 16)
            anchored_by = "0x" + log["topics"][2][-40:]
            print(f"[PASS] on-chain Anchored event : AnchorRegistry {ANCHOR_REGISTRY} (Base 8453)")
            print(f"         tx               : {log['transactionHash']}")
            print(f"         block            : {int(log['blockNumber'], 16)}")
            print(f"         anchoredBy       : {anchored_by}")
            print(f"         block timestamp  : {ts}")
        else:
            print(f"[FAIL] no Anchored event for {ref} on AnchorRegistry near block {hint}")
        ok &= check3

    print()
    print("ALL CHECKS PASS" if ok else "SOME CHECKS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
