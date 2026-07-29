# -*- coding: utf-8 -*-
"""Машинная проверка отчёта перед выдачей. Любой провал = отчёт не публикуется.

Запуск:
    python3 verify.py --outdir ../out --data data.json --content content.json
"""
import argparse, json, os, re, sys

BAN = ['лид', 'upsale', 'скоринг', 'кластер', 'инверси', 'дуга', 'дуги', 'дугу', 'транзакцион',
       'критическ', 'красный флаг', 'гособразц', 'государственного образца', 'установленного образца',
       'ФРДО', 'рассрочк', 'банк', 'третье лицо', 'третьего лица', 'перформанс', 'фидбэк', 'кейс',
       'воронк', 'деньг', 'денег', 'деньгам', 'базы', 'базе', 'базу']
VERB = re.compile(r'\w+(ет|ёт|ют|ит|ат|ят|ял|ыл|ул|ёл|ел|ил|ал|ла|ло|ли|ть|тся|ться|ось|ась|ись|'
                  r'ует|уют|ает|дут|нужно|стоит|можно|ся|лся|лись|аны|ены|ано|ено|ана|ена)\b', re.I)
SECTIONS = ['## Сводка для руководителя группы', '## Результат и качество по менеджерам',
            '## Расхождение балла и результата', '## Этапы разговора по менеджерам',
            '## Системные паттерны', '### Единичные наблюдения',
            '## Приоритеты команды на следующую неделю', '## Лучшие практики недели',
            '## Индивидуальные планы развития', '## Сделки недели', '## Как читать отчёт']

def words(t): return len(re.findall(r'[^\s]+', re.sub(r'[*`\[\]()]', '', t)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--data', required=True)
    ap.add_argument('--content', required=True)
    a = ap.parse_args()
    md = open(os.path.join(a.outdir, 'REPORT.md'), encoding='utf-8').read()
    R = json.load(open(os.path.join(a.outdir, 'REPORT.json'), encoding='utf-8'))
    C = json.load(open(a.content, encoding='utf-8'))
    D = json.load(open(a.data, encoding='utf-8'))
    fails = []

    # --- словарь
    body = re.sub(r'<!--.*?-->', '', re.sub(r'\(https?://[^)]+\)', '', md.split('## Как читать отчёт')[0]))
    for w in BAN:
        hits = [l.strip()[:80] for l in body.split('\n') if re.search(r'\b' + w, l, re.I)]
        if hits: fails.append(f'запрещённое слово «{w}»: {len(hits)} строк, например {hits[0]}')
    allow = {'amoCRM', 'C'} | {t for d in R['deals'] for t in re.findall(r'[A-Za-z][A-Za-z\-]{2,}', d.get('product', ''))}
    lat = set(re.findall(r'\b[A-Za-z][A-Za-z\-]{2,}\b', body)) - allow
    if lat: fails.append(f'латиница вне названий продуктов: {sorted(lat)}')

    # --- выводы недели
    theses = re.findall(r'^\d\. (.+)$', md.split('**Выводы недели**')[1].split('## Результат')[0], re.M)
    if not 3 <= len(theses) <= 5: fails.append(f'выводов недели {len(theses)}, нужно от 3 до 5')
    for t in theses:
        if words(t) > 40: fails.append(f'вывод длиннее 40 слов: {t[:60]}')
        if not re.search(r'\d', t): fails.append(f'вывод без числа: {t[:60]}')
        if not t.rstrip().endswith('.'): fails.append(f'вывод без точки: {t[:60]}')

    # --- паттерны и наблюдения
    for p in R['observations']:
        if p['deals'] <= D['config']['thresholds']['pattern_deals']:
            fails.append(f"паттерн {p['id']} ниже порога системности")
        shown = set(re.findall(r'leads/detail/(\d+)', md.split(f"### {p['id']}. ")[1].split('###')[0]))
        listed = {i for ids in p['by_manager'].values() for i in ids}
        if listed - shown: fails.append(f"паттерн {p['id']}: в тексте нет {len(listed-shown)} сделок")
        for f_ in ('observation', 'risk', 'action'):
            if not VERB.search(p[f_]): fails.append(f"паттерн {p['id']}.{f_} без сказуемого")
            if not p[f_].rstrip().endswith('.'): fails.append(f"паттерн {p['id']}.{f_} без точки")
    for s in R['single_observations']:
        if s['deals'] > D['config']['thresholds']['pattern_deals']:
            fails.append('единичное наблюдение выше порога')

    # --- планы развития
    cards = json.load(open(os.path.join(a.outdir, 'CARDS.json'), encoding='utf-8'))
    deal_ids = {d['deal_id'] for d in R['deals']}
    for name, cd in cards.items():
        if not VERB.search(cd['portrait']): fails.append(f'{name}: портрет без сказуемого')
        for x in cd['strengths']:
            for f_ in ('text', 'why'):
                if not VERB.search(x[f_]) or not x[f_].rstrip().endswith('.'):
                    fails.append(f"{name}: сильная сторона неполной фразой — {x['text'][:40]}")
            if x['deal'] not in deal_ids: fails.append(f"{name}: сделка {x['deal']} вне выборки")
        for x in cd['gaps']:
            for f_ in ('text', 'effect', 'action'):
                if f_ in x and x[f_] and not VERB.search(x[f_]):
                    fails.append(f"{name}: зона роста без сказуемого — {x['text'][:40]}")
            if x.get('deal') and x['deal'] not in deal_ids: fails.append(f"{name}: сделка {x['deal']} вне выборки")
        if not cd['plan']: fails.append(f'{name}: пустой план на неделю')
        for p in cd['plan']:
            if not VERB.search(p['task']) or not VERB.search(p['check']):
                fails.append(f'{name}: пункт плана без сказуемого')
        if not VERB.search(cd['score']): fails.append(f'{name}: раздел о балле без сказуемого')

    # --- лучшие практики
    B = C['best']
    for p in B['practices']:
        if p['deal'] not in deal_ids: fails.append(f"лучшая практика ссылается на чужую сделку {p['deal']}")
        if len(p['quote']) < 40: fails.append('лучшая практика без цитаты')

    # --- разбор ниже среднего
    for name in D['gap_managers']:
        if name not in C['gap_cases']: fails.append(f'нет разбора для {name}')
    for name, g in C['gap_cases'].items():
        m = next(x for x in R['managers'] if x['name'] == name)
        if m['rpc_delta_pct'] > -D['config']['thresholds']['gap_pct']:
            fails.append(f'{name}: разбор собран без повода, отклонение {m["rpc_delta_pct"]} %')
        for f_ in g['traffic'] + g['manager'] + g['check'] + [g['verdict'], g['excluded'], g['split']]:
            if not VERB.search(f_) or not f_.rstrip().endswith('.'):
                fails.append(f'{name}: пункт разбора неполной фразой — {f_[:40]}')

    # --- достоверность чисел
    if sum(m['clients'] for m in R['managers']) != R['base']['clients']:
        fails.append('сумма клиентов не сходится со строкой «Всего»')
    if sum(m['sales'] for m in R['managers']) != R['base']['sales']:
        fails.append('сумма продаж не сходится со строкой «Всего»')
    for m in R['managers']:
        if m['clients'] >= D['config']['thresholds']['min_clients'] and m['okk'] is None:
            fails.append(f"{m['name']}: нет балла качества при зачётной выборке")
        if m['label'] == 'ОКК↓ результат↑' and m['name'] not in C['divergence']:
            fails.append(f"{m['name']}: нет строки-пояснения при расхождении")

    # --- форма
    pos = [md.find(x) for x in SECTIONS]
    if any(p < 0 for p in pos): fails.append('нет разделов: ' + str([s for s, p in zip(SECTIONS, pos) if p < 0]))
    if pos != sorted(pos): fails.append('порядок разделов нарушен')
    ids = set(re.findall(r'leads/detail/(\d+)', md))
    if len(ids) < len(deal_ids): fails.append(f'ссылок на сделки {len(ids)}, сделок {len(deal_ids)}')

    # --- HTML
    html_path = os.path.join(a.outdir, 'index.html')
    if os.path.exists(html_path):
        h = open(html_path, encoding='utf-8').read()
        checks = [('<article class="ipr"', len(cards), 'карточек ИПР'),
                  ('exportIpr', 1, 'кнопка выгрузки ИПР'),
                  ('data:image/', 1, 'встроенный логотип'),
                  ('class="tiles"', 5, 'плитки показателей'),
                  ('blockquote class="say"', 5, 'карточки цитат')]
        for needle, least, what in checks:
            if h.count(needle) < least: fails.append(f'в HTML не хватает: {what}')
        if h.count('<details class="book-section"') < len(SECTIONS) - 4:
            fails.append('в HTML не свёрнуты разделы с третьего')

    print('ПРОВЕРКА НЕ ПРОЙДЕНА — отчёт публиковать нельзя:' if fails else
          'Проверка пройдена: словарь, полные фразы, пороги выборки, ссылки, порядок разделов, вёрстка.')
    for f in fails[:40]: print(' -', f)
    sys.exit(1 if fails else 0)

if __name__ == '__main__':
    main()
