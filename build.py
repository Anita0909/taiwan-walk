"""Build the static site from wiki Markdown using only the Python standard library."""
from pathlib import Path
import html, json, re, shutil
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'docs'
photos=json.loads((ROOT/'photos.json').read_text(encoding='utf-8'))
esc=lambda s:html.escape(str(s),quote=True)
def inline(s):
    s=esc(s)
    def link(m):
        url=html.unescape(m[2])
        if url.startswith('../sources/'): url='../sources/'+Path(url).stem+'.html'
        elif url.endswith('.md'): url=url[:-3]+'.html'
        return f'<a href="{esc(url)}">{m[1]}</a>'
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,s)
def markdown(text):
    out=[]; para=[]; listing=False; headings=[]; table=[]
    def flush():
        if para: out.append('<p>'+inline(' '.join(para))+'</p>');para.clear()
    def flush_table():
        if not table:return
        rows=[[cell.strip() for cell in row.strip('|').split('|')] for row in table]
        out.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th scope="col">'+inline(c)+'</th>' for c in rows[0])+'</tr></thead><tbody>')
        for row in rows[2:]:out.append('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>')
        out.append('</tbody></table></div>');table.clear()
    for line in text.splitlines()+['']:
        if line.startswith('|'):
            flush()
            if listing:out.append('</ul>');listing=False
            table.append(line);continue
        flush_table()
        if line.startswith('# '): continue
        if line.startswith('## '):
            flush()
            if listing: out.append('</ul>');listing=False
            title=line[3:];id='section-'+str(len(headings)+1);headings.append((id,title));out.append(f'<h2 id="{id}">{esc(title)}</h2>')
        elif line.startswith('- ') or re.match(r'^\d+\. ',line):
            flush()
            if not listing:out.append('<ul>');listing=True
            out.append('<li>'+inline(re.sub(r'^(?:- |\d+\. )','',line))+'</li>')
        else:
            if listing:out.append('</ul>');listing=False
            if line.strip():para.append(line)
            else:flush()
    return '\n'.join(out),headings
def shell(title,body,prefix='',desc='從自然地景與地方產業，認識台灣的旅遊知識庫。'):
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{esc(desc)}"><meta name="theme-color" content="#203d35"><title>{esc(title)}｜台灣走走</title><link rel="stylesheet" href="{prefix}assets/style.css"><script defer src="{prefix}assets/app.js"></script></head><body><a class="skip" href="#main">跳至主要內容</a><header><a class="brand" href="{prefix}index.html">台灣走走<small>TAIWAN WALK</small></a><nav class="nav" aria-label="主選單"><a href="{prefix}index.html#explore">探索景點</a><a href="{prefix}index.html#about">關於這裡</a><a href="{prefix}credits.html">圖片出處</a></nav></header><main id="main">{body}</main><footer><span>台灣走走 Taiwan Walk · 慢一點，看見更多。</span><span>資料查核 2026.11.16 · 出發前請確認官方公告</span></footer></body></html>'''
def credit(p):
    return f'照片：{esc(p["author"])} ／ <a href="{esc(p["source"])}">Wikimedia Commons 原作</a> ／ <a href="{p["licenseUrl"]}">{p["license"]}</a> · 拍攝：{p["date"]}'
places=[]
for p in photos:
    path=ROOT/'wiki/places'/f'{p["id"]}.md'
    text=path.read_text(encoding='utf-8')
    title=text.splitlines()[0][2:]
    meta=dict(re.findall(r'^- ([^：]+)：(.+)$',text,re.M))
    summary=meta['簡介']
    places.append(dict(p=p,title=title,meta=meta,summary=summary,text=text))
place_count=len(places)
def limit_related(text):
    # Links are curated in article order; never expand to the full catalog.
    pattern=r'(## 相關景點\n)(.*?)(?=\n## |\Z)'
    def cap(match):
        links=[line for line in match[2].splitlines() if line.startswith('- ')]
        return match[1]+'\n'.join(links[:3])+'\n'
    return re.sub(pattern,cap,text,flags=re.S)
slides=[];cards=[]
for i,x in enumerate(places):
    p=x['p'];m=x['meta'];href=f'places/{p["id"]}.html';src=f'assets/photos/{p["file"]}'
    slides.append(f'''<section class="slide" aria-label="第{i+1}張，共{place_count}張：{esc(x['title'])}"><img src="{src}" alt="{esc(p['alt'])}" {'loading="lazy"' if i else 'fetchpriority="high"'}><div class="overlay"><div><p>0{i+1} / {esc(m['區域'])} · {esc(m['類型'])}</p><h3>{esc(x['title'])}</h3></div><a class="round-link" href="{href}">走進這個地方 ↗</a></div></section>''')
    cards.append(f'''<section class="card" data-region="{esc(m['區域'])}" data-search="{esc(x['title']+' '+m['縣市／行政區']+' '+m['類型']+' '+x['summary'])}"><a href="{href}" aria-label="閱讀{esc(x['title'])}"><img loading="lazy" src="{src}" alt="{esc(p['alt'])}"></a><div><p class="meta">{esc(m['縣市／行政區'])} / {esc(m['類型'])}</p><h3>{esc(x['title'])}</h3><p>{esc(x['summary'])}</p><a class="read" href="{href}">閱讀景點筆記 ↗</a></div></section>''')
    body,toc=markdown(limit_related(x['text'][x['text'].index('## 景點特色與背景'):]))
    nav=''.join(f'<a href="#{id}">{esc(t)}</a>' for id,t in toc)
    article=f'''<p class="breadcrumb"><a href="../index.html#explore">探索景點</a> / {esc(m['區域'])} / {esc(m['縣市／行政區'])}</p><div class="article-head"><span class="eyebrow">{esc(m['類型'])}</span><h1>{esc(x['title'])}</h1><p>{esc(x['summary'])}</p><span class="badge">{esc(m['區域'])}</span><span class="badge">查核 {m['最後查核日期']}</span></div><figure class="article-photo"><img src="../{src}" alt="{esc(p['alt'])}"><figcaption>{credit(p)}。歷年實景照片，非即時影像；採來源影像或其縮小版本，頁面依版面縮放。</figcaption></figure><div class="article-layout"><nav class="toc" aria-label="文章目錄">{nav}</nav><article><p class="notice">時間與票價依查核日的官方資料整理，出發前請確認最新公告。</p>{body}</article></div>'''
    dest=OUT/'places'/f'{p["id"]}.html';dest.parent.mkdir(exist_ok=True);dest.write_text(shell(x['title'],article,'../',x['summary']),encoding='utf-8')
    notes=(ROOT/'wiki/sources'/f'{p["id"]}.md').read_text(encoding='utf-8')
    content,_=markdown(notes)
    dest=OUT/'sources'/f'{p["id"]}.html';dest.parent.mkdir(exist_ok=True);dest.write_text(shell(x['title']+'來源筆記',f'<div class="credits"><p class="breadcrumb"><a href="../places/{p["id"]}.html">返回景點文章</a></p><h1 style="font-size:36px">來源筆記</h1><article>{content}</article></div>','../'),encoding='utf-8')
home=f'''<section class="intro"><div><span class="eyebrow">A field guide to Taiwan</span><h1>把日子放慢，<br>沿著<em>台灣走走。</em></h1></div><p>從北海岸到東海岸，從山間池畔走向離島石屋。<br>不只收藏地點，也讀懂風景背後的故事。</p></section><section aria-labelledby="gallery-title"><div class="section-head"><div><small>{place_count} PLACES, {place_count} STORIES</small><h2 id="gallery-title">下一站，想去哪裡？</h2></div><div class="controls"><button id="previous" aria-label="上一張景點照片">←</button><button id="next" aria-label="下一張景點照片">→</button></div></div><div class="gallery" tabindex="0" aria-label="景點圖集，可左右滑動或使用左右方向鍵">{''.join(slides)}</div><p class="gallery-note"><span>左右滑動，發現不同風景 · <span id="gallery-status" aria-live="polite">1 / {place_count}</span></span><a href="credits.html">實景照片與作者授權 ↗</a></p></section><section class="explore" id="explore"><div class="section-head"><div><span class="eyebrow">Find your next walk</span><h2>依你的步調，找一個地方</h2></div></div><div class="searchbar"><label>搜尋景點、縣市或特色<input id="search" type="search" placeholder="試試：鹽田、南投、自然地景" autocomplete="off"></label><label>探索地區<select id="region"><option>全部</option><option>北部</option><option>中部</option><option>南部</option><option>東部</option><option>離島</option></select></label><button id="reset">清除篩選</button></div><p id="result-count" role="status">共{place_count}個景點</p><div class="cards">{''.join(cards)}</div><p id="empty" class="empty" hidden>還沒有符合的景點，換個關鍵字或清除篩選試試。</p><noscript><p>關鍵字搜尋與圖集箭頭需要 JavaScript；仍可滑動照片、閱讀下方全部景點。</p></noscript></section><section class="about" id="about"><div><span class="eyebrow">About this collection</span><h2>風景有故事，<br>知識有出處。</h2></div><div><p>台灣走走是一個持續累積的旅遊知識庫，以官方來源整理景點的地景、文化與參觀資訊。每篇都保留來源和查核日期，讓下一次探索有跡可循。</p><p>以政府觀光網站、景點官網及營運單位資料交叉整理。時間與費用可能變動；照片為歷年實景，不能代表當日狀態。</p><span class="badge">官方來源</span><span class="badge">持續更新</span><span class="badge">{place_count} 則地方故事</span></div></section>'''
(OUT/'index.html').write_text(shell('把日子放慢',home),encoding='utf-8')
credits=''.join(f'<section class="credit"><img src="assets/photos/{p["file"]}" alt="{esc(p["alt"])}"><h2>{esc(p["title"])}</h2><p>{credit(p)}</p><p>使用來源照片或其縮小版本，不調色或變更畫面內容；首頁與卡片以 CSS 裁切顯示，文章頁可看完整構圖。照片及其裁切呈現沿用所列授權，不代表作者為本網站背書。</p><a href="assets/photos/{p["file"]}">查看完整照片 ↗</a></section>' for p in photos)
(OUT/'credits.html').write_text(shell('圖片出處',f'<div class="credits"><span class="eyebrow">Photo credits</span><h1 style="font-size:42px">每張風景，都有出處。</h1><p>以下為歷年實景照片，非即時影像。授權查核日期：2026-11-16。</p>{credits}</div>'),encoding='utf-8')
(OUT/'.nojekyll').write_text('',encoding='utf-8')
dist=ROOT/'dist';shutil.copytree(OUT,dist,dirs_exist_ok=True)
print(f'Built homepage, {place_count} place pages, {place_count} source pages and photo credits.')
