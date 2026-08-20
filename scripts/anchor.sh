#!/usr/bin/env bash
# Anchor the produced action_ref into AnchorRegistry on Base mainnet.
# Permissionless anchor(bytes32). Reads the ref from artifacts/manifest.json.
#
# Requires: foundry (cast), and OWNER_PRIVATE_KEY in the environment (never
# committed). The signer address is the anchoredBy recorded on-chain.
set -euo pipefail

REGISTRY="0x49fEcA52bC634a9Ab773226D16619deC547794aa"
RPC="${BASE_RPC:-https://mainnet.base.org}"
ART="$(cd "$(dirname "$0")/.." && pwd)/artifacts"

REF="$(python3 -c 'import json;print(json.load(open("'"$ART"'/manifest.json"))["anchor_ref_bytes32"])')"
echo "Anchoring ref: $REF"
echo "Registry:      $REGISTRY (Base mainnet 8453)"

: "${OWNER_PRIVATE_KEY:?set OWNER_PRIVATE_KEY in env}"

cast send "$REGISTRY" "anchor(bytes32)" "$REF" \
  --rpc-url "$RPC" \
  --private-key "$OWNER_PRIVATE_KEY" \
  --json
