#!/usr/bin/env python3
"""Собирает weekly/data/<понедельник>.json из сырых данных сборщика (raw-*.json),
замеров подписчиков (followers.json) и выгрузки Metricool. Запуск: python3 weekly/make_week.py"""
import json, re, os
R = os.path.dirname(os.path.abspath(__file__))
W = '2026-11-09'
raw = json.load(open(f'{R}/data/raw-{W}.json', encoding='utf-8'))
F = json.load(open(f'{R}/data/followers.json'))
def pv(s):
    if not s: return None
    s = s.replace('\xa0', ' ').strip(); m = re.match(r'([\d ,]+)\s*(тыс|млн)?', s)
    if not m: return None
    n = float(m.group(1).replace(' ', '').replace(',', '.'))
    return int(round(n * (1000 if m.group(2) == 'тыс' else 1e6 if m.group(2) == 'млн' else 1)))
accs = []
for a, ps in raw.items():
    posts = [{'c': p[0], 'd': '2026-' + p[1], 't': 'reel' if p[2] else 'p', 'likes': p[3], 'com': p[4], 'views': pv(p[5]), 'cap': p[6]} for p in ps]
    g = F['2026-11-16'][a] - F['2026-11-09'][a] if a in F['2026-11-16'] else None
    gp = F['2026-11-09'][a] - F['2026-11-02'][a] if a in F['2026-11-02'] else None
    accs.append({'a': a, 'posts': posts, 'followers': F['2026-11-16'].get(a), 'growth': g, 'growth_prev': gp, 'blocked': a == 'kzchemistry'})
# Metricool, Glucose. Колонки: followers, gained, lost, feed posts, reels, reach, views, reels views, interactions, stories, content, engaged
MC = {
 'cur': [["47931","195","75","1",None,"83301","209929",None,"638","1","2","2467","20261109"],["47980","128","101","1","2","56938","162854","42836","2186","8","11","2912","20261110"],["48009","115","64","2","3","59122","191091","21212","3116","7","12","3543","20261111"],["48021","99","86","1","3","43792","155479","41576","1786","8","12","2839","20261112"],["48062","96","76","2","3","47046","185382","45700","2253","8","13","3187","20261113"],["48121","112","66","1","3","29971","153406","32323","809","9","13","6568","20261114"]],
 'prev': [["47076","186","70",None,"2","59988","158875","15599","430","14","16","2170","20261102"],["47173","141","92","2","1","54615","151695","9588","2054","11","14","2971","20261103"],["47255","191","69","2","4","77754","233952","42976","6015","10","16","4142","20261104"],["47343","148","85","4","2","86824","260133","32967","3025","8","14","4173","20261105"],["47597","238","87","1","1","103235","277771","15242","4608","9","11","4434","20261106"],["47755","307","89","1","5","122179","367681","70935","5859","22","28","4196","20261107"],["47873","261","104",None,"3","103096","288023","53383","1406","17","20","3304","20261108"]]}
def per_day(rows, i):
    v = [float(r[i]) for r in rows if r[i] is not None]
    return round(sum(v) / len(v)) if v else None
keys = {'gained': 1, 'lost': 2, 'reach': 5, 'views': 6, 'reels_views': 7, 'interactions': 8, 'stories': 9}
mc = {k: {'cur': per_day(MC['cur'], i), 'prev': per_day(MC['prev'], i)} for k, i in keys.items()}
week = {
 'week': W, 'end': '2026-11-15', 'measured_at': '16.11.2026, 14:30–15:30 по Алматы',
 'growth_from': '09.11 ~12:00', 'growth_to': '16.11 ~12:00',
 'accounts': accs,
 'glucose_prev': {'n': 31, 'np': 10, 'nr': 21, 'vir': 3, 'median_views': 12200, 'best_views': 50000, 'growth': 895, 'growth_rank': 5},
 'glucose_daily_followers': F['glucose_daily'],
 'metricool': mc, 'metricool_note': 'Средние за сутки: эта неделя — 09–14.11 (за 15.11 Metricool ещё не досчитал), прошлая — 02–08.11.',
 'notes': json.load(open(f'{R}/data/notes-{W}.json', encoding='utf-8')),
}
json.dump(week, open(f'{R}/data/{W}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', W, len(accs), sum(len(a['posts']) for a in accs), mc)
