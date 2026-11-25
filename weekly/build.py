#!/usr/bin/env python3
"""Недельный анализ конкурентов Glucose.
Читает weekly/data/<понедельник>.json (готовит make_week.py) и пишет weekly/<понедельник>/index.html и weekly/index.html.
Запуск: python3 weekly/build.py"""
import json, os, sys, glob, statistics as st, datetime as dt
R = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(R, '..', 'daily'))
from build import CSS, esc, fnum, fk, sign, url, viral, bars, ME, POST_T, REEL_T, MON

def dshort(d): x = dt.date.fromisoformat(d); return f"{x.day:02d}.{x.month:02d}"
def period(w, e): a, b = dt.date.fromisoformat(w), dt.date.fromisoformat(e); return f"{a.day}–{b.day} {MON[b.month-1]} {b.year}"
def pct(a, b): return '—' if not b else (('+' if a >= b else '−') + f"{abs(round(100*(a-b)/b))}%")

def page(d):
    accs = d['accounts']; open_accs = [a for a in accs if not a.get('blocked')]
    for a in accs:
        a['pubs'] = a['posts']; a['np'] = sum(p['t'] != 'reel' for p in a['pubs']); a['nr'] = sum(p['t'] == 'reel' for p in a['pubs'])
        a['n'] = a['np'] + a['nr']; a['vir'] = [p for p in a['pubs'] if viral(p)]
        vs = [p['views'] for p in a['pubs'] if p['t'] == 'reel' and p.get('views')]
        a['vsum'] = sum(vs); a['vmed'] = int(st.median(vs)) if vs else None
    me = next(a for a in accs if a['a'] == ME)
    allp = [(a['a'], p) for a in open_accs for p in a['pubs']]
    total = len(allp); nvir = sum(viral(p) for _, p in allp)
    act = sorted(open_accs, key=lambda a: (-a['n'], a['a'] != ME))
    rank_act = 1 + sum(a['n'] > me['n'] for a in open_accs)
    gr = sorted([a for a in accs if a.get('growth') is not None], key=lambda a: -a['growth'])
    rank_gr = 1 + sum(a['growth'] > me['growth'] for a in gr)
    second = max([a['growth'] for a in gr[1:]] + [1]); gcap = second * 1.15 if gr[0]['growth'] > 3 * second else gr[0]['growth']
    reels = sorted([(a, p) for a, p in allp if p['t'] == 'reel' and p.get('views')], key=lambda x: -x[1]['views'])
    my_best = next(((i+1, a, p) for i, (a, p) in enumerate(reels) if a == ME), None)
    vl = sorted([(a, p) for a, p in allp if viral(p)], key=lambda x: -x[1]['likes'])
    share = sorted([a for a in open_accs if a['n']], key=lambda a: (-len(a['vir'])/a['n'], -a['n']))
    vsum = sorted([a for a in open_accs if a['vsum']], key=lambda a: -a['vsum'])
    rank_vsum = 1 + sum(a['vsum'] > me['vsum'] for a in vsum)
    notes = d['notes']; why = notes.get('why', {}); gp = d['glucose_prev']; mc = d['metricool']

    def item(a, p):
        cls = ' me' if a == ME else ''
        m = f"{fnum(p['likes'])} лайков" if p.get('likes') is not None else 'лайки скрыты'
        if p.get('views'): m += f"<br>{fk(p['views'])} просмотров"
        return f'<div class="item{cls}"><span class="chip">{"рилс" if p["t"]=="reel" else "пост"} · {dshort(p["d"])}</span><span class="t"><a href="{url(p)}" target="_blank" rel="noopener">@{esc(a)}</a><small>{esc((p.get("cap") or "без подписи")[:140])}</small></span><span class="m">{m}</span></div>'

    kp = [f'<div class="kpi dark"><b>{me["n"]}</b><span>публикаций Glucose ({me["np"]} постов, {me["nr"]} рилсов) · {rank_act}-е место из {len(open_accs)}</span></div>',
          f'<div class="kpi"><b>{sign(me["growth"])}</b><span>подписчиков за {esc(d['growth_from'][:5])}→{esc(d['growth_to'][:5])} · {rank_gr}-е место из {len(gr)} (неделей раньше {sign(gp["growth"])}, {gp["growth_rank"]}-е)</span></div>',
          f'<div class="kpi"><b>{len(me["vir"])} из {me["n"]}</b><span>публикаций Glucose залетели ({round(100*len(me["vir"])/me["n"])}%, в нише {round(100*nvir/total)}%)</span></div>']
    if my_best: kp.append(f'<div class="kpi"><b>{fk(my_best[2]["views"])}</b><span>лучший рилс Glucose · {my_best[0]}-е место из {len(reels)}</span></div>')

    whyhtml = ''.join(f'<div><b>@{esc(a["a"])} · {sign(a["growth"])}</b>{esc(why.get(a["a"], "—"))}</div>' for a in gr[:3])
    # growth table with previous week
    gtab = f'<div class="tbl"><table><tr><th>Аккаунт</th><th>Подписчиков {d.get("followers_date","16.11")}</th><th>Эта неделя</th><th>Прошлая неделя</th><th>Темп, %</th></tr>' + ''.join(
        f'<tr{" style=\"font-weight:700\"" if a["a"]==ME else ""}><td>@{esc(a["a"])}</td><td>{fnum(a["followers"])}</td><td>{sign(a["growth"])}</td><td>{sign(a["growth_prev"]) if a.get("growth_prev") is not None else "—"}</td><td>{f"{100*a['growth']/(a['followers']-a['growth']):+.2f}".replace('.', ',').replace('-', '−')}%</td></tr>'
        for a in gr) + '</table></div>'
    # Glucose daily growth
    gd = d['glucose_daily_followers']; ks = sorted(gd)
    gdrows = ''.join(f'<tr><td>{dshort(ks[i-1])} → {dshort(ks[i])}</td><td>{sign(gd[ks[i]]-gd[ks[i-1]])}</td><td>{esc(", ".join(f"{"рилс" if p["t"]=="reel" else "пост"} {fk(p["views"]) + " просм." if p.get("views") else str(p["likes"]) + " лайков"}" for p in sorted([p for p in me["pubs"] if ks[i-1] <= p["d"] < ks[i]], key=lambda p: -(p.get("views") or p["likes"] or 0))[:3]))}</td></tr>' for i in range(1, len(ks)))
    gdtab = f'<div class="tbl"><table><tr><th>Сутки (замер ~12:00)</th><th>Прирост</th><th>Самые сильные публикации за эти сутки</th></tr>{gdrows}</table></div>'
    # week over week
    vs_me = [p['views'] for p in me['pubs'] if p['t'] == 'reel' and p.get('views')]
    wow = [('Публикаций', f'{gp["n"]} ({gp["np"]} п. + {gp["nr"]} р.)', f'{me["n"]} ({me["np"]} п. + {me["nr"]} р.)', pct(me['n'], gp['n'])),
           ('Залетело', f'{gp["vir"]} ({round(100*gp["vir"]/gp["n"])}%)', f'{len(me["vir"])} ({round(100*len(me["vir"])/me["n"])}%)', pct(len(me['vir']), gp['vir'])),
           ('Медиана просмотров рилса', fk(gp['median_views']), fk(me['vmed']), pct(me['vmed'], gp['median_views'])),
           ('Лучший рилс', fk(gp['best_views']), fk(max(vs_me)), pct(max(vs_me), gp['best_views'])),
           ('Прирост подписчиков (замеры; периоды см. выше)', sign(gp['growth']), sign(me['growth']), pct(me['growth'], gp['growth']))]
    lab = {'gained': 'Пришло подписчиков', 'lost': 'Ушло подписчиков', 'reach': 'Охват аккаунта', 'views': 'Просмотры аккаунта', 'reels_views': 'Просмотры рилсов', 'interactions': 'Взаимодействия', 'stories': 'Сторис'}
    for k, l in lab.items():
        v = mc.get(k) or {}
        if v.get('cur') is not None: wow.append((l + ' в сутки · Metricool', fnum(v['prev']), fnum(v['cur']), pct(v['cur'], v['prev'])))
    wtab = f'<div class="tbl"><table><tr><th>Glucose</th><th>{d.get("prev_label","02–08.11")}</th><th>{d.get("cur_label","09–15.11")}</th><th>Изменение</th></tr>' + ''.join(f'<tr><td>{a}</td><td>{b}</td><td><b>{c}</b></td><td>{e}</td></tr>' for a, b, c, e in wow) + '</table></div>'
    place = [('Публикаций', str(me['n']), f'{rank_act} из {len(open_accs)}', f"@{act[0]['a']} — {act[0]['n']}"),
             ('Прирост подписчиков', sign(me['growth']), f'{rank_gr} из {len(gr)}', f"@{gr[0]['a']} — {sign(gr[0]['growth'])}"),
             ('Доля залетевших', f"{round(100*len(me['vir'])/me['n'])}%", f"{1+sum(len(a['vir'])/a['n'] > len(me['vir'])/me['n'] for a in share)} из {len(share)}", f"@{share[0]['a']} — {round(100*len(share[0]['vir'])/share[0]['n'])}%"),
             ('Сумма просмотров рилсов', fk(me['vsum']), f'{rank_vsum} из {len(vsum)}', f"@{vsum[0]['a']} — {fk(vsum[0]['vsum'])}"),
             ('Лучший рилс', fk(my_best[2]['views']), f'{my_best[0]} из {len(reels)}', f"@{reels[0][0]} — {fk(reels[0][1]['views'])}")]
    ptab = '<div class="tbl"><table><tr><th>Показатель</th><th>Glucose</th><th>Место</th><th>Лидер</th></tr>' + ''.join(f'<tr><td>{a}</td><td><b>{b}</b></td><td>{c}</td><td>{esc(e)}</td></tr>' for a, b, c, e in place) + '</table></div>'
    blocked = [a['a'] for a in accs if a.get('blocked')]
    miss = {}
    for a, p in allp:
        if p['t'] == 'reel' and not p.get('views'): miss[a] = miss.get(a, 0) + 1
    miss_note = (f" Без просмотров остались {sum(miss.values())} рилсов (" + ', '.join(f"{v} у @{k}" for k, v in sorted(miss.items(), key=lambda x: -x[1])) + ") — их не было на вкладке Reels.") if miss else ''
    unav = d.get('unavailable') or {b: 'закрыл нам доступ' for b in blocked}
    unav_note = ''.join(f" @{k}: {v} — публикаций и прироста за неделю нет." for k, v in unav.items())
    body = f'''
<header><p class="k">Glucose · недельный анализ · Instagram ҰБТ</p><h1>Неделя {period(d["week"], d["end"])}</h1>
<p class="sub">Публикации {len(open_accs)} аккаунтов за {d.get('cur_label','09.11–15.11')} (время Алматы). Лайки и просмотры сняты {esc(d["measured_at"])}. Прирост подписчиков — замеры {esc(d["growth_from"])} → {esc(d["growth_to"])}.</p>
<p class="nav"><a href="../index.html">← все недели</a><a href="../../daily/">ежедневный анализ</a><a href="../../glucose-competitor-analysis/">презентация 02–08.11</a></p></header>
<div class="kpis">{''.join(kp)}</div>
<div class="out"><b>Главное за неделю:</b> {esc(notes["summary"])}</div>
<section><h2>Прирост подписчиков за неделю</h2><p class="find">{esc(d.get('growth_note',''))}{' Полоса лидера обрезана — она намного длиннее.' if gr[0]['growth'] > gcap else ''}</p>
{bars(gr, lambda a: max(0, a['growth']), None, maxv=gcap, fmt=lambda a: sign(a['growth']))}
<h2>Топ-3 и за счёт чего</h2><div class="why">{whyhtml}</div>
<h2>Сравнение с прошлой неделей</h2>{gtab}</section>
<section><h2>Активность</h2><p class="find">Всего {total} публикаций в нише за неделю. Тёмная часть полосы — посты, светлая — рилсы.</p>
<div class="legend"><span><i style="background:var(--bar2)"></i>посты</span><span><i style="background:var(--bar)"></i>рилсы</span></div>
{bars([a for a in act if a['n']], lambda a: a['n'], None, split=lambda a: (a['np'], a['nr']), fmt=lambda a: str(a['n']))}</section>
<section><h2>Залетевшие публикации</h2><p class="find">Залетел: пост больше {POST_T} лайков, рилс больше {REEL_T}. За неделю залетело {nvir} из {total} ({round(100*nvir/total)}%). Ниже — топ-20 по лайкам и все залетевшие Glucose.</p>
<div class="list">{''.join(item(a, p) for a, p in vl[:20])}{''.join(item(a, p) for a, p in vl[20:] if a == ME)}</div>
<h2>Доля залетевших по аккаунтам</h2>
{bars(share, lambda a: round(100*len(a['vir'])/a['n']), None, maxv=100, fmt=lambda a: f"{round(100*len(a['vir'])/a['n'])}% · {len(a['vir'])} из {a['n']}")}</section>
<section><h2>Рилсы по просмотрам</h2><p class="find">Топ-15 рилсов недели из {len(reels)}. Лучший рилс Glucose — {my_best[0]}-е место.</p>
<div class="list">{''.join(item(a, p) for a, p in reels[:15])}</div>
<h2>Сумма просмотров рилсов за неделю</h2><p class="find">Медиана просмотров одного рилса — в скобках.</p>
{bars(vsum, lambda a: a['vsum'], None, fmt=lambda a: f"{fk(a['vsum'])} ({fk(a['vmed'])})")}</section>
<section><h2>Glucose: неделя к неделе</h2>{wtab}<p class="find">{esc(d["metricool_note"])}</p>
<h2>Glucose по дням</h2>{gdtab}</section>
<section><h2>Место Glucose</h2>{ptab}</section>
<div class="out"><b>Что взять в работу:</b> {esc(notes["todo"])}</div>
<footer>Источник: Instagram (страницы публикаций и вкладки Reels), ежедневные замеры подписчиков около 12:00 по Алматы, Metricool для Glucose. Совместные публикации засчитаны каждому соавтору. {miss_note}{unav_note}</footer>'''
    return f'<!doctype html>\n<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><meta name="claude:viewport-fit-sides" content="cover"><title>Glucose · неделя {dshort(d["week"])}–{dshort(d["end"])}</title><style>{CSS}</style></head><body><div class="wrap">{body}</div></body></html>\n'

def index(weeks):
    rows = ''.join(f'<a class="item" href="{w["week"]}/" style="text-decoration:none;color:inherit"><span class="chip">{dshort(w["week"])}–{dshort(w["end"])}</span><span class="t"><b>Неделя {period(w["week"], w["end"])}</b><small>{esc(w["notes"]["summary"][:200])}</small></span><span class="m">→</span></a>' for w in sorted(weeks, key=lambda w: w['week'], reverse=True))
    rows += '<a class="item" href="../glucose-competitor-analysis/" style="text-decoration:none;color:inherit"><span class="chip">02.11–08.11</span><span class="t"><b>Неделя 2–8 ноября 2026</b><small>Презентация: прирост, активность, залетевшее и разбор кейсов конкурентов.</small></span><span class="m">→</span></a>'
    body = f'<header><p class="k">Glucose · Instagram ҰБТ</p><h1>Недельный анализ конкурентов</h1><p class="sub">Публикации, залетевшее, просмотры и прирост подписчиков 20 аккаунтов за неделю, сравнение Glucose с прошлой неделей.</p><p class="nav"><a href="../daily/">ежедневный анализ →</a></p></header><div class="list">{rows}</div>'
    return f'<!doctype html>\n<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><meta name="claude:viewport-fit-sides" content="cover"><title>Glucose · недельный анализ</title><style>{CSS}</style></head><body><div class="wrap">{body}</div></body></html>\n'

if __name__ == '__main__':
    weeks = [json.load(open(f, encoding='utf-8')) for f in sorted(glob.glob(os.path.join(R, 'data', '20*.json')))]
    for w in weeks:
        os.makedirs(os.path.join(R, w['week']), exist_ok=True)
        open(os.path.join(R, w['week'], 'index.html'), 'w', encoding='utf-8').write(page(w))
    open(os.path.join(R, 'index.html'), 'w', encoding='utf-8').write(index(weeks))
    print('ok', [w['week'] for w in weeks])
