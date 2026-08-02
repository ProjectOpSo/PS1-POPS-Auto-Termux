# PS1-POPS-Auto-Termux

Um conjunto de ferramentas automatizadas para converter jogos de PlayStation 1 para o formato POPStarter diretamente do Termux no Android.

O script `ps1popsauto.py` automatiza todo o processo de conversão, incluindo a mesclagem de faixas múltiplas, criação de VCD, sanitização de nomes de arquivo e geração da pasta POPStarter.

---

## Estrutura do Projeto

```text
PS1-POPS-Auto-Termux/
├── cue2pops-linux/      # código fonte do cue2pops compilado para Termux
├── binmerge/            # mesclador de BIN para múltiplas faixas
├── POPS-binaries/       # binários do POPStarter e arquivos BIOS
└── ps1popsauto.py       # script principal de automação
```

---

## Armazenamento no Android

O script usa automaticamente:
`/sdcard/Download/POPS2`

### Estrutura de pastas:
```text
POPS2/
├── JPS1/          # Jogos PS1 originais (.cue/.bin)
├── MPS1/          # Arquivos BIN mesclados temporários
├── VPS1/          # Arquivos VCD gerados
├── RPS1/          # Arquivos VCD renomeados
├── PS1M/          # Template de Memory Card virtual
└── .POPSTARTER/   # Saída final do POPStarter
```

---

## Instalação

### 1. Conceder permissão de armazenamento

```bash
termux-setup-storage
```

### 2. Instalar dependências e clonar este repositório

```bash
pkg update -y && \
pkg upgrade -y && \
pkg install -y git make clang python ffmpeg && \
git clone https://github.com/ProjectOpSo/PS1-POPS-Auto-Termux.git && \
cd PS1-POPS-Auto-Termux && \
git clone https://github.com/makefu/cue2pops-linux.git cue2pops-linux && \
git clone https://github.com/putnam/binmerge.git && \
git clone https://github.com/AnimMouse/POPS-binaries.git && \
cd cue2pops-linux && \
make && \
chmod +x cue2pops && \
cd .. && \
chmod +x ps1popsauto.py cheats.sh
```

## Para atualizar

```bash
cd $HOME && \
rm -rf PS1-POPS-Auto-Termux && \
pkg update -y && \
pkg upgrade -y && \
pkg install -y git make clang python ffmpeg && \
git clone https://github.com/ProjectOpSo/PS1-POPS-Auto-Termux.git && \
cd PS1-POPS-Auto-Termux && \
git clone https://github.com/makefu/cue2pops-linux.git cue2pops-linux && \
git clone https://github.com/putnam/binmerge.git && \
git clone https://github.com/AnimMouse/POPS-binaries.git && \
cd cue2pops-linux && \
make && \
chmod +x cue2pops && \
cd .. && \
chmod +x ps1popsauto.py cheats.sh
```

## Executar

```
./ps1popsauto.py
```

## Cheats

```
./cheats.sh
```

**O script realiza automaticamente:**
* Mesclagem de jogos com múltiplas faixas.
* Download das capas.
* Conversão para `.VCD`.
* Renomeação de nomes de arquivos incompatíveis.
* Montagem completa da pasta POPStarter.
* Geração da pasta final `.POPSTARTER`.

---

## Créditos

* **makefu** — [cue2pops-linux](https://github.com/makefu/cue2pops-linux.git)  
  * Implementação em C portátil do `cue2pops`.

* **putnam** — [binmerge](https://github.com/putnam/binmerge)  
  * Mesclador de imagens de PlayStation com múltiplas faixas.

* **AnimMouse** — [POPS-binaries](https://github.com/AnimMouse/POPS-binaries)  
  * Binários e arquivos de suporte necessários para o POPStarter.

* **xlenore** — [psx-covers](https://github.com/xlenore/psx-covers)  
  * Capas para jogos de PlayStation 1.
