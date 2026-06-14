from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from pathlib import Path
from datetime import datetime, timezone
import base64
import json
from vault.payments.usdc.verify_polygon_rpc_tx import verify_transaction
from vault.payments.usdc.verifier import create_payment_request
from vault.payments.usdc.check_access import check_access
from vault.payments.usdc.serve_bundle import (
    serve_bundle,
    serve_bundle_response,
)
from refinery_bundle_loader import load_bundle_payload

from x402 import x402ResourceServer
from x402.http import HTTPFacilitatorClient
from x402.http.middleware.fastapi import payment_middleware
from x402.mechanisms.evm.exact.server import ExactEvmScheme

BASE_DIR = Path(__file__).resolve().parent
PACKAGES_PATH = BASE_DIR / "packages.json"
CANONICAL_REGISTRY_PATH = BASE_DIR / "registry" / "packages.registry.json"
X402_CONFIG_PATH = BASE_DIR / "config" / "x402.json"
X402_AUDIT_PATH = BASE_DIR / "logs" / "x402_audit.jsonl"


def load_x402_config():
    if not X402_CONFIG_PATH.exists():
        raise RuntimeError(f"x402 configuration missing: {X402_CONFIG_PATH}")

    config = json.loads(X402_CONFIG_PATH.read_text())

    required = (
        "enabled",
        "environment",
        "bundle_id",
        "route",
        "network",
        "facilitator_url",
        "receiver_address",
        "description",
        "mime_type",
    )

    missing = [key for key in required if key not in config]

    if missing:
        raise RuntimeError(
            "x402 configuration missing fields: " + ", ".join(missing)
        )

    if not str(config["route"]).startswith("/x402/"):
        raise RuntimeError("x402 route must remain under /x402/")

    return config


def load_registry_bundle(bundle_id):
    registry = json.loads(CANONICAL_REGISTRY_PATH.read_text())

    bundle = next(
        (
            item
            for item in registry.get("bundles", [])
            if item.get("bundle_id") == bundle_id
        ),
        None,
    )

    if bundle is None:
        raise RuntimeError(
            f"x402 bundle missing from canonical registry: {bundle_id}"
        )

    if bundle.get("status") != "active":
        raise RuntimeError(
            f"x402 bundle is not active: {bundle_id}"
        )

    if not bundle.get("payment_enabled"):
        raise RuntimeError(
            f"x402 bundle is not payment enabled: {bundle_id}"
        )

    price = bundle.get("price_usd")

    if price is None:
        price = bundle.get("payment", {}).get("price_usd")

    if not isinstance(price, (int, float)) or price <= 0:
        raise RuntimeError(
            f"invalid canonical x402 price for {bundle_id}: {price!r}"
        )

    return bundle, float(price)


def decode_x402_header(value):
    if not value:
        return None

    try:
        padding = "=" * (-len(value) % 4)
        decoded = base64.b64decode(value + padding)
        return json.loads(decoded.decode("utf-8"))
    except Exception:
        return {
            "decode_error": True,
            "encoded_length": len(value),
        }


def append_x402_audit(record):
    X402_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with X402_AUDIT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                record,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        )


X402_CONFIG = load_x402_config()
X402_BUNDLE_ID = X402_CONFIG["bundle_id"]
X402_ROUTE = X402_CONFIG["route"]
X402_TEST_NETWORK = X402_CONFIG["network"]
X402_TEST_FACILITATOR = X402_CONFIG["facilitator_url"]
X402_RECEIVER_ADDRESS = X402_CONFIG["receiver_address"]
X402_ENVIRONMENT = X402_CONFIG["environment"]

X402_REGISTRY_BUNDLE, X402_PRICE_USD = load_registry_bundle(
    X402_BUNDLE_ID
)

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

if X402_CONFIG["enabled"]:
    x402_facilitator = HTTPFacilitatorClient({
        "url": X402_TEST_FACILITATOR
    })

    x402_server = x402ResourceServer(x402_facilitator)
    x402_server.register(
        X402_TEST_NETWORK,
        ExactEvmScheme()
    )

    x402_routes = {
        f"GET {X402_ROUTE}": {
            "accepts": [
                {
                    "scheme": "exact",
                    "price": f"${X402_PRICE_USD:.2f}",
                    "network": X402_TEST_NETWORK,
                    "payTo": X402_RECEIVER_ADDRESS
                }
            ],
            "description": X402_CONFIG["description"],
            "mimeType": X402_CONFIG["mime_type"]
        }
    }

    app.middleware("http")(
        payment_middleware(
            routes=x402_routes,
            server=x402_server,
            sync_facilitator_on_start=True
        )
    )


@app.middleware("http")
async def x402_audit_middleware(request: Request, call_next):
    if request.url.path != X402_ROUTE:
        return await call_next(request)

    started_at = datetime.now(timezone.utc)
    payment_signature_present = bool(
        request.headers.get("payment-signature")
    )

    try:
        response = await call_next(request)
    except Exception as exc:
        append_x402_audit({
            "timestamp": started_at.isoformat(),
            "event": "handler_error",
            "route": X402_ROUTE,
            "bundle_id": X402_BUNDLE_ID,
            "environment": X402_ENVIRONMENT,
            "network": X402_TEST_NETWORK,
            "price_usd": X402_PRICE_USD,
            "payment_signature_present": payment_signature_present,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
        })
        raise

    payment_required = response.headers.get("payment-required")
    payment_response = response.headers.get("payment-response")

    if response.status_code == 402:
        event = "payment_required"
    elif response.status_code == 200 and payment_response:
        event = "settled_delivery"
    elif response.status_code == 200:
        event = "delivery_without_settlement_header"
    else:
        event = "unexpected_response"

    append_x402_audit({
        "timestamp": started_at.isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "route": X402_ROUTE,
        "method": request.method,
        "status_code": response.status_code,
        "bundle_id": X402_BUNDLE_ID,
        "environment": X402_ENVIRONMENT,
        "network": X402_TEST_NETWORK,
        "price_usd": X402_PRICE_USD,
        "receiver_address": X402_RECEIVER_ADDRESS,
        "payment_signature_present": payment_signature_present,
        "payment_required": decode_x402_header(payment_required),
        "payment_response": decode_x402_header(payment_response),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "cf_ray": request.headers.get("cf-ray"),
    })

    return response


app.mount("/public", StaticFiles(directory="public"), name="public")


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

        explicit_signal_count = bundle.get("signal_count")

        if isinstance(explicit_signal_count, int) and explicit_signal_count >= 0:
            signal_count = explicit_signal_count
        elif isinstance(signals, list):
            signal_count = len(signals)
        else:
            signal_count = 0

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

    if isinstance(packages, dict) and isinstance(packages.get("bundles"), dict):
        package_items = packages["bundles"].items()
    elif isinstance(packages, dict) and isinstance(packages.get("bundles"), list):
        package_items = [
            (
                package.get("bundle_id") or package.get("id") or f"package_{i}",
                package
            )
            for i, package in enumerate(packages["bundles"])
            if isinstance(package, dict)
        ]
    elif isinstance(packages, dict):
        package_items = [
            (package_id, package)
            for package_id, package in packages.items()
            if isinstance(package, dict)
        ]
    elif isinstance(packages, list):
        package_items = [
            (
                package.get("bundle_id") or package.get("id") or f"package_{i}",
                package
            )
            for i, package in enumerate(packages)
            if isinstance(package, dict)
        ]
    else:
        package_items = []

    for package_id, package in package_items:
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

@app.get("/agent-buy.json")
@app.head("/agent-buy.json")
def agent_buy():
    return json_file_response("public/agent-buy.json")

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

@app.get(X402_ROUTE)
async def x402_test_solana_bundle():
    result = load_bundle_payload(X402_BUNDLE_ID)

    if not result.get("access"):
        return JSONResponse(
            status_code=404,
            content=result
        )

    return {
        "payment_protocol": "x402",
        "payment_environment": X402_ENVIRONMENT,
        "network": X402_TEST_NETWORK,
        "bundle_id": X402_BUNDLE_ID,
        "price_usd": X402_PRICE_USD,
        "access": True,
        "payload": result["payload"]
    }


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

    return serve_bundle_response(request_id)


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
