import os
import json
import traceback
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def _read_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def _write_state(data: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _save_upload(file_field) -> str | None:
    f = request.files.get(file_field)
    if f and f.filename:
        filename = secure_filename(f.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        f.save(path)
        return f"/uploads/{filename}"
    return None


@app.route("/")
def index():
    return render_template("admin.html")


@app.route("/sync/doctor", methods=["POST"])
def sync_doctor():
    results = {}
    name = request.form.get("name", "")
    specialty = request.form.get("specialty", "")
    bio = request.form.get("bio", "")
    image_url = _save_upload("photo") or ""
    platforms = request.form.getlist("platforms")

    if "shopline" in platforms:
        try:
            from api.shopline import build_doctor_card, update_doctor_page, get_page
            existing = get_page(os.getenv("SHOPLINE_DOCTOR_PAGE_ID"))
            new_card = build_doctor_card(name, specialty, bio, image_url)
            updated_html = existing.get("body_html", "") + new_card
            update_doctor_page(updated_html)
            results["shopline"] = {"ok": True}
        except Exception as e:
            results["shopline"] = {"ok": False, "error": str(e)}

    return jsonify(results)


@app.route("/sync/hours", methods=["POST"])
def sync_hours():
    results = {}
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    hours = {}
    for day in days:
        hours[day] = {
            "open": request.form.get(f"{day}_open", "09:00"),
            "close": request.form.get(f"{day}_close", "17:00"),
            "closed": request.form.get(f"{day}_closed") == "on"
        }
    platforms = request.form.getlist("platforms")
    post_caption = request.form.get("post_caption", "").strip()
    image_url = _save_upload("hours_image")

    if "shopline" in platforms:
        try:
            from api.shopline import build_hours_html, update_info_page
            update_info_page(build_hours_html(hours))
            results["shopline"] = {"ok": True}
        except Exception as e:
            results["shopline"] = {"ok": False, "error": str(e)}

    if "google" in platforms:
        try:
            from api.google_business import update_hours, create_post, delete_post

            # 1. 更新 Google 商家營業時間
            update_hours(hours)

            # 2. 刪除上一則營業時間貼文（若存在）
            state = _read_state()
            old_post = state.get("last_hours_post_name")
            deleted = False
            if old_post:
                try:
                    delete_post(old_post)
                    deleted = True
                except Exception:
                    pass  # 舊貼文已不存在時忽略

            # 3. 建立新的最新動態貼文
            caption = post_caption or "營業時間異動公告，請查看最新時間。"
            new_post = create_post(caption, image_url)
            new_post_name = new_post.get("name", "")

            # 4. 記錄新貼文名稱供下次刪除使用
            state["last_hours_post_name"] = new_post_name
            _write_state(state)

            results["google"] = {"ok": True, "deleted_old": deleted, "new_post": new_post_name}
        except Exception as e:
            results["google"] = {"ok": False, "error": str(e)}

    if "facebook" in platforms:
        try:
            from api.meta import post_to_facebook
            caption = post_caption or "營業時間異動公告，請查看最新時間。"
            post_to_facebook(caption, image_url)
            results["facebook"] = {"ok": True}
        except Exception as e:
            results["facebook"] = {"ok": False, "error": str(e)}

    return jsonify(results)


@app.route("/sync/post", methods=["POST"])
def sync_post():
    results = {}
    message = request.form.get("message", "")
    image_url = _save_upload("image")
    platforms = request.form.getlist("platforms")

    if "google" in platforms:
        try:
            from api.google_business import create_post
            create_post(message, image_url)
            results["google"] = {"ok": True}
        except Exception as e:
            results["google"] = {"ok": False, "error": str(e)}

    if "facebook" in platforms:
        try:
            from api.meta import post_to_facebook
            post_to_facebook(message, image_url)
            results["facebook"] = {"ok": True}
        except Exception as e:
            results["facebook"] = {"ok": False, "error": str(e)}

    if "instagram" in platforms:
        if not image_url:
            results["instagram"] = {"ok": False, "error": "Instagram 需要上傳圖片"}
        else:
            try:
                from api.meta import post_to_instagram
                post_to_instagram(message, image_url)
                results["instagram"] = {"ok": True}
            except Exception as e:
                results["instagram"] = {"ok": False, "error": str(e)}

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
