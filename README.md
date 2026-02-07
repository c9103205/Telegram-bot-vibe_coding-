# Telegram 自動回覆機器人

接入 Telegram Bot API 的自動回覆專案，收到訊息會自動回覆，並可依關鍵字自訂回覆內容。

## 環境需求

- Python 3.9+

## 取得 Bot Token

1. 在 Telegram 搜尋 **@BotFather**
2. 傳送 `/newbot`，依指示設定機器人名稱與 username
3. 完成後 BotFather 會給你一組 **Token**（格式如 `123456789:ABCdef...`）
4. 請妥善保管，勿提交到 Git

## 安裝與執行

1. 建立虛擬環境（建議）：

   ```bash
   python -m venv venv
   source venv/bin/activate   # macOS/Linux
   # Windows: venv\Scripts\activate
   ```

2. 安裝依賴：

   ```bash
   pip install -r requirements.txt
   ```

3. 設定 Token 與 AI API Key：

   ```bash
   cp .env.example .env
   ```

   在 Cursor 中開啟 `.env` 並編輯（`Cmd+P` 或 `Ctrl+P` 輸入 `.env`），
   至少填入 `TELEGRAM_BOT_TOKEN=`，若要使用 AI 功能，也需填入 `GEMINI_API_KEY=` 或 `OPENAI_API_KEY=`。
   圖片生成功能可選填 `GEMINI_IMAGE_MODEL=` 和 `AI_IMAGE_PROVIDER=`。

4. 啟動機器人：

   ```bash
   python main.py
   ```

   看到「機器人啟動中...」後，在 Telegram 搜尋你的機器人，傳送訊息即可測試自動回覆。

## 無法連接 Telegram？

執行診斷腳本找出原因：

```bash
python check_telegram.py
```

會依序檢查：套件是否安裝、Token 是否設定、能否連到 Telegram API。  
詳細原因分析與排除步驟見 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**。

## 自訂回覆

- **預設回覆**：在 `logic.py` 修改 `DEFAULT_REPLY`
- **關鍵字回覆**：在 `logic.py` 的 `KEYWORD_REPLIES` 字典新增「關鍵字 → 回覆內容」

## 專案結構

```
.
├── ai_image_gen.py     # 圖片生成邏輯（Gemini / DALL-E）
├── ai_reply_image.py   # 圖片分析邏輯（Gemini Vision / OpenAI Vision）
├── check_telegram.py   # 診斷「無法連接 Telegram」的腳本
├── debug_gemini.py     # 診斷「Gemini API 失效」的腳本
├── DEVELOPMENT.md     # 本地開發指南
├── DEPLOYMENT.md       # 部署到一般主機指南
├── DEPLOYMENT_GOOGLE_CLOUD.md # 部署到 Google Cloud 指南
├── logic.py            # 純邏輯（關鍵字對應、預設回覆）
├── main.py             # 程式進入點（啟動 bot 或本地模擬）
├── README.md
├── requirements.txt    # 依賴套件
└── TROUBLESHOOTING.md  # 故障排除指南
```

## 指令

- `/start`：開始或查看當前配置
- `/reset`：重新選擇女友和姓名
- `/imagine <文字>`：生成圖片（由 Gemini 或 DALL-E 提供）
- `/help`：顯示此訊息
- 傳送任意訊息：用 AI（Gemini）回覆

## 本地開發 vs 部署

### 本地開發（目前）

- **執行方式**：在你的電腦上執行 `python main.py`
- **連線方式**：使用 **polling**（機器人主動向 Telegram 伺服器詢問新訊息）
- **優點**：簡單、適合學習、修改程式碼後重啟即可測試
- **限制**：你的電腦必須開機且程式在運行，機器人才能回應

### 未來部署（雲端伺服器）

**如何把開發好的檔案部署上去？**  
- 一般主機（SCP / Git / systemd）：**[DEPLOYMENT.md](DEPLOYMENT.md)**  
- **Google Cloud（Compute Engine VM）**：**[DEPLOYMENT_GOOGLE_CLOUD.md](DEPLOYMENT_GOOGLE_CLOUD.md)**

當你準備好部署時，有幾個選項：

1. **雲端主機**（如 AWS EC2、DigitalOcean、Linode）
   - 在遠端伺服器上執行 `python main.py`
   - 使用 `screen` 或 `systemd` 讓程式在背景持續運行
   - 優點：完全控制、成本較低

2. **容器化部署**（Docker）
   - 建立 `Dockerfile`，打包整個環境
   - 部署到任何支援 Docker 的平台（如 Railway、Render、Fly.io）
   - 優點：環境一致、易於擴展

3. **Serverless / Webhook**
   - 改用 **webhook** 模式（Telegram 主動推送訊息到你的伺服器）
   - 部署到 AWS Lambda、Google Cloud Functions 等
   - 優點：按使用量計費、自動擴展

**目前建議**：先在本地學習和測試，熟悉機器人運作後，再考慮部署方式。需要部署時可以參考上述選項或詢問協助。
