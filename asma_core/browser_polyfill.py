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
            try { badEls[j].remove(); } catch(e) {}
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
              try { el.remove(); } catch(e) {}
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

      setInterval(removeBottomBadgesAndLogos, 300);
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

POLYFILL_SCRIPT = f"""<!-- ASMA Legacy Tablet & Browser ES2023 Polyfills and Mobile Dropdown Guard -->
<script>
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
    """
    Ensures that the active Streamlit static index.html has ES2023 polyfills and
    mobile dropdown virtual keyboard suppression injected into its <head>.
    """
    try:
        import streamlit
        index_path = pathlib.Path(streamlit.__file__).parent / "static" / "index.html"
        if not index_path.exists():
            return False

        content = index_path.read_text(encoding="utf-8")
        if "initMobileDropdownGuard" in content and "Array.prototype.toSorted" in content:
            return True

        needle = "<head>"
        if needle in content:
            if "Array.prototype.toSorted" in content or "ASMA Legacy Tablet" in content:
                content = re.sub(r'<!-- ASMA Legacy Tablet.*?-->\s*<script>.*?</script>', '', content, flags=re.DOTALL)
            new_content = content.replace(needle, f"{needle}\n    {POLYFILL_SCRIPT}")
            index_path.write_text(new_content, encoding="utf-8")
            return True
        return False
    except Exception as e:
        logging.warning("Could not patch streamlit index.html with polyfills/mobile guard: %s", e)
        return False


# Automatically verify patch on import
ensure_streamlit_index_patched()
