# -*- coding: utf-8 -*-
"""
複利人生實驗室 — 靜態站建置腳本
讀 passive-income-projects/03-affiliate-marketing/content 的 20 篇 .md，
轉成套用設計系統的 HTML（文章頁 + 首頁 + 5 分類索引），輸出到本 repo。
重跑即重建；之後填聯盟連結或加新文章只要再跑一次。
"""
import re
import html
import json
import markdown
from pathlib import Path

ROOT = Path(r"C:\Users\youfu\compound-life-lab")
SRC = Path(r"C:\Users\youfu\passive-income-projects\03-affiliate-marketing\content")
BASE = "https://youfuxu.github.io/compound-life-lab"
BRAND = "複利人生實驗室"
TAGLINE = "每天一個讓錢自動工作的方法"
SITE_DESC = "複利人生實驗室——用台灣人熟悉的方式，把 ETF、券商開戶、信用卡、保險講清楚，幫你做出適合自己的理財決定。"
# 站台發布日：同時給 sitemap 的 lastmod 與結構化資料的 datePublished 使用，
# 兩邊共用同一個常數，避免 schema 出現與 sitemap 不一致（或憑空捏造）的日期。
PUB_DATE = "2026-07-02"

# 分類：資料夾 → (顯示名, 索引頁 slug, 說明)
CATS = {
    "articles":    ("理財觀念", "concepts",    "投資理財的基礎觀念與新手入門"),
    "brokerages":  ("券商開戶", "brokers",     "台股與美股券商開戶教學、優惠與比較"),
    "comparisons": ("ETF 與商品比較", "comparisons", "熱門 ETF、信用卡回饋，一張表看懂怎麼選"),
    "credit-cards":("信用卡",   "cards",       "現金回饋、旅遊哩程、開卡禮怎麼選最划算"),
    "insurance":   ("保險",     "insurance",   "定期險、醫療險、意外險完整解析"),
}
CAT_ORDER = ["articles", "brokerages", "comparisons", "credit-cards", "insurance"]

# 檔名（無副檔名）→ 乾淨 ASCII slug
SLUGS = {
    "ETF推薦新手2026": "etf-beginners-2026",
    "存股策略入門2026": "dividend-stock-investing-2026",
    "存股資產追蹤工具2026": "asset-tracking-tools-2026",
    "定存vs-ETF哪個好2026": "deposit-vs-etf-2026",
    "美股ETF台灣買法2026": "buy-us-etf-taiwan-2026",
    "國泰證券開戶優惠": "cathay-securities-account",
    "富途證券評價優缺點": "futu-moomoo-review",
    "永豐證券開戶教學": "sinopac-securities-guide",
    "美股複委託vs海外券商比較": "sub-brokerage-vs-overseas-broker",
    "複委託開戶推薦2026": "sub-brokerage-recommend-2026",
    "0050-0056-006208-差別比較": "0050-0056-006208-comparison",
    "00878存股月配息評價": "00878-monthly-dividend-review",
    "VOO-QQQ-VTI怎麼選": "voo-qqq-vti-comparison",
    "信用卡海外刷卡回饋比較": "credit-card-overseas-cashback",
    "月配息ETF推薦2026": "monthly-dividend-etf-2026",
    "新戶信用卡開卡禮推薦": "new-cardholder-bonus",
    "旅遊信用卡哩程比較": "travel-mileage-card-comparison",
    "現金回饋信用卡推薦2026": "cashback-credit-card-2026",
    "定期險推薦比較": "term-life-insurance-comparison",
    "實支實付醫療險推薦": "medical-reimbursement-insurance",
    "意外險旅平險比較平台": "accident-travel-insurance",
    "理財族帳戶資安防護2026": "investment-account-security-2026",
}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap" rel="stylesheet">')

CF_ANALYTICS = ('<!-- Cloudflare Web Analytics --><script defer '
                "src='https://static.cloudflareinsights.com/beacon.min.js' "
                'data-cf-beacon=\'{"token": "e025212f3d784f0f848b0c0e98142893"}\'>'
                '</script><!-- End Cloudflare Web Analytics -->')


def topbar(prefix):
    nav = "".join(f'<a href="{prefix}{CATS[c][1]}.html">{CATS[c][0]}</a>' for c in CAT_ORDER)
    return (f'<div class="topbar"><div class="wrap">'
            f'<a href="{prefix}index.html" class="logo">複利人生<span class="dot">·</span>實驗室</a>'
            f'<div class="topnav">{nav}</div></div></div>')


def footer(prefix=""):
    links = " · ".join(f'<a href="{prefix}{CATS[c][1]}.html">{CATS[c][0]}</a>' for c in CAT_ORDER)
    tools = ('<div style="margin-top:8px">推薦工具：'
             '<a href="https://go.nordvpn.net/aff_c?offer_id=15&aff_id=151508&url_id=22500" '
             'rel="nofollow sponsored noopener" target="_blank">NordVPN — 公共 Wi-Fi 下保護券商與網銀登入</a>'
             '（聯盟連結，不會增加你的費用）</div>')
    radar = ('<div style="margin-top:8px">📡 每天 08:00 一分鐘看完市場哪裡不對勁 → '
             '<a href="https://t.me/youfu_trend" rel="noopener" target="_blank">Telegram 市場異常雷達</a>（免費）</div>')
    return (f'<footer><div class="wrap">'
            f'<div>© 2026 {BRAND} — {TAGLINE}</div>'
            f'<div>{links}</div>{tools}{radar}</div></footer>')


def parse_md(path: Path):
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    # H1
    h1 = next((l[2:].strip() for l in lines if l.startswith("# ")), path.stem)
    # SEO 標題 / Meta Description（在開頭 blockquote）
    m_title = re.search(r"SEO\s*標題[*\s]*[：:]\s*(.+)", raw)
    m_desc = re.search(r"Meta\s*Description[*\s]*[：:]\s*(.+)", raw)
    seo_title = (m_title.group(1).strip() if m_title else h1).replace("**", "").strip()
    meta_desc = (m_desc.group(1).strip() if m_desc else "").replace("**", "").strip()
    # 移除 H1 與開頭 meta blockquote，再去掉開頭多餘的空行/分隔線
    body_lines = []
    for l in lines:
        if l.startswith("# "):
            continue
        if l.lstrip().startswith(">") and ("SEO 標題" in l or "Meta Description" in l):
            continue
        body_lines.append(l)
    # 去掉開頭殘留的空行與第一條 ---
    while body_lines and (body_lines[0].strip() == "" or body_lines[0].strip() == "---"):
        body_lines.pop(0)
    body_md = "\n".join(body_lines)
    body_html = markdown.markdown(body_md, extensions=["tables", "fenced_code", "sane_lists"])
    # 表格加捲動容器
    body_html = body_html.replace("<table>", '<div class="table-scroll"><table>').replace("</table>", "</table></div>")
    # 聯盟連結揭露標籤（半形/全形括號）
    body_html = re.sub(r"[（(]\s*聯盟連結\s*[)）]", '<span class="aff">聯盟連結</span>', body_html)
    if not meta_desc:
        # 後備：取第一段純文字前 70 字
        txt = re.sub(r"<[^>]+>", "", body_html)
        meta_desc = txt.strip().replace("\n", "")[:70]
    return {"h1": h1, "seo_title": seo_title, "meta_desc": meta_desc, "body": body_html}


def related_block(related):
    if not related:
        return ""
    items = "".join(
        f'<a class="card" href="{r["_slug"]}.html">'
        f'<div class="ct">{r["_cat_name"]}</div>'
        f'<div class="ch">{html.escape(r["h1"])}</div>'
        f'<div class="cd">{html.escape(r["meta_desc"][:62])}…</div></a>'
        for r in related
    )
    return (f'<div class="section-title" style="margin-top:48px">'
            f'<span class="bar"></span>延伸閱讀</div>'
            f'<div class="cards">{items}</div>')


def ldjson(obj):
    """把 dict 包成 <script type="application/ld+json"> 區塊。"""
    return ('<script type="application/ld+json">\n'
            + json.dumps(obj, ensure_ascii=False, indent=2)
            + '\n</script>')


def site_node():
    """WebSite 與 Organization 節點，供各頁以 @id 參照。"""
    return [
        {"@type": "Organization", "@id": f"{BASE}/#org",
         "name": BRAND, "url": f"{BASE}/"},
        {"@type": "WebSite", "@id": f"{BASE}/#website",
         "name": BRAND, "url": f"{BASE}/", "description": SITE_DESC,
         "inLanguage": "zh-Hant", "publisher": {"@id": f"{BASE}/#org"}},
    ]


def article_page(art, cat_key, slug, related=None):
    cat_name, cat_slug, _ = CATS[cat_key]
    desc = html.escape(art["meta_desc"], quote=True)
    title = html.escape(art["seo_title"], quote=True)
    url = f"{BASE}/posts/{slug}.html"
    schema = ldjson({
        "@context": "https://schema.org",
        "@graph": site_node() + [{
            "@type": "BlogPosting",
            "@id": f"{url}#article",
            "headline": art["h1"],
            "description": art["meta_desc"],
            "url": url,
            "datePublished": PUB_DATE,
            "dateModified": PUB_DATE,
            "inLanguage": "zh-Hant",
            "articleSection": cat_name,
            "isPartOf": {"@id": f"{BASE}/#website"},
            "mainEntityOfPage": {"@type": "WebPage", "@id": url},
            "author": {"@id": f"{BASE}/#org"},
            "publisher": {"@id": f"{BASE}/#org"},
        }],
    })
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | {BRAND}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="{BRAND}">
<meta name="twitter:card" content="summary">
{schema}
{FONTS}
<link rel="stylesheet" href="../assets/style.css">
</head>
<body>
{topbar("../")}
<article><div class="wrap">
  <div class="crumb"><a href="../index.html">首頁</a> › <a href="../{cat_slug}.html">{cat_name}</a></div>
  <span class="pill">{cat_name}</span>
  <h1>{html.escape(art['h1'])}</h1>
  <div class="byline">複利人生實驗室 · 2026 · 投資理財教育</div>
  {art['body']}
  <div class="cta">
    <h3>讓錢開始自動工作</h3>
    <p>追蹤「複利人生實驗室」，{TAGLINE}。</p>
  </div>
  {related_block(related)}
  <p class="disclaimer">本站所有文章僅供投資理財教育與資訊分享，不構成任何投資建議或勸誘。投資有風險，過去績效不代表未來表現，請依自身狀況謹慎評估，必要時諮詢專業顧問。文中標示「聯盟連結」處為聯盟行銷連結，若您透過連結申辦或訂閱，本站可能獲得推薦獎金，但不會增加您的任何費用。</p>
</div></article>
{footer("../")}
{CF_ANALYTICS}
</body>
</html>
"""


def card(art, slug, prefix="posts/"):
    cat_name = art["_cat_name"]
    desc = html.escape(art["meta_desc"][:62])
    return (f'<a class="card" href="{prefix}{slug}.html">'
            f'<div class="ct">{cat_name}</div>'
            f'<div class="ch">{html.escape(art["h1"])}</div>'
            f'<div class="cd">{desc}…</div></a>')


def page_shell(title, desc, body, prefix="", canonical="", schema=""):
    canon = f'<link rel="canonical" href="{canonical}">\n<meta property="og:url" content="{canonical}">\n' if canonical else ""
    schema = (schema + "\n") if schema else ""
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc, quote=True)}">
{canon}<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc, quote=True)}">
<meta property="og:site_name" content="{BRAND}">
{schema}{FONTS}
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
{topbar(prefix)}
{body}
{footer(prefix)}
{CF_ANALYTICS}
</body>
</html>
"""


def main():
    # 收集文章（先全部讀進來，才能算同分類的延伸閱讀）
    by_cat = {c: [] for c in CAT_ORDER}
    for cat_key in CAT_ORDER:
        folder = SRC / cat_key
        for md in sorted(folder.glob("*.md")):
            slug = SLUGS.get(md.stem)
            if not slug:
                print(f"  [警告] 無 slug 對應，跳過: {md.stem}")
                continue
            art = parse_md(md)
            art["_cat_name"] = CATS[cat_key][0]
            art["_slug"] = slug
            art["_cat_key"] = cat_key
            by_cat[cat_key].append(art)

    # 生成文章頁（含同分類延伸閱讀 2-3 篇）
    all_arts = []
    total = 0
    for cat_key in CAT_ORDER:
        arts = by_cat[cat_key]
        for i, art in enumerate(arts):
            related = [a for a in arts if a["_slug"] != art["_slug"]][:3]
            slug = art["_slug"]
            (ROOT / "posts" / f"{slug}.html").write_text(
                article_page(art, cat_key, slug, related), encoding="utf-8")
            all_arts.append(art)
            total += 1
    print(f"  → 已生成 {total} 篇文章頁")

    # 首頁
    secs = []
    for cat_key in CAT_ORDER:
        name, cslug, sub = CATS[cat_key]
        cards = "".join(card(a, a["_slug"]) for a in by_cat[cat_key])
        secs.append(f'<div class="section-title"><span class="bar"></span>{name}'
                    f'<a href="{cslug}.html" style="font-size:14px;font-weight:500;margin-left:auto">看全部 →</a></div>'
                    f'<div class="section-sub">{sub}</div><div class="cards">{cards}</div>')
    hero = (f'<div class="hero"><div class="wrap"><h1>{BRAND}</h1>'
            f'<p>{SITE_DESC}</p></div></div>')
    home_body = hero + '<div class="wrap">' + "".join(secs) + '</div>'
    home_schema = ldjson({
        "@context": "https://schema.org",
        "@graph": site_node() + [{
            "@type": "WebPage", "@id": f"{BASE}/#webpage", "url": f"{BASE}/",
            "name": f"{BRAND}｜{TAGLINE}", "description": SITE_DESC,
            "inLanguage": "zh-Hant",
            "isPartOf": {"@id": f"{BASE}/#website"},
            "about": {"@id": f"{BASE}/#org"},
        }],
    })
    (ROOT / "index.html").write_text(
        page_shell(f"{BRAND}｜{TAGLINE}", SITE_DESC, home_body, prefix="",
                   canonical=f"{BASE}/", schema=home_schema),
        encoding="utf-8")

    # 5 個分類索引頁
    for cat_key in CAT_ORDER:
        name, cslug, sub = CATS[cat_key]
        cards = "".join(card(a, a["_slug"]) for a in by_cat[cat_key])
        hero = (f'<div class="hero"><div class="wrap"><h1>{name}</h1><p>{sub}</p></div></div>')
        body = hero + f'<div class="wrap"><div class="cards" style="margin-top:36px">{cards}</div></div>'
        cat_schema = ldjson({
            "@context": "https://schema.org",
            "@graph": site_node() + [{
                "@type": "CollectionPage", "@id": f"{BASE}/{cslug}.html#page",
                "url": f"{BASE}/{cslug}.html",
                "name": f"{name}｜{BRAND}", "description": f"{name} — {sub}。{BRAND}",
                "inLanguage": "zh-Hant",
                "isPartOf": {"@id": f"{BASE}/#website"},
            }],
        })
        (ROOT / f"{cslug}.html").write_text(
            page_shell(f"{name}｜{BRAND}", f"{name} — {sub}。{BRAND}", body, prefix="",
                       canonical=f"{BASE}/{cslug}.html", schema=cat_schema),
            encoding="utf-8")
    print(f"  → 已生成 首頁 + {len(CAT_ORDER)} 個分類索引頁")

    # sitemap.xml — 首頁 + 分類頁 + 全部文章頁
    urls = [f"{BASE}/"]
    urls += [f"{BASE}/{CATS[c][1]}.html" for c in CAT_ORDER]
    urls += [f"{BASE}/posts/{a['_slug']}.html" for a in all_arts]
    today = PUB_DATE
    entries = "\n".join(
        f"  <url><loc>{u}</loc><lastmod>{today}</lastmod>"
        f"<changefreq>weekly</changefreq><priority>{'1.0' if u.endswith('/') else '0.8'}</priority></url>"
        for u in urls)
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               f"{entries}\n</urlset>\n")
    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    # robots.txt
    robots = ("User-agent: *\n"
              "Allow: /\n\n"
              f"Sitemap: {BASE}/sitemap.xml\n")
    (ROOT / "robots.txt").write_text(robots, encoding="utf-8")
    print(f"  → 已生成 sitemap.xml（{len(urls)} 個 URL）+ robots.txt")
    print("完成。")


if __name__ == "__main__":
    main()
