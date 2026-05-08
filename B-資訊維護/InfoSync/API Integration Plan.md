# B | 資訊維護 API 串接說明

## 架構概覽

```
後台表單（admin.html）
        ↓
  app.py（Flask）
        ↓
 ┌──────┬──────────┬──────┐
 │      │          │      │
Shopline Google   Meta
 │      Business  (FB+IG)
 │      Profile
 │
醫師陣容頁 + 診所資訊頁
```

---

## 平台與 API

| 平台 | API | 認證方式 |
|------|-----|---------|
| Shopline 醫師陣容頁 | Shopline Open API v20230601 | Access Token |
| Shopline 診所資訊頁 | Shopline Open API v20230601 | Access Token |
| Google Business Profile | My Business API v4 | Service Account |
| Facebook Page | Meta Graph API v18.0 | Page Access Token |
| Instagram | Meta Graph API v18.0 | IG User Token |

---

## 可同步內容

| 內容類型 | Shopline | Google | FB | IG |
|---------|----------|--------|----|----|
| 醫師資訊 | ✓ 醫師陣容頁 | — | — | — |
| 營業時間 | ✓ 診所資訊頁 | ✓ | — | — |
| 公告/貼文 | — | ✓ LocalPost | ✓ | ✓ |
| 圖片素材 | ✓ | ✓ | ✓ | ✓ |

---

## 環境變數設定（.env）

```env
# Shopline
SHOPLINE_STORE_HANDLE=your_store_handle
SHOPLINE_ACCESS_TOKEN=your_access_token
SHOPLINE_DOCTOR_PAGE_ID=           # 醫師陣容頁 ID（從 Shopline 後台取得）
SHOPLINE_INFO_PAGE_ID=             # 診所資訊頁 ID

# Google Business Profile
GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
GOOGLE_LOCATION_NAME=accounts/ACCOUNT_ID/locations/LOCATION_ID

# Meta
META_PAGE_ID=
META_PAGE_ACCESS_TOKEN=
META_IG_USER_ID=
```

---

## 如何取得各平台憑證

### Shopline Access Token
1. Shopline 後台 → 應用程式 → 私人應用程式 → 建立應用程式
2. 勾選權限：`write_pages`、`write_content`
3. 複製 Access Token

### Shopline Page ID
```bash
curl -H "X-Shopline-Access-Token: YOUR_TOKEN" \
  https://YOUR_STORE.myshopline.com/admin/openapi/v20230601/pages.json
```
從回傳結果找到醫師陣容頁與診所資訊頁的 `id`，填入 .env

### Google Service Account
1. GCP Console → IAM → 服務帳戶 → 建立
2. 下載 JSON 金鑰
3. Google Business Profile → 設定 → 將服務帳戶 email 加為管理員

### Meta Page Access Token（長效）
1. Meta Developer → 應用程式 → Graph API Explorer
2. 選擇粉絲頁 → 取得 Page Access Token
3. 使用以下指令換成長效 token（60天）：
```
GET /oauth/access_token?grant_type=fb_exchange_token&
    client_id={app_id}&client_secret={app_secret}&
    fb_exchange_token={short_lived_token}
```

---

## 執行方式

```bash
cd InfoSync
pip install -r requirements.txt
cp .env.example .env        # 填入真實憑證
python app.py               # 開啟 http://localhost:5000
```

---

## 檔案結構

```
InfoSync/
├── app.py                  # Flask 主程式
├── config.py               # 環境變數載入
├── requirements.txt
├── .env.example
├── api/
│   ├── shopline.py         # Shopline API
│   ├── google_business.py  # Google Business Profile API
│   └── meta.py             # Facebook + Instagram API
└── templates/
    └── admin.html          # 後台表單
```
