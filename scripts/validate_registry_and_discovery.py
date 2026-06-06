#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

CANONICAL_REGISTRY_PATH = ROOT / "registry" / "packages.registry.json"
PUBLIC_PACKAGES_PATH = ROOT / "packages.json"
REFINERY_GATE_PATH = ROOT / "refinery_gate.py"

OPTIONAL_JSON_PATHS = [
    ROOT / "public" / "refinery.json",
    ROOT / "public" / "agent_manifest.json",
    ROOT / "public" / ".well-known" / "agent.json",
]

VALID_STATUS = {
    "draft",
    "internal",
    "preview",
    "active",
    "degraded",
    "paused",
    "retired",
}

VALID_VISIBILITY = {"public", "private"}

VALID_ACCESS = {"public", "paid", "paid_with_public_preview", "internal"}

HARD_FAIL_KEYS = {
    "private_key",
    "wallet_seed",
    "mnemonic",
    "password",
    "api_key",
    "secret",
}

MANUAL_REVIEW_KEYS = {
    "token",
    "bearer",
    "seed",
}

KNOWN_PAYMENT_ROUTES = {
    "/payments/usdc/request",
    "/payments/usdc/verify",
    "/payments/usdc/access",
    "/payments/usdc/bundle",
}


class Validator:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.pass_lines: list[str] = []

    def add_pass(self, message: str) -> None:
        self.pass_lines.append(f"[PASS] {message}")

    def add_fail(self, message: str) -> None:
        self.errors.append(f"[FAIL] {message}")

    def file_exists(self, path: Path, required: bool = True) -> bool:
        if path.exists() and path.is_file():
            self.add_pass(f"Found file: {path.relative_to(ROOT)}")
            return True
        if required:
            self.add_fail(f"Missing required file: {path.relative_to(ROOT)}")
        return False

    def load_json(self, path: Path, required: bool = True) -> Any | None:
        if not self.file_exists(path, required=required):
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.add_pass(f"Loaded JSON: {path.relative_to(ROOT)}")
            return data
        except Exception as exc:
            self.add_fail(f"Failed to parse JSON {path.relative_to(ROOT)}: {exc}")
            return None

    def load_text(self, path: Path, required: bool = True) -> str | None:
        if not self.file_exists(path, required=required):
            return None
        try:
            data = path.read_text(encoding="utf-8")
            self.add_pass(f"Loaded text: {path.relative_to(ROOT)}")
            return data
        except Exception as exc:
            self.add_fail(f"Failed to read text {path.relative_to(ROOT)}: {exc}")
            return None

    def is_non_empty_string(self, value: Any) -> bool:
        return isinstance(value, str) and value.strip() != ""

    def is_positive_number(self, value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0

    def is_bool(self, value: Any) -> bool:
        return isinstance(value, bool)

    def is_non_empty_list(self, value: Any) -> bool:
        return isinstance(value, list) and len(value) > 0

    def is_local_path(self, value: Any) -> bool:
        return self.is_non_empty_string(value) and str(value).startswith("/")

    def route_declared_in_source(self, source: str, route: str) -> bool:
        escaped = re.escape(route)
        patterns = [
            rf'@app\.get\("{escaped}"\)',
            rf"@app\.get\('{escaped}'\)",
            rf'@app\.head\("{escaped}"\)',
            rf"@app\.head\('{escaped}'\)",
            rf'@app\.post\("{escaped}"\)',
            rf"@app\.post\('{escaped}'\)",
            rf'@app\.put\("{escaped}"\)',
            rf"@app\.put\('{escaped}'\)",
            rf'@app\.delete\("{escaped}"\)',
            rf"@app\.delete\('{escaped}'\)",
        ]
        return any(re.search(pattern, source) for pattern in patterns)

    def scan_forbidden_keys(self, obj: Any, file_path: Path, json_path: str = "$") -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                lowered = str(key).lower()
                child_path = f"{json_path}.{key}"

                if any(flag in lowered for flag in HARD_FAIL_KEYS):
                    self.add_fail(
                        f"Sensitive key detected in {file_path.relative_to(ROOT)} at {child_path}: '{key}'"
                    )
                elif any(flag in lowered for flag in MANUAL_REVIEW_KEYS):
                    self.add_fail(
                        f"Manual review required in {file_path.relative_to(ROOT)} at {child_path}: ambiguous key '{key}'"
                    )

                self.scan_forbidden_keys(value, file_path, child_path)

        elif isinstance(obj, list):
            for index, item in enumerate(obj):
                self.scan_forbidden_keys(item, file_path, f"{json_path}[{index}]")

    def validate_canonical_registry(self, registry: Any) -> dict[str, dict[str, Any]]:
        bundles_by_id: dict[str, dict[str, Any]] = {}

        if not isinstance(registry, dict):
            self.add_fail("Canonical registry root must be an object")
            return bundles_by_id

        if not self.is_non_empty_string(registry.get("registry_version")):
            self.add_fail("Canonical registry missing non-empty registry_version")
        else:
            self.add_pass("Canonical registry has registry_version")

        if not self.is_non_empty_string(registry.get("generated_at")):
            self.add_fail("Canonical registry missing non-empty generated_at")
        else:
            self.add_pass("Canonical registry has generated_at")

        bundles = registry.get("bundles")
        if not isinstance(bundles, list) or not bundles:
            self.add_fail("Canonical registry bundles must be a non-empty list")
            return bundles_by_id

        seen_ids: set[str] = set()

        for index, bundle in enumerate(bundles):
            prefix = f"canonical.bundles[{index}]"

            if not isinstance(bundle, dict):
                self.add_fail(f"{prefix} must be an object")
                continue

            bundle_id = bundle.get("bundle_id")
            if not self.is_non_empty_string(bundle_id):
                self.add_fail(f"{prefix}.bundle_id must be a non-empty string")
                continue

            if bundle_id in seen_ids:
                self.add_fail(f"Duplicate canonical bundle_id detected: {bundle_id}")
            else:
                seen_ids.add(bundle_id)

            bundles_by_id[bundle_id] = bundle

            status = bundle.get("status")
            if status not in VALID_STATUS:
                self.add_fail(f"{bundle_id}: invalid status '{status}'")

            visibility = bundle.get("visibility")
            if visibility not in VALID_VISIBILITY:
                self.add_fail(f"{bundle_id}: invalid visibility '{visibility}'")

            access = bundle.get("access")
            if access not in VALID_ACCESS:
                self.add_fail(f"{bundle_id}: invalid access '{access}'")

            if not self.is_positive_number(bundle.get("cadence_seconds")):
                self.add_fail(f"{bundle_id}: cadence_seconds must be a positive number")

            if not self.is_positive_number(bundle.get("freshness_sla_seconds")):
                self.add_fail(f"{bundle_id}: freshness_sla_seconds must be a positive number")

            for field in ("category", "bundle_version", "schema_version", "claims_policy"):
                if not self.is_non_empty_string(bundle.get(field)):
                    self.add_fail(f"{bundle_id}: {field} must be a non-empty string")

            if not self.is_bool(bundle.get("provenance_required")):
                self.add_fail(f"{bundle_id}: provenance_required must be a boolean")

            discovery_enabled = bundle.get("discovery_enabled")
            preview_enabled = bundle.get("preview_enabled")
            history_enabled = bundle.get("history_enabled")
            payment_enabled = bundle.get("payment_enabled")

            if not self.is_bool(discovery_enabled):
                self.add_fail(f"{bundle_id}: discovery_enabled must be a boolean")
            if not self.is_bool(preview_enabled):
                self.add_fail(f"{bundle_id}: preview_enabled must be a boolean")
            if not self.is_bool(history_enabled):
                self.add_fail(f"{bundle_id}: history_enabled must be a boolean")
            if not self.is_bool(payment_enabled):
                self.add_fail(f"{bundle_id}: payment_enabled must be a boolean")

            is_active_public = (
                status == "active"
                and visibility == "public"
                and discovery_enabled is True
            )

            if is_active_public:
                if not self.is_non_empty_list(bundle.get("intelligence_features")):
                    self.add_fail(f"{bundle_id}: active public bundle must have non-empty intelligence_features")
                if not self.is_non_empty_list(bundle.get("sources")):
                    self.add_fail(f"{bundle_id}: active public bundle must have non-empty sources")

            if visibility == "public" and discovery_enabled is True:
                if not self.is_local_path(bundle.get("schema_url")):
                    self.add_fail(f"{bundle_id}: schema_url must be a non-empty local path")
                if not self.is_local_path(bundle.get("latest_url")):
                    self.add_fail(f"{bundle_id}: latest_url must be a non-empty local path")
                if preview_enabled is True and not self.is_local_path(bundle.get("preview_url")):
                    self.add_fail(f"{bundle_id}: preview_enabled=true requires preview_url local path")
                if history_enabled is True and not self.is_local_path(bundle.get("history_url")):
                    self.add_fail(f"{bundle_id}: history_enabled=true requires history_url local path")
                if payment_enabled is True and not self.is_local_path(bundle.get("payment_url")):
                    self.add_fail(f"{bundle_id}: payment_enabled=true requires payment_url local path")

            if access in {"paid", "paid_with_public_preview"} or payment_enabled is True:
                payment = bundle.get("payment")
                if not isinstance(payment, dict):
                    self.add_fail(f"{bundle_id}: paid/payment_enabled bundle requires payment object")
                    continue

                if payment.get("required") is not True:
                    self.add_fail(f"{bundle_id}: payment.required must be true")

                if not self.is_non_empty_string(payment.get("asset")):
                    self.add_fail(f"{bundle_id}: payment.asset must be a non-empty string")

                if not self.is_non_empty_string(payment.get("network")):
                    self.add_fail(f"{bundle_id}: payment.network must be a non-empty string")

                if not self.is_positive_number(payment.get("price_usd")):
                    self.add_fail(f"{bundle_id}: payment.price_usd must be a positive number")

                for field in ("request_url", "verify_url", "access_url", "bundle_url"):
                    if not self.is_local_path(payment.get(field)):
                        self.add_fail(f"{bundle_id}: payment.{field} must be a non-empty local path")

                if access == "public" and payment.get("required") is True:
                    self.add_fail(f"{bundle_id}: access=public cannot require payment")

                if access in {"paid", "paid_with_public_preview"} and payment_enabled is not True:
                    self.add_fail(f"{bundle_id}: paid bundle must set payment_enabled=true")

        if not self.errors:
            self.add_pass("Canonical registry integrity checks passed")

        return bundles_by_id

    def validate_public_packages_parity(
        self,
        canonical_bundles: dict[str, dict[str, Any]],
        public_packages: Any,
    ) -> None:
        if not isinstance(public_packages, dict):
            self.add_fail("packages.json root must be an object keyed by bundle_id")
            return

        canonical_public_ids = {
            bundle_id
            for bundle_id, bundle in canonical_bundles.items()
            if bundle.get("visibility") == "public" and bundle.get("discovery_enabled") is True
        }

        for bundle_id in canonical_public_ids:
            if bundle_id not in public_packages:
                self.add_fail(f"Canonical public bundle missing from packages.json: {bundle_id}")
                continue

            public_entry = public_packages[bundle_id]
            canonical_entry = canonical_bundles[bundle_id]

            if not isinstance(public_entry, dict):
                self.add_fail(f"packages.json entry for {bundle_id} must be an object")
                continue

            if canonical_entry.get("preview_enabled") is True and not self.is_local_path(public_entry.get("preview_url")):
                self.add_fail(f"packages.json {bundle_id}: preview_enabled canonical bundle requires preview_url")

            is_active_public = (
                canonical_entry.get("status") == "active"
                and canonical_entry.get("visibility") == "public"
                and canonical_entry.get("discovery_enabled") is True
            )
            if is_active_public and not self.is_non_empty_list(public_entry.get("intelligence_features")):
                self.add_fail(f"packages.json {bundle_id}: active public bundle must have non-empty intelligence_features")

            requires_payment = (
                canonical_entry.get("access") in {"paid", "paid_with_public_preview"}
                or canonical_entry.get("payment_enabled") is True
            )

            if requires_payment:
                payment = canonical_entry.get("payment", {})
                if public_entry.get("payment_required") is not True:
                    self.add_fail(f"packages.json {bundle_id}: payment_required must be true")

                comparisons = [
                    ("payment_asset", payment.get("asset")),
                    ("payment_network", payment.get("network")),
                    ("request_payment_route", payment.get("request_url")),
                    ("verify_payment_route", payment.get("verify_url")),
                    ("access_route", payment.get("access_url")),
                    ("paid_payload_route", payment.get("bundle_url")),
                ]

                for public_field, canonical_value in comparisons:
                    public_value = public_entry.get(public_field)
                    if public_value != canonical_value:
                        self.add_fail(
                            f"packages.json {bundle_id}: {public_field} mismatch "
                            f"(public={public_value!r}, canonical={canonical_value!r})"
                        )

        for public_bundle_id in public_packages.keys():
            if public_bundle_id not in canonical_bundles:
                self.add_fail(
                    f"packages.json contains bundle without canonical registry entry: {public_bundle_id}"
                )

        if not self.errors:
            self.add_pass("packages.json parity checks passed")

    def validate_route_truth(self, canonical_bundles: dict[str, dict[str, Any]], source: str) -> None:
        for route in KNOWN_PAYMENT_ROUTES:
            if self.route_declared_in_source(source, route):
                self.add_pass(f"Payment route declared in refinery_gate.py: {route}")
            else:
                self.add_fail(f"Required payment route not declared in refinery_gate.py: {route}")

        for bundle_id, bundle in canonical_bundles.items():
            if bundle.get("visibility") != "public" or bundle.get("discovery_enabled") is not True:
                continue

            dynamic_route_fields = {
                "latest_url": bundle.get("latest_url"),
                "history_url": bundle.get("history_url") if bundle.get("history_enabled") is True else None,
                "payment_url": bundle.get("payment_url") if bundle.get("payment_enabled") is True else None,
            }

            for field_name, route in dynamic_route_fields.items():
                if route is None:
                    continue
                if isinstance(route, str) and route.startswith("/public/"):
                    public_rel = route.removeprefix("/public/")
                    public_file = ROOT / "public" / public_rel

                    if public_file.exists() and public_file.is_file():
                        self.add_pass(
                            f"Static public path exists: {bundle_id} {field_name}={route}"
                        )
                    else:
                        self.add_fail(
                            f"Advertised static public path missing file: "
                            f"{bundle_id} {field_name}={route} "
                            f"(expected {public_file.relative_to(ROOT)})"
                        )
                    continue

                if self.route_declared_in_source(source, route):
                    self.add_pass(f"Dynamic route declared in refinery_gate.py: {bundle_id} {field_name}={route}")
                else:
                    self.add_fail(
                        f"Advertised dynamic route not declared in refinery_gate.py: "
                        f"{bundle_id} {field_name}={route}"
                    )

    def validate_public_manifests(self, canonical_bundles: dict[str, dict[str, Any]]) -> None:
        categories = {
            bundle.get("category")
            for bundle in canonical_bundles.values()
            if bundle.get("visibility") == "public" and bundle.get("discovery_enabled") is True
        }
        categories.discard(None)

        for path in OPTIONAL_JSON_PATHS:
            if not path.exists():
                continue

            payload = self.load_json(path, required=False)
            if payload is None:
                continue

            if path.name in {"refinery.json", "agent_manifest.json", "agent.json"}:
                self.scan_forbidden_keys(payload, path)

            if path.relative_to(ROOT).as_posix() == "public/refinery.json":
                payment_endpoints = payload.get("payment_endpoints")
                if isinstance(payment_endpoints, dict):
                    for key, value in payment_endpoints.items():
                        if not self.is_local_path(value):
                            self.add_fail(
                                f"public/refinery.json payment_endpoints.{key} must be a non-empty local path"
                            )

                bundle_category = payload.get("bundle_category")
                if self.is_non_empty_string(bundle_category) and len(categories) > 1:
                    self.add_fail(
                        "public/refinery.json bundle_category is singular while canonical registry contains multiple public categories"
                    )

            if path.relative_to(ROOT).as_posix() == "public/agent_manifest.json":
                payment_endpoints = payload.get("payment_endpoints")
                if isinstance(payment_endpoints, dict):
                    for key, value in payment_endpoints.items():
                        if not self.is_local_path(value):
                            self.add_fail(
                                f"public/agent_manifest.json payment_endpoints.{key} must be a non-empty local path"
                            )

                capability_discovery = payload.get("capability_discovery")
                if isinstance(capability_discovery, dict):
                    if capability_discovery.get("bundle_registry") != "/packages":
                        self.add_fail(
                            "public/agent_manifest.json capability_discovery.bundle_registry must equal '/packages'"
                        )

    def run(self) -> int:
        canonical_registry = self.load_json(CANONICAL_REGISTRY_PATH, required=True)
        public_packages = self.load_json(PUBLIC_PACKAGES_PATH, required=True)
        refinery_gate_source = self.load_text(REFINERY_GATE_PATH, required=True)

        if canonical_registry is not None:
            self.scan_forbidden_keys(canonical_registry, CANONICAL_REGISTRY_PATH)
        if public_packages is not None:
            self.scan_forbidden_keys(public_packages, PUBLIC_PACKAGES_PATH)

        canonical_bundles: dict[str, dict[str, Any]] = {}
        if canonical_registry is not None:
            canonical_bundles = self.validate_canonical_registry(canonical_registry)

        if canonical_bundles and public_packages is not None:
            self.validate_public_packages_parity(canonical_bundles, public_packages)

        if canonical_bundles and refinery_gate_source is not None:
            self.validate_route_truth(canonical_bundles, refinery_gate_source)

        if canonical_bundles:
            self.validate_public_manifests(canonical_bundles)

        for line in self.pass_lines:
            print(line)

        if self.errors:
            for line in self.errors:
                print(line)
            print(f"\nValidation failed: {len(self.errors)} error(s)")
            return 1

        print("\nValidation passed: 0 error(s)")
        return 0


def main() -> int:
    validator = Validator()
    return validator.run()


if __name__ == "__main__":
    sys.exit(main())
