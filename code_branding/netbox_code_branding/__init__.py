"""CODE corporate branding for NetBox.

Applies the CODE visual identity to the NetBox UI without modifying any NetBox
core file. Everything is delivered through the supported plugin API: a single
``PluginTemplateExtension.head()`` hook injects a stylesheet, the CODE favicon
set and a small runtime script into every page NetBox renders (including the
login page, which extends the same base template).

See CODE_BRANDING.md in the repository root for the full customization and
upgrade notes.
"""

from netbox.plugins import PluginConfig

__version__ = '1.0.0'


class CodeBrandingConfig(PluginConfig):
    name = 'netbox_code_branding'
    verbose_name = 'CODE Branding'
    description = 'CODE corporate branding and theme for the NetBox IP Management platform.'
    version = __version__
    author = 'CODE'
    author_email = 'sales@code.sa'
    base_url = 'code-branding'

    # Verified against NetBox 4.7. No max_version is declared on purpose: this
    # plugin adds no models, URLs or API surface, so a NetBox minor upgrade
    # should never be blocked by it. See CODE_BRANDING.md for the short list of
    # template selectors to re-check after an upgrade.
    min_version = '4.6.0'

    default_settings = {
        # Wordmark shown in the sidebar/login lockup alt text and document title.
        'brand_name': 'CODE',
        # Descriptor rendered beneath the logo, replacing the NetBox edition label.
        'product_name': 'IP Management',
        # Suffix applied to every page title, replacing '| NetBox'.
        'title_suffix': 'CODE IPAM',
        # Strapline on the login screen.
        'login_tagline': 'Inspire Your Vision',
        # Optional support link rendered in the footer. Set to None to omit.
        'support_url': 'https://code.sa',
        'support_label': 'code.sa',
        # NetBox is Apache-2.0; keeping the attribution visible is both good
        # practice and consistent with 'CODE-branded platform powered by NetBox'.
        'show_powered_by': True,
        # Set False to keep NetBox's stock light/dark palette and apply only the
        # logo, favicon and title changes.
        'apply_theme': True,
    }


config = CodeBrandingConfig
