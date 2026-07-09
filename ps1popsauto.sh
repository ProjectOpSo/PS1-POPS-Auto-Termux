#!/bin/bash

clear
echo "V.0.0.2"
sleep 5
clear

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
POPS2_DIR="$BASE/Download/POPS2"

JPS1_DIR="$POPS2_DIR/JPS1"
MPS1_DIR="$POPS2_DIR/MPS1"
VPS1_DIR="$POPS2_DIR/VPS1"
RPS1_DIR="$POPS2_DIR/RPS1"
PS1M_DIR="$POPS2_DIR/PS1M"

POPSTARTER_FINAL_DIR="$POPS2_DIR/.POPSTARTER"
FINAL_POPS_DIR="$POPSTARTER_FINAL_DIR/POPS"
FINAL_APPS_DIR="$POPSTARTER_FINAL_DIR/APPS"
CONF_APPS="$POPSTARTER_FINAL_DIR/conf_apps.cfg"

POPS_ELF="$POPS2_DIR/POPSTARTER.ELF"
REPO_DIR="./POPS-binaries"
CUE2POPS="./cue2pops-linux/cue2pops"
BINMERGE="./binmerge/binmerge"

merge_multi_bin_games() {
    if [ ! -x "$BINMERGE" ] && [ -f "./binmerge/binmerge.py" ]; then
        BINMERGE="python ./binmerge/binmerge.py"
    fi

    for cue in "$JPS1_DIR"/*.cue; do
        local stem="${cue##*/}"
        stem="${stem%.cue}"
        
        # Parse the .cue file internally using native regex matching
        local bin_files=()
        while IFS= read -r line; do
            if [[ "$line" =~ FILE[[:space:]]+\"([^\"]+)\" ]]; then
                bin_files+=("${BASH_REMATCH[1]}")
            fi
        done < "$cue"

        if [ "${#bin_files[@]}" -gt 1 ]; then
            for bin_file in "${bin_files[@]}"; do
                mv "$JPS1_DIR/$bin_file" "$MPS1_DIR/" 2>/dev/null
            done
            mv "$cue" "$MPS1_DIR/" 2>/dev/null

            if $BINMERGE --outdir "$JPS1_DIR" "$MPS1_DIR/$stem.cue" "$stem" >/dev/null 2>&1; then
                rm -f "$MPS1_DIR/$stem"* 2>/dev/null
            else
                mv "$MPS1_DIR/$stem"* "$JPS1_DIR/" 2>/dev/null
            fi
        fi
    done
}

convert_games() {
    for cue in "$JPS1_DIR"/*.cue; do
        local stem="${cue##*/}"
        stem="${stem%.cue}"
        local out="$VPS1_DIR/$stem.VCD"
        
        if [ -f "$out" ]; then
            continue
        fi
        
        if [ ! -x "$CUE2POPS" ]; then
            return 1
        fi
        
        "$CUE2POPS" "$cue" "$out" >/dev/null 2>&1
        
        if [ -s "$out" ]; then
            rm -f "$JPS1_DIR/$stem.cue" 2>/dev/null
            rm -f "$JPS1_DIR/$stem.bin" 2>/dev/null
        fi
    done
}

rename_and_move_to_rps1() {
    for vcd in "$VPS1_DIR"/*.VCD; do
        local base_vcd="${vcd##*/}"
        local file_name="${base_vcd%.VCD}"
        
        # Native global regex substitution completely replaces sed
        file_name="${file_name//[^[:alnum:]]/}"
        mv "$vcd" "$RPS1_DIR/$file_name.VCD" 2>/dev/null
    done
}

build_final_structure() {
    if [ -d "$REPO_DIR" ]; then
        for bin_file in "$REPO_DIR"/*; do
            if [ -f "$bin_file" ]; then
                local b_name="${bin_file##*/}"
                if [ ! -f "$FINAL_POPS_DIR/$b_name" ]; then
                    cp "$bin_file" "$FINAL_POPS_DIR/" 2>/dev/null
                fi
            fi
        done
    fi

    # Native truncation creates or empties the file without launching touch/rm
    > "$CONF_APPS"
    
    local games_file
    games_file=$(mktemp)

    for vcd in "$RPS1_DIR"/*.VCD; do
        local base_vcd="${vcd##*/}"
        local file_name="${base_vcd%.*}"

        mv "$vcd" "$FINAL_POPS_DIR/" 2>/dev/null
        echo "$file_name|$file_name" >> "$games_file"
        
        if [ -d "$PS1M_DIR" ]; then
            local dest_mem="$FINAL_POPS_DIR/$file_name"
            mkdir -p "$dest_mem"
            cp -r "$PS1M_DIR"/. "$dest_mem/" 2>/dev/null
        fi
    done

    if [ -f "$POPS_ELF" ] && [ -s "$games_file" ]; then
        while IFS='|' read -r disp_name file_name; do
            if [ -n "$file_name" ]; then
                local elf_name="XX.$file_name.ELF"
                cp "$POPS_ELF" "$FINAL_APPS_DIR/$elf_name" 2>/dev/null
            fi
        done < "$games_file"
    fi
    
    if [ -s "$games_file" ]; then
        # Grouped loop redirection streams the batch out to the file in one single write command
        sort -t'|' -k1,1 "$games_file" | while IFS='|' read -r disp_name file_name; do
            if [ -n "$disp_name" ]; then
                echo "$disp_name=mass:/APPS/XX.$file_name.ELF"
            fi
        done >> "$CONF_APPS"
    fi
    
    rm -f "$games_file"
}

main() {
    # Enabled globally for the runtime scope of the script setup
    shopt -s nullglob
    
    mkdir -p "$POPS2_DIR" "$JPS1_DIR" "$MPS1_DIR" "$VPS1_DIR" "$RPS1_DIR" "$PS1M_DIR"
    mkdir -p "$POPSTARTER_FINAL_DIR" "$FINAL_POPS_DIR" "$FINAL_APPS_DIR"

    merge_multi_bin_games
    convert_games
    rename_and_move_to_rps1
    build_final_structure
    
    clear
    echo "END"
    shopt -u nullglob
}

main
