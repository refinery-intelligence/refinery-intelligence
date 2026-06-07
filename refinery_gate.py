from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from pathlib import Path
import json
from vault.payments.usdc.verify_polygon_rpc_tx import verify_transaction
from vault.payments.usdc.verifier import create_payment_request
from vault.payments.usdc.check_access import check_access
from vault.payments.usdc.serve_bundle import serve_bundle

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)
app.mount("/public", StaticFiles(directory="public"), name="public")

BASE_DIR = Path(__file__).resolve().parent
PACKAGES_PATH = BASE_DIR / "packages.json"
CANONICAL_REGISTRY_PATH = BASE_DIR / "registry" / "packages.registry.json"


def json_file_response(relative_path: str):
    path = BASE_DIR / relative_path

    if not path.exists() or not path.is_file():
        return JSONResponse(
            status_code=404,
            content={
                "error": "discovery_file_not_found",
                "file": relative_path
            }
        )

    return FileResponse(
        path,
        media_type="application/json",
        headers={
            "Cache-Control": "public, max-age=300"
        }
    )


def text_file_response(relative_path: str):
    path = BASE_DIR / relative_path

    if not path.exists() or not path.is_file():
        return JSONResponse(
            status_code=404,
            content={
                "error": "discovery_file_not_found",
                "file": relative_path
            }
        )

    return FileResponse(
        path,
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "public, max-age=300"
        }
    )


@app.get("/packages.json")
async def packages_json_alias():
    return json_file_response("packages.json")


@app.get("/agent_manifest.json")
async def agent_manifest_alias():
    return json_file_response("public/agent_manifest.json")


@app.get("/refinery.json")
async def refinery_json_alias():
    return json_file_response("public/refinery.json")


@app.get("/llms.txt")
async def llms_txt_alias():
    return text_file_response("public/llms.txt")


@app.get("/manifest")
async def manifest_alias():
    return json_file_response("public/agent_manifest.json")


@app.get("/discovery")
async def discovery_alias():
    return {
        "platform": "Refinery",
        "node": "Refinery-01",
        "status": "online",
        "machine_readable": True,
        "canonical": {
            "meta": "/meta",
            "packages": "/packages",
            "packages_json": "/packages.json",
            "refinery_json": "/refinery.json",
            "agent_manifest": "/agent_manifest.json",
            "llms_txt": "/llms.txt"
        },
        "well_known": {
            "agent": "/.well-known/agent.json",
            "ai_plugin": "/.well-known/ai-plugin.json",
            "refinery": "/.well-known/refinery.json"
        }
    }


@app.get("/.well-known/agent.json")
async def well_known_agent_json():
    return json_file_response("public/agent_manifest.json")


@app.get("/.well-known/refinery.json")
async def well_known_refinery_json():
    return json_file_response("public/refinery.json")


@app.get("/.well-known/ai-plugin.json")
async def well_known_ai_plugin_json():
    return {
        "schema_version": "v1",
        "name_for_human": "Refinery",
        "name_for_model": "refinery_temporal_intelligence",
        "description_for_human": "Refinery provides machine-readable DeFi temporal intelligence bundles.",
        "description_for_model": "Use Refinery to discover agent-readable DeFi temporal intelligence packages, manifests, payment endpoints, and public bundle metadata.",
        "auth": {
            "type": "none"
        },
        "api": {
            "type": "openapi",
            "url": "https://api.dalien.net/openapi.json",
            "has_user_authentication": False
        },
        "logo_url": "https://dalien.net/logo.png",
        "contact_email": "hello@dalien.net",
        "legal_info_url": "https://dalien.net"
    }




def load_canonical_registry():
    if not CANONICAL_REGISTRY_PATH.exists() or not CANONICAL_REGISTRY_PATH.is_file():
        raise FileNotFoundError(f"canonical registry not found: {CANONICAL_REGISTRY_PATH}")

    with open(CANONICAL_REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    if not isinstance(registry, dict):
        raise ValueError("canonical registry root must be an object")

    bundles = registry.get("bundles")
    if not isinstance(bundles, list):
        raise ValueError("canonical registry bundles must be a list")

    return registry


def build_meta_from_registry():
    registry = load_canonical_registry()
    bundles = registry.get("bundles", [])

    public_bundles = [
        bundle for bundle in bundles
        if bundle.get("visibility") == "public"
    ]

    active_bundles = [
        bundle for bundle in bundles
        if bundle.get("status") == "active"
    ]

    payment_enabled_bundles = [
        bundle for bundle in bundles
        if bundle.get("payment_enabled") is True
    ]

    cadence_seconds_available = sorted({
        int(bundle["cadence_seconds"])
        for bundle in public_bundles
        if isinstance(bundle.get("cadence_seconds"), (int, float))
    })

    freshness_sla_values = [
        int(bundle["freshness_sla_seconds"])
        for bundle in public_bundles
        if isinstance(bundle.get("freshness_sla_seconds"), (int, float))
    ]

    bundle_categories = sorted({
        bundle["category"]
        for bundle in public_bundles
        if isinstance(bundle.get("category"), str) and bundle.get("category")
    })

    bundle_signal_counts = {}
    total_signal_count = 0

    for bundle in public_bundles:
        bundle_id = bundle.get("bundle_id")
        signals = bundle.get("signals", [])
        signal_count = len(signals) if isinstance(signals, list) else 0

        if isinstance(bundle_id, str) and bundle_id:
            bundle_signal_counts[bundle_id] = signal_count
            total_signal_count += signal_count

    payment_networks = sorted({
        bundle["payment"]["network"]
        for bundle in public_bundles
        if isinstance(bundle.get("payment"), dict)
        and isinstance(bundle["payment"].get("network"), str)
        and bundle["payment"].get("network")
    })

    payment_network_labels = [
        f"{network} USDC" if network == "Polygon" else network
        for network in payment_networks
    ]

    if "Polygon" in payment_networks:
        primary_payment_network = "Polygon USDC"
    elif payment_network_labels:
        primary_payment_network = payment_network_labels[0]
    else:
        primary_payment_network = "Polygon USDC"

    cadence_model = "mixed"
    if len(cadence_seconds_available) == 1:
        cadence_model = "uniform"

    return {
        "platform": "Refinery",
        "node": "Refinery-01",
        "version": "1.1.0",
        "status": "online",
        "mode": "agent_only",
        "machine_readable": True,
        "registry_loaded": True,
        "canonical_registry_source": "registry/packages.registry.json",
        "bundle_model": "multi_bundle_temporal_intelligence",
        "bundle_count": len(bundles),
        "active_bundle_count": len(active_bundles),
        "public_bundle_count": len(public_bundles),
        "payment_enabled_bundle_count": len(payment_enabled_bundles),
        "bundle_categories": bundle_categories,
        "total_signal_count": total_signal_count,
        "bundle_signal_counts": bundle_signal_counts,
        "cadence_model": cadence_model,
        "cadence_seconds_available": cadence_seconds_available,
        "min_cadence_seconds": min(cadence_seconds_available) if cadence_seconds_available else None,
        "max_freshness_sla_seconds": max(freshness_sla_values) if freshness_sla_values else None,
        "payment_networks": payment_network_labels or ["Polygon USDC", "XRPL"],
        "primary_payment_network": primary_payment_network,
        "legacy_payment_network": "XRPL",
        "payment_endpoints": {
            "usdc_request": "/payments/usdc/request",
            "usdc_verify": "/payments/usdc/verify",
            "usdc_access": "/payments/usdc/access",
            "usdc_bundle": "/payments/usdc/bundle"
        },
        "history": {
            "available": any(bundle.get("history_enabled") is True for bundle in public_bundles),
            "model": "bundle_specific"
        },
        "packages_endpoint": "/packages",
        "discovery": {
            "refinery_json": "/public/refinery.json",
            "agent_manifest": "/public/agent_manifest.json",
            "llms_txt": "/public/llms.txt"
        }
    }


def head_response(media_type: str = "application/json"):
    return Response(
        status_code=200,
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=300"
        }
    )


@app.head("/meta")
async def meta_head():
    return head_response("application/json")


@app.head("/packages")
async def packages_head():
    return head_response("application/json")


@app.head("/packages.json")
async def packages_json_head():
    return head_response("application/json")


@app.head("/health")
async def health_head():
    return head_response("application/json")


@app.head("/agent_manifest.json")
async def agent_manifest_head():
    return head_response("application/json")


@app.head("/refinery.json")
async def refinery_json_head():
    return head_response("application/json")


@app.head("/llms.txt")
async def llms_txt_head():
    return head_response("text/plain; charset=utf-8")


@app.head("/manifest")
async def manifest_head():
    return head_response("application/json")


@app.head("/discovery")
async def discovery_head():
    return head_response("application/json")


@app.head("/.well-known/agent.json")
async def well_known_agent_head():
    return head_response("application/json")


@app.head("/.well-known/refinery.json")
async def well_known_refinery_head():
    return head_response("application/json")


@app.head("/.well-known/ai-plugin.json")
async def well_known_ai_plugin_head():
    return head_response("application/json")


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


@app.get("/")
async def root():

    with open(PACKAGES_PATH, "r") as f:
        packages = json.load(f)

    cards = []

    for package_id, package in packages.items():
        cards.append({
            "package_id": package_id,
            "name": package.get("name", package_id),
            "category": package.get("category", "general"),
            "price_xrp": package.get("price_xrp"),
            "price_usd": package.get("price_usd"),
            "payment_asset": package.get("payment_asset"),
            "payment_network": package.get("payment_network"),
            "delivery_format": package.get("delivery_format", "file"),
            "update_frequency": package.get("update_frequency", "on_demand"),
            "signals": package.get("signals", []),
            "supported_chains": package.get(
                "supported_chains",
                package.get("supported_domains", [])
            ),
            "description": package.get("description", ""),
            "public_url": package.get("public_url"),
            "paid_payload_fields": package.get("paid_payload_fields", []),
            "intelligence_features": package.get("intelligence_features", []),
            "status": "discoverable",
            "agent_endpoint": f"/packages/{package_id}",
            "registry_source": "/packages"
        })

    return {
        "node": "Refinery-01",
        "status": "online",
        "mode": "agent_only",
        "bundle_count": len(cards),
        "registry_source": "/packages",
        "frontend_mode": "auto_generated_bundle_cards",

        "discovery": {
            "packages": "/packages",
            "platform_manifest": "/public/refinery.json",
            "agent_manifest": "/public/agent_manifest.json",
            "llms": "/public/llms.txt"
        },

        "payment_endpoints": {
            "usdc_request": "/payments/usdc/request?bundle_id={bundle_id}",
            "usdc_verify": "/payments/usdc/verify?request_id={request_id}&tx_hash={tx_hash}",
            "usdc_bundle": "/payments/usdc/bundle?request_id={request_id}"
        },

        "primary_payment": {
            "asset": "USDC",
            "network": "Polygon"
        },

        "bundle_cards": cards
    }

@app.get("/public/{filename}")
async def public_file(filename: str):
    path = BASE_DIR / "public" / filename

    if not path.exists() or not path.is_file():
        return {"error": "public_file_not_found", "file": filename}

    return FileResponse(path)

@app.get("/packages")
async def packages():

    with open(PACKAGES_PATH, "r") as f:
        return json.load(f)
@app.get("/bundles/defi-liquidation-intel-v1")
async def live_bundle():

    bundle_path = Path(
        "/home/dalien/Refinery-01/vault/datasets/defi-liquidation-intel-v1/bundle.json"
    )

    if not bundle_path.exists():
        return {
            "status": "bundle_not_found"
        }

    with open(bundle_path, "r") as f:
        return json.load(f)
@app.get("/bundles/solana-temporal-intel-v1")
async def solana_bundle():

    bundle_path = Path(
        "/home/dalien/Refinery-01/vault/datasets/solana-temporal-intel-v1/bundle.json"
    )

    if not bundle_path.exists():
        return {
            "status": "bundle_not_found"
        }

    with open(bundle_path, "r") as f:
        return json.load(f)
@app.get("/bundles/xrpl-settlement-intel-v1")
async def xrpl_bundle():

    bundle_path = Path(
        "/home/dalien/Refinery-01/vault/datasets/xrpl-settlement-intel-v1/bundle.json"
    )

    if not bundle_path.exists():
        return {
            "status": "bundle_not_found"
        }

    with open(bundle_path, "r") as f:
        return json.load(f)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "api": "online",
        "xrpl_listener": "connected",
        "archive": "active",
        "bundle_engine": "active"
    }

@app.get("/meta")
async def meta():
    try:
        return build_meta_from_registry()
    except Exception:
        return {
            "platform": "Refinery",
            "node": "Refinery-01",
            "status": "degraded",
            "registry_loaded": False,
            "error": "registry_load_failed",
            "packages_endpoint": "/packages"
        }
@app.get("/payments/usdc/request")
async def usdc_payment_request(bundle_id: str = None, buyer_id: str = "anonymous"):
    if not bundle_id:
        return {
            "error": "missing_bundle_id",
            "usage": "/payments/usdc/request?bundle_id=xrp-etf-temporal-intel-v1"
        }

    try:
        return create_payment_request(bundle_id, buyer_id)
    except Exception as e:
        return {
            "error": "payment_request_failed",
            "detail": str(e)
        }


@app.get("/payments/usdc/access")
async def usdc_payment_access(request_id: str = None):
    if not request_id:
        return {
            "error": "missing_request_id",
            "usage": "/payments/usdc/access?request_id=REQUEST_ID"
        }

    return check_access(request_id)


@app.get("/payments/usdc/bundle")
async def usdc_payment_bundle(request_id: str = None):
    if not request_id:
        return {
            "error": "missing_request_id",
            "usage": "/payments/usdc/bundle?request_id=REQUEST_ID"
        }

    return serve_bundle(request_id)


@app.get("/payments/usdc/verify")
async def usdc_payment_verify(request_id: str = None, tx_hash: str = None):
    if not request_id or not tx_hash:
        return {
            "error": "missing_required_params",
            "usage": "/payments/usdc/verify?request_id=REQUEST_ID&tx_hash=TX_HASH"
        }

    try:
        return verify_transaction(request_id, tx_hash)
    except Exception as e:
        return {
            "error": "verification_exception",
            "detail": str(e)
        }
