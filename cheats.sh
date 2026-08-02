#!/bin/bash

detect_storage() {
    local candidates=("/sdcard" "/storage/emulated/0" "$EXTERNAL_STORAGE" "$HOME/storage/shared")
    for c in "${candidates[@]}"; do
        if [ -n "$c" ] && [ -d "$c" ]; then
            echo "$c"
            return 0
        fi
    done
    echo "/sdcard"
}

BASE=$(detect_storage)
POPS_DIR="$BASE/Download/POPS2/.POPSTARTER/POPS"
mkdir -p "$POPS_DIR"

declare -A STATE
declare -A VAL_STATE
declare -A DESC_PT
declare -A DESC_EN

KEYS_VAL=("XPOS" "YPOS" "DWSTRETCH" "DWCROP" "USBDELAY")

SUB_COMPAT=("SAFEMODE" "FAKELC" "COMPATIBILITY_0x01" "COMPATIBILITY_0x02" "COMPATIBILITY_0x03" "COMPATIBILITY_0x04" "COMPATIBILITY_0x05" "COMPATIBILITY_0x06" "COMPATIBILITY_0x07")
SUB_VIDEO=("480p" "HDTVFIX" "NOPAL" "FORCEPAL" "XPOS" "YPOS" "DWSTRETCH" "DWCROP")
SUB_GRAPH=("SMOOTH" "SCANLINES" "WIDESCREEN" "ULTRA_WIDESCREEN" "EYEFINITY")
SUB_AUDIO_CTRL=("MUTE_CDDA" "UNDO_MUTE_CDDA" "D2LS" "D2LS_ALT")
SUB_SYS=("CACHE1" "USBDELAY" "NOIGR" "UNDO_GAME_FIXES")

DESC_PT[SAFEMODE]="Modo de segurança (evita travamentos no boot)"
DESC_EN[SAFEMODE]="Safe mode (prevents boot freezes)"
DESC_PT[FAKELC]="Simula a proteção LibCrypt (jogos europeus protegidos)"
DESC_EN[FAKELC]="Simulates LibCrypt protection (protected PAL games)"
DESC_PT[COMPATIBILITY_0x01]="Corrige áudio (restaura músicas e vozes)"
DESC_EN[COMPATIBILITY_0x01]="Fixes audio (restores music and voices)"
DESC_PT[COMPATIBILITY_0x02]="Variante do 0x01 (mantém FMVs - ex: Colony Wars)"
DESC_EN[COMPATIBILITY_0x02]="Variant of 0x01 (keeps FMVs working - e.g., Colony Wars)"
DESC_PT[COMPATIBILITY_0x03]="Alternativa de áudio para jogos específicos"
DESC_EN[COMPATIBILITY_0x03]="Alternative audio fix for specific games"
DESC_PT[COMPATIBILITY_0x04]="Corrige bugs gráficos, lentidão e flickering (Mais Usado)"
DESC_EN[COMPATIBILITY_0x04]="Fixes graphics bugs, slowdown, and flickering (Most Used)"
DESC_PT[COMPATIBILITY_0x05]="Corrige cutscenes (ex: Resident Evil Director's Cut)"
DESC_EN[COMPATIBILITY_0x05]="Fixes cutscenes (e.g., Resident Evil Director's Cut)"
DESC_PT[COMPATIBILITY_0x06]="Desativa o OSD da BIOS virtual (evita travar no boot)"
DESC_EN[COMPATIBILITY_0x06]="Disables virtual BIOS OSD (prevents boot freeze)"
DESC_PT[COMPATIBILITY_0x07]="Modo não documentado oficialmente"
DESC_EN[COMPATIBILITY_0x07]="Officially undocumented mode"

DESC_PT[480p]="Força saída de vídeo em 480p"
DESC_EN[480p]="Forces 480p video output"
DESC_PT[HDTVFIX]="Corrige tela verde/preta/distorcida em TVs modernas"
DESC_EN[HDTVFIX]="Fixes green/black/distorted screens on modern TVs"
DESC_PT[NOPAL]="Desativa o patch automático PAL"
DESC_EN[NOPAL]="Disables automatic PAL patch"
DESC_PT[FORCEPAL]="Força o modo de vídeo PAL"
DESC_EN[FORCEPAL]="Forces PAL video mode"
DESC_PT[XPOS]="Move a imagem horizontalmente (Ex: 620)"
DESC_EN[XPOS]="Moves image horizontally (e.g., 620)"
DESC_PT[YPOS]="Move a imagem verticalmente (Ex: 8)"
DESC_EN[YPOS]="Moves image vertically (e.g., 8)"
DESC_PT[DWSTRETCH]="Altera a largura da imagem digitalmente"
DESC_EN[DWSTRETCH]="Changes the image width digitally"
DESC_PT[DWCROP]="Recorta ou amplia a tela horizontalmente"
DESC_EN[DWCROP]="Crops or stretches the screen horizontally"

DESC_PT[SMOOTH]="Filtro bilinear (remove serrilhados dos jogos)"
DESC_EN[SMOOTH]="Bilinear filter (removes aliasing/jagged edges)"
DESC_PT[SCANLINES]="Simula linhas de varredura de TV CRT"
DESC_EN[SCANLINES]="Simulates CRT TV scanlines"
DESC_PT[WIDESCREEN]="Hack de tela widescreen nativo (16:9)"
DESC_EN[WIDESCREEN]="Native widescreen screen hack (16:9)"
DESC_PT[ULTRA_WIDESCREEN]="Hack de tela para proporção UltraWide"
DESC_EN[ULTRA_WIDESCREEN]="Screen hack for UltraWide ratio"
DESC_PT[EYEFINITY]="Hack de exibição para múltiplos monitores (3 telas)"
DESC_EN[EYEFINITY]="Display hack for multiple monitors (3 screens)"

DESC_PT[MUTE_CDDA]="Desativa a reprodução de faixas de música CDDA"
DESC_EN[MUTE_CDDA]="Disables CDDA audio track playback"
DESC_PT[UNDO_MUTE_CDDA]="Força a reativação de músicas CDDA"
DESC_EN[UNDO_MUTE_CDDA]="Forces CDDA audio track re-enabling"
DESC_PT[D2LS]="Mapeia o D-Pad para o Analógico Esquerdo"
DESC_EN[D2LS]="Maps the D-Pad layout to the Left Analog Stick"
DESC_PT[D2LS_ALT]="Mapeamento alternativo do D-Pad para Analógico"
DESC_EN[D2LS_ALT]="Alternative D-Pad to Analog mapping layout"

DESC_PT[CACHE1]="Reduz cache para 1 setor (melhora leitura via USB)"
DESC_EN[CACHE1]="Reduces cache to 1 sector (improves USB reading)"
DESC_PT[USBDELAY]="Define o tempo de atraso do USB em segundos (Ex: 4)"
DESC_EN[USBDELAY]="Sets USB delay time in seconds (e.g., 4)"
DESC_PT[NOIGR]="Desativa o In-Game Reset (Combinação de botões de sair)"
DESC_EN[NOIGR]="Disables In-Game Reset button combination"
DESC_PT[UNDO_GAME_FIXES]="Desativa correções automáticas padrões do emulador"
DESC_EN[UNDO_GAME_FIXES]="Disables default emulator automatic fixes"

select_lang() {
    clear
    echo "1) Português (BR)"
    echo "2) English"
    read -rp "Select Language / Selecione o Idioma: " l
    if [ "$l" = "1" ]; then LANG="PT"; else LANG="EN"; fi
}

ask_operation() {
    local target_dir="$1"
    while true; do
        clear
        local bname=$(basename "$target_dir")
        if [ "$LANG" = "PT" ]; then
            echo "=== PASTA SELECIONADA: $bname ==="
            echo "1) Copiar os cheats globais para a pasta selecionada e modificar"
            echo "2) Criar um arquivo CHEATS.TXT personalizável?"
            read -rp "Escolha uma opção: " op
        else
            echo "=== SELECTED FOLDER: $bname ==="
            echo "1) Copy global cheats to the selected folder and modify"
            echo "2) Create a customizable CHEATS.TXT file?"
            read -rp "Choose an option: " op
        fi
        if [ "$op" = "1" ]; then
            if [ -f "$POPS_DIR/CHEATS.TXT" ]; then
                cp "$POPS_DIR/CHEATS.TXT" "$target_dir/CHEATS.TXT"
            else
                touch "$target_dir/CHEATS.TXT"
            fi
            CHEATS_FILE="$target_dir/CHEATS.TXT"
            break
        elif [ "$op" = "2" ]; then
            CHEATS_FILE="$target_dir/CHEATS.TXT"
            break
        fi
    done
}

select_folder() {
    while true; do
        clear
        if [ "$LANG" = "PT" ]; then
            echo "=== SELECIONE A PASTA DO JOGO ==="
        else
            echo "=== SELECT GAME FOLDER ==="
        fi
        local dirs=()
        local idx=1
        for d in "$POPS_DIR"/*/; do
            if [ -d "$d" ]; then
                dirs+=("$d")
                local bname=$(basename "$d")
                echo "$idx) $bname"
                idx=$((idx+1))
            fi
        done
        if [ ${#dirs[@]} -eq 0 ]; then
            if [ "$LANG" = "PT" ]; then
                echo "Nenhuma pasta de jogo encontrada em: $POPS_DIR"
                echo "Gerenciando arquivo raiz padrão."
            else
                echo "No game folders found in: $POPS_DIR"
                echo "Managing default root file."
            fi
            sleep 3
            CHEATS_FILE="$POPS_DIR/CHEATS.TXT"
            return
        fi
        if [ "$LANG" = "PT" ]; then
            echo "0) Usar arquivo raiz da pasta POPS (Global)"
            read -rp "Selecione a pasta (ou 0): " choice
        else
            echo "0) Use root file inside POPS folder (Global)"
            read -rp "Select folder (or 0): " choice
        fi
        if [ "$choice" = "0" ]; then
            CHEATS_FILE="$POPS_DIR/CHEATS.TXT"
            return
        fi
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -lt "$idx" ]; then
            local sel_dir="${dirs[$((choice-1))]}"
            ask_operation "$sel_dir"
            return
        fi
    done
}

load_state() {
    [ -f "$CHEATS_FILE" ] || return
    while IFS= read -r line; do
        line=$(echo "$line" | tr -d '\r' | xargs)
        [[ "$line" =~ ^\$ ]] || continue
        local k="${line#\$}"
        local is_val=0
        for vk in "${KEYS_VAL[@]}"; do
            if [[ "$k" =~ ^${vk}_(.+)$ ]]; then
                VAL_STATE["$vk"]="${BASH_REMATCH[1]}"
                is_val=1
                break
            fi
        done
        if [ $is_val -eq 0 ]; then
            STATE["$k"]=1
        fi
    done < "$CHEATS_FILE"
}

save_state() {
    : > "$CHEATS_FILE"
    for k in "${!STATE[@]}"; do
        if [ "${STATE[$k]}" = "1" ]; then
            echo "\$$k" >> "$CHEATS_FILE"
        fi
    done
    for vk in "${KEYS_VAL[@]}"; do
        if [ -n "${VAL_STATE[$vk]}" ]; then
            echo "\$${vk}_${VAL_STATE[$vk]}" >> "$CHEATS_FILE"
        fi
    done
    if [ -s "$CHEATS_FILE" ]; then
        sort -u "$CHEATS_FILE" -o "$CHEATS_FILE"
    fi
}

prompt_value() {
    local key="$1"
    clear
    if [ "$LANG" = "PT" ]; then
        echo "=== CONFIGURAR VALOR DE TELA / SISTEMA ==="
        echo "Modificador selecionado: \$$key"
        echo "Valor atual: ${VAL_STATE[$key]:-Não definido (Desativado)}"
        echo "------------------------------------------"
        echo "Deixe EM BRANCO e pressione Enter para desativar."
        read -rp "Digite o novo valor para este cheat: " val
    else
        echo "=== CONFIGURE SCREEN / SYSTEM VALUE ==="
        echo "Selected modifier: \$$key"
        echo "Current value: ${VAL_STATE[$key]:-Not set (Disabled)}"
        echo "------------------------------------------"
        echo "Leave BLANK and press Enter to disable."
        read -rp "Enter the new value for this cheat: " val
    fi
    val=$(echo "$val" | xargs)
    if [ -z "$val" ]; then
        unset "VAL_STATE[$key]"
    else
        VAL_STATE["$key"]="$val"
    fi
}

prompt_custom_hex() {
    clear
    if [ "$LANG" = "PT" ]; then
        echo "=== COMPATIBILIDADE HEX CUSTOMIZADA ==="
        echo "Insira um valor hexadecimal válido de 0x00 a 0xFF"
        echo "Exemplos comuns de bits: 20, 80, C0"
        echo "------------------------------------------"
        read -rp "Digite os dois caracteres HEX (ex: 20): " hex
    else
        echo "=== CUSTOM HEX COMPATIBILITY ==="
        echo "Insert a valid hexadecimal value from 0x00 to 0xFF"
        echo "Common bit examples: 20, 80, C0"
        echo "------------------------------------------"
        read -rp "Enter the two HEX characters (e.g., 20): " hex
    fi
    hex=$(echo "$hex" | tr -d ' ' | tr '[:lower:]' '[:upper:]')
    hex="${hex#0X}"
    if [[ "$hex" =~ ^[0-9A-F]{2}$ ]]; then
        STATE["COMPATIBILITY_0x$hex"]=1
    else
        if [ "$LANG" = "PT" ]; then echo "Valor Inválido!"; else echo "Invalid Value!"; fi
        sleep 1.5
    fi
}

run_submenu() {
    local name_pt="$1"
    local name_en="$2"
    local -n arr="$3"
    local is_compat_menu=0
    if [ "$3" = "SUB_COMPAT" ]; then is_compat_menu=1; fi
    while true; do
        clear
        if [ "$LANG" = "PT" ]; then
            echo "========================================================="
            echo " CATEGORIA: $name_pt"
            echo " 0) Voltar ao Menu Principal"
            echo "========================================================="
        else
            echo "========================================================="
            echo " CATEGORY: $name_en"
            echo " 0) Back to Main Menu"
            echo "========================================================="
        fi
        local idx=1
        for k in "${arr[@]}"; do
            local status="[ ]"
            local prefix="\$$k"
            local is_val_key=0
            for vk in "${KEYS_VAL[@]}"; do
                if [ "$vk" = "$k" ]; then is_val_key=1; break; fi
            done
            if [ $is_val_key -eq 1 ]; then
                if [ -n "${VAL_STATE[$k]}" ]; then
                    status="[=${VAL_STATE[$k]}]"
                fi
                prefix="\$${k}_valor"
            else
                if [ "${STATE[$k]}" = "1" ]; then
                    status="[*]"
                fi
            fi
            local desc="${DESC_PT[$k]}"
            if [ "$LANG" = "EN" ]; then desc="${DESC_EN[$k]}"; fi
            echo "$idx) $status $prefix -> $desc"
            idx=$((idx+1))
        done
        if [ $is_compat_menu -eq 1 ]; then
            if [ "$LANG" = "PT" ]; then
                echo "$idx) [ ] \$COMPATIBILITY_0x## -> Adicionar modo Hex customizado"
            else
                echo "$idx) [ ] \$COMPATIBILITY_0x## -> Add custom Hex mode"
            fi
        fi
        echo "---------------------------------------------------------"
        read -rp "> " choice
        if [ "$choice" = "0" ] || [ -z "$choice" ]; then break; fi
        if [[ "$choice" =~ ^[0-9]+$ ]]; then
            if [ $is_compat_menu -eq 1 ] && [ "$choice" -eq "$idx" ]; then
                prompt_custom_hex
                continue
            fi
            if [ "$choice" -ge 1 ] && [ "$choice" -lt "$idx" ]; then
                local target_key="${arr[$((choice-1))]}"
                local is_val_key=0
                for vk in "${KEYS_VAL[@]}"; do
                    if [ "$vk" = "$target_key" ]; then is_val_key=1; break; fi
                done
                if [ $is_val_key -eq 1 ]; then
                    prompt_value "$target_key"
                else
                    if [ "${STATE[$target_key]}" = "1" ]; then
                        STATE[$target_key]=0
                    else
                        STATE[$target_key]=1
                    fi
                fi
            fi
        fi
    done
}

verify() {
    clear
    if [ "$LANG" = "PT" ]; then
        echo "========================================="
        echo "      RESUMO DOS CHEATS SELECIONADOS"
        echo "========================================="
    else
        echo "========================================="
        echo "      SUMMARY OF SELECTED CHEATS"
        echo "========================================="
    fi
    local count=0
    for k in "${!STATE[@]}"; do
        if [ "${STATE[$k]}" = "1" ]; then
            echo "\$$k"
            count=$((count+1))
        fi
    done
    for vk in "${KEYS_VAL[@]}"; do
        if [ -n "${VAL_STATE[$vk]}" ]; then
            echo "\$${vk}_${VAL_STATE[$vk]}"
            count=$((count+1))
        fi
    done
    if [ $count -eq 0 ]; then
        if [ "$LANG" = "PT" ]; then echo "(Nenhum cheat ativo)"; else echo "(No active cheats)"; fi
    fi
    echo "========================================="
    read -rp "Press Enter / Pressione Enter..." ix
}

menu() {
    while true; do
        clear
        if [ "$LANG" = "PT" ]; then
            echo "========================================================="
            echo "              POPSTARTER CHEATS MANAGER"
            echo "========================================================="
            echo "1) Modos de Compatibilidade"
            echo "2) Configurações de Vídeo e Tela (Valores Customizados)"
            echo "3) Filtros e Hacks Gráficos"
            echo "4) Ajustes de Áudio e Controles"
            echo "5) Opções de Sistema e Boot (Valores Customizados)"
            echo "---------------------------------------------------------"
            echo "V) Verificar lista de cheats ativos no momento"
            echo "0) Salvar modificações e Sair"
            echo "========================================================="
            read -rp "Selecione uma categoria: " opt
        else
            echo "========================================================="
            echo "              POPSTARTER CHEATS MANAGER"
            echo "========================================================="
            echo "1) Compatibility Modes"
            echo "2) Video & Screen Options (Custom Values)"
            echo "3) Graphical Hacks & Filters"
            echo "4) Audio & Controls Remapping"
            echo "5) System & Boot Tweaks (Custom Values)"
            echo "---------------------------------------------------------"
            echo "V) Verify currently active cheats list"
            echo "0) Save modifications and Exit"
            echo "========================================================="
            read -rp "Select a category: " opt
        fi
        case "$opt" in
            1) run_submenu "Modos de Compatibilidade" "Compatibility Modes" SUB_COMPAT ;;
            2) run_submenu "Vídeo e Ajustes de Tela" "Video & Screen Options" SUB_VIDEO ;;
            3) run_submenu "Filtros e Hacks Gráficos" "Graphical Hacks & Filters" SUB_GRAPH ;;
            4) run_submenu "Áudio e Controles" "Audio & Controls" SUB_AUDIO_CTRL ;;
            5) run_submenu "Ajustes de Sistema" "System Tweaks" SUB_SYS ;;
            [vV]) verify ;;
            0) break ;;
        esac
    done
}

main() {
    clear
    echo "V0.0.1"
    sleep 5
    clear
    select_lang
    select_folder
    load_state
    menu
    save_state
    verify
}

main
