# Sources: Cryptocurrency Investigations With Maltego

## Primary Source

- Mikhnovich, Vladimir. *Cryptocurrency Investigations with Maltego: Tips and Tricks for Efficient Analysis and Visualization of Bitcoin and Ethereum Movement*. Maltego white paper, 51 pages. Retrieved 2026-07-10 from <https://ftp.kr-labs.com.ua/books/investigate-crypto-maltego.pdf>.

The source is a practical white paper, not an evidentiary authority for a particular wallet attribution. Its examples, Transform names, interface labels, provider capabilities, and addresses are historical and must be checked against current tools and independent evidence.

## Named References And Tools Extracted From The Paper

- Blockchain.com Bitcoin Transform set: historical Maltego transforms for Bitcoin addresses and transactions. The paper uses outbound-transaction, destination-address, and address-details transforms. Verify current availability and output before use.
- Etherscan: Ethereum explorer used in the paper to export ERC-20 transfer data as CSV. Use a current explorer/API export, document the retrieval time and query parameters, and retain raw data outside the reusable skill.
- Vivigle: a public Bitcoin-address attribution lookup mentioned for exchange attribution. Treat its result as a lead requiring corroboration.
- Maltego technical documentation: cited for entity creation, external-data import, and graph views. Prefer current official documentation because the white paper's UI is historical.
- Antonopoulos, Andreas M. and Gavin Wood. *Mastering Ethereum*. Recommended by the paper for Ethereum technical background.
- Heberger, Matthew. *American Rivers: A Graphic*. Pacific Institute, 2013. Used as an analogy for converging flows; it is not a blockchain-analysis source.

## Method Notes Extracted From The Paper

- Bitcoin is modeled through transaction nodes because UTXO transactions may have multiple inputs and outputs; direct address-to-address links discard material context.
- Address activity, throughput, and network connectivity can prioritize leads, but public cluster/service attribution still needs independent support.
- Ethereum token-transfer rows may share a transaction hash. Model the shared transaction once and preserve each transfer relationship.
- Imported graph schemas should be driven by a clear verbal relationship model before mapping columns to entities and links.
