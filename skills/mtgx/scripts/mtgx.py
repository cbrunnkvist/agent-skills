#!/usr/bin/env python3
"""
mtgx — CLI tool for building, querying, and manipulating Maltego MTGX files.

Handles all XML/namespace/ZIP/base64 complexity so agents can work in the
investigative domain. Single file, stdlib only, zero dependencies.

Usage:
  mtgx create  <input> -o <output.mtgx>     Build from JSON/NDJSON
  mtgx add     <file>  <json>               Add entity or link
  mtgx remove  <file>  <id>                 Remove by ID
  mtgx update  <file>  <id>  <json>         Update properties
  mtgx import  <file>  --entities <in> --links <in>
  mtgx export  <file>  --format json|ndjson|graphml
  mtgx query   <file>  [--filter "k=v,..."] [--neighborhood <id> --depth N] [--path <from> <to>]
  mtgx merge   <a>  <b>  -o <out>
  mtgx diff    <a>  <b>
  mtgx embed   <file>  <id>  <image-path>
  mtgx stats   <file>
  mtgx timeline <file>
  mtgx validate <file>
"""

import xml.etree.ElementTree as ET
import zipfile
import base64
import json
import os
import sys
import re
import argparse
import copy
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

MTG_NS = "http://maltego.paterva.com/xml/mtgx"
GRAPHML_NS = "http://graphml.graphdrawing.org/xmlns"

VERSION_PROPERTIES = "maltego.graph.version=1.3\nmaltego.client.version=4.11\n"
EXPECTED_MTGX_ENTRIES = {"version.properties", "Graphs/Graph1.graphml"}

MAX_INPUT_SIZE_BYTES = 50 * 1024 * 1024
MAX_ENTITY_COUNT = 100_000
MAX_STRING_LENGTH = 10_000
EMBED_ALLOWED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".ico", ".webp",
}
EMBED_MAX_SIZE_BYTES = 10 * 1024 * 1024

_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def mtg_q(tag: str) -> str:
    return f"{{{MTG_NS}}}{tag}"


def _sanitize_string(value: str, max_len: int = MAX_STRING_LENGTH) -> str:
    cleaned = _CONTROL_CHAR_RE.sub("", value)
    return cleaned[:max_len]


def _safe_resolve(base_dir: str, relative_path: str) -> str:
    if not base_dir:
        raise ValueError(
            "logo_dir must be set when providing relative image paths"
        )
    base = Path(base_dir).resolve()
    target = (base / relative_path).resolve()
    if not (target == base or str(target).startswith(str(base) + os.sep)):
        raise ValueError(
            f"Path traversal detected: '{relative_path}' resolves outside "
            f"the logo directory"
        )
    return str(target)


def _validate_image_path(path: str) -> None:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image file not found: {path}")
    ext = p.suffix.lower()
    if ext not in EMBED_ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported image type '{ext}'; allowed: "
            + ", ".join(sorted(EMBED_ALLOWED_EXTENSIONS))
        )
    size = p.stat().st_size
    if size > EMBED_MAX_SIZE_BYTES:
        raise ValueError(
            f"Image too large ({size} bytes); max {EMBED_MAX_SIZE_BYTES}"
        )


def _assert_no_external_entities(xml_bytes: bytes) -> None:
    head = xml_bytes[:4096].lower()
    if b"<!doctype" in head or b"<!entity" in head:
        raise ValueError("XML contains DTD/entity declarations; rejected")


# ──────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────

@dataclass
class Property:
    name: str
    value: str
    display_name: str = ""

    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.name


@dataclass
class Entity:
    id: str
    type: str
    value: str
    properties: list[Property] = field(default_factory=list)
    x: float = 0.0
    y: float = 0.0
    image_b64: str = ""

    def get_property(self, name: str) -> Optional[Property]:
        for p in self.properties:
            if p.name == name:
                return p
        return None

    def set_property(self, name: str, value: str, display_name: str = ""):
        for p in self.properties:
            if p.name == name:
                p.value = value
                if display_name:
                    p.display_name = display_name
                return
        self.properties.append(Property(name, value, display_name or name))

    def to_dict(self) -> dict:
        props = {}
        for p in self.properties:
            props[p.name] = p.value
        d = {
            "id": self.id,
            "type": self.type,
            "value": self.value,
            "x": self.x,
            "y": self.y,
            "properties": props,
        }
        if self.image_b64:
            d["has_image"] = True
        return d


@dataclass
class Link:
    id: str
    source: str
    target: str
    label: str
    description: str = ""
    unverified: bool = False
    properties: list[Property] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "label": self.label,
            "description": self.description,
            "unverified": self.unverified,
        }


@dataclass
class Graph:
    entities: dict[str, Entity] = field(default_factory=dict)
    links: dict[str, Link] = field(default_factory=dict)
    _next_entity_id: int = field(default=0, repr=False)
    _next_link_id: int = field(default=0, repr=False)

    def next_id(self) -> str:
        self._next_entity_id += 1
        return f"n{self._next_entity_id}"

    def next_link_id(self) -> str:
        self._next_link_id += 1
        return f"e{self._next_link_id}"

    def add_entity(self, entity: Entity):
        if not entity.id:
            entity.id = self.next_id()
        self.entities[entity.id] = entity
        # Update counter to avoid collisions
        try:
            num = int(entity.id.lstrip("n"))
            if num > self._next_entity_id:
                self._next_entity_id = num
        except ValueError:
            pass

    def remove_entity(self, eid: str) -> bool:
        if eid not in self.entities:
            return False
        del self.entities[eid]
        # Remove linked edges
        to_remove = [lid for lid, link in self.links.items()
                     if link.source == eid or link.target == eid]
        for lid in to_remove:
            del self.links[lid]
        return True

    def add_link(self, link: Link):
        if not link.id:
            link.id = self.next_link_id()
        self.links[link.id] = link
        try:
            num = int(link.id.lstrip("e"))
            if num > self._next_link_id:
                self._next_link_id = num
        except ValueError:
            pass

    def remove_link(self, lid: str) -> bool:
        if lid not in self.links:
            return False
        del self.links[lid]
        return True

    def find_entity_by_value(self, entity_type: str, value: str) -> Optional[Entity]:
        for e in self.entities.values():
            if e.type == entity_type and e.value == value:
                return e
        return None

    def find_entity_by_label(self, label: str) -> Optional[Entity]:
        """Find entity by display label (value property)."""
        for e in self.entities.values():
            if e.value == label:
                return e
        return None

    def neighborhood(self, eid: str, depth: int = 1) -> "Graph":
        """BFS from entity to given depth, return sub-graph."""
        if eid not in self.entities:
            return Graph()
        visited = set()
        queue = deque([(eid, 0)])
        result = Graph()
        while queue:
            current, d = queue.popleft()
            if current in visited or d > depth:
                continue
            visited.add(current)
            if current in self.entities:
                result.add_entity(self.entities[current])
            for link in self.links.values():
                if link.source == current and link.target not in visited:
                    result.add_link(link)
                    if d + 1 <= depth:
                        queue.append((link.target, d + 1))
                if link.target == current and link.source not in visited:
                    result.add_link(link)
                    if d + 1 <= depth:
                        queue.append((link.source, d + 1))
        return result

    def shortest_path(self, from_id: str, to_id: str) -> Optional[list[str]]:
        """BFS shortest path between two entities."""
        if from_id not in self.entities or to_id not in self.entities:
            return None
        visited = {from_id}
        queue = deque([(from_id, [from_id])])
        while queue:
            current, path = queue.popleft()
            if current == to_id:
                return path
            for link in self.links.values():
                next_node = None
                if link.source == current:
                    next_node = link.target
                elif link.target == current:
                    next_node = link.source
                if next_node and next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [next_node]))
        return None

    def merge(self, other: "Graph"):
        """Merge another graph into this one. Dedup by (type, value)."""
        id_map = {}
        for e in other.entities.values():
            existing = self.find_entity_by_value(e.type, e.value)
            if existing:
                id_map[e.id] = existing.id
                # Merge properties (other wins on conflict)
                for prop in e.properties:
                    existing.set_property(prop.name, prop.value, prop.display_name)
                if e.image_b64 and not existing.image_b64:
                    existing.image_b64 = e.image_b64
            else:
                old_id = e.id
                new_id = self.next_id()
                copied = copy.deepcopy(e)
                copied.id = new_id
                self.add_entity(copied)
                id_map[old_id] = new_id
        for link in other.links.values():
            src = id_map.get(link.source, link.source)
            tgt = id_map.get(link.target, link.target)
            if src in self.entities and tgt in self.entities:
                # Check for duplicate links
                dup = False
                for existing in self.links.values():
                    if existing.source == src and existing.target == tgt and existing.label == link.label:
                        dup = True
                        break
                if not dup:
                    copied = copy.deepcopy(link)
                    copied.id = self.next_link_id()
                    copied.source = src
                    copied.target = tgt
                    self.add_link(copied)

    def diff(self, other: "Graph") -> dict:
        """Compare two graphs, return added/removed/modified."""
        added_entities = []
        removed_entities = []
        modified_entities = []
        added_links = []
        removed_links = []

        other_vals = {(e.type, e.value) for e in other.entities.values()}
        self_vals = {(e.type, e.value) for e in self.entities.values()}

        for e in other.entities.values():
            if (e.type, e.value) not in self_vals:
                added_entities.append(e.to_dict())

        for e in self.entities.values():
            if (e.type, e.value) not in other_vals:
                removed_entities.append(e.to_dict())

        other_labels = {(l.source, l.target, l.label) for l in other.links.values()}
        self_labels = {(l.source, l.target, l.label) for l in self.links.values()}

        for l in other.links.values():
            if (l.source, l.target, l.label) not in self_labels:
                added_links.append(l.to_dict())

        for l in self.links.values():
            if (l.source, l.target, l.label) not in other_labels:
                removed_links.append(l.to_dict())

        return {
            "added_entities": added_entities,
            "removed_entities": removed_entities,
            "modified_entities": modified_entities,
            "added_links": added_links,
            "removed_links": removed_links,
        }


# ──────────────────────────────────────────────
# MTGX reader (parse ZIP → Graph)
# ──────────────────────────────────────────────

def read_mtgx(path: str) -> Graph:
    graph = Graph()
    with zipfile.ZipFile(path, "r") as zf:
        info = zf.getinfo("Graphs/Graph1.graphml")
        if info.file_size > MAX_INPUT_SIZE_BYTES:
            raise ValueError("GraphML entry exceeds size limit")
        graphml_data = zf.read("Graphs/Graph1.graphml")
    _assert_no_external_entities(graphml_data)
    root = ET.fromstring(graphml_data)
    graphml_root = root
    # Handle namespace
    ns_match = re.match(r"\{(.+?)\}", root.tag)
    ns = ns_match.group(1) if ns_match else GRAPHML_NS

    graph_el = root.find(f"{{{ns}}}graph")
    if graph_el is None:
        return graph

    # Read nodes
    for node in graph_el.findall(f"{{{ns}}}node"):
        eid = node.get("id", "")
        data0 = node.find(f"{{{ns}}}data[@key='d0']")
        if data0 is None:
            continue
        mte = data0.find(mtg_q("MaltegoEntity"))
        if mte is None:
            continue
        etype = mte.get("type", "")
        mtprops = mte.find(mtg_q("Properties"))
        if mtprops is None:
            continue

        image_b64 = ""
        value = ""
        properties = []
        for prop_el in mtprops.findall(mtg_q("Property")):
            name = prop_el.get("name", "")
            dn = prop_el.get("displayName", name)
            val_el = prop_el.find(mtg_q("Value"))
            val = val_el.text if val_el is not None and val_el.text else ""
            if name == "value":
                value = val
            elif name == "base64":
                image_b64 = val
            else:
                properties.append(Property(name, val, dn))

        # Read position
        x, y = 0.0, 0.0
        data1 = node.find(f"{{{ns}}}data[@key='d1']")
        if data1 is not None:
            renderer = data1.find(mtg_q("EntityRenderer"))
            if renderer is not None:
                pos = renderer.find(mtg_q("Position"))
                if pos is not None:
                    x = float(pos.get("x", "0"))
                    y = float(pos.get("y", "0"))

        entity = Entity(id=eid, type=etype, value=value,
                       properties=properties, x=x, y=y, image_b64=image_b64)
        graph.add_entity(entity)

    # Read edges
    link_counter = 0
    for edge in graph_el.findall(f"{{{ns}}}edge"):
        lid = edge.get("id", f"e{link_counter}")
        src = edge.get("source", "")
        tgt = edge.get("target", "")

        data2 = edge.find(f"{{{ns}}}data[@key='d2']")
        if data2 is None:
            link_counter += 1
            continue
        mtl = data2.find(mtg_q("MaltegoLink"))
        if mtl is None:
            link_counter += 1
            continue
        lprops = mtl.find(mtg_q("Properties"))
        if lprops is None:
            link_counter += 1
            continue

        label = ""
        desc = ""
        unverified = False
        for prop_el in lprops.findall(mtg_q("Property")):
            name = prop_el.get("name", "")
            val_el = prop_el.find(mtg_q("Value"))
            val = val_el.text if val_el is not None and val_el.text else ""
            if name == "maltego.link.manual.type":
                label = val
                if label.startswith("[UNVERIFIED] "):
                    label = label[len("[UNVERIFIED] "):]
                    unverified = True
            elif name == "maltego.link.manual.description":
                desc = val
                if desc.startswith("[UNVERIFIED CLAIM] "):
                    desc = desc[len("[UNVERIFIED CLAIM] "):]

        link = Link(id=lid, source=src, target=tgt, label=label,
                   description=desc, unverified=unverified)
        graph.add_link(link)
        link_counter += 1

    return graph


def validate_mtgx_archive(path: str) -> list[str]:
    """Validate MTGX ZIP contents before parsing GraphML."""
    issues = []
    try:
        with zipfile.ZipFile(path, "r") as zf:
            entries = set(zf.namelist())
    except zipfile.BadZipFile:
        return [f"Not a valid ZIP/MTGX archive: {path}"]

    missing = sorted(EXPECTED_MTGX_ENTRIES - entries)
    extra = sorted(entries - EXPECTED_MTGX_ENTRIES)
    if missing:
        issues.append(f"Missing required archive entries: {', '.join(missing)}")
    if extra:
        issues.append(
            "Invalid archive entries present; MTGX must contain only "
            "version.properties and Graphs/Graph1.graphml: "
            + ", ".join(extra)
        )
    return issues


# ──────────────────────────────────────────────
# MTGX writer (Graph → ZIP)
# ──────────────────────────────────────────────

def write_mtgx(graph: Graph, output_path: str):
    graphml_str = graph_to_graphml(graph)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("version.properties", VERSION_PROPERTIES)
        zf.writestr("Graphs/Graph1.graphml", graphml_str)


def graph_to_graphml(graph: Graph) -> str:
    ET.register_namespace("", GRAPHML_NS)
    ET.register_namespace("mtg", MTG_NS)

    graphml = ET.Element(f"{{{GRAPHML_NS}}}graphml")

    for attrs in [
        {"for": "node", "id": "d0", "attr.name": "MaltegoEntity"},
        {"for": "node", "id": "d1"},
        {"for": "edge", "id": "d2", "attr.name": "MaltegoLink"},
        {"for": "edge", "id": "d3"},
    ]:
        ET.SubElement(graphml, "key", attrs)

    ET.SubElement(graphml, "VersionInfo", {
        "createdBy": "mtgx CLI",
        "subtitle": "",
        "version": "4.11.3.f4fe3a1"
    })

    g = ET.SubElement(graphml, "graph", {"edgedefault": "directed", "id": "G"})

    # Nodes
    for entity in graph.entities.values():
        node = ET.SubElement(g, "node", {"id": entity.id})

        data0 = ET.SubElement(node, "data", {"key": "d0"})
        mte = ET.SubElement(data0, mtg_q("MaltegoEntity"), {"type": entity.type})
        mtprops = ET.SubElement(mte, mtg_q("Properties"))

        # Value property
        valp = ET.SubElement(mtprops, mtg_q("Property"), {
            "displayName": "Entity value", "hidden": "false", "name": "value",
            "nullable": "true", "readonly": "false", "type": "string"
        })
        ET.SubElement(valp, mtg_q("Value")).text = entity.value

        # Other properties
        for prop in entity.properties:
            p_el = ET.SubElement(mtprops, mtg_q("Property"), {
                "displayName": prop.display_name, "hidden": "false", "name": prop.name,
                "nullable": "true", "readonly": "false", "type": "string"
            })
            ET.SubElement(p_el, mtg_q("Value")).text = prop.value

        # Image
        if entity.image_b64:
            mtprops.set("image", "base64")
            b64p = ET.SubElement(mtprops, mtg_q("Property"), {
                "displayName": "Base64 image", "hidden": "false", "name": "base64",
                "nullable": "true", "readonly": "false", "type": "string"
            })
            ET.SubElement(b64p, mtg_q("Value")).text = entity.image_b64

        # Position
        data1 = ET.SubElement(node, "data", {"key": "d1"})
        renderer = ET.SubElement(data1, mtg_q("EntityRenderer"))
        ET.SubElement(renderer, mtg_q("Position"), {
            "x": str(entity.x), "y": str(entity.y)
        })

    # Edges
    for link in graph.links.values():
        edge = ET.SubElement(g, "edge", {
            "id": link.id, "source": link.source, "target": link.target
        })

        data2 = ET.SubElement(edge, "data", {"key": "d2"})
        link_el = ET.SubElement(data2, mtg_q("MaltegoLink"),
                              {"type": "maltego.link.manual-link"})
        lprops = ET.SubElement(link_el, mtg_q("Properties"))

        final_label = f"[UNVERIFIED] {link.label}" if link.unverified else link.label
        desc_text = f"[UNVERIFIED CLAIM] {link.description}" if link.unverified else link.description

        edge_props = [
            ("Label", "maltego.link.manual.type", "string", final_label),
            ("Show Label", "maltego.link.show-label", "int", "1"),
            ("Color", "maltego.link.color", "color",
             "#ff0000" if link.unverified else "#7f7f7f"),
            ("Reversed", "maltego.link.is_reversed", "boolean", "false"),
            ("Style", "maltego.link.style", "int", "1" if link.unverified else "0"),
            ("Thickness", "maltego.link.thickness", "int",
             "1" if link.unverified else "2"),
            ("Description", "maltego.link.manual.description", "string", desc_text),
        ]
        for dn, nm, pt, val in edge_props:
            ep = ET.SubElement(lprops, mtg_q("Property"), {
                "displayName": dn, "hidden": "false", "name": nm,
                "nullable": "true", "readonly": "false", "type": pt
            })
            ET.SubElement(ep, mtg_q("Value")).text = val

        data3 = ET.SubElement(edge, "data", {"key": "d3"})
        ET.SubElement(data3, mtg_q("LinkRenderer"))

    return ('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
            + ET.tostring(graphml, encoding="unicode", xml_declaration=False))


# ──────────────────────────────────────────────
# GraphML writer (standalone, no MTGX)
# ──────────────────────────────────────────────

def write_graphml(graph: Graph, output_path: str):
    graphml_str = graph_to_graphml(graph)
    with open(output_path, "w") as f:
        f.write(graphml_str)


# ──────────────────────────────────────────────
# JSON/NDJSON reader
# ──────────────────────────────────────────────

def read_json_spec(path: str) -> Graph:
    """Read a JSON or NDJSON graph specification."""
    graph = Graph()
    if path == "-":
        text = sys.stdin.read(MAX_INPUT_SIZE_BYTES + 1)
        if len(text) > MAX_INPUT_SIZE_BYTES:
            raise ValueError(f"Input exceeds {MAX_INPUT_SIZE_BYTES} byte limit")
    else:
        p = Path(path)
        if p.stat().st_size > MAX_INPUT_SIZE_BYTES:
            raise ValueError(f"Input file exceeds {MAX_INPUT_SIZE_BYTES} byte limit")
        text = p.read_text()
    text = text.strip()
    if not text:
        raise ValueError("Input is empty; refusing to create an empty MTGX graph")

    # Detect JSON vs NDJSON
    if text.startswith("{") or text.startswith("["):
        # JSON format
        data = json.loads(text)
        if isinstance(data, dict):
            _apply_json_spec(graph, data)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    _apply_json_spec(graph, item)
    else:
        # NDJSON format (one JSON object per line)
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            _apply_json_spec(graph, item)

    return graph


def _apply_json_spec(graph: Graph, data: dict):
    """Apply a single JSON spec object to a graph."""
    # Batch format: {"entities": [...], "links": [...], "logos": {...}}
    if "entities" in data:
        for e_spec in data["entities"]:
            entity = _parse_entity_spec(e_spec)
            graph.add_entity(entity)
    if "links" in data:
        for l_spec in data["links"]:
            link = _parse_link_spec(l_spec)
            graph.add_link(link)
    if "logos" in data:
        logo_dir = data.get("logo_dir", "")
        for eid, img_path in data["logos"].items():
            if eid in graph.entities:
                full_path = _safe_resolve(logo_dir, img_path)
                _validate_image_path(full_path)
                with open(full_path, "rb") as f:
                    graph.entities[eid].image_b64 = base64.b64encode(f.read()).decode("ascii")
    # Single entity: {"id": ..., "type": ..., "value": ...}
    elif "type" in data and "value" in data and "entities" not in data:
        entity = _parse_entity_spec(data)
        graph.add_entity(entity)
    # Single link: {"src": ..., "dst": ..., "label": ...}
    elif "src" in data and "dst" in data and "links" not in data:
        link = _parse_link_spec(data)
        graph.add_link(link)


def _parse_entity_spec(spec: dict) -> Entity:
    eid = _sanitize_string(spec.get("id", ""))
    etype = _sanitize_string(spec.get("type", ""))
    value = _sanitize_string(spec.get("value", ""))
    x = float(spec.get("x", 0))
    y = float(spec.get("y", 0))
    image_b64 = spec.get("image_b64", "")

    properties = []
    raw_props = spec.get("properties", {})
    if isinstance(raw_props, dict):
        for k, v in raw_props.items():
            properties.append(Property(_sanitize_string(k), _sanitize_string(str(v)), _sanitize_string(k)))
    elif isinstance(raw_props, list):
        for p in raw_props:
            if isinstance(p, dict):
                properties.append(Property(
                    _sanitize_string(p.get("name", "")),
                    _sanitize_string(str(p.get("value", ""))),
                    _sanitize_string(p.get("display_name", p.get("name", "")))
                ))

    return Entity(id=eid, type=etype, value=value,
                 properties=properties, x=x, y=y, image_b64=image_b64)


def _parse_link_spec(spec: dict) -> Link:
    lid = _sanitize_string(spec.get("id", ""))
    src = _sanitize_string(spec.get("src", spec.get("source", "")))
    dst = _sanitize_string(spec.get("dst", spec.get("target", "")))
    label = _sanitize_string(spec.get("label", ""))
    desc = _sanitize_string(spec.get("description", spec.get("desc", "")))
    unverified = spec.get("unverified", False)

    return Link(id=lid, source=src, target=dst, label=label,
               description=desc, unverified=unverified)


# ──────────────────────────────────────────────
# JSON/NDJSON writer
# ──────────────────────────────────────────────

def graph_to_json(graph: Graph) -> dict:
    return {
        "entities": [e.to_dict() for e in graph.entities.values()],
        "links": [l.to_dict() for l in graph.links.values()],
    }


def graph_to_ndjson(graph: Graph) -> str:
    lines = []
    for e in graph.entities.values():
        lines.append(json.dumps(e.to_dict()))
    for l in graph.links.values():
        lines.append(json.dumps(l.to_dict()))
    return "\n".join(lines)


# ──────────────────────────────────────────────
# Filter engine
# ──────────────────────────────────────────────

def parse_filter(filter_str: str) -> list[tuple[str, str, str]]:
    """Parse filter string into list of (key, op, value) tuples.
    
    Supported: key=value, key!=value, key~=regex
    """
    conditions = []
    for part in filter_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "~=" in part:
            key, val = part.split("~=", 1)
            conditions.append((key.strip(), "~=", val.strip()))
        elif "!=" in part:
            key, val = part.split("!=", 1)
            conditions.append((key.strip(), "!=", val.strip()))
        elif "=" in part:
            key, val = part.split("=", 1)
            conditions.append((key.strip(), "=", val.strip()))
    return conditions


def matches_filter(entity: Entity, conditions: list[tuple[str, str, str]]) -> bool:
    """Check if entity matches all filter conditions."""
    for key, op, val in conditions:
        if key == "type":
            actual = entity.type
        elif key == "value":
            actual = entity.value
        elif key == "id":
            actual = entity.id
        else:
            prop = entity.get_property(key)
            actual = prop.value if prop else ""

        if op == "=":
            if actual != val:
                return False
        elif op == "!=":
            if actual == val:
                return False
        elif op == "~=":
            if not re.search(val, actual):
                return False
    return True


# ──────────────────────────────────────────────
# Subcommands
# ──────────────────────────────────────────────

def cmd_create(args):
    """Build MTGX from JSON/NDJSON input."""
    try:
        graph = read_json_spec(args.input)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    if not args.output or args.output == "-":
        graphml_str = graph_to_graphml(graph)
        sys.stdout.write(graphml_str)
    else:
        write_mtgx(graph, args.output)
        print(f"Created: {args.output} ({len(graph.entities)} entities, {len(graph.links)} links)",
              file=sys.stderr)


def cmd_add(args):
    """Add entity or link to existing graph."""
    graph = read_mtgx(args.file)
    spec = json.loads(sys.stdin.read()) if args.json == "-" else json.loads(args.json)

    if "type" in spec and "value" in spec:
        entity = _parse_entity_spec(spec)
        graph.add_entity(entity)
        print(f"Added entity: {entity.id} ({entity.type}: {entity.value})", file=sys.stderr)
    elif "src" in spec or "source" in spec:
        link = _parse_link_spec(spec)
        graph.add_link(link)
        print(f"Added link: {link.id} ({link.source} -> {link.target})", file=sys.stderr)
    else:
        print("Error: JSON must contain entity (type+value) or link (src+dst)", file=sys.stderr)
        sys.exit(1)

    out = args.file if args.inplace else (args.output or args.file)
    write_mtgx(graph, out)
    if not args.inplace:
        print(f"Written to: {out}", file=sys.stderr)


def cmd_remove(args):
    """Remove entity or link by ID."""
    graph = read_mtgx(args.file)
    removed = False
    if args.id in graph.entities:
        graph.remove_entity(args.id)
        removed = True
        print(f"Removed entity: {args.id}", file=sys.stderr)
    elif args.id in graph.links:
        graph.remove_link(args.id)
        removed = True
        print(f"Removed link: {args.id}", file=sys.stderr)

    if not removed:
        print(f"Error: ID '{args.id}' not found", file=sys.stderr)
        sys.exit(1)

    out = args.file if args.inplace else (args.output or args.file)
    write_mtgx(graph, out)
    if not args.inplace:
        print(f"Written to: {out}", file=sys.stderr)


def cmd_update(args):
    """Update properties on entity/link."""
    graph = read_mtgx(args.file)
    spec = json.loads(sys.stdin.read()) if args.json == "-" else json.loads(args.json)

    if args.id in graph.entities:
        entity = graph.entities[args.id]
        for k, v in spec.items():
            entity.set_property(k, str(v))
        print(f"Updated entity: {args.id}", file=sys.stderr)
    elif args.id in graph.links:
        link = graph.links[args.id]
        if "label" in spec:
            link.label = spec["label"]
        if "description" in spec:
            link.description = spec["description"]
        if "unverified" in spec:
            link.unverified = bool(spec["unverified"])
        print(f"Updated link: {args.id}", file=sys.stderr)
    else:
        print(f"Error: ID '{args.id}' not found", file=sys.stderr)
        sys.exit(1)

    out = args.file if args.inplace else (args.output or args.file)
    write_mtgx(graph, out)
    if not args.inplace:
        print(f"Written to: {out}", file=sys.stderr)


def cmd_import(args):
    """Batch insert from JSON/NDJSON files."""
    graph = read_mtgx(args.file)

    if args.entities:
        entities_text = sys.stdin.read() if args.entities == "-" else Path(args.entities).read_text()
        entities_data = json.loads(entities_text)
        if isinstance(entities_data, list):
            for e_spec in entities_data:
                entity = _parse_entity_spec(e_spec)
                graph.add_entity(entity)
        elif isinstance(entities_data, dict):
            entity = _parse_entity_spec(entities_data)
            graph.add_entity(entity)

    if args.links:
        links_text = sys.stdin.read() if args.links == "-" else Path(args.links).read_text()
        links_data = json.loads(links_text)
        if isinstance(links_data, list):
            for l_spec in links_data:
                link = _parse_link_spec(l_spec)
                graph.add_link(link)
        elif isinstance(links_data, dict):
            link = _parse_link_spec(links_data)
            graph.add_link(link)

    out = args.output or args.file
    write_mtgx(graph, out)
    print(f"Imported to: {out} ({len(graph.entities)} entities, {len(graph.links)} links)",
          file=sys.stderr)


def cmd_export(args):
    """Export graph in structured format."""
    graph = read_mtgx(args.file)

    if args.format == "json":
        data = graph_to_json(graph)
        print(json.dumps(data, indent=2))
    elif args.format == "ndjson":
        print(graph_to_ndjson(graph))
    elif args.format == "graphml":
        print(graph_to_graphml(graph))
    else:
        print(f"Error: Unknown format '{args.format}'", file=sys.stderr)
        sys.exit(1)


def cmd_query(args):
    """Query graph: filter, neighborhood, or path."""
    graph = read_mtgx(args.file)

    if args.filter:
        conditions = parse_filter(args.filter)
        results = [e.to_dict() for e in graph.entities.values()
                   if matches_filter(e, conditions)]
        print(json.dumps(results, indent=2))

    elif args.neighborhood:
        subgraph = graph.neighborhood(args.neighborhood, args.depth or 1)
        print(json.dumps(graph_to_json(subgraph), indent=2))

    elif args.path:
        if len(args.path) != 2:
            print("Error: --path requires exactly 2 entity IDs", file=sys.stderr)
            sys.exit(1)
        path = graph.shortest_path(args.path[0], args.path[1])
        if path:
            print(json.dumps({
                "path": path,
                "entities": [graph.entities[eid].to_dict() for eid in path if eid in graph.entities]
            }, indent=2))
        else:
            print(json.dumps({"path": None, "error": "No path found"}))

    else:
        # Default: show all entities
        print(json.dumps([e.to_dict() for e in graph.entities.values()], indent=2))


def cmd_merge(args):
    """Merge two graphs."""
    graph_a = read_mtgx(args.a)
    graph_b = read_mtgx(args.b)
    graph_a.merge(graph_b)
    write_mtgx(graph_a, args.output)
    print(f"Merged: {args.output} ({len(graph_a.entities)} entities, {len(graph_a.links)} links)",
          file=sys.stderr)


def cmd_diff(args):
    """Compare two graphs."""
    graph_a = read_mtgx(args.a)
    graph_b = read_mtgx(args.b)
    result = graph_a.diff(graph_b)
    print(json.dumps(result, indent=2))


def cmd_embed(args):
    """Embed base64 image on entity."""
    graph = read_mtgx(args.file)

    if args.id not in graph.entities:
        print(f"Error: Entity '{args.id}' not found", file=sys.stderr)
        sys.exit(1)

    try:
        _validate_image_path(args.image)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    with open(args.image, "rb") as f:
        img_data = f.read()
    graph.entities[args.id].image_b64 = base64.b64encode(img_data).decode("ascii")

    out = args.file if args.inplace else (args.output or args.file)
    write_mtgx(graph, out)
    print(f"Embedded image on {args.id}", file=sys.stderr)


def cmd_stats(args):
    """Show graph statistics."""
    graph = read_mtgx(args.file)

    type_counts = defaultdict(int)
    for e in graph.entities.values():
        type_counts[e.type] += 1

    label_counts = defaultdict(int)
    for l in graph.links.values():
        label_counts[l.label] += 1

    print(f"Entities: {len(graph.entities)}")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")
    print(f"\nLinks: {len(graph.links)}")
    for l, c in sorted(label_counts.items(), key=lambda x: -x[1]):
        print(f"  {l}: {c}")

    unverified = sum(1 for l in graph.links.values() if l.unverified)
    if unverified:
        print(f"\nUnverified links: {unverified}")

    with_images = sum(1 for e in graph.entities.values() if e.image_b64)
    if with_images:
        print(f"Entities with images: {with_images}")


def cmd_timeline(args):
    """Show entities sorted by date property."""
    graph = read_mtgx(args.file)

    dated = []
    for e in graph.entities.values():
        prop = e.get_property("date")
        if prop:
            dated.append((prop.value, e.to_dict()))

    if not dated:
        print("No entities with 'date' property found.", file=sys.stderr)
        return

    dated.sort(key=lambda x: x[0])
    print(json.dumps([{"date": d, **e} for d, e in dated], indent=2))


def cmd_validate(args):
    """Validate graph structure."""
    issues = validate_mtgx_archive(args.file)
    if any(issue.startswith("Not a valid") or issue.startswith("Missing required") for issue in issues):
        print(f"Validation found {len(issues)} issue(s):", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        sys.exit(1)

    graph = read_mtgx(args.file)

    # Check for dangling link references
    for lid, link in graph.links.items():
        if link.source not in graph.entities:
            issues.append(f"Link {lid}: source '{link.source}' not in entities")
        if link.target not in graph.entities:
            issues.append(f"Link {lid}: target '{link.target}' not in entities")

    # Check for duplicate IDs
    all_ids = [e.id for e in graph.entities.values()] + [l.id for l in graph.links.values()]
    seen = set()
    for id_ in all_ids:
        if id_ in seen:
            issues.append(f"Duplicate ID: {id_}")
        seen.add(id_)

    # Check for empty values
    for e in graph.entities.values():
        if not e.value:
            issues.append(f"Entity {e.id}: empty value")

    if issues:
        print(f"Validation found {len(issues)} issue(s):", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"Valid: {len(graph.entities)} entities, {len(graph.links)} links")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="mtgx",
        description="CLI tool for building, querying, and manipulating Maltego MTGX files"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = sub.add_parser("create", help="Build MTGX from JSON/NDJSON")
    p_create.add_argument("input", help="Input file (- for stdin)")
    p_create.add_argument("-o", "--output", help="Output MTGX file (- for stdout GraphML)")
    p_create.set_defaults(func=cmd_create)

    # add
    p_add = sub.add_parser("add", help="Add entity or link")
    p_add.add_argument("file", help="Existing MTGX file")
    p_add.add_argument("json", help="JSON entity/link (- for stdin)")
    p_add.add_argument("-o", "--output", help="Output file (default: modify in place)")
    p_add.add_argument("-i", "--inplace", action="store_true", help="Modify in place")
    p_add.set_defaults(func=cmd_add)

    # remove
    p_remove = sub.add_parser("remove", help="Remove entity or link")
    p_remove.add_argument("file", help="Existing MTGX file")
    p_remove.add_argument("id", help="Entity or link ID")
    p_remove.add_argument("-o", "--output", help="Output file")
    p_remove.add_argument("-i", "--inplace", action="store_true", help="Modify in place")
    p_remove.set_defaults(func=cmd_remove)

    # update
    p_update = sub.add_parser("update", help="Update properties")
    p_update.add_argument("file", help="Existing MTGX file")
    p_update.add_argument("id", help="Entity or link ID")
    p_update.add_argument("json", help="JSON properties (- for stdin)")
    p_update.add_argument("-o", "--output", help="Output file")
    p_update.add_argument("-i", "--inplace", action="store_true", help="Modify in place")
    p_update.set_defaults(func=cmd_update)

    # import
    p_import = sub.add_parser("import", help="Batch insert entities/links")
    p_import.add_argument("file", help="Existing MTGX file")
    p_import.add_argument("--entities", help="JSON entities file (- for stdin)")
    p_import.add_argument("--links", help="JSON links file (- for stdin)")
    p_import.add_argument("-o", "--output", help="Output file (default: modify in place)")
    p_import.set_defaults(func=cmd_import)

    # export
    p_export = sub.add_parser("export", help="Export graph")
    p_export.add_argument("file", help="MTGX file")
    p_export.add_argument("--format", choices=["json", "ndjson", "graphml"],
                         default="json", help="Output format")
    p_export.set_defaults(func=cmd_export)

    # query
    p_query = sub.add_parser("query", help="Query graph")
    p_query.add_argument("file", help="MTGX file")
    p_query.add_argument("--filter", help="Filter: key=val,key!=val,key~=regex")
    p_query.add_argument("--neighborhood", help="Entity ID for neighborhood query")
    p_query.add_argument("--depth", type=int, default=1, help="Depth for neighborhood")
    p_query.add_argument("--path", nargs=2, metavar="ID", help="Shortest path between two IDs")
    p_query.set_defaults(func=cmd_query)

    # merge
    p_merge = sub.add_parser("merge", help="Merge two graphs")
    p_merge.add_argument("a", help="First MTGX file")
    p_merge.add_argument("b", help="Second MTGX file")
    p_merge.add_argument("-o", "--output", required=True, help="Output MTGX file")
    p_merge.set_defaults(func=cmd_merge)

    # diff
    p_diff = sub.add_parser("diff", help="Compare two graphs")
    p_diff.add_argument("a", help="First MTGX file")
    p_diff.add_argument("b", help="Second MTGX file")
    p_diff.set_defaults(func=cmd_diff)

    # embed
    p_embed = sub.add_parser("embed", help="Embed image on entity")
    p_embed.add_argument("file", help="MTGX file")
    p_embed.add_argument("id", help="Entity ID")
    p_embed.add_argument("image", help="Image file path")
    p_embed.add_argument("-o", "--output", help="Output file")
    p_embed.add_argument("-i", "--inplace", action="store_true", help="Modify in place")
    p_embed.set_defaults(func=cmd_embed)

    # stats
    p_stats = sub.add_parser("stats", help="Show graph statistics")
    p_stats.add_argument("file", help="MTGX file")
    p_stats.set_defaults(func=cmd_stats)

    # timeline
    p_timeline = sub.add_parser("timeline", help="Show entities sorted by date")
    p_timeline.add_argument("file", help="MTGX file")
    p_timeline.set_defaults(func=cmd_timeline)

    # validate
    p_validate = sub.add_parser("validate", help="Validate graph structure")
    p_validate.add_argument("file", help="MTGX file")
    p_validate.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
