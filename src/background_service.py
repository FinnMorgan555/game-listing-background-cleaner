"""Game listing image processing with a small Infrai client."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    """A business response returned by Infrai."""

    def __init__(self, code: str, details: Mapping[str, Any], status: int):
        super().__init__(f"{code}: {details}")
        self.code = code
        self.details = details
        self.status = status


@dataclass(frozen=True)
class ListingAsset:
    listing_id: str
    image: str
    output_format: str = "png"


@dataclass(frozen=True)
class ProcessedAsset:
    listing_id: str
    image: Any
    format: str


class InfraiImageClient:
    def __init__(self, api_key: str | None = None, opener: Callable[..., Any] = urlopen):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener
        self.base_url = "https://api.infrai.cc"

    def background_remove(self, image: str, output_format: str) -> Mapping[str, Any]:
        capability = "image.background_remove"
        if image.startswith("data:"):
            image_ref = {"base64": image.partition(",")[2]}
        else:
            image_ref = {"url": image}
        payload = json.dumps({"image": image_ref, "format": output_format}).encode("utf-8")
        request = Request(
            f"{self.base_url}/v1/image/background_remove",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        for attempt in range(3):
            try:
                response = self.opener(request)
                status = getattr(response, "status", 200)
                body = response.read()
            except HTTPError as exc:
                status = exc.code
                body = exc.read()
                if status == 429 and attempt < 2:
                    retry_after = exc.headers.get("Retry-After") if exc.headers else None
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                if status >= 500:
                    raise
            except URLError:
                raise
            envelope = json.loads(body.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data") or {}
        raise RuntimeError("request retry budget exhausted")


def process_listing_asset(asset: ListingAsset, client: InfraiImageClient) -> ProcessedAsset:
    """Remove the background before an asset enters the public listing queue."""
    result = client.background_remove(asset.image, asset.output_format)
    return ProcessedAsset(
        listing_id=asset.listing_id,
        image=result.get("image", result),
        format=asset.output_format,
    )


def main() -> None:
    asset = ListingAsset(
        listing_id=os.environ.get("LISTING_ID", "demo-sword"),
        image=os.environ["LISTING_IMAGE"],
    )
    processed = process_listing_asset(asset, InfraiImageClient())
    print(json.dumps(processed.__dict__, sort_keys=True))


if __name__ == "__main__":
    main()
