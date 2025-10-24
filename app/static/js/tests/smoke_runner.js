(function () {
  const resultsEl = document.getElementById('results');
  const tests = [];
  const log = (cls, msg) => {
    const p = document.createElement('p');
    p.className = cls; p.textContent = msg;
    resultsEl.appendChild(p);
  };
  window.test = function (name, fn) { tests.push({ name, fn }); };
  window.expect = function (cond, msg) { if (!cond) throw new Error(msg || 'Expectation failed'); };
  window.expectEq = function (a, b, msg) {
    if (JSON.stringify(a) !== JSON.stringify(b)) {
      throw new Error((msg ? msg + ' — ' : '') + `expected ${JSON.stringify(b)}, got ${JSON.stringify(a)}`);
    }
  };

  window.addEventListener('load', async () => {
    let pass = 0, fail = 0;
    for (const t of tests) {
      try { await t.fn(); pass++; log('ok', `✔ ${t.name}`); }
      catch (e) { fail++; console.error(t.name, e); log('fail', `✖ ${t.name}: ${e.message}`); }
    }
    const summary = `${pass} passed, ${fail} failed`;
    (fail ? log.bind(null, 'fail') : log.bind(null, 'ok'))(`Done: ${summary}`);
  });
})();
