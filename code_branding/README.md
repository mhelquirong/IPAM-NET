# netbox-code-branding

CODE corporate branding for NetBox. Turns a stock NetBox deployment into a
CODE-branded IP Management platform without modifying a single NetBox core file.

## How it works

The plugin registers one global `PluginTemplateExtension`. NetBox's
`templates/base/base.html` calls `{% plugin_head %}` at the end of every page's
`<head>` — including the login page, which extends the same base template — and
that hook renders `templates/netbox_code_branding/head.html`.

That single injection point delivers:

| Surface | Mechanism |
| --- | --- |
| Colours, typography, layout, motifs | `css/code-branding.css`, loaded after `netbox.css` so it wins on document order |
| Sidebar and login logos | CSS `content: url(...)` on NetBox's existing `<img>` elements |
| Favicon, touch icon, theme colour | Extra `<link>`/`<meta>` tags; later declarations win |
| Page title suffix (`… \| NetBox`) | `js/code-branding.js`, running synchronously in `<head>` |
| Product name and login strapline | CSS custom properties emitted from `PLUGINS_CONFIG` |
| Footer corporate link and NetBox credit | `js/code-branding.js` plus a CSS `::after` |

No NetBox template, stylesheet, static asset or setting is patched or replaced.

## Installation

```bash
pip install -e ./code_branding
```

Then in `netbox/netbox/configuration.py`:

```python
PLUGINS = ['netbox_code_branding']
```

Restart NetBox and run `manage.py collectstatic --no-input`.

## Configuration

All keys are optional; the defaults are shown.

```python
PLUGINS_CONFIG = {
    'netbox_code_branding': {
        'brand_name': 'CODE',
        'product_name': 'IP Management',       # replaces the NetBox edition label
        'title_suffix': 'CODE IPAM',           # replaces '| NetBox' in page titles
        'login_tagline': 'Inspire Your Vision',
        'support_url': 'https://code.sa',
        'support_label': 'code.sa',
        'show_powered_by': True,               # NetBox attribution in the footer
        'apply_theme': True,                   # False = logo/favicon/title only
    },
}
```

## Brand assets

Everything under `static/netbox_code_branding/img/` is generated from the single
source asset `logo-code.svg` in the repository root:

```bash
python code_branding/tools/build_assets.py
```

Re-run it if the source logo is ever replaced. The palette used across the theme
is sampled from that logo and cross-checked against `code.sa`:

| Token | Value | Source |
| --- | --- | --- |
| Navy / primary text | `#221F33` | wordmark, `.colorOne` |
| Action blue | `#006EC6` | brandmark, `.colorBlue` |
| Cyan | `#00AAC8` | brandmark |
| Red | `#D51C38` | brandmark |
| Orange | `#F9863D` | brandmark |
| Signature gradient | `linear-gradient(109deg, #FAA26B 14.67%, #E74B62 110.18%)` | `.btn-linearGradient` |
| Nav highlight | `#FDE0CE` | site navigation |

## Upgrading NetBox

See `CODE_BRANDING.md` in the repository root for the upgrade procedure and the
list of NetBox selectors this plugin depends on.
