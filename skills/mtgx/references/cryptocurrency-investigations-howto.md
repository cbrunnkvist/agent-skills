# Cryptocurrency Investigations With Maltego

This workflow distills Vladimir Mikhnovich's *Cryptocurrency Investigations with Maltego: Tips and Tricks for Efficient Analysis and Visualization of Bitcoin and Ethereum Movement* (51-page Maltego white paper). The source and its named references are recorded in [cryptocurrency-investigations-sources.md](cryptocurrency-investigations-sources.md).

Use this as an investigation-modeling guide. The bundled MTGX CLI is the implementation path: represent the selected evidence in JSON or NDJSON, create an MTGX, and run `validate` before delivery.

## Transform Boundary

The paper describes actions performed by a human in the interactive Maltego client. This skill and its bundled CLI cannot run Blockchain.com or any other Maltego Transform, select entities in the UI, apply views, or inspect the resulting interactive graph. Treat Transform output as evidence supplied by the user or as data exported from a separately executed workflow. The CLI can then model and validate that data in an MTGX.

References below to retrieving, filtering, ranking, or expanding data specify the investigative workflow. They are not a claim that this skill has performed a Maltego Transform. Obtain equivalent data from an authorized, documented source only when the task and available tools permit it; record its provenance.

## Scope And Evidence

1. Start from a known, evidentially supported address, transaction hash, or exported transfer dataset. Record source URL, retrieval time, chain, and any applicable time window in entity properties or link descriptions.
2. State the question before expanding the graph: for example, trace suspected proceeds to an identified service, identify the next receiving address, or visualize a token-transfer sequence.
3. Treat public attribution as a lead, not proof of ownership. Preserve the attribution source and confidence; label unsupported assertions `[UNVERIFIED]` and use red dashed links.
4. Work on a copy or a small focused graph. Avoid presenting a visual adjacency or a common counterparty as proof of control, laundering, or cash-out.

## Bitcoin: Trace Funds Through Transactions

Model UTXO movement as `Bitcoin Address -> Bitcoin Transaction -> Bitcoin Address`. Do not collapse it into direct address-to-address links: a transaction can have multiple inputs and outputs, and the transaction entity carries the date, amounts, fees, and block context needed to interpret the movement.

1. In interactive Maltego, add the seed address and run the relevant outbound-transaction Transform. Alternatively, supply/export equivalent records from a current, documented blockchain-data source.
2. Filter transaction entities to the defined time window and causal order. Remove or move out-of-scope branches before expanding further.
3. For each retained transaction, add its destination addresses. Expand a next hop only where it serves the stated question.
4. Fetch and record address details before ranking candidates: transaction count, total input/output or throughput, final balance, and any source attribution. In the client this may be a Transform; for MTGX construction, provide the resulting fields in the input data.
5. Prioritize high-throughput or high-connectivity addresses as leads. Compare structural ranking methods such as degree-like rank and diverse inbound sources; then independently corroborate any exchange/service attribution.
6. When a candidate and seed are relevant, retain the connecting path and copy it to a focused graph. Keep intermediate transaction nodes and link labels for amount and time.
7. Continue from the focused graph only as necessary. Link the output to evidence records, rather than making a categorical conclusion from graph shape alone.

For MTGX input, use `maltego.BitcoinAddress` and `maltego.BitcoinTransaction` only when those types are available in the target Maltego installation. Otherwise use stable generic/custom types and preserve the chain, address/hash, timestamp, value, asset, and source URL as properties.

## Ethereum And Token Transfers: Import A Dataset

For account-based transfers, build the graph from an exported and normalized dataset. Keep native transaction hashes: one transaction can contain multiple token-transfer rows, including swaps.

1. Export transfers for the address and asset scope from a current explorer or provider. The white paper uses Etherscan ERC-20 transfer CSV exports; confirm present exporter/API fields and terms before relying on them.
2. Normalize the CSV/JSON: ISO 8601 timestamps, canonical addresses, decimal quantities without locale-specific separators, chain ID, token symbol/name, token-contract address, and a source URL or dataset identifier.
3. Add a display-only `value_label` such as `12.5 USDC`; retain the numeric quantity and token decimals separately for analysis.
4. Use one transaction entity per transaction hash. Attach timestamp as a transaction property, and map each transfer through the concise schema:

   ```text
   Sender Address -> Transaction -> Token -> Recipient Address
   ```

   Put amount/token display values on the appropriate links. Store token contract address as a token property; do not confuse it with sender or recipient addresses.

5. Deduplicate transaction entities by `(chain_id, transaction_hash)` and keep multiple transfer links for a transaction when the dataset contains them.
6. Remove disconnected artifacts after checking whether they are data-import errors or legitimate isolated records. Apply a stable layout and show only properties that help answer the question, such as transaction timestamp and token contract.
7. Save the mapping/schema alongside the dataset definition so future exports with the same columns can be reproduced. Enrich with verified fiat/ETH valuation data only when its time basis and provenance are explicit.

## Delivery Checklist

- Every material node/link has an evidence source or is visibly marked as an analytical lead.
- The graph has a stated time range and chain/asset scope.
- Amount, asset, timestamp, transaction hash, and direction remain recoverable from properties or links.
- Visual ranking narrows investigation targets; it does not establish attribution by itself.
- The generated MTGX passes `python3 <skill>/scripts/mtgx.py validate output.mtgx`.
