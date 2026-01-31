# 無法連接 Telegram：原因分析與排除

## 先跑診斷腳本

在專案目錄執行：

```bash
python check_telegram.py
```

腳本會依序檢查：**套件是否安裝**、**Token 是否設定**、**能否連到 Telegram API**，並在失敗時提示可能原因。

---

## 常見原因對照表

| 現象 | 可能原因 | 怎麼檢查 / 怎麼做 |
|------|----------|--------------------|
| 執行 `main.py` 直接進入「本地模擬模式」、沒有連到 Telegram | **未安裝 `python-telegram-bot`** | 終端執行 `python check_telegram.py`，第一步就會寫「未安裝」。<br>→ 在**同一個環境**執行：`pip install python-telegram-bot`<br>若出現 **SSL 錯誤**，多半是網路/憑證問題，見下方「SSL 錯誤」一節。 |
| 有裝套件，但執行時仍說「無法使用 Telegram」 | **用的 Python 和裝套件的不是同一個** | 確認：<br>1. 有虛擬環境就先 `source venv/bin/activate`<br>2. 用 `which python` 和 `pip show python-telegram-bot` 看路徑是否一致<br>3. 用「同一個終端、同一個 python」執行：`python check_telegram.py` 和 `python main.py` |
| 診斷腳本第 2 步失敗：未設定 Token | **沒有 .env 或變數名寫錯** | 在專案目錄要有 `.env`，內容一行：<br>`TELEGRAM_BOT_TOKEN=你的Token`<br>變數名必須是 `TELEGRAM_BOT_TOKEN`，不要有空格、引號。 |
| 診斷腳本第 3 步失敗：401 / Unauthorized | **Token 錯誤或過期** | 到 Telegram 找 **@BotFather**，傳送 `/mybots` → 選你的 bot → **API Token**，複製新 Token 到 `.env` 覆蓋舊的。 |
| 診斷腳本第 3 步失敗：連線逾時 / Connection 錯誤 | **本機網路連不到 Telegram** | 可能：<br>• 公司/學校防火牆擋住 `api.telegram.org`<br>• 地區限制（例如需透過代理）<br>→ 換網路（如手機熱點）或設定 HTTP 代理後再跑一次 `check_telegram.py`。 |
| `pip install` 時出現 SSL / 憑證錯誤 | **本機無法安全連到 PyPI** | 可能：<br>• 系統憑證未更新（macOS 可執行 Python 的「Install Certificates」）<br>• 公司代理/防火牆干擾<br>→ 換網路或請 IT 協助；暫時可先用專案內的「本地模擬模式」學習。 |

---

## 建議檢查順序

1. **執行診斷**  
   ```bash
   cd /Users/martin/cursorProject
   python check_telegram.py
   ```  
   看是卡在「套件」「Token」還是「連線 API」。

2. **確認環境一致**  
   - 用同一個終端、同一個 Python（若有 venv 就先 `source venv/bin/activate`）。  
   - 安裝套件與執行程式都用這同一個環境。

3. **確認 Token**  
   - 從 @BotFather 複製，整段貼到 `.env`，不要前後加引號或空格。  
   - 格式應類似：`123456789:ABCdefGHI...`（數字 + `:` + 一串字元）。

4. **確認網路**  
   - 若診斷在第 3 步失敗且錯誤與「連線/逾時」有關，代表本機目前連不到 Telegram API，需從網路/代理/地區限制著手。

---

## SSL 錯誤（裝不起 python-telegram-bot）

若執行 `pip install python-telegram-bot` 時出現：

```text
SSLCertVerificationError ... OSStatus -26276
```

表示你的電腦連到 PyPI 時憑證驗證失敗，常見原因：

- **網路環境**：公司/學校防火牆或代理會檢查 HTTPS，導致憑證錯誤。  
- **系統憑證**：macOS 上可試著執行 Python 安裝目錄裡的「Install Certificates」腳本（若有的話）。  
- **暫時做法**：先使用專案內的「本地模擬模式」（執行 `python main.py` 不裝 telegram 套件），等網路/憑證問題排除後再安裝並連接真實 Telegram。

---

## Gemini API 失效除錯

若機器人回「目前暫時無法回覆，請稍後再試」或沒有 AI 回覆，代表 Gemini API 可能失效。

### 1. 先跑除錯腳本（建議）

在專案目錄執行：

```bash
python debug_gemini.py
```

腳本會：載入 `.env`、直接呼叫 Gemini API、印出**回覆或完整錯誤**。  
依輸出判斷：

| 輸出 | 可能原因 | 做法 |
|------|----------|------|
| 未設定 GEMINI_API_KEY | .env 沒設或變數名錯 | 在 `.env` 加一行 `GEMINI_API_KEY=你的金鑰`，不要空格、引號 |
| 無法匯入 google.genai | 未裝套件 | `pip install google-genai` |
| 401 / Invalid API key | 金鑰錯誤或過期 | 到 [AI Studio](https://aistudio.google.com/app/apikey) 重新建立金鑰，貼到 `.env` |
| 404 / model not found | 模型名稱錯 | 預設用 `gemini-2.0-flash`；若 `.env` 有 `GEMINI_MODEL=gemini-1.5-flash` 請刪除或改為 `gemini-2.0-flash` |
| 連線逾時 / Connection | 網路連不到 Google | 換網路、檢查防火牆或代理 |
| 配額 / quota | 免費額度用盡 | 到 AI Studio 查看使用量，或等隔日重置 |

### 2. 看機器人執行時的日誌

執行 `python main.py` 後，在 Telegram 傳一則訊息，看終端是否出現：

- `Gemini API 錯誤: ...` → 後面會帶例外訊息，可依訊息排查。
- 已改為印出完整 traceback（`exc_info=True`），方便對照錯誤行數。

### 3. 常見原因整理

- **金鑰格式**：`.env` 裡 `GEMINI_API_KEY=金鑰`，等號後直接貼，不要 `"金鑰"` 或前後空格。
- **環境一致**：跑 `main.py` 的 Python 要和跑 `debug_gemini.py`、裝 `google-genai` 的同一個（有 venv 就先 `source venv/bin/activate`）。
- **模型名稱**：預設為 `gemini-2.0-flash`；`gemini-1.5-flash` 在此 API 會回 404，請勿使用。

---

## 總結

- **先跑** `python check_telegram.py`，依訊息判斷是「套件」「Token」還是「連線」問題。  
- **環境要一致**：裝套件與執行程式用同一個 Python（同一個 venv）。  
- **Token 從 @BotFather 取得**，放在 `.env` 的 `TELEGRAM_BOT_TOKEN=` 後面，不要加引號。  
- **連線問題**多半是網路/防火牆/地區限制，需換網路或代理後再試。
