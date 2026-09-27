<div align="center">

# 🌟 **ANIME DEKHO BOT** 🌟

<p align="center">
  <img src="https://images.unsplash.com/photo-1576477330363-5460ff24818d?w=1280" 
       alt="AnimeDekho Bot - Anime Streaming & Library Engine" 
       style="max-width: 100%; border-radius: 20px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);"
       width="1280">
</p>

### ⚡ **Next-Gen Anime Streaming, Archival & Channel Automation Engine** ⚡

<p align="center">
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://github.com/TgbotWorld/animedekho-bot"><img src="https://img.shields.io/badge/MTProto-WZGram%202GB%20Engine-0088cc?style=for-the-badge&logo=telegram&logoColor=white" alt="WZGram"/></a>
  <a href="https://mongodb.com"><img src="https://img.shields.io/badge/Database-MongoDB%20Async-47A248?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB"/></a>
  <a href="https://anilist.co"><img src="https://img.shields.io/badge/Metadata-AniList%20GraphQL-02A9FF?style=for-the-badge&logo=anilist&logoColor=white" alt="AniList"/></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-F59E0B?style=for-the-badge" alt="License"/></a>
</p>

<p align="center">
  <a href="#-flagship-features">🔥 Features</a> • 
  <a href="#-quick-commands">⚡ Commands</a> • 
  <a href="#-configuration-guide">⚙️ Config</a> • 
  <a href="#-vps-deployment">🚀 Deploy</a>
</p>

</div>

---

## 🌌 What is AnimeDekho Bot?

**AnimeDekho Bot** is a powerful automated Telegram engine that turns any anime channel into a professional streaming + archival platform.

It fetches official AniList HD art, downloads multi-quality anime streams (480p → 4K), auto-generates stunning thumbnails, and maintains **single-post-per-anime** albums with zero duplicates.

```mermaid
flowchart LR
    User --> Bot[AnimeDekho Bot]
    Bot --> AniList[AniList GraphQL]
    Bot --> Streams[Multi-Quality Streams]
    Bot --> MongoDB[(MongoDB)]
    Bot --> Thumbnail[Auto Thumbnail Studio]
```

---

## 🔥 Flagship Features

### 🎨 Auto Thumbnail Studio (5 Premium Styles)

Automatically generates beautiful 1280x720 HD thumbnails every time. 5 stunning designs + random mode!

| Style          | Vibe                          | Perfect For                  |
|----------------|-------------------------------|------------------------------|
| `modern`       | High-contrast dark neon       | Weekly TV episodes           |
| `cinematic`    | Indigo widescreen letterbox   | Movies & long story arcs     |
| `movie_gold`   | Luxury metallic gold frame    | OVAs & feature films         |
| `neon_cyber`   | Electric cyan + hot pink      | Shonen, Sci-Fi, Action       |
| `minimal`      | Clean frosted glass look      | Aesthetic index channels     |
| `random`       | Dynamic every upload          | Surprise factor              |

### ⭐ Premium Telegram Emojis

Full support for Telegram Premium custom emojis with beautiful Unicode fallback.

### 📚 Smart Library Engine

- **Single master post per anime** — Updates in-place when new episodes drop
- **Auto movie → series routing** — Jujutsu Kaisen 0 goes to its parent series
- **New episode notification thread** with clean HTML formatting
- **Channel navigation buttons** + optional ongoing broadcast channel

### 🔒 Advanced Security

- 2-minute expiring invite links
- Auto media delete with countdown
- Unlimited child worker bots for load balancing
- Full privacy & rate-limit protection

---

## ⚡ Quick Commands

| Command       | Description                              |
|---------------|------------------------------------------|
| `/start`      | Main menu + welcome banner               |
| `/search`     | Anime search across database              |
| `/commands`   | Interactive command guide                 |
| `/settings`   | Real-time admin panel (admins only)       |

*(Full command list available in-bot with `/commands`)*

---

## ⚙️ Configuration

Edit `config.py` or use `.env` file:

| Variable                | Description                                      | Default     |
|-------------------------|--------------------------------------------------|-------------|
| `BOT_TOKEN`             | Telegram Bot Token                               | Required    |
| `API_ID`                | Telegram API ID                                  | Required    |
| `API_HASH`              | Telegram API Hash                                | Required    |
| `OWNER_ID`              | Your Telegram ID                                 | Required    |
| `MAIN_CHANNEL`          | Main library channel                             | `0`         |
| `THUMB_TEMPLATE`        | Thumbnail style (`modern`, `cinematic` etc.)     | `modern`    |
| `RANDOM_THUMB_TEMPLATE` | Random style every upload                        | `false`     |
| `AUTO_DELETE_TIME`      | Media auto-delete timer (seconds)                | `600`       |
| `MONGO_URI`             | MongoDB connection string                        | —           |

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/TgbotWorld/animedekho-bot.git
cd animedekho-bot

# 2. Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp sample.env .env
# Edit .env or config.py

# 4. Run
python3 main.py
```

**Production ready** with Systemd support, Docker, Railway, and more.

---

## 📜 License

MIT License — Free to use and modify!

<div align="center">
  <p><strong>Made with ❤️ for the Anime Community</strong></p>
</div>

