# -*- coding: utf-8 -*-
import re,html,json,base64,pathlib,argparse

_ap=argparse.ArgumentParser(description='Рендер HTML-страницы отчёта из REPORT.md')
_ap.add_argument('--md',required=True,help='путь к REPORT.md')
_ap.add_argument('--logo',required=True,help='файл логотипа Eduson (любой формат, определяется по сигнатуре)')
_ap.add_argument('--out',required=True,help='куда записать index.html')
ARGS=_ap.parse_args()
from book_css import CSS
_p=pathlib.Path(ARGS.logo)
_b=_p.read_bytes()
_mime='image/webp' if _b[:4]==b'RIFF' and _b[8:12]==b'WEBP' else ('image/png' if _b[:8]==b'\x89PNG\r\n\x1a\n' else 'image/jpeg')
LOGO=f"data:{_mime};base64,"+base64.b64encode(_b).decode()
md=open(ARGS.md,encoding='utf-8').read()
lines=md.split('\n')
LABELS={'эталон':'ok','ОКК↓ результат↑':'inv','ОКК↑ результат↓':'warn','зона риска':'bad','выборка мала':'mute'}
def inline(t,tagify=False):
    t=html.escape(t)
    t=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',t)
    t=re.sub(r'`(.+?)`',r'<code>\1</code>',t)
    t=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<a href="\2" target="_blank" rel="noopener">\1</a>',t)
    if tagify and t.strip() in LABELS:
        k=t.strip(); t=f'<span class="tag {LABELS[k]}">{k}</span>'
    return t
out=[];i=0;toc=[];TITLE=[];SEC=[]
def cell(c,head=False):
    c=c.strip()
    if head: return f'<th>{inline(c)}</th>'
    m=re.match(r'^(.+?)\s*\(([+−][^()]*)\)$',c)
    if m:
        main,delta=m.group(1),m.group(2)
        dcls='pos' if delta.startswith('+') else 'neg'
        return ('<td class="n"><span class="cv">'+inline(main)+'</span>'
                f'<span class="dl {dcls}">'+inline(delta)+'</span></td>')
    cls=''
    if re.fullmatch(r'[−+]?[\d\s ,%.₽]+',c) and c: cls=' class="n"'
    if c.startswith('−'): cls=' class="n neg"'
    if c.startswith('+'): cls=' class="n pos"'
    return f'<td{cls}>{inline(c,tagify=True)}</td>'

while i<len(lines):
    l=lines[i]
    if l.startswith('# '):
        TITLE.append(l[2:]);i+=1;continue
    if l.startswith('## ') or l.startswith('### '):
        lvl=l.count('#');txt=l.lstrip('# ')
        sid=re.sub(r'[^a-zа-яё0-9]+','-',txt.lower())
        if lvl==2:
            toc.append((sid,txt))
            if SEC: out.append('</details>' if len(SEC)>=3 else '</section>')
            SEC.append(sid)
            n=str(len(SEC)).zfill(2)
            headmark=('<div class="section-head"><div class="section-index">'+n+'</div>'
                      '<div class="section-title-wrap"><p class="section-eyebrow">Раздел '+n+'</p>'
                      f'<h2>{inline(txt)}</h2></div></div>')
            if len(SEC)>=3:
                out.append(f'<details class="book-section" id="{sid}">')
                out.append('<summary>'+headmark+'<span class="sec-toggle"><i></i></span></summary>')
            else:
                out.append(f'<section class="book-section" id="{sid}">')
                out.append(headmark)
        else:
            btn=''
            if out and out[-1].startswith('<article class="ipr"'):
                btn=('<button class="dl-btn" type="button" onclick="exportIpr(this)">'
                     '<span>↓</span>Выгрузить ИПР</button>')
            out.append(f'<div class="h3row"><h3 id="{sid}">{inline(txt)}</h3>{btn}</div>' if btn else f'<h3 id="{sid}">{inline(txt)}</h3>')
        i+=1;continue
    if l.strip().startswith('<!--ipr:'):
        nm=l.strip()[8:-3]
        slug=re.sub(r'[^a-zа-яё0-9]+','-',nm.lower())
        out.append(f'<article class="ipr" id="ipr-{slug}" data-name="{html.escape(nm)}">')
        i+=1;continue
    if l.strip()=='<!--/ipr-->':
        out.append('</article>');i+=1;continue
    if l.strip()=='<!--stats-->':
        i+=1
        rows=[]
        while i<len(lines) and lines[i].startswith('|'):
            rows.append(lines[i]);i+=1
        head=[c.strip() for c in rows[0].strip('|').split('|')]
        vals=[c.strip() for c in rows[2].strip('|').split('|')]
        tiles=[]
        for k,v in zip(head,vals):
            m=re.match(r'^(.*?)\s*\((.+)\)$',v)
            main,delta=(m.group(1),m.group(2)) if m else (v,None)
            dcls=''
            if delta: dcls=' pos' if delta.startswith('+') else (' neg' if delta.startswith('−') else '')
            tiles.append('<div class="tile"><div class="tk">'+inline(k)+'</div><div class="tv">'+inline(main)+'</div>'
                         +(f'<div class="td{dcls}">{inline(delta)}</div>' if delta else '')+'</div>')
        out.append('<div class="tiles">'+''.join(tiles)+'</div>');continue
    if l.startswith('|'):
        rows=[];
        while i<len(lines) and lines[i].startswith('|'):
            rows.append(lines[i]);i+=1
        head=[c for c in rows[0].strip('|').split('|')]
        body=[r for r in rows[2:]]
        big=' big' if len(body)>20 else ''
        t=[f'<div class="tw{big}"><table><thead><tr>'+''.join(cell(c,True) for c in head)+'</tr></thead><tbody>']
        for r in body:
            cs=r.strip('|').split('|')
            tr='<tr>'+''.join(cell(c) for c in cs)+'</tr>'
            t.append(tr)
        t.append('</tbody></table></div>')
        out.append('\n'.join(t));continue
    if l.startswith('> '):
        q=[];cap=None
        while i<len(lines) and lines[i].startswith('> '):
            t=lines[i][2:]
            if t.startswith('— '): cap=t[2:]
            else: q.append(t)
            i+=1
        html_q='<blockquote class="say"><p>«'+inline(' '.join(q))+'»</p>'
        if cap: html_q+='<cite>'+inline(cap)+'</cite>'
        out.append(html_q+'</blockquote>');continue
    if l.startswith('- ') or re.match(r'^\d+\. ',l):
        items=[];ordered=bool(re.match(r'^\d+\. ',l))
        while i<len(lines) and (lines[i].startswith('- ') or re.match(r'^\d+\. ',lines[i]) or lines[i].startswith('  ')):
            ln=lines[i]
            if ln.startswith('  '):
                body=ln.strip()
                if body.startswith('> '): items[-1].append(('q',body[2:]))
                else: items[-1].append(('p',body))
            else:
                items.append([('t',re.sub(r'^(- |\d+\. )','',ln))])
            i+=1
        tag='ol' if ordered else 'ul'
        buf=[f'<{tag}>']
        for it in items:
            parts=[]
            for kind,txt in it:
                if kind=='q': parts.append('<blockquote class="say"><p>«'+inline(txt)+'»</p></blockquote>')
                elif kind=='t': parts.append(inline(txt))
                else: parts.append('<p class="sub">'+inline(txt)+'</p>')
            buf.append('<li>'+''.join(parts)+'</li>')
        buf.append(f'</{tag}>')
        out.append('\n'.join(buf));continue
    if l.strip()=='':
        i+=1;continue
    para=[]
    while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','- ','> ','<!--')) and not re.match(r'^\d+\. ',lines[i]):
        para.append(lines[i]);i+=1
    cls=' class="note"' if para[0].startswith('**Оговорка') or para[0].startswith('Строка «Всего»') or para[0].startswith('Сычева Татьяна показана') else ''
    m=re.match(r'^\*\*(.+?)\.\*\*\s+(.*)$',para[0]) if len(para)==1 else None
    if m:
        out.append('<p class="kv"><span class="k">'+inline(m.group(1))+'</span><span class="v">'+inline(m.group(2))+'</span></p>')
    else:
        out.append(f'<p{cls}>'+'<br>'.join(inline(x) for x in para)+'</p>')
if SEC: out.append('</details>' if len(SEC)>=3 else '</section>')
body='\n'.join(out)
title=TITLE[0] if TITLE else 'Отчёт'
head,_,tail=title.partition('·')
period=title.split('·')[-1].strip()
MON={'01':'января','02':'февраля','03':'марта','04':'апреля','05':'мая','06':'июня','07':'июля','08':'августа','09':'сентября','10':'октября','11':'ноября','12':'декабря'}
m=re.match(r'(\d{4})-(\d{2})-(\d{2})\s*—\s*(\d{4})-(\d{2})-(\d{2})',period)
if m:
    y1,m1,d1_,y2,m2,d2=m.groups()
    period=(f"{int(d1_)}–{int(d2)} {MON[m2]} {y2}" if m1==m2 else f"{int(d1_)} {MON[m1]} — {int(d2)} {MON[m2]} {y2}")
team=title.split('·')[1].strip() if title.count('·')>=2 else ''
h1html=f'Отчёт по <em>качеству переговоров</em>'
nav='<nav class="toc"><span>Разделы</span>'+' '.join(f'<a href="#{sid}">{t}</a>' for sid,t in toc)+'</nav>'
hero=('<div class="hero">'
      '<div class="hero-top">'
      f'<div class="logo-frame"><img src="{LOGO}" alt="Eduson Academy"></div>'
      f'<div class="edition-badge"><span>Отдел контроля качества<br>Недельный отчёт</span><b>ОКК</b></div>'
      '</div>'
      f'<h1>{h1html}</h1>'
      f'<div class="hero-kicker"><span>{team}</span><span>{period}</span></div>'
      '</div>')
doc=f'''<title>{html.escape(title)}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{LOGO}">
<style>{CSS}</style>
<div class="wrap">
{hero}
{nav}
{body}
</div>
<script>
function openTarget(){{
  var id=decodeURIComponent(location.hash.slice(1));
  if(!id) return;
  var el=document.getElementById(id);
  if(el && el.tagName==='DETAILS') el.open=true;
  var d=el&&el.closest('details'); if(d) d.open=true;
  if(el) setTimeout(function(){{el.scrollIntoView();}},0);
}}
window.addEventListener('hashchange',openTarget);
window.addEventListener('DOMContentLoaded',openTarget);
window.addEventListener('beforeprint',function(){{
  document.querySelectorAll('details').forEach(function(d){{d.dataset.wasOpen=d.open?'1':'0';d.open=true;}});
}});
window.addEventListener('afterprint',function(){{
  document.querySelectorAll('details').forEach(function(d){{if(d.dataset.wasOpen==='0') d.open=false;}});
}});
function exportIpr(btn){{
  var art=btn.closest('article.ipr');
  var name=art.getAttribute('data-name')||'ИПР';
  var css=document.querySelector('style').textContent;
  var clone=art.cloneNode(true);
  var b=clone.querySelector('.dl-btn'); if(b) b.remove();
  var head='<div class="hero"><div class="hero-top">'
    +'<div class="logo-frame"><img src="{LOGO}" alt="Eduson Academy"></div>'
    +'<div class="edition-badge"><span>Отдел контроля качества<br>Индивидуальный план развития</span><b>ОКК</b></div>'
    +'</div><h1>'+name+'</h1><div class="hero-kicker"><span>{team}</span><span>{period}</span></div></div>';
  var doc='<!doctype html><html lang="ru"><head><meta charset="utf-8">'
    +'<meta name="viewport" content="width=device-width,initial-scale=1">'
    +'<title>ИПР · '+name+' · {period}</title><link rel="icon" href="{LOGO}">'
    +'<style>'+css+'</style></head><body><div class="wrap">'+head
    +'<section class="book-section">'+clone.innerHTML+'</section></div></body></html>';
  var blob=new Blob([doc],{{type:'text/html;charset=utf-8'}});
  var url=URL.createObjectURL(blob);
  var a=document.createElement('a');
  a.href=url;
  a.download='ИПР '+name+' '+'{period}'.replace(/ /g,'-')+'.html';
  document.body.appendChild(a);a.click();
  setTimeout(function(){{URL.revokeObjectURL(url);a.remove();}},1500);
}}
</script>'''
open(ARGS.out,'w',encoding='utf-8').write(doc)
print(f'{ARGS.out}: {len(doc)} байт, разделов {len(SEC)}, свёрнутых {max(0,len(SEC)-2)}')
