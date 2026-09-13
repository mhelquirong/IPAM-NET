/*
 * CODE branding runtime for NetBox.
 *
 * Handles the few branding surfaces CSS cannot reach: the document title
 * suffix, which NetBox hard-codes in base/base.html, and the accessible names
 * attached to the logo and search box.
 *
 * This file is loaded synchronously from <head>, immediately after <title> has
 * been parsed, so the title is corrected before the browser paints the tab.
 */
(function () {
  'use strict';

  var DEFAULTS = {
    brandName: 'CODE',
    productName: 'IP Management',
    titleSuffix: 'CODE IPAM',
    supportUrl: '',
    supportLabel: '',
    showPoweredBy: true,
    netboxVersion: '',
  };

  function readConfig() {
    var el = document.getElementById('code-branding-config');
    if (!el) return DEFAULTS;
    try {
      var parsed = JSON.parse(el.textContent);
      return Object.assign({}, DEFAULTS, parsed);
    } catch (e) {
      return DEFAULTS;
    }
  }

  var cfg = readConfig();

  // NetBox renders "<page> | NetBox". Swap only that trailing vendor segment so
  // the page-specific part, which carries the object name, is left alone.
  var SUFFIX_RE = /\s*\|\s*NetBox\s*$/;

  function applyTitle() {
    if (!cfg.titleSuffix) return;
    var title = document.title;
    if (SUFFIX_RE.test(title)) {
      document.title = title.replace(SUFFIX_RE, ' | ' + cfg.titleSuffix);
    } else if (title.indexOf('| ' + cfg.titleSuffix) === -1) {
      document.title = title + ' | ' + cfg.titleSuffix;
    }
  }

  applyTitle();

  function applyLabels() {
    // The logo images are swapped by CSS `content`, which leaves the original
    // alt text in the accessibility tree.
    document.querySelectorAll('img.navbar-brand-image, .page-center img.logo').forEach(function (img) {
      img.alt = cfg.brandName + ' ' + cfg.productName;
    });

    // Swap the real "Community" text node for the product descriptor. The CSS
    // pseudo-element handles first paint; this makes it readable to AT too.
    document.querySelectorAll('.netbox-edition').forEach(function (el) {
      if (!el.classList.contains('code-edition-set')) {
        el.textContent = cfg.productName;
        el.classList.add('code-edition-set');
      }
    });

    var search = document.querySelector('.navbar input[name="q"]');
    if (search) {
      search.setAttribute('aria-label', 'Search ' + cfg.titleSuffix);
    }

    // Corporate link in the footer icon row, matching NetBox's own markup so it
    // inherits the existing styling and tooltip behaviour.
    var links = document.querySelector('.footer .container-fluid > ul');
    if (links && cfg.supportUrl && !links.querySelector('.code-support-link')) {
      var li = document.createElement('li');
      li.className = 'list-inline-item code-support-link';
      var a = document.createElement('a');
      a.href = cfg.supportUrl;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.className = 'link-secondary';
      a.setAttribute('aria-label', cfg.supportLabel || cfg.brandName);
      var i = document.createElement('i');
      i.className = 'mdi mdi-web text-primary';
      i.title = cfg.supportLabel || cfg.brandName;
      i.setAttribute('data-bs-toggle', 'tooltip');
      i.setAttribute('data-bs-placement', 'top');
      a.appendChild(i);
      li.appendChild(a);
      links.appendChild(li);
    }

    // The footer credit is drawn with CSS ::after content, which is not exposed
    // to assistive technology; add a real, visually hidden equivalent once.
    if (cfg.showPoweredBy) {
      var footer = document.querySelector('.footer .container-fluid');
      if (footer && !footer.querySelector('.code-powered-by-sr')) {
        var sr = document.createElement('span');
        sr.className = 'code-powered-by-sr visually-hidden';
        sr.textContent = 'Powered by NetBox' + (cfg.netboxVersion ? ' ' + cfg.netboxVersion : '');
        footer.appendChild(sr);
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyLabels);
  } else {
    applyLabels();
  }

  // NetBox drives much of the UI with htmx; re-assert after content swaps.
  document.addEventListener('htmx:afterSettle', function () {
    applyTitle();
    applyLabels();
  });
})();
