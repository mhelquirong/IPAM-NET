"""Injects the CODE branding bundle into every NetBox page.

``PluginTemplateExtension`` subclasses with ``models = None`` are registered
globally, and ``{% plugin_head %}`` in ``templates/base/base.html`` calls
``head()`` on them for every rendered page — the login screen included, since
``login.html`` extends the same base template.

Because the injection point sits at the end of ``<head>``, everything emitted
here wins over NetBox's own stylesheet and icon links by document order alone;
no ``!important`` arms race and no core template overrides are required.
"""

from django.conf import settings

from netbox.plugins import PluginTemplateExtension

PLUGIN_NAME = 'netbox_code_branding'


class CodeBranding(PluginTemplateExtension):
    """Global branding: stylesheet, favicon set and title/label runtime."""

    models = None

    def head(self):
        plugin_settings = settings.PLUGINS_CONFIG.get(PLUGIN_NAME, {})
        return self.render(
            'netbox_code_branding/head.html',
            extra_context={'branding': plugin_settings},
        )


template_extensions = [CodeBranding]
