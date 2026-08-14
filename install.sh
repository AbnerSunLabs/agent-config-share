#!/bin/sh
set -e

REPO_URL="https://github.com/AbnerSunLabs/agent-config-share.git"
REPO_BRANCH="main"
DEFAULT_SHARE="${HOME}/.local/share/agent-config-share"
SHARE_ROOT="${AGENT_CONFIG_SHARE_ROOT:-$DEFAULT_SHARE}"
BIN_DIR="${AGENT_CONFIG_BIN_DIR:-${HOME}/.local/bin}"

info() { printf '%s\n' "$1"; }
err() { printf '%s\n' "$1" >&2; exit 1; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || err "缺少命令: $1"
}

resolve_local_root() {
  script_path=$1
  case "$script_path" in
    /*) abs=$script_path ;;
    *) abs=$(pwd)/$script_path ;;
  esac
  dir=$(dirname "$abs")
  # 脚本在仓库根
  if [ -d "$dir/inventory" ] && [ -d "$dir/scripts" ]; then
    printf '%s\n' "$dir"
    return 0
  fi
  return 1
}

write_shim() {
  root=$1
  dest=$2
  mkdir -p "$(dirname "$dest")"
  cat > "$dest" <<EOF
#!/bin/sh
exec "$root/.venv/bin/python" "$root/scripts/agent-config" "\$@"
EOF
  chmod +x "$dest"
}

main() {
  need_cmd git
  need_cmd python3
  need_cmd curl
  python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' \
    || err "需要 Python 3.9+（当前: $(python3 -c 'import sys; print(sys.version.split()[0])')）"
  python3 -m venv --help >/dev/null 2>&1 || err "python3 -m venv 不可用"

  install_root=""
  if [ -n "$0" ] && [ "$0" != "sh" ] && [ "$0" != "-sh" ] && [ "$0" != "bash" ] && [ "$0" != "-bash" ]; then
    if install_root=$(resolve_local_root "$0" 2>/dev/null); then
      info "本地安装: $install_root"
    else
      install_root=""
    fi
  fi

  if [ -z "$install_root" ]; then
    install_root=$SHARE_ROOT
    info "远程安装: $install_root"
    mkdir -p "$(dirname "$install_root")"
    if [ -d "$install_root/.git" ]; then
      git -C "$install_root" fetch origin
      git -C "$install_root" checkout "$REPO_BRANCH"
      git -C "$install_root" pull --ff-only origin "$REPO_BRANCH"
    else
      git clone --branch "$REPO_BRANCH" "$REPO_URL" "$install_root"
    fi
  fi

  python3 -m venv "$install_root/.venv"
  "$install_root/.venv/bin/python" -m pip install -q -r "$install_root/scripts/requirements-run.txt"

  shim="$BIN_DIR/agent-config"
  if mkdir -p "$BIN_DIR" 2>/dev/null && [ -w "$BIN_DIR" ]; then
    write_shim "$install_root" "$shim"
  else
    info "需要 sudo 才能写入 /usr/local/bin"
    tmp=$(mktemp)
    write_shim "$install_root" "$tmp"
    sudo mv "$tmp" /usr/local/bin/agent-config
    sudo chmod +x /usr/local/bin/agent-config
    shim=/usr/local/bin/agent-config
  fi

  info "已安装: $shim"
  if ! command -v agent-config >/dev/null 2>&1; then
    info "未在 PATH 中找到 agent-config。请把 $BIN_DIR 加入 PATH，例如:"
    info "  export PATH=\"$BIN_DIR:\$PATH\""
  fi
  info "启动面板: agent-config ui"
}

main "$@"
