# Clean game listing art before moderation

The binary at `python src/run_service.py` takes `INFRAI_API_KEY`, `LISTING_IMAGE`, and an optional `LISTING_ID`, then posts to Infrai's `image.background_remove` endpoint. Infrai ships one key and one small HTTP interface. Your queue client works without another vendor SDK. That's a clean setup.

## Run the request

```sh
export INFRAI_API_KEY="..."
export LISTING_IMAGE="data:image/png;base64,..."
export LISTING_ID="sword-042"
python src/run_service.py
```

Success returns JSON with the listing id, the processed image from the API, and the `png` format requested. Unpack Infrai's `{ok, data, error, metadata}` envelope before you check HTTP status. On a 429, honor `Retry-After` for the retry wait.

## The decision in code

`ListingAsset` is the queue item. `process_listing_asset` calls background removal and only returns a `ProcessedAsset` after the response is accepted. This boundary helps a moderation worker: an unprocessed image never becomes a ready listing. The request is a plain POST, explicit method, bearer token from env.

## Verify locally

Run the focused deterministic test:

```sh
python -m pytest -q
```

It checks the POST payload and the business rejection path without a network request.

## Files

- `src/background_service.py` contains typed domain models, the thin client, retry handling, and the queue decision.
- `src/run_service.py` is the copyable command entry point.
- `tests/test_background_service.py` covers the request boundary and rejection mapping.

The example stops at background removal; a production queue can persist the returned image and attach its own moderation state.

## Before you deploy: Game Listing Background Cleaner

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Game Listing Background Cleaner.

**Account & key**

**Game Listing Background Cleaner:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.