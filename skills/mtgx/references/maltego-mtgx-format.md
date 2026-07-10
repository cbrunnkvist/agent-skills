# Maltego MTGX Format

This CLI writes a minimal MTGX archive validated against Maltego 4.11 behavior, `maltego-mcp` v0.4.3, and `pymtgx` expectations.

## ZIP Contents

An MTGX archive must contain exactly two entries:

```text
version.properties
Graphs/Graph1.graphml
```

`version.properties`:

```properties
maltego.graph.version=1.3
maltego.client.version=4.11
```

Do not include any other archive entries.

## GraphML Requirements

- Use keys `d0` for node entity data, `d1` for node graphics, `d2` for edge link data, and `d3` for edge graphics.
- Do not use `yfiles.type` on key elements.
- Do not add `xmlns:xsi` or `xsi:schemaLocation` on `<graphml>`.
- Do not add trailing `<y:Resources>`.
- Do not add `MaltegoEntityList` child entities.
- Use `mtg:EntityRenderer` and `mtg:Position` for node layout.
- Use `mtg:LinkRenderer` in edge data key `d3`.
- Use hex strings for edge colors, such as `#7f7f7f` or `#ff0000`.
- Always include `maltego.link.is_reversed = false`.
- Prefer sequential node IDs `n1`, `n2`, and so on. Maltego may rewrite IDs when saving.

## Images

Embed entity images as base64 directly on the entity:

```xml
<mtg:Properties image="base64">
```

Store the base64 payload in the `base64` property. Do not create child `maltego.File` entities just to carry images; Maltego strips those on re-save.

## NPE-Causing Archive Mistakes

Avoid these entries and structures:

- `Icons/`
- `Entities/`
- `Graphs/Graph1.properties`
- `META-INF/MANIFEST.MF`
- Binary PNG/SVG files inside the MTGX archive

Maltego's archive reader iterates ZIP entries as metadata. Binary files or unexpected metadata entries can trigger `GraphMetadataEntry.fromString` null-pointer failures in Maltego 4.11.

## Unverified Claims

Represent unverified claims with:

- Label prefix `[UNVERIFIED]`
- Description prefix `[UNVERIFIED CLAIM]`
- Red edge color `#ff0000`
- Dashed style

Use known-unknown notes or labels for missing but material investigative facts.
