CSS = r'''
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Inter+Tight:ital,wght@0,600;0,700;0,800;0,900;1,800;1,900&family=JetBrains+Mono:wght@500;600&display=swap");
:root{
 --ed-yellow:#ffd53b;--ed-yellow-soft:#ffe88a;--ed-yellow-pale:#fff5c9;
 --ed-ink:#1e1e20;--ed-ink-soft:#37373d;
 --ed-violet:#6b5eec;--ed-violet-deep:#5547d5;--ed-violet-soft:#efedff;
 --ed-beige:#f1ede5;--ed-paper:#fffdf8;--ed-line:#d9d4cb;--ed-muted:#77736d;
 --ed-positive:#2eb872;--ed-positive-bg:rgba(46,184,114,.14);
 --ed-negative:#ef5268;--ed-negative-bg:rgba(239,82,104,.13);
 --font-display:"Inter Tight","Arial Narrow",Arial,sans-serif;
 --font-body:"Inter",Arial,sans-serif;--font-mono:"JetBrains Mono",Consolas,monospace;
 --border:2px solid var(--ed-ink);color-scheme:light}
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth;background:var(--ed-beige)}
body{margin:0;background:var(--ed-beige);color:var(--ed-ink);font-family:var(--font-body);font-size:16px;line-height:1.55;-webkit-font-smoothing:antialiased}
::selection{background:var(--ed-violet);color:#fff}
.wrap{width:min(1320px,calc(100vw - 40px));margin:0 auto;padding:20px 0 96px}
.hero{position:relative;overflow:hidden;margin:0;padding:22px 28px 40px;border:var(--border);background:linear-gradient(90deg,rgba(30,30,32,.08) 1px,transparent 1px) 0 0/88px 88px,linear-gradient(rgba(30,30,32,.08) 1px,transparent 1px) 0 0/88px 88px,var(--ed-yellow)}
.hero::before{position:absolute;top:60px;right:-120px;width:360px;height:360px;border:48px solid var(--ed-ink);border-radius:50%;content:"";opacity:.06}
.hero-top{position:relative;z-index:2;display:flex;align-items:stretch;justify-content:space-between;gap:20px;padding-bottom:18px;border-bottom:var(--border);flex-wrap:wrap}
.logo-frame{display:flex;width:240px;min-height:62px;align-items:center;overflow:hidden;border:var(--border);background:#ffe27f}
.logo-frame img{width:100%;height:auto;mix-blend-mode:multiply}
.edition-badge{display:grid;min-width:230px;grid-template-columns:1fr auto;align-items:center;gap:16px;padding:10px 16px 10px 20px;border:var(--border);background:var(--ed-ink);color:#fff;font:600 11px/1.4 var(--font-mono)}
.edition-badge b{display:grid;width:52px;height:38px;place-items:center;border-radius:999px;background:var(--ed-violet);color:#fff;font-size:10px}
.hero h1{position:relative;z-index:2;max-width:1000px;margin:44px 0 0;font:900 clamp(38px,5.4vw,74px)/.92 var(--font-display);letter-spacing:-.055em}
.hero h1 em{color:var(--ed-violet);font-style:italic}
.hero-kicker{position:relative;z-index:2;display:flex;width:min(560px,100%);align-items:center;justify-content:space-between;gap:16px;margin:26px 0 0;padding-bottom:10px;border-bottom:1px solid rgba(30,30,32,.55);font:600 12px/1.3 var(--font-mono);letter-spacing:.06em;text-transform:uppercase}
.toc{position:sticky;top:0;z-index:9;display:flex;gap:8px;flex-wrap:wrap;align-items:center;padding:10px 14px;border:var(--border);border-top:0;background:var(--ed-paper);font:600 11px/1 var(--font-mono);text-transform:uppercase;letter-spacing:.04em}
.toc span{color:var(--ed-muted)}
.toc a{padding:6px 11px;border:1px solid var(--ed-line);border-radius:999px;color:var(--ed-ink);text-decoration:none;white-space:nowrap;font-weight:600}
.toc a:hover{border-color:var(--ed-violet);background:var(--ed-violet-soft);color:var(--ed-violet-deep)}
.book-section{padding:64px 0 8px;scroll-margin-top:70px}
details.book-section{padding:28px 0 8px}
details.book-section>summary{display:block;cursor:pointer;list-style:none;padding:0;position:relative}
details.book-section>summary::-webkit-details-marker{display:none}
details.book-section>summary .section-head{margin-bottom:0;padding-bottom:22px;align-items:center}
details.book-section .sec-toggle{position:absolute;right:0;top:50%;transform:translateY(-50%);display:inline-flex;align-items:center;gap:10px;min-height:44px;padding:0 18px;border:var(--border);border-radius:999px;background:var(--ed-paper);font:700 12px/1 var(--font-mono);text-transform:uppercase;letter-spacing:.05em}
details.book-section .sec-toggle::before{content:"Развернуть"}
details.book-section[open] .sec-toggle::before{content:"Свернуть"}
details.book-section .sec-toggle i{display:block;width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-top:8px solid var(--ed-ink);transition:transform 150ms ease}
details.book-section[open] .sec-toggle i{transform:rotate(180deg)}
details.book-section>summary:hover .sec-toggle{background:var(--ed-yellow)}
details.book-section[open]>summary .section-head{margin-bottom:34px}
@media (max-width:860px){details.book-section .sec-toggle{position:static;transform:none;margin-top:14px;transform:none}}
@media print{details.book-section .sec-toggle{display:none}}
.section-head{display:grid;grid-template-columns:72px minmax(0,1fr);gap:24px;margin-bottom:34px;padding-bottom:26px;border-bottom:var(--border)}
.section-index{display:grid;width:64px;height:64px;place-items:center;border:var(--border);border-radius:50%;background:var(--ed-yellow);font:800 18px/1 var(--font-display)}
.section-eyebrow{margin:2px 0 14px;color:var(--ed-muted);font:600 11px/1 var(--font-mono);letter-spacing:.08em;text-transform:uppercase}
.section-title-wrap h2{max-width:1080px;margin:0;font:900 clamp(30px,4.1vw,58px)/.98 var(--font-display);letter-spacing:-.045em}
.h3row{display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;margin:38px 0 12px}
.h3row h3{margin:0}
.dl-btn{display:inline-flex;min-height:44px;align-items:center;gap:10px;padding:0 20px;border:var(--border);border-radius:999px;background:var(--ed-yellow);color:var(--ed-ink);font:700 13px/1 var(--font-body);cursor:pointer;transition:transform 120ms ease}
.dl-btn span{font-size:17px}
.dl-btn:hover{transform:translateY(-2px);background:var(--ed-yellow-soft)}
.dl-btn:active{transform:translateY(0)}
@media print{.dl-btn{display:none}}
article.ipr{scroll-margin-top:70px}
h3{margin:38px 0 12px;font:800 clamp(20px,2vw,27px)/1.08 var(--font-display);letter-spacing:-.03em}
p{margin:12px 0}
strong{font-weight:700}
em{color:var(--ed-violet);font-style:normal}
a{color:var(--ed-violet-deep);text-decoration:none;border-bottom:1px solid rgba(107,94,236,.45);font-weight:600}
a:hover{background:var(--ed-violet-soft);border-bottom-color:var(--ed-violet)}
code{color:var(--ed-violet-deep);font:500 13px/1.4 var(--font-mono);background:var(--ed-violet-soft);padding:1px 6px}
ul,ol{margin:14px 0 14px 22px;padding:0}
li{margin:14px 0}
.note{color:var(--ed-muted);font-size:14px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));margin:22px 0;border:var(--border);background:var(--ed-paper)}
.tile{padding:18px 20px;border-right:1px solid var(--ed-line)}
.tile:last-child{border-right:0}
.tk{margin-bottom:10px;color:var(--ed-muted);font:600 10px/1.2 var(--font-mono);letter-spacing:.07em;text-transform:uppercase}
.tv{font:800 clamp(22px,2.4vw,30px)/1 var(--font-display);letter-spacing:-.045em;font-variant-numeric:tabular-nums}
.td{display:inline-block;margin-top:10px;padding:5px 10px;border-radius:999px;background:var(--ed-beige);color:var(--ed-ink-soft);font:600 11px/1 var(--font-mono);font-variant-numeric:tabular-nums}
.td.pos{color:var(--ed-positive);background:var(--ed-positive-bg)}
.td.neg{color:var(--ed-negative);background:var(--ed-negative-bg)}
blockquote.say{margin:20px 0;border:var(--border);background:var(--ed-paper)}
blockquote.say::before{display:block;padding:11px 18px;border-bottom:var(--border);background:var(--ed-violet);color:#fff;font:600 10px/1 var(--font-mono);letter-spacing:.08em;text-transform:uppercase;content:"Цитата из разговора"}
blockquote.say p{margin:0;padding:20px 22px;font:500 17px/1.45 var(--font-display);letter-spacing:-.01em}
blockquote.say cite{display:block;padding:0 22px 16px;color:var(--ed-muted);font:500 11px/1.5 var(--font-mono);font-style:normal;text-transform:uppercase;letter-spacing:.05em}
li>blockquote.say{margin:12px 0}
li>blockquote.say p{padding:16px 18px;font-size:15.5px}
p.sub{margin:8px 0;color:var(--ed-ink-soft);font-size:15px}
p.kv{display:grid;grid-template-columns:minmax(170px,210px) minmax(0,1fr);gap:22px;margin:0;padding:16px 0;border-bottom:1px solid var(--ed-line)}
p.kv .k{color:var(--ed-violet-deep);font:600 11px/1.4 var(--font-mono);letter-spacing:.07em;text-transform:uppercase}
p.kv .v{font-size:16px}
@media (max-width:700px){p.kv{grid-template-columns:1fr;gap:6px}}
.tw{overflow-x:auto;margin:22px 0;border:var(--border);background:var(--ed-paper)}
.tw.big{max-height:74vh;overflow-y:auto}
table{border-collapse:collapse;width:100%;font-size:13.5px;table-layout:auto}
td .cv{display:block;font-weight:650;font-variant-numeric:tabular-nums}
td .dl{display:block;margin-top:3px;font:600 10.5px/1 var(--font-mono);color:var(--ed-muted);font-variant-numeric:tabular-nums}
td .dl.pos{color:var(--ed-positive)}td .dl.neg{color:var(--ed-negative)}
th,td{padding:10px 11px;text-align:left;border-bottom:1px solid var(--ed-line);vertical-align:top}
thead th{position:sticky;top:0;z-index:1;border-bottom:0;background:var(--ed-ink);color:#fff;font:600 9.5px/1.25 var(--font-mono);letter-spacing:.04em;text-transform:uppercase}
tbody tr:nth-child(even){background:rgba(241,237,229,.5)}
tbody tr:hover{background:var(--ed-violet-soft)}
tbody tr:last-child td{border-bottom:0}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;font-weight:600}
td.pos{color:var(--ed-positive)}td.neg{color:var(--ed-negative)}
.tag{display:inline-flex;align-items:center;min-height:24px;padding:0 9px;border:1px solid currentColor;border-radius:999px;font:600 11px/1 var(--font-mono);letter-spacing:.04em;white-space:nowrap}
td .tag{font-size:10px;letter-spacing:.02em;white-space:normal;text-align:center}
.tag.ok{color:#1c7a4d;background:var(--ed-positive-bg)}
.tag.bad{color:#b32b3c;background:var(--ed-negative-bg)}
.tag.warn{color:#7a5f00;background:var(--ed-yellow-pale)}
.tag.inv{color:var(--ed-violet-deep);background:var(--ed-violet-soft)}
.tag.mute{color:var(--ed-muted);background:var(--ed-beige)}
@media print{.toc{display:none}.tw.big{max-height:none}body{background:#fff}}
@media (max-width:700px){.section-head{grid-template-columns:1fr;gap:14px}.section-index{width:52px;height:52px}.tile{border-right:0;border-bottom:1px solid var(--ed-line)}}
'''
