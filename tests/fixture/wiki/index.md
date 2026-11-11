# Example Corp knowledge base

Rules: [RULES.md](RULES.md). Status: [status.md](status.md). History: [log.md](log.md).

## Quick facts
- Connect: VPN profile `corp-vpn`, then SSH to `app01`; credentials in vault item "Example app01"
- Files in/out: `scp` via the jump host, see [IIS](web/iis.md#transfer)

## General
- [Status](status.md): what is live, in progress, open

## web
- [IIS](web/iis.md): app pools, bindings, `svc-app` identity, file transfer
