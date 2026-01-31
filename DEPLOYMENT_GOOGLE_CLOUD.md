# 在 Google Cloud 上部署 Telegram 機器人

本指南使用 **Compute Engine（VM 虛擬機）** 來跑你的機器人，讓它 24 小時在線。  
使用 **e2-micro** 可符合 [GCP 免費方案](https://cloud.google.com/free)（每月限額內不扣費）。

---

## 前置準備

1. **Google 帳號**（Gmail）
2. **專案程式碼** 已推到 **GitHub**（或 GitLab），且 **不要** 把 `.env` 推上去（已在 .gitignore）
3. 若本機還沒推過，可先：
   ```bash
   cd /Users/martin/cursorProject
   git init
   git add main.py bot.py logic.py ai_reply.py requirements.txt .env.example README.md DEPLOYMENT.md check_telegram.py TROUBLESHOOTING.md DEVELOPMENT.md
   git commit -m "Telegram bot"
   # 在 GitHub 建立新 repo 後：
   git remote add origin https://github.com/你的帳號/你的repo名.git
   git push -u origin main
   ```

---

## 一、建立 GCP 專案與 VM

### 1. 進入 Google Cloud Console

1. 打開 [Google Cloud Console](https://console.cloud.google.com/)
2. 登入 Google 帳號
3. 若沒有專案：點上方「選取專案」→「新增專案」→ 輸入專案名稱（例如 `telegram-bot`）→「建立」
4. 選取該專案

### 2. 啟用 Compute Engine API

1. 左側選單「API 和服務」→「程式庫」
2. 搜尋 **Compute Engine API**
3. 點進去 →「啟用」

### 3. 建立 VM 執行個體

1. 左側選單「Compute Engine」→「VM 執行個體」
2. 點「建立執行個體」

填寫：

| 欄位 | 建議值 |
|------|--------|
| **名稱** | `telegram-bot`（自訂即可） |
| **地區** | 選離你近的，例如 `asia-east1`（台灣） |
| **機器類型** | **e2-micro**（1 vCPU、1 GB 記憶體，免費額度內） |
| **開機磁碟** | 作業系統 **Debian** 或 **Ubuntu**，約 10 GB |
| **防火牆** | 勾選「允許 HTTP 流量」「允許 HTTPS 流量」（bot 用不到網頁，但勾了無妨） |

3. 點「建立」，等 VM 出現（狀態為綠色勾勾）。

### 4. 記下連線方式

- VM 建立好後，在「VM 執行個體」列表會看到一筆，有 **外部 IP**（例如 `34.80.xxx.xxx`）。
- 點該 VM 名稱可進詳情；點「SSH」會開瀏覽器內建的 SSH 視窗，或你本機有 `gcloud` 的話可用終端機 SSH。

---

## 二、連線到 VM 並安裝環境

### 1. 用瀏覽器 SSH 連線（最簡單）

1. 在 Console 的「VM 執行個體」頁，點你剛建的 VM 那一行的 **「SSH」**
2. 會開新視窗，連到該 VM 的終端機（以 Debian/Ubuntu 為例，使用者名為你 GCP 帳號名或 `username`）

### 2. 在 VM 上安裝 Python 3 與 Git

在 SSH 視窗裡依序執行：

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git
```

確認版本：

```bash
python3 --version
git --version
```

### 3. 把專案放到 VM 上

**方式 A：用 Git clone（推薦，程式碼已在 GitHub）**

```bash
cd ~
git clone https://github.com/你的帳號/你的repo名.git cursorProject
cd cursorProject
```

**方式 B：本機用 gcloud 上傳（若沒用 Git）**

在本機（Mac）終端執行（把 `專案ID`、`VM名稱`、`地區` 換成你的）：

```bash
gcloud compute scp --recurse /Users/martin/cursorProject/* 使用者名@VM名稱 --zone=地區
```

例如：

```bash
gcloud compute scp --recurse /Users/martin/cursorProject/* username@telegram-bot --zone=asia-east1-b
```

VM 上就會有專案檔案（不含 venv、.env，需在 VM 上自己建）。

---

## 三、在 VM 上設定機器人

在 **VM 的 SSH 視窗** 執行：

```bash
cd ~/cursorProject
```

### 1. 建立虛擬環境並安裝依賴

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 建立 .env（Token）

```bash
nano .env
```

內容（換成你的 Token，若有 AI 可加下面兩行）：

```
TELEGRAM_BOT_TOKEN=你的機器人Token
OPENAI_API_KEY=你的OpenAI_Key
```

存檔：`Ctrl+O` → Enter → `Ctrl+X` 離開。

### 3. 先手動測一次

```bash
source venv/bin/activate
python main.py
```

在 Telegram 傳訊息給機器人，有回覆就代表正常。按 `Ctrl+C` 關掉。

---

## 四、用 systemd 讓機器人常駐（關掉 SSH 也繼續跑）

### 1. 查你的使用者名稱

```bash
whoami
```

記下輸出（例如 `username` 或一長串信箱名）。

### 2. 建立 systemd 服務檔

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

貼上以下內容，**把 `你的使用者名` 和路徑改成實際的**（`whoami` 的結果；路徑通常是 `/home/你的使用者名/cursorProject`）：

```ini
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=你的使用者名
WorkingDirectory=/home/你的使用者名/cursorProject
ExecStart=/home/你的使用者名/cursorProject/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

存檔：`Ctrl+O` → Enter → `Ctrl+X`。

### 3. 啟用並啟動服務

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

### 4. 檢查狀態與日誌

```bash
sudo systemctl status telegram-bot
```

應顯示 `active (running)`。看即時日誌：

```bash
journalctl -u telegram-bot -f
```

按 `Ctrl+C` 離開日誌。關掉 SSH 視窗後，機器人仍會在 GCP 上跑。

---

## 五、之後更新程式怎麼做

1. **本機** 改完程式後推到 GitHub：
   ```bash
   git add .
   git commit -m "更新說明"
   git push
   ```

2. **在 GCP VM 上**（SSH 連進去）：
   ```bash
   cd ~/cursorProject
   git pull
   sudo systemctl restart telegram-bot
   ```

---

## 六、常用指令整理

| 目的 | 指令 |
|------|------|
| 看機器人狀態 | `sudo systemctl status telegram-bot` |
| 看即時日誌 | `journalctl -u telegram-bot -f` |
| 重啟機器人 | `sudo systemctl restart telegram-bot` |
| 停止機器人 | `sudo systemctl stop telegram-bot` |
| 開機自動啟動 | 已用 `enable` 設定，重開 VM 會自動跑 |

---

## 七、費用與免費額度

- **e2-micro** 在 [GCP 免費方案](https://cloud.google.com/free) 內：每月可免費用一定時數（依地區而異），超過才計費。
- 只跑一個小 bot 通常不會超過；若不放心，可在 Console「計費」→「預算與警示」設定每月預算上限。

---

## 八、故障排除

| 狀況 | 可能做法 |
|------|----------|
| SSH 連不上 | 檢查 VM 是否在運行、防火牆是否允許 SSH（預設會開） |
| 機器人沒回覆 | `journalctl -u telegram-bot -f` 看錯誤；確認 `.env` 的 Token 正確 |
| 想重設 .env | `nano ~/cursorProject/.env` 修改後 `sudo systemctl restart telegram-bot` |

完成以上步驟後，你的機器人就會在 **Google Cloud 的 VM** 上 24 小時運行。
