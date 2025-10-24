// Clear slate
localStorage.clear();
history.replaceState(null, '', location.pathname); // remove any existing ?eid

test('FAST namespace exists and is isolated from EIDs', () => {
  const kF = nsKeys(); // no eid
  expectEq(kF.ns, 'ee.FAST.', 'FAST ns should be ee.FAST.');
  expectEq(kF.totalsKey, 'ee.FAST.totals');
  localStorage.setItem(kF.totalsKey, JSON.stringify({ total_material: 111 }));
  expect(localStorage.getItem('ee.FAST.totals') !== null, 'FAST totals should be set');
});

test('E1 and E2 use disjoint keys', () => {
  history.replaceState(null, '', '?eid=E1');
  const k1 = nsKeys();
  expectEq(k1.ns, 'ee.E1.');
  localStorage.setItem(k1.totalsKey, JSON.stringify({ total_material: 222 }));
  localStorage.setItem(k1.estimateDataKey, JSON.stringify({ rows: [{ id: 1 }] }));

  history.replaceState(null, '', '?eid=E2');
  const k2 = nsKeys();
  expectEq(k2.ns, 'ee.E2.');
  localStorage.setItem(k2.totalsKey, JSON.stringify({ total_material: 333 }));
  localStorage.setItem(k2.estimateDataKey, JSON.stringify({ rows: [{ id: 9 }] }));

  expectEq(localStorage.getItem('ee.E1.totals') !== null, true, 'E1 totals present');
  expectEq(localStorage.getItem('ee.E2.totals') !== null, true, 'E2 totals present');
  expectEq(localStorage.getItem('ee.FAST.totals') !== null, true, 'FAST totals present');
});

test('When eid is present, consumers read EID keys (not FAST)', () => {
  history.replaceState(null, '', '?eid=E1');
  const { totalsKey, estimateDataKey } = nsKeys();
  expect(totalsKey.startsWith('ee.E1.'), 'Totals key should be E1-scoped');
  expect(estimateDataKey.startsWith('ee.E1.'), 'EstimateData key should be E1-scoped');

  const v = JSON.parse(localStorage.getItem(totalsKey));
  expectEq(v.total_material, 222, 'E1 totals must win over FAST/E2');
});

test('No bare "estimateData" key is ever used', () => {
  // Ensure legacy bare key is absent
  expectEq(localStorage.getItem('estimateData'), null, 'Legacy estimateData should not exist');
});
