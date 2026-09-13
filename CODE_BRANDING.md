# CODE-branded IP Management platform — customization and upgrade notes

This repository is an unmodified checkout of **NetBox v4.7.0** plus a self-contained
branding plugin. It presents as a CODE IP Management platform while remaining a
stock NetBox underneath.

---

## 1. What was reviewed before making changes

NetBox 4.7 renders its UI from:

| Layer | Location | Role |
| --- | --- | --- |
| Base template | `netbox/templates/base/base.html` | `<head>`, favicon links, `<title>`, calls `{% plugin_head %}` |
| App layout | `netbox/templates/base/layout.html` | Sidebar, header, search, footer |
| Login | `netbox/templates/login.html` | Extends `base/base.html` directly |
| Styles | `netbox/project-static/styles/**` → bundled `dist/netbox.css` | Tabler 1.4 / Bootstrap 5.3, `--tblr-*` custom properties |
| Static assets | `netbox/project-static/img/` | `logo_netbox_*.svg`, `netbox.ico`, `motif.svg` |

Two constraints shaped the design:

1. **Template overriding from a plugin is not possible.** `settings.py` sets
   `TEMPLATES[0]['DIRS'] = [<netbox>/templates]` with `APP_DIRS = True`. The
   filesystem loader is consulted before app directories, so a plugin can never
   shadow a core template by name.
2. **Static file shadowing from a plugin is not possible either.**
   `STATICFILES_DIRS` (`FileSystemFinder`) is searched before
   `AppDirectoriesFinder`, so a plugin cannot replace `netbox.ico` or
   `logo_netbox_dark_teal.svg` by supplying a same-named file.

NetBox does load `netbox/netbox/local_settings.py` if present (gitignored), which
*would* allow prepending template and static directories — but it is explicitly
labelled **"UNSUPPORTED FUNCTIONALITY"** in `settings.py`. It is deliberately not
used here.

What *is* supported is `PluginTemplateExtension.head()`, which
`base/base.html` invokes via `{% plugin_head %}` on **every** page, login
included. That is the only integration point this customization uses.

---

## 2. What was changed

### Files added (none modified)

```
code_branding/                      # the branding plugin (pip-installable)
├── pyproject.toml
├── README.md
├── tools/build_assets.py           # regenerates brand assets from logo-code.svg
└── netbox_code_branding/
    ├── __init__.py                 # PluginConfig + default settings
    ├── template_content.py         # the single global head() extension
    ├── templates/netbox_code_branding/head.html
    └── static/netbox_code_branding/
        ├── css/code-branding.css   # the theme
        ├── js/code-branding.js     # title + accessible-name runtime
        └── img/                    # generated CODE assets
deploy/                             # local validation stack (not required in prod)
├── Dockerfile
├── docker-compose.yml
├── configuration.py                # secrets required from env, no fallbacks
├── entrypoint.sh
├── .env.example                    # template for the required secrets
└── .gitignore                      # keeps the real .env out of git
CODE_BRANDING.md                    # this document
```

**Zero files under `netbox/` were edited.** Verify at any time with:

```bash
git status --porcelain netbox/
```

It must print nothing.

### Branding surfaces covered

| Surface | How |
| --- | --- |
| Sidebar + login logo | CSS `content: url()` on `.navbar-brand-image` / `.page-center .logo`, using the compact lockup |
| Login strapline | Live gradient text from `login_tagline`, not the raster strapline baked into the full lockup |
| Edition label → "IP Management" | `.netbox-edition::after`, text from `PLUGINS_CONFIG` |
| Favicon / touch icon / theme colour | Extra `<link>`/`<meta>` after NetBox's own |
| Page titles (`… \| NetBox`) | `code-branding.js`, synchronous in `<head>` |
| Colours, type, radii, shadows | `--tblr-*` token remap + targeted rules |
| Navigation | Peach `#FDE0CE` active state with the asymmetric `5px 0 5px 5px` corner |
| Header | Translucent surface, blurred backdrop, branded search focus ring |
| Dashboard / cards / tables | Radius, shadow, uppercase tracked headers |
| Login page | Aurora ground, branded card, gradient CTA, strapline |
| Footer | Brand-coloured icons, NetBox Labs outreach links hidden, "Powered by NetBox" credit retained |
| Top brand ribbon | `body::before`, the brandmark's colour sequence |
| Footer corporate link | `code-branding.js`, mirroring NetBox's own footer markup |

### Dashboard defaults (configuration, not code)

`deploy/configuration.py` also sets NetBox's stock **`DEFAULT_DASHBOARD`**
parameter. This is ordinary NetBox configuration — no override, no patch:

- IPAM object counts lead, ahead of DCIM and circuits;
- a CODE welcome note replaces the generic one;
- the **"NetBox News" RSS widget is removed**, because it calls an external
  NetBox Labs endpoint on every dashboard render and is off-brand here.

`DEFAULT_DASHBOARD` applies only to users who have not yet customised their own
dashboard; existing users keep theirs. Remove the block to fall back to NetBox's
stock layout.

### Design decisions worth knowing

- **Primary is CODE blue `#006EC6`, not the warm gradient.** The gradient is the
  corporate site's CTA treatment and is applied to `.btn-primary` and the login
  CTA, but the *token* `--tblr-primary` stays blue so that links, focus rings and
  active states never collide with `--tblr-danger`. In a network tool, "save" and
  "delete" must not read as the same colour.
- **The UI stays light and airy** rather than adopting a dark navy chrome,
  because code.sa is a light-only, white-ground identity.
- **Dark mode is an extension, not a copy.** code.sa has no dark palette, so the
  wordmark navy `#221F33` was developed into a surface family with the cooler
  half of the brandmark (`#00AAC8` → `#4FC8E0`) carrying the accents.
- **NetBox attribution is kept.** NetBox is Apache-2.0 and the goal is a CODE
  platform *powered by* NetBox. Set `show_powered_by: False` to remove it.

### Deliberately left alone

Two things look like obvious rebranding targets and are not touched, because
recolouring them would destroy information:

- **Progress bars.** NetBox colours prefix, aggregate and IP-range utilisation
  with `bg-success` / `bg-warning` / `bg-danger`. A blanket `.progress-bar`
  background would override all three and flatten the signal to one colour.
- **`.bg-primary` / `.text-bg-primary` in dark mode.** `--tblr-primary` is a
  light cyan there, and NetBox already pairs those surfaces with near-black
  text — the correct contrast direction. Only `.btn-primary` is overridden,
  because it carries the warm gradient and needs white text.

### NetBox's own brand colours are hardcoded in places

Most of the theme is a clean `--tblr-*` token remap, but NetBox's SCSS pins its
brand colours literally in a handful of dark-mode rules (`$rich-black #001423`,
`$bright-teal #00F2D4`, `$dark-teal #00857D`). Those are restated explicitly in
section 3 and 7 of `code-branding.css`: `.card`, `.page-header`, `.table thead
th`, `.page-tabs .nav-tabs .nav-link.active`, `.btn-primary`, the sidebar, the
footer icons and the sidebar submenu links. Each override matches NetBox's own
selector weight and wins on document order. `grep -rn "rich-black\|bright-teal\|
dark-teal" netbox/project-static/styles/` lists the full set if it changes.

---

## 3. Enabling the branding

In `netbox/netbox/configuration.py`:

```python
PLUGINS = ['netbox_code_branding']
```

Install and collect:

```bash
pip install -e ./code_branding
python netbox/manage.py collectstatic --no-input
```

Optional overrides live in `PLUGINS_CONFIG` — see `code_branding/README.md`.

To disable the branding entirely, remove the entry from `PLUGINS`. To keep the
logo, favicon and titles but restore NetBox's stock palette, set
`apply_theme: False`.

---

## 4. Upgrading NetBox

The plugin holds no models, no migrations, no URLs and no API surface, so an
upgrade is the normal NetBox procedure:

```bash
git fetch --tags
git checkout v4.8.0          # nothing under netbox/ is modified, so this is clean
pip install -r requirements.txt
pip install -e ./code_branding
python netbox/manage.py migrate
python netbox/manage.py collectstatic --no-input
```

### Post-upgrade checklist

The branding is coupled to NetBox's markup only through the selectors below.
None of them are private APIs, but they are not a stability contract either —
check them after a major/minor upgrade. Each failure is cosmetic and localized;
none can break IPAM functionality.

| Selector / string | Used for | If NetBox changes it |
| --- | --- | --- |
| `{% plugin_head %}` in `base/base.html` | the entire integration | Branding stops applying — check NetBox's plugin release notes first |
| `.navbar-brand-image`, `.hide-theme-dark` / `.hide-theme-light` | logo swap | NetBox logo reappears in the sidebar |
| `.page-center .logo` | login logo | NetBox logo reappears on login |
| `.netbox-edition` | product label | "Community" reappears |
| `.navbar-vertical.navbar-expand-lg …` | sidebar theming | Sidebar reverts to NetBox teal |
| `<title>… \| NetBox</title>` | title suffix | `SUFFIX_RE` in `code-branding.js` stops matching; titles read "… \| NetBox" |
| `--tblr-*` custom properties | colour system | Only if NetBox leaves Tabler |
| `.footer .container-fluid > ul:first-of-type` | footer credit | Credit misplaces |
| `<h2 class="card-header">` panel headers | tracked-out caps | Panel headers revert to sentence case |
| `$rich-black` / `$bright-teal` in dark SCSS | dark surfaces | Blue-black patches appear inside the navy UI |

A five-minute visual check of the login page, sidebar, dashboard, an IPAM list
view and one object detail page in both light and dark mode covers all of them.

### Things that do *not* need rework on upgrade

- No NetBox template, stylesheet or asset is patched, so `git checkout <tag>`
  never conflicts.
- `min_version` is `4.6.0` and **no `max_version` is set**, deliberately: this
  plugin must never be the reason a security upgrade is blocked.
- Brand assets are generated, not hand-edited — rerun
  `python code_branding/tools/build_assets.py` if `logo-code.svg` is replaced.

---

## 5. Validation performed

Validated against a live NetBox 4.7.0 instance running this checkout with the
plugin installed (PostgreSQL 17 + Valkey, `DEBUG=False`).

**Branding delivery** — 14 automated checks, all passing:

- the stylesheet, favicon set, touch icon and runtime script are injected, and
  land inside `<head>` (verified by splitting the response at `</head>`);
- every generated asset is served — `code-logo{,-dark,-compact,-compact-dark}.svg`,
  `code-mark.svg`, `favicon.{ico,svg}`, `code-touch-icon-180.png`;
- `login_tagline` from `PLUGINS_CONFIG` reaches the rendered CSS;
- template renders cleanly for a full config, `apply_theme: False`, and an empty
  config, with no stray template tags in any branch.

**IPAM functionality** — 21 automated checks against the REST API, all passing:

| Area | Checks |
| --- | --- |
| Create | RIR, aggregate, VRF, prefix, IP address, VLAN, IP range — all `201` |
| Read | list endpoints for all six IPAM object types — all `200` |
| Compute | `available-ips/` (returned 50), `available-prefixes/` |
| Filter | `?within=10.0.0.0/8` |
| Update / delete | `PATCH` prefix `200`, `DELETE` prefix `204` |
| GraphQL | `vrf_list` query `200` |
| Auth | unauthenticated `/api/` correctly refused (`403`) |

**NetBox's own IPAM test suites** — run with the plugin installed and active:

```
python manage.py test ipam.tests.test_views ipam.tests.test_api ipam.tests.test_models --parallel 4
Ran 1423 tests in 37.437s
OK (skipped=18)
```

The view tests render real templates, so every IPAM page was exercised with
`{% plugin_head %}` injecting the branding bundle.

**Interface** — reviewed in the browser, light and dark, on the login page,
dashboard, an IPAM list view, an object detail view and a create form:

- computed contrast in dark mode: body 14.6:1, cards 13.4:1, table headers
  7.8:1 (this caught a real bug — the light `:root` token block was leaking
  `--tblr-body-color` into dark mode, painting navy text on a navy ground);
- prefix utilisation bars still resolve to `bg-success` green, confirming the
  semantic colours survive the rebrand;
- page titles read `<object> | CODE IPAM` throughout;
- `.netbox-edition` resolves to "IP Management" as real text, not only as a
  pseudo-element, so assistive technology reads it.

---

## 6. Local validation stack

```bash
cp deploy/.env.example deploy/.env    # fill in; there are no committed defaults
docker compose -f deploy/docker-compose.yml up -d --build
# http://localhost:8000/
```

Builds NetBox from this checkout (unmodified) with the plugin installed on top,
against PostgreSQL 17 and Valkey 8.

> **Verification status:** the image in `deploy/Dockerfile` builds successfully,
> but `docker compose up` was **not** exercised on the machine this was developed
> on — Docker Desktop's Linux engine would not start there (its `docker-desktop`
> WSL distro never came up). The validation in section 5 was therefore run
> against a native install instead: the same source and plugin, on Python 3.12,
> PostgreSQL 17 and Redis, with the same `deploy/configuration.py`. Treat the
> compose stack as convenience tooling to smoke-test once in your environment,
> not as a verified artifact.

Equivalent native setup, which is what section 5 was run against:

```bash
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
./venv/bin/pip install -e ./code_branding
cp deploy/configuration.py netbox/netbox/configuration.py   # edit DB/Redis hosts
./venv/bin/python netbox/manage.py migrate
./venv/bin/python netbox/manage.py collectstatic --no-input
./venv/bin/python netbox/manage.py createsuperuser
./venv/bin/python netbox/manage.py runserver 0.0.0.0:8000 --insecure
```

`SECRET_KEY`, `API_TOKEN_PEPPER_1` and `SUPERUSER_PASSWORD` are read from the
environment with **no in-repo fallback**. `deploy/configuration.py` raises
`ImproperlyConfigured` naming the missing variable, and Compose refuses to start
with a message pointing at `deploy/.env`. A committed default would be a
published signing key the moment this repository is public.

Neither stack is intended for production; use the standard NetBox installation
guide with gunicorn + nginx for that.
