#!/usr/bin/env python3
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

SANITIZE_RE = re.compile(r'[@#$_&\-\+\(\)/\*"\'\:;\!\?,\~`\|•√π÷×§∆£¢€¥\^°=\{\}\\%\©®™✓\[\]<>\.\,\s]+')
SERIAL_PRIMARY_RE = re.compile(r"([A-Z]{4})[_-]?([0-9]{3})\.?([0-9]{2})", re.IGNORECASE)
SERIAL_MATCH_RE = re.compile(
    r"(?:BOOT\s*=\s*cdrom:\\?|cdrom:\\?|\b)([S|P][L|C][E|U|P|M][S|A|R|D|P|M][_|\-]?[0-9]{3}\.?[0-9]{2}(?:;[0-9]+)?)",
    re.IGNORECASE,
)
ALT_SERIAL_RE = re.compile(
    r"\b([S|P][L|C][E|U|P|M][S|A|R|D|P|M][_|\-]?[0-9]{5})\b",
    re.IGNORECASE,
)
TRACK_RE = re.compile(r"\s*\([T|t]rack\s*[0-9]+\)", re.IGNORECASE)
CUE_FILE_RE = re.compile(r'FILE\s+"([^"]+)"', re.IGNORECASE)
CUE_FILE_REPLACE = re.compile(r'FILE ".*" BINARY', re.IGNORECASE)

HAS_FFMPEG = shutil.which("ffmpeg") is not None


def detect_storage():
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


BASE = detect_storage()
POPS2_DIR = os.path.join(BASE, "Download", "POPS2")

JPS1_DIR = os.path.join(POPS2_DIR, "JPS1")
MPS1_DIR = os.path.join(POPS2_DIR, "MPS1")
VPS1_DIR = os.path.join(POPS2_DIR, "VPS1")
RPS1_DIR = os.path.join(POPS2_DIR, "RPS1")
PS1M_DIR = os.path.join(POPS2_DIR, "PS1M")

POPSTARTER_FINAL_DIR = os.path.join(POPS2_DIR, ".POPSTARTER")
FINAL_POPS_DIR = os.path.join(POPSTARTER_FINAL_DIR, "POPS")

ROOT_ART_DIR = os.path.join(POPSTARTER_FINAL_DIR, "ART")
TMP_ART_DIR = os.path.join(POPSTARTER_FINAL_DIR, "TMPART")

FINAL_APPS_DIR = os.path.join(POPSTARTER_FINAL_DIR, "APPS")

POPS_ELF = os.path.join(POPS2_DIR, "POPSTARTER.ELF")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CAD_TXT = os.path.join(SCRIPT_DIR, "cad.txt")

REPO_DIR = "./POPS-binaries"
CUE2POPS = "./cue2pops-linux/cue2pops"
BINMERGE = "./binmerge/binmerge"


def sanitize_name(name):
    return SANITIZE_RE.sub("", name).strip()


def sanitize_input_files():
    if not os.path.exists(JPS1_DIR):
        return

    for item in os.listdir(JPS1_DIR):
        full_path = os.path.join(JPS1_DIR, item)
        if not os.path.isfile(full_path):
            continue

        base_name, ext = os.path.splitext(item)
        cleaned_base = sanitize_name(base_name)

        if not cleaned_base:
            continue

        new_filename = f"{cleaned_base}{ext}"
        new_path = os.path.join(JPS1_DIR, new_filename)

        if full_path != new_path:
            shutil.move(full_path, new_path)


def format_raw_serial(raw):
    raw = raw.upper().strip()
    if ";" in raw:
        raw = raw.split(";")[0].strip()

    raw = raw.replace("\\", "/").split("/")[-1]

    match = SERIAL_PRIMARY_RE.search(raw)
    if match:
        prefix = match.group(1)
        num1 = match.group(2)
        num2 = match.group(3)
        return f"{prefix}_{num1}.{num2}"

    return None


def extract_serial_from_bin(bin_path, chunk_size=1024 * 1024):
    if not os.path.exists(bin_path):
        return None
    try:
        buffer = ""
        with open(bin_path, "rb") as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break

                buffer += data.decode("latin-1", errors="ignore")

                for m in SERIAL_MATCH_RE.findall(buffer):
                    formatted = format_raw_serial(m)
                    if formatted:
                        return formatted

                for m in ALT_SERIAL_RE.findall(buffer):
                    formatted = format_raw_serial(m)
                    if formatted:
                        return formatted

                buffer = buffer[-1024:]

    except (OSError, IOError):
        pass
    return None


def get_game_serials_map():
    game_map = {}
    titles_map = {}
    bin_files = glob.glob(os.path.join(JPS1_DIR, "*.[bB][iI][nN]"))

    for bin_path in bin_files:
        stem = os.path.splitext(os.path.basename(bin_path))[0]
        base_stem = TRACK_RE.sub("", stem).strip()
        clean_name = sanitize_name(base_stem)

        serial = extract_serial_from_bin(bin_path)
        if serial:
            game_map[clean_name] = serial
            game_map[base_stem] = serial
            game_map[stem] = serial
            titles_map[clean_name] = base_stem

    return game_map, titles_map


def process_and_resize_image_ffmpeg(temp_img_path, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    if HAS_FFMPEG:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png", dir=os.path.dirname(out_path)) as tmp:
            tmp_name = tmp.name

        cmd = [
            "ffmpeg",
            "-y",
            "-i", temp_img_path,
            "-vf", "scale=200:200",
            "-pix_fmt", "pal8",
            tmp_name
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0 and os.path.exists(tmp_name) and os.path.getsize(tmp_name) > 0:
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

    if hasattr(os, "sync"):
        try:
            os.sync()
        except Exception:
            pass


def download_covers_opl(game_serials, mode_prefix):
    print("\n--- Downloading Cover Art (.png) ---")
    os.makedirs(ROOT_ART_DIR, exist_ok=True)
    os.makedirs(TMP_ART_DIR, exist_ok=True)

    cad_urls = []
    if os.path.exists(CAD_TXT):
        with open(CAD_TXT, "r", encoding="utf-8", errors="ignore") as f:
            cad_urls = [line.strip() for line in f if line.strip().startswith("http")]

    search_dirs = [FINAL_POPS_DIR]
    found_vcds = []

    for s_dir in search_dirs:
        for path in glob.glob(os.path.join(s_dir, "*.[vV][cC][dD]")):
            base = os.path.basename(path)
            found_vcds.append(base)

    if not found_vcds:
        print("[!] No games found for cover downloading.")
        time.sleep(2)
        return

    headers = {"User-Agent": "Mozilla/5.0 (Android; Termux)"}

    for vcd_filename in sorted(found_vcds):
        vcd_stem = os.path.splitext(vcd_filename)[0]

        game_title = vcd_stem
        clean_game_name = sanitize_name(game_title)
        serial = (
            game_serials.get(game_title)
            or game_serials.get(clean_game_name)
        )
        if not serial:
            for k, v in game_serials.items():
                if k.lower() in clean_game_name.lower() or clean_game_name.lower() in k.lower():
                    serial = v
                    break

        app_cover_name = f"{mode_prefix}{vcd_stem}.ELF_COV.png"
        target_app_cover = os.path.join(ROOT_ART_DIR, app_cover_name)

        if os.path.exists(target_app_cover):
            print(f"[=] Cover already exists for: {vcd_stem}")
            continue

        if not serial:
            print(f"[!] ID not found: {vcd_stem}")
            continue

        print(f"[*] ID [{serial}] -> {vcd_stem}")
        downloaded = False
        raw_download_path = None

        target_cad_url = f"http://www.hwc.nat.cu/psx/{serial}_COV.jpg"
        cad_match = [u for u in cad_urls if serial.lower() in u.lower()]
        url_to_try = cad_match[0] if cad_match else target_cad_url

        with tempfile.NamedTemporaryFile(delete=False, suffix=".img", dir=POPS2_DIR) as tmp_file:
            raw_download_path = tmp_file.name

        try:
            req = urllib.request.Request(url_to_try, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                with open(raw_download_path, "wb") as out_file:
                    out_file.write(response.read())
            downloaded = True
        except Exception:
            pass

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
                        with open(raw_download_path, "wb") as out_file:
                            out_file.write(response.read())
                    downloaded = True
                    break
                except Exception:
                    continue

        if downloaded and raw_download_path and os.path.exists(raw_download_path):
            tmp_app = os.path.join(TMP_ART_DIR, "app_" + app_cover_name)

            process_and_resize_image_ffmpeg(raw_download_path, tmp_app)

            shutil.move(tmp_app, target_app_cover)

            if os.path.exists(raw_download_path):
                os.remove(raw_download_path)
            print("  [✓] Cover processed to PNG (pal8) via FFmpeg.")
        else:
            if raw_download_path and os.path.exists(raw_download_path):
                os.remove(raw_download_path)
            print("  [X] Cover not found.")

    shutil.rmtree(TMP_ART_DIR, ignore_errors=True)
    print("\n[*] Cover downloading process completed.")
    time.sleep(2)


def fix_cue_files():
    cue_files = glob.glob(os.path.join(JPS1_DIR, "*.[cC][uU][eE]"))

    for cue_path in cue_files:
        cue_dir = os.path.dirname(cue_path)
        cue_base = os.path.splitext(os.path.basename(cue_path))[0]
        first_word = cue_base.split()[0] if cue_base.split() else ""

        bin_files = glob.glob(os.path.join(cue_dir, "*.[bB][iI][nN]"))
        matching_bins = [
            os.path.basename(b)
            for b in bin_files
            if first_word.lower() in os.path.basename(b).lower()
        ]

        with open(cue_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        new_lines = []

        if len(matching_bins) == 1:
            for line in lines:
                new_line = CUE_FILE_REPLACE.sub(f'FILE "{matching_bins[0]}" BINARY', line)
                new_lines.append(new_line)
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
                new_line = CUE_FILE_REPLACE.sub(f'FILE "{single_bin}" BINARY', line)
                new_lines.append(new_line)
        else:
            continue

        with open(cue_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)


def merge_multi_bin_games():
    binmerge_cmd = BINMERGE
    if not os.access(BINMERGE, os.X_OK) and os.path.exists("./binmerge/binmerge.py"):
        binmerge_cmd = [sys.executable, "./binmerge/binmerge.py"]

    cue_files = glob.glob(os.path.join(JPS1_DIR, "*.[cC][uU][eE]"))

    for cue_path in cue_files:
        stem = os.path.splitext(os.path.basename(cue_path))[0]
        bin_files = []

        with open(cue_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                match = CUE_FILE_RE.search(line)
                if match:
                    bin_files.append(match.group(1))

        if len(bin_files) > 1:
            for bin_file in bin_files:
                src_bin = os.path.join(JPS1_DIR, bin_file)
                if os.path.exists(src_bin):
                    shutil.move(src_bin, os.path.join(MPS1_DIR, bin_file))

            shutil.move(cue_path, os.path.join(MPS1_DIR, f"{stem}.cue"))

            target_cue = os.path.join(MPS1_DIR, f"{stem}.cue")
            cmd = (
                binmerge_cmd + ["--outdir", JPS1_DIR, target_cue, stem]
                if isinstance(binmerge_cmd, list)
                else [binmerge_cmd, "--outdir", JPS1_DIR, target_cue, stem]
            )

            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if result.returncode == 0:
                for f in glob.glob(os.path.join(MPS1_DIR, f"{stem}*")):
                    os.remove(f)
            else:
                for f in glob.glob(os.path.join(MPS1_DIR, f"{stem}*")):
                    shutil.move(f, JPS1_DIR)


def convert_games():
    tmp_work_dir = os.path.join(POPS2_DIR, ".tmp_conv")
    os.makedirs(tmp_work_dir, exist_ok=True)

    if not os.access(CUE2POPS, os.X_OK) and not os.path.exists(CUE2POPS):
        shutil.rmtree(tmp_work_dir, ignore_errors=True)
        return

    cue_files = glob.glob(os.path.join(JPS1_DIR, "*.[cC][uU][eE]"))

    for cue_path in cue_files:
        stem = os.path.splitext(os.path.basename(cue_path))[0]
        out_vcd = os.path.join(VPS1_DIR, f"{stem}.VCD")

        if os.path.exists(out_vcd):
            continue

        tmp_vcd = os.path.join(tmp_work_dir, f"{stem}.VCD")

        def set_prio():
            if hasattr(os, "nice"):
                os.nice(19)

        try:
            subprocess.run(
                [CUE2POPS, cue_path, tmp_vcd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=900,
                preexec_fn=set_prio if os.name == "posix" else None,
            )
        except subprocess.TimeoutExpired:
            pass

        if os.path.exists(tmp_vcd) and os.path.getsize(tmp_vcd) > 0:
            shutil.move(tmp_vcd, out_vcd)
            for f in glob.glob(os.path.join(JPS1_DIR, f"{stem}*")):
                os.remove(f)

        for f in glob.glob(os.path.join(tmp_work_dir, f"{stem}*")):
            os.remove(f)

        time.sleep(1)

    shutil.rmtree(tmp_work_dir, ignore_errors=True)


def rename_and_move_to_rps1():
    vcd_files = glob.glob(os.path.join(VPS1_DIR, "*.[vV][cC][dD]"))

    for vcd in vcd_files:
        base_vcd = os.path.basename(vcd)
        stem = os.path.splitext(base_vcd)[0]

        clean_title = sanitize_name(stem)
        final_vcd_name = f"{clean_title}.VCD"

        dest = os.path.join(RPS1_DIR, final_vcd_name)
        shutil.move(vcd, dest)


def build_final_structure(titles_map, mode_prefix):
    if os.path.isdir(REPO_DIR):
        for bin_file in glob.glob(os.path.join(REPO_DIR, "*")):
            if os.path.isfile(bin_file):
                b_name = os.path.basename(bin_file)
                dest = os.path.join(FINAL_POPS_DIR, b_name)
                if not os.path.exists(dest):
                    shutil.copy(bin_file, dest)

    vcd_files = glob.glob(os.path.join(RPS1_DIR, "*.[vV][cC][dD]"))
    games = []

    for vcd in vcd_files:
        base_vcd = os.path.basename(vcd)
        stem = os.path.splitext(base_vcd)[0]

        shutil.move(vcd, os.path.join(FINAL_POPS_DIR, base_vcd))
        games.append(stem)

        if os.path.isdir(PS1M_DIR):
            dest_mem = os.path.join(FINAL_POPS_DIR, stem)
            os.makedirs(dest_mem, exist_ok=True)
            for item in os.listdir(PS1M_DIR):
                s = os.path.join(PS1M_DIR, item)
                d = os.path.join(dest_mem, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)

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


def run_workflow(game_serials, titles_map, mode_prefix):
    fix_cue_files()
    merge_multi_bin_games()
    convert_games()
    rename_and_move_to_rps1()
    build_final_structure(titles_map, mode_prefix)


def main():
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
            choice = input("Invalid option. Press 1 for USB or 2 for SMB: ").strip()

        mode_prefix = "XX." if choice == "1" else "SB."

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

        game_serials, titles_map = get_game_serials_map()
        sanitize_input_files()
        run_workflow(game_serials, titles_map, mode_prefix)
        download_covers_opl(game_serials, mode_prefix)

        remaining_cues = glob.glob(os.path.join(JPS1_DIR, "*.[cC][uU][eE]"))
        if len(remaining_cues) == 1:
            run_workflow(game_serials, titles_map, mode_prefix)
            remaining_cues = glob.glob(os.path.join(JPS1_DIR, "*.[cC][uU][eE]"))

        if len(remaining_cues) > 0:
            print(f"\n[!] Pending files in JPS1: {len(remaining_cues)}")
        else:
            print("\n[✓] Completed successfully.")

    finally:
        if os.path.exists(tmp_work_dir):
            shutil.rmtree(tmp_work_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
