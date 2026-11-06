"""
ASMA Accordi Next Generation - Browser Compatibility Polyfills
Fixes ES2023 Array methods (toSorted, toReversed, toSpliced, with) on older Android/Huawei tablets.
"""

import sys
import pathlib
import logging

POLYFILL_SCRIPT = """<!-- ASMA Legacy Tablet & Browser ES2023 Polyfills -->
<script>
(function() {
  if (!Array.prototype.toSorted) {
    Array.prototype.toSorted = function(compareFn) {
      return this.slice().sort(compareFn);
    };
  }
  if (!Array.prototype.toReversed) {
    Array.prototype.toReversed = function() {
      return this.slice().reverse();
    };
  }
  if (!Array.prototype.toSpliced) {
    Array.prototype.toSpliced = function() {
      var copy = this.slice();
      copy.splice.apply(copy, arguments);
      return copy;
    };
  }
  if (!Array.prototype.with) {
    Array.prototype.with = function(index, value) {
      var copy = this.slice();
      var actualIndex = index < 0 ? copy.length + index : index;
      copy[actualIndex] = value;
      return copy;
    };
  }
})();
</script>
"""


def ensure_streamlit_index_patched() -> bool:
    """
    Ensures that the active Streamlit static index.html has ES2023 polyfills injected
    into its <head> before any module scripts execute.
    """
    try:
        import streamlit
        index_path = pathlib.Path(streamlit.__file__).parent / "static" / "index.html"
        if not index_path.exists():
            return False

        content = index_path.read_text(encoding="utf-8")
        if "Array.prototype.toSorted" in content:
            return True

        # Inject right after <head>
        needle = "<head>"
        if needle in content:
            new_content = content.replace(needle, f"{needle}\n    {POLYFILL_SCRIPT}")
            index_path.write_text(new_content, encoding="utf-8")
            return True
        return False
    except Exception as e:
        logging.warning("Could not patch streamlit index.html with polyfills: %s", e)
        return False


# Automatically verify patch on import
ensure_streamlit_index_patched()
