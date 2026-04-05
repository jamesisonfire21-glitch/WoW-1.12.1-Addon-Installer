# WoW 1.12.1 Addon Installer

A command-line tool for installing and updating World of Warcraft 1.12.1 (Vanilla) addons. Pulls from [fondlez's wow-addons-vanilla](https://github.com/fondlez/wow-addons-vanilla) repository by default, with a catalogue of 121 addons sourced directly from the project wiki.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support%20development-yellow?style=for-the-badge&logo=buy-me-a-coffee)](https://buymeacoffee.com/jamesisonfire)

---

## Features

- **Native folder picker** — on first launch a folder browser dialog opens so you can select your AddOns directory without typing a path; the choice is saved for future runs
- **Interactive curses UI** — navigate with arrow keys, tick addons with Space, search with `/`
- **121 addons** catalogued from the fondlez wiki, with names and descriptions
- **Smart download resolution** — filenames in the repo include author tags and dates; the tool resolves the correct file automatically at install time
- **Update checking** — compares local install dates against the latest repo commit and shows what may need updating
- **Smart extraction** — handles all GitHub zip layouts correctly and strips `-main`/`-master` suffixes from folder names
- **Stays open** — after installing or updating, returns to the main menu rather than closing

---

## Requirements

- Python 3.8+
- Windows, macOS, or Linux

### Installing Python

**Windows:**
1. Go to [python.org/downloads](https://www.python.org/downloads/) and download the latest Python 3 installer
2. Run the installer — **make sure to tick "Add Python to PATH"** before clicking Install
3. Open a Command Prompt and run `python --version` to confirm it worked

**macOS:**
1. Go to [python.org/downloads](https://www.python.org/downloads/) and download the latest Python 3 installer, or install via Homebrew: `brew install python`
2. Run `python3 --version` in Terminal to confirm

**Linux:**
```
sudo apt install python3 python3-pip   # Debian/Ubuntu
sudo dnf install python3               # Fedora
```

### Windows — install curses support

After installing Python, open a Command Prompt and run:

```
pip install windows-curses
```

---

## Installation

Download `wow_vanilla_addon_installer.py` and run it directly — no other files needed.

```
python wow_vanilla_addon_installer.py
```

**First run:** a native folder picker dialog opens automatically so you can browse to your `Interface\AddOns` folder. The path is saved to `~/.wow_vanilla_addon_installer` and reused on every subsequent launch.

---

## Usage

### Interactive mode

```
python wow_vanilla_addon_installer.py
```

On launch you'll see the main menu:

```
  1.  Install addons
  2.  Update installed addons
  3.  Change AddOns folder
```

**Option 1 — Install:**
- Opens the full-screen picker to browse and tick addons
- Resolves the correct download file from the repo at install time
- Shows a summary when done

**Option 2 — Update:**
- Scans your AddOns folder for installed catalogue addons
- Compares local install dates against the latest repo commit
- Lets you update all, pick specific ones, or cancel

**Option 3 — Change AddOns folder:**
- Opens the folder picker dialog to select a different directory
- Saves the new path for future runs

### Picker controls

| Key | Action |
|-----|--------|
| `↑` / `↓` | Move up / down |
| `Page Up` / `Page Down` | Jump a whole page |
| `Space` | Tick / untick the highlighted addon |
| `A` | Select all / deselect all |
| `/` | Search by name or description |
| `Esc` | Clear search |
| `Enter` | Confirm and install |
| `Q` | Quit without selecting |

---

## Addon catalogue

121 addons across all categories, including:

| Category | Examples |
|----------|---------|
| **Raid & Boss Mods** | BigWigs, CT_RaidAssist, oRA2, KLHThreatMeter, RABuffs |
| **UI & Bars** | Bartender2, Bongos, FuBar, CT Mod, MoveAnything, SuperMacro |
| **Unit Frames** | LunaUnitFrames, HealComm, DebuffFilter, TipBuddy |
| **Bags & Inventory** | Bagnon, Possessions, ShaguInventory, MrPlow, enginventory |
| **Questing** | EQL3, QuestAnnouncer, QuestItem, QuestHistory, QuestHaste |
| **Auction House** | Auctioneer, aux-addon |
| **Class Tools** | PallyPower, Necrosis, SoulShardManager, HBPowerInfusion, IgniteMonitor |
| **Combat & Cooldowns** | !OmniCC, CooldownCount, Recap, Decursive, ccwatch |
| **Maps & Social** | Cartographer, MapCoords, WIM, Radar, ShaguChat |
| **Misc** | MCP, Outfitter, GearMenu, Automaton, FishingBuddy, Clique |

---

## How extraction works

The tool handles every zip layout it encounters from GitHub:

| Layout | Result |
|--------|--------|
| Plain zip with one folder | `AddOns\AddonName\` |
| GitHub wrapper (`addon-master/`) | Wrapper stripped, folder renamed cleanly |
| Loose files at root | Wrapped in `AddOns\AddonName\` |

Folder names are always cleaned — suffixes like `-main`, `-master`, and version numbers are stripped automatically.

---

## Credits

Addon repository maintained by [fondlez](https://github.com/fondlez/wow-addons-vanilla).

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

## Support

If this tool saves you some time, a coffee is always appreciated!

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/jamesisonfire)
