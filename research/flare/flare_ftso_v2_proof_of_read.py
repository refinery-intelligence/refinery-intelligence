#!/usr/bin/env python3
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Tuple


RPC_URL = "https://flare-api.flare.network/ext/C/rpc"
REGISTRY_ADDRESS = "0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019"
FTSO_CONTRACT_NAME = "FtsoV2"

FEEDS: List[Dict[str, str]] = [
    {
        "symbol": "FLR/USD",
        "feed_id": "0x01464c522f55534400000000000000000000000000",
        "source": "official Flare feed docs",
    },
    {
        "symbol": "XRP/USD",
        "feed_id": "0x015852502f55534400000000000000000000000000",
        "source": "official Flare feed docs",
    },
]

_MASK_64 = (1 << 64) - 1
_KECCAKF_ROUNDS = 24
_KECCAKF_RNDC = [
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
]
_KECCAKF_ROTC = [
    1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 2, 14,
    27, 41, 56, 8, 25, 43, 62, 18, 39, 61, 20, 44,
]
_KECCAKF_PILN = [
    10, 7, 11, 17, 18, 3, 5, 16, 8, 21, 24, 4,
    15, 23, 19, 13, 12, 2, 20, 14, 22, 9, 6, 1,
]


def _rol64(value: int, shift: int) -> int:
    return ((value << shift) | (value >> (64 - shift))) & _MASK_64


def _keccak_f1600(state: List[int]) -> None:
    for rnd in range(_KECCAKF_ROUNDS):
        bc = [0] * 5
        for i in range(5):
            bc[i] = state[i] ^ state[i + 5] ^ state[i + 10] ^ state[i + 15] ^ state[i + 20]

        for i in range(5):
            t = bc[(i - 1) % 5] ^ _rol64(bc[(i + 1) % 5], 1)
            for j in range(0, 25, 5):
                state[j + i] ^= t

        t = state[1]
        for i in range(24):
            j = _KECCAKF_PILN[i]
            state[j], t = _rol64(t, _KECCAKF_ROTC[i]), state[j]

        for j in range(0, 25, 5):
            row = state[j:j + 5]
            for i in range(5):
                state[j + i] = row[i] ^ ((~row[(i + 1) % 5]) & row[(i + 2) % 5])

        state[0] ^= _KECCAKF_RNDC[rnd]


def keccak256(data: bytes) -> bytes:
    rate = 136
    state = [0] * 25
    offset = 0

    while offset + rate <= len(data):
        block = data[offset:offset + rate]
        for i in range(rate // 8):
            lane = int.from_bytes(block[i * 8:(i + 1) * 8], "little")
            state[i] ^= lane
        _keccak_f1600(state)
        offset += rate

    tail = bytearray(data[offset:])
    tail.append(0x01)
    while len(tail) < rate:
        tail.append(0x00)
    tail[-1] ^= 0x80

    for i in range(rate // 8):
        lane = int.from_bytes(tail[i * 8:(i + 1) * 8], "little")
        state[i] ^= lane
    _keccak_f1600(state)

    out = bytearray()
    while len(out) < 32:
        for lane in state[: rate // 8]:
            out.extend(lane.to_bytes(8, "little"))
            if len(out) >= 32:
                break
        if len(out) < 32:
            _keccak_f1600(state)

    return bytes(out[:32])


def function_selector(signature: str) -> str:
    return keccak256(signature.encode("utf-8"))[:4].hex()


def rpad_32(data: bytes) -> bytes:
    if len(data) > 32:
        raise ValueError("value exceeds 32 bytes")
    return data + (b"\x00" * (32 - len(data)))


def encode_uint256(value: int) -> bytes:
    return value.to_bytes(32, "big")


def encode_string(value: str) -> bytes:
    raw = value.encode("utf-8")
    padded_len = ((len(raw) + 31) // 32) * 32
    return encode_uint256(len(raw)) + raw + (b"\x00" * (padded_len - len(raw)))


def encode_bytes21_array(values: List[str]) -> bytes:
    encoded = bytearray()
    encoded.extend(encode_uint256(len(values)))
    for item in values:
        raw = bytes.fromhex(item.removeprefix("0x"))
        if len(raw) != 21:
            raise ValueError(f"bytes21 value must be 21 bytes, got {len(raw)}: {item}")
        encoded.extend(rpad_32(raw))
    return bytes(encoded)


def make_call_data(signature: str, encoded_args: bytes) -> str:
    return "0x" + function_selector(signature) + encoded_args.hex()


def make_single_string_call(signature: str, value: str) -> str:
    return make_call_data(signature, encode_uint256(32) + encode_string(value))


def make_single_bytes21_array_call(signature: str, values: List[str]) -> str:
    return make_call_data(signature, encode_uint256(32) + encode_bytes21_array(values))


def rpc(method: str, params: List[Any]) -> Any:
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode("utf-8")
    request = urllib.request.Request(
        RPC_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"RPC HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"RPC connection failed: {exc}") from exc

    parsed = json.loads(body)
    if "error" in parsed:
        raise RuntimeError(f"RPC error: {parsed['error']}")
    return parsed["result"]


def eth_call(to: str, data: str, block: str = "latest") -> str:
    return rpc("eth_call", [{"to": to, "data": data}, block])


def eth_block_number() -> int:
    return int(rpc("eth_blockNumber", []), 16)


def hex_to_bytes(result_hex: str) -> bytes:
    return bytes.fromhex(result_hex.removeprefix("0x"))


def read_word(blob: bytes, index: int) -> bytes:
    start = index * 32
    end = start + 32
    return blob[start:end]


def read_uint(blob: bytes, index: int) -> int:
    return int.from_bytes(read_word(blob, index), "big")


def decode_address(result_hex: str) -> str:
    blob = hex_to_bytes(result_hex)
    return "0x" + blob[12:32].hex()


def decode_uint_array(blob: bytes, byte_offset: int) -> List[int]:
    length = int.from_bytes(blob[byte_offset:byte_offset + 32], "big")
    out: List[int] = []
    cursor = byte_offset + 32
    for _ in range(length):
        out.append(int.from_bytes(blob[cursor:cursor + 32], "big"))
        cursor += 32
    return out


def decode_int_array(blob: bytes, byte_offset: int) -> List[int]:
    length = int.from_bytes(blob[byte_offset:byte_offset + 32], "big")
    out: List[int] = []
    cursor = byte_offset + 32
    for _ in range(length):
        out.append(int.from_bytes(blob[cursor:cursor + 32], "big", signed=True))
        cursor += 32
    return out


def decode_get_feeds_by_id(result_hex: str) -> Tuple[List[int], List[int], int]:
    blob = hex_to_bytes(result_hex)
    values_offset = read_uint(blob, 0)
    decimals_offset = read_uint(blob, 1)
    timestamp = read_uint(blob, 2)
    return decode_uint_array(blob, values_offset), decode_int_array(blob, decimals_offset), timestamp


def decode_get_feeds_by_id_in_wei(result_hex: str) -> Tuple[List[int], int]:
    blob = hex_to_bytes(result_hex)
    values_offset = read_uint(blob, 0)
    timestamp = read_uint(blob, 1)
    return decode_uint_array(blob, values_offset), timestamp


def normalize_to_wei(value: int, decimals: int) -> int:
    if decimals == 18:
        return value
    if decimals < 18:
        return value * (10 ** (18 - decimals))
    return value // (10 ** (decimals - 18))


def resolve_ftso_v2_address() -> Tuple[str, Dict[str, Any]]:
    call_data = make_single_string_call("getContractAddressByName(string)", FTSO_CONTRACT_NAME)
    result = eth_call(REGISTRY_ADDRESS, call_data)
    address = decode_address(result)
    return address, {
        "registry_address": REGISTRY_ADDRESS,
        "registry_method_signature": "getContractAddressByName(string)",
        "registry_method_selector": "0x" + function_selector("getContractAddressByName(string)"),
        "registry_contract_name": FTSO_CONTRACT_NAME,
        "resolved_address": address,
        "assumption": 'Contract name "FtsoV2" is used by Flare ContractRegistry as recommended by Flare docs and examples.',
    }


def read_feeds(ftso_v2_address: str) -> Dict[str, Any]:
    feed_ids = [item["feed_id"] for item in FEEDS]

    raw_values, decimals, raw_timestamp = decode_get_feeds_by_id(
        eth_call(ftso_v2_address, make_single_bytes21_array_call("getFeedsById(bytes21[])", feed_ids))
    )
    wei_values, wei_timestamp = decode_get_feeds_by_id_in_wei(
        eth_call(ftso_v2_address, make_single_bytes21_array_call("getFeedsByIdInWei(bytes21[])", feed_ids))
    )

    now = int(time.time())
    feeds: List[Dict[str, Any]] = []

    for index, item in enumerate(FEEDS):
        timestamp = int(wei_timestamp or raw_timestamp)
        feeds.append(
            {
                "symbol": item["symbol"],
                "feed_id": item["feed_id"],
                "value_raw": str(raw_values[index]),
                "decimals": int(decimals[index]),
                "value_wei": str(wei_values[index]),
                "value_wei_computed_from_raw": str(normalize_to_wei(raw_values[index], decimals[index])),
                "timestamp": timestamp,
                "staleness_seconds": max(0, now - timestamp) if timestamp else None,
                "source": item["source"],
            }
        )

    return {
        "ftso_read": {
            "ftso_v2_address": ftso_v2_address,
            "getFeedsById": {
                "signature": "getFeedsById(bytes21[])",
                "selector": "0x" + function_selector("getFeedsById(bytes21[])"),
                "timestamp": int(raw_timestamp),
            },
            "getFeedsByIdInWei": {
                "signature": "getFeedsByIdInWei(bytes21[])",
                "selector": "0x" + function_selector("getFeedsByIdInWei(bytes21[])"),
                "timestamp": int(wei_timestamp),
            },
            "feeds": feeds,
        }
    }


def main() -> int:
    started_at = int(time.time())
    out: Dict[str, Any] = {
        "ok": False,
        "network": {
            "name": "Flare Mainnet",
            "rpc_url": RPC_URL,
            "chain_id_expected": 14,
        },
        "sources": {
            "contract_path": "Flare Contract Registry -> FtsoV2",
            "registry_address": REGISTRY_ADDRESS,
            "registry_contract_name": FTSO_CONTRACT_NAME,
            "feed_ids": {item["symbol"]: item["feed_id"] for item in FEEDS},
        },
        "assumptions": [
            'Registry contract name "FtsoV2" is assumed from Flare docs/examples and may need adjustment if Flare renames the registry key.',
            "Feed IDs are taken from the official Flare feed docs.",
        ],
        "timestamp": started_at,
    }

    try:
        out["block_number"] = eth_block_number()
        ftso_v2_address, registry_meta = resolve_ftso_v2_address()
        out["registry_resolution"] = registry_meta
        out.update(read_feeds(ftso_v2_address))
        out["ok"] = True
    except BrokenPipeError:
        return 0
    except Exception as exc:
        out["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }

    try:
        print(json.dumps(out, indent=2, sort_keys=False))
    except BrokenPipeError:
        return 0
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
