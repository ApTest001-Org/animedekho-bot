<div align="center">

# ❖ ANIME DEKHO BOT ❖

<p align="center">
  <img src="./assets/banner.jpg" width="100%" alt="AnimeDekho Bot Banner" style="border-radius: 12px;"/>
</p>

### ⚡ *Next-Generation Telegram Anime Streaming, Archival & Channel Automation Engine* ⚡

<p align="center">
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://github.com/TgbotWorld/animedekho-bot"><img src="https://img.shields.io/badge/MTProto-WZGram%202GB%20Engine-0088cc?style=for-the-badge&logo=telegram&logoColor=white" alt="WZGram"/></a>
  <a href="https://mongodb.com"><img src="https://img.shields.io/badge/Database-MongoDB%20Async-47A248?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB"/></a>
  <a href="https://anilist.co"><img src="https://img.shields.io/badge/Metadata-AniList%20GraphQL-02A9FF?style=for-the-badge&logo=anilist&logoColor=white" alt="AniList"/></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-F59E0B?style=for-the-badge" alt="License"/></a>
</p>

<p align="center">
  <a href="#-flagship-features"><b>[ ⚡ Features ]</b></a> &nbsp;•&nbsp;
  <a href="#-quick-commands"><b>[ 🎮 Commands ]</b></a> &nbsp;•&nbsp;
  <a href="#-configuration-guide"><b>[ ⚙️ Config ]</b></a> &nbsp;•&nbsp;
  <a href="#-system-architecture"><b>[ 🏗️ Architecture ]</b></a> &nbsp;•&nbsp;
  <a href="#-vps-deployment"><b>[ 🚀 Deploy ]</b></a>
</p>

---

</div>

## 🌌 What is AnimeDekho Bot?

> [!NOTE]
> **AnimeDekho Bot** is an automated Telegram publishing engine engineered for anime networks, archival channels, and streaming communities. It automatically fetches official AniList HD artwork, downloads multi-quality streams (480p to 4K), generates branded 1280x720 video thumbnails, and maintains a clean **single-post-per-anime** channel library with zero duplicate clutter.

```
       AniList GraphQL ──┐
                         ▼
Anime Streamers ──► [AnimeDekho Core] ──► Auto-Thumb Studio ──► Main Library Channel
                         ▲
MongoDB Async   ─────────┘
```

---

## ⚡ Flagship Features

### 🎨 Modular 5-Design Auto-Thumbnail Studio
Automatically generates crisp **1280x720 HD (16:9)** thumbnails using PIL, fusing official artwork, episode badges, audio tags, and channel branding. Choose your style or let the bot randomize per upload!

| Style | Aesthetic Palette | Best Suited For |
| :--- | :--- | :--- |
| **`modern`** | High-contrast dark gradient with rounded poster | Weekly anime TV episodes & simulcasts |
| **`cinematic`** | Indigo widescreen letterbox with silver framing | Theatrical movies & dramatic story arcs |
| **`movie_gold`** | Luxury obsidian & metallic gold VIP frame | Feature films, OVA specials & 4K releases |
| **`neon_cyber`** | Cyberpunk theme with electric cyan & hot pink | Shonen, Sci-Fi & futuristic action series |
| **`minimal`** | Translucent frosted glass card with soft shadows | Aesthetic, clean & uncluttered index channels |
| **`random`** | Dynamic rotation mode | Automatically picks a different design on every upload |

---

### ⭐ Telegram Premium Custom Emojis
- **Native Custom Emoji Support**: Fully supports Telegram Premium `<emoji id="...">` tags across start menus, file captions, and library posts.
- **100% Graceful Unicode Fallback**: If custom emojis are disabled or unsupported by the client, standard clean Unicode emojis (⭐, 🎬, 🔊, 📷, 🎭, ➽, ✓) render automatically with zero errors.

---

### 🏛️ Main Library Channel & In-Place Auto-Updates
- **Single Master Post Per Anime**: Never duplicate posts. The bot updates the existing album message in-place whenever a new episode arrives.
- **New Episode Reply Thread**: Automatically sends a clean notification reply directly to the series' main post:

```html
<b>The Angel Next Door Spoils Me Rotten</b>
<b>──────────────────────</b>

<blockquote>• S2 | Episode 04 | #Added ✓</blockquote>

<a href="https://t.me/YourBot?start=get_...">Start The Bot And Get Linke Here</a>
```

> [!TIP]
> **Zero Inline Buttons on Reply**: The notification thread uses a pure text hyperlink, keeping the discussion section clean while allowing users to access files in a single tap!

- **Channel Navigation Buttons**:
  - `[ DOWNLOAD ]` — Routes users into the mapped private anime channel join flow.
  - `[ DOWNLOAD NETWORK ]` — Directs users to your main network channel.
- **Ongoing Broadcast Channel**: Optionally mirrors new episode alerts to `ONGOING_CHANNEL`.

---

### 🎬 Smart Movie-to-Series Channel Routing
- Franchise movies (e.g. *Demon Slayer: Mugen Train*, *Jujutsu Kaisen 0*) are automatically detected and uploaded to the **existing parent anime series channel**.
- Keeps entire franchises organized under one roof and eliminates duplicate channels.

---

### 🛡️ Security, Privacy & Mesh Network
- **2-Minute Expiring Invite Links**: Generates dynamic single-use channel links (`expire_date = now + 120s`) to prevent link scraping and protect channels.
- **Media Auto-Delete Timer**: Automatically deletes delivered media from private user chats after a set delay (e.g. 10m) with real-time countdown alerts.
- **Child Worker Mesh**: Add unlimited auxiliary worker bots (`/addbot`) to balance download traffic and bypass Telegram API rate limits.
- **Dual Configuration Engine**: Edit [`config.py`](file:///workspaces/animedekho-bot/config.py) directly or configure via `.env` environment variables.

---

## 🎮 Quick Commands

Only the 4 essential core commands are shown below. Tap the drawer underneath to view all available commands!

| Command | Action | Availability |
| :--- | :--- | :---: |
| `/start` | Open main menu, view releases, or access deep links | Everyone |
| `/search <title>` | Search anime catalog for series and movies | Everyone |
| `/commands` | Open interactive in-bot visual guide & category browser | Everyone |
| `/settings` | Open real-time visual control panel (toggle features on the fly) | Admins |

<br>

<details>
<summary><b>▶ TAP HERE TO VIEW COMPLETE COMMAND DIRECTORY (17 COMMANDS)</b></summary>

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

## ⚙️ Configuration Guide

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

## 🚀 VPS Deployment

### Prerequisites
- **Python**: 3.10, 3.11, 3.12, or 3.14
- **FFmpeg**: Required for stream integrity checks and thumbnail generation
- **MongoDB**: Local server or free [MongoDB Atlas](https://www.mongodb.com/atlas) cluster

```bash
# 1. Update packages & install dependencies
sudo apt update && sudo apt install -y python3 python3-pip python3-venv ffmpeg git

# 2. Clone the repository
git clone https://github.com/TgbotWorld/animedekho-bot.git
cd animedekho-bot

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# 5. Configure credentials
cp sample.env .env
nano .env   # (or edit config.py directly)

# 6. Start the bot
python3 main.py
```

### 24/7 Background Service (Systemd)

```ini
# /etc/systemd/system/animedekho.service
[Unit]
Description=AnimeDekho Telegram Bot Service
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
