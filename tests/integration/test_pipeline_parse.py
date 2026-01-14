import asyncio

from src.parsers import (
    _parse_search_results_json,
    _parse_user_items_data,
    calculate_reputation_from_ratings,
    parse_ratings_data,
    parse_user_head_data,
)


def test_parse_search_results(load_json_fixture):
    raw = load_json_fixture("search_results.json")
    items = asyncio.run(_parse_search_results_json(raw, source="search"))
    assert len(items) == 1
    item = items[0]
    assert item["Product title"] == "Sony A7M4 Body"
    assert item["Current selling price"].startswith("¥")
    assert "Free shipping" in item["Product tag"]
    assert "Inspection treasure" in item["Product tag"]
    assert item["Product link"].startswith("https://www.goofish.com/")


def test_parse_user_head_and_items(load_json_fixture):
    head_json = load_json_fixture("user_head.json")
    items_json = load_json_fixture("user_items.json")

    head = asyncio.run(parse_user_head_data(head_json))
    assert head["Seller nickname"] == "seller_01"
    assert head["The total number of reviews the seller has received"] == 88

    items = asyncio.run(_parse_user_items_data(items_json))
    assert items[0]["Product status"] == "On sale"
    assert items[1]["Product status"] == "sold"


def test_parse_ratings_and_reputation(load_json_fixture):
    ratings_json = load_json_fixture("ratings.json")
    ratings = asyncio.run(parse_ratings_data(ratings_json))
    assert ratings[0]["Review type"] == "Good reviews"

    reputation = asyncio.run(calculate_reputation_from_ratings(ratings_json))
    assert reputation["Number of positive reviews as a seller"].startswith("1/")
    assert reputation["Number of positive reviews as a buyer"].startswith("1/")
