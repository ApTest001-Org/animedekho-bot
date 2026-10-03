# 🎌 AnimeDekho Bot — Complete Deep Audit, Bug Fixes & Enhancement Report
**Addressed Issues:** [Issue #22](https://github.com/PR0FESS0R-99/animedekho-bot/issues/22) & [Issue #23](https://github.com/PR0FESS0R-99/animedekho-bot/issues/23)  
**Date:** October 2026  
**Status:** ✅ Fully Audited, Implemented, Tested & Verified

---

## 1. Executive Summary

This deep audit and engineering refactor resolves all core bugs and system limitations outlined in Issues #22 and #23. The focus was on moving the bot from stream-embed scraping to **direct video file sources**, fixing the **"Wrong Anime Result"** matching bug across all multi-source scrapers, preventing the **0.00 min video duration** display on Telegram, establishing an **immediate feedback and cancellable download job manager**, enabling **VidStream / FirePlayer (`ravok.buzz`) stream resolution**, preventing **MongoDB `$set` vs `$setOnInsert` update collisions**, eliminating the **Windows subprocess crash**, and standardizing **Modern Formatted Cards** as the sole default UI.

---

## 2. Root Cause Analysis & Solutions

### 1. Primary Download Source Prioritization & AnimeDubHindi Integration
* **Problem**: Stream embed scrapers (`AnimeDrive`, `ToonFlix`, `AnimeDekho`) often rely on ephemeral third-party players with aggressive Cloudflare protections or low-bitrate streams. In contrast, direct video file sources provide direct MKV/MP4 files (often stored on high-speed Cloudflare Workers or R2) with multiple audio tracks and full quality variants.
* **Failure Example in Issue #22**: `JoJo’s Bizarre Adventure — Season 2 Episode 1` failed or returned missing servers. On AnimeDubHindi, this episode is readily available in 480p, 720p, and 1080p BDRip with Multi Audio (Hindi-Eng-Jap).
* **Fix**:
  1. Built new native extractor [`extractors/animedubhindi.py`](file:///workspaces/animedekho-bot/extractors/animedubhindi.py):
     - Scrapes `https://www.animedubhindi.link/` and decodes `https://new.adhlinks.com/episode/...` redirects to obtain direct Cloudflare Worker download URLs (`*.workers.dev/?id=...`).
  2. Registered in [`extractors/multisource.py`](file:///workspaces/animedekho-bot/extractors/multisource.py) as **Source Index 0**, prioritizing direct download/video file sources before web scrapers:
     - `AnimeDubHindi` -> `ToonWorld4All` -> `RareAnimes` -> `DeadToons` -> `TOONo` -> `AnimeDrive` -> `ToonFlix`.
  3. Live tested and verified resolution of `JoJo's Bizarre Adventure S02E01 [480p]`:
     ```json
     {
       "url": "https://icy-feather-221c.jakcminasi.workers.dev/?id=...&name=%5BAnimedubhindi.com%5D+Jojos+Bizarre+Adventure+S02E01+480p+BDRip+%5BHindi-Eng-Jap%5D+Esub.mkv",
       "quality": "480p",
       "source": "AnimeDubHindi"
     }
     ```

---

### 2. "Wrong Anime Result" Scraper Matching Bug
* **Problem**: In [`extractors/rareanimes.py`](file:///workspaces/animedekho-bot/extractors/rareanimes.py), [`extractors/deadtoons.py`](file:///workspaces/animedekho-bot/extractors/deadtoons.py), [`extractors/toonworld4all.py`](file:///workspaces/animedekho-bot/extractors/toonworld4all.py), and [`extractors/animedrive.py`](file:///workspaces/animedekho-bot/extractors/animedrive.py), searches fell back to `search_results[0]` when requested season or title didn't match, or matched any post containing `"season {season}"` regardless of title similarity (e.g. returning *Clevatess Season 2* when searching *JoJo Season 2*).
* **Fix**:
  - Implemented strict title keyword overlap: non-trivial word tokens from the query must match the post title with at least 2 common tokens (or all tokens if query is short).
  - Enforced strict season verification. If no post matches the requested title and season, the extractor returns `None` rather than falling back to an unrelated anime.
  - Eliminated arbitrary `post_buttons[0]` and `episode_links[0]` fallbacks.

---

### 3. Video Duration `0.00 min` Bug
* **Problem**: On Telegram, delivered anime videos sometimes displayed `0.00 min` in captions. In [`bot/downloader.py`](file:///workspaces/animedekho-bot/bot/downloader.py), FFprobe output for streams or format containers frequently has `"duration": "N/A"`. The Python expression `float(format_info.get("duration") or v_stream.get("duration") or 0)` evaluated the truthy string `"N/A"`, raising `ValueError: could not convert string to float: 'N/A'`. The exception handler caught this and returned metadata containing only `{"size": size}`, missing `width`, `height`, and `duration`. Consequently, `vid_duration = 0`, leading to `0.00 min` on Telegram.
* **Fix**:
  - Created module-level robust parser [`_parse_safe_float(val, default=0.0)`](file:///workspaces/animedekho-bot/bot/downloader.py):
    - Sanitizes `"N/A"`, `"none"`, `"null"`, empty strings, and handles integer/float/string conversions safely.
  - Added multi-tier duration discovery: checks format duration, video stream duration, container duration tags, stream duration tags, and computes `(size * 8) / bitrate` as fallback.
  - Added secondary FFprobe probe right before Telegram video upload in [`download_and_upload`](file:///workspaces/animedekho-bot/bot/downloader.py).

---

### 4. Immediate Quality Button Feedback & Real Cancel Button (`cendl:{job_id}`)
* **Problem**: When a user tapped a quality button (e.g. `480p`, `720p`, `1080p`), server resolution across multi-source scrapers took 3–10 seconds before any message was posted or edited, making the UI feel frozen. Furthermore, there was no way to stop a download or cancel a running FFmpeg/N_m3u8DL process.
* **Fix**:
  1. In [`bot/handlers/callbacks.py`](file:///workspaces/animedekho-bot/bot/handlers/callbacks.py):
     - Cache hits are checked in 50ms and served immediately.
     - On cache miss, immediately acknowledge callback query via `await q.answer("⏳ Finding video quality...")` and send an immediate progress message: `⏳ Finding video quality... Searching fastest servers...`.
  2. Implemented `DownloadJobManager` and `DownloadJob` in [`bot/downloader.py`](file:///workspaces/animedekho-bot/bot/downloader.py):
     - Assigns a unique `job_id` per download.
     - Tracks active `asyncio.Task`, OS subprocesses (`ffmpeg`, `N_m3u8DL-RE`, `aria2c`), and temporary files on disk.
     - Progress messages render an inline `🛑 Cancel Download` button with callback `cendl:{job_id}`.
     - When clicked, `cancel_job` isolates user permission (users cannot cancel other users' jobs; admins can cancel any), kills subprocesses, cancels the asyncio task, deletes temporary files, and updates the progress message to `🛑 Download Cancelled`.

---

### 5. VidStream / Ravok (`ravok.buzz` / `as-cdn` / FirePlayer) Resolution
* **Problem**: VidStream player links on `ravok.buzz` failed to resolve stream URLs.
* **Fix**:
  - Updated [`extractors/resolver.py`](file:///workspaces/animedekho-bot/extractors/resolver.py):
    - Added `ravok.buzz` and `ravok` domains to `_resolve_fireplayer` routing.
    - Set custom `Referer` headers matching the request domain (`https://ravok.buzz/`) in `get_m3u8_qualities`.
  - Tested live on `https://ravok.buzz/video/faa9afea49ef2ff029a833cccc778fd0`:
    - Successfully resolved master playlist containing `720p` video variant:
      `https://ravok.buzz/hls2/01/01798/faa9afea49ef_h/index-v1-a1.m3u8`

---

### 6. MongoDB `$set` vs `$setOnInsert` Update Conflict
* **Problem**: Calling `db.set_channel_mapping(...)` could fail with MongoDB `WriteError: Updating the path 'series_title' would create a conflict at 'series_title'`. This occurred when `series_title`, `poster_url`, or `language` were passed in both `$set` and `$setOnInsert`.
* **Fix**:
  - In [`bot/database.py`](file:///workspaces/animedekho-bot/bot/database.py), filtered `set_on_insert`:
    ```python
    for k in list(set_on_insert.keys()):
        if k in update_set:
            set_on_insert.pop(k, None)
    ```
  - Eliminates path collisions completely while preserving atomic upsert semantics.

---

### 7. Windows Subprocess `NotImplementedError`
* **Problem**: Running on Windows raised `NotImplementedError` when spawning asyncio subprocesses with `WindowsSelectorEventLoopPolicy`.
* **Fix**:
  - In [`main.py`](file:///workspaces/animedekho-bot/main.py), switched policy to `asyncio.WindowsProactorEventLoopPolicy()`.

---

### 8. Retirement of Classic Legacy UI in Favor of Modern Formatted Cards
* **Problem**: Legacy "classic" UI lacked rich metadata, audio information, genres, and stylish layout.
* **Fix**:
  - Modern formatted card is now the sole default:
    - `get_ep_style()`, `get_start_style()`, `get_sched_style()`, `get_post_style()` in [`bot/database.py`](file:///workspaces/animedekho-bot/bot/database.py) default to `"modern"`.
    - In [`bot/downloader.py`](file:///workspaces/animedekho-bot/bot/downloader.py), `_build_episode_caption_and_markup` renders the modern card layout with emojis, genres, audio tags, and inline quality deep-links.

---

## 3. Verification & Test Results

1. **Compilation**:
   - `python3 -m compileall .` passed with **exit code 0**.
2. **Issue #20 Regression Test Suite**:
   - `PYTHONPATH=. python3 scratch/test_issue20_fixes.py` passed with **exit code 0** (all 38 items verified).
3. **Issue #22 & #23 Dedicated Test Suite (`scratch/test_issues_22_23.py`)**:
   - **`test_01_multisource_priority_and_animedubhindi`**: Verified `AnimeDubHindi` is source #0 and query sanitization functions. (PASS)
   - **`test_02_ravok_buzz_routing_in_resolver`**: Verified `ravok.buzz` routing to FirePlayer. (PASS)
   - **`test_03_search_result_accuracy_and_rejection`**: Verified scrapers reject mismatched anime titles and do not fallback to unrelated posts. (PASS)
   - **`test_04_parse_safe_float_and_duration_validation`**: Verified `_parse_safe_float` handles `"N/A"`, empty strings, and valid floats without crashing. (PASS)
   - **`test_05_download_job_manager_cancellation_and_security`**: Verified download cancellation isolation, process killing, temp file deletion, and UI cancellation updates. (PASS)
   - **`test_06_database_channel_mapping_mongodb_path_conflict`**: Verified MongoDB update document has zero key overlap between `$set` and `$setOnInsert`. (PASS)
   - **`test_07_modern_ui_sole_default`**: Verified default styles in database and verified episode caption builder renders modern formatted cards. (PASS)
   - **`test_08_windows_proactor_loop`**: Verified `main.py` uses `WindowsProactorEventLoopPolicy`. (PASS)
4. **Live Scraper End-to-End Verification**:
   - Resolved `JoJo’s Bizarre Adventure — Season 2 Episode 1` directly from `AnimeDubHindi` -> direct Cloudflare Worker link (HTTP 200, 164.7 MB, `video/x-matroska`).
