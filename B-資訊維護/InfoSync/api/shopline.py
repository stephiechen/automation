import requests
from config import SHOPLINE_BASE_URL, SHOPLINE_ACCESS_TOKEN, SHOPLINE_DOCTOR_PAGE_ID, SHOPLINE_INFO_PAGE_ID


def _headers():
    return {"X-Shopline-Access-Token": SHOPLINE_ACCESS_TOKEN, "Content-Type": "application/json"}


def update_doctor_page(html_content: str) -> dict:
    """更新醫師陣容頁 body_html"""
    url = f"{SHOPLINE_BASE_URL}/pages/{SHOPLINE_DOCTOR_PAGE_ID}.json"
    payload = {"page": {"body_html": html_content}}
    resp = requests.put(url, json=payload, headers=_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def update_info_page(html_content: str) -> dict:
    """更新診所資訊頁 body_html（含營業時間）"""
    url = f"{SHOPLINE_BASE_URL}/pages/{SHOPLINE_INFO_PAGE_ID}.json"
    payload = {"page": {"body_html": html_content}}
    resp = requests.put(url, json=payload, headers=_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_page(page_id: str) -> dict:
    """取得指定頁面的現有內容"""
    url = f"{SHOPLINE_BASE_URL}/pages/{page_id}.json"
    resp = requests.get(url, headers=_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json().get("page", {})


def build_doctor_card(name: str, specialty: str, bio: str, image_url: str) -> str:
    """產生醫師卡片 HTML 片段"""
    return f"""
<div class="doctor-card">
  <img src="{image_url}" alt="{name}" />
  <h3>{name}</h3>
  <p class="specialty">{specialty}</p>
  <p class="bio">{bio}</p>
</div>
"""


def build_hours_html(hours: dict) -> str:
    """
    hours 格式: {"monday": {"open": "09:00", "close": "17:00", "closed": False}, ...}
    產生營業時間 HTML 片段
    """
    day_names = {
        "monday": "週一", "tuesday": "週二", "wednesday": "週三",
        "thursday": "週四", "friday": "週五", "saturday": "週六", "sunday": "週日"
    }
    rows = ""
    for day_key, label in day_names.items():
        info = hours.get(day_key, {})
        if info.get("closed"):
            rows += f"<tr><td>{label}</td><td>休診</td></tr>"
        else:
            rows += f"<tr><td>{label}</td><td>{info.get('open', '')} – {info.get('close', '')}</td></tr>"
    return f"<table class='hours-table'>{rows}</table>"
