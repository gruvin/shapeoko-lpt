#!/usr/bin/env python3
"""
element14 Product Search API client.

Rate limits: 2 calls/sec, 1000 calls/day.
Every response is cached on disk (bom/cache/) so re-runs cost zero quota.

Store selection matters: the NZ store has thinner stock than AU. The caller
passes a store per call; `STORES` is the fallback order used by resolve.py.

Usage:
    from e14 import E14
    api = E14()
    api.by_mpn("MCSR06X3300FTL", store="nz.element14.com")
    api.by_sku("2074240")
    api.keyword("ceramic resonator 16MHz")
"""

import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "bom" / "cache"
BASE = "https://api.element14.com/catalog/products"

# Stay just under 2 calls/sec. Only applies to real network hits (cache misses).
MIN_INTERVAL = 0.55

ORDERABLE = ("STOCKED", "DIRECT_SHIP")


def _load_env() -> dict:
    env = {}
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    env.update(os.environ)
    return env


class E14Error(RuntimeError):
    pass


class E14:
    def __init__(self) -> None:
        env = _load_env()
        self.key = env.get("E14_API_KEY", "")
        self.store = env.get("E14_STORE", "nz.element14.com")
        raw = env.get("E14_STORES", "")
        self.stores = [s.strip() for s in raw.split(",") if s.strip()] or [
            self.store,
            "au.element14.com",
            "uk.farnell.com",
        ]
        if not self.key:
            raise E14Error("E14_API_KEY missing (expected in .env)")
        CACHE.mkdir(parents=True, exist_ok=True)
        self.refresh = os.environ.get("E14_REFRESH", "").strip().lower() in (
            "1", "true", "yes", "on")
        self._last = 0.0
        self.network_calls = 0
        self.cache_hits = 0

    # -- internals ---------------------------------------------------------
    def _cache_path(self, params: dict) -> Path:
        key = json.dumps(params, sort_keys=True)
        h = hashlib.sha256(key.encode()).hexdigest()[:16]
        # MPNs can contain '/', ',', ' ' etc. -- keep the label filesystem-safe
        raw = f"{params.get('storeInfo.id','')}_{params.get('term','x')}"
        label = "".join(c if (c.isalnum() or c in "-_") else "_" for c in raw)[:48]
        return CACHE / f"{label}_{h}.json"

    def _get(self, params: dict) -> dict:
        q = dict(params)
        q.setdefault("storeInfo.id", self.store)
        q["callInfo.responseDataFormat"] = "JSON"
        q["callInfo.apiKey"] = self.key
        q.setdefault("resultsSettings.responseGroup", "large")

        cp = self._cache_path(q)
        # Responses are cached forever, which is right for re-runs but wrong
        # weeks later: stock and pricing go stale silently. Set E14_REFRESH=1
        # to ignore the cache and re-fetch everything.
        if cp.exists() and not self.refresh:
            self.cache_hits += 1
            return json.loads(cp.read_text())

        url = f"{BASE}?{urllib.parse.urlencode(q)}"

        for attempt in range(4):
            dt = time.monotonic() - self._last
            if dt < MIN_INTERVAL:
                time.sleep(MIN_INTERVAL - dt)
            try:
                with urllib.request.urlopen(url, timeout=30) as r:
                    self._last = time.monotonic()
                    self.network_calls += 1
                    data = json.loads(r.read().decode("utf-8", "replace"))
                break
            except Exception as e:  # noqa: BLE001
                self._last = time.monotonic()
                if attempt == 3:
                    raise E14Error(f"request failed: {e}") from e
                time.sleep(1.5 * (attempt + 1))

        cp.write_text(json.dumps(data, indent=1))
        return data

    @staticmethod
    def _unwrap(data: dict) -> list[dict]:
        if not isinstance(data, dict):
            return []
        for wrapper in (
            "manufacturerPartNumberSearchReturn",
            "premierFarnellPartNumberReturn",
            "keywordSearchReturn",
            "manufacturerPartNumberSearchReturn",
        ):
            if wrapper in data:
                return data[wrapper].get("products") or []
        return []

    # -- public ------------------------------------------------------------
    def by_sku(self, sku: str, store: str | None = None) -> list[dict]:
        return self._unwrap(
            self._get({"term": f"id:{sku}", "storeInfo.id": store or self.store})
        )

    def by_mpn(self, mpn: str, store: str | None = None, exact: bool = True) -> list[dict]:
        p = {
            "term": f"manuPartNum:{mpn}",
            "storeInfo.id": store or self.store,
            "resultsSettings.responseGroup": "large",
        }
        if exact:
            p["resultsSettings.matchIncluded"] = "exactMatch"
        return self._unwrap(self._get(p))

    def lookup(self, token: str, store: str | None = None) -> list[dict]:
        """Resolve a token that might be an element14 order code OR a numeric MPN.

        Phoenix Contact MPNs (1725656) are indistinguishable from element14
        order codes (2074240) by shape alone, so try the order-code endpoint
        first and fall back to the MPN endpoint.
        """
        out = self.by_sku(token, store)
        if out:
            return out
        return self.by_mpn(token, store)

    def keyword(self, text: str, store: str | None = None, n: int = 10,
                in_stock: bool = False) -> list[dict]:
        p = {
            "term": f"any:{text}",
            "storeInfo.id": store or self.store,
            "resultsSettings.offset": 0,
            "resultsSettings.numberOfResults": n,
            "resultsSettings.responseGroup": "large",
        }
        if in_stock:
            p["resultsSettings.refinements.filters"] = "inStock"
        return self._unwrap(self._get(p))


# -- normalisation helpers -------------------------------------------------

def attrs(product: dict) -> dict[str, str]:
    return {
        (a.get("attributeLabel") or ""): (a.get("attributeValue") or "")
        for a in product.get("attributes") or []
    }


def attr(product: dict, label: str) -> str | None:
    """Case-insensitive attribute lookup."""
    want = label.lower()
    for a in product.get("attributes") or []:
        if (a.get("attributeLabel") or "").lower() == want:
            return a.get("attributeValue")
    return None


def moq_of(p: dict) -> int:
    try:
        return int(p.get("translatedMinimumOrderQuality") or 0)
    except (TypeError, ValueError):
        return 0


def unit_price(product: dict, qty: int) -> float | None:
    """Unit price for the given quantity, honouring price breaks."""
    breaks = []
    for br in product.get("prices") or []:
        try:
            breaks.append((int(br.get("from") or 0), float(br.get("cost"))))
        except (TypeError, ValueError):
            continue
    if not breaks:
        return None
    breaks.sort()
    price = breaks[0][1]
    for lo, cost in breaks:
        if lo <= qty:
            price = cost
    return price


def is_orderable(p: dict) -> bool:
    return (p.get("productStatus") or "") in ORDERABLE


def is_reel(p: dict) -> bool:
    """True if this is a full reel rather than individual parts.

    element14 exposes an explicit `reeling` boolean; that is authoritative.
    The 'RL' SKU suffix is a strong hint but not reliable on its own (and there
    are SKUs that look like reels but are not), so it is only a fallback.
    """
    flag = p.get("reeling")
    if isinstance(flag, bool):
        return flag
    if isinstance(flag, str):
        return flag.strip().lower() in ("true", "yes", "1")
    return str(p.get("sku", "")).upper().endswith("RL")


def pack_size(p: dict) -> int:
    try:
        return int(p.get("packSize") or 1)
    except (TypeError, ValueError):
        return 1


def score(p: dict, qty: int) -> tuple:
    """Sort key: lower is better."""
    inv = p.get("inv") or 0
    moq = moq_of(p) or 1
    return (
        inv <= 0,                 # in stock first
        not is_orderable(p),      # then orderable
        is_reel(p),               # never a full reel if cut-tape exists
        pack_size(p) > 1,         # nor a multi-pack
        moq,                      # then lowest MOQ
        unit_price(p, max(qty, moq)) or 9e9,
        # Finally prefer the shortest order code: element14 carries duplicate
        # listings (1012247 vs 101224701) for the same part, and the plain
        # 7-digit code is the one that also works in their BOM upload tool.
        len(str(p.get("sku", ""))),
    )


def short(p: dict) -> str:
    return (
        f"{p.get('translatedManufacturerPartNumber')} "
        f"[{p.get('sku')}] {p.get('productStatus')} "
        f"inv={p.get('inv')} moq={moq_of(p)}"
    )


if __name__ == "__main__":
    import sys

    api = E14()
    for mpn in sys.argv[1:]:
        print(f"--- {mpn}")
        for st in api.stores:
            base = api.by_mpn(mpn, store=st)
            exact = [
                p for p in base
                if (p.get("translatedManufacturerPartNumber") or "").lower() == mpn.lower()
            ]
            if not exact:
                print(f"   {st:<20} not found")
                continue
            best = sorted(exact, key=lambda p: score(p, 1))[0]
            print(f"   {st:<20} {short(best)}")
    print(f"\nnetwork={api.network_calls} cache={api.cache_hits}")
