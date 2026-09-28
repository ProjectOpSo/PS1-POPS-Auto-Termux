# PS1-POPS-Auto-Termux

An automated toolset designed to fully convert PlayStation 1 games (`.BIN`/`.CUE`) into the POPStarter format (`.VCD`) natively inside **Termux on Android**. It handles multi-track merging, Game ID parsing, cover art scraping, and deployment structural layouts out-of-the-box.

---

## Architecture & Directory Layout

### 1. Repository Structure
The local repository folder contains the orchestration automation scripts and underlying upstream tools compiled/optimized for Termux:

```text
PS1-POPS-Auto-Termux/
├── binmerge/              # Python multi-track BIN merger engine
├── cue2pops-android/      # Portable C implementation of cue2pops compiled for Termux
├── POPS-binaries/         # Essential POPStarter deployment binaries and system BIOS files
├── cheats.py              # Cheat management and patching utility
└── ps1popsauto.py         # Main automation orchestration engine
```

### 2. Working Directory Structure (`/sdcard/Download/POPS2`)
The application automatically targets a standardized directory footprint inside your device storage. The table below explains the precise purpose of each workflow subfolder:

| Directory | Type | Description |
| :--- | :--- | :--- |
| `JPS1/` | **Input** | The source directory. **Must contain individual folders per game** (Loose files will be skipped). |
| `MPS1/` | **Temporary** | Workspace where `binmerge` combines multi-track `.BIN` tracks into unified single `.BIN` profiles. |
| `VPS1/` | **Temporary** | The immediate build destination for transformed `.VCD` formats before staging. |
| `RPS1/` | **Staging** | Staging ground used to index and standardize naming conventions for final transfer. |
| `PS1M/` | **Template** | Houses the baseline Virtual Memory Card (`.VMC`) template file duplicated to every game asset. |
| `.POPSTARTER/` | **Output** | The final portable production folder containing structured subdirectories (`POPS/`, `APPS/`, `ART/`) ready to export. |

---

## How It Works (Pipeline Workflow)

When you execute `ps1popsauto.py`, the core orchestration engine executes a multi-layered internal pipeline without requiring manual intervention:

```text
[Storage Detection] ──> [Structure Validation] ──> [Game ID Extraction] ──> [Art Download & Optimization]
                                                                                        │
[POPStarter Packaging] <── [VCD Conversion] <── [Multi-Track Merging] <─────────────────┘
```

1. **Dynamic Storage Detection:** Automatically mounts and detects your target root `/sdcard/` footprint or absolute internal Android environment storage path safely.
2. **Structure Validation:** Assesses structural configurations across `JPS1/` to ensure games conform to structural formatting rules.
3. **Game ID Parsing:** Scans and extracts official Game Serial/IDs directly out of raw `.BIN` data header layers natively.
4. **Art Scraping & Optimization:** Downloads matching background assets from upstream databases, parsing it through an `FFmpeg` pipeline to scale, convert, and output optimized `200x200 8-bit PNG` formatting required for OPL/POPStarter.
5. **Multi-Track Merging:** Passes multi-track image dumps directly into `binmerge` to cleanly unify splits into structured single files.
6. **VCD Conversion:** Compiles structural code payloads into raw binary streams via `rcue2pops.py`.
7. **Production Packaging:** Constructs ready-to-run file structures mapping output assets cleanly inside dedicated target folders (`.POPSTARTER/POPS`, `.POPSTARTER/APPS` with tracking metadata arrays like `title.cfg`, and `.POPSTARTER/ART`).

---

## Step-by-Step Tutorial

### 1. Prerequisites
Before invoking dependencies or operational configurations, you must provide Termux explicit filesystem authorizations to view Android storage parameters:

```bash
termux-setup-storage
```

### 2. Automated Installation
Execute this single-line installation string inside Termux to resolve application package links, clean broken builds, fetch remote source structures, and automate execution tracking properties:

```bash
cd "$HOME" && dpkg --configure -a && apt --fix-broken install -y && pkg update -y && pkg upgrade -y && pkg install -y git make clang python ffmpeg && rm -rf PS1-POPS-Auto-Termux && git clone https://github.com/ProjectOpSo/PS1-POPS-Auto-Termux.git && cd PS1-POPS-Auto-Termux && git clone https://github.com/ProjectOpSo/rcue2pops-android.git cue2pops-android && git clone https://github.com/ProjectOpSo/binmerge.git && git clone https://github.com/AnimMouse/POPS-binaries.git && cd cue2pops-android && cd .. && chmod +x ps1popsauto.py cheats.py
```

### 3. ROM Preparation Guide
For the scanner engine to properly parse your games, compliance with the structure rules inside `/sdcard/Download/POPS2/JPS1/` is **strictly required**:

* ❌ **Incorrect Layout:** Placing loose files directly into the directory root.
  ```text
  JPS1/
  ├── Game1.bin
  └── Game1.cue
  ```
*  **Correct Layout:** Every game title must reside cleanly isolated in its own unique subfolder wrapper.
  ```text
  JPS1/
  ├── Crash Bandicoot/
  │   ├── Crash.bin
  │   └── Crash.cue
  └── Spyro The Dragon/
      ├── Spyro.bin
      └── Spyro.cue
  ```

### 4. Usage Command Execution

#### Main Conversion Engine (`ps1popsauto.py`)
Run the core configuration manager interface directly:

```bash
./ps1popsauto.py
```
*Follow the interactive prompt instructions within the shell environment to select your desired deployment target:*
* **USB Mode:** Formats final structural file wrappers prepending `XX.` to output execution `.ELF` targets.
* **SMB / Network Mode:** Formats structural wrapper deployments prepending `SB.` to output execution `.ELF` targets.

#### Game Cheating Sub-System (`cheats.py`)
To configure, maintain, or selectively attach functional patch adjustments onto targeted system configurations, deploy the ancillary script system via:

```bash
./cheats.py
```

---

## Credits

Special thanks to the authors and projects whose core components power this automation pipeline:

* **ProjectOpSo** — [cue2pops-android](https://github.com/ProjectOpSo/cue2pops-android) (Portable C implementation of `cue2pops`).
* **ProjectOpSo** — [binmerge](https://github.com/ProjectOpSo/binmerge) (Multi-track PlayStation structural disk merger engine).
* **AnimMouse** — [POPS-binaries](https://github.com/AnimMouse/POPS-binaries) (Essential POPStarter compiled binaries and supporting files).
* **xlenore** — [psx-covers](https://github.com/xlenore/psx-covers) (Comprehensive high-density cover art directory).
