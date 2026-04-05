#!/usr/bin/env python3
"""
WoW 1.12.1 Addon Installer
Installs addons from https://github.com/fondlez/wow-addons-vanilla
Catalogue is hardcoded from the wiki; download URLs are resolved at install time
via a single GitHub API call per letter folder (avoids rate limiting on startup).
"""

import os
import sys
import re
import json
import shutil
import zipfile
import tempfile
import argparse
import urllib.request
import urllib.error
import curses  # Windows users: pip install windows-curses

try:
    import rarfile
    RAR_SUPPORT = True
except ImportError:
    RAR_SUPPORT = False

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_ADDON_DIR   = r"C:\World of Warcraft\Interface\AddOns"
REPO_OWNER          = "fondlez"
REPO_NAME           = "wow-addons-vanilla"
REPO_BRANCH         = "main"
REPO_URL            = f"https://github.com/{REPO_OWNER}/{REPO_NAME}"
RAW_BASE            = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{REPO_BRANCH}"
API_BASE            = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
CONFIG_FILE         = os.path.join(os.path.expanduser("~"), ".wow_vanilla_addon_installer")

# ──────────────────────────────────────────────────────────────────────────────
# ANSI colours
# ──────────────────────────────────────────────────────────────────────────────

BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def cprint(color, msg):
    print(f"{color}{msg}{RESET}")

# ──────────────────────────────────────────────────────────────────────────────
# Hardcoded catalogue  (name, description, letter_folder)
# Sourced from https://github.com/fondlez/wow-addons-vanilla/wiki
# ──────────────────────────────────────────────────────────────────────────────

ADDONS = [
    ("Accountant",                    "Logs your WoW incomings / outgoings",                                          "a"),
    ("Ace",                           "AddOn development and management toolkit",                                      "a"),
    ("AckisRecipeList",               "Displays a list of missing recipes for your trade skills",                      "a"),
    ("AdvancedTradeSkillWindow",      "An improved window for your tradeskills for Vanilla",                           "a"),
    ("Atlas",                         "Instance Map Browser",                                                          "a"),
    ("Auctioneer",                    "Displays item info and analyzes auction data",                                   "a"),
    ("AutoBar",                       "Configurable buttons for consumables in your pack",                             "a"),
    ("AutoInvite",                    "Automatically sends a group invite on a prescribed string",                     "a"),
    ("Automaton",                     "Reduces interface tedium by doing the little things for you",                   "a"),
    ("aux-addon",                     "Auction House replacement",                                                     "a"),
    ("Bagnon",                        "Displays the player's inventory in a single frame",                             "b"),
    ("Bartender2",                    "ActionBar AddOn which modifies the layout using Blizzard buttons",              "b"),
    ("BetterAlign",                   "A better version of Align",                                                     "b"),
    ("BetterCharacterStats",          "Displays character statistics in one place",                                    "b"),
    ("BigWigs 20022",                 "Boss Mods with Timer bars (Hosq Fondlez build)",                                "b"),
    ("BigWigs 20051",                 "Boss Mods with Timer bars (Relar build)",                                       "b"),
    ("Bongos",                        "Movable Bar Framework",                                                         "b"),
    ("BuffCheck2",                    "Monitor consumes and display icons when not active",                            "b"),
    ("BuyEmAll",                      "Enhances shift-click interface at vendors",                                     "b"),
    ("Cartographer",                  "Addon to manipulate the map",                                                   "c"),
    ("cerniesWonderfulFunctions",     "Script methods for using specific items and simpler macros",                    "c"),
    ("ChatLog",                       "Logs and displays the chat",                                                    "c"),
    ("ClassicSnowfall",               "Keydown Cast Support for Vanilla",                                              "c"),
    ("CleanMinimap",                  "Provides total control over your minimap",                                      "c"),
    ("Clique",                        "Simply powerful click-casting interface",                                       "c"),
    ("ColorPickerPlus",               "Replaces Color Picker with RGB / hex text entry, copy and paste",              "c"),
    ("CooldownCount",                 "See time until actions have cooled down in the buttons",                        "c"),
    ("CustomNameplates",              "Smaller stylized nameplates with class icons and target debuffs",               "c"),
    ("ccwatch",                       "Progress bars for CCs and DRs",                                                "c"),
    ("cdframes",                      "Cooldown timer frames",                                                         "c"),
    ("cooline",                       "Displays icons of spells and items on a single bar/line",                       "c"),
    ("CT Mod",                        "Collection: CT_AllBags, CT_BarMod, CT_BuffMod, CT_RaidAssist and more",        "c"),
    ("CT_RaidTracker",                "Counts raid loot and attendance",                                               "c"),
    ("DebuffFilter",                  "Filter target debuffs and player buffs into a separate frame",                  "d"),
    ("DebuffTimers",                  "Timer Overlays for enemy buffs and debuffs",                                    "d"),
    ("Decursive",                     "Raid cleaning mod — iterates through the raid and cures who needs it",          "d"),
    ("DevTools",                      "Debugging, Exploration, and Diagnostic Tools",                                  "d"),
    ("DisableEscape",                 "Disables escape button cancelling party invites and summons",                   "d"),
    ("EQL3",                          "Extended QuestLog with different layouts and many nice features",               "e"),
    ("ElkBuffBar",                    "Shows player's buffs and debuffs as bars",                                      "e"),
    ("enginventory",                  "AutoSorting Inventory Replacement",                                             "e"),
    ("EquipCompare",                  "Compare items easily with ones you have equipped",                              "e"),
    ("EasyCopy",                      "Clickable Timestamp to copy a message",                                         "e"),
    ("FishingBuddy",                  "Help with fishing related tasks",                                               "f"),
    ("FonzAppraiser",                 "Tracks the value of personal loot",                                             "f"),
    ("FonzSummon",                    "Chat messages during Warlock summoning",                                        "f"),
    ("FreeRefills",                   "Automatic Refilling of User Defined Items",                                     "f"),
    ("FuBar",                         "A panel that modules can plug into",                                            "f"),
    ("GearMenu",                      "Addon to manage usable gear",                                                   "g"),
    ("GrimoireKeeper",                "Tracks which grimoires your warlock pets have learned",                         "g"),
    ("HBPowerInfusion",               "Helper for Power Infusion Priests with Shadow Weaving tracking",               "h"),
    ("HealComm",                      "Visual representation of incoming heals",                                       "h"),
    ("IgniteMonitor",                 "Monitors Ignites",                                                              "i"),
    ("ignitestatus",                  "Indicators for Ignite and Scorch",                                              "i"),
    ("ImprovedErrorFrame",            "Display errors in a scrollable / selectable frame",                             "i"),
    ("Invite O' Matic",               "Makes it simple for friends to group up with you",                              "i"),
    ("JIM_CooldownPulse",             "Icons flash when spells and items become available",                            "j"),
    ("KLHPerformanceMonitor",         "Determines which frames use the most processor time or memory",                 "k"),
    ("KLHThreatMeter 17.36",          "A Threat Meter",                                                               "k"),
    ("KLHThreatMeter 17.35",          "A Threat Meter (older build)",                                                  "k"),
    ("KTMAutoHider",                  "Hides KLHThreatMeter while outside Party / Raid",                              "k"),
    ("killlog",                       "Keeps a record of your exploits fighting creeps in Azeroth",                   "k"),
    ("KillsToLevel",                  "Works out how many more kills are needed to level",                             "k"),
    ("LieExp",                        "Experience p/hour p/minute tracking tooltip and bar",                           "l"),
    ("LunaUnitFrames",                "Lightweight Unit Frames in a modern look",                                      "l"),
    ("_LazyPig",                      "UI Enhancements",                                                               "l"),
    ("MCP",                           "Addon loading control after login",                                             "m"),
    ("Mail",                          "Mailbox enhancement",                                                           "m"),
    ("MapCoords",                     "Shows cursor / player coords on worldmap and portrait",                         "m"),
    ("MikScrollingBattleText",        "Scrolls battle information around the character model",                         "m"),
    ("MissingTradeSkillsList",        "Shows missing skills and recipes for a profession",                             "m"),
    ("MobInfo2",                      "Adds mob information to the tooltip and target frame",                          "m"),
    ("ModifiedPowerAuras (Continued)","Advanced version of Power Auras, further developed by Berranzan",              "m"),
    ("ModifiedPowerAuras",            "Advanced version of the original Power Auras from Sinesther",                   "m"),
    ("MoveAnything",                  "Move any UI element — updated for patch 1.10",                                  "m"),
    ("MrPlow",                        "Regain that wasted bag space",                                                  "m"),
    ("Necronomicon",                  "Warlock soul shard management",                                                 "n"),
    ("Necrosis",                      "Graphical management of Warlock soul shards",                                   "n"),
    ("_Nameplates",                   "Makes nameplates less obtrusive with nearby unit lists",                        "n"),
    ("ntmysFixLoadingTimes",          "Improves loading-times when switching zones",                                   "n"),
    ("!OmniCC",                       "CooldownCount for Everything",                                                  "o"),
    ("Outfitter",                     "Create named gear sets and switch on the fly by hotkey or menu",                "o"),
    ("oRA2",                          "Lightweight alternative to CT_RaidAssist",                                      "o"),
    ("PallyPower",                    "Paladin aura and buff management addon",                                        "p"),
    ("PingoMatic",                    "Minimap Ping Improvements",                                                     "p"),
    ("Possessions",                   "Keeps track of all of your items across characters",                            "p"),
    ("PowerAuras",                    "Buff / Debuff visual effects around the player",                                "p"),
    ("ProfessionLevel",               "Shows minimum gathering level of profession resource nodes",                    "p"),
    ("Punschrulle",                   "Highly customizable castbar",                                                   "p"),
    ("QuestAnnouncer",                "Sends a party message as you advance in a quest",                               "q"),
    ("QuestHaste",                    "Boost your quest delivery",                                                     "q"),
    ("QuestHistory",                  "In-game history of quests accepted, completed, and abandoned",                  "q"),
    ("QuestItem",                     "In-game database over quest items and which quest they belong to",              "q"),
    ("RABuffs",                       "Monitors a raid / party group displaying various statistics",                   "r"),
    ("Radar",                         "Keeps track of hostile players around you",                                     "r"),
    ("RangeColor",                    "Change the icon color when out of range or no mana",                            "r"),
    ("Recap",                         "Displays the damage and healing of all participants in combat",                 "r"),
    ("RightClick",                    "Disables right click attacking enemies",                                        "r"),
    ("RingMenu",                      "Circular action bar summoned by a mouse button click",                          "r"),
    ("Roid-Macros",                   "Vanilla macros on steroids",                                                    "r"),
    ("sentry",                        "Shows frames for nearby enemy players",                                         "s"),
    ("ShaguChat",                     "Hides and highlights chat messages with specific keywords",                     "s"),
    ("ShaguInventory",                "Shows item counts across all characters on the same account",                   "s"),
    ("ShaguValue",                    "Show item sell and buy values",                                                  "s"),
    ("SimpleActionSets",              "Save and switch action bar sets",                                               "s"),
    ("SimpleAutoDelete",              "Lightweight addon to automatically delete unwanted items",                      "s"),
    ("SmartLoot",                     "Unobtrusive group loot frames addon",                                           "s"),
    ("SmartRes",                      "Smart Ressing",                                                                 "s"),
    ("SoulShardManager",              "Keeps your Soul Shards in check",                                               "s"),
    ("SpecialTalent",                 "Improved talent frame",                                                         "s"),
    ("SummonsMonitor",                "Helps warlocks coordinate summons of multiple people",                          "s"),
    ("SUCC-ecb",                      "Enemy castbar addon",                                                           "s"),
    ("SuperMacro",                    "Unlimited macros up to 7000 letters with keybinding support",                   "s"),
    ("Talentsaver",                   "Save and Load your Talents easily",                                             "t"),
    ("TheoryCraft",                   "Tells you everything about an ability on the tooltip",                          "t"),
    ("TimeManager",                   "Alarm clock, stopwatch, and local time display from patch 2.4.3+",              "t"),
    ("TipBuddy",                      "Enhanced, configurable unit tooltip",                                           "t"),
    ("VCB",                           "Vanilla Consolidate Buff-Frames — smart aura management system",                "v"),
    ("WIM",                           "Give whispers an instant messenger feel",                                       "w"),
    ("Zorlen",                        "Functions to reduce macro sizes and avoid character limits",                    "z"),
    ("zBar",                          "Action Bar Enhancement",                                                        "z"),
]

# ──────────────────────────────────────────────────────────────────────────────
# Banner
# ──────────────────────────────────────────────────────────────────────────────

def print_banner():
    print()
    cprint(BOLD + CYAN, "  \u2554" + "\u2550"*58 + "\u2557")
    cprint(BOLD + CYAN, "  \u2551   WoW 1.12.1 Addon Installer                          \u2551")
    cprint(BOLD + CYAN, "  \u2551   Addons from github.com/fondlez/wow-addons-vanilla   \u2551")
    cprint(BOLD + CYAN, "  \u255a" + "\u2550"*58 + "\u255d")
    print()

# ──────────────────────────────────────────────────────────────────────────────
# Resolve download URL at install time
# ──────────────────────────────────────────────────────────────────────────────

# Cache letter folder listings so we only call the API once per letter per run
_folder_cache = {}
_folder_error  = {}

import ssl as _ssl

def _nossl_context():
    """Return an SSL context that skips certificate verification."""
    ctx = _ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = _ssl.CERT_NONE
    return ctx


def _fetch_folder_listing(letter):
    """
    Fetch the file listing for addons/{letter}/ using the GitHub API.
    Falls back to scraping the GitHub HTML page if the API is rate-limited.
    Results are cached. Returns a list of filename strings.
    SSL certificate verification is disabled to avoid issues on Windows.
    """
    global _folder_cache, _folder_error

    if letter in _folder_cache:
        return _folder_cache[letter]

    filenames = []
    ctx = _nossl_context()

    # ── Strategy 1: GitHub contents API ──────────────────────────────────────
    api_url = f"{API_BASE}/contents/addons/{letter}"
    token   = os.environ.get("GITHUB_TOKEN", "")
    headers = {"User-Agent": "WoW-Addon-Installer/1.0",
               "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            data = json.loads(r.read())
        filenames = [f["name"] for f in data
                     if f.get("type") == "file"
                     and (f["name"].endswith(".zip") or f["name"].endswith(".rar"))]
        _folder_cache[letter] = filenames
        return filenames
    except urllib.error.HTTPError as e:
        _folder_error[letter] = f"API HTTP {e.code}"
    except Exception as e:
        _folder_error[letter] = str(e)

    # ── Strategy 2: Scrape the GitHub HTML folder page ───────────────────────
    html_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/tree/{REPO_BRANCH}/addons/{letter}"
    try:
        req2 = urllib.request.Request(html_url,
                                      headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req2, timeout=10, context=ctx) as r:
            html = r.read().decode("utf-8", errors="replace")
        pattern = rf'/blob/{REPO_BRANCH}/addons/{letter}/([^"]+\.(?:zip|rar))'
        found = re.findall(pattern, html, re.IGNORECASE)
        filenames = [urllib.parse.unquote(f) for f in found]
        if filenames:
            _folder_cache[letter] = filenames
            return filenames
    except Exception:
        pass

    _folder_cache[letter] = []
    return []


def resolve_download_url(addon_name, letter):
    """
    Find the actual .zip/.rar filename for an addon in addons/{letter}/
    and return the raw download URL, or None if not found.
    """
    files = _fetch_folder_listing(letter)

    if not files:
        err = _folder_error.get(letter, "unknown error")
        print(f"  {DIM}(Could not list addons/{letter}/ — {err}){RESET}")
        return None

    # Strip non-alphanumeric chars for fuzzy matching
    search = re.sub(r'[^a-z0-9]', '', addon_name.lower())

    # 1. Exact prefix match (most reliable)
    for fname in files:
        fname_clean = re.sub(r'[^a-z0-9]', '', fname.lower())
        if fname_clean.startswith(search):
            return f"{RAW_BASE}/addons/{letter}/{urllib.parse.quote(fname)}"

    # 2. Substring match
    for fname in files:
        fname_clean = re.sub(r'[^a-z0-9]', '', fname.lower())
        if search in fname_clean:
            return f"{RAW_BASE}/addons/{letter}/{urllib.parse.quote(fname)}"

    return None


# ──────────────────────────────────────────────────────────────────────────────
# Directory persistence
# ──────────────────────────────────────────────────────────────────────────────

def load_saved_dir():
    try:
        with open(CONFIG_FILE) as f:
            path = f.read().strip()
            return path if path else None
    except FileNotFoundError:
        return None


def save_dir(path):
    try:
        with open(CONFIG_FILE, "w") as f:
            f.write(path)
    except OSError:
        pass


def pick_folder_dialog(title="Select your WoW AddOns folder", initial=None):
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        chosen = filedialog.askdirectory(
            title=title,
            initialdir=initial or os.path.expanduser("~"),
        )
        root.destroy()
        return chosen if chosen else None
    except Exception:
        return None


def resolve_dir(args_dir):
    if args_dir:
        save_dir(args_dir)
        return args_dir
    saved = load_saved_dir()
    if saved and os.path.isdir(saved):
        return saved
    print()
    cprint(BOLD + CYAN, "  Welcome! Please select your WoW AddOns folder.")
    print()
    chosen = pick_folder_dialog("Select your WoW Interface\\AddOns folder")
    if chosen:
        cprint(GREEN, f"  \u2714 AddOns folder set to:\n    {chosen}")
        save_dir(chosen)
        return chosen
    cprint(YELLOW, "  (Folder picker unavailable \u2014 please type the path instead)")
    raw = input(
        f"\n  {BOLD}AddOns folder path{RESET} {DIM}(Enter = {DEFAULT_ADDON_DIR}){RESET}\n"
        f"  {BOLD}> {RESET}"
    ).strip().strip('"').strip("'")
    path = raw if raw else DEFAULT_ADDON_DIR
    save_dir(path)
    return path

# ──────────────────────────────────────────────────────────────────────────────
# Download
# ──────────────────────────────────────────────────────────────────────────────

import urllib.parse

def download_file(url, dest_path):
    headers = {"User-Agent": "WoW-Addon-Installer/1.0"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=_nossl_context()) as response, open(dest_path, "wb") as f:
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        while True:
            data = response.read(65536)
            if not data:
                break
            f.write(data)
            downloaded += len(data)
            if total:
                pct = min(100, downloaded * 100 // total)
                bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
                print(f"\r  [{bar}] {pct:3d}%", end="", flush=True)
    print()

# ──────────────────────────────────────────────────────────────────────────────
# Extraction
# ──────────────────────────────────────────────────────────────────────────────

def is_github_wrapper(name):
    return bool(re.search(r'[-_](main|master|\d+(?:\.\d+)*)$', name, re.IGNORECASE))


def has_lua_or_toc(files):
    return any(f.endswith((".lua", ".toc")) for f in files)


def extract_archive(archive_path, addon_name, addons_dir):
    ext = os.path.splitext(archive_path)[1].lower()
    if ext == ".zip":
        with zipfile.ZipFile(archive_path, "r") as zf:
            members = zf.namelist()
            top_dirs  = {m.split("/")[0] for m in members if "/" in m and m.split("/")[0]}
            top_files = [m for m in members if "/" not in m.rstrip("/") and m.strip("/")]
            with tempfile.TemporaryDirectory() as tmp:
                zf.extractall(tmp)
                src = tmp
                github_wrapped = (len(top_dirs) == 1 and not top_files
                                  and is_github_wrapper(list(top_dirs)[0]))
                if github_wrapped:
                    src = os.path.join(tmp, list(top_dirs)[0])
                for _ in range(5):
                    inner = os.listdir(src)
                    inner_dirs  = [i for i in inner if os.path.isdir(os.path.join(src, i))]
                    inner_files = [i for i in inner if os.path.isfile(os.path.join(src, i))]
                    if len(inner_dirs) == 1 and not has_lua_or_toc(inner_files):
                        only_path = os.path.join(src, inner_dirs[0])
                        sub = os.listdir(only_path)
                        sub_dirs  = [s for s in sub if os.path.isdir(os.path.join(only_path, s))]
                        sub_files = [s for s in sub if os.path.isfile(os.path.join(only_path, s))]
                        if len(sub_dirs) > 1 or has_lua_or_toc(sub_files):
                            break
                        src = only_path
                    else:
                        break
                inner_items = os.listdir(src)
                inner_dirs  = [i for i in inner_items if os.path.isdir(os.path.join(src, i))]
                inner_files = [i for i in inner_items if os.path.isfile(os.path.join(src, i))]
                if not inner_dirs or has_lua_or_toc(inner_files):
                    dest = os.path.join(addons_dir, addon_name)
                    if os.path.exists(dest): shutil.rmtree(dest)
                    shutil.copytree(src, dest)
                elif len(inner_dirs) == 1:
                    only_path = os.path.join(src, inner_dirs[0])
                    sub_dirs  = [i for i in os.listdir(only_path)
                                 if os.path.isdir(os.path.join(only_path, i))]
                    sub_files = [i for i in os.listdir(only_path)
                                 if os.path.isfile(os.path.join(only_path, i))]
                    if len(sub_dirs) > 1 and not has_lua_or_toc(sub_files):
                        for item in sub_dirs:
                            clean = re.sub(r'[-_](main|master|\d+(?:\.\d+)*)$', '',
                                          item, flags=re.IGNORECASE)
                            s = os.path.join(only_path, item)
                            d = os.path.join(addons_dir, clean)
                            if os.path.exists(d): shutil.rmtree(d) if os.path.isdir(d) else os.remove(d)
                            shutil.move(s, d)
                    else:
                        s = only_path
                        d = os.path.join(addons_dir, addon_name)
                        if os.path.exists(d): shutil.rmtree(d) if os.path.isdir(d) else os.remove(d)
                        shutil.move(s, d)
                else:
                    for item in inner_dirs:
                        clean = re.sub(r'[-_](main|master|\d+(?:\.\d+)*)$', '',
                                      item, flags=re.IGNORECASE)
                        s = os.path.join(src, item)
                        d = os.path.join(addons_dir, clean)
                        if os.path.exists(d): shutil.rmtree(d) if os.path.isdir(d) else os.remove(d)
                        shutil.move(s, d)
    elif ext == ".rar":
        if not RAR_SUPPORT:
            raise RuntimeError("RAR support not available. Run: pip install rarfile")
        with rarfile.RarFile(archive_path) as rf:
            rf.extractall(addons_dir)
    else:
        raise ValueError(f"Unsupported archive format: {ext}")

# ──────────────────────────────────────────────────────────────────────────────
# Install
# ──────────────────────────────────────────────────────────────────────────────

def install_addons(addons, install_dir):
    os.makedirs(install_dir, exist_ok=True)
    total = len(addons)
    ok, failed = [], []

    for i, (name, desc, letter) in enumerate(addons, 1):
        cprint(BOLD, f"\n[{i}/{total}] {name}")
        if desc:
            print(f"  {DIM}{desc}{RESET}")

        print(f"  {DIM}Resolving download URL…{RESET}", end="\r", flush=True)
        url = resolve_download_url(name, letter)
        if not url:
            cprint(RED, f"  \u2718 Could not find download file for {name} in addons/{letter}/")
            failed.append((name, "file not found in repo"))
            continue

        ext = ".rar" if url.endswith(".rar") else ".zip"
        tmp_file = os.path.join(tempfile.gettempdir(), f"wow_vanilla_{re.sub(r'[^a-z0-9]', '_', name.lower())}{ext}")

        try:
            print(f"  Downloading from: {DIM}{url}{RESET}")
            download_file(url, tmp_file)
            print(f"  Extracting to {install_dir}…")
            extract_archive(tmp_file, name, install_dir)
            cprint(GREEN, f"  \u2714 {name} installed successfully.")
            ok.append(name)
        except Exception as e:
            cprint(RED, f"  \u2718 Failed: {e}")
            failed.append((name, str(e)))
        finally:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)

    print()
    cprint(BOLD + CYAN, "\u2550" * 60)
    cprint(BOLD, "Installation summary")
    cprint(BOLD + CYAN, "\u2550" * 60)
    cprint(GREEN, f"  \u2714 Installed ({len(ok)}): {', '.join(ok) if ok else '\u2014'}")
    if failed:
        cprint(RED, f"  \u2718 Failed    ({len(failed)}):")
        for name, reason in failed:
            cprint(RED, f"      \u2022 {name}: {reason}")
    print()

# ──────────────────────────────────────────────────────────────────────────────
# Curses picker
# ──────────────────────────────────────────────────────────────────────────────

def _curses_picker(stdscr, addons):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN,   -1)
    curses.init_pair(2, curses.COLOR_GREEN,  -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_WHITE,  -1)
    curses.init_pair(5, curses.COLOR_RED,    -1)

    checked   = set()
    cursor    = 0
    scroll    = 0
    query     = ""
    searching = False

    def filtered():
        if not query:
            return list(enumerate(addons))
        q = query.lower()
        return [(i, a) for i, a in enumerate(addons)
                if q in a[0].lower() or q in a[1].lower()]

    while True:
        rows, cols = stdscr.getmaxyx()
        list_rows = rows - 5
        visible = filtered()
        if cursor >= len(visible): cursor = max(0, len(visible) - 1)
        if cursor < scroll:        scroll = cursor
        if cursor >= scroll + list_rows: scroll = cursor - list_rows + 1

        stdscr.erase()
        hdr = " WoW 1.12.1 Addon Installer  \u2502  Space=tick  A=all  /=search  Enter=install  Q=quit"
        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(0, 0, hdr[:cols-1].ljust(cols-1))
        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
        n = len(checked)
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(1, 0, f" {n} addon{'s' if n != 1 else ''} selected of {len(addons)}"[:cols-1])
        stdscr.attroff(curses.color_pair(1))
        stdscr.attron(curses.color_pair(4) | curses.A_DIM)
        stdscr.addstr(2, 0, "\u2500" * (cols-1))
        stdscr.attroff(curses.color_pair(4) | curses.A_DIM)

        for row_i, (orig_idx, (name, desc, _)) in enumerate(visible[scroll:scroll+list_rows]):
            y = 3 + row_i
            is_cursor  = (row_i + scroll == cursor)
            is_checked = orig_idx in checked
            tick = "[x]" if is_checked else "[ ]"
            line = f" {tick} {name:<28}  {desc}"
            line = line[:cols-1].ljust(cols-1)
            if is_cursor:
                attr = curses.color_pair(3) | curses.A_BOLD | curses.A_REVERSE
            elif is_checked:
                attr = curses.color_pair(2) | curses.A_BOLD
            else:
                attr = curses.color_pair(4)
            stdscr.attron(attr)
            stdscr.addstr(y, 0, line)
            stdscr.attroff(attr)

        search_y = rows - 2
        stdscr.attron(curses.color_pair(4) | curses.A_DIM)
        stdscr.addstr(search_y - 1, 0, "\u2500" * (cols-1))
        stdscr.attroff(curses.color_pair(4) | curses.A_DIM)
        if searching or query:
            bar = f" Search: {query}_"
            stdscr.attron(curses.color_pair(5) | curses.A_BOLD)
        else:
            bar = " Press / to search"
            stdscr.attron(curses.color_pair(4) | curses.A_DIM)
        stdscr.addstr(search_y, 0, bar[:cols-1].ljust(cols-1))
        stdscr.attroff(curses.color_pair(5) | curses.A_BOLD)
        stdscr.attroff(curses.color_pair(4) | curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if searching:
            if key in (curses.KEY_ENTER, 10, 13):   searching = False
            elif key == 27:                          query = ""; searching = False; cursor = scroll = 0
            elif key in (curses.KEY_BACKSPACE, 127, 8): query = query[:-1]; cursor = scroll = 0
            elif 32 <= key <= 126:                   query += chr(key); cursor = scroll = 0
            continue
        if   key == curses.KEY_UP:    cursor = max(0, cursor - 1)
        elif key == curses.KEY_DOWN:  cursor = min(len(visible)-1, cursor + 1)
        elif key == curses.KEY_PPAGE: cursor = max(0, cursor - list_rows)
        elif key == curses.KEY_NPAGE: cursor = min(len(visible)-1, cursor + list_rows)
        elif key == curses.KEY_HOME:  cursor = 0
        elif key == curses.KEY_END:   cursor = max(0, len(visible)-1)
        elif key == ord(" "):
            if visible:
                orig_idx = visible[cursor][0]
                checked.discard(orig_idx) if orig_idx in checked else checked.add(orig_idx)
                cursor = min(len(visible)-1, cursor+1)
        elif key in (ord("a"), ord("A")):
            checked = set() if len(checked) == len(addons) else set(range(len(addons)))
        elif key == ord("/"):    searching = True
        elif key == 27:          query = ""; cursor = scroll = 0
        elif key in (curses.KEY_ENTER, 10, 13):
            return [addons[i] for i in sorted(checked)]
        elif key in (ord("q"), ord("Q")):
            return []


def prompt_selection():
    try:
        return curses.wrapper(_curses_picker, ADDONS)
    except Exception as e:
        cprint(RED, f"Could not start interactive picker: {e}")
        cprint(YELLOW, "Tip: on Windows run  pip install windows-curses  then retry.")
        sys.exit(1)

# ──────────────────────────────────────────────────────────────────────────────
# Update checking
# ──────────────────────────────────────────────────────────────────────────────

def normalise_name(s):
    return s.lower().replace("-", "_").replace(" ", "_").lstrip("_!")


def scan_installed(addons_dir):
    if not os.path.isdir(addons_dir):
        return []
    installed = {normalise_name(f) for f in os.listdir(addons_dir)
                 if os.path.isdir(os.path.join(addons_dir, f))}
    return [a for a in ADDONS if normalise_name(a[0]) in installed]


def local_install_time(addon_name, addons_dir):
    import datetime
    folder = os.path.join(addons_dir, addon_name)
    if not os.path.isdir(folder):
        return None
    latest = 0.0
    for root, _, files in os.walk(folder):
        for f in files:
            try:
                t = os.path.getmtime(os.path.join(root, f))
                if t > latest: latest = t
            except OSError:
                pass
    if latest == 0.0:
        try: latest = os.path.getmtime(folder)
        except OSError: return None
    return datetime.datetime.utcfromtimestamp(latest)


def github_last_commit_for_repo():
    """Return the latest commit date for the whole repo (single API call)."""
    import datetime
    url = f"{API_BASE}/commits?sha={REPO_BRANCH}&per_page=1"
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"User-Agent": "WoW-Addon-Installer/1.0",
               "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        if isinstance(data, list) and data:
            date_str = data[0]["commit"]["committer"]["date"].rstrip("Z")
            return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None


def run_update(addons_dir):
    import datetime
    cprint(BOLD + CYAN, f"\n  Scanning for installed addons in:\n  {addons_dir}\n")
    installed = scan_installed(addons_dir)
    if not installed:
        cprint(YELLOW, "  No recognised addons found in that folder.")
        return

    cprint(BOLD, f"  Found {len(installed)} installed addon(s). Checking for updates…\n")

    # Use one repo-level commit date as the "latest available" for all addons
    remote_dt = github_last_commit_for_repo()

    updates_available, up_to_date, unknown = [], [], []
    for addon in installed:
        local_dt = local_install_time(addon[0], addons_dir)
        if remote_dt is None:
            unknown.append(addon)
        elif local_dt is None or remote_dt > local_dt:
            updates_available.append((addon, local_dt, remote_dt))
        else:
            up_to_date.append((addon, local_dt))

    def fmt_dt(dt):
        return dt.strftime("%Y-%m-%d") if dt else "unknown"

    if updates_available:
        cprint(BOLD + YELLOW, f"  \u2b06  {len(updates_available)} addon(s) may have updates:\n")
        for addon, local_dt, remote_dt in updates_available:
            print(f"    {YELLOW}\u2022{RESET} {BOLD}{addon[0]:<28}{RESET} "
                  f"{DIM}installed {fmt_dt(local_dt)}  \u2192  repo updated {fmt_dt(remote_dt)}{RESET}")
    else:
        cprint(GREEN, "  \u2714  All addons appear up to date!")

    if up_to_date:
        print()
        cprint(GREEN, f"  \u2714  {len(up_to_date)} appear up to date")

    if unknown:
        print()
        cprint(DIM, f"  ?  {len(unknown)} could not be checked")

    if not updates_available:
        print()
        return

    print()
    print(f"    {BOLD}1.{RESET}  Update all {len(updates_available)} addon(s)")
    print(f"    {BOLD}2.{RESET}  Choose which to update")
    print(f"    {BOLD}3.{RESET}  Cancel")
    print()

    while True:
        sub = input(f"  {BOLD}Enter 1, 2 or 3: {RESET}").strip()
        if sub in ("1", "2", "3"):
            break

    if sub == "3":
        cprint(YELLOW, "  Cancelled.")
        return

    to_install = ([a[0] for a in updates_available] if sub == "1"
                  else curses.wrapper(_curses_picker, [a[0] for a in updates_available]))

    if not to_install:
        cprint(YELLOW, "  Nothing selected.")
        return
    print()
    install_addons(to_install, addons_dir)

# ──────────────────────────────────────────────────────────────────────────────
# Main menu
# ──────────────────────────────────────────────────────────────────────────────

def main_menu(install_dir):
    print()
    cprint(BOLD + CYAN, "  \u2554" + "\u2550"*58 + "\u2557")
    cprint(BOLD + CYAN, "  \u2551   What would you like to do?                          \u2551")
    cprint(BOLD + CYAN, "  \u255a" + "\u2550"*58 + "\u255d")
    print()
    print(f"    {BOLD}1.{RESET}  Install addons")
    print(f"    {BOLD}2.{RESET}  Update installed addons")
    print(f"    {BOLD}3.{RESET}  Change AddOns folder")
    print()
    cprint(DIM, f"  AddOns folder: {install_dir}")
    print()
    while True:
        choice = input(f"  {BOLD}Enter 1, 2 or 3: {RESET}").strip()
        if choice in ("1", "2", "3"):
            return choice
        cprint(YELLOW, "  Please enter 1, 2 or 3.")

# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Install WoW 1.12.1 addons from fondlez/wow-addons-vanilla.")
    parser.add_argument("--dir", "-d", metavar="ADDON_DIR",
                        help="Path to your WoW Interface/AddOns folder.")
    args = parser.parse_args()

    print_banner()
    install_dir = resolve_dir(args.dir)

    while True:
        choice = main_menu(install_dir)

        if choice == "1":
            selected = prompt_selection()
            if not selected:
                cprint(YELLOW, "\n  No addons selected.")
            else:
                print()
                cprint(BOLD, f"  About to install {len(selected)} addon(s) into:")
                cprint(CYAN, f"  {install_dir}\n")
                for name, _, _ in selected:
                    print(f"    \u2022 {name}")
                print()
                confirm = input(f"  {BOLD}Proceed? [Y/n]: {RESET}").strip().lower()
                if confirm in ("", "y", "yes"):
                    install_addons(selected, install_dir)

        elif choice == "2":
            run_update(install_dir)

        elif choice == "3":
            chosen = pick_folder_dialog("Select your WoW Interface\\AddOns folder",
                                        initial=install_dir)
            if chosen:
                install_dir = chosen
                save_dir(install_dir)
                cprint(GREEN, f"\n  \u2714 AddOns folder updated to:\n    {install_dir}")
            else:
                raw = input(
                    f"\n  {BOLD}New AddOns folder path{RESET} "
                    f"{DIM}(Enter = keep current){RESET}\n"
                    f"  {BOLD}> {RESET}"
                ).strip().strip('"').strip("'")
                if raw:
                    install_dir = raw
                    save_dir(install_dir)

        print()
        again = input(f"  {BOLD}Return to main menu? [Y/n]: {RESET}").strip().lower()
        if again not in ("", "y", "yes"):
            cprint(CYAN, "\n  Goodbye!\n")
            break


if __name__ == "__main__":
    main()
