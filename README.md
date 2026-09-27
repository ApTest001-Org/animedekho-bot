<div align="center">

# ⚡ AnimeDekho Bot

<p align="center">
  <img src="https://images.unsplash.com/photo-1578632767115-351597cf2477?w=1200&auto=format&fit=crop" width="100%" alt="AnimeDekho Bot Banner" style="border-radius: 14px; box-shadow: 0 8px 24px rgba(0,0,0,0.5);"/>
</p>

### *Next-Generation Telegram Anime Streaming & Library Automation Engine*

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![WZGram](https://img.shields.io/badge/Engine-WZGram%20MTProto%202GB-0088cc?style=for-the-badge&logo=telegram&logoColor=white)](https://github.com/TgbotWorld/animedekho-bot)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB%20Async-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)
[![AniList](https://img.shields.io/badge/Metadata-AniList%20GraphQL-02A9FF?style=for-the-badge&logo=anilist&logoColor=white)](https://anilist.co)
[![License](https://img.shields.io/badge/License-MIT-F59E0B?style=for-the-badge)](./LICENSE)

<p align="center">
  <a href="#-flagship-features">Features</a> •
  <a href="#-interactive-commands">Commands</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="#-system-architecture">Architecture</a> •
  <a href="#-deployment--setup">Quick Start</a>
</p>

---

</div>

## 🌟 Overview

> [!NOTE]
> **AnimeDekho Bot** is an automated Telegram publishing and streaming suite engineered for anime networks, archival channels, and communities. It eliminates channel clutter by indexing every anime into a **single master post**, auto-updating on new episode drops, routing movies directly to parent anime series channels, and generating studio-grade **1280x720 HD thumbnails** on the fly.

```
       AniList GraphQL ──┐
                         ▼
Anime Streamers ──► [AnimeDekho Engine] ──► Auto-Thumb Studio ──► Main Library Channel
                         ▲
MongoDB Async   ─────────┘
```

---

## 🚀 Flagship Features

### 🎨 Modular 5-Design Auto-Thumbnail Studio
The bot features a built-in PIL-based graphics engine that automatically creates pristine **1280x720 HD (16:9)** thumbnails containing official artwork, season/episode tags, audio pills, and bot watermarks.

| Style Name | Aesthetic & Palette | Highlights |
| :--- | :--- | :--- |
| **`modern`** | High-contrast dark gradient with rounded artwork | Dual-gradient overlay, bright accent pills, clean typography |
| **`cinematic`** | Indigo theatrical letterbox with silver framing | 16:9 widescreen bars, atmospheric glow, film-reel motif |
| **`movie_gold`** | Luxury obsidian with metallic gold VIP frame | Specially tailored for movies, feature films & 4K specials |
| **`neon_cyber`** | Cyberpunk theme with electric cyan & hot pink glow | Dual-color neon glow border, futuristic tech brackets |
| **`minimal`** | Frosted glass translucent card with soft shadows | Modern frosted overlay, airy typography, uncluttered layout |
| **`random`** | Dynamic per-upload rotation | Automatically picks a different design on every new episode |

---

### ⭐ Telegram Premium Custom Emojis
- **Native Custom Emoji Support**: Renders Telegram Premium `<emoji id="...">` tags across library captions, movie posts, and start menus.
- **Graceful Zero-Crash Fallback**: Automatically renders clean standard Unicode symbols (⭐, 🎬, 🔊, 📷, 🎭, ➽, ✓) if custom emojis are disabled, unsupported, or invalid.

---

### 🏛️ Main Library Channel UI & In-Place Auto-Updates
- **Single Master Post Per Anime**: Never duplicate posts. The bot updates the existing album message in-place whenever a new episode is uploaded.
- **New Episode Reply Thread**: When an episode is uploaded, the bot sends an automated reply directly to the series' main post:

```html
<b>The Angel Next Door Spoils Me Rotten</b>
<b>──────────────────────</b>

<blockquote>• S2 | Episode 04 | #Added ✓</blockquote>

<a href="https://t.me/YourBot?start=get_...">Start The Bot And Get Linke Here</a>
```

> [!TIP]
> **Pure Text Hyperlink**: The notification contains **zero inline buttons** to keep the discussion thread clean, while allowing users to launch the bot flow in a single tap!

- **Refined Channel Buttons**:
  - `[ DOWNLOAD ]` — Routes user directly to the mapped anime series channel.
  - `[ DOWNLOAD NETWORK ]` — Links users to your main network channel.
- **Dedicated Ongoing Feed**: Optionally broadcasts real-time release alerts to `ONGOING_CHANNEL`.

---

### 🎬 Smart Movie-to-Series Channel Routing
- Movies and film sequels (e.g. *Demon Slayer: Mugen Train*, *Jujutsu Kaisen 0*) are automatically detected and uploaded to the **existing parent anime series channel**.
- Prevents duplicate channel creation and keeps your anime network organized.

---

### 🛡️ Security, Privacy & Mesh Network
- **2-Minute Expiring Invite Links**: Prevents link scraping with single-use time-limited channel invitations (`expire_date = now + 120s`).
- **Media Auto-Delete Timer**: Automatically wipes delivered media from private user chats after a configurable timer (e.g. 10 minutes) with real-time countdown alerts.
- **Multi-Worker Child Mesh**: Add unlimited auxiliary worker bots (`/addbot`) to balance download traffic and bypass Telegram API rate limits.
- **Dual Configuration Engine**: Seamlessly switch between editing [`config.py`](file:///workspaces/animedekho-bot/config.py) directly or using `.env` variables.

---

## ⚡ Interactive Commands

### 📱 Quick Commands

Only the most frequently used commands are listed below. For full interactive navigation, tap `/commands` inside the bot!

| Command | Action | Who Can Use |
| :--- | :--- | :---: |
| `/start` | Open main menu, view releases, or access deep links | Everyone |
| `/search <title>` | Search anime catalog for series and movies | Everyone |
| `/commands` | Open interactive in-bot visual guide & category browser | Everyone |
| `/settings` | Open real-time visual control panel (toggle features on the fly) | Admins |

---

<details>
<summary><b>👇 Tap to Expand Full Command Directory (17 Commands)</b></summary>
<br>

#### 👤 Public User Commands
| Command | Description |
| :--- | :--- |
| `/start` | Launch the bot, check welcome banner, or handle file delivery deep links |
| `/search <title>` | Search across the entire AnimeDekho multi-quality database |
| `/schedule` | View 30-day upcoming dubbed anime releases with pagination |
| `/commands` | Interactive visual catalog of all commands and features |
| `/help` | Detailed bot usage manual and instructions |

#### 👑 Administrator & Owner Commands
| Command | Description |
| :--- | :--- |
| `/settings` | Visual control panel with real-time toggle buttons |
| `/stats` | View live VPS hardware telemetry (CPU, RAM, Disk, Uptime) |
| `/health` | Diagnostic self-check for Main Bot, Userbot, Child Bots & MongoDB |
| `/users` | Analytics on registered bot users and activity metrics |
| `/broadcast <msg>` | Broadcast announcement message to all registered users |
| `/autosearch <on\|off>` | Toggle direct chat text search trigger |
| `/automonitor <on\|off>` | Toggle automated background episode watcher |
| `/setthumb` | Set custom channel upload thumbnail (reply to photo) |
| `/delthumb` | Remove custom channel upload thumbnail |
| `/mapchannel <slug> <cid>` | Route specific anime uploads to a dedicated channel |
| `/addbot <token>` | Register a child worker bot to distribute download traffic |
| `/login` | Interactive MTProto userbot login wizard |
| `/ai <prompt>` | Query the natural-language anime assistant |

</details>

---

## ⚙️ Configuration

Configure the bot by modifying [`config.py`](file:///workspaces/animedekho-bot/config.py) directly or by setting variables in a `.env` file:

| Variable | Required | Default | Description |
| :--- | :---: | :---: | :--- |
| `BOT_TOKEN` | **Yes** | — | Telegram Bot Token from [@BotFather](https://t.me/BotFather) |
| `API_ID` | **Yes** | — | Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | **Yes** | — | Telegram API Hash from [my.telegram.org](https://my.telegram.org) |
| `OWNER_ID` | **Yes** | — | Telegram User ID of the primary bot administrator |
| `MAIN_CHANNEL` | No | `0` | Main Channel ID for single-post series albums |
| `ONGOING_CHANNEL` | No | `0` | Channel ID for live new-episode broadcast alerts |
| `NETWORK_CHANNEL_LINK`| No | `https://t.me/animedekho` | Link assigned to the `DOWNLOAD NETWORK` button |
| `ENABLE_CUSTOM_EMOJI` | No | `false` | Enable Telegram Premium custom emojis (`<emoji id="...">`) |
| `THUMB_TEMPLATE` | No | `modern` | Active thumbnail design (`modern`, `cinematic`, `movie_gold`, `neon_cyber`, `minimal`) |
| `RANDOM_THUMB_TEMPLATE`| No | `false` | When true, chooses a random thumbnail style on every upload |
| `AUTO_SEARCH` | No | `true` | Trigger search when anime name is typed directly in chat |
| `AUTO_THUMB` | No | `true` | Automatically generate 1280x720 HD thumbnails |
| `AUTO_DELETE_TIME` | No | `600` | Delivered video auto-delete timer in seconds (`0` = off) |
| `FSUB_MOD` | No | `true` | Use 2-minute expiring single-use invite links for Force-Subscribe |
| `MONGO_URI` | No | `mongodb://localhost:27017` | MongoDB connection URI (Atlas or self-hosted) |
| `AI_API_KEY` | No | `""` | API key for `/ai` assistant (OpenAI, Gemini, OpenRouter) |

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    User([Telegram User]) <--> MainBot[Main AnimeDekho Bot]
    MainBot <--> Workers[Child Worker Bot Mesh\nLoad Balanced Downloads]
    
    subgraph Data Sources
        API[AnimeDekho / Multi-Stream API]
        AniList[AniList GraphQL API\nAuthoritative Posters & Metadata]
        ScheduleSource[AnimeDubHindi Scraper\n30-Day Upcoming Schedule]
    end

    subgraph Processing Pipeline
        Downloader[Async Downloader & FFmpeg Engine]
        ThumbStudio[Modular Thumbnail Studio\n5 Visual Designs + Random Mode]
        VideoValidator[FFprobe Stream & Codec Validator]
    end

    subgraph Storage & Channels
        MongoDB[(MongoDB Database\nAsync Motor Drivers)]
        MainLib[Main Library Channel\nSingle Post per Anime]
        AnimeChan[Dedicated Anime Series Channel\nAuto Movie + Episode Routing]
        OngoingChan[Ongoing Broadcast Channel\nInstant Update Feed]
    end

    MainBot --> API
    MainBot --> AniList
    MainBot --> ScheduleSource
    API --> Downloader
    AniList --> ThumbStudio
    Downloader --> VideoValidator
    ThumbStudio --> Downloader
    Downloader --> AnimeChan
    Downloader --> MongoDB
    MongoDB <--> MainLib
    MongoDB <--> OngoingChan
```

---

## 🛠️ Deployment & Setup

### Prerequisites
- **Python**: 3.10, 3.11, 3.12, or 3.14
- **FFmpeg**: Required for media stream verification and thumbnail processing
- **MongoDB**: Local `mongod` instance or cloud-hosted [MongoDB Atlas](https://www.mongodb.com/atlas)

### Standard Linux VPS Deployment

```bash
# 1. Update packages and install FFmpeg
sudo apt update && sudo apt install -y python3 python3-pip python3-venv ffmpeg git

# 2. Clone the repository
git clone https://github.com/TgbotWorld/animedekho-bot.git
cd animedekho-bot

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Configure credentials
cp sample.env .env
nano .env   # (or edit config.py directly)

# 6. Launch the bot
python3 main.py
```

### 24/7 Production Service (Systemd)

```ini
# /etc/systemd/system/animedekho.service
[Unit]
Description=AnimeDekho Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/animedekho-bot
ExecStart=/root/animedekho-bot/venv/bin/python3 main.py
Restart=always
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now animedekho
sudo systemctl status animedekho
```

---

## 📄 License & Community

Distributed under the **MIT License**. See [`LICENSE`](file:///workspaces/animedekho-bot/LICENSE) for details.

<div align="center">
  <b>Built with ❤️ by the AnimeDekho Community</b>
</div>
