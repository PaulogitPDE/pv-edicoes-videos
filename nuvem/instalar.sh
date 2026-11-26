#!/usr/bin/env bash
# Instala o painel Achadinhos do PV numa máquina Ubuntu (Google Cloud e2-micro).
# Uso, no SSH da máquina:  curl -fsSL https://raw.githubusercontent.com/PaulogitPDE/pv-edicoes-videos/main/nuvem/instalar.sh | sudo bash
# Pode rodar de novo sem problema (atualiza o código e mantém sessão do WhatsApp, senha e tokens).
set -euo pipefail
REPO_URL=https://github.com/PaulogitPDE/pv-edicoes-videos.git
DIR=/opt/achadinhos
DADOS=/var/lib/achadinhos
ENVF=/etc/achadinhos.env

echo "== 1/6 Memória extra (swap de 2 GB, a máquina só tem 1 GB)"
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile >/dev/null && swapon /swapfile
  grep -q /swapfile /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "== 2/6 Programas (Node 22, Python, fontes, Caddy)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg git python3 python3-pil python3-numpy fonts-inter debian-keyring debian-archive-keyring apt-transport-https >/dev/null
if ! command -v node >/dev/null || [ "$(node -v | cut -d. -f1 | tr -d v)" -lt 20 ]; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash - >/dev/null
  apt-get install -y -qq nodejs >/dev/null
fi
if ! command -v caddy >/dev/null; then
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -qq && apt-get install -y -qq caddy >/dev/null
fi

echo "== 3/6 Código"
id achadinhos >/dev/null 2>&1 || useradd --system --home "$DADOS" --shell /usr/sbin/nologin achadinhos
if [ -d "$DIR/.git" ]; then git -C "$DIR" pull --ff-only -q; else git clone -q "$REPO_URL" "$DIR"; fi
mkdir -p "$DADOS"
# histórico de produtos já usados vem do repo na primeira vez
[ -f "$DADOS/usados.json" ] || cp "$DIR/achadinhos/usados.json" "$DADOS/" 2>/dev/null || true
[ -f "$DADOS/precos.json" ] || cp "$DIR/achadinhos/precos.json" "$DADOS/" 2>/dev/null || true
chown -R achadinhos:achadinhos "$DIR" "$DADOS"
(cd "$DIR/nuvem" && sudo -u achadinhos npm install --omit=dev --no-audit --no-fund --silent)

echo "== 4/6 Endereço"
IP=$(curl -fs -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip || curl -fs https://api.ipify.org)
DOMINIO="${IP//./-}.sslip.io"

echo "== 5/6 Senha e chaves"
if [ ! -f "$ENVF" ]; then
  exec 3</dev/tty
  read -r -s -p "Crie uma senha para o painel: " SENHA <&3; echo
  read -r -p "ML_CLIENT_ID (Mercado Livre, app de desenvolvedor): " MLID <&3
  read -r -s -p "ML_CLIENT_SECRET: " MLSEC <&3; echo
  umask 077
  cat > "$ENVF" <<EOF
PAINEL_SENHA=$SENHA
ML_CLIENT_ID=$MLID
ML_CLIENT_SECRET=$MLSEC
BASE_URL=https://$DOMINIO
PORT=3000
DADOS=$DADOS
EOF
else
  sed -i "s#^BASE_URL=.*#BASE_URL=https://$DOMINIO#" "$ENVF"
fi
chmod 600 "$ENVF"

echo "== 6/6 Serviços"
cat > /etc/systemd/system/achadinhos.service <<EOF
[Unit]
Description=Achadinhos do PV (WhatsApp + painel)
After=network-online.target
Wants=network-online.target

[Service]
User=achadinhos
WorkingDirectory=$DIR/nuvem
EnvironmentFile=$ENVF
ExecStart=/usr/bin/node app.js
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
cat > /etc/caddy/Caddyfile <<EOF
$DOMINIO {
  reverse_proxy 127.0.0.1:3000
}
EOF
systemctl daemon-reload
systemctl enable --now achadinhos >/dev/null 2>&1
systemctl restart achadinhos caddy

echo
echo "Pronto! Abra no celular ou no PC:  https://$DOMINIO"
echo "(o certificado HTTPS leva até 1 minuto para sair na primeira vez)"
echo "No Mercado Livre (developers.mercadolivre.com.br > seu app), a URL de redirecionamento é:"
echo "   https://$DOMINIO/ml/retorno"
