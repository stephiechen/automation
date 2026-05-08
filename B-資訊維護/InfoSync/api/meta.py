import requests
from config import META_GRAPH_URL, META_PAGE_ID, META_PAGE_ACCESS_TOKEN, META_IG_USER_ID


def post_to_facebook(message: str, image_url: str = None) -> dict:
    """發文到 Facebook 粉絲頁"""
    if image_url:
        url = f"{META_GRAPH_URL}/{META_PAGE_ID}/photos"
        payload = {"caption": message, "url": image_url, "access_token": META_PAGE_ACCESS_TOKEN}
    else:
        url = f"{META_GRAPH_URL}/{META_PAGE_ID}/feed"
        payload = {"message": message, "access_token": META_PAGE_ACCESS_TOKEN}

    resp = requests.post(url, data=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def post_to_instagram(caption: str, image_url: str) -> dict:
    """發文到 Instagram（需要圖片）"""
    # Step 1: 建立媒體容器
    container_url = f"{META_GRAPH_URL}/{META_IG_USER_ID}/media"
    container_resp = requests.post(container_url, data={
        "image_url": image_url,
        "caption": caption,
        "access_token": META_PAGE_ACCESS_TOKEN
    }, timeout=20)
    container_resp.raise_for_status()
    creation_id = container_resp.json().get("id")

    # Step 2: 發布
    publish_url = f"{META_GRAPH_URL}/{META_IG_USER_ID}/media_publish"
    publish_resp = requests.post(publish_url, data={
        "creation_id": creation_id,
        "access_token": META_PAGE_ACCESS_TOKEN
    }, timeout=20)
    publish_resp.raise_for_status()
    return publish_resp.json()
