# 本地開發指南

這份文件說明如何在本地開發和測試 Telegram 機器人。

## 快速開始

1. **建立虛擬環境**（避免套件衝突）：

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS/Linux
   ```

2. **安裝依賴**：

   ```bash
   pip install -r requirements.txt
   ```

3. **設定 Token**：

   ```bash
   cp .env.example .env
   # 編輯 .env，填入你的 TELEGRAM_BOT_TOKEN
   ```

4. **啟動機器人**：

   ```bash
   python main.py
   ```

   看到「機器人啟動中...」表示成功啟動。

5. **測試**：
   - 在 Telegram 搜尋你的機器人（username）
   - 傳送 `/start` 測試
   - 傳送任意文字測試自動回覆

6. **停止機器人**：
   - 按 `Ctrl+C` 優雅關閉

## 開發流程

### 修改回覆邏輯

編輯 `bot.py`：

- **修改預設回覆**：改 `DEFAULT_REPLY` 變數
- **新增關鍵字回覆**：在 `KEYWORD_REPLIES` 字典新增項目
- **修改指令**：編輯 `start()` 或 `help_command()` 函數

修改後：
1. 停止機器人（`Ctrl+C`）
2. 重新執行 `python main.py`
3. 在 Telegram 測試新功能

### 查看日誌

機器人執行時會在終端顯示日誌，包含：
- 收到的訊息
- 回覆內容
- 錯誤訊息（如有）

範例輸出：
```
2026-01-30 10:30:15 - bot - INFO - 機器人啟動中...
2026-01-30 10:30:20 - bot - INFO - 回覆使用者 123456789: 你好！有什麼可以幫您的嗎？
```

## 本地接上 Gemini API（AI 回覆）

專案已支援 **Gemini**，只要在本機設定 API Key，機器人就會用 Gemini 回覆（未設定或錯誤時會退回關鍵字回覆）。

### 1. 取得 Gemini API Key（免費）

1. 打開 **[Google AI Studio](https://aistudio.google.com/app/apikey)**（用 Google 帳號登入）
2. 點「**Create API key**」或「建立 API 金鑰」
3. 選一個 GCP 專案（或建立新專案），完成後會得到一組 **API 金鑰**（一串字元）
4. 複製這組金鑰，待會貼到 `.env`

### 2. 安裝 Gemini 套件（若尚未安裝）

在專案目錄、有啟動 venv 的終端執行：

```bash
pip install google-genai
```

或一次裝齊專案依賴：

```bash
pip install -r requirements.txt
```

### 3. 在 .env 裡設定 GEMINI_API_KEY

1. 開啟專案目錄下的 **`.env`**（沒有就從 `.env.example` 複製一份再改）
2. 新增一行（換成你剛複製的金鑰）：

   ```
   GEMINI_API_KEY=你的Gemini_API_金鑰
   ```

3. 存檔

### 4. 啟動機器人測試

```bash
python main.py
```

在 Telegram 傳任意文字給機器人，若設定正確，會收到 **Gemini 產生的回覆**；若 Key 錯誤或未裝套件，會自動改用關鍵字回覆。

### 可選：指定模型

預設使用 `gemini-2.0-flash`。若想換模型，在 `.env` 加一行：

```
GEMINI_MODEL=gemini-2.0-flash
```

可改成其他 [Gemini 模型名稱](https://ai.google.dev/gemini-api/docs/models)（例如 `gemini-1.5-flash`）。

### 常見問題

**Q: 還是關鍵字回覆，沒有 AI？**  
- 確認 `.env` 有 `GEMINI_API_KEY=...` 且沒有多餘空格、引號  
- 確認有執行 `pip install google-genai`，且用**同一個** Python 跑 `main.py`  
- 看終端日誌是否有 `Gemini API 錯誤`，依錯誤訊息排查  

**Q: 免費額度夠嗎？**  
- Google 提供免費額度（每分鐘請求數、每日請求數有限），個人小機器人通常夠用；詳見 [Gemini API 定價與配額](https://ai.google.dev/pricing)。

---

### 常見問題

**Q: 機器人沒有回應？**
- 確認 Token 正確（檢查 `.env`）
- 確認機器人已啟動（看到「機器人啟動中...」）
- 確認你在 Telegram 有傳送訊息給正確的機器人

**Q: 修改程式碼後沒生效？**
- 必須**重新啟動**機器人（停止後再執行）
- polling 模式不會自動重新載入程式碼

**Q: 如何測試不同的回覆？**
- 直接修改 `bot.py` 中的 `KEYWORD_REPLIES` 或 `DEFAULT_REPLY`
- 重啟機器人測試

## 下一步

熟悉本地開發後，可以：
- 添加更多指令（如 `/about`、`/status`）
- 處理圖片、檔案等其他類型的訊息
- 整合資料庫儲存對話記錄
- 準備部署到雲端伺服器
