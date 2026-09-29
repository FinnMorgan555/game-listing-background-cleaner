import json

from src.background_service import InfraiError, InfraiImageClient, ListingAsset, process_listing_asset


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def read(self):
        return self.payload


def test_listing_asset_is_published_only_with_processed_image():
    seen = {}

    def opener(request):
        seen["method"] = request.get_method()
        seen["body"] = json.loads(request.data.decode())
        return FakeResponse({"ok": True, "data": {"image": "https://cdn/game.png"}, "error": None, "metadata": {}})

    asset = ListingAsset("listing-42", "data:image/png;base64,raw")
    result = process_listing_asset(asset, InfraiImageClient(api_key="test", opener=opener))

    assert result.listing_id == "listing-42"
    assert result.image == "https://cdn/game.png"
    assert seen == {"method": "POST", "body": {"image": {"base64": "raw"}, "format": "png"}}


def test_business_rejection_is_exposed_after_envelope_decode():
    def opener(request):
        return FakeResponse({"ok": False, "data": None, "error": {"code": "INVALID_ARGUMENT"}, "metadata": {}})

    try:
        InfraiImageClient(api_key="test", opener=opener).background_remove("x", "png")
    except InfraiError as exc:
        assert exc.code == "INVALID_ARGUMENT"
    else:
        raise AssertionError("expected InfraiError")
