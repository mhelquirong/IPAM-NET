"""NetBox configuration for the CODE-branded validation stack.

Mounted into the container at netbox/netbox/configuration.py. In a real
deployment this file is the only place the branding needs to be switched on:
add 'netbox_code_branding' to PLUGINS and, optionally, override the strings in
PLUGINS_CONFIG.
"""

import os

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'netbox'),
        'USER': os.environ.get('DB_USER', 'netbox'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'netbox'),
        'HOST': os.environ.get('DB_HOST', 'postgres'),
        'PORT': os.environ.get('DB_PORT', ''),
        'CONN_MAX_AGE': 300,
    }
}

REDIS = {
    'tasks': {
        'HOST': os.environ.get('REDIS_HOST', 'redis'),
        'PORT': 6379,
        'DATABASE': 0,
        'SSL': False,
    },
    'caching': {
        'HOST': os.environ.get('REDIS_HOST', 'redis'),
        'PORT': 6379,
        'DATABASE': 1,
        'SSL': False,
    },
}

SECRET_KEY = os.environ.get('SECRET_KEY', 'code-branding-local-validation-key-not-for-production-use!!')

# Required for v2 API tokens. Replace before any real deployment — generate with
# `python netbox/generate_secret_key.py`.
API_TOKEN_PEPPERS = {
    1: os.environ.get(
        'API_TOKEN_PEPPER_1',
        'local-validation-pepper-do-not-use-in-production-000000000000',
    ),
}

DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

#
# CODE branding
#

PLUGINS = [
    'netbox_code_branding',
]

# Dashboard shown to users who have not yet customised their own. This is a
# stock NetBox configuration parameter — no override or patch involved. It leads
# with IPAM rather than DCIM, and drops the "NetBox News" RSS widget, which
# reaches out to an external NetBox Labs endpoint and is off-brand here.
DEFAULT_DASHBOARD = [
    {
        'widget': 'extras.ObjectCountsWidget',
        'width': 4,
        'height': 4,
        'title': 'IP Address Management',
        'color': 'blue',
        'config': {
            'models': [
                'ipam.prefix',
                'ipam.ipaddress',
                'ipam.iprange',
                'ipam.vlan',
                'ipam.vrf',
                'ipam.aggregate',
            ]
        },
    },
    {
        'widget': 'extras.NoteWidget',
        'width': 4,
        'height': 2,
        'title': 'CODE IP Management',
        'color': 'cyan',
        'config': {
            'content': (
                'Welcome to the CODE IP Management platform. This dashboard is yours — '
                'rearrange, resize or remove widgets, and add new ones with the '
                '"Add Widget" button. Changes affect only _your_ dashboard.'
            )
        },
    },
    {
        'widget': 'extras.BookmarksWidget',
        'width': 4,
        'height': 4,
        'title': 'Bookmarks',
        'color': 'orange',
    },
    {
        'widget': 'extras.ObjectListWidget',
        'width': 8,
        'height': 4,
        'title': 'Prefixes',
        'config': {
            'model': 'ipam.prefix',
            'page_size': 10,
        },
    },
    {
        'widget': 'extras.ObjectCountsWidget',
        'width': 4,
        'height': 3,
        'title': 'Infrastructure',
        'config': {
            'models': [
                'dcim.site',
                'dcim.device',
                'dcim.rack',
            ]
        },
    },
    {
        'widget': 'extras.ObjectCountsWidget',
        'width': 4,
        'height': 3,
        'title': 'Circuits',
        'config': {
            'models': [
                'circuits.provider',
                'circuits.circuit',
            ]
        },
    },
]

PLUGINS_CONFIG = {
    'netbox_code_branding': {
        'brand_name': 'CODE',
        'product_name': 'IP Management',
        'title_suffix': 'CODE IPAM',
        'login_tagline': 'Inspire Your Vision',
        'support_url': 'https://code.sa',
        'support_label': 'code.sa',
        'show_powered_by': True,
        'apply_theme': True,
    },
}
