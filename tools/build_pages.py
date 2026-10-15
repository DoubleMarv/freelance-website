"""Generate Freelance Ireland service + county landing pages, sitemap and robots.txt.

Usage: python3 build_pages.py <site_root>
Re-run any time; it overwrites the generated folders only.
"""
import sys, os, html, re, json
from datetime import date

ROOT = sys.argv[1]
SITE = "https://freelance-ireland.com"
TODAY = date.today().isoformat()

COUNTIES = {
    "Carlow": ["Kildare", "Laois", "Kilkenny", "Wexford", "Wicklow"],
    "Cavan": ["Monaghan", "Meath", "Westmeath", "Longford", "Leitrim"],
    "Clare": ["Galway", "Tipperary", "Limerick"],
    "Cork": ["Kerry", "Limerick", "Tipperary", "Waterford"],
    "Donegal": ["Leitrim", "Sligo"],
    "Dublin": ["Meath", "Kildare", "Wicklow"],
    "Galway": ["Mayo", "Roscommon", "Offaly", "Tipperary", "Clare"],
    "Kerry": ["Cork", "Limerick"],
    "Kildare": ["Dublin", "Meath", "Offaly", "Laois", "Carlow", "Wicklow"],
    "Kilkenny": ["Laois", "Carlow", "Wexford", "Waterford", "Tipperary"],
    "Laois": ["Offaly", "Kildare", "Carlow", "Kilkenny", "Tipperary"],
    "Leitrim": ["Donegal", "Sligo", "Roscommon", "Longford", "Cavan"],
    "Limerick": ["Clare", "Tipperary", "Cork", "Kerry"],
    "Longford": ["Leitrim", "Cavan", "Westmeath", "Roscommon"],
    "Louth": ["Meath", "Monaghan"],
    "Mayo": ["Sligo", "Roscommon", "Galway"],
    "Meath": ["Louth", "Monaghan", "Cavan", "Westmeath", "Offaly", "Kildare", "Dublin"],
    "Monaghan": ["Cavan", "Meath", "Louth"],
    "Offaly": ["Westmeath", "Meath", "Kildare", "Laois", "Tipperary", "Galway", "Roscommon"],
    "Roscommon": ["Sligo", "Leitrim", "Longford", "Westmeath", "Offaly", "Galway", "Mayo"],
    "Sligo": ["Leitrim", "Roscommon", "Mayo", "Donegal"],
    "Tipperary": ["Galway", "Offaly", "Laois", "Kilkenny", "Waterford", "Cork", "Limerick", "Clare"],
    "Waterford": ["Kilkenny", "Tipperary", "Cork", "Wexford"],
    "Westmeath": ["Longford", "Cavan", "Meath", "Offaly", "Roscommon"],
    "Wexford": ["Wicklow", "Carlow", "Kilkenny", "Waterford"],
    "Wicklow": ["Dublin", "Kildare", "Carlow", "Wexford"],
}
# Sanity: adjacency must be symmetric.
for c, ns in COUNTIES.items():
    for n in ns:
        assert c in COUNTIES[n], f"{c} -> {n} not symmetric"

SERVICES = [
    dict(slug="freelance-web-designers", form="Web design", noun="web designers", short="Web design",
         lede="Websites with personality, designed to look good and work hard.",
         items=[("Business websites", "A site that explains what you do and makes it easy to get in touch."),
                ("Redesigns", "A fresh look for a site that no longer reflects the business."),
                ("Landing pages", "Focused pages for a launch, campaign or event."),
                ("Online shops", "Product pages and checkout that are simple to use.")],
         faq=("What should I put in a web design brief?",
              "What the site is for, who it's for, a few sites you like, and any content you already have. Rough is fine.")),
    dict(slug="freelance-graphic-designers", form="Brand & graphic design", noun="graphic designers", short="Brand & graphic design",
         lede="Distinctive identities and thoughtful design, for screen and print.",
         items=[("Logos & brand identity", "A mark, colours and type that feel like you."),
                ("Print & brochures", "Brochures, programmes, posters and signage."),
                ("Packaging", "Packaging and labels that stand out on the shelf."),
                ("Marketing assets", "Social graphics, ads and presentation templates.")],
         faq=("What should I put in a design brief?",
              "What you need designed, where it'll be used, any existing brand guidelines, and examples of styles you like.")),
    dict(slug="freelance-web-developers", form="Development", noun="web developers", short="Development",
         lede="From first click to final detail. Bring your digital ideas to life.",
         items=[("WordPress builds", "Custom themes and blocks that are easy to edit yourself."),
                ("Shopify", "Store setup, theme work and customisation."),
                ("Integrations", "Connecting your site to CRMs, booking, payments and other tools."),
                ("Fixes & maintenance", "Speed, security, updates and bugs on an existing site.")],
         faq=("I have an existing site. Can a developer work on it?",
              "Usually, yes. Tell us what it's built on, if you know, and what needs doing.")),
    dict(slug="freelance-motion-designers", form="Motion & illustration", noun="motion designers & illustrators", short="Motion & illustration",
         lede="A little movement, a different perspective. Make people look twice.",
         items=[("Social & explainer video", "Short animated pieces for social, ads or your site."),
                ("Web animation", "Lightweight animations and interactions for websites."),
                ("Illustration", "Custom illustration for brands, editorial and print."),
                ("Animated brand assets", "Logo animations, motion guidelines and stings.")],
         faq=("What do I need for a motion or illustration project?",
              "Where it'll be shown, rough length or size, any brand assets, and examples of styles you like.")),
]

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

ARROW = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 7h10v10"/><path d="M7 17 17 7"/></svg>'
CHEV = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>'
BTN = "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium cursor-pointer transition-colors fi-button h-9 px-4 py-2"
FIELD = "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-sm md:text-sm"
e = html.escape

def head(title, desc, path):
    url = SITE + path
    return f"""<!doctype html>
<html lang="en-IE">
<head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}"/>
<link rel="canonical" href="{url}"/>
<meta property="og:title" content="{e(title)}"/><meta property="og:description" content="{e(desc)}"/>
<meta property="og:type" content="website"/><meta property="og:url" content="{url}"/>
<meta property="og:image" content="{SITE}/images/og-image.jpg"/><meta name="twitter:card" content="summary_large_image"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;650;700&family=Space+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/seo-pages.css">
</head>
<body>
<div class="site-wrap">
<header class="site-header container">
<a href="/" class="logo" aria-label="Freelance Ireland home"><span class="logo-word">freelance<br/>ireland</span><span class="logo-symbol">*</span></a>
<nav class="nav-links" aria-label="Main navigation"><a href="/#expertise">Find your talent</a><a href="/#how-it-works">How it works</a><a href="/#for-freelancers">For freelancers</a></nav>
<div class="header-actions">
<a href="/#for-freelancers" class="{BTN} fi-button-quiet">Join the network {ARROW}</a>
<a href="#brief" class="{BTN} fi-button-primary">Start a project {ARROW}</a>
</div>
</header>
<main>"""

def breadcrumbs(trail):
    items = json.dumps([{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + p}
                        for i, (n, p) in enumerate(trail)], ensure_ascii=False)
    nav = ' <span aria-hidden="true">/</span> '.join(
        f'<a href="{p}">{e(n)}</a>' if i < len(trail) - 1 else f'<span aria-current="page">{e(n)}</span>'
        for i, (n, p) in enumerate(trail))
    return (f'<nav class="crumbs container" aria-label="Breadcrumb">{nav}</nav>'
            f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":{items}}}</script>')

def form(service, county):
    opts = "".join(f'<option{" selected" if s["form"] == service["form"] else ""}>{e(s["form"])}</option>' for s in SERVICES)
    loc = e(county) if county else ""
    return f"""<div class="hero-request-area seo-form" id="brief">
<form class="enquiry-form quick-enquiry-form" aria-label="Project enquiry">
<input type="hidden" name="location" value="{loc}"/>
<div class="form-pair">
<label>Your name<input class="{FIELD}" autocomplete="name" required maxlength="100" placeholder="Alex Taylor" name="name"/></label>
<label>Email address<input type="email" class="{FIELD}" autocomplete="email" required maxlength="255" placeholder="alex@example.com" name="email"/></label>
</div>
<div class="form-pair">
<label>What do you need?<select name="service">{opts}</select></label>
<label>Project budget<select name="budget"><option selected>Not sure yet</option><option>Under €1,000</option><option>€1,000–€5,000</option><option>€5,000–€10,000</option><option>€10,000+</option></select></label>
</div>
<label>A little about your project<textarea class="{FIELD} min-h-[60px]" name="details" required minlength="10" maxlength="3000" rows="3" placeholder="What would you like to make? Any timelines in mind?"></textarea></label>
<div class="honeypot" aria-hidden="true"><label>Website<input class="{FIELD}" tabindex="-1" autocomplete="off" name="website"/></label></div>
<div class="quick-form-footer">
<label class="consent"><input type="checkbox" required name="consent"/><span>I agree to Freelance Ireland storing my details and contacting me about this enquiry.</span></label>
<button class="{BTN} fi-button-primary" type="submit">Send my request{ARROW}</button>
</div>
</form>
</div>"""

def services_block(service):
    cards = "".join(f'<article class="service-item"><h3>{e(t)}</h3><p>{e(d)}</p></article>' for t, d in service["items"])
    return cards

def process():
    return """<section class="section process-section"><div class="container">
<div class="section-header"><div><span class="eyebrow">LESS SEARCHING. MORE MAKING.</span><h2>How it works.</h2></div></div>
<div class="process-grid">
<div class="process-step"><span class="step-number">01 / THE IDEA</span><h3>Tell us what’s on your mind.</h3><p>Share your idea, your goals, and the kind of talent you’re looking for. A rough sketch is a great place to start.</p></div>
<div class="process-step"><span class="step-number">02 / THE PEOPLE</span><h3>Meet your kind of creative.</h3><p>We’ll review your brief and get in touch to connect you with independent talent that fits your project.</p></div>
<div class="process-step"><span class="step-number">03 / THE GOOD STUFF</span><h3>Make something that matters.</h3><p>Agree on the scope, connect with your collaborator, and turn that “what if” into something real.</p></div>
</div></div></section>"""

def faq(items):
    rows = "".join(f'<details class="faq-item"><summary>{e(q)}{CHEV}</summary><p>{e(a)}</p></details>' for q, a in items)
    ld = json.dumps([{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items], ensure_ascii=False)
    return (f'<section class="section container faq-layout"><div><span class="eyebrow">A FEW GOOD QUESTIONS</span><h2>Glad you asked.</h2></div><div>{rows}</div></section>'
            f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":{ld}}}</script>')

def links_block(title, links):
    lis = "".join(f'<li><a href="{p}">{e(n)}</a></li>' for n, p in links)
    return f'<section class="section container link-block"><h2 class="link-block-title">{e(title)}</h2><ul class="link-grid">{lis}</ul></section>'

def footer():
    hubs = "".join(f'<a href="/{s["slug"]}/">Freelance {e(s["noun"])}</a>' for s in SERVICES)
    return f"""</main>
<footer class="footer">
<div class="container footer-inner">
<a href="/" class="logo" aria-label="Freelance Ireland home"><span class="logo-word">freelance<br/>ireland</span><span class="logo-symbol">*</span></a>
<p>© 2026 Freelance Ireland. Good people. Great work.</p>
<a href="https://doublemarvellous.com" style="font-size: 10px;">Built by Doublemarvellous</a>
<div class="footer-right"><a href="/#questions">Questions?</a><a href="#brief" class="{BTN} fi-button-primary">Let’s make something {ARROW}</a></div>
</div>
<nav class="container footer-links" aria-label="Services">{hubs}</nav>
</footer>
</div>
<script src="/script.js" defer></script>
</body>
</html>
"""

def page_path(service, county=None):
    return f"/{service['slug']}/" + (f"{slug(county)}/" if county else "")

def write(path, content):
    full = os.path.join(ROOT, path.strip("/"), "index.html")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)

urls = []

for s in SERVICES:
    # Hub page
    path = page_path(s)
    title = f"Freelance {s['noun'].title()} in Ireland | Freelance Ireland"
    desc = f"Find independent freelance {s['noun']} across Ireland. Share a brief and Freelance Ireland will connect you with suitable talent."
    body = (head(title, desc, path)
            + breadcrumbs([("Home", "/"), (f"Freelance {s['noun']}", path)])
            + f'<section class="hero hero-requests container seo-hero"><span class="eyebrow"><span class="status-dot"></span> {e(s["short"].upper())} · IRELAND</span>'
            + f'<h1 class="hero-title seo-title">Freelance {e(s["noun"])} in Ireland.</h1>'
            + f'<p class="hero-description">{e(s["lede"])}<br/>Tell us what you need and we’ll connect you with independent talent.</p>'
            + form(s, "") + "</section>"
            + f'<section class="section container"><div class="section-header"><div><span class="eyebrow">WHAT WE CAN HELP WITH</span><h2>{e(s["short"])} projects.</h2></div></div><div class="service-grid">{services_block(s)}</div></section>'
            + links_block(f"Freelance {s['noun']} by county", [(c, page_path(s, c)) for c in COUNTIES])
            + process()
            + faq([s["faq"],
                   ("Do I need a freelancer near me?", "Not necessarily. Plenty of projects work well remotely. If meeting in person matters, say so in your brief."),
                   ("What will it cost?", "It depends on the scope. Pick a budget range in the form, or ‘Not sure yet’, and we’ll talk it through.")])
            + footer())
    write(path, body)
    urls.append(path)

    for c, near in COUNTIES.items():
        path = page_path(s, c)
        title = f"Freelance {s['noun'].title()} in {c} | Freelance Ireland"
        desc = f"Looking for freelance {s['noun']} in {c}? Share your brief and Freelance Ireland will connect you with independent Irish talent."
        others = [x for x in SERVICES if x is not s]
        body = (head(title, desc, path)
                + breadcrumbs([("Home", "/"), (f"Freelance {s['noun']}", page_path(s)), (c, path)])
                + f'<section class="hero hero-requests container seo-hero"><span class="eyebrow"><span class="status-dot"></span> {e(s["short"].upper())} · {e(c.upper())}</span>'
                + f'<h1 class="hero-title seo-title">Freelance {e(s["noun"])} in {e(c)}.</h1>'
                + f'<p class="hero-description">{e(s["lede"])}<br/>Tell us about your {e(c)} project and we’ll connect you with independent talent.</p>'
                + form(s, c) + "</section>"
                + f'<section class="section container"><div class="section-header"><div><span class="eyebrow">FOR {e(c.upper())} BUSINESSES</span><h2>{e(s["short"])} projects.</h2></div>'
                + f'<p>Independent talent from across Ireland, working with {e(c)} businesses in person or remotely.</p></div><div class="service-grid">{services_block(s)}</div></section>'
                + process()
                + faq([s["faq"],
                       (f"Do I need a freelancer based in {c}?", f"Not necessarily. Plenty of projects work well remotely. If meeting in person in {c} matters to you, say so in your brief and we’ll take it into account."),
                       ("What will it cost?", "It depends on the scope. Pick a budget range in the form, or ‘Not sure yet’, and we’ll talk it through.")])
                + links_block(f"Also in {c}", [(f"Freelance {x['noun']}", page_path(x, c)) for x in others])
                + links_block("Nearby counties", [(n, page_path(s, n)) for n in near])
                + footer())
        write(path, body)
        urls.append(path)

# Sitemap + robots
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
      f"<url><loc>{SITE}/</loc><lastmod>{TODAY}</lastmod></url>"]
sm += [f"<url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>" for u in urls]
sm.append("</urlset>")
open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
print(len(urls), "pages")
