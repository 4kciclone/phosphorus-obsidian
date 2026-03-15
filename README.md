# 🟢 PHOSPHORUS OBSIDIAN — Instalador Automático

> Arch Linux + Hyprland + BlackArch + VirtualBox Rice  
> Cores: Verde Fósforo `#20c20e` · Fundo Obsidian `#0d1117`

---

## 📁 Ficheiros gerados

| Ficheiro | Função |
|---|---|
| `phosphorus_setup.py` | Script principal (instala TUDO) |
| `phosphorus_config.json` | Config do archinstall (disco, pacotes, rede…) |
| `phosphorus_credentials.json` | Utilizador + passwords |

---

## 🚀 Como usar no Live ISO do Arch

### Opção A — Script completo (recomendado)

Boot na ISO → confirma rede → corre numa linha:

```bash
curl -fsSL https://raw.githubusercontent.com/SEU_USER/SEU_REPO/main/phosphorus_setup.py | python -
```

Ou, se transferires o ficheiro para a VM:

```bash
python phosphorus_setup.py
```

O script faz tudo sozinho:
1. Gera os JSONs para o `archinstall`
2. Executa o `archinstall --silent`
3. Executa o `arch-chroot` com o script de pós-instalação
4. Reinicia a VM

---

### Opção B — Apenas gerar configs (sem instalar)

```bash
python phosphorus_setup.py --generate-only
```

Depois instala manualmente:

```bash
archinstall \
  --config /tmp/phosphorus_config.json \
  --creds /tmp/phosphorus_credentials.json \
  --silent

arch-chroot /mnt bash /tmp/phosphorus_postinstall.sh
```

---

### Opção C — Carregar configs no archinstall interativo

```bash
archinstall \
  --config /tmp/phosphorus_config.json \
  --creds /tmp/phosphorus_credentials.json
```

*(Remove `--silent` para ver o menu do archinstall com as opções pré-preenchidas)*

---

## 👤 Credenciais padrão

| Campo | Valor |
|---|---|
| Utilizador | `obsidian` |
| Password | `phosphorus` |
| Root pass | `phosphorus` |
| Hostname | `phosphorus-obsidian` |

> ⚠️ Muda as passwords após o primeiro boot: `passwd` e `sudo passwd root`

---

## ✅ O que é instalado

### Base
- Kernel `linux` estável
- Disco `/dev/sda` — GPT/EFI (500MB boot + 20GB root + resto /home)
- NetworkManager, PipeWire (áudio)

### Desktop
- **Hyprland** — compositor Wayland com bordas `#20c20e` e efeitos blur
- **Waybar** — barra de status com tema Obsidian
- **Kitty** — terminal com fonte JetBrainsMono Nerd
- **Rofi** — launcher de apps
- **swww** — wallpapers animados
- **dunst** — notificações

### Ferramentas
- **BlackArch** (repositório completo via strap.sh)
- **Starship** — prompt Zsh estilizado
- **Neovim**, git, base-devel, curl, wget

### VirtualBox
- `virtualbox-guest-utils` + `vboxservice` (clipboard, resize, etc.)
- `WLR_NO_HARDWARE_CURSORS=1` configurado para evitar problemas de cursor

---

## 🎮 Atalhos Hyprland

| Tecla | Ação |
|---|---|
| `Super + Enter` | Abre Kitty |
| `Super + D` | Rofi (launcher) |
| `Super + W` | Troca wallpaper (swww + Rofi) |
| `Super + Q` | Fecha janela |
| `Super + F` | Fullscreen |
| `Super + Shift + F` | Floating |
| `Super + 1-5` | Muda workspace |
| `Super + Shift + 1-5` | Move janela para workspace |

---

## 🖼️ Wallpapers

Coloca imagens em `~/Pictures/Wallpapers/` e usa `Super + W` para escolher via Rofi.

```bash
# Exemplo — download de um wallpaper
curl -o ~/Pictures/Wallpapers/meu_wp.jpg https://exemplo.com/wallpaper.jpg
```

---

## 🔧 Pós-boot (primeiros passos)

```bash
# Atualiza o sistema
sudo pacman -Syu

# Instala ferramentas BlackArch (exemplo)
sudo pacman -S blackarch-scanner

# Adiciona wallpaper e troca
cp meu_wallpaper.jpg ~/Pictures/Wallpapers/
# Super + W no Hyprland
```
