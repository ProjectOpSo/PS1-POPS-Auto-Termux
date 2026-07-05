# PS1-POPS-Auto-Termux

An automated toolkit for converting PlayStation 1 games into the POPStarter format directly from Termux on Android.

The `ps1popsauto.sh` script automates the entire conversion process, including multi-track merging, VCD creation, filename sanitization, and POPStarter folder generation.

---

## Project Structure

```text
PS1-POPS-Auto-Termux/
├── cue2pops-linux/      # cue2pops source compiled for Termux
├── binmerge/            # Multi-track BIN merger
├── POPS-binaries/       # POPStarter binaries and BIOS files
└── ps1popsauto.sh       # Main automation script
```

---

## Android Storage

The script automatically uses:
`/sdcard/Download/POPS2`

### Folder structure:
```text
POPS2/
├── JPS1/          # Original PS1 games (.cue/.bin)
├── MPS1/          # Temporary merged BIN files
├── VPS1/          # Generated VCD files
├── RPS1/          # Renamed VCD files
├── PS1M/          # Virtual Memory Card template
└── .POPSTARTER/   # Final POPStarter output
```

---

## Installation

### 1. Grant Storage Permission

```bash
termux-setup-storage
```

### 2. Install dependencies, repository, and run the script

```bash
pkg update -y && \
pkg upgrade -y && \
pkg install -y git make clang python && \
git clone https://github.com/ProjectOpSo/PS1-POPS-Auto-Termux.git && \
cd PS1-POPS-Auto-Termux && \
git clone https://github.com/makefu/cue2pops-linux.git cue2pops-linux && \
git clone https://github.com/putnam/binmerge.git && \
git clone https://github.com/AnimMouse/POPS-binaries.git && \
cd cue2pops-linux && \
make && \
chmod +x cue2pops && \
cd .. && \
chmod +x ps1popsauto.sh && \
./ps1popsauto.sh
```

**The script automatically:**
* Merges multi-track games.
* Converts them to `.VCD`.
* Renames incompatible filenames.
* Builds the complete POPStarter directory.
* Generates the final `.POPSTARTER` folder.

---

## Credits

* **makefu** — [cue2pops-linux](https://github.com/makefu/cue2pops-linux.git)
  * Portable C implementation of `cue2pops`.
* **putnam** — [binmerge](https://github.com/putnam/binmerge)
  * Multi-track PlayStation image merger.
* **AnimMouse** — [POPS-binaries](https://github.com/AnimMouse/POPS-binaries)
  * Required POPStarter binaries and supporting file
