# -*- coding: utf-8 -*-
"""Слой рендера: data.json + content.json -> REPORT.md, REPORT.json, CARDS.json, GAP.json.

Рендер не имеет права ввести число, которого нет в data.json, и текст, которого нет в content.json.
Запуск:
    python3 render_report.py --data data.json --content content.json --outdir ../out
"""
import argparse, json, os, re, statistics

NB = '\u00a0'  # неразрывный пробел внутри чисел
MONTHS = {'01':'января','02':'февраля','03':'марта','04':'апреля','05':'мая','06':'июня',
          '07':'июля','08':'августа','09':'сентября','10':'октября','11':'ноября','12':'декабря'}

def money(n): return f"{int(n):,}".replace(',', NB)
def d1(x): return f"{x:.1f}".replace('.', ',').replace('-', '−')
def sp(x, dig=1): return f"{x:+.{dig}f}".replace('.', ',').replace('-', '−')
def spi(x): return f"{x:+d}".replace('-', '−')
WORDS = {0:'ноль',1:'одной',2:'двумя',3:'тремя',4:'четырьмя',5:'пятью',6:'шестью',7:'семью',8:'восемью',9:'девятью',10:'десятью'}
COUNT = {1:'одного',2:'двух',3:'трёх',4:'четырёх',5:'пяти',6:'шести',7:'семи',8:'восьми',9:'девяти',10:'десяти',
         11:'одиннадцати',12:'двенадцати',15:'пятнадцати',20:'двадцати',30:'тридцати'}
def plu(n, forms):
    n = abs(int(n)); a, b = n % 10, n % 100
    return forms[0] if (a == 1 and b != 11) else (forms[1] if (2 <= a <= 4 and not 12 <= b <= 14) else forms[2])

CAT_WHAT = {
 'A': "Менеджер выяснил задачу клиента, показал программу и предложил оплатить в разговоре.",
 'B': "Часть этапов менеджер провёл сильно, часть не довёл до конца.",
 'C': "Менеджер ограничился анкетой и ценой, образ результата клиенту не показал.",
 '—': "Ключевые этапы разговора остались за пределами записи."}
CAT_WORKS = {
 'A': "Менеджер довёл клиента до предложения оплатить.",
 'B': "Менеджер выяснил задачу и показал программу.",
 'C': "Менеджер установил контакт и рассказал о программе.",
 '—': "Наблюдаемая часть разговора проведена верно."}
FLAG_WHAT = [('P1', "Оплату в разговоре не предложил."), ('P3', "Возражение клиента осталось без ответа."),
             ('P4', "Цену не назвал."), ('P2', "Дату следующего разговора не назначил.")]
FLAG_GROW = [('P1', "Менеджеру нужно предложить оплату в самом разговоре."),
             ('P3', "Менеджеру нужно выяснить причину сомнения клиента."),
             ('P4', "Менеджеру нужно назвать цену и размер скидки."),
             ('P2', "Менеджеру нужно назначить день и час следующего разговора."),
             ('P5', "Менеджеру нужно выяснить задачу и желаемый результат клиента.")]
GROW_DEFAULT = "Менеджеру нужно держать темп и порядок разговора."

LEGEND = """## Как читать отчёт

- **Категория A** — менеджер выяснил задачу клиента, показал программу под эту задачу, ответил на возражение и предложил оплатить или забронировать место.
- **Категория B** — часть этапов менеджер провёл сильно, часть не довёл до конца.
- **Категория C** — разговор ограничен анкетой, ценой и оформлением: нужный клиенту результат менеджер не выяснил и программу под него не показал.
- **Недостаточно данных** — ключевые этапы разговора остались за пределами записи.
- **Выручка на клиента** — выручка менеджера, делённая на число его клиентов за неделю. Показатель уравнивает менеджеров с разным размером потока.
- **Конверсия C2** — доля клиентов, дошедших до покупки. Отклонения по ней считаются в процентных пунктах, отклонения по выручке — в процентах.
- **Балл качества** — средняя оценка разговоров менеджера по стандарту компании, от 0 до 100.
- **Оценка недели** — «эталон» означает, что выручка и качество выше среднего по группе; «ОКК↓ результат↑» — выручка выше среднего по группе, балл ниже; «ОКК↑ результат↓» — балл выше среднего по группе, выручка ниже; «зона риска» — оба показателя ниже среднего по группе; «выборка мала» — клиентов меньше десяти, показатели не интерпретируются.
- **Среднее по группе** — строка «Всего» в выгрузке метрик, то есть итог по всем менеджерам группы за неделю.
- **Системный паттерн** — вывод, подтверждённый более чем четырьмя сделками. Всё, что встретилось в четырёх сделках и реже, вынесено в единичные наблюдения."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--content', required=True)
    ap.add_argument('--outdir', required=True)
    a = ap.parse_args()
    D = json.load(open(a.data, encoding='utf-8'))
    C = json.load(open(a.content, encoding='utf-8'))
    cfg, base, team = D['config'], D['base'], D['team']
    managers = D['managers']
    M = {m['name']: m for m in managers}
    order = [m['name'] for m in managers]
    amo = cfg['amo_url_prefix']
    def link(did): return f"[{did}]({amo}{did})"

    L = []; w = L.append
    def stats(pairs):
        w("<!--stats-->")
        w("| " + " | ".join(p[0] for p in pairs) + " |")
        w("|" + "---|" * len(pairs))
        w("| " + " | ".join(p[1] for p in pairs) + " |")
        w("")
    def quote(text, did, stage):
        w(f"> {text}")
        w(f"> — сделка {link(did)}, этап «{stage}»")
        w("")

    w(f"# Отчёт по качеству переговоров · команда {cfg['team']} · {cfg['period']['label']}\n")
    w("")
    # 01 -----------------------------------------------------------------
    w("## Сводка для руководителя группы\n")
    stats([("Выручка команды", f"{money(base['revenue'])} ₽"), ("Конверсия C2", f"{d1(base['c2'])} %"),
           ("Выручка на клиента", f"{money(base['revenue_per_client'])} ₽"), ("Балл качества", d1(team['okk'])),
           ("Клиентов за неделю", str(base['clients'])), ("Разобрано сделок", str(team['deals']))])
    w("**Выводы недели**\n")
    for i, t in enumerate(C['theses'], 1):
        w(f"{i}. {t}")
    w("")
    # 02 -----------------------------------------------------------------
    w("## Результат и качество по менеджерам\n")
    w("| Менеджер | Клиенты | Продажи | Выручка | Конверсия C2 | Средний чек | Выручка на клиента | Балл | Разобрано | A/B/C | Оценка недели |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for m in managers:
        c = m['categories']
        w(f"| {m['name']} | {m['clients']} | {m['sales']} | {money(m['revenue'])} | "
          f"{d1(m['c2'])} % ({sp(m['c2_delta_pp'])} п.п.) | {money(m['avg_check'])} ({spi(m['avg_check_delta_pct'])} %) | "
          f"{money(m['revenue_per_client'])} ({spi(m['rpc_delta_pct'])} %) | {d1(m['okk'])} ({sp(m['okk_delta'])}) | "
          f"{m['deals_reviewed']} | A{c['A']}·B{c['B']}·C{c['C']} | {m['label']} |")
    tc = team['categories']
    w(f"| **Вся команда** | {base['clients']} | {base['sales']} | {money(base['revenue'])} | {d1(base['c2'])} % | "
      f"{money(base['avg_check'])} | {money(base['revenue_per_client'])} | {d1(team['okk'])} | {team['deals']} | "
      f"A{tc['A']}·B{tc['B']}·C{tc['C']} | среднее по группе |\n")
    w("Строка «Всего» в выгрузке — это итог по всем менеджерам группы. Отдельного среднего по отделу в данных нет, поэтому все отклонения считаются от итога группы.")
    w(f"Границы недели: по выручке менеджер считается сильным при выручке на клиента не ниже {money(D['thresholds']['money_floor'])} ₽, по качеству — при балле не ниже {d1(D['thresholds']['okk_floor'])}.\n")
    # 03 -----------------------------------------------------------------
    w("## Расхождение балла и результата\n")
    w(C['divergence_intro'] + "\n")
    for m in managers:
        if m['label'] not in ('ОКК↓ результат↑', 'ОКК↑ результат↓'):
            continue
        dv = C['divergence'][m['name']]
        w(f"### {m['name']} — оценка «{m['label']}»\n")
        stats([("Балл качества", f"{d1(m['okk'])} ({sp(m['okk_delta'])})"),
               ("Выручка на клиента", f"{money(m['revenue_per_client'])} ₽ ({spi(m['rpc_delta_pct'])} %)"),
               ("Конверсия C2", f"{d1(m['c2'])} % ({sp(m['c2_delta_pp'])} п.п.)"),
               ("Клиенты", str(m['clients'])), ("Продажи", str(m['sales'])), ("Разобрано сделок", str(m['deals_reviewed']))])
        w(f"**Что говорит балл.** {dv['score']}")
        w("")
        w(f"**Что говорит выручка.** {dv['money']}")
        w("")
        w(f"**Где возникает разрыв.** {dv['where']}")
        w("")
        quote(dv['quote'], dv['deal'], dv['stage'])
        w(f"**Что с этим делать.** {dv['action']}\n")
    w(f"### {C['divergence_summary_title']}\n")
    w(C['divergence_summary'] + "\n")
    for extra in C.get('divergence_notes', []):
        w(extra + "\n")
    # 04 -----------------------------------------------------------------
    if D['gap_managers']:
        w("## Почему результат ниже среднего по группе\n")
        w(f"Раздел собирается автоматически для менеджеров, у которых выручка на клиента ниже среднего по группе более чем "
          f"на {cfg['thresholds']['gap_pct']} процентов и при этом клиентов не меньше {COUNT.get(cfg['thresholds']['min_clients'], cfg['thresholds']['min_clients'])}. "
          f"На этой неделе под правило {plu(len(D['gap_managers']),['попал','попали','попали'])} "
          f"{len(D['gap_managers'])} {plu(len(D['gap_managers']),['менеджер','менеджера','менеджеров'])}. "
          "По каждому разобрано, что можно объяснить входящим потоком, а что — работой в разговоре, и как проверить вывод.\n")
        w(f"Ориентиры группы для сравнения: сделка длится {d1(team['minutes'])} минуты, отдельный разговор — {d1(team['call'])} минуты, "
          f"до названной цены доходят {team['price']} процентов сделок, оплата не предложена в {team['close']} процентах, "
          f"полный цикл продажи собран в {team['a']} процентах, повторный разговор состоялся в {team['second']} процентах.\n")
        for name in D['gap_managers']:
            m = M[name]; g = C['gap_cases'][name]
            w(f"### {name}\n")
            stats([("Выручка на клиента", f"{money(m['revenue_per_client'])} ₽ ({spi(m['rpc_delta_pct'])} %)"),
                   ("Клиенты", str(m['clients'])), ("Продажи", str(m['sales'])),
                   ("Разговор, минут", d1(m['minutes_per_call'])),
                   ("Доводят до цены", f"{m['share_price']} %"), ("Полный цикл продажи", f"{m['share_a']} %")])
            w(f"**Короткий вывод.** {g['verdict']}")
            w("")
            w("**Что говорит входящий поток**\n")
            for x in g['traffic']: w(f"- {x}")
            w("")
            w("**Что говорит работа менеджера**\n")
            for x in g['manager']: w(f"- {x}")
            w("")
            w(f"**Что потоком не объясняется.** {g['excluded']}")
            w("")
            w(f"**Распределение ответственности.** {g['split']}")
            w("")
            w("**Что проверить руководителю группы на неделе**\n")
            for x in g['check']: w(f"- {x}")
            w("")
        for note in C.get('gap_notes', []):
            w(note + "\n")
    # 05 -----------------------------------------------------------------
    w("## Этапы разговора по менеджерам\n")
    w("Оценка по блокам качества в выгрузке отсутствует, поэтому таблица блоков не строится. "
      "Ниже приведена таблица, посчитанная из разбора сделок: в каждой ячейке — доля сделок менеджера, где этап разговора не доведён до конца.\n")
    short = [n.split()[0] for n in order]
    w("| Этап разговора | " + " | ".join(short) + " | Вся команда |")
    w("|---|" + "---|" * (len(order) + 1))
    tot = {m['name']: m['deals_reviewed'] for m in managers}
    for key, p in D['stage_patterns'].items():
        per = {}
        for name in order:
            n = sum(1 for did in p['deals'] if next(r for r in D['deals'] if r['deal_id'] == did)['manager'] == name)
            per[name] = round(100 * n / tot[name]) if tot[name] else 0
        team_share = round(100 * len(p['deals']) / team['deals'])
        w(f"| {p['name']} | " + " | ".join(f"{per[n]} %" for n in order) + f" | {team_share} % |")
    w("| **Средний балл качества** | " + " | ".join(d1(M[n]['okk']) for n in order) + f" | {d1(team['okk'])} |")
    w("| Разобрано сделок | " + " | ".join(str(tot[n]) for n in order) + f" | {team['deals']} |\n")
    drag = []
    for key, p in D['stage_patterns'].items():
        team_share = round(100 * len(p['deals']) / team['deals'])
        names = []
        for name in order:
            if tot[name] < 5: continue
            n = sum(1 for did in p['deals'] if next(r for r in D['deals'] if r['deal_id'] == did)['manager'] == name)
            if round(100 * n / tot[name]) - team_share >= 10:
                names.append(name.split()[0])
        if names: drag.append(f"{p['name'].lower()} — " + ", ".join(names))
    if drag:
        w("Сильнее всего отстают от команды следующие этапы: " + "; ".join(drag) + ".")
    small = [m for m in managers if m['label'] == 'выборка мала']
    for m in small:
        w(f"Строка «{m['name']}» приведена в таблице для полноты, но показатели не интерпретируются: "
          f"{m['clients']} {plu(m['clients'],['клиент','клиента','клиентов'])} и {m['deals_reviewed']} "
          f"{plu(m['deals_reviewed'],['разобранная сделка','разобранные сделки','разобранных сделок'])} за неделю.")
    w("")
    # 06 -----------------------------------------------------------------
    w("## Системные паттерны\n")
    w(f"Паттерн считается системным, если он подтверждён более чем {WORDS.get(cfg['thresholds']['pattern_deals'], cfg['thresholds']['pattern_deals'])} сделками. "
      "Ниже каждый паттерн сопровождается объёмом выборки.\n")
    patterns_out = []
    for idx, p in enumerate(C['patterns'], 1):
        sp_ = D['stage_patterns'][p['key']]
        ids = sp_['deals']
        if len(ids) <= cfg['thresholds']['pattern_deals']:
            raise SystemExit(f"паттерн {p['key']} ниже порога системности: {len(ids)} сделок")
        mgrs = {}
        for name in order:
            got = [i for i in ids if next(r for r in D['deals'] if r['deal_id'] == i)['manager'] == name]
            if got: mgrs[name] = got
        w(f"### {idx}. {p['title']}\n")
        stats([("Сделок с признаком", str(len(ids))), ("Менеджеров", str(len(mgrs))),
               ("Доля разобранных сделок", f"{round(100*len(ids)/team['deals'])} %"), ("Этап разговора", sp_['stage'])])
        w(p['observation'])
        w("")
        w(f"**Объём выборки.** {len(ids)} {plu(len(ids),['сделка','сделки','сделок'])} у {len(mgrs)} "
          f"{plu(len(mgrs),['менеджера','менеджеров','менеджеров'])} из {team['deals']} разобранных.")
        w(f"**Чем это грозит.** {p['risk']}")
        w(f"**Что делает руководитель группы.** {p['action']}")
        w(f"**Все сделки паттерна — {len(ids)} {plu(len(ids),['сделка','сделки','сделок'])}, этап «{sp_['stage']}»:**")
        for name, got in mgrs.items():
            w(f"- {name} — {len(got)} {plu(len(got),['сделка','сделки','сделок'])}: " + ", ".join(link(i) for i in got) + ".")
        w("")
        patterns_out.append(dict(id=idx, key=p['key'], title=p['title'], observation=p['observation'],
                                 risk=p['risk'], action=p['action'], stage=sp_['stage'], deals=len(ids),
                                 managers=len(mgrs), of_reviewed=team['deals'],
                                 by_manager={k: v for k, v in mgrs.items()}))
    w("### Единичные наблюдения\n")
    singles = []
    for s in C.get('single_observations', []):
        sp_ = D['stage_patterns'][s['key']]
        ids = sp_['deals']
        if len(ids) > cfg['thresholds']['pattern_deals']:
            raise SystemExit(f"наблюдение {s['key']} выше порога единичных: {len(ids)} сделок")
        mgrs = sorted({next(r for r in D['deals'] if r['deal_id'] == i)['manager'] for i in ids})
        w(f"- {s['text']} Наблюдение встретилось в {len(ids)} {plu(len(ids),['сделке','сделках','сделках'])} у {len(mgrs)} "
          f"{plu(len(mgrs),['менеджера','менеджеров','менеджеров'])}: {link(ids[0])}. "
          "Наблюдение единичное и на всю команду не переносится.")
        singles.append(dict(key=s['key'], text=s['text'], deals=len(ids), managers=len(mgrs), deal_id=ids[0]))
    w("")
    # 07 -----------------------------------------------------------------
    w("## Приоритеты команды на следующую неделю\n")
    for i, p in enumerate(C['priorities'], 1):
        w(f"**{i}. {p['title']}.** {p['why']} Ожидаемый результат: {p['target_metric']} {p['target_shift']}. "
          "Разобрать с командой: " + ", ".join(link(c) for c in p['cases']) + ".\n")
    # 08 -----------------------------------------------------------------
    B = C['best']
    w("## Лучшие практики недели\n")
    w(B['lead'] + "\n")
    w("**Что показывают цифры**\n")
    for n in B['numbers']:
        w(f"- **{n['who']}.** {n['fact']} {n['meaning']}")
    w("")
    w("**Приёмы, которые стоит повторить**\n")
    for i, p in enumerate(B['practices'], 1):
        w(f"**{i}. {p['title']}.** Приём {p['author']}, сделка {link(p['deal'])}, этап «{p['stage']}».")
        w(f"> {p['quote']}")
        w(f"Что это даёт: {p['effect']}\n")
    w(f"**Что делает руководитель группы.** {B['howto']}\n")
    # 09 -----------------------------------------------------------------
    w("## Индивидуальные планы развития\n")
    w("Карточку можно переслать сотруднику целиком: в ней нет сравнений с коллегами и оценок личности, "
      "только разбор его разговоров, цитаты, ссылки на сделки и план на неделю.\n")
    deals_by_manager = {}
    for d in D['deals']:
        deals_by_manager.setdefault(d['manager'], []).append(d)
    for m in managers:
        card = C['cards'][m['name']]; c = m['categories']
        w(f"<!--ipr:{m['name']}-->")
        w(f"### {m['name']}\n")
        stats([("Клиенты", str(m['clients'])), ("Продажи", str(m['sales'])), ("Выручка", f"{money(m['revenue'])} ₽"),
               ("Конверсия C2", f"{d1(m['c2'])} % ({sp(m['c2_delta_pp'])} п.п.)"),
               ("Средний чек", f"{money(m['avg_check'])} ₽ ({spi(m['avg_check_delta_pct'])} %)"),
               ("Выручка на клиента", f"{money(m['revenue_per_client'])} ₽ ({spi(m['rpc_delta_pct'])} %)"),
               ("Балл качества", f"{d1(m['okk'])} ({sp(m['okk_delta'])})"), ("Разобрано сделок", str(m['deals_reviewed']))])
        w(f"**Оценка недели:** {m['label']}. **Категории сделок:** A — {c['A']}, B — {c['B']}, C — {c['C']}, недостаточно данных — {c['—']}.\n")
        w(card['portrait'] + "\n")
        w("**Что уже работает**\n")
        for x in card['strengths']:
            w(f"- **{x['text']}** Сделка {link(x['deal'])}, этап «{x['stage']}».")
            if x.get('quote'): w(f"  > {x['quote']}")
            w("  Почему это работает: " + x['why'][0].lower() + x['why'][1:])
        w("")
        w("**Что мешает результату**\n")
        for x in card['gaps']:
            if not x.get('deal'):
                w(f"- {x['text']}")
                continue
            w(f"- **{x['text']}** Сделка {link(x['deal'])}, этап «{x['stage']}».")
            if x.get('quote'): w(f"  > {x['quote']}")
            t = ("  К чему приводит: " + x['effect'][0].lower() + x['effect'][1:] +
                 " Что делать: " + x['action'][0].lower() + x['action'][1:])
            if x.get('pattern'): t += f" Подробнее — паттерн {x['pattern']}."
            w(t)
        w("")
        w("**План на неделю**\n")
        w("| Что сделать | Как проверим |")
        w("|---|---|")
        for p in card['plan']:
            w(f"| {p['task']} | {p['check']} |")
        w("")
        w(f"**Как поднять балл.** {card['score']}\n")
        ds = sorted(deals_by_manager.get(m['name'], []), key=lambda x: -x['okk'])
        w(f"**Сделки недели ({len(ds)}).** " + ", ".join(f"{link(d['deal_id'])} — {d1(d['okk'])}, категория {d['category']}" for d in ds) + ".\n")
        w("<!--/ipr-->")
        w("")
    # 10 -----------------------------------------------------------------
    w("## Сделки недели\n")
    w("В таблице перечислены все разобранные сделки. Номер сделки ведёт в карточку клиента в системе amoCRM.\n")
    w("| Сделка | Менеджер | Разг. | Мин. | Балл | Кат. | Что произошло | Что сработало | Что улучшить |")
    w("|---|---|---|---|---|---|---|---|---|")
    deals_out = []
    for d in sorted(D['deals'], key=lambda x: (x['manager'], x['deal_id'])):
        what = CAT_WHAT[d['category']]
        for key, add in FLAG_WHAT:
            if key in d['flags']:
                if len(what) + len(add) + 1 <= 140: what = what + " " + add
                break
        grow = GROW_DEFAULT
        for key, txt in FLAG_GROW:
            if key in d['flags']: grow = txt; break
        works = CAT_WORKS[d['category']]
        w(f"| {link(d['deal_id'])} | {d['manager']} | {d['calls_reviewed']} | {str(d['minutes']).replace('.',',')} | "
          f"{d1(d['okk'])} | {d['category']} | {what} | {works} | {grow} |")
        deals_out.append(dict(deal_id=d['deal_id'], url=amo + d['deal_id'], manager=d['manager'],
                              calls=d['calls'], calls_reviewed=d['calls_reviewed'], minutes=d['minutes'],
                              okk=d['okk'], category=d['category'], product=d['product'], crm_stage=d['crm_stage'],
                              what_happened=what, works=works, growth=grow))
    w("")
    w(LEGEND)

    os.makedirs(a.outdir, exist_ok=True)
    open(os.path.join(a.outdir, 'REPORT.md'), 'w', encoding='utf-8').write("\n".join(L) + "\n")
    report = dict(meta=dict(team=cfg['team'], period=cfg['period']['label'], generated_at=cfg['generated_at'],
                            thresholds=D['thresholds'], warnings=D['warnings']),
                  sample=dict(clients=base['clients'], deals_reviewed=team['deals'], calls_reviewed=team['calls'],
                              managers_total=len(managers),
                              managers_counted=sum(1 for m in managers if m['label'] != 'выборка мала'),
                              managers_small_sample=sum(1 for m in managers if m['label'] == 'выборка мала')),
                  base=dict(**base, okk=team['okk']), team=team, managers=managers,
                  observations=patterns_out, single_observations=singles,
                  priorities=C['priorities'], deals=deals_out)
    json.dump(report, open(os.path.join(a.outdir, 'REPORT.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(C['cards'], open(os.path.join(a.outdir, 'CARDS.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(dict(team=team, cases={n: C['gap_cases'][n] for n in D['gap_managers']}),
              open(os.path.join(a.outdir, 'GAP.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"REPORT.md: {len(L)} строк, {len(deals_out)} сделок, {len(patterns_out)} паттернов, {len(C['cards'])} планов развития")

if __name__ == '__main__':
    main()
