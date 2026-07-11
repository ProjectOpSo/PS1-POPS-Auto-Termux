#!/bin/bash

echo "V.0.0.3"

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
        [ -e "$cue" ] || continue
        local stem="${cue##*/}"
        stem="${stem%.cue}"
        
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
    local TMP_WORK_DIR="$POPS2_DIR/.tmp_conv"
    mkdir -p "$TMP_WORK_DIR"

    if [ ! -x "$CUE2POPS" ]; then
        rm -rf "$TMP_WORK_DIR"
        return 1
    fi

    for cue in "$JPS1_DIR"/*.cue; do
        [ -e "$cue" ] || continue
        local stem="${cue##*/}"
        stem="${stem%.cue}"
        local out="$VPS1_DIR/$stem.VCD"
        
        if [ -f "$out" ]; then
            continue
        fi
        
        nice -n 19 timeout 15m "$CUE2POPS" "$cue" "$TMP_WORK_DIR/$stem.VCD" >/dev/null 2>&1
        
        if [ -s "$TMP_WORK_DIR/$stem.VCD" ]; then
            mv "$TMP_WORK_DIR/$stem.VCD" "$out" 2>/dev/null
            rm -f "$JPS1_DIR/$stem.cue" 2>/dev/null
            rm -f "$JPS1_DIR/$stem.bin" 2>/dev/null
        fi
        
        rm -f "$TMP_WORK_DIR/$stem"* 2>/dev/null
        sync
        sleep 1
    done

    rm -rf "$TMP_WORK_DIR"
}

rename_and_move_to_rps1() {
    for vcd in "$VPS1_DIR"/*.VCD; do
        [ -e "$vcd" ] || continue
        local base_vcd="${vcd##*/}"
        local file_name="${base_vcd%.VCD}"
        
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

    > "$CONF_APPS"
    
    local games_file
    games_file=$(mktemp)

    for vcd in "$RPS1_DIR"/*.VCD; do
        [ -e "$vcd" ] || continue
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
        sort -t'|' -k1,1 "$games_file" | while IFS='|' read -r disp_name file_name; do
            if [ -n "$disp_name" ]; then
                echo "$disp_name=mass:/APPS/XX.$file_name.ELF"
            fi
        done >> "$CONF_APPS"
    fi
    
    rm -f "$games_file"
}

main() {
    trap 'rm -rf "$POPS2_DIR/.tmp_conv"; shopt -u nullglob' EXIT INT TERM
    shopt -s nullglob
    
    mkdir -p "$POPS2_DIR" "$JPS1_DIR" "$MPS1_DIR" "$VPS1_DIR" "$RPS1_DIR" "$PS1M_DIR"
    mkdir -p "$POPSTARTER_FINAL_DIR" "$FINAL_POPS_DIR" "$FINAL_APPS_DIR"

    merge_multi_bin_games
    convert_games
    rename_and_move_to_rps1
    build_final_structure
    
    echo "END"
    shopt -u nullglob
}

main
