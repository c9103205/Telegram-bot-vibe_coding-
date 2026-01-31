# 將機器人部署到 Server

這份文件說明如何把開發好的專案「放上」一台主機（server），並讓機器人 24 小時運行。

**若你要部署在 Google Cloud（Compute Engine VM）**，請直接看 **[DEPLOYMENT_GOOGLE_CLOUD.md](DEPLOYMENT_GOOGLE_CLOUD.md)**，有完整步驟。

---

## 前提：你要有一台 Server

- **雲端主機（VPS）**：例如 DigitalOcean、Linode、AWS EC2、Google Cloud、台灣的遠振等，通常會給你一個 **IP** 和 **SSH 登入方式**。
- **或** 家裡/辦公室一台 **一直開著的 Linux 電腦**，有固定 IP 或能對外連線。

以下假設你的 server 是 **Linux**，且你可以用 **SSH** 登入（例如：`ssh user@你的主機IP`）。

---

## 步驟一：把檔案傳到 Server

選一種方式即可。

### 方式 A：用 SCP（複製整個專案資料夾）

在你**本機**（放專案的電腦）打開終端，進入專案上一層目錄，執行：

```bash
# 把 cursorProject 整個資料夾傳到 server 的 home 目錄
scp -r /Users/martin/cursorProject 使用者名稱@主機IP:~
```

例如：`scp -r /Users/martin/cursorProject ubuntu@123.45.67.89:~`  
傳完後，server 上會有 `~/cursorProject/`，裡面是 main.py、bot.py、requirements.txt 等。

**注意**：`.env` 通常不會被傳（若專案有 .gitignore 且你是用 git 備份的話）。若用 SCP 複製整個資料夾，.env **會一起傳**，請確認主機上權限安全。若你本機 .env 不想傳，可先從本機刪掉再 scp，或傳完在 server 上自己建 .env（見步驟三）。

### 方式 B：用 Git（推薦，方便之後更新）

1. **本機**：把專案放到 Git 並推到 GitHub / GitLab（**不要**把 `.env` 加入 git）。

2. **Server 上**：安裝 git 後 clone：

   ```bash
   ssh 使用者名稱@主機IP
   cd ~
   git clone https://github.com/你的帳號/你的專案.git cursorProject
   cd cursorProject
   ```

之後要更新：在 server 上 `cd cursorProject` 再 `git pull` 即可。

### 方式 C：用 rsync（只傳有變更的檔案）

```bash
rsync -avz --exclude 'venv' --exclude '.env' /Users/martin/cursorProject/ 使用者名稱@主機IP:~/cursorProject/
```

會排除 `venv` 和 `.env`，避免蓋掉 server 上的 .env。

---

## 步驟二：在 Server 上裝好環境

SSH 登入主機後：

```bash
cd ~/cursorProject   # 或你放專案的目錄

# 建立虛擬環境
python3 -m venv venv
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

確認 `python main.py` 會報「請設定 TELEGRAM_BOT_TOKEN」之類的錯誤，代表程式有跑、只差 Token。

---

## 步驟三：在 Server 上設定 .env（Token）

**.env 不要從本機複製貼上**（可能含本機路徑或舊設定），在 server 上**新建**即可：

```bash
cd ~/cursorProject
nano .env
```

內容一行（換成你的 Token）：

```
TELEGRAM_BOT_TOKEN=你的機器人Token
```

若有使用 AI 回覆，可加：

```
OPENAI_API_KEY=你的OpenAI_Key
# 或
GEMINI_API_KEY=你的Gemini_Key
```

存檔後離開（nano：`Ctrl+O` 存檔，`Ctrl+X` 離開）。

---

## 步驟四：讓機器人一直在背景跑

若直接執行 `python main.py`，關掉 SSH 視窗程式就停了。要用下列方式之一讓它**常駐**。

### 方式一：systemd（開機自動啟動、崩潰可重啟，推薦）

1. 建立服務檔：

   ```bash
   sudo nano /etc/systemd/system/telegram-bot.service
   ```

2. 貼上以下內容（把 `你的使用者名稱` 和專案路徑改成實際的）：

   ```ini
   [Unit]
   Description=Telegram Bot
   After=network.target

   [Service]
   Type=simple
   User=你的使用者名稱
   WorkingDirectory=/home/你的使用者名稱/cursorProject
   ExecStart=/home/你的使用者名稱/cursorProject/venv/bin/python main.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. 啟用並啟動：

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable telegram-bot
   sudo systemctl start telegram-bot
   ```

4. 檢查狀態與日誌：

   ```bash
   sudo systemctl status telegram-bot
   journalctl -u telegram-bot -f
   ```

### 方式二：screen（簡單，關掉 SSH 也不會停）

```bash
cd ~/cursorProject
source venv/bin/activate
screen -S bot
python main.py
```

按 `Ctrl+A` 再按 `D` 脫離 screen，程式會繼續跑。要再進去看：

```bash
screen -r bot
```

---

## 之後更新程式怎麼做

1. **本機**改好程式，用 Git 的話就 `git push`。
2. **Server 上**：
   - 用 Git：`cd ~/cursorProject` → `git pull`
   - 用 SCP/rsync：在本機再執行一次 scp/rsync 把專案傳上去。
3. 重啟機器人：
   - systemd：`sudo systemctl restart telegram-bot`
   - screen：`screen -r bot` → `Ctrl+C` 停掉 → 再執行 `python main.py`，再 `Ctrl+A` `D` 脫離。

---

## 檢查清單

| 項目 | 說明 |
|------|------|
| 檔案已傳到 server | 在 server 上 `ls ~/cursorProject` 能看到 main.py、bot.py、requirements.txt 等 |
| 有建 venv 並安裝依賴 | `source venv/bin/activate` 後 `pip list` 能看到 python-telegram-bot |
| .env 已設定 | server 上 `~/cursorProject/.env` 存在且含 `TELEGRAM_BOT_TOKEN=...` |
| 用 systemd 或 screen 常駐 | 關掉 SSH 後，在 Telegram 傳訊息給機器人仍會回覆 |

這樣，**server 就是你的主機**，程式在 server 上跑，機器人就會 24 小時上線。
