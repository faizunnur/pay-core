#!/usr/bin/env bash
#
# PayCore bootcamp — VM bootstrap
# Transfotech Academy | DevSecOps Bootcamp
#
# Prepares a fresh Ubuntu 24.04 droplet for all sixteen weeks of the course.
# Run it as root on the VM, not on your laptop:
#
#     bash bootstrap.sh
#
# It is safe to run more than once.
#
set -euo pipefail

GREEN=$'\033[0;32m'; YELLOW=$'\033[0;33m'; RED=$'\033[0;31m'; NC=$'\033[0m'
step() { echo; echo "${GREEN}==>${NC} $*"; }
warn() { echo "${YELLOW}warning:${NC} $*"; }
die()  { echo "${RED}error:${NC} $*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Run this as root on your VM (you should see root@paycore-lab-... in your prompt)."

if ! grep -q "Ubuntu" /etc/os-release 2>/dev/null; then
    warn "This script targets Ubuntu 24.04. Continuing anyway, but you may hit surprises."
fi

export DEBIAN_FRONTEND=noninteractive

# ---------------------------------------------------------------- packages ---
step "Updating the system (this is the slow part — 2 to 3 minutes)"
apt-get update -qq
apt-get upgrade -y -qq

step "Installing everyday tools"
apt-get install -y -qq \
    ca-certificates curl gnupg lsb-release \
    git jq htop unzip tree lsof \
    python3 python3-pip python3-venv \
    postgresql-client

install -m 0755 -d /etc/apt/keyrings

# ------------------------------------------------------------------ docker ---
if command -v docker >/dev/null 2>&1; then
    step "Docker is already installed — skipping"
else
    step "Installing Docker Engine and the Compose plugin"
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        > /etc/apt/sources.list.d/docker.list

    apt-get update -qq
    apt-get install -y -qq \
        docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin

    systemctl enable --now docker
fi

# -------------------------------------------------------------- github cli ---
if command -v gh >/dev/null 2>&1; then
    step "GitHub CLI is already installed — skipping"
else
    step "Installing the GitHub CLI"
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        -o /etc/apt/keyrings/githubcli.gpg
    chmod a+r /etc/apt/keyrings/githubcli.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli.gpg] \
https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list
    apt-get update -qq
    apt-get install -y -qq gh
fi

# ---------------------------------------------------------------- firewall ---
step "Configuring the firewall to allow SSH and nothing else"

apt-get install -y ufw || die "Failed to install UFW"

command -v ufw >/dev/null 2>&1 || die "UFW installation failed: ufw command not found"

ufw --force reset >/dev/null
ufw default deny incoming >/dev/null
ufw default allow outgoing >/dev/null
ufw allow OpenSSH >/dev/null
ufw --force enable >/dev/null

# --------------------------------------------------- docker vs the firewall ---
# ufw on its own is NOT enough, and this surprises almost everybody.
#
# When you publish a container port -- ports: "8000:8000" in a compose file --
# Docker writes its own iptables rules into the FORWARD and nat chains. Those
# are evaluated BEFORE ufw's INPUT rules, so the container is reachable from
# the public internet even though ufw says "default deny incoming".
#
# You can watch this happen: `ufw status` will say the port is blocked, and
# the port will answer anyway.
#
# Docker leaves a chain called DOCKER-USER specifically for us to filter that
# traffic. Rules we put there run before Docker's own. So:
#   1. let replies to connections the container started come back
#   2. drop everything else arriving from the public interface
#
# PayCore is deliberately vulnerable teaching software -- SQL injection, card
# tokens in the logs, no rate limiting. It must never be reachable from the
# internet. Reach it through the SSH tunnel VS Code sets up for you instead.

step "Stopping Docker from publishing containers to the internet"
apt-get install -y -qq iptables-persistent netfilter-persistent

PUBLIC_IF="$(ip route show default 2>/dev/null | awk '/default/ {print $5; exit}')"
PUBLIC_IF="${PUBLIC_IF:-eth0}"
echo "    public interface: ${PUBLIC_IF}"

# Wait for Docker to have created the chain, then make our rules idempotent.
iptables -N DOCKER-USER 2>/dev/null || true
while iptables -D DOCKER-USER -i "$PUBLIC_IF" -j DROP 2>/dev/null; do :; done
while iptables -D DOCKER-USER -m conntrack --ctstate RELATED,ESTABLISHED -j RETURN 2>/dev/null; do :; done

iptables -I DOCKER-USER -i "$PUBLIC_IF" -j DROP
iptables -I DOCKER-USER -m conntrack --ctstate RELATED,ESTABLISHED -j RETURN

netfilter-persistent save >/dev/null 2>&1 || warn "Could not persist iptables rules; they will not survive a reboot."

# ----------------------------------------------------------------- workdir ---
step "Creating your working directory"
mkdir -p /root/devsecops-bootcamp

# ------------------------------------------------------------------ verify ---
step "Verifying the install"
FAILED=0
check() {
    if "$@" >/dev/null 2>&1; then
        printf '  %-26s %s\n' "$*" "${GREEN}ok${NC}"
    else
        printf '  %-26s %s\n' "$*" "${RED}FAILED${NC}"
        FAILED=1
    fi
}
check docker --version
check docker compose version
check python3 --version
check git --version
check gh --version

echo
if [ "$FAILED" -ne 0 ]; then
    die "Something did not install. Re-run this script; if it fails again, post the output in the class channel."
fi

echo "${GREEN}==> Your VM is ready.${NC}"
echo
echo "Versions:"
echo "  docker   $(docker --version | cut -d' ' -f3 | tr -d ,)"
echo "  compose  $(docker compose version --short)"
echo "  python   $(python3 --version | cut -d' ' -f2)"
echo "  git      $(git --version | cut -d' ' -f3)"
echo
echo "Firewall:"
ufw status | head -6
echo
echo "Docker containers are blocked from the public interface:"
iptables -L DOCKER-USER -n --line-numbers | head -5
echo "  (ufw alone does not do this -- see the comments in bootstrap.sh)"
echo
echo "Next steps — see the VM Setup Guide, sections 5.3 onward:"
echo "  1. git config --global user.name / user.email"
echo "  2. gh auth login"
echo "  3. Connect VS Code with Remote-SSH"
echo
