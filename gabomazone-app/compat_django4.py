"""
Shims de compatibilité pour les packages tiers non mis à jour pour Django 4.0+.
Django 4.0 a supprimé plusieurs APIs deprecated que les anciens packages utilisent encore.

Packages concernés : jsonfield (2.x), django-currencies
"""

# ── django.utils.translation ──────────────────────────────────────────────────
import django.utils.translation as _trans

if not hasattr(_trans, 'ugettext_lazy'):
    _trans.ugettext_lazy = _trans.gettext_lazy
if not hasattr(_trans, 'ugettext'):
    _trans.ugettext = _trans.gettext
if not hasattr(_trans, 'ugettext_noop'):
    _trans.ugettext_noop = _trans.gettext_noop
if not hasattr(_trans, 'ungettext'):
    _trans.ungettext = _trans.ngettext
if not hasattr(_trans, 'ungettext_lazy'):
    _trans.ungettext_lazy = _trans.ngettext_lazy

# ── django.utils.encoding ─────────────────────────────────────────────────────
import django.utils.encoding as _encoding

if not hasattr(_encoding, 'force_text'):
    _encoding.force_text = _encoding.force_str
if not hasattr(_encoding, 'smart_text'):
    _encoding.smart_text = _encoding.smart_str
if not hasattr(_encoding, 'force_unicode'):
    _encoding.force_unicode = _encoding.force_str
if not hasattr(_encoding, 'smart_unicode'):
    _encoding.smart_unicode = _encoding.smart_str

# ── django.utils.http ─────────────────────────────────────────────────────────
import django.utils.http as _http

if not hasattr(_http, 'is_safe_url'):
    _http.is_safe_url = _http.url_has_allowed_host_and_scheme

# ── django.conf.urls ──────────────────────────────────────────────────────────
import django.conf.urls as _conf_urls
from django.urls import re_path as _re_path

if not hasattr(_conf_urls, 'url'):
    _conf_urls.url = _re_path
