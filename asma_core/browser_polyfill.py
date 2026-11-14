"""
ASMA Accordi Next Generation - Browser Compatibility Polyfills & Mobile UX Guard
1. Fixes ES2023 Array methods (toSorted, toReversed, toSpliced, with) on older Android/Huawei tablets.
2. Suppresses the virtual on-screen keyboard when tapping selectbox / dropdown menus on mobile devices (SRS Cap. 10 / Mobile UX).
"""

from __future__ import annotations
import sys
import pathlib
import logging
import re

MOBILE_DROPDOWN_GUARD_JS = """
(function() {
  function initMobileDropdownGuard() {
    var rootDocs = [document];
    try {
      if (window.parent && window.parent.document && window.parent.document !== document) {
        rootDocs.push(window.parent.document);
      }
    } catch(e) {}
    try {
      if (window.top && window.top.document && rootDocs.indexOf(window.top.document) === -1) {
        rootDocs.push(window.top.document);
      }
    } catch(e) {}

    rootDocs.forEach(function(targetDoc) {
      if (!targetDoc || targetDoc.__asma_dropdown_guard_installed) return;
      targetDoc.__asma_dropdown_guard_installed = true;

      try {
        if (targetDoc.head && !targetDoc.getElementById('asma-purge-badges-css')) {
          var stEl = targetDoc.createElement('style');
          stEl.id = 'asma-purge-badges-css';
          stEl.textContent = [
            'footer, [data-testid="stFooter"], #MainMenu,',
            '[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],',
            '[data-testid="manage-app-button"], #manage-app-button,',
            '[aria-label*="Manage app"], button[aria-label*="Manage app"],',
            'div[class*="viewerBadge"], div[class*="styles_viewerBadge"],',
            'div[class*="manageApp"], div[class*="HostBadge"], div[class*="FloatingBadge"],',
            'div[class*="embeddedAppMetaInfoBar"], div[class*="stDeployButton"],',
            'a[class*="viewerBadge"], a[href*="github.com"], a[href*="streamlit.io"],',
            'img[src*="githubusercontent.com"], img[src*="identicon"], #GithubIcon, svg[class*="viewerBadge"] {',
            '  display: none !important;',
            '  visibility: hidden !important;',
            '  opacity: 0 !important;',
            '  pointer-events: none !important;',
            '  width: 0 !important;',
            '  height: 0 !important;',
            '  margin: 0 !important;',
            '  padding: 0 !important;',
            '  position: absolute !important;',
            '  left: -9999px !important;',
            '}'
          ].join(' ');
          targetDoc.head.appendChild(stEl);
        }
      } catch(e) {}

      function guardSelectInput(inp) {
        if (!inp) return;
        inp.setAttribute('inputmode', 'none');
        inp.setAttribute('readonly', 'readonly');
        inp.readOnly = true;
        inp.setAttribute('autocomplete', 'off');
        inp.setAttribute('autocorrect', 'off');
        inp.setAttribute('autocapitalize', 'off');
        inp.setAttribute('spellcheck', 'false');
      }

      function scanAllSelectboxes() {
        try {
          var inputs = targetDoc.querySelectorAll('[data-baseweb="select"] input, [data-testid="stSelectbox"] input');
          for (var i = 0; i < inputs.length; i++) {
            guardSelectInput(inputs[i]);
          }
        } catch(err) {}
      }

      function removeBottomBadgesAndLogos() {
        try {
          var sel = [
            'footer',
            '[data-testid="stFooter"]',
            'div[class*="viewerBadge"]',
            'div[class*="styles_viewerBadge"]',
            '.viewerBadge_container__1QSob',
            '.styles_viewerBadge__1yB5_',
            'a[href*="github.com"]',
            'a[href*="streamlit.io"]',
            '[data-testid="manage-app-button"]',
            '#manage-app-button',
            '[aria-label*="Manage app"]',
            'button[aria-label*="Manage app"]',
            'img[src*="githubusercontent.com"]',
            'img[src*="identicon"]',
            '#GithubIcon',
            'div[class*="manageApp"]',
            'div[class*="embeddedAppMetaInfoBar"]',
            'div[class*="HostBadge"]'
          ].join(',');
          var badEls = targetDoc.querySelectorAll(sel);
          for (var j = 0; j < badEls.length; j++) {
            badEls[j].style.setProperty('display', 'none', 'important');
            badEls[j].style.setProperty('visibility', 'hidden', 'important');
            badEls[j].style.setProperty("opacity", "0", "important"); badEls[j].style.setProperty("pointer-events", "none", "important");
          }

          var floatingCandidates = targetDoc.querySelectorAll('body > div, body > a, body > button, #root ~ div');
          for (var k = 0; k < floatingCandidates.length; k++) {
            var el = floatingCandidates[k];
            if (!el || el.id === 'root' || el.hasAttribute('data-baseweb')) continue;
            var txt = (el.innerText || el.textContent || '').toLowerCase();
            var h = el.innerHTML || '';
            if (txt.indexOf('manage app') !== -1 || txt.indexOf('streamlit') !== -1 ||
                h.indexOf('githubusercontent') !== -1 || h.indexOf('identicon') !== -1 ||
                h.indexOf('streamlit.io') !== -1 || h.indexOf('github.com') !== -1) {
              el.style.setProperty('display', 'none', 'important');
              el.style.setProperty('visibility', 'hidden', 'important');
              el.style.setProperty("opacity", "0", "important"); el.style.setProperty("pointer-events", "none", "important");
            }
          }
        } catch(err) {}
      }

      scanAllSelectboxes();
      removeBottomBadgesAndLogos();

      var handleTouch = function(e) {
        var target = e.target;
        if (!target) return;
        var selectEl = target.closest ? (target.closest('[data-baseweb="select"]') || target.closest('[data-testid="stSelectbox"]')) : null;
        if (selectEl) {
          var inp = selectEl.querySelector('input');
          if (inp) {
            guardSelectInput(inp);
          }
        }
      };

      targetDoc.addEventListener('touchstart', handleTouch, { capture: true, passive: true });
      targetDoc.addEventListener('pointerdown', handleTouch, { capture: true, passive: true });
      targetDoc.addEventListener('click', handleTouch, { capture: true, passive: true });
      targetDoc.addEventListener('focusin', function(e) {
        var target = e.target;
        if (target && target.tagName === 'INPUT') {
          var selectEl = target.closest ? (target.closest('[data-baseweb="select"]') || target.closest('[data-testid="stSelectbox"]')) : null;
          if (selectEl) {
            guardSelectInput(target);
          }
        }
      }, { capture: true });

      if (window.MutationObserver && targetDoc.body) {
        var observer = new MutationObserver(function() {
          scanAllSelectboxes();
          removeBottomBadgesAndLogos();
        });
        observer.observe(targetDoc.body, { childList: true, subtree: true });
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMobileDropdownGuard);
  } else {
    initMobileDropdownGuard();
  }
  setTimeout(initMobileDropdownGuard, 100);
  setTimeout(initMobileDropdownGuard, 500);
  setTimeout(initMobileDropdownGuard, 1500);
})();
"""

POLYFILL_SCRIPT = f"""<!-- ASMA Polyfill v3.1 No-Remove & Safe DOM Reconciliation Guard -->
<meta name="google" content="notranslate">
<script>
// Prevent React 18 / DOM reconciliation crash 'Node.removeChild: The node to be removed is not a child of this node'
(function() {{
  if (typeof Node !== 'undefined' && Node.prototype) {{
    var origRemoveChild = Node.prototype.removeChild;
    Node.prototype.removeChild = function(child) {{
      if (child && child.parentNode !== this) {{
        if (console && console.warn) {{
          console.warn("Prevented Node.removeChild crash: child is not a child of this node", child);
        }}
        return child;
      }}
      return origRemoveChild.apply(this, arguments);
    }};

    var origInsertBefore = Node.prototype.insertBefore;
    Node.prototype.insertBefore = function(newNode, referenceNode) {{
      if (referenceNode && referenceNode.parentNode !== this) {{
        if (console && console.warn) {{
          console.warn("Prevented Node.insertBefore crash: referenceNode is not a child of this node", referenceNode);
        }}
        return this.appendChild(newNode);
      }}
      return origInsertBefore.apply(this, arguments);
    }};
  }}
}})();

(function() {{
  if (!Array.prototype.toSorted) {{
    Array.prototype.toSorted = function(compareFn) {{
      return this.slice().sort(compareFn);
    }};
  }}
  if (!Array.prototype.toReversed) {{
    Array.prototype.toReversed = function() {{
      return this.slice().reverse();
    }};
  }}
  if (!Array.prototype.toSpliced) {{
    Array.prototype.toSpliced = function() {{
      var copy = this.slice();
      copy.splice.apply(copy, arguments);
      return copy;
    }};
  }}
  if (!Array.prototype.with) {{
    Array.prototype.with = function(index, value) {{
      var copy = this.slice();
      var actualIndex = index < 0 ? copy.length + index : index;
      copy[actualIndex] = value;
      return copy;
    }};
  }}
}})();
{MOBILE_DROPDOWN_GUARD_JS}
</script>
"""


def ensure_streamlit_index_patched() -> bool:
    """Legacy helper maintained for backward compatibility (no-op in FastAPI + PWA)."""
    return False
