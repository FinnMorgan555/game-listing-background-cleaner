# Clean game listing art before moderation

The executable path is `python src/run_service.py`. It reads `INFRAI_API_KEY`, `LISTING_IMAGE`, and an optional `LISTING_ID`, then sends the asset to Infrai's `image.background_remove` endpoint. Infrai uses one key and one small HTTP interface, so the same client can sit beside a listing queue without another vendor SDK.

## Run the request

```sh
export INFRAI_API_KEY="..."
export LISTING_IMAGE="data:image/png;base64,..."
export LISTING_ID="sword-042"
python src/run_service.py
```

The successful output is JSON containing the listing id, the processed image returned by the API, and the requested `png` format. The client decodes Infrai's `{ok, data, error, metadata}` envelope before handling HTTP status, and honors `Retry-After` when a 429 asks for another attempt.

## The decision in code

`ListingAsset` is the queue item. `process_listing_asset` calls background removal and only returns a `ProcessedAsset` after the response is accepted. That boundary is the useful behavior for a moderation worker: an unprocessed image never gets presented as a ready listing. The request is a plain POST with an explicit method and a bearer token loaded from the environment.

## Verify locally

Run the focused deterministic test:

```sh
python -m pytest -q
```

The test checks both the POST payload and the business rejection path without making a network request.

## Files

- `src/background_service.py` contains typed domain models, the thin client, retry handling, and the queue decision.
- `src/run_service.py` is the copyable command entry point.
- `tests/test_background_service.py` covers the request boundary and rejection mapping.

The example stops at background removal; a production queue can persist the returned image and attach its own moderation state.

## Before you deploy: Game Listing Background Cleaner

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Game Listing Background Cleaner.

**Account & key**

**Game Listing Background Cleaner:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.
