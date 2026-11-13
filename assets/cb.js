// 11-12 /best/ pages (best_ui.py): the "Check the VIN" box hands the VIN to /vin/ in the URL hash (#v=...), so it never reaches a server log.
// Without JS the form still opens /vin/ (the input has no name, so nothing is sent).
(function () {
  document.querySelectorAll('form.cbx-vinf').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      var v = (f.querySelector('input').value || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
      if (!v) return; e.preventDefault(); location.href = '/vin/#v=' + v;
    });
  });
})();
