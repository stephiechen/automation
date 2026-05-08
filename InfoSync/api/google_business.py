import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import GOOGLE_SERVICE_ACCOUNT_JSON, GOOGLE_LOCATION_NAME

SCOPES = ["https://www.googleapis.com/auth/business.manage"]


def _credentials():
    return service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_JSON, scopes=SCOPES
    )


def update_hours(hours: dict) -> dict:
    """
    hours 格式: {"monday": {"open": "09:00", "close": "17:00", "closed": False}, ...}
    更新 Google Business Profile 營業時間
    """
    day_map = {
        "monday": "MONDAY", "tuesday": "TUESDAY", "wednesday": "WEDNESDAY",
        "thursday": "THURSDAY", "friday": "FRIDAY", "saturday": "SATURDAY", "sunday": "SUNDAY"
    }

    periods = []
    for day_key, gmb_day in day_map.items():
        info = hours.get(day_key, {})
        if not info.get("closed"):
            open_h, open_m = info.get("open", "09:00").split(":")
            close_h, close_m = info.get("close", "17:00").split(":")
            periods.append({
                "openDay": gmb_day, "closeDay": gmb_day,
                "openTime": {"hours": int(open_h), "minutes": int(open_m)},
                "closeTime": {"hours": int(close_h), "minutes": int(close_m)}
            })

    service = build("mybusinessbusinessinformation", "v1", credentials=_credentials())
    body = {"regularHours": {"periods": periods}}
    result = service.locations().patch(
        name=GOOGLE_LOCATION_NAME,
        updateMask="regularHours",
        body=body
    ).execute()
    return result


def create_post(summary: str, image_url: str = None) -> dict:
    """建立 Google Business Profile 貼文（LocalPost），回傳含 name 欄位"""
    service = build("mybusiness", "v4", credentials=_credentials())
    body = {
        "languageCode": "zh-TW",
        "summary": summary,
        "topicType": "STANDARD"
    }
    if image_url:
        body["media"] = [{"mediaFormat": "PHOTO", "sourceUrl": image_url}]

    result = service.accounts().locations().localPosts().create(
        parent=GOOGLE_LOCATION_NAME,
        body=body
    ).execute()
    return result


def delete_post(post_name: str) -> None:
    """刪除指定 LocalPost（post_name 格式：accounts/.../localPosts/xxx）"""
    service = build("mybusiness", "v4", credentials=_credentials())
    service.accounts().locations().localPosts().delete(name=post_name).execute()
