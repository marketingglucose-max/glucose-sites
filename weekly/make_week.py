#!/usr/bin/env python3
"""Собирает weekly/data/<понедельник>.json из сырых данных сборщика (raw-*.json),
замеров подписчиков (followers.json), выгрузки Metricool (metricool.json) и выводов (notes-*.json).
Запуск: python3 weekly/make_week.py 2026-11-16"""
import json, re, os, sys, statistics as st, datetime as dt
R = os.path.dirname(os.path.abspath(__file__))
D = lambda s: dt.date.fromisoformat(s)
CONFIG = {
 '2026-11-16': {'g_from': '2026-11-16', 'g_to': '2026-11-24', 'pg_from': '2026-11-09', 'pg_to': '2026-11-16',
                'measured_at': '25.11.2026, 12:00–13:30 по Алматы',
                'growth_note': 'Замеров за 21–23.11 нет, поэтому прирост этой недели — за 8 дней (16.11 → 24.11), прошлой — за 7 дней (09.11 → 16.11).',
                'unavailable': {'zerdeli.ubt': 'страница не открывается (с 18.11 нет и в замерах подписчиков)', 'kzchemistry': 'закрыл нам доступ'}},
}
def pv(s):
    if not s: return None
    s = s.replace('\xa0', ' ').strip(); m = re.match(r'([\d ,]+)\s*(тыс|млн)?', s)
    if not m: return None
    n = float(m.group(1).replace(' ', '').replace(',', '.'))
    return int(round(n * (1000 if m.group(2) == 'тыс' else 1e6 if m.group(2) == 'млн' else 1)))
def viral(p): return p['likes'] is not None and p['likes'] > (500 if p['t'] == 'reel' else 1000)

W = sys.argv[1]; C = CONFIG[W]
end = (D(W) + dt.timedelta(days=6)).isoformat(); prevW = (D(W) - dt.timedelta(days=7)).isoformat()
raw = json.load(open(f'{R}/data/raw-{W}.json', encoding='utf-8'))
F = json.load(open(f'{R}/data/followers.json')); MC = json.load(open(f'{R}/data/metricool.json'))
accs = []
for a, ps in raw.items():
    posts = [{'c': p[0], 'd': '2026-' + p[1], 't': 'reel' if p[2] else 'p', 'likes': p[3], 'com': p[4], 'views': pv(p[5]), 'cap': p[6]} for p in ps]
    f1, f0 = F[C['g_to']].get(a), F[C['g_from']].get(a)
    p1, p0 = F[C['pg_to']].get(a), F[C['pg_from']].get(a)
    accs.append({'a': a, 'posts': posts, 'followers': f1, 'growth': f1 - f0 if f1 and f0 else None,
                 'growth_prev': p1 - p0 if p1 and p0 else None, 'blocked': a in C['unavailable']})
# прошлая неделя Glucose — из её файла
pw = json.load(open(f'{R}/data/{prevW}.json', encoding='utf-8'))
me = next(x for x in pw['accounts'] if x['a'] == 'glucose.online')
vs = [p['views'] for p in me['posts'] if p['t'] == 'reel' and p.get('views')]
gr = sorted([x for x in pw['accounts'] if x.get('growth') is not None], key=lambda x: -x['growth'])
gprev = {'n': len(me['posts']), 'np': sum(p['t'] != 'reel' for p in me['posts']), 'nr': sum(p['t'] == 'reel' for p in me['posts']),
         'vir': sum(viral(p) for p in me['posts']), 'median_views': int(st.median(vs)), 'best_views': max(vs),
         'growth': me['growth'], 'growth_rank': 1 + sum(x['growth'] > me['growth'] for x in gr)}
# Metricool: средние за сутки. Колонки: followers, gained, lost, feed posts, reels, reach, views, reels views, interactions, stories, content, engaged
keys = {'gained': 1, 'lost': 2, 'reach': 5, 'views': 6, 'reels_views': 7, 'interactions': 8, 'stories': 9}
def days(a): return [(D(a) + dt.timedelta(days=i)).isoformat() for i in range(7)]
def per_day(ds, i):
    v = [float(MC[d][i]) for d in ds if d in MC and MC[d][i] is not None]
    return round(sum(v) / len(v)) if v else None
mc = {k: {'cur': per_day(days(W), i), 'prev': per_day(days(prevW), i)} for k, i in keys.items()}
fmt = lambda s: D(s).strftime('%d.%m')
week = {
 'week': W, 'end': end, 'measured_at': C['measured_at'],
 'growth_from': fmt(C['g_from']) + ' ~12:00', 'growth_to': fmt(C['g_to']) + ' ~12:00', 'growth_note': C['growth_note'],
 'cur_label': f"{fmt(W)}–{fmt(end)}", 'prev_label': f"{fmt(prevW)}–{fmt((D(prevW)+dt.timedelta(days=6)).isoformat())}",
 'followers_date': fmt(C['g_to']), 'unavailable': C['unavailable'],
 'accounts': accs, 'glucose_prev': gprev,
 'glucose_daily_followers': {k: v for k, v in F['glucose_daily'].items() if C['g_from'] <= k <= C['g_to']},
 'metricool': mc, 'metricool_note': 'Средние за сутки по данным Metricool (дни, которые Metricool ещё не досчитал, не учитываются).',
 'notes': json.load(open(f'{R}/data/notes-{W}.json', encoding='utf-8')),
}
json.dump(week, open(f'{R}/data/{W}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', W, len(accs), sum(len(a['posts']) for a in accs), gprev, mc)
