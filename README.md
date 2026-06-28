# 🚀 LifeOS — Personal Life Management Telegram Bot

Tera daily task tracker jo Google Sheets ke saath directly connect hota hai.
Har task ka reminder aata hai, tu ✅ Done dabata hai, sheet automatically update ho jaata hai.

---

## 📁 Project Structure

```
lifeos/
├── bot.py                  ← Main entry point
├── config.py               ← All constants & env vars
├── requirements.txt
├── Procfile                ← Render deployment
├── render.yaml
├── .env.example
│
├── core/
│   ├── sheets.py           ← Google Sheets read/write
│   ├── scheduler.py        ← APScheduler reminders
│   └── streak.py           ← SQLite streak tracking
│
├── handlers/
│   ├── start.py            ← /start, /help
│   ├── today.py            ← /today, /yesterday, /tomorrow
│   ├── done.py             ← All inline button callbacks
│   ├── stats.py            ← /stats dashboard
│   └── report.py           ← /report weekly summary
│
├── keyboards/
│   └── inline.py           ← InlineKeyboardMarkup builders
│
└── utils/
    └── formatting.py       ← Message text formatters
```

---

## ⚙️ Step 1 — Google Cloud Setup

### 1.1 Project banana

1. https://console.cloud.google.com pe jao
2. New Project banao → naam do "LifeOS"
3. Project select karo

### 1.2 APIs enable karo

Search karo aur enable karo:
- **Google Sheets API**
- **Google Drive API**

### 1.3 Service Account banana

1. IAM & Admin → Service Accounts → Create Service Account
2. Name: `lifeos-bot`
3. Role: **Editor**
4. Create → Keys → Add Key → JSON
5. JSON file download hoga — iska naam rakho `credentials.json`
6. Yeh file lifeos/ folder mein rakho (KABHI GITHUB PE MAT DAALO)

### 1.4 Sheet share karo

1. Apni Google Sheet kholo (jo tumhare paas pehle se hai)
2. Share button dabao
3. Service account ki email paste karo (credentials.json mein `client_email` field hai)
4. Permission: **Editor**
5. Share karo

### 1.5 Spreadsheet ID nikalo

Sheet URL kuch aisa hoga:
```
https://docs.google.com/spreadsheets/d/1ABC123XYZ.../edit
```
`1ABC123XYZ...` wala part = tumhara `SPREADSHEET_ID`

---

## 🤖 Step 2 — Telegram Bot Setup

1. Telegram pe @BotFather kholo
2. `/newbot` type karo
3. Naam do: `LifeOS`
4. Username do: `lifeos_yourname_bot`
5. **BOT_TOKEN** copy karo (aise dikhega: `1234567890:ABCdef...`)

Apna Chat ID jaanne ke liye:
1. @userinfobot pe message karo
2. `Id:` wali value = tumhara `ADMIN_CHAT_ID`

---

## 🛠️ Step 3 — Local Setup

```bash
# Clone / folder mein jao
cd lifeos

# Virtual env (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Dependencies install karo
pip install -r requirements.txt

# .env file banao
cp .env.example .env
```

`.env` file edit karo:
```env
BOT_TOKEN=1234567890:ABCdef...
SPREADSHEET_ID=1ABC123XYZ...
GOOGLE_CREDS_JSON=credentials.json
ADMIN_CHAT_ID=987654321
```

`credentials.json` file lifeos/ folder mein rakho.

### Test karo locally

```bash
python bot.py
```

Telegram pe `/start` bhejo — agar response aaya toh sab sahi hai! ✅

---

## ☁️ Step 4 — Render Deployment

### 4.1 GitHub pe push karo

```bash
git init
echo "credentials.json" >> .gitignore
echo ".env" >> .gitignore
echo "lifeos_cache.db" >> .gitignore
git add .
git commit -m "LifeOS initial commit"
git remote add origin https://github.com/YOUR_USERNAME/lifeos.git
git push -u origin main
```

### 4.2 Render pe deploy karo

1. https://render.com pe jao → New → **Background Worker**
2. GitHub repo connect karo
3. Settings:
   - **Name**: lifeos-bot
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`

### 4.3 Environment Variables add karo

Render dashboard → Environment → Add:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | Tumhara bot token |
| `SPREADSHEET_ID` | Sheet ID |
| `ADMIN_CHAT_ID` | Tumhara Telegram ID |
| `GOOGLE_CREDS_JSON` | `credentials.json` |

### 4.4 credentials.json Render pe kaise daalein?

**Option A (Recommended):** Secret File
1. Render → Environment → Secret Files
2. Filename: `credentials.json`
3. Contents: credentials.json ka poora content paste karo

**Option B:** Single-line env var  
```bash
# credentials.json ka content ek line mein:
cat credentials.json | python -c "import sys,json; print(json.dumps(json.load(sys.stdin)))"
```
Phir `GOOGLE_CREDS_JSON_CONTENT` naam se add karo aur `config.py` mein thoda tweak karo.

### 4.5 Deploy karo

Save karo → Deploy → Logs check karo
"Bot polling started" dikh gaya = 🎉

---

## 💬 Bot Commands

| Command | Kya karta hai |
|---------|---------------|
| `/start` | Welcome message |
| `/today` | Aaj ke tasks + buttons |
| `/yesterday` | Kal ke tasks |
| `/tomorrow` | Kal ke tasks (preview) |
| `/stats` | Dashboard — completion %, streaks |
| `/report` | Weekly report |
| `/help` | Help |

Plain text bhi kaam karta hai: `today`, `stats`, `report`

---

## ⏰ Reminders Schedule (IST)

| Time | Task |
|------|------|
| 6:00 | 🌅 Morning Motivation |
| 6:30 | Wake Up |
| 6:35 | Drink 500ml Water |
| 6:40 | Warm Up |
| 6:50 | Yoga |
| 7:10 | Surya Namaskar & Pranayama |
| 8:00 | Breakfast |
| 13:00 | Lunch |
| 15:30 | Water Reminder |
| 18:45 | Healthy Snack |
| 19:00 | Evening Walk |
| 19:30 | Workout (M/W/F) |
| 20:00 | Dinner |
| 20:45 | Crypto Study |
| 22:30 | Sleep by 10:30 PM |

---

## 🔥 How It Works

```
Reminder aata hai
       ↓
Tu /today type karta hai
       ↓
Bot Google Sheet se aaj ka row fetch karta hai
       ↓
Har task ke saath ✅ Done ❌ Skip ⏰ Snooze buttons
       ↓
Tu ✅ Done dabata hai
       ↓
Sheet immediately update → checkbox TRUE, completion % recalculate
       ↓
Streak counter bhi update hota hai (SQLite)
       ↓
/stats pe sab kuch dikh jaata hai
```

---

## 🔒 Security Notes

- `credentials.json` — kabhi GitHub pe mat daalo
- `.env` — kabhi GitHub pe mat daalo  
- `.gitignore` mein dono add karo (ऊपर diya hai)
- Render pe Secret Files feature use karo credentials ke liye

---

## 🐛 Common Issues

**"Sheet data nahi mila"**  
→ Spreadsheet ID sahi hai? Service account ko Editor access diya?

**Reminders nahi aa rahe**  
→ ADMIN_CHAT_ID sahi hai? Bot se pehle `/start` bheja?

**"APIError: 403"**  
→ Google Sheets API enable hai? Service account email se sheet share ki?

**Render pe deploy ke baad bot kaam nahi kar raha**  
→ Logs check karo, credentials.json Secret File sahi se upload hui?
