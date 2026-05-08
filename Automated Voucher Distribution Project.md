# 健檢券 & 疫苗券派送自動化計畫

## Context
Karen 交接工作中，每月的疫苗券與健檢券派送目前為手動流程：資訊部提供 CSV/Excel 名單 → 手動篩選 → 手動匯入 Maac（LINE CRM）→ 手動貼標籤觸發旅程。
目標：用 Python 腳本將整個 pipeline 自動化，減少人工作業。

---

## 業務規則

### 篩選條件
| 條件 | 規則 |
|------|------|
| 名單來源 | 資訊部已預篩符合資格者，腳本**不需**再做消費金額過濾 |
| LINE ID 為空 | **排除**（無法發送，發送邏輯以 LINE ID 為唯一依據）|
| 手機號 | 不做任何篩選；由資訊部撈名單時同步提供，腳本原樣帶入 sent log，供事後 mapping 病歷系統追蹤成效用 |
| 健檢狀態欄位 = N | 納入（未健檢者）|
| 健檢狀態欄位 = Y | 排除 |
| 去重規則 | 以 LINE ID 為主鍵去重（保留一筆）|
| 疊加規則 | 健檢券＋疫苗券**可並發**（部分客戶為拆單，兩者門檻皆符合），不需去重 |
| 到期提醒篩選 | 疫苗券、健檢券僅篩**最近一個月內到期**者（用於提醒旅程）|

### 通知排程（由 Maac 旅程處理）
- 疫苗券（1年效期）：第1個月 + 第12個月各通知1次
- 健檢券（90天效期）：第1天 + 第~60天各通知1次

### 發送時間限制
- 僅工作日 09:00–17:00（需有客服在線）

---

## 檔案結構
```
voucher-automation/
├── main.py           # 進入點，執行完整 pipeline
├── filter_list.py    # 讀取 CSV/Excel、套用業務規則、輸出篩選結果
├── maac_client.py    # Maac API 封裝（匯入聯絡人、貼標籤）
├── config.py         # 設定（API 金鑰、欄位名稱、金額門檻、標籤名稱）
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
COL_SPEND         = "total_spend"
COL_HEALTH_STATUS = "health_check"  # Y/N

# Maac 標籤名稱
TAG_VACCINE = "疫苗券_已發放"
TAG_HEALTH  = "健檢券_已發放"
```

### filter_list.py
- `load_data(filepath)` → 支援 .csv / .xlsx 自動判斷
- `filter_eligible(df)` → 排除 LINE ID 空值、health_check == 'Y'（手機號不做任何篩選）
- `deduplicate(df)` → 以 LINE ID 去重，保留一筆
- `filter_expiring_soon(df, days=30)` → 只留最近 N 天內到期的券（用於提醒）
- `export_filtered(df, output_path)` → 輸出篩選後 CSV（含 LINE ID + 手機號）
- `export_skipped(df, output_path)` → 輸出被排除名單（含排除原因，供事後核對）
- 注意：名單已預篩金額資格，不需做消費門檻判斷；健檢券與疫苗券可並發

### maac_client.py
- 封裝 Maac API（參考：https://developers.maac.io）
- `bulk_import_contacts(contacts: list[dict])` → 批次匯入聯絡人
- `apply_tag(line_uid: str, tag: str)` → 貼標籤以觸發旅程
- `check_import_status(batch_id)` → 確認匯入結果

### main.py（CLI）
```
python main.py --vaccine /path/to/vaccine_list.csv --health /path/to/health_list.csv [--dry-run]
```
執行步驟：
1. 分別載入疫苗券名單、健檢券名單（各一份 CSV/Excel）
2. 各自套用篩選邏輯（health_check == 'N'、到期日過濾）
3. 印出統計（疫苗券 N 筆、健檢券 N 筆、排除 N 筆）
4. `--dry-run` 模式：只輸出篩選結果 CSV，不呼叫 API
5. 正式執行：批次匯入 Maac + 貼對應標籤
6. 輸出執行報告（成功/失敗筆數）

---

## 待確認事項（實作前需補充）
- [ ] 實際 CSV 的欄位名稱（健檢狀態、消費金額、LINE UID 欄位名稱）
- [ ] Maac API Token 取得方式（從 Maac 後台 > 設定 > API）
- [x] 需要排程自動執行（cron/launchd）—— 每月固定某日執行（日期 TBD），執行時間 TBD，遇國定假日自動順延至下一個工作日
- [x] Maac 旅程已預先設定好，腳本只需貼對應標籤觸發即可（標籤名稱待確認）

---

## 驗證方式
1. 用 dry-run 模式跑測試 CSV，確認篩選邏輯正確
2. 用少量測試聯絡人確認 Maac API 匯入成功
3. 在 Maac 後台確認標籤有正確貼上
4. 確認對應旅程有被觸發
