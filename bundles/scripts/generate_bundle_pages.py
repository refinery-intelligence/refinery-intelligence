#!/usr/bin/env python3
"""Generate static, crawler-readable Refinery bundle documentation pages.

Inputs:
  registry/packages.registry.json
  registry/bundle-pages.content.json
  public/agent-buy.json
  public/<bundle-id>.json

Outputs:
  public/bundles/<bundle-id>/index.html
  public/sitemap.xml

This script is additive. It does not modify API routes, payment logic, bundle
generators, nginx, Cloudflare, systemd, or paid payloads.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "registry" / "packages.registry.json"
CONTENT_PATH = ROOT / "registry" / "bundle-pages.content.json"
AGENT_BUY_PATH = ROOT / "public" / "agent-buy.json"
PUBLIC_DIR = ROOT / "public"
SITEMAP_PATH = PUBLIC_DIR / "sitemap.xml"
DOC_BASE = "https://dalien.net/bundles"
API_BASE = "https://api.dalien.net"
EXPECTED_PURCHASE_URL = f"{API_BASE}/payments/usdc/request"

FORBIDDEN_OUTPUT_PATTERNS = (
    "/home/dalien",
    "vault/",
    "private_key",
    "seed phrase",
    "mnemonic",
    "signal_weights",
    "detector_threshold",
    "scoring_formula",
)

def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc

def bundle_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    bundles = registry.get("bundles")
    if not isinstance(bundles, list) or not bundles:
        raise ValueError("registry.bundles must be a non-empty list")
    result: dict[str, dict[str, Any]] = {}
    for bundle in bundles:
        bundle_id = bundle.get("bundle_id")
        if not isinstance(bundle_id, str) or not bundle_id:
            raise ValueError("registry bundle missing bundle_id")
        if bundle_id in result:
            raise ValueError(f"duplicate registry bundle_id: {bundle_id}")
        result[bundle_id] = bundle
    return result

def find_purchase_step(agent_buy: dict[str, Any]) -> dict[str, Any]:
    for step in agent_buy.get("purchase_flow", []):
        if step.get("action") == "create_payment_request":
            method = step.get("method")
            url = step.get("url")
            if method != "GET":
                raise ValueError(f"payment request method must be GET, got {method!r}")
            if url != EXPECTED_PURCHASE_URL:
                raise ValueError(
                    f"payment request URL mismatch: expected {EXPECTED_PURCHASE_URL}, got {url!r}"
                )
            return step
    raise ValueError("agent-buy.json lacks create_payment_request step")

def require(bundle: dict[str, Any], field: str, bundle_id: str) -> Any:
    value = bundle.get(field)
    if value is None or value == "" or value == []:
        raise ValueError(f"{bundle_id}: missing registry field {field}")
    return value

def load_editorial() -> dict[str, dict[str, Any]]:
    data = load_json(CONTENT_PATH)
    items = data.get("bundles")
    if not isinstance(items, list):
        raise ValueError("bundle-pages.content.json bundles must be a list")
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        bundle_id = item.get("bundle_id")
        if not isinstance(bundle_id, str) or not bundle_id:
            raise ValueError("editorial entry missing bundle_id")
        if bundle_id in result:
            raise ValueError(f"duplicate editorial bundle_id: {bundle_id}")
        for key in (
            "title", "summary", "measures", "why_agents_buy",
            "source_provenance", "schema_highlights", "known_limitations"
        ):
            if not item.get(key):
                raise ValueError(f"{bundle_id}: missing editorial field {key}")
        for source in item["source_provenance"]:
            if source.get("status") not in {"live", "limited", "reserved"}:
                raise ValueError(f"{bundle_id}: invalid source status {source.get('status')!r}")
        result[bundle_id] = item
    return result

def parse_existing_sitemap(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return re.findall(r"https?://[^\s<]+", text)
    urls: list[str] = []
    for element in root.iter():
        if element.tag.endswith("loc") and element.text:
            urls.append(element.text.strip())
    return urls

def build_sitemap(existing_urls: list[str], bundle_ids: list[str]) -> str:
    urls = []
    seen = set()
    for url in existing_urls + [f"{DOC_BASE}/{bundle_id}" for bundle_id in bundle_ids]:
        if url and url not in seen:
            urls.append(url)
            seen.add(url)
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    urlset = ET.Element("{http://www.sitemaps.org/schemas/sitemap/0.9}urlset")
    for url in urls:
        url_el = ET.SubElement(urlset, "{http://www.sitemaps.org/schemas/sitemap/0.9}url")
        ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text = url
    ET.indent(urlset, space="  ")
    return ET.tostring(urlset, encoding="unicode", xml_declaration=True) + "\n"

def list_html(items: list[str]) -> str:
    return "\n".join(f"<li>{html.escape(item)}</li>" for item in items)

def provenance_html(items: list[dict[str, str]]) -> str:
    rows = []
    for item in items:
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['source_type'])}</td>"
            f"<td>{html.escape(item['role'])}</td>"
            f"<td><code>{html.escape(item['status'])}</code></td>"
            "</tr>"
        )
    return "\n".join(rows)

def build_json_ld(bundle: dict[str, Any], editorial: dict[str, Any]) -> dict[str, Any]:
    bundle_id = bundle["bundle_id"]
    preview_url = API_BASE + require(bundle, "preview_url", bundle_id)
    return {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": editorial["title"],
        "description": editorial["summary"],
        "identifier": bundle_id,
        "version": require(bundle, "bundle_version", bundle_id),
        "url": f"{DOC_BASE}/{bundle_id}",
        "isAccessibleForFree": False,
        "creator": {
            "@type": "Organization",
            "name": "Refinery Intelligence",
            "url": "https://dalien.net/",
        },
        "distribution": [{
            "@type": "DataDownload",
            "encodingFormat": "application/json",
            "contentUrl": preview_url,
            "description": "Intentionally minimal redacted public discovery preview.",
        }],
        "offers": {
            "@type": "Offer",
            "price": str(require(bundle, "price_usd", bundle_id)),
            "priceCurrency": "USD",
            "description": (
                f"Settlement through {require(bundle, 'payment_asset', bundle_id)} "
                f"on {require(bundle, 'payment_network', bundle_id)}."
            ),
        },
        "additionalProperty": [
            {
                "@type": "PropertyValue",
                "name": "updateCadenceSeconds",
                "value": require(bundle, "cadence_seconds", bundle_id),
            },
            {
                "@type": "PropertyValue",
                "name": "signalCount",
                "value": require(bundle, "signal_count", bundle_id),
            },
        ],
        "keywords": list(dict.fromkeys(
            [bundle.get("category", "temporal intelligence")]
            + bundle.get("signals", [])
            + bundle.get("sources", [])
        )),
    }

def build_page(
    bundle: dict[str, Any],
    editorial: dict[str, Any],
    preview: dict[str, Any],
    purchase_step: dict[str, Any],
) -> str:
    bundle_id = bundle["bundle_id"]
    canonical = f"{DOC_BASE}/{bundle_id}"
    preview_url = API_BASE + require(bundle, "preview_url", bundle_id)
    json_ld = build_json_ld(bundle, editorial)
    preview_text = json.dumps(preview, indent=2, ensure_ascii=False)
    request_body = dict(purchase_step.get("body") or {})
    request_body["bundle_id"] = bundle_id
    request_text = json.dumps(request_body, indent=2)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(editorial['title'])} for Autonomous Agents | Refinery Intelligence</title>
  <meta name="description" content="{html.escape(editorial['summary'])}">
  <link rel="canonical" href="{canonical}">
  <link rel="alternate" type="application/json" href="{preview_url}">
  <link rel="service-desc" type="application/openapi+json" href="{API_BASE}/openapi.json">
  <style>
    :root {{ color-scheme: dark; --bg:#071015; --panel:#0d1a21; --text:#e9f1f4; --muted:#9db0ba; --line:#243640; --accent:#71e0b1; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font:16px/1.6 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    main {{ max-width:1040px; margin:auto; padding:48px 24px 80px; }}
    header,section {{ border-bottom:1px solid var(--line); padding:28px 0; }}
    h1 {{ font-size:clamp(2rem,5vw,4rem); line-height:1.05; margin:.2em 0; }}
    h2 {{ margin-top:0; }}
    a {{ color:var(--accent); }}
    .eyebrow,.muted {{ color:var(--muted); }}
    .facts {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; }}
    .fact {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; }}
    .fact strong {{ display:block; font-size:.82rem; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; }}
    pre {{ overflow:auto; background:#03080b; border:1px solid var(--line); border-radius:8px; padding:18px; }}
    code {{ font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }}
    table {{ width:100%; border-collapse:collapse; }}
    th,td {{ text-align:left; vertical-align:top; border-bottom:1px solid var(--line); padding:10px; }}
    .warning {{ border-left:4px solid var(--accent); padding-left:16px; }}
  </style>
  <script type="application/ld+json">
{json.dumps(json_ld, indent=2, ensure_ascii=False)}
  </script>
</head>
<body>
<main>
  <header>
    <div class="eyebrow">Operational paid temporal intelligence bundle</div>
    <h1>{html.escape(editorial['title'])}</h1>
    <p>{html.escape(editorial['summary'])}</p>
    <p><a href="#purchase">Purchase instructions</a> · <a href="{preview_url}">Public preview JSON</a> · <a href="{API_BASE}/packages">Package registry</a></p>
  </header>

  <section>
    <h2>Bundle facts</h2>
    <div class="facts">
      <div class="fact"><strong>Bundle ID</strong><code>{bundle_id}</code></div>
      <div class="fact"><strong>Status</strong>{html.escape(str(require(bundle, 'status', bundle_id)))}</div>
      <div class="fact"><strong>Version</strong>{html.escape(str(require(bundle, 'bundle_version', bundle_id)))}</div>
      <div class="fact"><strong>Cadence</strong>{int(require(bundle, 'cadence_seconds', bundle_id))} seconds</div>
      <div class="fact"><strong>Signals</strong>{int(require(bundle, 'signal_count', bundle_id))}</div>
      <div class="fact"><strong>Price</strong>USD ${float(require(bundle, 'price_usd', bundle_id)):.2f}</div>
      <div class="fact"><strong>Settlement</strong>{html.escape(str(require(bundle, 'payment_asset', bundle_id)))} on {html.escape(str(require(bundle, 'payment_network', bundle_id)))}</div>
    </div>
  </section>

  <section>
    <h2>What it measures</h2>
    <ul>{list_html(editorial['measures'])}</ul>
  </section>

  <section>
    <h2>Why autonomous agents buy it</h2>
    <ul>{list_html(editorial['why_agents_buy'])}</ul>
  </section>

  <section>
    <h2>Source provenance</h2>
    <table>
      <thead><tr><th>Source</th><th>Role</th><th>Status</th></tr></thead>
      <tbody>{provenance_html(editorial['source_provenance'])}</tbody>
    </table>
  </section>

  <section>
    <h2>Schema highlights</h2>
    <p class="muted">High-level categories only. Paid field values, detector thresholds, formulas, and internal weighting are not published here.</p>
    <ul>{list_html(editorial['schema_highlights'])}</ul>
  </section>

  <section>
    <h2>Known limitations</h2>
    <ul>{list_html(editorial['known_limitations'])}</ul>
  </section>

  <section>
    <h2>Public preview</h2>
    <p class="warning">This is the exact intentionally minimal, redacted public preview. It is not the full paid payload and is not a live trading instruction.</p>
    <pre><code>{html.escape(preview_text)}</code></pre>
  </section>

  <section id="purchase">
    <h2>Canonical purchase flow</h2>
    <p>Discovery is public. Full intelligence is delivered only after verified Polygon USDC payment and an access grant.</p>
    <pre><code>POST {EXPECTED_PURCHASE_URL}
Content-Type: application/json

{html.escape(request_text)}</code></pre>
    <ol>
      <li>Create the payment request.</li>
      <li>Send the exact Polygon USDC amount to the returned receiver.</li>
      <li>Call <code>/payments/usdc/verify?request_id=REQUEST_ID&amp;tx_hash=TX_HASH</code> using GET.</li>
      <li>Retrieve the paid payload from the returned bundle URL or <code>/payments/usdc/bundle</code>.</li>
    </ol>
  </section>

  <section>
    <h2>Machine-readable links</h2>
    <ul>
      <li><a href="{API_BASE}/agent-buy.json">Agent buying guide</a></li>
      <li><a href="{API_BASE}/packages">Package registry</a></li>
      <li><a href="{preview_url}">Bundle preview</a></li>
      <li><a href="{API_BASE}/meta">Service metadata</a></li>
      <li><a href="{API_BASE}/openapi.json">OpenAPI</a></li>
      <li><a href="{API_BASE}/public/agent_manifest.json">Agent manifest</a></li>
    </ul>
  </section>
</main>
</body>
</html>
"""

def validate_page(text: str, bundle_id: str) -> None:
    required = (
        f"{DOC_BASE}/{bundle_id}",
        bundle_id,
        "GET https://api.dalien.net/payments/usdc/request?bundle_id=BUNDLE_ID&buyer_id=BUYER_ID",
        "public preview",
        'type="application/ld+json"',
    )
    for item in required:
        if item not in text:
            raise ValueError(f"{bundle_id}: generated HTML missing {item!r}")
    for pattern in FORBIDDEN_OUTPUT_PATTERNS:
        if pattern.lower() in text.lower():
            raise ValueError(f"{bundle_id}: forbidden output pattern {pattern!r}")
    matches = re.findall(
        r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
        text,
        flags=re.DOTALL,
    )
    if not matches:
        raise ValueError(f"{bundle_id}: missing JSON-LD")
    for raw in matches:
        json.loads(html.unescape(raw))

def generate(check_only: bool) -> None:
    registry = load_json(REGISTRY_PATH)
    registry_bundles = bundle_map(registry)
    editorial = load_editorial()
    agent_buy = load_json(AGENT_BUY_PATH)
    purchase_step = find_purchase_step(agent_buy)

    unknown = sorted(set(editorial) - set(registry_bundles))
    if unknown:
        raise ValueError(f"editorial content references unknown bundles: {unknown}")

    target_ids = sorted(editorial)
    if not target_ids:
        raise ValueError("no editorial bundles configured")

    existing_urls = parse_existing_sitemap(SITEMAP_PATH)
    sitemap_text = build_sitemap(existing_urls, target_ids)
    ET.fromstring(sitemap_text)

    generated_pages: dict[str, str] = {}
    for bundle_id in target_ids:
        bundle = registry_bundles[bundle_id]
        for field in (
            "status", "bundle_version", "cadence_seconds", "preview_url",
            "signal_count", "price_usd", "payment_asset", "payment_network"
        ):
            require(bundle, field, bundle_id)
        preview_path = PUBLIC_DIR / f"{bundle_id}.json"
        preview = load_json(preview_path)
        if preview.get("bundle_id") != bundle_id:
            raise ValueError(f"{bundle_id}: preview bundle_id mismatch")
        expected_preview = f"/public/{bundle_id}.json"
        if bundle.get("preview_url") != expected_preview:
            raise ValueError(
                f"{bundle_id}: expected preview_url {expected_preview}, got {bundle.get('preview_url')!r}"
            )
        text = build_page(bundle, editorial[bundle_id], preview, purchase_step)
        validate_page(text, bundle_id)
        generated_pages[bundle_id] = text

    for bundle_id in target_ids:
        if f"{DOC_BASE}/{bundle_id}" not in sitemap_text:
            raise ValueError(f"sitemap missing {bundle_id}")

    if check_only:
        print("check-ok")
        print(f"validated_bundles={len(target_ids)}")
        print(f"generated_pages={len(generated_pages)}")
        print(f"sitemap_entries={len(parse_existing_sitemap_from_text(sitemap_text))}")
        return

    temp_root = Path(tempfile.mkdtemp(prefix="refinery-bundle-pages-", dir=str(ROOT)))
    try:
        temp_public = temp_root / "public"
        for bundle_id, text in generated_pages.items():
            target = temp_public / "bundles" / bundle_id / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        temp_sitemap = temp_public / "sitemap.xml"
        temp_sitemap.parent.mkdir(parents=True, exist_ok=True)
        temp_sitemap.write_text(sitemap_text, encoding="utf-8")

        for bundle_id in target_ids:
            validate_page(
                (temp_public / "bundles" / bundle_id / "index.html").read_text(encoding="utf-8"),
                bundle_id,
            )
        ET.parse(temp_sitemap)

        for bundle_id in target_ids:
            source = temp_public / "bundles" / bundle_id / "index.html"
            target = PUBLIC_DIR / "bundles" / bundle_id / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, target)
        os.replace(temp_sitemap, SITEMAP_PATH)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    print("write-ok")
    print(f"generated_pages={len(generated_pages)}")
    print(f"updated_sitemap={SITEMAP_PATH}")

def parse_existing_sitemap_from_text(text: str) -> list[str]:
    root = ET.fromstring(text)
    return [
        element.text.strip()
        for element in root.iter()
        if element.tag.endswith("loc") and element.text
    ]

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate and render in memory only")
    args = parser.parse_args()
    generate(check_only=args.check)

if __name__ == "__main__":
    main()
