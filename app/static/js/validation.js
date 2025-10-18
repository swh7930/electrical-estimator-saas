(function (global) {
  function collapseSpaces(s, maxLen) {
    if (!s) return "";
    let t = s.replace(/\s+/g, " ").trim();
    if (typeof maxLen === "number" && maxLen > 0 && t.length > maxLen) {
      t = t.slice(0, maxLen);
    }
    return t;
  }

  function validateEmail(s) {
    if (!s) return true;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);
  }

  function normalizePhone(s) {
    if (!s) return "";
    let digits = (s.match(/\d/g) || []).join("");
    if (digits.length === 11 && digits.startsWith("1")) digits = digits.slice(1);
    if (digits.length !== 10) return ""; // invalid
    return `(${digits.slice(0,3)}) ${digits.slice(3,6)}-${digits.slice(6)}`;
  }

  global.EM_VALID = { collapseSpaces, validateEmail, normalizePhone };
})(window);
