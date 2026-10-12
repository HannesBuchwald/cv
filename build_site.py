"""Build the static CV from the repository's Markdown. Python standard library only."""
from pathlib import Path
import html, re, shutil, os

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'site'
OUT.mkdir(exist_ok=True)

def read(path):
    raw = path.read_text()
    meta = {}
    if raw.startswith('---\n'):
        _, head, body = raw.split('---', 2)
        lines = head.splitlines()
        for i, line in enumerate(lines):
            m = re.match(r'^([\w_]+):\s*(.*)', line)
            if not m: continue
            key, value = m.groups()
            if value == '>-':
                value = ' '.join(x.strip() for x in lines[i+1:] if x.startswith('  ') and not x.lstrip().startswith('-'))
            meta[key] = value.strip('"')
        return meta, body.strip()
    return meta, raw

def inline(text, source):
    def url(u):
        if u.startswith(('http:', 'https:', 'mailto:', '#')): return u
        base, sep, anchor = u.partition('#')
        dest = (source.parent / base).resolve()
        if base.endswith('.md'): dest = dest.with_suffix('.html')
        target = OUT / dest.relative_to(ROOT)
        return os.path.relpath(target, (OUT / source.relative_to(ROOT)).parent) + (sep + anchor if sep else '')
    def token(m):
        image, label, u = m.groups()
        safe = html.escape(url(u), quote=True)
        if image: return '<figure><img loading="lazy" src="'+safe+'" alt="'+html.escape(label, quote=True)+'"></figure>'
        return '<a href="'+safe+'">'+html.escape(label)+'</a>'
    placeholders = []
    def stash(m):
        placeholders.append(token(m)); return '\x00'+str(len(placeholders)-1)+'\x00'
    text = re.sub(r'(!?)\[([^\]]+)\]\(([^)]+)\)', stash, text)
    text = html.escape(text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return re.sub(r'\x00(\d+)\x00', lambda m: placeholders[int(m[1])], text)

def render(body, source, skip_title=True):
    out, paragraph, inlist = [], [], False
    def flush():
        if paragraph: out.append('<p>'+inline(' '.join(paragraph), source)+'</p>'); paragraph.clear()
    for line in body.splitlines():
        heading = re.match(r'^(#{1,6}) (.+)$', line)
        bullet = line.startswith('- ')
        if not bullet and inlist: out.append('</ul>'); inlist=False
        if heading:
            flush(); level=len(heading[1])
            if level==1 and skip_title: continue
            out.append(f'<h{level}>'+inline(heading[2],source)+f'</h{level}>')
        elif bullet:
            flush()
            if not inlist: out.append('<ul>'); inlist=True
            out.append('<li>'+inline(line[2:],source)+'</li>')
        elif not line.strip(): flush()
        elif line.startswith('!['): flush(); out.append(inline(line,source))
        else: paragraph.append(line)
    flush()
    if inlist: out.append('</ul>')
    return ''.join(out)

def page(title, content, filename, active='', description=''):
    depth = len(Path(filename).parts)-1
    prefix = '../'*depth
    nav = ''.join('<a '+('aria-current="page" ' if label==active else '')+'href="'+prefix+target+'">'+label+'</a>' for label,target in [('Projekte','projekte.html'),('CV','cv.html'),('Publications','publications.html'),('Fotografie','portraetfotografie.html')])
    data = f'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{html.escape(description,quote=True)}"><title>{html.escape(title)} · Hannes Buchwald</title><link rel="stylesheet" href="{prefix}style.css"></head><body><a class="skip" href="#content">Zum Inhalt</a><header><a class="brand" href="{prefix}index.html"><span>HB</span>Hannes Buchwald</a><nav aria-label="Hauptnavigation">{nav}</nav></header><main id="content">{content}</main><footer><span>Hannes Buchwald · Fotografie, Design & Informatik</span><a href="https://github.com/HannesBuchwald/cv">GitHub ↗</a></footer><script src="{prefix}site.js" defer></script></body></html>'''
    dest=OUT/filename;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(data)

projects = []
for path in (ROOT/'Projekte').glob('*.md'):
    meta,body=read(path);projects.append((path,meta,body))
projects.sort(key=lambda x: max(re.findall(r'\d{4}',x[1].get('period','')) or ['0000']),reverse=True)
cards=[]
for n,(path,m,body) in enumerate(projects,1):
    tags=m.get('tags','').strip('[]').split(',')
    group='code' if any(t.strip() in ['Forschung','Lehre','App-Entwicklung','Zeitnutzung'] for t in tags) else 'photo'
    images=re.findall(r'!\[([^\]]*)\]\(([^)]+)\)',body)
    visual=''
    if images:
        alt,u=images[0];u=u if u.startswith('http') else str((path.parent/u).resolve().relative_to(ROOT))
        visual='<img loading="lazy" src="'+html.escape(u,quote=True)+'" alt="'+html.escape(alt,quote=True)+'">'
    else:visual='<div class="project-mark" aria-hidden="true">'+('02' if '2.0' in m.get('title','') else '↗')+'</div>'
    period=m.get('period','');period='' if period=='null' else period
    cards.append('<article class="project" data-group="'+group+'"><a href="'+str(path.relative_to(ROOT).with_suffix('.html'))+'"><div class="project-image">'+visual+'</div><div class="project-copy"><span class="eyebrow">'+html.escape(period or 'FORSCHUNG & DESIGN')+'</span><h3>'+html.escape(m.get('title',path.stem))+' <span>↗</span></h3><p>'+html.escape(m.get('description',''))+'</p><small>'+html.escape(m.get('role',''))+'</small></div></a></article>')
    facts=''.join('<div><dt>'+label+'</dt><dd>'+html.escape(m[key])+'</dd></div>' for key,label in [('period','Zeitraum'),('role','Rolle'),('location','Ort'),('scope','Reichweite')] if m.get(key) and m[key]!='null')
    content='<div class="page-head"><a class="back" href="../projekte.html">← Alle Projekte</a><p class="eyebrow">PROJEKT / '+str(n).zfill(2)+'</p><h1>'+html.escape(m.get('title',''))+'</h1><p class="lead">'+html.escape(m.get('description',''))+'</p></div><dl class="facts">'+facts+'</dl><div class="reading">'+render(body,path)+'</div>'
    page(m.get('title','Projekt'),content,str(path.relative_to(ROOT).with_suffix('.html')),'Projekte',m.get('description',''))

art='''<svg viewBox="0 0 420 420" role="img" aria-label="Verbundene geometrische Formen als Sinnbild für Menschen, Bilder und Technik"><defs><pattern id="hatch" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(35)"><path d="M0 0V9" stroke="#19362e" stroke-width="1"/></pattern></defs><circle cx="160" cy="155" r="120" fill="#cef08b"/><circle cx="235" cy="255" r="120" fill="url(#hatch)"/><rect x="155" y="35" width="155" height="300" rx="78" transform="rotate(35 235 185)" fill="none" stroke="#19362e"/><path d="M30 310L320 50L380 360Z" fill="none" stroke="#19362e"/><circle cx="200" cy="200" r="30" fill="#19362e"/></svg>'''
home='''<div class="hero"><div><p class="eyebrow">HANNES BUCHWALD / PERSÖNLICHES CV</p><h1>Menschen.<br><em>Bilder.</em><br>Möglichkeiten.</h1><p class="lead">Mein Weg zwischen sozialer Perspektive, Fotografie, kreativem Denken und Informatik.</p><a class="button" href="projekte.html">Meine Projekte entdecken ↗</a></div><div class="hero-art">'''+art+'''<span>VIER PERSPEKTIVEN. EIN PROFIL.</span></div></div><div class="discipline"><span>Sozial</span><span>Fotografie</span><span>Design</span><span>Computer Science</span></div><section class="home-projects"><div class="section-head"><div><p class="eyebrow">ARBEITEN & STATIONEN</p><h2>Von der Idee<br>zur Begegnung.</h2></div><p>Fotografie, Forschung und Lehre: ausgewählte Projekte und die Geschichten dahinter.</p></div><div class="projects">'''+''.join(cards[:4])+'''</div><a class="text-link" href="projekte.html">Alle sechs Projekte ansehen ↗</a></section><div class="paths"><a href="cv.html"><span>01 / PROFIL</span><h2>Lebenslauf ↗</h2><p>Beruf, Ausbildung und fachliche Schwerpunkte.</p></a><a href="publications.html"><span>02 / VERÖFFENTLICHUNGEN</span><h2>Publications ↗</h2><p>Awards, Papers, Konferenzen und Presse.</p></a><a href="portraetfotografie.html"><span>03 / PERSPEKTIVE</span><h2>Fotografie ↗</h2><p>Menschen und ihre individuellen Geschichten.</p></a></div>'''
page('Start',home,'index.html',description='Hannes Buchwald – Projekte, Lebenslauf, Veröffentlichungen und Fotografie.')
filters='<div class="filters" aria-label="Projekte filtern"><button data-filter="all" aria-pressed="true">Alle</button><button data-filter="code" aria-pressed="false">Forschung & Lehre</button><button data-filter="photo" aria-pressed="false">Fotografie & Kunst</button></div>'
page('Projekte','<div class="page-head"><p class="eyebrow">ARBEITEN & STATIONEN</p><h1>Projekte.</h1><p class="lead">Sechs Einblicke in Fotografie, Forschung, Design und Lehre.</p></div>'+filters+'<div class="projects">'+''.join(cards)+'</div>','projekte.html','Projekte')
for name,active in [('cv','CV'),('publications','Publications'),('portraetfotografie','Fotografie')]:
    path=ROOT/(name+'.md');m,body=read(path)
    content=render(body,path)
    if name=='publications':
        sections=re.split(r'(?=<h2>)',content)
        content='<div class="pubfilters filters"><button data-pub="all" aria-pressed="true">Alle</button>'+''.join('<button data-pub="'+str(i)+'" aria-pressed="false">'+re.search(r'<h2>(.*?)</h2>',s)[1]+'</button>' for i,s in enumerate(sections) if '<h2>' in s and i<=4)+'</div>'+''.join('<section class="pubsection" data-section="'+str(i)+'">'+s+'</section>' for i,s in enumerate(sections))
    if name=='portraetfotografie':
        # Keep the editorial checklist in Markdown, show only the visitor-facing content here.
        content='<h2>Mein Blick auf Menschen</h2><p>Menschen und ihre individuellen Geschichten stehen im Mittelpunkt meiner Porträtfotografie. Mich interessiert, wie ein Bild Begegnungen auf Augenhöhe ermöglicht und die Würde der porträtierten Person sichtbar werden lässt.</p><div class="empty-gallery"><span class="eyebrow">BILDAUSWAHL FOLGT</span><p>Die Porträtgalerie wird gerade zusammengestellt.</p></div><h2>Ausstellungen</h2><ul><li><a href="Projekte/face-to-face.html">Face to Face · 2009</a></li><li><a href="Projekte/party-life.html">Party Life · 2009–2010</a></li></ul>'
    title={'cv':'Lebenslauf.','publications':'Publications.','portraetfotografie':'Porträtfotografie.'}[name]
    page(title,'<div class="page-head"><p class="eyebrow">HANNES BUCHWALD</p><h1>'+title+'</h1></div><div class="reading">'+content+'</div>',name+'.html',active,m.get('description',''))
if (ROOT/'assets').exists():shutil.copytree(ROOT/'assets',OUT/'assets',dirs_exist_ok=True)
shutil.copyfile(ROOT/'web/style.css',OUT/'style.css');shutil.copyfile(ROOT/'web/site.js',OUT/'site.js')
print(f'Built {len(list(OUT.rglob("*.html")))} pages in {OUT}')
