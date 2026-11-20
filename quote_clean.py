# 11-20 owner quotes (Elijah, from the site videos: the Kia Forte quote had typos). One rule for every NHTSA owner quote on the site:
#   1. light spelling cleanup only: broken characters (â€™ -> ’), obvious misspellings from a fixed list, missing apostrophes
#      (dont -> don't), a lone "i" -> "I", spaces before punctuation, a capital first letter. The owner's words are never rewritten.
#   2. a quote with an odd word (likely a typo) is used only when no clean one is left; a quote that is still garbled after that (2+ words that aren't in the owner-complaint vocabulary, data/quote_vocab.json from
#      tools/quote_vocab.py), cut off mid-sentence ("... and"), or a staff letter naming people is skipped. A page with no clean quote
#      shows no quote box rather than a garbled one.
# Used by build.py (exec) on data/years.json and the other quote sources, and by data_years.py when it picks quotes.
import json as _qc_json, os as _qc_os, re as _qc_re
_QC_DIR = _qc_os.path.dirname(_qc_os.path.abspath(__file__)) if '__file__' in globals() else '.'
try: QC_VOCAB = dict(_qc_json.load(open(_qc_os.path.join(_QC_DIR, 'data', 'quote_vocab.json'), encoding='utf-8')))
except FileNotFoundError: QC_VOCAB = {}
_qc_known = lambda w: QC_VOCAB.get(w, 0) >= (300 if len(w) <= 3 else 15)   # short slips ("om", "mu") are common, so short words need more use
QC_FIX = {'dispite': 'despite', 'foward': 'forward', 'fowards': 'forwards', 'recieve': 'receive', 'recieved': 'received', 'untill': 'until',
          'alot': 'a lot', 'definately': 'definitely', 'definatly': 'definitely', 'becuase': 'because', 'beacuse': 'because', 'accross': 'across',
          'wierd': 'weird', 'seperate': 'separate', 'seperately': 'separately', 'occured': 'occurred', 'occuring': 'occurring', 'begining': 'beginning',
          'accelorate': 'accelerate', 'accelarate': 'accelerate', 'excelerate': 'accelerate', 'acclerate': 'accelerate', 'accelaration': 'acceleration',
          'transmision': 'transmission', 'tranmission': 'transmission', 'transmisson': 'transmission', 'stearing': 'steering', 'steeing': 'steering',
          'vehical': 'vehicle', 'vehicule': 'vehicle', 'dealrship': 'dealership', 'dealearship': 'dealership', 'dealershio': 'dealership',
          'engin': 'engine', 'alternater': 'alternator', 'batery': 'battery', 'bateries': 'batteries', 'accidant': 'accident', 'accedent': 'accident',
          'acident': 'accident', 'accidint': 'accident', 'happend': 'happened', 'happed': 'happened', 'stoped': 'stopped', 'droped': 'dropped',
          'shuting': 'shutting', 'immediatly': 'immediately', 'immediatley': 'immediately', 'recal': 'recall', 'reccall': 'recall', 'warrenty': 'warranty',
          'warrantee': 'warranty', 'tommorow': 'tomorrow', 'wich': 'which', 'thier': 'their', 'beleive': 'believe',
          'basicly': 'basically', 'probaly': 'probably', 'proably': 'probably', 'everytime': 'every time', 'infront': 'in front',
          'dont': "don't", 'didnt': "didn't", 'doesnt': "doesn't", 'isnt': "isn't", 'wasnt': "wasn't", 'werent': "weren't", 'couldnt': "couldn't",
          'wouldnt': "wouldn't", 'shouldnt': "shouldn't", 'havent': "haven't", 'hasnt': "hasn't", 'hadnt': "hadn't", 'arent': "aren't", 'cant': "can't",
          'wont': "won't", 'ive': "I've", 'im': "I'm", 'id': None, 'youre': "you're", 'theyre': "they're", 'thats': "that's", 'whats': "what's"}
QC_FIX = {k: v for k, v in QC_FIX.items() if v}
_QC_MOJI = _qc_re.compile(r'[\xc2-\xf4][\x80-\xbf]{1,3}')
def _qc_moji(m):
    try: return m.group(0).encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError): return m.group(0)
def _qc_case(src, dst):
    return dst[0].upper() + dst[1:] if src[:1].isupper() and dst[:1].islower() else dst
def QC_TIDY(t):
    """Light spelling cleanup of one owner quote (see the top of this file)."""
    t = _QC_MOJI.sub(_qc_moji, t or '')
    t = _qc_re.sub(r'\s*INFORMATION REDACTED PURSUANT TO.*$', '', t, flags=_qc_re.S)   # NHTSA's redaction note
    t = _qc_re.sub(r'\b(could|would|should|did|does|do|is|was|were|are|has|have|had)\s+nt\b', r"\1n't", t, flags=_qc_re.I)   # "could nt"
    t = _qc_re.sub(r"[A-Za-z]+(?:'[a-z]+)?", lambda m: _qc_case(m.group(0), QC_FIX[m.group(0).lower()]) if m.group(0).lower() in QC_FIX else m.group(0), t)
    t = _qc_re.sub(r"(?<![\w.'’])i(?=[\s,.;:!?']|$)", 'I', t)
    t = _qc_re.sub(r'\s+([,.;:!?])', r'\1', t)          # "away ." -> "away."
    t = _qc_re.sub(r'([,;:])(?=[A-Za-z])', r'\1 ', t)   # "wrong,the" -> "wrong, the"
    t = _qc_re.sub(r'\.{4,}', '...', t)
    t = _qc_re.sub(r'\s{2,}', ' ', t).strip()
    return t[:1].upper() + t[1:]
_QC_END = {'and', 'the', 'a', 'an', 'my', 'but', 'or', 'i', 'of', 'with'}
_QC_STAFF = _qc_re.compile(r'\b(ltr|letter)\b.{0,30}\b(on behalf|from (congressman|senator|rep))|\bconstituent\b|\battn\b', _qc_re.I)
def QC_ODD(t):
    """Words in the quote that owners almost never write: likely typos. Capitalized words (names, brands) and numbers don't count."""
    if not QC_VOCAB: return []
    return [w for w in _qc_re.findall(r"(?<![\w/])[A-Za-z]+(?:['’][a-z]+)?(?![\w/])", t) if w[:1].islower() and len(w) > 1 and not _qc_known(_qc_re.sub(r"['’]s$", '', w).lower())]
def QC_OK(t):
    """Clean enough to show as an owner quote (after QC_TIDY)."""
    if _QC_STAFF.search(t) or '[XXX]' in t: return False
    ws = _qc_re.findall(r"[A-Za-z']+", t)
    if not ws: return False
    if t[-1:].isalpha() and ws[-1].lower() in _QC_END: return False   # cut off mid-sentence ("... I have a bad accident and")
    if sum(ch.isupper() for ch in t) > .5 * sum(ch.isalpha() for ch in t): return False
    return len(QC_ODD(t)) < 2
def QC_PICK(qs):
    """The tidied quotes that pass QC_OK, cleanest first: quotes with no odd word keep their order; a quote with one odd word is used
    only when no fully clean quote is left (pick a cleaner quote over a typo). Each quote dict keeps its other fields."""
    ok = []
    for q in qs or []:
        t = QC_TIDY(q.get('text', ''))
        if QC_OK(t): ok.append((len(QC_ODD(t)), dict(q, text=t)))
    clean = [q for n, q in ok if n == 0]
    return clean or [q for n, q in ok][:1]
