# Writes survey_worker.dist.js (the file uploaded to the lemon-survey Worker) from survey_worker.js + data/survey.json + data/votes.json.
import json, os
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H)
sv = json.load(open(os.path.join(R, 'data', 'survey.json'), encoding='utf-8')); vt = json.load(open(os.path.join(R, 'data', 'votes.json'), encoding='utf-8'))
Q = {q['id']: {'a': q['a'], 'car': True} for q in sv['car']}
Q.update({q['id']: {'a': q['a']} for q in sv['site']})
for site in ('lemon', 'bs'): Q.update({q['id']: {'a': q['a'], 'v': site} for q in vt[site]})
src = open(os.path.join(H, 'survey_worker.js'), encoding='utf-8').read(); assert src.count('__Q__') == 1
open(os.path.join(H, 'survey_worker.dist.js'), 'w', encoding='utf-8').write(src.replace('__Q__', json.dumps(Q, ensure_ascii=False, separators=(',', ':'))))
print('worker Q:', len(Q), 'questions')
