#!/usr/bin/env python3
"""Ежедневный анализ конкурентов Glucose.
Читает daily/data/ГГГГ-ММ-ДД.json и пишет daily/ГГГГ-ММ-ДД/index.html и daily/index.html.
Запуск: python3 daily/build.py [ГГГГ-ММ-ДД]   (без даты — пересобрать все дни)
Формат JSON — см. daily/README.md.
"""
import json, os, sys, glob, html, statistics as st, datetime as dt

ROOT = os.path.dirname(os.path.abspath(__file__))
POST_T, REEL_T = 1000, 500
ME = 'glucose.online'
WD = ['понедельник','вторник','среда','четверг','пятница','суббота','воскресенье']
MON = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']

def esc(s): return html.escape(str(s or ''))
def fnum(n): return f"{int(n):,}".replace(',', ' ')
def fk(n):
    if n is None: return '—'
    if n >= 1_000_000: return f"{n/1e6:.1f}".replace('.', ',') + ' млн'
    if n >= 1000:
        v = round(n/1000, 1); s = (f"{v:.1f}" if v < 100 else f"{v:.0f}").replace('.', ',')
        return s.replace(',0', '') + ' тыс.'
    return str(n)
def sign(n): return ('+' if n > 0 else '−' if n < 0 else '') + fnum(abs(n))
def url(p): return f"https://www.instagram.com/{'reel' if p['t']=='reel' else 'p'}/{p['c']}/"
def viral(p): return p.get('likes') is not None and p['likes'] > (REEL_T if p['t']=='reel' else POST_T)
def human(d):
    x = dt.date.fromisoformat(d); return f"{x.day} {MON[x.month-1]} {x.year}, {WD[x.weekday()]}"

CSS = """
:root{--bg:#F5F6F3;--card:#FFFFFF;--fg:#12291E;--muted:#5A645E;--line:#E1E6E1;--bar:#C7CDC9;--bar2:#7D8781;--me:#1F6B45;--me2:#86CBA2;--accent:#2E7D52;--dark:#12291E;--darkfg:#F3F1E8;--darkacc:#7FD3A1;color-scheme:light}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0F1A14;--card:#17241C;--fg:#E8EFEA;--muted:#9DB0A4;--line:#2A3A30;--bar:#3A4A40;--bar2:#6E8578;--me:#5FBF8A;--me2:#2F6B4A;--accent:#7FD3A1;--dark:#0B140F;--darkfg:#E8EFEA;--darkacc:#7FD3A1;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0F1A14;--card:#17241C;--fg:#E8EFEA;--muted:#9DB0A4;--line:#2A3A30;--bar:#3A4A40;--bar2:#6E8578;--me:#5FBF8A;--me2:#2F6B4A;--accent:#7FD3A1;--dark:#0B140F;--darkfg:#E8EFEA;--darkacc:#7FD3A1;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:Helvetica,Arial,sans-serif;font-size:16px;line-height:1.45}
.wrap{max-width:1100px;margin:0 auto;padding-block:28px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:28px}
.k{margin:0;font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);font-weight:700}
h1{margin:4px 0 0;font-size:clamp(26px,4vw,40px);text-transform:uppercase;line-height:1.1;text-wrap:balance}
h2{margin:0;font-size:22px;text-transform:uppercase;text-wrap:balance}
.sub{margin:6px 0 0;color:var(--muted);max-width:75ch}
.nav{display:flex;gap:12px;flex-wrap:wrap;font-size:14px}
.nav a{color:var(--accent)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;display:grid;gap:4px}
.kpi b{font-size:34px;line-height:1;color:var(--me)}
.kpi span{color:var(--muted);font-size:14px}
.kpi.dark{background:var(--dark);border-color:var(--dark)} .kpi.dark b{color:var(--darkacc)} .kpi.dark span{color:var(--darkfg)}
section{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;display:grid;gap:14px;min-width:0}
.find{margin:0;color:var(--muted)}
.rows{display:grid;gap:4px;overflow-x:auto}
.row{display:grid;grid-template-columns:minmax(120px,190px) minmax(0,1fr) auto;gap:10px;align-items:center;min-height:28px}
.row .n{font-size:14px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:right}
.row.me .n{color:var(--fg);font-weight:700}
.row .b{display:flex;height:16px;min-width:0}
.row .b i{display:block;height:16px;background:var(--bar)} .row .b i.d{background:var(--bar2)}
.row.me .b i{background:var(--me2)} .row.me .b i.d{background:var(--me)}
.row .v{font-size:14px;font-variant-numeric:tabular-nums;white-space:nowrap}
.row.me .v{font-weight:700}
.legend{display:flex;gap:14px;font-size:13px;color:var(--muted)} .legend i{display:inline-block;width:12px;height:12px;vertical-align:-1px;margin-right:4px}
.list{display:grid;gap:8px}
.item{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:12px;align-items:center;padding:10px 12px;border:1px solid var(--line);border-radius:10px}
.item.me{border-color:var(--me)}
.chip{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:2px 8px;border-radius:99px;border:1px solid var(--accent);color:var(--accent);white-space:nowrap}
.item .t{min-width:0} .item .t a{color:var(--fg);font-weight:700} .item .t small{display:block;color:var(--muted);overflow-wrap:anywhere}
.item .m{text-align:right;font-variant-numeric:tabular-nums;font-size:14px;white-space:nowrap}
.empty{color:var(--muted)}
.why{display:grid;gap:10px}
.why div{background:var(--bg);border-radius:10px;padding:12px 14px} .why b{display:block}
table{border-collapse:collapse;width:100%;font-size:15px} th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)} th{color:var(--muted);font-weight:600}
.tbl{overflow-x:auto}
.out{background:var(--dark);color:var(--darkfg);border-radius:16px;padding:18px 20px} .out b{color:var(--darkacc)}
footer{color:var(--muted);font-size:13px}
a{color:var(--accent)}
"""

def bars(items, val, label, maxv=None, split=None, fmt=str):
    items = list(items)
    if not items: return '<p class="empty">Нет данных.</p>'
    mx = maxv or max([val(x) for x in items] + [1])
    out = []
    for x in items:
        v = val(x); w = max(0, v) / mx * 100 if mx else 0
        if split:
            a, b = split(x); ws = (a/mx*100, b/mx*100) if mx else (0, 0)
            bar = f'<i class="d" style="width:{ws[0]:.2f}%"></i><i style="width:{ws[1]:.2f}%"></i>'
        else:
            bar = f'<i class="d" style="width:{min(w,100):.2f}%"></i>'
        me = ' me' if x['a'] == ME else ''
        out.append(f'<div class="row{me}"><span class="n">@{esc(x["a"])}</span><span class="b">{bar}</span><span class="v">{fmt(x)}</span></div>')
    return '<div class="rows">' + ''.join(out) + '</div>'

def page_day(d):
    accs = d['accounts']; date = d['date']
    for a in accs:
        a['pubs'] = a.get('posts', [])
        a['np'] = sum(1 for p in a['pubs'] if p['t'] != 'reel'); a['nr'] = sum(1 for p in a['pubs'] if p['t'] == 'reel')
        a['n'] = a['np'] + a['nr']; a['vir'] = [p for p in a['pubs'] if viral(p)]
    allp = [(a['a'], p) for a in accs for p in a['pubs']]
    me = next((a for a in accs if a['a'] == ME), None)
    total = len(allp); nvir = sum(1 for _, p in allp if viral(p))
    # activity
    act = sorted(accs, key=lambda a: (-a['n'], a['a'] != ME, a['a']))
    rank_act = 1 + sum(1 for a in accs if a['n'] > (me['n'] if me else 0))
    # growth
    gr = [a for a in accs if a.get('growth') is not None]
    gr.sort(key=lambda a: -a['growth'])
    rank_gr = 1 + sum(1 for a in gr if me and me.get('growth') is not None and a['growth'] > me['growth'])
    gmax = max([a['growth'] for a in gr[1:]] + [1]) if gr else 1
    if gr and gr[0]['growth'] > 3 * gmax: gcap = gmax * 1.15
    else: gcap = max([a['growth'] for a in gr] + [1])
    # views
    reels = [(a, p) for a, p in allp if p['t'] == 'reel' and p.get('views')]
    reels.sort(key=lambda x: -x[1]['views'])
    my_best = next(((i+1, a, p) for i, (a, p) in enumerate(reels) if a == ME), None)
    # viral list
    vl = sorted([(a, p) for a, p in allp if viral(p)], key=lambda x: -x[1]['likes'])
    def item(a, p, extra=''):
        cls = ' me' if a == ME else ''
        cap = esc((p.get('cap') or 'без подписи')[:140])
        m = f"{fnum(p['likes'])} лайков" if p.get('likes') is not None else 'лайки скрыты'
        if p.get('views'): m += f"<br>{fk(p['views'])} просмотров"
        return f'<div class="item{cls}"><span class="chip">{"рилс" if p["t"]=="reel" else "пост"}</span><span class="t"><a href="{url(p)}" target="_blank" rel="noopener">@{esc(a)}</a><small>{cap}</small></span><span class="m">{m}{extra}</span></div>'
    share = [a for a in accs if a['n']]
    share.sort(key=lambda a: (-len(a['vir'])/a['n'], -a['n']))
    notes = d.get('notes', {})
    why = notes.get('why', {})
    top3 = gr[:3]
    whyhtml = ''.join(f'<div><b>@{esc(a["a"])} · {sign(a["growth"])}</b>{esc(why.get(a["a"], "Причина не определена: заметных публикаций за день нет."))}</div>' for a in top3)
    mm = d.get('glucose_metricool') or {}
    kp = []
    if me:
        kp.append(f'<div class="kpi dark"><b>{me["n"]}</b><span>публикаций Glucose ({me["np"]} постов, {me["nr"]} рилсов) · место {rank_act} из {len(accs)}</span></div>')
        if me.get('growth') is not None: kp.append(f'<div class="kpi"><b>{sign(me["growth"])}</b><span>подписчиков за сутки · место {rank_gr} из {len(gr)}</span></div>')
        kp.append(f'<div class="kpi"><b>{len(me["vir"])} из {me["n"]}</b><span>публикаций Glucose залетели</span></div>')
        if my_best: kp.append(f'<div class="kpi"><b>{fk(my_best[2]["views"])}</b><span>лучший рилс Glucose · {my_best[0]}-е место из {len(reels)}</span></div>')
    if mm.get('reach') is not None: kp.append(f'<div class="kpi"><b>{fk(mm["reach"])}</b><span>охват Glucose (Metricool)</span></div>')
    mtable = ''
    if mm:
        rows = [('Пришло подписчиков', mm.get('gained')), ('Ушло подписчиков', mm.get('lost')), ('Охват аккаунта', mm.get('reach')), ('Просмотры аккаунта', mm.get('views')), ('Просмотры рилсов', mm.get('reels_views')), ('Взаимодействия', mm.get('interactions')), ('Сторис', mm.get('stories'))]
        mtable = '<div class="tbl"><table><tr><th>Glucose · Metricool</th><th>за сутки</th></tr>' + ''.join(f'<tr><td>{k}</td><td>{fnum(v) if v is not None else "—"}</td></tr>' for k, v in rows) + '</table></div>'
    place = []
    if me:
        place.append(('Публикаций', str(me['n']), f'{rank_act} из {len(accs)}', f"@{act[0]['a']} — {act[0]['n']}"))
        if me.get('growth') is not None and gr: place.append(('Прирост подписчиков', sign(me['growth']), f'{rank_gr} из {len(gr)}', f"@{gr[0]['a']} — {sign(gr[0]['growth'])}"))
        if share: 
            r = 1 + sum(1 for a in share if me['n'] and len(a['vir'])/a['n'] > len(me['vir'])/me['n'])
            place.append(('Доля залетевших', f"{round(100*len(me['vir'])/me['n']) if me['n'] else 0}%", f'{r} из {len(share)}' if me['n'] else '—', f"@{share[0]['a']} — {round(100*len(share[0]['vir'])/share[0]['n'])}%"))
        if reels: place.append(('Лучший рилс, просмотров', fk(my_best[2]['views']) if my_best else '—', f'{my_best[0]} из {len(reels)}' if my_best else '—', f"@{reels[0][0]} — {fk(reels[0][1]['views'])}"))
    ptable = '<div class="tbl"><table><tr><th>Показатель</th><th>Glucose</th><th>Место</th><th>Лидер</th></tr>' + ''.join(f'<tr><td>{a}</td><td><b>{b}</b></td><td>{c}</td><td>{esc(e)}</td></tr>' for a, b, c, e in place) + '</table></div>'
    body = f'''
<header><p class="k">Glucose · ежедневный анализ · Instagram ҰБТ</p><h1>{human(date)}</h1>
<p class="sub">Публикации {len(accs)} аккаунтов за сутки ({date}, время Алматы). Лайки и просмотры сняты {esc(d.get('measured_at',''))}; у свежих публикаций они ещё растут.</p>
<p class="nav"><a href="../index.html">← все дни</a><a href="../../glucose-competitor-analysis/">недельный анализ</a></p></header>
<div class="kpis">{''.join(kp)}</div>
{f'<div class="out"><b>Главное за день:</b> {esc(notes.get("summary"))}</div>' if notes.get('summary') else ''}
<section><h2>Прирост подписчиков за сутки</h2><p class="find">Разница замеров {esc(d.get('growth_from',''))} → {esc(d.get('growth_to',''))}.{' Полоса лидера обрезана — она намного длиннее.' if gr and gr[0]['growth'] > gcap else ''}</p>
{bars(gr, lambda a: max(0,a['growth']), None, maxv=gcap, fmt=lambda a: sign(a['growth']))}
<h2>Топ-3 и за счёт чего</h2><div class="why">{whyhtml}</div></section>
<section><h2>Активность</h2><p class="find">Всего {total} публикаций в нише за день. Тёмная часть полосы — посты, светлая — рилсы.</p>
<div class="legend"><span><i style="background:var(--bar2)"></i>посты</span><span><i style="background:var(--bar)"></i>рилсы</span></div>
{bars([a for a in act if a['n']], lambda a: a['n'], None, split=lambda a: (a['np'], a['nr']), fmt=lambda a: str(a['n']))}
<p class="find">Ничего не выложили: {esc(', '.join('@'+a['a'] for a in act if not a['n'])) or '—'}.</p></section>
<section><h2>Залетевшие публикации</h2><p class="find">Залетел: пост больше {POST_T} лайков, рилс больше {REEL_T}. За день залетело {nvir} из {total} ({round(100*nvir/total) if total else 0}%).</p>
<div class="list">{''.join(item(a, p) for a, p in vl) or '<p class="empty">Ничего не залетело.</p>'}</div>
<h2>Доля залетевших по аккаунтам</h2>
{bars(share, lambda a: round(100*len(a['vir'])/a['n']), None, maxv=100, fmt=lambda a: f"{round(100*len(a['vir'])/a['n'])}% · {len(a['vir'])} из {a['n']}")}</section>
<section><h2>Рилсы по просмотрам</h2><p class="find">Топ-10 рилсов дня.{f" Лучший рилс Glucose — {my_best[0]}-е место из {len(reels)}." if my_best else ''}</p>
<div class="list">{''.join(item(a, p, '') for a, p in reels[:10]) or '<p class="empty">Нет рилсов с просмотрами.</p>'}</div></section>
<section><h2>Место Glucose</h2>{ptable}{mtable}</section>
{f'<div class="out"><b>Что взять в работу:</b> {esc(notes.get("todo"))}</div>' if notes.get('todo') else ''}
<footer>Источник: Instagram (страницы публикаций и вкладки Reels), ежедневные замеры подписчиков около 12:00 по Алматы, Metricool для Glucose. Совместные публикации засчитаны каждому соавтору.</footer>'''
    return f'<!doctype html>\n<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><meta name="claude:viewport-fit-sides" content="cover"><title>Glucose · день {date}</title><style>{CSS}</style></head><body><div class="wrap">{body}</div></body></html>\n'

def page_index(days):
    rows = []
    for d in sorted(days, key=lambda x: x['date'], reverse=True):
        me = next((a for a in d['accounts'] if a['a'] == ME), {'posts': []})
        n = len(me.get('posts', [])); v = sum(1 for p in me.get('posts', []) if viral(p))
        g = me.get('growth'); summ = d.get('notes', {}).get('summary', '')
        rows.append(f'<a class="item" href="{d["date"]}/" style="text-decoration:none;color:inherit"><span class="chip">{d["date"][8:10]}.{d["date"][5:7]}</span><span class="t"><b>{human(d["date"])}</b><small>{esc(summ[:180])}</small></span><span class="m">Glucose: {n} публ. · {v} залет.<br>{sign(g) if g is not None else "—"} подп.</span></a>')
    body = f'<header><p class="k">Glucose · Instagram ҰБТ</p><h1>Ежедневный анализ конкурентов</h1><p class="sub">Каждый день — публикации, залетевшее, просмотры и прирост подписчиков 20 аккаунтов за прошедшие сутки.</p><p class="nav"><a href="../glucose-competitor-analysis/">недельный анализ →</a></p></header><div class="list">{"".join(rows) or "<p class=empty>Пока нет дней.</p>"}</div>'
    return f'<!doctype html>\n<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><meta name="claude:viewport-fit-sides" content="cover"><title>Glucose · ежедневный анализ</title><style>{CSS}</style></head><body><div class="wrap">{body}</div></body></html>\n'

def main():
    files = sorted(glob.glob(os.path.join(ROOT, 'data', '*.json')))
    days = [json.load(open(f, encoding='utf-8')) for f in files]
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for d in days:
        if only and d['date'] != only: continue
        os.makedirs(os.path.join(ROOT, d['date']), exist_ok=True)
        open(os.path.join(ROOT, d['date'], 'index.html'), 'w', encoding='utf-8').write(page_day(d))
    open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(page_index(days))
    print('ok', [d['date'] for d in days])

if __name__ == '__main__':
    main()
