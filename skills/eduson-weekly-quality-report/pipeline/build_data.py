# -*- coding: utf-8 -*-
"""Слой данных недельного отчёта ОКК.

Вход:  выгрузка звонков (txt), выгрузка метрик по менеджерам (json), config.json, content.json
Выход: data.json — все числа, признаки и профили, на которых потом строится отчёт.

Запуск:
    python3 build_data.py --calls CALLS.txt --metrics METRICS.json \
        --config config.json --content content.json --out data.json
"""
import argparse, json, re, statistics, unicodedata
from collections import Counter, defaultdict

# ---------------------------------------------------------------- разбор выгрузки звонков
CALL_HEAD = re.compile(r'(\d+) · ([^·]+) · (\d{4}-\d{2}-\d{2})')
CALL_META = re.compile(r'Продукт: (.*?) · Этап: (.*?) · Score: (\d+)% · Длит\.: (\d+):(\d+)')

def parse_calls(path):
    txt = open(path, encoding='utf-8').read()
    calls = []
    for block in re.split(r'\n### Звонок ', txt)[1:]:
        head, rest = block.split('\n', 1)
        h = CALL_HEAD.match(head)
        m = CALL_META.search(rest)
        did = re.search(r'Deal ID: (\d+)', rest)
        summ = re.search(r'Резюме: (.*)', rest)
        if not (h and m and did and summ):
            raise SystemExit(f'не разобран заголовок звонка: {head[:80]}')
        j = rest.find('\n', rest.find('Резюме:'))
        body = rest[j + 1:].split('\n---')[0].strip()
        calls.append(dict(
            no=int(h.group(1)), manager=h.group(2).strip(), date=h.group(3),
            product=m.group(1).strip(), stage=m.group(2).strip(), score=int(m.group(3)),
            minutes=round(int(m.group(4)) + int(m.group(5)) / 60, 1),
            deal_id=did.group(1), summary=summ.group(1).strip(), text=body))
    return calls

# ---------------------------------------------------------------- нормализация метрик
def num(s):
    if s is None: return None
    s = str(s).replace(' ', ' ').replace('%', '').strip()
    if s in ('', '—', 'n/a', '-'): return None
    s = s.replace(' ', '').replace(',', '.')
    return float(s)

def parse_metrics(path, fields):
    raw = json.load(open(path, encoding='utf-8'))
    rows, base = {}, None
    for r in raw:
        name = str(r[fields['manager']]).strip()
        row = dict(
            clients=int(num(r[fields['clients']]) or 0),
            c2=num(r[fields['c2']]) or 0.0,
            c2_catalog=num(r.get(fields.get('c2_catalog'), '')) or 0.0,
            sales=int(num(r[fields['sales']]) or 0),
            revenue=int(num(r[fields['revenue']]) or 0),
            avg_check=int(num(r[fields['avg_check']]) or 0),
            revenue_per_client=int(num(r[fields['revenue_per_client']]) or 0))
        if name.lower() == fields.get('total_row', 'всего').lower():
            base = row
        else:
            rows[name] = row
    if base is None:
        raise SystemExit('в выгрузке метрик нет строки «Всего» — отчёт не собирается')
    return rows, base

# ---------------------------------------------------------------- признаки этапов
# Ключи стабильны между неделями: тексты паттернов в content.json ссылаются на них.
STAGE_PATTERNS = {
 'P1': dict(name='Предложение оплаты', stage='Закрытие',
   rx=r'(не (сделан|предприн|было|последовало|совершена|удалось|попытал|пытал|смог\w?)\w*[^.]{0,45}'
      r'(попытк\w+ закрытия|закрыть|закрытия в моменте|закрыл)|попытк\w+ закрытия[^.]{0,45}(отсутств|не )|'
      r'закрытие в моменте не предлагалось|не предложи\w+[^.]{0,30}(оплату в моменте|оформление в моменте)|'
      r'активн\w+ попытк\w+ закрытия[^.]{0,20}(нет|не)|не предложил закрытие в моменте|'
      r'не оформлена рассрочка (на звонке|в звонке))'),
 'P2': dict(name='Назначение следующего разговора', stage='Следующий шаг',
   rx=r'(не (согласован|назначен|уточнен|зафиксирован|определен|конкретизирован)\w*[^.]{0,45}'
      r'(дат|следующ|созвон|звонк|шаг|врем)|следующ\w+ шаг[^.]{0,35}(не |размыт)|'
      r'договорённость о повторном звонке размытая|повторн\w+ звонок без точного времени|без точного времени)'),
 'P3': dict(name='Работа с возражениями', stage='Работа с возражениями',
   rx=r'(не (отработ|справил|обработ|заверш)\w*[^.]{0,45}возражени|'
      r'возражени\w+[^.]{0,50}(не отработ|не заверш|без отработ|отсутств)|'
      r'отработ\w+ (возражений )?частично|не отработано возражение)'),
 'P4': dict(name='Названная цена', stage='Цена',
   rx=r'(не (названа|озвучена|обсуждалась|обсуждена|указан|уточнен|обсудил|назвал)\w*[^.]{0,35}(цен|стоимост|скидк))'),
 'P5': dict(name='Выяснение задачи', stage='Выяснение задачи',
   rx=r'(не (выявл|выяснил|провод\w+ выявлени|проведен\w? выявлени|проработ|узнал)\w*[^.]{0,45}'
      r'(потребност|цел|опыт|бол|триггер)|выявлени\w*[^.]{0,45}(поверхностн|практически не проведено|не проведено|отсутств|слаб)|'
      r'поверхностн\w+ выявлени|потребности[^.]{0,25}не выявлен|не выявлен\w+ (триггер|опыт|цель))'),
 'P6': dict(name='Вопрос о способе оплаты', stage='Закрытие',
   rx=r'(не (уточн|выясн|задан|спрош)\w*[^.]{0,45}(способ\w? оплаты|метод оплаты|предпочтен\w+ по оплате|'
      r'предпочитаемый способ|о выборе тарифа|вопрос о способе оплаты))'),
 'P7': dict(name='Апсейл', stage='Апсейл',
   rx=r'(апсейл[^.]{0,35}(не |отсутств)|не (предложен|сделан|проведен|предложил)\w*[^.]{0,25}(апсейл|upsale|апсейла))'),
 'P8': dict(name='Повтор задачи клиента вслух', stage='Резюме',
   rx=r'(не (сделал|подвел|провел|резюмиров)\w*[^.]{0,30}(резюме|итог)|резюме[^.]{0,35}(не |отсутств)|не резюмиров)'),
 'P9': dict(name='Объяснение порядка разговора', stage='Порядок разговора',
   rx=r'(не (анонсирова|озвуч)\w*[^.]{0,40}блок|отсутств\w+ (программирован|структурирован)|'
      r'не было программирования|не хватает программирования|программирован\w+[^.]{0,30}(нет|отсутств|не ))'),
}

# ---------------------------------------------------------------- категории A/B/C
CLOSE_POS = re.compile(r'(предпринята попытка закрытия|попытка закрытия в моменте предпринята|'
  r'предложил\w? (оформить|оформление|записаться|оплат\w+) (в моменте|с бонусом|сейчас|сегодня)|'
  r'оформил\w? (заявку|рассрочку|запись|на звонке)|закрыл\w? (сделку|на полную оплату|на рассрочку)|'
  r'согласовал\w? (полную )?оплату|клиент согласился на (оплату|рассрочку|полную оплату)|предложил\w? оформление|'
  r'попытк\w+ закрытия с (бонусом|подарком)|предложила оформить в моменте|оперативно предложил ссылку|оформил на звонке)', re.I)
DISC_POS = re.compile(r'(качественн\w+ выявлени|полноценн\w+ (квалификаци|выявлени)|структурированн\w+ (консультаци|выявлени|звонок)|'
  r'выявил\w? потребност|выявила потребност|качественн\w+ квалификаци|выявлен\w+ потребност)', re.I)
BROKEN = re.compile(r'(обрыв(а|у)? связи|звонок прервался|проблем\w+ со связью)', re.I)

def auto_category(summary_text, flags):
    cp = bool(CLOSE_POS.search(summary_text))
    dp = bool(DISC_POS.search(summary_text))
    dn = 'P5' in flags
    obj = 'P3' in flags
    br = bool(BROKEN.search(summary_text))
    if br and not cp: return '—'
    if dn and not cp: return 'C'
    if cp and dp and not dn and not obj: return 'A'
    if cp and (dp or not dn): return 'B'
    if dp: return 'B'
    return 'C'

# ---------------------------------------------------------------- сборка
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--calls', required=True)
    ap.add_argument('--metrics', required=True)
    ap.add_argument('--config', required=True)
    ap.add_argument('--content', required=True)
    ap.add_argument('--out', default='data.json')
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding='utf-8'))
    content = json.load(open(a.content, encoding='utf-8'))
    calls = parse_calls(a.calls)
    metrics, base = parse_metrics(a.metrics, cfg['metrics_fields'])

    cc = set(content.get('contact_center_calls', []))
    for c in calls:
        c['cc'] = c['no'] in cc

    # сверка имён между источниками
    names_calls = {c['manager'] for c in calls}
    unknown = sorted(names_calls - set(metrics))
    if unknown:
        raise SystemExit('менеджеры из выгрузки звонков отсутствуют в метриках: ' + ', '.join(unknown))

    deals = defaultdict(list)
    for c in calls:
        deals[c['deal_id']].append(c)

    rows = []
    for did, cs in deals.items():
        cs.sort(key=lambda x: x['no'])
        live = [c for c in cs if not c['cc']]
        if not live:
            continue
        summary_text = ' '.join(c['summary'] for c in cs)
        flags = [k for k, p in STAGE_PATTERNS.items() if re.search(p['rx'], summary_text, re.I)]
        cat = content.get('category_overrides', {}).get(did) or auto_category(summary_text, flags)
        rows.append(dict(
            deal_id=did, manager=live[0]['manager'], product=cs[0]['product'], crm_stage=cs[-1]['stage'],
            calls=len(cs), calls_reviewed=len(live),
            minutes=round(sum(c['minutes'] for c in live), 1),
            okk=round(statistics.mean([c['score'] for c in live]), 1),
            category=cat, flags=flags, summaries=[c['summary'] for c in cs],
            call_numbers=[c['no'] for c in cs]))

    by_manager = defaultdict(list)
    for r in rows:
        by_manager[r['manager']].append(r)

    team_okk = round(statistics.mean([r['okk'] for r in rows]), 1)
    money_floor = base['revenue_per_client'] * cfg['thresholds']['revenue_ratio']
    okk_floor = team_okk - cfg['thresholds']['okk_gap']

    managers = []
    for name, m in sorted(metrics.items(), key=lambda x: -x[1]['revenue_per_client']):
        rs = by_manager.get(name, [])
        okk = round(statistics.mean([r['okk'] for r in rs]), 1) if rs else None
        cats = Counter(r['category'] for r in rs)
        small = m['clients'] < cfg['thresholds']['min_clients']
        if small:
            label = 'выборка мала'
        else:
            money_ok = m['revenue_per_client'] >= money_floor
            okk_ok = okk is not None and okk >= okk_floor
            label = ('эталон' if money_ok and okk_ok else
                     'ОКК↑ результат↓' if okk_ok else
                     'ОКК↓ результат↑' if money_ok else 'зона риска')
        managers.append(dict(
            name=name, **m,
            c2_delta_pp=round(m['c2'] - base['c2'], 1),
            avg_check_delta_pct=round((m['avg_check'] / base['avg_check'] - 1) * 100) if base['avg_check'] and m['avg_check'] else -100,
            rpc_delta_pct=round((m['revenue_per_client'] / base['revenue_per_client'] - 1) * 100) if base['revenue_per_client'] else None,
            okk=okk, okk_delta=round(okk - team_okk, 1) if okk is not None else None,
            deals_reviewed=len(rs), calls_reviewed=sum(r['calls_reviewed'] for r in rs),
            categories={k: cats.get(k, 0) for k in ('A', 'B', 'C', '—')},
            label=label,
            minutes_per_deal=round(statistics.mean([r['minutes'] for r in rs]), 1) if rs else None,
            minutes_per_call=round(statistics.mean([r['minutes'] / r['calls_reviewed'] for r in rs]), 1) if rs else None,
            share_price=round(100 * (1 - sum(1 for r in rs if 'P4' in r['flags']) / len(rs))) if rs else None,
            share_no_close=round(100 * sum(1 for r in rs if 'P1' in r['flags']) / len(rs)) if rs else None,
            share_a=round(100 * cats['A'] / len(rs)) if rs else None,
            share_c=round(100 * cats['C'] / len(rs)) if rs else None,
            share_second=round(100 * sum(1 for r in rs if r['calls_reviewed'] > 1) / len(rs)) if rs else None,
            products=[p for p, _ in Counter(r['product'] for r in rs).most_common(4)],
            live_stage=sum(1 for r in rs if r['crm_stage'] not in ('Закрыто и не реализовано',))))

    # контроль целостности
    warn = []
    if sum(m['clients'] for m in managers) != base['clients']:
        warn.append('сумма клиентов менеджеров не совпала со строкой «Всего»')
    if sum(m['sales'] for m in managers) != base['sales']:
        warn.append('сумма продаж менеджеров не совпала со строкой «Всего»')

    stage_hits = {k: sorted(r['deal_id'] for r in rows if k in r['flags']) for k in STAGE_PATTERNS}
    team = dict(
        okk=team_okk, deals=len(rows), calls=sum(r['calls_reviewed'] for r in rows),
        minutes=round(statistics.mean([r['minutes'] for r in rows]), 1),
        call=round(statistics.mean([r['minutes'] / r['calls_reviewed'] for r in rows]), 1),
        price=round(100 * (1 - len(stage_hits['P4']) / len(rows))),
        close=round(100 * len(stage_hits['P1']) / len(rows)),
        a=round(100 * sum(1 for r in rows if r['category'] == 'A') / len(rows)),
        second=round(100 * sum(1 for r in rows if r['calls_reviewed'] > 1) / len(rows)),
        categories={k: sum(1 for r in rows if r['category'] == k) for k in ('A', 'B', 'C', '—')})

    gap_names = [m['name'] for m in managers
                 if m['clients'] >= cfg['thresholds']['min_clients']
                 and m['rpc_delta_pct'] is not None
                 and m['rpc_delta_pct'] <= -cfg['thresholds']['gap_pct']]

    out = dict(config=cfg, base=base, team=team, managers=managers, deals=rows,
               stage_patterns={k: dict(name=v['name'], stage=v['stage'], deals=stage_hits[k],
                                       managers=sorted({r['manager'] for r in rows if k in r['flags']}))
                               for k, v in STAGE_PATTERNS.items()},
               thresholds=dict(money_floor=round(money_floor), okk_floor=round(okk_floor, 1)),
               gap_managers=gap_names, warnings=warn)
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"data.json: {len(rows)} сделок, {team['calls']} разговоров, {len(managers)} менеджеров, "
          f"балл группы {team_okk}, разбор ниже среднего: {', '.join(gap_names) or 'нет'}")
    for w in warn:
        print('  предупреждение:', w)

if __name__ == '__main__':
    main()
