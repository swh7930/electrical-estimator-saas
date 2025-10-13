// (moved from templates/base.html → scripts block)
(function () {
  const token =
    document
      .querySelector('meta[name="csrf-token"]')
      ?.getAttribute("content") || "";
  const _fetch = window.fetch;
  window.fetch = function (input, init) {
    init = init || {};
    init.headers = init.headers || {};
    if (!("X-CSRFToken" in init.headers)) {
      init.headers["X-CSRFToken"] = token;
    }
    return _fetch(input, init);
  };
})();