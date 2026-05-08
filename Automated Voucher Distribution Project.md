# 健檢券 & 疫苗券到期提醒自動化計畫

## Context
Karen 交接工作中，每月的疫苗券與健檢券**到期提醒**目前為手動流程：資訊部提供 CSV/Excel 名單 → 手動篩選 → 手動匯入 Maac（LINE CRM）→ 手動貼標籤觸發旅程。
目標：用 Python 腳本將整個 pipeline 自動化，減少人工作業。

> **範圍說明**：本腳本僅處理「券到期前一個月提醒」流程。首次派發不在此任務內。

> 健檢券流程與疫苗券流程**完全獨立**，分開執行、貼不同標籤、觸發不同旅程。

---

## 業務規則

### 共用篩選邏輯
| 條件 | 規則 |
|------|------|
| 名單來源 | 資訊部已預篩符合資格者，腳本**不需**再做消費金額過濾 |
| LINE ID 為空 | **排除**（發送邏輯以 LINE ID 為唯一依據）|
| 手機號 | 不做任何篩選；由資訊部撈名單時同步提供，腳本原樣帶入 sent log，供事後 mapping 病歷系統追蹤成效用 |
| 去重規則 | 以 LINE ID 為主鍵去重（保留一筆）|
| 到期提醒篩選 | 僅篩**最近一個月內到期**者（用於提醒旅程）|

### 疫苗券流程（到期提醒）
- 輸入：資訊部提供疫苗券到期名單（CSV/Excel），內含到期日欄位
- 效期不固定（部分1年、部分3年），一律以名單上的到期日欄位為準
- 篩選：排除 LINE ID 空值、以到期日往前推一個月篩出即將到期者、去重
- Maac 標籤：`TAG_VACCINE_EXPIRY`（待確認）
- 觸發 Maac 旅程：到期前一個月提醒

### 健檢券流程（到期提醒）
- 輸入：資訊部提供健檢券到期名單（CSV/Excel），內含到期日欄位
- 篩選：排除 LINE ID 空值、篩出最近一個月內到期、去重
- Maac 標籤：`TAG_HEALTH_EXPIRY`（待確認）
- 觸發 Maac 旅程：到期前提醒（對應第~60天通知）

### 疊加說明
部分客戶因拆單同時符合兩者資格，會同時出現在兩份名單中 → 兩個流程各自獨立執行即可，無需去重或互斥。

### 發送時間限制
- 僅工作日 09:00–17:00（需有客服在線）

---

## 檔案結構
```
voucher-automation/
├── run_vaccine.py    # 疫苗券執行進入點
├── run_health.py     # 健檢券執行進入點
├── filter_list.py    # 讀取 CSV/Excel、套用篩選邏輯、輸出結果
├── maac_client.py    # Maac API 封裝（匯入聯絡人、貼標籤）
├── config.py         # 設定（API 金鑰、欄位名稱、標籤名稱）
├── requirements.txt  # pandas, openpyxl, requests, python-dotenv
└── .env              # 存放 Maac API Token（不進 git）
```

---

## 各模組設計

### config.py
```python
EXPIRY_FILTER_DAYS = 30  # 只提醒最近 N 天內到期的券

# 欄位名稱（依實際 CSV header 調整）
COL_LINE_UID      = "line_uid"
COL_PHONE         = "phone"
COL_HEALTH_STATUS = "health_check"  # Y/N（健檢券名單專用）

# Maac 標籤名稱（待確認）
TAG_VACCINE = "疫苗券_已發放"
TAG_HEALTH  = "健檢券_已發放"
```

### filter_list.py
- `load_data(filepath)` → 支援 .csv / .xlsx 自動判斷
- `filter_eligible(df, check_health_status=False)` → 排除 LINE ID 空值；健檢券流程額外排除 health_check == 'Y'
- `deduplicate(df)` → 以 LINE ID 去重，保留一筆
- `filter_expiring_soon(df, days=30)` → 只留最近 N 天內到期的券（用於提醒）
- `export_filtered(df, output_path)` → 輸出篩選後 CSV（含 LINE ID + 手機號）
- `export_skipped(df, output_path)` → 輸出被排除名單（含排除原因）

### maac_client.py
- 封裝 Maac API（參考：https://developers.maac.io）
- `bulk_import_contacts(contacts: list[dict])` → 批次匯入聯絡人
- `apply_tag(line_uid: str, tag: str)` → 貼標籤以觸發旅程
- `check_import_status(batch_id)` → 確認匯入結果

### CLI（兩個獨立指令）
```
# 疫苗券
python run_vaccine.py --input /path/to/vaccine_list.csv [--dry-run]

# 健檢券
python run_health.py --input /path/to/health_list.csv [--dry-run]
```

執行步驟（各自獨立）：
1. 載入名單
2. 套用篩選邏輯
3. 印出統計（有效 N 筆、排除 N 筆）
4. `--dry-run`：只輸出篩選結果 CSV，不呼叫 API
5. 正式執行：批次匯入 Maac + 貼對應標籤
6. 輸出執行報告（成功/失敗筆數）

---

## 待確認事項（實作前需補充）
- [ ] 實際 CSV 的欄位名稱（LINE UID、手機號、健檢狀態欄位名稱）
- [ ] Maac API Token 取得方式（從 Maac 後台 > 設定 > API）
- [ ] 疫苗券、健檢券各自的 Maac 標籤名稱
- [x] Maac 旅程已預先設定好，腳本只需貼對應標籤觸發即可
- [x] 需要排程自動執行（cron/launchd）—— 每月固定某日執行（日期 TBD），執行時間 TBD，遇國定假日自動順延至下一個工作日

---

## 驗證方式
1. 用 dry-run 模式跑測試 CSV，確認篩選邏輯正確
2. 用少量測試聯絡人確認 Maac API 匯入成功
3. 在 Maac 後台確認標籤有正確貼上
4. 確認對應旅程有被觸發
