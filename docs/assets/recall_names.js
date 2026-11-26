// recall_names.js (round 5, 11-25): turn one raw NHTSA recall into plain English for a buyer.
//   recallName({ Component, Summary, Consequence }) -> { name, what, area, sentence }
//   name      the part, as a buyer says it ("Hood", "Anti-lock brakes", "Spare tire")
//   what      what goes wrong, one short clause (<= 100 characters)
//   area      the broad area the site uses on recall pages ("body structure", "brakes")
//   sentence  the full one-sentence summary the site shows under each recall
// Input is NHTSA's recallsByVehicle record as-is (api.nhtsa.gov/recalls/recallsByVehicle): Component, Summary, Consequence.
//
// Where the logic comes from (Lemon Index site repo, C:\Users\elift\Code\lemon-soon):
//   - PART + RPART in build.py: NHTSA's top-level component -> the site's plain area name  (ported as AREA / area())
//   - rsum() in build.py, and sentence() in docs/assets/vin.js and docs/assets/rc.js: drop NHTSA's
//     "X is recalling certain ... vehicles ..." opener and keep the first defect sentence; fall back to the
//     consequence ("risk") text when what's left is too short                                   (ported as sentence())
// Added here, so the short name reads well on a phone (no hand-written names anywhere):
//   1. name: the most specific part in the component path that a buyer knows (PARTS list below: generic NHTSA
//      component words, not per-recall). "STRUCTURE:BODY:HOOD:HINGE AND ATTACHMENTS" -> "Hood".
//   2. what: the first sentence that says what goes wrong (may / can / could / fail / not / incorrect / missing ...),
//      "In the affected vehicles," dropped, cut before ", allowing" / " resulting in" / ", which" / ", possibly" ...,
//      then a short list of generic NHTSA phrases swapped for buyer words (PLAIN: "electronic control unit (ECU)" -> "computer").
// Works in the browser (window.recallName) and in Node (module.exports). No network, no keys.
(function (root) {
  // build.py PART (11-11), same keys and words
  var AREA = { 'ELECTRICAL SYSTEM': 'electrical', 'POWER TRAIN': 'transmission & drivetrain', 'SERVICE BRAKES': 'brakes', 'VEHICLE SPEED CONTROL': 'speed control',
    'FUEL/PROPULSION SYSTEM': 'fuel or EV drive system', 'FORWARD COLLISION AVOIDANCE': 'automatic emergency braking', 'VISIBILITY/WIPER': 'wipers & visibility',
    'VISIBILITY': 'visibility', 'AIR BAGS': 'airbags', 'STRUCTURE': 'body structure', 'EXTERIOR LIGHTING': 'lights', 'ELECTRONIC STABILITY CONTROL (ESC)': 'stability control',
    'LANE DEPARTURE': 'lane assist', 'ENGINE AND ENGINE COOLING': 'engine', 'SEAT BELTS': 'seat belts' };
  // build.py RPART: the area of the first component segment, "service brakes, hydraulic" -> "brakes"
  function area(comp) {
    var top = String(comp || 'other').split(':')[0].trim();
    return (AREA[top] || top.toLowerCase()).replace('service brakes, hydraulic', 'brakes');
  }
  // parts a buyer knows, most specific first (checked against every segment of the component path, deepest segment first)
  var PARTS = [
    [/ANTILOCK|\bABS\b/, 'Anti-lock brakes'], [/PARKING BRAKE/, 'Parking brake'], [/BRAKE (HOSE|LINE|PIPE)/, 'Brake lines'], [/BRAKE/, 'Brakes'],
    [/SPARE TIRE/, 'Spare tire'], [/\bTIRE/, 'Tires'], [/\bWHEEL/, 'Wheels'],
    [/AIR ?BAG/, 'Airbags'], [/SEAT BELT|RESTRAINT/, 'Seat belts'], [/\bSEAT/, 'Seats'],
    [/\bHOOD\b/, 'Hood'], [/\bDOOR/, 'Doors'], [/LIFTGATE|TAILGATE|TRUNK/, 'Tailgate or trunk'], [/WINDSHIELD|WINDOW|GLASS/, 'Glass'],
    [/STEERING/, 'Steering'], [/SUSPENSION/, 'Suspension'], [/FUEL PUMP/, 'Fuel pump'], [/FUEL/, 'Fuel system'],
    [/HEADLIGHT|HEADLAMP/, 'Headlights'], [/LIGHT|LAMP/, 'Lights'], [/WIPER/, 'Wipers'], [/CAMERA/, 'Rearview camera'],
    [/TRANSMISSION|POWER TRAIN|DRIVESHAFT|AXLE/, 'Transmission & drivetrain'], [/ENGINE/, 'Engine'], [/BATTERY/, 'Battery'],
    [/LABEL/, 'Labels'], [/ELECTRICAL|WIRING/, 'Electrical'], [/SPEED CONTROL|CRUISE/, 'Cruise control'],
  ];
  function partName(comp, summary) {
    if (/LABEL/i.test(comp || '') && /tire|placard|load|weight/i.test(summary || '')) return 'Tire and load label';
    var segs = String(comp || '').toUpperCase().split(':').map(function (s) { return s.trim(); }).filter(Boolean).reverse();
    for (var i = 0; i < segs.length; i++) for (var j = 0; j < PARTS.length; j++) if (PARTS[j][0].test(segs[i])) return PARTS[j][1];
    var a = area(comp); return a.charAt(0).toUpperCase() + a.slice(1);
  }
  var clean = function (s) { return String(s || '').replace(/\s+/g, ' ').trim(); };
  var OPENER = /^.*?\brecalling\b.*?\b(vehicles|trucks|pick-ups|pickups|cars|SUVs|equipment|tires|seats|motorcycles)\b(?:[^.]|\.(?=\d))*?(?<!\bCo)(?<!\bInc)\.(?!\d)\s*/i;
  var SPLIT = /(?<!\bCo)(?<!\bInc)(?<!\bCorp)(?<!\bNo)\.\s+(?=[A-Z(])/;
  // build.py rsum(): skip the "X is recalling certain ... vehicles ..." opener, keep the defect; fall back to the consequence text
  function sentence(r) {
    var s = clean(r.Summary).replace(OPENER, '');
    var first = (s.split(SPLIT)[0] || '').trim().replace(/\.$/, '');
    if (first.length < 25 || /recalling/i.test(first)) first = clean(r.Consequence).replace(/\.$/, '');
    first = first ? first + '.' : '';
    return first.length <= 220 ? first : first.slice(0, 220).replace(/\s+\S*$/, '').replace(/[,;:]$/, '') + '…';
  }
  // generic NHTSA wording -> words a buyer uses (applies to any recall, not written for one)
  var PLAIN = [[/requires the use of/gi, 'needs'], [/electronic control unit \(ECU\)|control unit\/module|control module/gi, 'computer'], [/\bmay malfunction\b/gi, 'may fail'],
    [/\bmay not operate as designed\b/gi, 'may not work right'], [/occupant (sensing|classification) system/gi, 'passenger airbag sensor'], [/\bcomponent\b/gi, 'part'],
    [/\bwithin\b/gi, 'in'], [/adhesive attaching/gi, 'glue holding'], [/tire and loading information placard/gi, 'tire label'], [/\s*\bon each vehicle\b/gi, ''],
    [/\bcontains inaccurate\b/gi, 'shows the wrong'], [/\b(list|show)s? incorrect\b/gi, 'show the wrong'], [/\binoperative\b/gi, 'stop working'], [/\band\/or\b/gi, 'or'],
    [/\binformation\b/gi, 'info'], [/\bair bag/gi, 'airbag'], [/\bexperience an increased resistance\b/gi, 'develop high resistance'], [/\bthe vehicle\b/gi, 'the car'], [/\bto attach it to the car\b/gi, '']];
  var BAD = /\b(may|can|could|might|fail|fails|failed|not|incorrect|inaccurate|missing|without|detach|break|crack|leak|loose)\b/i;
  function what(r) {
    var parts = clean(r.Summary).replace(OPENER, '').split(SPLIT).map(clean).filter(Boolean);
    if (parts.length && parts.join(' ') === parts.join(' ').toUpperCase()) parts = parts.map(function (x) { return x.toLowerCase(); });  // ALL-CAPS older recalls
    var i = -1;
    parts.some(function (x, k) { if (BAD.test(x) && !/recalling|comply with|federal motor vehicle safety standard/i.test(x)) { i = k; return true; } });
    // "These lug nuts were not provided ...": a sentence that leans on the one before it -> use that one instead
    if (i > 0 && /^(these|this|they|it)\b/i.test(parts[i])) i -= 1;
    var cq = clean(r.Consequence); if (cq === cq.toUpperCase()) cq = cq.toLowerCase();
    var t = i >= 0 ? parts[i] : (cq.split(/\.\s+/)[0] || parts[0] || '');
    t = t.replace(/^(in|on) (the )?(affected|these|some|certain|subject) (vehicles|trucks|cars|models)[^,]*,\s*/i, '')
         .replace(/^(during|while|without) [^,]{0,120},\s*/i, '')
         .replace(/^(as such|thus|therefore|additionally),\s*/i, '')
         .replace(/^the (affected )?(vehicles|trucks|cars) (may )?/i, function (m, a, b, may) { return may ? 'may ' : ''; })
         .split(/,?\s+(?:allowing|resulting in|which|causing|increasing|potentially|possibly|and could|that could|so the)\b|;/i)[0]
         .replace(/\.$/, '').trim();
    PLAIN.forEach(function (w) { t = t.replace(w[0], w[1]); });
    t = t.replace(/\s+/g, ' ').trim(); t = t.charAt(0).toUpperCase() + t.slice(1);
    return t.length <= 100 ? t : t.slice(0, 98).replace(/\s+\S*$/, '').replace(/[,;:]$/, '') + '…';
  }
  function recallName(r) { return { name: partName(r.Component, r.Summary), what: what(r), area: area(r.Component), sentence: sentence(r) }; }
  if (typeof module !== 'undefined' && module.exports) module.exports = { recallName: recallName, area: area, sentence: sentence };
  else root.recallName = recallName;
})(this);
