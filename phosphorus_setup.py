#!/usr/bin/env python3
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
    "git", "base-devel", "kitty", "hyprland", "waybar", "swww",
    "rofi-lbonn-wayland", "virtualbox-guest-utils", "starship", "zsh",
    "ttf-jetbrains-mono-nerd", "networkmanager", "sudo", "neovim",
    "curl", "wget", "python", "xdg-user-dirs", "pipewire",
    "pipewire-pulse", "wireplumber", "xdg-portal-hyprland",
    "polkit-kde-agent", "qt5-wayland", "qt6-wayland",
    "grim", "slurp", "wl-clipboard", "dunst",
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
# STEP 1 – CONFIGURAÇÃO DO ARCHINSTALL
# ---------------------------------------------------------------------------

def build_archinstall_config():
    """Gera os JSONs de configuração e credenciais para o archinstall."""

    config = {
        "additional-repositories": [],
        "archinstall-language": "Portuguese",
        "audio_config": {"audio": "pipewire"},
        "bootloader": "Grub",
        "config_version": "2.8.0",
        "debug": False,
        "disk_config": {
            "config_type": "default_layout",
            "device_modifications": [
                {
                    "device": DISK,
                    "wipe": True,
                    "partitions": [
                        {
                            "btrfs": [], "flags": ["Boot", "ESP"],
                            "fs_type": "fat32",
                            "length": {"unit": "GiB", "value": 0.5,
                                       "sector_size": None, "total_size": None},
                            "mount_options": [], "mountpoint": "/boot",
                            "obj_id": "efi-partition",
                            "start": {"unit": "MiB", "value": 1,
                                      "sector_size": None, "total_size": None},
                            "status": "create", "type": "primary",
                        },
                        {
                            "btrfs": [], "flags": [],
                            "fs_type": "ext4",
                            "length": {"unit": "GiB", "value": 20,
                                       "sector_size": None, "total_size": None},
                            "mount_options": [], "mountpoint": "/",
                            "obj_id": "root-partition",
                            "start": {"unit": "MiB", "value": 513,
                                      "sector_size": None, "total_size": None},
                            "status": "create", "type": "primary",
                        },
                        {
                            "btrfs": [], "flags": [],
                            "fs_type": "ext4",
                            "length": {"unit": "GiB", "value": -1,
                                       "sector_size": None, "total_size": None},
                            "mount_options": [], "mountpoint": "/home",
                            "obj_id": "home-partition",
                            "start": {"unit": "GiB", "value": 20.5,
                                      "sector_size": None, "total_size": None},
                            "status": "create", "type": "primary",
                        },
                    ],
                }
            ],
        },
        "hostname": HOSTNAME,
        "kernels": ["linux"],
        "locale_config": {
            "kb_layout": KEYMAP,
            "sys_enc": "UTF-8",
            "sys_lang": LOCALE,
        },
        "network_config": {"nics": [], "type": "nm"},
        "ntp": True,
        "packages": PACKAGES,
        "profile_config": {
            "profile": {"custom_settings": {}, "details": [], "main": "Minimal"},
            "gfx_driver": "VMware / VirtualBox (open-source)",
        },
        "services": ["NetworkManager", "vboxservice"],
        "swap": True,
        "timezone": TIMEZONE,
        "version": "2.8.0",
    }

    credentials = {
        "!root-password": ROOT_PASSWORD,
        "!users": [
            {"username": USERNAME, "!password": PASSWORD, "sudo": True}
        ],
    }

    write_file("/tmp/phosphorus_config.json",
               json.dumps(config, indent=2, ensure_ascii=False))
    write_file("/tmp/phosphorus_credentials.json",
               json.dumps(credentials, indent=2, ensure_ascii=False))

    print("\n[✓] Configurações do archinstall geradas.")


# ---------------------------------------------------------------------------
# STEP 2 – EXECUTA O ARCHINSTALL
# ---------------------------------------------------------------------------

def run_archinstall():
    """Executa o archinstall com as configs geradas."""
    print("\n[➤] A iniciar o archinstall…")
    run(
        "archinstall "
        "--config /tmp/phosphorus_config.json "
        "--creds /tmp/phosphorus_credentials.json "
        "--silent"
    )


# ---------------------------------------------------------------------------
# STEP 3 – SCRIPTS DE PÓS-INSTALAÇÃO (chroot)
# ---------------------------------------------------------------------------

POSTINSTALL_SCRIPT = r"""#!/bin/bash
set -euo pipefail

USERNAME="{username}"
HOME_DIR="/home/$USERNAME"
GREEN="{green}"
OBSIDIAN="{obsidian}"

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
exec-once = swww init
exec-once = dunst
exec-once = /usr/lib/polkit-kde-authentication-agent-1

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
    -p "🌿 Wallpaper" \
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
/* Phosphorus Obsidian – Waybar Style */
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

echo "==> Configurando Starship prompt…"
STARSHIP_DIR="$HOME_DIR/.config"
cat > "$STARSHIP_DIR/starship.toml" << 'STARSHIP_CONF'
# Phosphorus Obsidian – Starship Prompt
format = """
[╭─](bold green)$username$hostname$directory$git_branch$git_status
[╰─](bold green)$character"""

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
success_symbol = "[❯](bold #20c20e)"
error_symbol   = "[❯](bold red)"
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
echo "║   Utilizador: {username}  /  Pass: phosphorus  ║"
echo "║   Reinicia e entra no Hyprland!               ║"
echo "╚══════════════════════════════════════════════╝"
""".format(
    username=USERNAME,
    green=PHOSPHORUS_GREEN,
    obsidian=OBSIDIAN_BLACK,
)


def write_postinstall_script():
    write_file("/tmp/phosphorus_postinstall.sh",
               POSTINSTALL_SCRIPT, mode=0o755)


def run_postinstall():
    """Executa o script de pós-instalação em chroot."""
    print("\n[➤] Copiando script para o novo sistema…")
    run("cp /tmp/phosphorus_postinstall.sh /mnt/tmp/phosphorus_postinstall.sh")
    print("[➤] Executando em chroot…")
    run("arch-chroot /mnt bash /tmp/phosphorus_postinstall.sh")
    print("[✓] Pós-instalação concluída!")


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

    # Verifica modo: pode rodar como gerador (--generate-only)
    # ou como instalador completo
    generate_only = "--generate-only" in sys.argv

    print("[1/4] Gerando configurações do archinstall…")
    build_archinstall_config()

    print("[2/4] Gerando script de pós-instalação…")
    write_postinstall_script()

    if generate_only:
        print("\n[ℹ] Modo --generate-only: ficheiros gerados em /tmp/")
        print("    Config:       /tmp/phosphorus_config.json")
        print("    Credentials:  /tmp/phosphorus_credentials.json")
        print("    Post-install: /tmp/phosphorus_postinstall.sh")
        print("\n    Para instalar manualmente:")
        print("    archinstall --config /tmp/phosphorus_config.json \\")
        print("                --creds /tmp/phosphorus_credentials.json \\")
        print("                --silent")
        print("    arch-chroot /mnt bash /tmp/phosphorus_postinstall.sh")
        return

    print("[3/4] Executando archinstall…")
    run_archinstall()

    print("[4/4] Executando pós-instalação em chroot…")
    run_postinstall()

    print("\n[✓] Sistema Phosphorus Obsidian instalado com sucesso!")
    print("[✓] Reinicia a VM e desfruta do Hyprland!")
    run("umount -R /mnt || true", check=False)
    run("reboot", check=False)


if __name__ == "__main__":
    main()
