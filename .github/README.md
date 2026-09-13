# CODE IP Management

A CODE-branded IP Address Management platform, powered by [NetBox](https://github.com/netbox-community/netbox).

This repository is an **unmodified checkout of NetBox v4.7.0** plus a self-contained
branding plugin. Nothing under `netbox/` is patched, so upstream NetBox upgrades
stay a routine `git checkout`.

> GitHub renders this file as the repository landing page. NetBox's own
> `README.md` is left untouched in the repository root, which is what keeps the
> upgrade path clean.

---

## What's in here

| Path | Purpose |
| --- | --- |
| `netbox/`, `docs/`, `requirements.txt`, … | NetBox v4.7.0, exactly as released upstream |
| `code_branding/` | The `netbox_code_branding` plugin — the entire customization |
| `deploy/` | Docker Compose stack, Dockerfile and example configuration |
| `CODE_BRANDING.md` | Architecture, design decisions, validation and upgrade notes |
| `deploy/DEPLOY-UBUNTU.md` | Step-by-step deployment onto a remote Ubuntu server |
| `logo-code.svg` | The source brand asset every other image is generated from |

## Deploy

### Docker Compose (quickest)

```bash
cp deploy/.env.example deploy/.env
python netbox/generate_secret_key.py        # once per value, paste into deploy/.env
docker compose -f deploy/docker-compose.yml up -d --build
# http://localhost:8000/
```

There are no secrets committed to this repository, so `deploy/.env` must be
filled in first — Compose refuses to start without it and tells you what is
missing. `deploy/.env` is gitignored.

### Remote Ubuntu server

Full walkthrough — PostgreSQL, Redis, gunicorn, systemd, nginx and TLS — in
**[`deploy/DEPLOY-UBUNTU.md`](../deploy/DEPLOY-UBUNTU.md)**.

### Native install (summary)

```bash
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
./venv/bin/pip install -e ./code_branding

cp deploy/configuration.py netbox/netbox/configuration.py   # then edit it
export SECRET_KEY=...  API_TOKEN_PEPPER_1=...               # required, no defaults
./venv/bin/python netbox/manage.py migrate
./venv/bin/python netbox/manage.py collectstatic --no-input
./venv/bin/python netbox/manage.py createsuperuser
```

The branding activates from `configuration.py`:

```python
PLUGINS = ['netbox_code_branding']
```

## Before going to production

- [x] `SECRET_KEY`, `API_TOKEN_PEPPER_1` and `SUPERUSER_PASSWORD` have no
      committed defaults — the stack will not start until you supply them in
      `deploy/.env`. Generate each with `python netbox/generate_secret_key.py`.
- [ ] Set `ALLOWED_HOSTS` to your actual hostnames; it defaults to `*`, e.g.
      `ALLOWED_HOSTS=ipam.example.com` in `deploy/.env`.
- [ ] Serve behind HTTPS with gunicorn + nginx, not `runserver`.
- [ ] **Disable GitHub Actions for this repository.** The upstream NetBox
      workflows in `.github/workflows/` came along with the source and are not
      meant to run on a deployment fork — they will fail noisily and some act on
      issues and pull requests. Settings → Actions → General → *Disable actions*.

## Upgrading NetBox

```bash
git remote add upstream https://github.com/netbox-community/netbox.git
git fetch upstream --tags
git merge v4.8.0        # nothing under netbox/ is modified, so this is clean
pip install -r requirements.txt && pip install -e ./code_branding
python netbox/manage.py migrate && python netbox/manage.py collectstatic --no-input
```

See [`CODE_BRANDING.md`](../CODE_BRANDING.md) for the post-upgrade checklist —
the short list of NetBox selectors the branding depends on.

## Licence

NetBox is licensed under Apache 2.0; see [`LICENSE.txt`](../LICENSE.txt) and
[`NOTICE`](../NOTICE). The CODE brand assets under
`code_branding/netbox_code_branding/static/netbox_code_branding/img/` are the
property of CODE and are not covered by that licence.
