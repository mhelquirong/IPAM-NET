# Deploying CODE IP Management on Ubuntu

Step-by-step deployment of <https://github.com/mhelquirong/IPAM-NET> onto a
remote Ubuntu server.

Two options:

- **[Option A — Docker Compose](#option-a--docker-compose)** — one command once
  secrets are set. Good for a pilot, a lab, or an internal host.
- **[Option B — Native install](#option-b--native-install)** — PostgreSQL,
  Redis, gunicorn, systemd and nginx, following NetBox's own production layout.
  Use this for a real deployment.

Tested against **Ubuntu 24.04 LTS**, which ships the versions NetBox 4.7 needs:
Python 3.12+ and PostgreSQL 15+. On Ubuntu 22.04 the default PostgreSQL is 14,
which is **too old** — add the PGDG repository or use Option A.

---

## Before you start

| Requirement | Notes |
| --- | --- |
| Ubuntu 24.04 LTS | 22.04 works but needs a newer PostgreSQL (see above) |
| 4 GB RAM, 2 vCPU, 20 GB disk | Comfortable starting point |
| `sudo` access | All steps below assume it |
| DNS record | e.g. `ipam.example.com` → the server's IP, for TLS |
| Ports 80 and 443 open | 80 is needed for Let's Encrypt validation |

```bash
ssh youruser@your-server
sudo apt update && sudo apt upgrade -y
```

---

## Option A — Docker Compose

### A1. Install Docker

```bash
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER" && newgrp docker
```

### A2. Clone and configure

```bash
sudo mkdir -p /opt && cd /opt
sudo git clone https://github.com/mhelquirong/IPAM-NET.git
sudo chown -R "$USER":"$USER" IPAM-NET
cd IPAM-NET

cp deploy/.env.example deploy/.env
```

Generate a value for each secret and paste it into `deploy/.env`:

```bash
python3 netbox/generate_secret_key.py   # run once per value
```

Fill in `SECRET_KEY`, `API_TOKEN_PEPPER_1` and `SUPERUSER_PASSWORD`. There are
no defaults committed — Compose refuses to start without them and tells you
which one is missing.

### A3. Start

```bash
docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml logs -f netbox
```

First start runs migrations, which takes several minutes. It is ready when the
log shows `Starting NetBox on :8000`. Browse to `http://<server-ip>:8000/`.

> The compose stack runs Django's development server and listens on plain HTTP.
> For anything internet-facing, put nginx in front of it (steps **B9** and
> **B10** below apply unchanged — point `proxy_pass` at `127.0.0.1:8000` and
> bind the container to `127.0.0.1:8000:8000` in `deploy/docker-compose.yml`),
> or use Option B.

Skip to [Verify](#verify).

---

## Option B — Native install

This follows NetBox's documented production layout: the application under
`/opt/netbox`, running as a dedicated `netbox` user, behind gunicorn and nginx.

### B1. System packages

```bash
sudo apt install -y \
  postgresql redis-server \
  python3 python3-pip python3-venv python3-dev \
  build-essential libxml2-dev libxslt1-dev libffi-dev libpq-dev libssl-dev \
  zlib1g-dev git nginx

psql --version     # must be 15 or later
python3 --version  # must be 3.12 or later
```

### B2. PostgreSQL

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE netbox;
CREATE USER netbox WITH PASSWORD 'CHANGE-ME-strong-db-password';
ALTER DATABASE netbox OWNER TO netbox;
\q
```

Verify the credentials work:

```bash
psql --username netbox --password --host localhost netbox -c '\conninfo'
```

### B3. Redis

Ubuntu's default Redis is already listening on `127.0.0.1:6379`:

```bash
sudo systemctl enable --now redis-server
redis-cli ping      # -> PONG
```

### B4. Clone from GitHub

```bash
sudo mkdir -p /opt
cd /opt
sudo git clone https://github.com/mhelquirong/IPAM-NET.git netbox
cd /opt/netbox
```

Create the service account and hand it the directories it writes to:

```bash
sudo adduser --system --group netbox
sudo chown --recursive netbox /opt/netbox/netbox/media/
sudo chown --recursive netbox /opt/netbox/netbox/reports/
sudo chown --recursive netbox /opt/netbox/netbox/scripts/
```

### B5. NetBox configuration

```bash
sudo cp /opt/netbox/deploy/configuration.py /opt/netbox/netbox/netbox/configuration.py
sudo nano /opt/netbox/netbox/netbox/configuration.py
```

Set the database password to what you chose in **B2**. The file reads
`DB_PASSWORD` from the environment, so you can instead add it to the secrets
file in the next step and leave the file untouched.

### B6. Secrets

`SECRET_KEY` and `API_TOKEN_PEPPER_1` are read from the environment and have
**no in-repo default** — NetBox will refuse to start without them, by design.

```bash
python3 /opt/netbox/netbox/generate_secret_key.py   # run twice, keep both values
sudo nano /opt/netbox/deploy.env
```

```bash
SECRET_KEY=<first generated value>
API_TOKEN_PEPPER_1=<second generated value>
DB_PASSWORD=CHANGE-ME-strong-db-password
DB_HOST=localhost
REDIS_HOST=localhost
ALLOWED_HOSTS=ipam.example.com
```

Lock it down — it holds your signing keys:

```bash
sudo chown root:netbox /opt/netbox/deploy.env
sudo chmod 640 /opt/netbox/deploy.env
```

### B7. Install the branding plugin

`upgrade.sh` installs `local_requirements.txt` if it exists, so putting the
plugin there means every future upgrade reinstalls it automatically. That file
is gitignored, so it stays deployment-local.

```bash
echo '-e ./code_branding' | sudo tee /opt/netbox/local_requirements.txt
```

### B8. Build

`upgrade.sh` creates the virtualenv, installs dependencies, runs migrations,
collects static files and rebuilds the search index. It imports
`configuration.py`, so the secrets must be in the environment first:

```bash
cd /opt/netbox
set -a; source /opt/netbox/deploy.env; set +a
sudo -E ./upgrade.sh
```

Migrations take several minutes on first run. Then create your login:

```bash
source /opt/netbox/venv/bin/activate
python3 /opt/netbox/netbox/manage.py createsuperuser
```

Sanity-check that the branding plugin loaded:

```bash
python3 /opt/netbox/netbox/manage.py shell -c \
  "from django.conf import settings; print('PLUGINS =', settings.PLUGINS)"
# -> PLUGINS = ['netbox_code_branding']
deactivate
```

### B9. gunicorn and systemd

```bash
sudo cp /opt/netbox/contrib/gunicorn.py /opt/netbox/gunicorn.py
sudo cp -v /opt/netbox/contrib/*.service /etc/systemd/system/
```

The stock unit files do not load an environment file, and this deployment needs
one. Add it as a **drop-in** rather than editing the units, so a future upgrade
that refreshes them doesn't wipe your change:

```bash
sudo mkdir -p /etc/systemd/system/netbox.service.d /etc/systemd/system/netbox-rq.service.d
printf '[Service]\nEnvironmentFile=/opt/netbox/deploy.env\n' \
  | sudo tee /etc/systemd/system/netbox.service.d/10-env.conf
printf '[Service]\nEnvironmentFile=/opt/netbox/deploy.env\n' \
  | sudo tee /etc/systemd/system/netbox-rq.service.d/10-env.conf
```

Start both services — `netbox` serves the UI and API, `netbox-rq` runs
background jobs (report and script execution, webhooks):

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now netbox netbox-rq
systemctl status netbox netbox-rq --no-pager
```

gunicorn now listens on `127.0.0.1:8001`.

### B10. nginx and TLS

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo cp /opt/netbox/contrib/nginx.conf /etc/nginx/sites-available/netbox
sudo sed -i 's/netbox.example.com/ipam.example.com/' /etc/nginx/sites-available/netbox
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/netbox /etc/nginx/sites-enabled/netbox
```

The shipped config points at a self-signed certificate. Let certbot replace it
with a real one and handle renewal:

```bash
sudo certbot --nginx -d ipam.example.com
sudo nginx -t && sudo systemctl restart nginx
```

Make sure `ALLOWED_HOSTS` in `/opt/netbox/deploy.env` matches the hostname, then
`sudo systemctl restart netbox`.

Optional firewall:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

---

## Verify

Browse to `https://ipam.example.com/` and confirm:

- the login page shows the **CODE** lockup, "IP MANAGEMENT" and the gradient
  Sign In button, with the four-colour brand ribbon along the top edge;
- the browser tab reads `… | CODE IPAM` with the CODE favicon;
- after logging in, the dashboard leads with **IP Address Management**;
- **IPAM → Prefixes** loads, and you can create a prefix.

From the shell:

```bash
curl -sSk https://ipam.example.com/login/ | grep -c code-branding.css   # -> 1
systemctl is-active netbox netbox-rq nginx postgresql redis-server
```

---

## Upgrading

### Your own changes (branding, config)

```bash
cd /opt/netbox
sudo git pull origin main
set -a; source /opt/netbox/deploy.env; set +a
sudo -E ./upgrade.sh
sudo systemctl restart netbox netbox-rq
```

### A new NetBox release

Nothing under `netbox/` is modified in this repository, so merging upstream is
clean:

```bash
cd /opt/netbox
sudo git remote add upstream https://github.com/netbox-community/netbox.git   # once
sudo git fetch upstream --tags
sudo git merge v4.8.0            # substitute the release you want
sudo git push origin main        # optional: record it in your own repo

set -a; source /opt/netbox/deploy.env; set +a
sudo -E ./upgrade.sh
sudo systemctl restart netbox netbox-rq
```

Then run the post-upgrade visual check in [`CODE_BRANDING.md`](../CODE_BRANDING.md)
— five minutes across the login page, sidebar, dashboard, an IPAM list and one
object detail page, in both light and dark mode.

### Back up first

```bash
sudo -u postgres pg_dump -Fc netbox > ~/netbox-$(date +%F).dump
sudo tar czf ~/netbox-media-$(date +%F).tgz -C /opt/netbox/netbox media
```

Restore with `pg_restore -d netbox --clean ~/netbox-YYYY-MM-DD.dump`.

---

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `ImproperlyConfigured: SECRET_KEY is not set` | The service can't see `deploy.env`. Check the drop-in exists (`systemctl cat netbox`) and that the file is readable by the `netbox` group. |
| `netbox.service` fails, `journalctl -u netbox -n 50` shows a DB error | Password mismatch between `configuration.py`/`deploy.env` and **B2**, or PostgreSQL is older than 15. |
| 502 Bad Gateway from nginx | gunicorn isn't running (`systemctl status netbox`) or isn't on `127.0.0.1:8001`. |
| Pages load but unstyled, no logo | `collectstatic` didn't run, or nginx's `/static/` alias doesn't point at `/opt/netbox/netbox/static/`. Re-run `./upgrade.sh`. |
| UI is stock NetBox, no CODE branding | The plugin isn't installed. Confirm `local_requirements.txt` contains `-e ./code_branding`, re-run `./upgrade.sh`, and check `PLUGINS` as in **B8**. |
| `DisallowedHost` in the logs | Add the hostname to `ALLOWED_HOSTS` in `deploy.env` and restart. |
| Background jobs stay queued | `netbox-rq` isn't running, or Redis is unreachable. |

Logs:

```bash
sudo journalctl -u netbox -f
sudo journalctl -u netbox-rq -f
sudo tail -f /var/log/nginx/error.log
```
