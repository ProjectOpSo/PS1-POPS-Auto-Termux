#!/usr/bin/env python3
import os
import re
import sys
import time
import shutil
from pathlib import Path

KEYS_VAL = {"XPOS", "YPOS", "DWSTRETCH", "DWCROP", "USBDELAY"}

SUB_COMPAT = [
    "SAFEMODE",
    "FAKELC",
    "COMPATIBILITY_0x01",
    "COMPATIBILITY_0x02",
    "COMPATIBILITY_0x03",
    "COMPATIBILITY_0x04",
    "COMPATIBILITY_0x05",
    "COMPATIBILITY_0x06",
    "COMPATIBILITY_0x07",
]
SUB_VIDEO = ["480p", "HDTVFIX", "NOPAL", "FORCEPAL", "XPOS", "YPOS", "DWSTRETCH", "DWCROP"]
SUB_GRAPH = ["SMOOTH", "SCANLINES", "WIDESCREEN", "ULTRA_WIDESCREEN", "EYEFINITY"]
SUB_AUDIO_CTRL = ["MUTE_CDDA", "UNDO_MUTE_CDDA", "D2LS", "D2LS_ALT"]
SUB_SYS = ["CACHE1", "USBDELAY", "NOIGR", "UNDO_GAME_FIXES"]

SUB_COMPAT_SET = set(SUB_COMPAT)
HEX_VALIDATOR = re.compile(r"^[0-9A-FA-f]{2}$")

DESC_PT = {
    "SAFEMODE": "Modo de segurança (evita travamentos no boot)",
    "FAKELC": "Simula a proteção LibCrypt (jogos europeus protegidos)",
    "COMPATIBILITY_0x01": "Corrige áudio (restaura músicas e vozes)",
    "COMPATIBILITY_0x02": "Variante do 0x01 (mantém FMVs - ex: Colony Wars)",
    "COMPATIBILITY_0x03": "Alternativa de áudio para jogos específicos",
    "COMPATIBILITY_0x04": "Corrige bugs gráficos, lentidão e flickering (Mais Usado)",
    "COMPATIBILITY_0x05": "Corrige cutscenes (ex: Resident Evil Director's Cut)",
    "COMPATIBILITY_0x06": "Desativa o OSD da BIOS virtual (evita travar no boot)",
    "COMPATIBILITY_0x07": "Modo não documentado oficialmente",
    "480p": "Força saída de vídeo em 480p",
    "HDTVFIX": "Corrige tela verde/preta/distorcida em TVs modernas",
    "NOPAL": "Desativa o patch automático PAL",
    "FORCEPAL": "Força o modo de vídeo PAL",
    "XPOS": "Move a imagem horizontalmente (Ex: 620)",
    "YPOS": "Move a imagem verticalmente (Ex: 8)",
    "DWSTRETCH": "Altera a largura da imagem digitalmente",
    "DWCROP": "Recorta ou amplia a tela horizontalmente",
    "SMOOTH": "Filtro bilinear (remove serrilhados dos jogos)",
    "SCANLINES": "Simula linhas de varredura de TV CRT",
    "WIDESCREEN": "Hack de tela widescreen nativo (16:9)",
    "ULTRA_WIDESCREEN": "Hack de tela para proporção UltraWide",
    "EYEFINITY": "Hack de exibição para múltiplos monitores (3 telas)",
    "MUTE_CDDA": "Desativa a reprodução de faixas de música CDDA",
    "UNDO_MUTE_CDDA": "Força a reativação de músicas CDDA",
    "D2LS": "Mapeia o D-Pad para o Analógico Esquerdo",
    "D2LS_ALT": "Mapeamento alternativo do D-Pad para Analógico",
    "CACHE1": "Reduz cache para 1 setor (melhora leitura via USB)",
    "USBDELAY": "Define o tempo de atraso do USB em segundos (Ex: 4)",
    "NOIGR": "Desativa o In-Game Reset (Combinação de botões de sair)",
    "UNDO_GAME_FIXES": "Desativa correções automáticas padrões do emulador",
}

DESC_EN = {
    "SAFEMODE": "Safe mode (prevents boot freezes)",
    "FAKELC": "Simulates LibCrypt protection (protected PAL games)",
    "COMPATIBILITY_0x01": "Fixes audio (restores music and voices)",
    "COMPATIBILITY_0x02": "Variant of 0x01 (keeps FMVs working - e.g., Colony Wars)",
    "COMPATIBILITY_0x03": "Alternative audio fix for specific games",
    "COMPATIBILITY_0x04": "Fixes graphics bugs, slowdown, and flickering (Most Used)",
    "COMPATIBILITY_0x05": "Fixes cutscenes (e.g., Resident Evil Director's Cut)",
    "COMPATIBILITY_0x06": "Disables virtual BIOS OSD (prevents boot freeze)",
    "COMPATIBILITY_0x07": "Officially undocumented mode",
    "480p": "Forces 480p video output",
    "HDTVFIX": "Fixes green/black/distorted screens on modern TVs",
    "NOPAL": "Disables automatic PAL patch",
    "FORCEPAL": "Forces PAL video mode",
    "XPOS": "Moves image horizontally (e.g., 620)",
    "YPOS": "Moves image vertically (e.g., 8)",
    "DWSTRETCH": "Changes the image width digitally",
    "DWCROP": "Crops or stretches the screen horizontally",
    "SMOOTH": "Bilinear filter (removes aliasing/jagged edges)",
    "SCANLINES": "Simulates CRT TV scanlines",
    "WIDESCREEN": "Native widescreen screen hack (16:9)",
    "ULTRA_WIDESCREEN": "Screen hack for UltraWide ratio",
    "EYEFINITY": "Display hack for multiple monitors (3 screens)",
    "MUTE_CDDA": "Disables CDDA audio track playback",
    "UNDO_MUTE_CDDA": "Forces CDDA audio track re-enabling",
    "D2LS": "Maps the D-Pad layout to the Left Analog Stick",
    "D2LS_ALT": "Alternative D-Pad to Analog mapping layout",
    "CACHE1": "Reduces cache to 1 sector (improves USB reading)",
    "USBDELAY": "Sets USB delay time in seconds (e.g., 4)",
    "NOIGR": "Disables In-Game Reset button combination",
    "UNDO_GAME_FIXES": "Disables default emulator automatic fixes",
}

STATE = {}
VAL_STATE = {}
LANG = "EN"
CHEATS_FILE = None
POPS_DIR = None
BASE_POPSDIR = None


def clear():
    os.system("clear" if os.name != "nt" else "cls")


def detect_storage():
    candidates = [
        "/sdcard",
        "/storage/emulated/0",
        os.environ.get("EXTERNAL_STORAGE", ""),
        str(Path.home() / "storage" / "shared"),
    ]
    for c in candidates:
        if c and Path(c).is_dir():
            return Path(c)
    return Path("/sdcard")


def load_state():
    global CHEATS_FILE
    if CHEATS_FILE is None:
        return
    p = Path(CHEATS_FILE)
    if not p.is_file():
        return
    with p.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line.startswith("$"):
                continue
            k = line[1:]
            is_val = False
            for vk in KEYS_VAL:
                if k.startswith(f"{vk}_"):
                    VAL_STATE[vk] = k.split("_", 1)[1]
                    is_val = True
                    break
            if not is_val:
                STATE[k] = 1


def save_state():
    global CHEATS_FILE
    if CHEATS_FILE is None:
        return
    p = Path(CHEATS_FILE)
    entries = set()
    for k, v in STATE.items():
        if v == 1:
            entries.add(f"${k}")
    for vk in KEYS_VAL:
        if VAL_STATE.get(vk):
            entries.add(f"${vk}_{VAL_STATE[vk]}")
            
    p.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(sorted(entries)) + "\n" if entries else ""
    p.write_text(content, encoding="utf-8")


def select_lang():
    global LANG
    clear()
    print("1) Português (BR)")
    print("2) English")
    l = input("Select Language / Selecione o Idioma: ").strip()
    LANG = "PT" if l == "1" else "EN"


def ask_operation(target_dir: Path):
    global CHEATS_FILE
    while True:
        clear()
        bname = target_dir.name
        if LANG == "PT":
            print(f"=== PASTA SELECIONADA: {bname} ===")
            print("1) Copiar os cheats globais para a pasta selecionada e modificar")
            print("2) Criar um arquivo CHEATS.TXT personalizável?")
            op = input("Escolha uma opção: ").strip()
        else:
            print(f"=== SELECTED FOLDER: {bname} ===")
            print("1) Copy global cheats to the selected folder and modify")
            print("2) Create a customizable CHEATS.TXT file?")
            op = input("Choose an option: ").strip()
        if op == "1":
            global_cheats = POPS_DIR / "CHEATS.TXT"
            dest = target_dir / "CHEATS.TXT"
            if global_cheats.is_file():
                try:
                    shutil.copy2(str(global_cheats), str(dest))
                except Exception:
                    dest.write_text("", encoding="utf-8")
            else:
                dest.write_text("", encoding="utf-8")
            CHEATS_FILE = str(dest)
            break
        elif op == "2":
            CHEATS_FILE = str(target_dir / "CHEATS.TXT")
            break


def select_folder():
    global CHEATS_FILE
    while True:
        clear()
        print("=== SELECIONE A PASTA DO JOGO ===" if LANG == "PT" else "=== SELECT GAME FOLDER ===")
        dirs = []
        if POPS_DIR.exists():
            dirs = sorted([p for p in POPS_DIR.iterdir() if p.is_dir()])
        if not dirs:
            if LANG == "PT":
                print(f"Nenhuma pasta de jogo encontrada em: {POPS_DIR}")
                print("Gerenciando arquivo raiz padrão.")
            else:
                print(f"No game folders found in: {POPS_DIR}")
                print("Managing default root file.")
            time.sleep(2)
            CHEATS_FILE = str(POPS_DIR / "CHEATS.TXT")
            return
        for idx, d in enumerate(dirs, 1):
            print(f"{idx}) {d.name}")
            
        if LANG == "PT":
            print("0) Usar arquivo raiz da pasta POPS (Global)")
            choice = input("Selecione a pasta (ou 0): ").strip()
        else:
            print("0) Use root file inside POPS folder (Global)")
            choice = input("Select folder (or 0): ").strip()
        if choice == "0":
            CHEATS_FILE = str(POPS_DIR / "CHEATS.TXT")
            return
        if choice.isdigit():
            n = int(choice)
            if 1 <= n <= len(dirs):
                ask_operation(dirs[n - 1])
                return


def prompt_value(key: str):
    clear()
    cur = VAL_STATE.get(key, None)
    if LANG == "PT":
        print("=== CONFIGURAR VALOR DE TELA / SISTEMA ===")
        print(f"Modificador selecionado: ${key}")
        print(f"Valor atual: {cur if cur is not None else 'Não definido (Desativado)'}")
        print("------------------------------------------")
        print("Deixe EM BRANCO e pressione Enter para desativar.")
        val = input("Digite o novo valor para este cheat: ").strip()
    else:
        print("=== CONFIGURE SCREEN / SYSTEM VALUE ===")
        print(f"Selected modifier: ${key}")
        print(f"Current value: {cur if cur is not None else 'Not set (Disabled)'}")
        print("------------------------------------------")
        print("Leave BLANK and press Enter to disable.")
        val = input("Enter the new value for this cheat: ").strip()
    if not val:
        VAL_STATE.pop(key, None)
    else:
        VAL_STATE[key] = val


def prompt_custom_hex():
    clear()
    if LANG == "PT":
        print("=== COMPATIBILIDADE HEX CUSTOMIZADA ===")
        print("Insira um valor hexadecimal válido de 0x00 a 0xFF")
        print("Exemplos comuns de bits: 20, 80, C0")
        print("------------------------------------------")
        hex_in = input("Digite os dois caracteres HEX (ex: 20): ").strip()
    else:
        print("=== CUSTOM HEX COMPATIBILITY ===")
        print("Insert a valid hexadecimal value from 0x00 to 0xFF")
        print("Common bit examples: 20, 80, C0")
        print("------------------------------------------")
        hex_in = input("Enter the two HEX characters (e.g., 20): ").strip()
    hex_norm = hex_in.replace(" ", "").upper().lstrip("0X")
    if HEX_VALIDATOR.match(hex_norm):
        STATE[f"COMPATIBILITY_0x{hex_norm}"] = 1
    else:
        print("Valor Inválido!" if LANG == "PT" else "Invalid Value!")
        time.sleep(1.5)


def run_submenu(name_pt: str, name_en: str, arr):
    is_compat_menu = (arr == SUB_COMPAT)
    desc_dict = DESC_PT if LANG == "PT" else DESC_EN
    while True:
        clear()
        title = name_pt if LANG == "PT" else name_en
        print("=" * 57)
        print(f" CATEGORIA: {title}" if LANG == "PT" else f" CATEGORY: {title}")
        print(" 0) Voltar ao Menu Principal" if LANG == "PT" else " 0) Back to Main Menu")
        print("=" * 57)
        for idx, k in enumerate(arr, 1):
            if k in KEYS_VAL:
                val = VAL_STATE.get(k)
                status = f"[={val}]" if val else "[ ]"
                prefix = f"${k}_valor"
            else:
                status = "[*]" if STATE.get(k) == 1 else "[ ]"
                prefix = f"${k}"
            desc = desc_dict.get(k, "")
            print(f"{idx}) {status} {prefix} -> {desc}")
        idx = len(arr) + 1
        if is_compat_menu:
            custom_msg = "$COMPATIBILITY_0x## -> Adicionar modo Hex customizado" if LANG == "PT" else "$COMPATIBILITY_0x## -> Add custom Hex mode"
            print(f"{idx}) [ ] {custom_msg}")
        print("-" * 57)
        choice = input("> ").strip()
        if choice in ("", "0"):
            break
        if choice.isdigit():
            n = int(choice)
            if is_compat_menu and n == idx:
                prompt_custom_hex()
                continue
            if 1 <= n < idx:
                target_key = arr[n - 1]
                if target_key in KEYS_VAL:
                    prompt_value(target_key)
                else:
                    STATE[target_key] = 0 if STATE.get(target_key) == 1 else 1


def verify():
    clear()
    print("=========================================")
    print("      RESUMO DOS CHEATS SELECIONADOS" if LANG == "PT" else "      SUMMARY OF SELECTED CHEATS")
    print("=========================================")
    count = 0
    for k in sorted(STATE.keys()):
        if STATE.get(k) == 1:
            print(f"${k}")
            count += 1
    for vk in KEYS_VAL:
        if VAL_STATE.get(vk):
            print(f"${vk}_{VAL_STATE[vk]}")
            count += 1
    if count == 0:
        print("(Nenhum cheat ativo)" if LANG == "PT" else "(No active cheats)")
    print("=========================================")
    input("Pressione Enter..." if LANG == "PT" else "Press Enter...")


def menu():
    while True:
        clear()
        print("=" * 57)
        print("              POPSTARTER CHEATS MANAGER")
        print("=" * 57)
        if LANG == "PT":
            print("1) Modos de Compatibilidade")
            print("2) Configurações de Vídeo e Tela (Valores Customizados)")
            print("3) Filtros e Hacks Gráficos")
            print("4) Ajustes de Áudio e Controles")
            print("5) Opções de Sistema e Boot (Valores Customizados)")
            print("-" * 57)
            print("V) Verificar lista de cheats ativos no momento")
            print("0) Salvar modificações e Sair")
        else:
            print("1) Compatibility Modes")
            print("2) Video & Screen Options (Custom Values)")
            print("3) Graphical Hacks & Filters")
            print("4) Audio & Controls Remapping")
            print("5) System & Boot Tweaks (Custom Values)")
            print("-" * 57)
            print("V) Verify currently active cheats list")
            print("0) Save modifications and Exit")
        print("=" * 57)
        opt = input("Selecione uma categoria: " if LANG == "PT" else "Select a category: ").strip()
        if opt == "1":
            run_submenu("Modos de Compatibilidade", "Compatibility Modes", SUB_COMPAT)
        elif opt == "2":
            run_submenu("Vídeo e Ajustes de Tela", "Video & Screen Options", SUB_VIDEO)
        elif opt == "3":
            run_submenu("Filtros e Hacks Gráficos", "Graphical Hacks & Filters", SUB_GRAPH)
        elif opt == "4":
            run_submenu("Áudio e Controles", "Audio & Controls", SUB_AUDIO_CTRL)
        elif opt == "5":
            run_submenu("Ajustes de Sistema", "System Tweaks", SUB_SYS)
        elif opt.lower() == "v":
            verify()
        elif opt == "0":
            break


if __name__ == "__main__":
    clear()
    print("V0.0.1")
    time.sleep(1)
    clear()

    BASE_POPSDIR = detect_storage()
    POPS_DIR = BASE_POPSDIR / "Download" / "POPS2" / ".POPSTARTER" / "POPS"
    if not POPS_DIR.exists():
        alt = BASE_POPSDIR / "Download" / "POPS" / ".POPSTARTER" / "POPS"
        if alt.exists():
            POPS_DIR = alt
    POPS_DIR.mkdir(parents=True, exist_ok=True)

    select_lang()
    select_folder()
    load_state()
    menu()
    save_state()
    verify()
    clear()
    print("Saved. Exiting.")
    time.sleep(0.5)
