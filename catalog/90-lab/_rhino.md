# Server-side Rhino examples

Rhino belongs to **IndexServer scripting**, not to arbitrary JavaScript injected into
ELO Web Client. The playground therefore exposes these snippets as documentation-only
server artifacts. Deploy a reviewed script through ELO administration and invoke the
named endpoint with `IXServicePortIF.executeScript`; pass structured arguments only.

## Safety contract

- Do not evaluate user supplied code or build a script name from user input.
- Allowlist script names and outbound HTTP destinations in the deployed script.
- Use a dedicated technical user with the minimum archive, metadata and network rights.
- Make document creation/copy operations idempotent and log the resulting object IDs.
- Treat invoice classification as business configuration: mask and GRP names vary by tenant.

## Suggested reviewed functions

1. `RF_playground_readMetadata`: check out a `Sord`, return its ID, name and mask.
2. `RF_playground_createDocument`: create a document under an approved parent and check in content.
3. `RF_playground_copyToStructure`: resolve an approved path template and copy into it.
4. `RF_playground_invoiceMetadata`: return only configured invoice GRP/MAP metadata.
5. `RF_playground_sendWebhook`: POST a minimal event payload to a configured allowlisted URL.

The browser must call a backend-owned endpoint which invokes the reviewed server
function. It must never receive IndexServer credentials or upload arbitrary Rhino code.
