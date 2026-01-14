import json
from datetime import datetime

from src.config import AI_DEBUG_MODE
from src.utils import safe_get


async def _parse_search_results_json(json_data: dict, source: str) -> list:
    """Analytical searchAPIofJSONData, returns the basic product information list。"""
    page_data = []
    try:
        items = await safe_get(json_data, "data", "resultList", default=[])
        if not items:
            print(f"LOG: ({source}) APIProduct list not found in response (resultList)。")
            if AI_DEBUG_MODE:
                print(f"--- [SEARCH DEBUG] RAW JSON RESPONSE from {source} ---")
                print(json.dumps(json_data, ensure_ascii=False, indent=2))
                print("----------------------------------------------------")
            return []

        for item in items:
            main_data = await safe_get(item, "data", "item", "main", "exContent", default={})
            click_params = await safe_get(item, "data", "item", "main", "clickParam", "args", default={})

            title = await safe_get(main_data, "title", default="Unknown title")
            price_parts = await safe_get(main_data, "price", default=[])
            price = "".join([str(p.get("text", "")) for p in price_parts if isinstance(p, dict)]).replace("current price", "").strip() if isinstance(price_parts, list) else "Price anomaly"
            if "Ten thousand" in price: price = f"¥{float(price.replace('¥', '').replace('Ten thousand', '')) * 10000:.0f}"
            area = await safe_get(main_data, "area", default="Region unknown")
            seller = await safe_get(main_data, "userNickName", default="anonymous seller")
            raw_link = await safe_get(item, "data", "item", "main", "targetUrl", default="")
            image_url = await safe_get(main_data, "picUrl", default="")
            pub_time_ts = click_params.get("publishTime", "")
            item_id = await safe_get(main_data, "itemId", default="unknownID")
            original_price = await safe_get(main_data, "oriPrice", default="None yet")
            wants_count = await safe_get(click_params, "wantNum", default='NaN')


            tags = []
            if await safe_get(click_params, "tag") == "freeship":
                tags.append("Free shipping")
            r1_tags = await safe_get(main_data, "fishTags", "r1", "tagList", default=[])
            for tag_item in r1_tags:
                content = await safe_get(tag_item, "data", "content", default="")
                if "Inspection treasure" in content:
                    tags.append("Inspection treasure")

            page_data.append({
                "Product title": title,
                "Current selling price": price,
                "Product original price": original_price,
                "“"Want" number of people": wants_count,
                "Product tag": tags,
                "Shipping area": area,
                "Seller nickname": seller,
                "Product link": raw_link.replace("fleamarket://", "https://www.goofish.com/"),
                "Release time": datetime.fromtimestamp(int(pub_time_ts)/1000).strftime("%Y-%m-%d %H:%M") if pub_time_ts.isdigit() else "unknown time",
                "commodityID": item_id
            })
        print(f"LOG: ({source}) Successfully parsed to {len(page_data)} Basic product information。")
        return page_data
    except Exception as e:
        print(f"LOG: ({source}) JSONData processing exception: {str(e)}")
        return []


async def calculate_reputation_from_ratings(ratings_json: list) -> dict:
    """from original reviewAPIIn the data list, calculate the number of positive reviews and positive review rates for sellers and buyers。"""
    seller_total = 0
    seller_positive = 0
    buyer_total = 0
    buyer_positive = 0

    for card in ratings_json:
        # use safe_get Ensure secure access
        data = await safe_get(card, 'cardData', default={})
        role_tag = await safe_get(data, 'rateTagList', 0, 'text', default='')
        rate_type = await safe_get(data, 'rate') # 1=Good reviews, 0=Neutral rating, -1=Bad review

        if "seller" in role_tag:
            seller_total += 1
            if rate_type == 1:
                seller_positive += 1
        elif "buyer" in role_tag:
            buyer_total += 1
            if rate_type == 1:
                buyer_positive += 1

    # Calculate ratios and handle division by zero
    seller_rate = f"{(seller_positive / seller_total * 100):.2f}%" if seller_total > 0 else "N/A"
    buyer_rate = f"{(buyer_positive / buyer_total * 100):.2f}%" if buyer_total > 0 else "N/A"

    return {
        "Number of positive reviews as a seller": f"{seller_positive}/{seller_total}",
        "Positive rating as a seller": seller_rate,
        "Number of positive reviews as a buyer": f"{buyer_positive}/{buyer_total}",
        "Positive rating as a buyer": buyer_rate
    }


async def _parse_user_items_data(items_json: list) -> list:
    """Parse the product list on the user's homepageAPIofJSONdata。"""
    parsed_list = []
    for card in items_json:
        data = card.get('cardData', {})
        status_code = data.get('itemStatus')
        if status_code == 0:
            status_text = "On sale"
        elif status_code == 1:
            status_text = "sold"
        else:
            status_text = f"unknown status ({status_code})"

        parsed_list.append({
            "commodityID": data.get('id'),
            "Product title": data.get('title'),
            "Product price": data.get('priceInfo', {}).get('price'),
            "Product main image": data.get('picInfo', {}).get('picUrl'),
            "Product status": status_text
        })
    return parsed_list


async def parse_user_head_data(head_json: dict) -> dict:
    """Parse user headerAPIofJSONdata。"""
    data = head_json.get('data', {})
    ylz_tags = await safe_get(data, 'module', 'base', 'ylzTags', default=[])
    seller_credit, buyer_credit = {}, {}
    for tag in ylz_tags:
        if await safe_get(tag, 'attributes', 'role') == 'seller':
            seller_credit = {'level': await safe_get(tag, 'attributes', 'level'), 'text': tag.get('text')}
        elif await safe_get(tag, 'attributes', 'role') == 'buyer':
            buyer_credit = {'level': await safe_get(tag, 'attributes', 'level'), 'text': tag.get('text')}
    return {
        "Seller nickname": await safe_get(data, 'module', 'base', 'displayName'),
        "Seller avatar link": await safe_get(data, 'module', 'base', 'avatar', 'avatar'),
        "Seller's personalized signature": await safe_get(data, 'module', 'base', 'introduction', default=''),
        "Seller is selling/Number of items sold": await safe_get(data, 'module', 'tabs', 'item', 'number'),
        "The total number of reviews the seller has received": await safe_get(data, 'module', 'tabs', 'rate', 'number'),
        "Seller credit rating": seller_credit.get('text', 'None yet'),
        "Buyer credit rating": buyer_credit.get('text', 'None yet')
    }


async def parse_ratings_data(ratings_json: list) -> list:
    """Parse the review listAPIofJSONdata。"""
    parsed_list = []
    for card in ratings_json:
        data = await safe_get(card, 'cardData', default={})
        rate_tag = await safe_get(data, 'rateTagList', 0, 'text', default='unknown role')
        rate_type = await safe_get(data, 'rate')
        if rate_type == 1: rate_text = "Good reviews"
        elif rate_type == 0: rate_text = "Neutral rating"
        elif rate_type == -1: rate_text = "Bad review"
        else: rate_text = "unknown"
        parsed_list.append({
            "evaluateID": data.get('rateId'),
            "Review content": data.get('feedback'),
            "Review type": rate_text,
            "Review source role": rate_tag,
            "Reviewer Nickname": data.get('raterUserNick'),
            "Evaluation time": data.get('gmtCreate'),
            "Review pictures": await safe_get(data, 'pictCdnUrlList', default=[])
        })
    return parsed_list
