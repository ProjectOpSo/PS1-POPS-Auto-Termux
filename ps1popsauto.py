#!/usr/bin/env python3
#
#  POPS Auto Converter
#

import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

# Regular expressions to locate PS1 game serials (IDs) in binary data
SERIAL_PRIMARY_RE_BYTES = re.compile(
    rb"([A-Z]{4})[_-]?([0-9]{3})\.?([0-9]{2})", re.IGNORECASE
)
SERIAL_MATCH_RE_BYTES = re.compile(
    rb"(?:BOOT\s*=\s*cdrom:\\?|cdrom:\\?|\b)([S|P][L|C][E|U|P|M][S|A|R|D|P|M][_|\-]?[0-9]{3}\.?[0-9]{2}(?:;[0-9]+)?)",
    re.IGNORECASE,
)
ALT_SERIAL_RE_BYTES = re.compile(
    rb"\b([S|P][L|C][E|U|P|M][S|A|R|D|P|M][_|\-]?[0-9]{5})\b", re.IGNORECASE
)

# Regular expressions for cleaning track markers and updating CUE binary references
TRACK_RE = re.compile(r"\s*\([T|t]rack\s*[0-9]+\)", re.IGNORECASE)
CUE_FILE_RE = re.compile(r'FILE\s+"([^"]+)"', re.IGNORECASE)
CUE_FILE_REPLACE = re.compile(r'FILE ".*" BINARY', re.IGNORECASE)

# Check if FFmpeg is available on the host environment
HAS_FFMPEG = shutil.which("ffmpeg") is not None


def detect_storage():
  """Detect system storage path dynamically for Termux/Android or standard Unix environments."""
  candidates = [
      "/sdcard",
      "/storage/emulated/0",
      os.environ.get("EXTERNAL_STORAGE", ""),
      os.path.expanduser("~/storage/shared"),
  ]
  for c in candidates:
    if c and os.path.isdir(c):
      return c
  return "/sdcard"


# Define main environment base directory and standard POPS2 directory tree
BASE = detect_storage()
POPS2_DIR = os.path.join(BASE, "Download", "POPS2")

JPS1_DIR = os.path.join(POPS2_DIR, "JPS1")
MPS1_DIR = os.path.join(POPS2_DIR, "MPS1")
VPS1_DIR = os.path.join(POPS2_DIR, "VPS1")
RPS1_DIR = os.path.join(POPS2_DIR, "RPS1")
PS1M_DIR = os.path.join(POPS2_DIR, "PS1M")

# Define target structure for OPL/POPStarter execution
POPSTARTER_FINAL_DIR = os.path.join(POPS2_DIR, ".POPSTARTER")
FINAL_POPS_DIR = os.path.join(POPSTARTER_FINAL_DIR, "POPS")
ROOT_ART_DIR = os.path.join(POPSTARTER_FINAL_DIR, "ART")
FINAL_APPS_DIR = os.path.join(POPSTARTER_FINAL_DIR, "APPS")

POPS_ELF = os.path.join(POPS2_DIR, "POPSTARTER.ELF")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CAD_TXT = os.path.join(SCRIPT_DIR, "cad.txt")

REPO_DIR = "./POPS-binaries"
RCUE2POPS = os.path.join(SCRIPT_DIR, "cue2pops-android", "rcue2pops.py")
BINMERGE = "./binmerge/binmerge"


def sanitize_vcd_name(name):
  """Strip all non-alphanumeric characters (spaces, hyphens, quotes, symbols) leaving only letters and numbers."""
  return re.sub(r"[^A-Za-z0-9]", "", name)


def validate_jps1_structure():
  """Ensure no loose files are placed directly inside 'JPS1'.

  All games must be in subdirectories.
  """
  if not os.path.exists(JPS1_DIR):
    return
  with os.scandir(JPS1_DIR) as entries:
    loose_files = [e.name for e in entries if e.is_file()]

  if loose_files:
    print("\n" + "=" * 60)
    print("[ERROR] Loose files detected directly inside 'JPS1' folder!")
    print("Please place each game inside its own individual subfolder.")
    print("=" * 60 + "\n")
    sys.exit(1)


def fix_cue_files_in_folder(folder_path):
  """Repair path references inside .CUE files to point correctly to associated .BIN files."""
  with os.scandir(folder_path) as entries:
    cue_files = [
        e.path for e in entries if e.is_file() and e.name.lower().endswith(".cue")
    ]
  if not cue_files:
    return

  with os.scandir(folder_path) as entries:
    bin_files = [
        e.path for e in entries if e.is_file() and e.name.lower().endswith(".bin")
    ]

  for cue_path in cue_files:
    cue_dir = os.path.dirname(cue_path)
    cue_base = os.path.splitext(os.path.basename(cue_path))[0]
    first_word = cue_base.split()[0] if cue_base.split() else ""

    matching_bins = [
        os.path.basename(b)
        for b in bin_files
        if first_word.lower() in os.path.basename(b).lower()
    ]

    try:
      with open(cue_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    except Exception:
      continue

    new_lines = []
    if len(matching_bins) == 1:
      for line in lines:
        new_lines.append(
            CUE_FILE_REPLACE.sub(f'FILE "{matching_bins[0]}" BINARY', line)
        )
    elif len(matching_bins) > 1:
      idx = 0
      for line in lines:
        if CUE_FILE_REPLACE.search(line):
          match = CUE_FILE_RE.search(line)
          target_bin = match.group(1) if match else ""
          if not os.path.exists(os.path.join(cue_dir, target_bin)):
            if idx < len(matching_bins):
              new_lines.append(f'FILE "{matching_bins[idx]}" BINARY\n')
              idx += 1
            else:
              new_lines.append(line)
          else:
            new_lines.append(line)
        else:
          new_lines.append(line)
    elif len(bin_files) == 1:
      single_bin = os.path.basename(bin_files[0])
      for line in lines:
        new_lines.append(
            CUE_FILE_REPLACE.sub(f'FILE "{single_bin}" BINARY', line)
        )
    else:
      continue

    try:
      with open(cue_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    except Exception:
      pass


def format_raw_serial_bytes(raw_bytes):
  """Parse raw byte matches into standardized PS1 game serial format (e.g., SLUS_000.05)."""
  try:
    raw = raw_bytes.decode("latin-1", errors="ignore").upper().strip()
  except Exception:
    return None

  if ";" in raw:
    raw = raw.split(";")[0].strip()
  raw = raw.replace("\\", "/").split("/")[-1]

  match = re.search(
      r"([A-Z]{4})[_-]?([0-9]{3})\.?([0-9]{2})", raw, re.IGNORECASE
  )
  if match:
    return f"{match.group(1)}_{match.group(2)}.{match.group(3)}"
  return None


def _scan_buffer_for_serial(buf):
  """Scan byte buffer using compiled regular expressions to detect game IDs."""
  for m in SERIAL_MATCH_RE_BYTES.findall(buf):
    formatted = format_raw_serial_bytes(m)
    if formatted:
      return formatted

  for m in ALT_SERIAL_RE_BYTES.findall(buf):
    formatted = format_raw_serial_bytes(m)
    if formatted:
      return formatted

  return None


def extract_serial_from_bin(bin_path):
  """Extract game serial directly from the .BIN header using progressive buffer reading."""
  if not os.path.exists(bin_path):
    return None

  try:
    file_size = os.path.getsize(bin_path)
    with open(bin_path, "rb") as f:
      # Perform initial scan on first 16 MB chunk
      first_chunk_size = min(file_size, 16 * 1024 * 1024)
      data = f.read(first_chunk_size)
      serial = _scan_buffer_for_serial(data)
      if serial:
        return serial

      # Progressive windowed fallback search across the full binary
      f.seek(0)
      chunk_size = 1024 * 1024
      overlap = 2048
      window = bytearray()

      while True:
        chunk = f.read(chunk_size)
        if not chunk:
          break
        window.extend(chunk)

        serial = _scan_buffer_for_serial(bytes(window))
        if serial:
          return serial

        if len(window) > overlap:
          del window[:-overlap]

  except (OSError, IOError):
    pass

  return None


def get_first_bin_from_cue(cue_path):
  """Parse .CUE file to locate Track 1 binary file for accurate serial extraction."""
  if not os.path.exists(cue_path):
    return None

  cue_dir = os.path.dirname(cue_path)
  try:
    with open(cue_path, "r", encoding="utf-8", errors="ignore") as f:
      for line in f:
        match = CUE_FILE_RE.search(line)
        if match:
          bin_name = match.group(1)
          target_bin = os.path.join(cue_dir, bin_name)
          if os.path.exists(target_bin):
            return target_bin
  except Exception:
    pass

  # Fallback: scan folder directly for the first available .BIN file
  with os.scandir(cue_dir) as entries:
    bins = [
        e.path for e in entries if e.is_file() and e.name.lower().endswith(".bin")
    ]
    if bins:
      return sorted(bins)[0]

  return None


def process_and_resize_image_ffmpeg(temp_img_path, out_path):
  """Resize downloaded cover image using FFmpeg to comply with OPL specs (200x200 8-bit PNG)."""
  os.makedirs(os.path.dirname(out_path), exist_ok=True)
  if HAS_FFMPEG:
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".png", dir=os.path.dirname(out_path)
    ) as tmp:
      tmp_name = tmp.name

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        temp_img_path,
        "-vf",
        "scale=200:200",
        "-pix_fmt",
        "pal8",
        "-pred",
        "mixed",
        tmp_name,
    ]
    try:
      res = subprocess.run(
          cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
      )
      if (
          res.returncode == 0
          and os.path.exists(tmp_name)
          and os.path.getsize(tmp_name) > 0
      ):
        os.replace(tmp_name, out_path)
      else:
        if os.path.exists(tmp_name):
          os.remove(tmp_name)
        shutil.copy(temp_img_path, out_path)
    except Exception:
      if os.path.exists(tmp_name):
        try:
          os.remove(tmp_name)
        except Exception:
          pass
      shutil.copy(temp_img_path, out_path)
  else:
    shutil.copy(temp_img_path, out_path)


def download_single_cover(sanitized_vcd_stem, serial, mode_prefix):
  """Download high-priority game cover image using sanitized target VCD name."""
  if not serial:
    print(f"[!] ID not found: {sanitized_vcd_stem}")
    return

  os.makedirs(ROOT_ART_DIR, exist_ok=True)
  app_cover_name = f"{mode_prefix}{sanitized_vcd_stem}.ELF_COV.png"
  target_app_cover = os.path.join(ROOT_ART_DIR, app_cover_name)

  if os.path.exists(target_app_cover):
    print(f"[=] Cover already exists for: {sanitized_vcd_stem}")
    return

  print(f"[*] Downloading Cover Art (Priority) -> ID [{serial}] : {sanitized_vcd_stem}")

  cad_urls = []
  if os.path.exists(CAD_TXT):
    with open(CAD_TXT, "r", encoding="utf-8", errors="ignore") as f:
      cad_urls = [line.strip() for line in f if line.strip().startswith("http")]

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
      )
  }

  downloaded = False
  raw_download_path = None

  target_cad_url = f"http://www.hwc.nat.cu/psx/{serial}_COV.jpg"
  cad_match = [u for u in cad_urls if serial.lower() in u.lower()]
  url_to_try = cad_match[0] if cad_match else target_cad_url

  with tempfile.NamedTemporaryFile(
      delete=False, suffix=".jpg", dir=POPS2_DIR
  ) as tmp_file:
    raw_download_path = tmp_file.name

  try:
    req = urllib.request.Request(url_to_try, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as response:
      data = response.read()
      if len(data) > 2048:
        with open(raw_download_path, "wb") as out_file:
          out_file.write(data)
        downloaded = True
  except Exception:
    pass

  # Fallback to GitHub repositories if CAD repository lookup fails
  if not downloaded:
    clean_serial = serial.replace("_", "-").replace(".", "")
    test_urls = [
        f"https://raw.githubusercontent.com/xlenore/psx-covers/main/covers/default/{clean_serial}.jpg",
        f"https://raw.githubusercontent.com/xlenore/psx-covers/main/covers/3d/{clean_serial}.png",
    ]
    for url in test_urls:
      try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as response:
          data = response.read()
          if len(data) > 2048:
            with open(raw_download_path, "wb") as out_file:
              out_file.write(data)
            downloaded = True
            break
      except Exception:
        continue

  if downloaded and raw_download_path and os.path.exists(raw_download_path):
    process_and_resize_image_ffmpeg(raw_download_path, target_app_cover)
    if os.path.exists(raw_download_path):
      os.remove(raw_download_path)
    print("  [✓] Cover processed successfully.")
  else:
    if raw_download_path and os.path.exists(raw_download_path):
      os.remove(raw_download_path)
    print("  [X] Cover not found.")


def process_single_game(folder_path, binmerge_cmd, tmp_work_dir, mode_prefix):
  """Individual pipeline: Extract Serial -> Priority Cover Download -> BIN Merge (MPS1) -> VCD Conversion (VPS1)."""
  folder_name = os.path.basename(folder_path)
  print(f"\n[*] Processing: {folder_name}")

  with os.scandir(folder_path) as entries:
    files = [e for e in entries if e.is_file()]

  cue_files = [f.path for f in files if f.name.lower().endswith(".cue")]
  bin_files = [f.path for f in files if f.name.lower().endswith(".bin")]

  if not cue_files:
    print(f"[!] No CUE file found in: {folder_name}")
    return None, None

  cue_path = cue_files[0]
  
  # Retain unmodified original folder name for title.cfg
  original_title = TRACK_RE.sub("", folder_name).strip()
  
  # Sanitize stem for VCD output file name
  sanitized_vcd_stem = sanitize_vcd_name(original_title)

  # Step 1: Extract serial from Track 1 BIN prior to any modification
  track1_bin = get_first_bin_from_cue(cue_path)
  serial = extract_serial_from_bin(track1_bin) if track1_bin else None

  # Step 2: PRIORITY - Download game cover art before proceeding to conversion
  download_single_cover(sanitized_vcd_stem, serial, mode_prefix)

  # Step 3: Handle multi-BIN merging inside temporary folder MPS1
  target_cue_for_conversion = cue_path

  if len(bin_files) > 1:
    fix_cue_files_in_folder(folder_path)
    print(f"[*] Trying BIN merge: {folder_name}")
    game_mps1_dir = os.path.join(MPS1_DIR, folder_name)
    os.makedirs(game_mps1_dir, exist_ok=True)

    cmd = (
        binmerge_cmd + ["--outdir", game_mps1_dir, cue_path, sanitized_vcd_stem]
        if isinstance(binmerge_cmd, list)
        else [binmerge_cmd, "--outdir", game_mps1_dir, cue_path, sanitized_vcd_stem]
    )
    res = subprocess.run(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    if res.returncode == 0:
      print(f"[✓] Merge successful in MPS1: {folder_name}")
      merged_cue = os.path.join(game_mps1_dir, f"{sanitized_vcd_stem}.cue")
      if os.path.exists(merged_cue):
        target_cue_for_conversion = merged_cue
    else:
      print(f"[!] Merge unavailable, continuing with original files: {folder_name}")
      shutil.rmtree(game_mps1_dir, ignore_errors=True)
  else:
    print(f"[*] Single BIN detected, skipping merge: {folder_name}")

  out_vcd = os.path.join(VPS1_DIR, f"{sanitized_vcd_stem}.VCD")

  if os.path.exists(out_vcd):
    print(f"[=] VCD already exists in VPS1: {sanitized_vcd_stem}.VCD")
    shutil.rmtree(folder_path, ignore_errors=True)
    return sanitized_vcd_stem, original_title

  # Step 4: Convert source image to .VCD format directly inside VPS1
  print(f"[*] Converting: {folder_name} -> {sanitized_vcd_stem}.VCD")
  tmp_vcd = os.path.join(tmp_work_dir, f"{sanitized_vcd_stem}.VCD")

  try:
    subprocess.run(
        [sys.executable, RCUE2POPS, target_cue_for_conversion, "-o", tmp_work_dir, "-f"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=900,
    )
  except subprocess.TimeoutExpired:
    print(f"[!] Conversion timed out: {folder_name}")

  # Clean temporary MPS1 folder if it was created during merge
  game_mps1_dir = os.path.join(MPS1_DIR, folder_name)
  if os.path.exists(game_mps1_dir):
    shutil.rmtree(game_mps1_dir, ignore_errors=True)

  if os.path.exists(tmp_vcd) and os.path.getsize(tmp_vcd) > 0:
    shutil.move(tmp_vcd, out_vcd)
    print(f"[✓] VCD created in VPS1: {sanitized_vcd_stem}.VCD")
    shutil.rmtree(folder_path, ignore_errors=True)
    return sanitized_vcd_stem, original_title
  else:
    print(f"[!] Conversion failed to produce VCD: {folder_name}")

  for f in glob.glob(os.path.join(tmp_work_dir, f"{sanitized_vcd_stem}*")):
    try:
      os.remove(f)
    except Exception:
      pass

  return None, None


def process_all_games_sequentially(mode_prefix):
  """Process every game directory inside JPS1 sequentially."""
  tmp_work_dir = os.path.join(POPS2_DIR, ".tmp_conv")
  os.makedirs(tmp_work_dir, exist_ok=True)

  if not os.path.exists(RCUE2POPS):
    print(f"[ERROR] Conversion script not found: {RCUE2POPS}")
    shutil.rmtree(tmp_work_dir, ignore_errors=True)
    return {}

  binmerge_cmd = BINMERGE
  if not os.access(BINMERGE, os.X_OK) and os.path.exists(
      "./binmerge/binmerge.py"
  ):
    binmerge_cmd = [sys.executable, "./binmerge/binmerge.py"]

  if not os.path.exists(JPS1_DIR):
    shutil.rmtree(tmp_work_dir, ignore_errors=True)
    return {}

  with os.scandir(JPS1_DIR) as entries:
    subfolders = [e.path for e in entries if e.is_dir()]

  titles_map = {}

  for folder in subfolders:
    vcd_stem, original_title = process_single_game(folder, binmerge_cmd, tmp_work_dir, mode_prefix)
    if vcd_stem and original_title:
      titles_map[vcd_stem] = original_title

  shutil.rmtree(tmp_work_dir, ignore_errors=True)
  return titles_map


def move_to_rps1():
  """Move converted .VCD files from VPS1 to RPS1 stage directory."""
  if not os.path.exists(VPS1_DIR):
    return
  with os.scandir(VPS1_DIR) as entries:
    vcd_files = [
        e.path for e in entries if e.is_file() and e.name.lower().endswith(".vcd")
    ]

  for vcd in vcd_files:
    base_vcd = os.path.basename(vcd)
    dest = os.path.join(RPS1_DIR, base_vcd)
    shutil.move(vcd, dest)


def build_final_structure(titles_map, mode_prefix):
  """Construct final .POPSTARTER folder layout (POPS, APPS, title.cfg, VMC templates)."""
  if os.path.isdir(REPO_DIR):
    with os.scandir(REPO_DIR) as entries:
      for entry in entries:
        if entry.is_file():
          dest = os.path.join(FINAL_POPS_DIR, entry.name)
          if not os.path.exists(dest):
            shutil.copy(entry.path, dest)

  if not os.path.exists(RPS1_DIR):
    return

  with os.scandir(RPS1_DIR) as entries:
    vcd_files = [
        e.path for e in entries if e.is_file() and e.name.lower().endswith(".vcd")
    ]

  games = []

  for vcd in vcd_files:
    base_vcd = os.path.basename(vcd)
    stem = os.path.splitext(base_vcd)[0]

    # Move VCDs into final POPS execution path
    shutil.move(vcd, os.path.join(FINAL_POPS_DIR, base_vcd))
    games.append(stem)

    # Copy virtual memory card templates if present
    if os.path.isdir(PS1M_DIR):
      dest_mem = os.path.join(FINAL_POPS_DIR, stem)
      os.makedirs(dest_mem, exist_ok=True)
      with os.scandir(PS1M_DIR) as mem_entries:
        for item in mem_entries:
          s = item.path
          d = os.path.join(dest_mem, item.name)
          if item.is_dir():
            shutil.copytree(s, d, dirs_exist_ok=True)
          else:
            shutil.copy2(s, d)

  # Create launcher ELFs and title.cfg configuration keeping original uncleaned name for titles
  if os.path.isfile(POPS_ELF) and games:
    for game in games:
      game_app_dir = os.path.join(FINAL_APPS_DIR, game)
      os.makedirs(game_app_dir, exist_ok=True)

      elf_name = f"{mode_prefix}{game}.ELF"
      shutil.copy(POPS_ELF, os.path.join(game_app_dir, elf_name))

      display_title = titles_map.get(game, game)
      cfg_path = os.path.join(game_app_dir, "title.cfg")
      with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(f"title={display_title}\nboot={elf_name}\n")


def main():
  """Main execution entry point."""
  tmp_work_dir = os.path.join(POPS2_DIR, ".tmp_conv")

  try:
    os.system("cls" if os.name == "nt" else "clear")
    print("========================================")
    print("         POPS AUTO CONVERTER            ")
    print("========================================")
    print("Select target mode:")
    print("1 - USB")
    print("2 - SMB")

    choice = input("\nPress 1 for USB or 2 for SMB: ").strip()
    while choice not in ["1", "2"]:
      choice = input(
          "Invalid option. Press 1 for USB or 2 for SMB: "
      ).strip()

    mode_prefix = "XX." if choice == "1" else "SB."

    # Build initial POPS2 environment folder structure
    dirs = [
        POPS2_DIR,
        JPS1_DIR,
        MPS1_DIR,
        VPS1_DIR,
        RPS1_DIR,
        PS1M_DIR,
        POPSTARTER_FINAL_DIR,
        FINAL_POPS_DIR,
        ROOT_ART_DIR,
        FINAL_APPS_DIR,
    ]
    for d in dirs:
      os.makedirs(d, exist_ok=True)

    validate_jps1_structure()

    # Run processing pipeline with cover priority and sanitized file output
    titles_map = process_all_games_sequentially(mode_prefix)

    # Transition files through RPS1 into final layout
    move_to_rps1()
    build_final_structure(titles_map, mode_prefix)

    print("\n[✓] Completed successfully.")

  finally:
    # Ensure temporary working directory cleanup on finish or error
    if os.path.exists(tmp_work_dir):
      shutil.rmtree(tmp_work_dir, ignore_errors=True)


if __name__ == "__main__":
  main()
