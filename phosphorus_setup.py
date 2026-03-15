#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  PHOSPHORUS OBSIDIAN - Automated Arch Linux Installer
#  Sistema: Hyprland + BlackArch + Visual Rice para VirtualBox
#  Uso: python phosphorus_setup.py
# =============================================================================

import os
import subprocess
import sys
import json
import tempfile
import shutil

# ---------------------------------------------------------------------------
# CONFIGURAÇÕES GLOBAIS
# ---------------------------------------------------------------------------
USERNAME       = "obsidian"
PASSWORD       = "phosphorus"
ROOT_PASSWORD  = "phosphorus"
HOSTNAME       = "phosphorus-obsidian"
DISK           = "/dev/sda"
TIMEZONE       = "Europe/Lisbon"
LOCALE         = "pt_PT.UTF-8"
KEYMAP         = "pt"

PHOSPHORUS_GREEN = "#20c20e"
OBSIDIAN_BLACK   = "#0d1117"

PACKAGES = [
    # Ferramentas base
    "git", "base-devel", "neovim", "curl", "wget", "python", "zsh",
    # Desktop Wayland
    "hyprland", "waybar", "rofi-wayland",
    "kitty", "dunst", "swaybg",          # swaybg = wallpaper (oficial)
    "grim", "slurp", "wl-clipboard",
    # Audio
    "pipewire", "pipewire-pulse", "wireplumber",
    # Portal / polkit
    "xdg-desktop-portal-hyprland", "xdg-user-dirs",
    "polkit-gnome",                      # polkit-kde-agent nao existe
    "qt5-wayland", "qt6-wayland",
    # Fonts e extras
    "ttf-jetbrains-mono-nerd", "starship",
    # Rede
    "networkmanager", "sudo",
    # VirtualBox
    "virtualbox-guest-utils",
]

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def run(cmd, check=True, **kwargs):
    print(f"\n[+] {cmd}")
    return subprocess.run(cmd, shell=True, check=check, **kwargs)


def write_file(path, content, mode=0o644):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, mode)
    print(f"[✓] Escrito: {path}")


# ---------------------------------------------------------------------------
# STEP 1 – INSTALAÇÃO MANUAL (sgdisk + pacstrap)
# ---------------------------------------------------------------------------

def install_system():
    """Particiona, formata, monta e instala o sistema base manualmente."""

    print("\n[1/6] Actualizando relogio do sistema...")
    run("timedatectl set-ntp true")

    print("\n[2/6] Particionando disco (GPT/EFI) - layout simples para VM...")
    # Limpa o disco e cria tabela GPT
    run(f"sgdisk --zap-all {DISK}")
    run(f"sgdisk --clear {DISK}")
    # Particao 1: EFI (512MB)
    run(f"sgdisk -n 1:0:+512M -t 1:ef00 -c 1:EFI {DISK}")
    # Particao 2: root (todo o espaco restante)
    run(f"sgdisk -n 2:0:0 -t 2:8300 -c 2:root {DISK}")
    run("partprobe || true", check=False)
    run("sleep 2")

    # Detecta nomes correctos das particoes (sda1/sda2 ou nvme0n1p1 etc.)
    import glob
    parts = sorted(glob.glob(f"{DISK}*[0-9]"))
    if len(parts) < 2:
        parts = sorted(glob.glob(f"{DISK}p*[0-9]"))
    efi, root = parts[0], parts[1]
    print(f"  Particoes detectadas: EFI={efi} root={root}")

    print("\n[3/6] Formatando particoes...")
    run(f"mkfs.fat -F32 {efi}")
    run(f"mkfs.ext4 -F {root}")

    print("\n[4/6] Montando particoes...")
    run(f"mount {root} /mnt")
    run("mkdir -p /mnt/boot/efi")
    run(f"mount {efi} /mnt/boot/efi")

    print("\n[5/6] Optimizando mirrors e instalando sistema base com pacstrap...")
    # Escreve mirrorlist com mirrors confiaveis diretamente via Python
    mirrorlist = (
        "# Phosphorus Obsidian - mirrorlist\n"
        "Server = https://mirror.ufscar.br/archlinux/$repo/os/$arch\n"
        "Server = https://mirrors.kernel.org/archlinux/$repo/os/$arch\n"
        "Server = https://mirror.rackspace.com/archlinux/$repo/os/$arch\n"
        "Server = https://mirrors.mit.edu/archlinux/$repo/os/$arch\n"
        "Server = https://geo.mirror.pkgbuild.com/$repo/os/$arch\n"
    )
    with open("/etc/pacman.d/mirrorlist", "w") as f:
        f.write(mirrorlist)
    print("  [✓] Mirrorlist atualizado")

    # Tenta melhorar com reflector (pode falhar, nao e critico)
    run("reflector --country Brazil,US --age 6 --protocol https "
        "--sort rate --save /etc/pacman.d/mirrorlist", check=False)

    run("pacman -Sy --noconfirm", check=False)

    pkgs = " ".join(PACKAGES + [
        "base", "linux", "linux-firmware", "grub", "efibootmgr",
        "os-prober", "sudo", "nano",
    ])
    # Sem --disable-download-timeout (flag invalido nesta versao)
    # Usar --noconfirm para evitar prompts interativos
    run(f"pacstrap -K /mnt {pkgs}")

    print("\n[6/6] Gerando fstab...")
    run("genfstab -U /mnt >> /mnt/etc/fstab")

    # Swap file (2GB) dentro do root
    print("  Criando swap file (2GB)...")
    run("dd if=/dev/zero of=/mnt/swapfile bs=1M count=2048 status=progress")
    run("chmod 600 /mnt/swapfile")
    run("mkswap /mnt/swapfile")
    run("echo '/swapfile none swap defaults 0 0' >> /mnt/etc/fstab")

    print("[✓] Sistema base instalado!")



# ---------------------------------------------------------------------------
# STEP 3 – SCRIPTS DE PÓS-INSTALAÇÃO (chroot)
# ---------------------------------------------------------------------------

POSTINSTALL_SCRIPT = r'''#!/bin/bash
set -euo pipefail

USERNAME="__USERNAME__"
HOME_DIR="/home/$USERNAME"
GREEN="__GREEN__"
OBSIDIAN="__OBSIDIAN__"

echo "==> [1/7] Sudo sem password durante instalação…"
echo "$USERNAME ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/phosphorus_tmp
chmod 440 /etc/sudoers.d/phosphorus_tmp

echo "==> [2/7] Shell padrão: zsh…"
chsh -s /usr/bin/zsh "$USERNAME"

echo "==> [3/7] BlackArch strap…"
curl -fsSL https://blackarch.org/strap.sh -o /tmp/strap.sh
chmod +x /tmp/strap.sh
bash /tmp/strap.sh || true   # continua mesmo que haja avisos

echo "==> [4/7] Criando configuração Hyprland…"
HYPR_DIR="$HOME_DIR/.config/hypr"
mkdir -p "$HYPR_DIR"

cat > "$HYPR_DIR/hyprland.conf" << 'HYPR_CONF'
# ─────────────────────────────────────────────
#  PHOSPHORUS OBSIDIAN – hyprland.conf
# ─────────────────────────────────────────────

# VirtualBox compatibility
env = WLR_NO_HARDWARE_CURSORS,1
env = WLR_RENDERER_ALLOW_SOFTWARE,1
env = LIBVA_DRIVER_NAME,d3d12

# Monitor
monitor=,preferred,auto,1

# Autostart
exec-once = waybar
exec-once = dunst
exec-once = /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1
# Wallpaper: usa swww se disponivel, swaybg como fallback
exec-once = swww-daemon || true
exec-once = (swww img $HOME/.config/hypr/wallpaper.png --transition-type fade 2>/dev/null) || swaybg -c __OBSIDIAN__ &

# Input
input {{
    kb_layout = pt
    follow_mouse = 1
    touchpad {{
        natural_scroll = yes
    }}
}}

# General – Phosphorus Green borders on Obsidian bg
general {{
    gaps_in = 5
    gaps_out = 10
    border_size = 2
    col.active_border = rgba(20c20eff)
    col.inactive_border = rgba(0d1117aa)
    layout = dwindle
}}

# Decoration
decoration {{
    rounding = 10
    blur {{
        enabled = true
        size = 8
        passes = 2
        new_optimizations = true
    }}
    drop_shadow = yes
    shadow_range = 20
    shadow_color = rgba(20c20e66)
    active_opacity = 0.95
    inactive_opacity = 0.85
}}

# Animations
animations {{
    enabled = yes
    bezier = obsidian, 0.05, 0.9, 0.1, 1.05
    animation = windows, 1, 7, obsidian
    animation = windowsOut, 1, 7, default, popin 80%
    animation = border, 1, 10, default
    animation = fade, 1, 7, default
    animation = workspaces, 1, 6, default
}}

# Layout
dwindle {{
    pseudotile = yes
    preserve_split = yes
}}

# Keybindings
$mod = SUPER
bind = $mod, RETURN, exec, kitty
bind = $mod, Q, killactive,
bind = $mod, M, exit,
bind = $mod SHIFT, F, togglefloating,
bind = $mod, F, fullscreen,
bind = $mod, D, exec, rofi -show drun
bind = $mod, W, exec, ~/.local/bin/wallpaper_switcher.sh

# Workspaces
bind = $mod, 1, workspace, 1
bind = $mod, 2, workspace, 2
bind = $mod, 3, workspace, 3
bind = $mod, 4, workspace, 4
bind = $mod, 5, workspace, 5
bind = $mod SHIFT, 1, movetoworkspace, 1
bind = $mod SHIFT, 2, movetoworkspace, 2
bind = $mod SHIFT, 3, movetoworkspace, 3
bind = $mod SHIFT, 4, movetoworkspace, 4
bind = $mod SHIFT, 5, movetoworkspace, 5

# Move/resize with mouse
bindm = $mod, mouse:272, movewindow
bindm = $mod, mouse:273, resizewindow
HYPR_CONF

echo "==> [5/7] Configurando Kitty…"
KITTY_DIR="$HOME_DIR/.config/kitty"
mkdir -p "$KITTY_DIR"
cat > "$KITTY_DIR/kitty.conf" << 'KITTY_CONF'
# ─────────────────────────────────────────────
#  PHOSPHORUS OBSIDIAN – kitty.conf
# ─────────────────────────────────────────────
font_family      JetBrainsMono Nerd Font
bold_font        auto
italic_font      auto
bold_italic_font auto
font_size        12.0

# Obsidian palette
foreground            #c9d1d9
background            #0d1117
background_opacity    0.92
selection_background  #20c20e
selection_foreground  #0d1117

# Phosphorus Green accents
color2  #20c20e
color10 #39d353

# cursor
cursor                #20c20e
cursor_text_color     #0d1117

# Tabs
tab_bar_style              powerline
active_tab_foreground      #0d1117
active_tab_background      #20c20e
inactive_tab_foreground    #8b949e
inactive_tab_background    #161b22

# Misc
enable_audio_bell no
KITTY_CONF

echo "==> [6/7] Criando script de wallpapers (swww + rofi)…"
mkdir -p "$HOME_DIR/Pictures/Wallpapers"
mkdir -p "$HOME_DIR/.local/bin"

cat > "$HOME_DIR/.local/bin/wallpaper_switcher.sh" << 'WALLPAPER_SCRIPT'
#!/usr/bin/env bash
# Phosphorus Obsidian – Wallpaper Switcher via Rofi + swww
WALLPAPER_DIR="$HOME/Pictures/Wallpapers"

if [ -z "$(ls -A "$WALLPAPER_DIR" 2>/dev/null)" ]; then
    notify-send "Phosphorus Obsidian" "Adiciona wallpapers em ~/Pictures/Wallpapers" --icon=image
    exit 0
fi

SELECTED=$(ls "$WALLPAPER_DIR" | rofi \
    -dmenu \
    -p "Wallpaper" \
    -theme-str 'window {background-color: #0d1117; border: 2px solid #20c20e;}
                listview {background-color: #161b22;}
                element-text {color: #c9d1d9;}
                element selected {background-color: #20c20e; text-color: #0d1117;}
                inputbar {background-color: #161b22; text-color: #20c20e;}')

[ -z "$SELECTED" ] && exit 0

swww img "$WALLPAPER_DIR/$SELECTED" \
    --transition-type wipe \
    --transition-angle 30 \
    --transition-duration 1.5
WALLPAPER_SCRIPT
chmod +x "$HOME_DIR/.local/bin/wallpaper_switcher.sh"

echo "==> Baixando um wallpaper padrão Phosphorus Obsidian…"
# Wallpaper Obsidian via API pública (imagem tech dark)
curl -fsSL \
  "https://raw.githubusercontent.com/linuxdotexe/nordic-wallpapers/master/wallpapers/ign_wallpaper.jpg" \
  -o "$HOME_DIR/Pictures/Wallpapers/phosphorus_default.jpg" 2>/dev/null || true

echo "==> [7/7] Configurando Waybar (barra de status)…"
WAYBAR_DIR="$HOME_DIR/.config/waybar"
mkdir -p "$WAYBAR_DIR"

cat > "$WAYBAR_DIR/config" << 'WAYBAR_CONFIG'
{
    "layer": "top",
    "position": "top",
    "height": 32,
    "spacing": 4,
    "modules-left": ["hyprland/workspaces", "hyprland/mode"],
    "modules-center": ["clock"],
    "modules-right": ["cpu", "memory", "network", "pulseaudio", "tray"],
    "hyprland/workspaces": {
        "format": "{icon}",
        "on-click": "activate",
        "format-icons": {
            "1": "󰊠", "2": "󰊠", "3": "󰊠",
            "4": "󰊠", "5": "󰊠",
            "active": "󰮯", "default": "󰊠"
        }
    },
    "clock": {
        "format": "  {:%H:%M   %d/%m/%Y}",
        "tooltip-format": "<big>{:%A, %d %B %Y}</big>"
    },
    "cpu": {"format": "  {usage}%", "tooltip": false},
    "memory": {"format": "  {}%"},
    "network": {
        "format-wifi": "  {signalStrength}%",
        "format-ethernet": "󰈀 Connected",
        "format-disconnected": "⚠ Offline"
    },
    "pulseaudio": {"format": "  {volume}%", "format-muted": " "},
    "tray": {"spacing": 10}
}
WAYBAR_CONFIG

cat > "$WAYBAR_DIR/style.css" << 'WAYBAR_CSS'
/* Phosphorus Obsidian - Waybar Style */
* { font-family: "JetBrainsMono Nerd Font"; font-size: 13px; border: none; border-radius: 0; }
window#waybar {
    background: rgba(13, 17, 23, 0.90);
    color: #c9d1d9;
    border-bottom: 2px solid #20c20e;
}
#workspaces button {
    color: #8b949e;
    padding: 0 8px;
    background: transparent;
    border-bottom: 2px solid transparent;
}
#workspaces button.active {
    color: #20c20e;
    border-bottom: 2px solid #20c20e;
    background: rgba(32, 194, 14, 0.1);
}
#clock { color: #20c20e; padding: 0 12px; font-weight: bold; }
#cpu, #memory, #network, #pulseaudio { padding: 0 10px; color: #c9d1d9; }
#tray { padding: 0 8px; }
WAYBAR_CSS

echo "==> Configurando Starship prompt..."
STARSHIP_DIR="$HOME_DIR/.config"
cat > "$STARSHIP_DIR/starship.toml" << 'STARSHIP_CONF'
# Phosphorus Obsidian - Starship Prompt
format = "$username$hostname$directory$git_branch$git_status\n> $character"

[username]
style_user = "bold #20c20e"
style_root = "bold red"
format = "[$user]($style) "
show_always = true

[hostname]
ssh_only = false
format = "[@$hostname](bold #39d353) "

[directory]
style = "#20c20e"
format = "[  $path]($style) "
truncation_length = 3

[git_branch]
format = "[ $branch](bold #8b949e) "

[character]
success_symbol = "[>](bold #20c20e)"
error_symbol   = "[>](bold red)"
STARSHIP_CONF


echo "==> Configurando .zshrc…"
cat > "$HOME_DIR/.zshrc" << 'ZSHRC'
# Phosphorus Obsidian – .zshrc
export PATH="$HOME/.local/bin:$PATH"
export EDITOR=nvim
export TERMINAL=kitty

# Starship
eval "$(starship init zsh)"

# Aliases
alias ls='ls --color=auto'
alias ll='ls -lah'
alias la='ls -A'
alias grep='grep --color=auto'
alias vi=nvim
alias vim=nvim

# BlackArch tools PATH
export PATH="$PATH:/usr/share/blackarch/utils"

# Hyprland autostart (TTY1)
if [ -z "$WAYLAND_DISPLAY" ] && [ "$XDG_VTNR" -eq 1 ]; then
    exec Hyprland
fi
ZSHRC

echo "==> Ajustando permissões…"
chown -R "$USERNAME:$USERNAME" "$HOME_DIR"

echo "==> Removendo sudo sem password temporário…"
rm -f /etc/sudoers.d/phosphorus_tmp

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   PHOSPHORUS OBSIDIAN – Instalação Concluída  ║"
echo "║   Utilizador: __USERNAME__  /  Pass: phosphorus  ║"
echo "║   Reinicia e entra no Hyprland!               ║"
echo "╚══════════════════════════════════════════════╝"
'''.replace('__USERNAME__', USERNAME).replace('__GREEN__', PHOSPHORUS_GREEN).replace('__OBSIDIAN__', OBSIDIAN_BLACK)


def write_postinstall_script():
    write_file("/tmp/phosphorus_postinstall.sh",
               POSTINSTALL_SCRIPT, mode=0o755)


def run_base_chroot_config():
    """Configura locale, hostname, GRUB, utilizador e yay em chroot."""
    base_script = f'''#!/bin/bash
set -e

# Locale
echo "{LOCALE} UTF-8" >> /etc/locale.gen
locale-gen
echo "LANG={LOCALE}" > /etc/locale.conf
echo "KEYMAP={KEYMAP}" > /etc/vconsole.conf

# Timezone
ln -sf /usr/share/zoneinfo/{TIMEZONE} /etc/localtime
hwclock --systohc

# Hostname
echo "{HOSTNAME}" > /etc/hostname
cat >> /etc/hosts << 'HOSTS'
127.0.0.1   localhost
::1         localhost
127.0.1.1   {HOSTNAME}.localdomain {HOSTNAME}
HOSTS

# Root password
echo "root:{ROOT_PASSWORD}" | chpasswd

# User (sem -s bash pois zsh pode nao estar no path ainda)
useradd -m -G wheel,audio,video,storage -s /usr/bin/zsh {USERNAME} 2>/dev/null || \
    useradd -m -G wheel,audio,video,storage {USERNAME}
echo "{USERNAME}:{PASSWORD}" | chpasswd

# sudoers
echo "%wheel ALL=(ALL:ALL) ALL" >> /etc/sudoers
echo "Defaults !requiretty" >> /etc/sudoers

# Servicos
systemctl enable NetworkManager
systemctl enable vboxservice 2>/dev/null || true

# GRUB para VirtualBox EFI - --removable necessario para a VM arrancar
grub-install --target=x86_64-efi --efi-directory=/boot/efi \
    --bootloader-id=GRUB --recheck --removable
grub-mkconfig -o /boot/grub/grub.cfg

# xdg dirs
sudo -u {USERNAME} xdg-user-dirs-update 2>/dev/null || true

# Instalar yay (AUR helper) para pacotes AUR como swww
echo "==> Instalando yay (AUR helper)..."
cd /tmp
sudo -u {USERNAME} git clone --depth=1 https://aur.archlinux.org/yay-bin.git /tmp/yay-bin 2>/dev/null || true
if [ -d /tmp/yay-bin ]; then
    cd /tmp/yay-bin
    sudo -u {USERNAME} makepkg -si --noconfirm 2>/dev/null || true
fi

# Instalar swww via yay (animated wallpaper - AUR package)
if command -v yay &>/dev/null; then
    echo "==> Instalando swww via yay..."
    sudo -u {USERNAME} yay -S --noconfirm swww 2>/dev/null || true
fi

echo "==> Configuracao base concluida!"
'''
    write_file("/tmp/phosphorus_base.sh", base_script, mode=0o755)
    run("cp /tmp/phosphorus_base.sh /mnt/tmp/phosphorus_base.sh")
    run("arch-chroot /mnt bash /tmp/phosphorus_base.sh")
    print("[✓] Configuracao base do sistema concluida!")



def run_postinstall():
    """Executa o script de pós-instalação (rice) em chroot."""
    print("\n[➤] Copiando script de rice para o novo sistema...")
    run("cp /tmp/phosphorus_postinstall.sh /mnt/tmp/phosphorus_postinstall.sh")
    print("[➤] Executando rice em chroot...")
    run("arch-chroot /mnt bash /tmp/phosphorus_postinstall.sh")
    print("[✓] Pos-instalacao concluida!")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("""
╔══════════════════════════════════════════════════════╗
║          PHOSPHORUS OBSIDIAN INSTALLER               ║
║   Hyprland + BlackArch + VirtualBox Rice             ║
╚══════════════════════════════════════════════════════╝
    """)

    print("[1/4] Instalando sistema base (sgdisk + pacstrap)...")
    install_system()

    print("[2/4] Configurando sistema base em chroot...")
    run_base_chroot_config()

    print("[3/4] Gerando script de pos-instalacao (rice)...")
    write_postinstall_script()

    print("[4/4] Executando pos-instalacao (Hyprland rice + BlackArch)...")
    run_postinstall()

    print("\n[✓] Sistema Phosphorus Obsidian instalado com sucesso!")
    print("[✓] Reinicia a VM e desfruta do Hyprland!")
    run("umount -R /mnt || true", check=False)
    run("reboot", check=False)


if __name__ == "__main__":
    main()
