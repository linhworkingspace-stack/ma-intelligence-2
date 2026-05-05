#!/usr/bin/env python3
"""
M&A Financial Intelligence Newsletter
Fetch RSS -> Gemini AI analysis -> HTML report -> Email
"""

import os, json, smtplib, feedparser, requests, re
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

ICT = timezone(timedelta(hours=7))
NOW = datetime.now(ICT)
DATE_STR = NOW.strftime("%d/%m/%Y")
DATE_FILE = NOW.strftime("%Y-%m-%d")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

SOURCES = [
    {"name":"Axios Pro Rata","url":"https://api.axios.com/feed/rss","category":"M&A / PE","lang":"en",
     "keywords":["M&A","merger","acquisition","private equity","PE","VC","deal","buyout","due diligence","IPO","fund","LBO"]},
    {"name":"The Middle Market","url":"https://www.themiddlemarket.com/feed","category":"M&A / PE","lang":"en",
     "keywords":["M&A","merger","acquisition","private equity","PE","middle market","deal","buyout","leverage","sponsor"]},
    {"name":"PitchBook News","url":"https://pitchbook.com/rss/news","category":"M&A / PE","lang":"en",
     "keywords":["M&A","PE","VC","deal","fund","venture","acquisition","private equity","IPO","valuation","exit"]},
    {"name":"Harvard Law Corp Gov","url":"https://corpgov.law.harvard.edu/feed/","category":"Pháp lý / Governance","lang":"en",
     "keywords":["M&A","governance","compliance","due diligence","acquisition","deal","regulation","shareholder","fiduciary","SEC"]},
    {"name":"Thời báo Tài chính VN","url":"https://thoibaotaichinhvietnam.vn/rss/tin-tuc.rss","category":"Tài chính / Thuế","lang":"vi",
     "keywords":["thuế","kế toán","tài chính","chính sách","thông tư","nghị định","doanh nghiệp","đầu tư","ngân sách","M&A","mua bán"]},
    {"name":"Tạp chí KT&KT","url":"https://tapchiketoankiemtoan.vn/feed","category":"Kế toán / Kiểm toán","lang":"vi",
     "keywords":["kế toán","kiểm toán","thuế","thông tư","nghị định","báo cáo tài chính","chuẩn mực","doanh nghiệp","IFRS","VAS"]},
    {"name":"Tạp chí Tài chính DN","url":"https://taichinhdoanhnghiep.net.vn/rss","category":"Tài chính DN","lang":"vi",
     "keywords":["tài chính","doanh nghiệp","thuế","kế toán","đầu tư","M&A","mua bán","sáp nhập","vốn","định giá"]},
    {"name":"VnEconomy","url":"https://vneconomy.vn/rss/home.rss","category":"Kinh tế vĩ mô","lang":"vi",
     "keywords":["FDI","đầu tư","tăng trưởng","GDP","lãi suất","tỷ giá","thị trường","vốn","M&A","mua bán","sáp nhập","chứng khoán","ngân hàng"]},
]

def fetch_articles(sources, max_per_source=10):
    articles = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MAIntelligenceBot/1.0)"}
    for src in sources:
        try:
            resp = requests.get(src["url"], headers=headers, timeout=15)
            feed = feedparser.parse(resp.content)
            count = 0
            for entry in feed.entries:
                if count >= max_per_source:
                    break
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                summary = re.sub(r"<[^>]+>", " ", entry.get("summary", entry.get("description", ""))).strip()[:600]
                if not title or not link:
                    continue
                text_check = (title + " " + summary).lower()
                if not any(k.lower() in text_check for k in src["keywords"]):
                    continue
                articles.append({"source":src["name"],"category":src["category"],"lang":src["lang"],
                                  "title":title,"link":link,"summary":summary})
                count += 1
            print(f"OK {src['name']}: {count} bài")
        except Exception as e:
            print(f"ERR {src['name']}: {e}")
    return articles

def analyze_with_gemini(articles):
    if not GEMINI_API_KEY or not articles:
        return None
    payload = json.dumps([{"id":i,"source":a["source"],"category":a["category"],"lang":a["lang"],
                           "title":a["title"],"summary":a["summary"][:350]} for i,a in enumerate(articles)], ensure_ascii=False)
    prompt = f"""Bạn là chuyên gia phân tích tài chính M&A cấp cao, nền tảng kiểm toán Big4, 10+ năm kinh nghiệm due diligence và định giá doanh nghiệp tại Việt Nam.

Phân tích các bài báo sau. Trả về JSON THUẦN (không markdown, không giải thích):

{{
  "digest": "4-5 câu tổng hợp insight quan trọng nhất hôm nay cho chuyên gia M&A/tài chính tại VN. Thực chất, không chung chung.",
  "alerts": ["tối đa 3 cảnh báo khẩn nếu có sự kiện quan trọng cần xử lý ngay"],
  "articles": [
    {{
      "id": <id gốc>,
      "quality": "cao|trung bình|thấp",
      "relevance": "M&A|Tài chính|Kế toán|Thuế|Vĩ mô|Pháp lý|PE/VC",
      "insight": "1-2 câu insight thực chất cho chuyên gia, không paraphrase tiêu đề",
      "impact": "Rủi ro hoặc cơ hội cụ thể cho công việc due diligence/tư vấn tài chính",
      "score": <1-10>
    }}
  ]
}}

Chỉ trả về bài score >= 5. Lọc bỏ hoàn toàn bài PR/seeding/chung chung.

Bài báo:
{payload}"""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        r = requests.post(url, json={"contents":[{"parts":[{"text":prompt}]}],
                                     "generationConfig":{"temperature":0.3,"maxOutputTokens":8000}}, timeout=60)
        r.raise_for_status()
        raw = re.sub(r"```json|```","", r.json()["candidates"][0]["content"]["parts"][0]["text"]).strip()
        return json.loads(raw)
    except Exception as e:
        print(f"Gemini error: {e}")
        return None

def build_html(articles, analysis):
    analyzed = {}
    alerts, digest = [], ""
    if analysis:
        digest = analysis.get("digest","")
        alerts = analysis.get("alerts",[])
        for item in analysis.get("articles",[]):
            analyzed[item["id"]] = item

    enriched = []
    for i,a in enumerate(articles):
        meta = analyzed.get(i,{})
        if meta.get("quality") == "thấp" or meta.get("score",5) < 5:
            continue
        enriched.append({**a,**meta,"orig_id":i})
    enriched.sort(key=lambda x: x.get("score",5), reverse=True)

    CAT_COLORS = {
        "M&A":("#dbeafe","#2563eb","#1e40af"),
        "PE/VC":("#ede9fe","#7c3aed","#5b21b6"),
        "Pháp lý":("#fef3c7","#d97706","#92400e"),
        "Tài chính":("#d1fae5","#059669","#065f46"),
        "Kế toán":("#e0f2fe","#0284c7","#075985"),
        "Thuế":("#fff7ed","#ea580c","#9a3412"),
        "Vĩ mô":("#fdf4ff","#9333ea","#581c87"),
    }
    def color(cat):
        for k,v in CAT_COLORS.items():
            if k in str(cat): return v
        return ("#f1f5f9","#475569","#1e293b")

    cards = ""
    for a in enriched:
        bg,acc,drk = color(a.get("relevance", a.get("category","")))
        sc = a.get("score",5)
        sc_col = "#16a34a" if sc>=8 else "#d97706" if sc>=6 else "#64748b"
        ql = {"cao":"✦ Giá trị cao","trung bình":"Trung bình"}.get(a.get("quality",""),"")
        flag = "🇬🇧" if a.get("lang")=="en" else "🇻🇳"
        ins = a.get("insight", a.get("summary","")[:200])
        imp = a.get("impact","")
        rel = a.get("relevance", a.get("category",""))
        cards += f"""<div class="card" data-cat="{rel}" style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px 24px;margin-bottom:14px;border-left:4px solid {acc};">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
    <span style="background:{bg};color:{drk};font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;">{rel}</span>
    <span style="font-size:11px;color:#94a3b8;">{flag} {a["source"]}</span>
    {f'<span style="font-size:11px;color:{sc_col};font-weight:600;">· {ql}</span>' if ql else ""}
    <span style="margin-left:auto;font-size:13px;font-weight:700;color:{sc_col};">{sc}/10</span>
  </div>
  <h3 style="margin:0 0 8px;font-size:15px;font-weight:600;color:#0f172a;line-height:1.4;">
    <a href="{a["link"]}" target="_blank" style="color:#0f172a;text-decoration:none;">{a["title"]}</a>
  </h3>
  {f'<p style="margin:0 0 8px;font-size:13px;color:#334155;line-height:1.65;">{ins}</p>' if ins else ""}
  {f'<div style="background:#f8fafc;border-radius:8px;padding:10px 12px;margin-top:8px;font-size:12px;color:#475569;"><strong style="color:#64748b;">Tác động: </strong>{imp}</div>' if imp else ""}
  <div style="margin-top:10px;"><a href="{a["link"]}" target="_blank" style="font-size:12px;color:{acc};font-weight:500;text-decoration:none;">Đọc bài gốc →</a></div>
</div>"""

    alerts_html = ""
    if alerts:
        items = "".join(f'<li style="margin-bottom:6px;font-size:13px;color:#92400e;">{al}</li>' for al in alerts)
        alerts_html = f'<div style="background:#fffbeb;border:1px solid #fbbf24;border-radius:12px;padding:16px 20px;margin-bottom:20px;"><div style="font-size:11px;font-weight:700;color:#b45309;letter-spacing:.5px;margin-bottom:8px;">⚡ CẦN CHÚ Ý HÔM NAY</div><ul style="margin:0;padding-left:16px;">{items}</ul></div>'

    digest_html = ""
    if digest:
        digest_html = f'<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:12px;padding:20px 24px;margin-bottom:20px;"><div style="font-size:11px;font-weight:700;color:#0369a1;letter-spacing:.5px;margin-bottom:10px;">📋 DIGEST HÔM NAY · AI SUMMARY</div><p style="margin:0;font-size:14px;color:#0c4a6e;line-height:1.75;">{digest}</p></div>'

    n = len(enriched)
    ns = len(set(a["source"] for a in enriched))
    na = len(alerts)

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>M&A Intelligence · {DATE_STR}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f1f5f9;color:#0f172a}}
.wrap{{max-width:720px;margin:0 auto;padding:0 16px 48px}}
.pill{{display:inline-block;padding:6px 16px;border-radius:20px;font-size:12px;font-weight:500;cursor:pointer;border:1px solid #e2e8f0;background:#fff;color:#475569;transition:.15s}}
.pill.active{{background:#0f172a;color:#fff;border-color:#0f172a}}
.pill:hover{{border-color:#94a3b8}}
@media(max-width:600px){{.stats{{gap:16px!important}}.stat-n{{font-size:20px!important}}}}
</style>
</head>
<body>
<div class="wrap">

<div style="background:linear-gradient(135deg,#0f172a 0%,#1a3a5c 100%);border-radius:0 0 20px 20px;padding:32px 28px 28px;margin-bottom:24px;">
  <div style="font-size:10px;font-weight:700;color:#64748b;letter-spacing:2px;margin-bottom:10px;">M&A FINANCIAL INTELLIGENCE · I-GLOCAL HCM</div>
  <h1 style="font-size:26px;font-weight:700;color:#fff;margin-bottom:6px;">Báo cáo {DATE_STR}</h1>
  <p style="font-size:13px;color:#94a3b8;margin-bottom:20px;">M&A · Due Diligence · Tài chính · Kế toán · Thuế · Kinh tế vĩ mô</p>
  <div class="stats" style="display:flex;gap:28px;flex-wrap:wrap;">
    <div><div class="stat-n" style="font-size:24px;font-weight:700;color:#38bdf8;">{n}</div><div style="font-size:11px;color:#64748b;margin-top:2px;">Bài phân tích</div></div>
    <div><div class="stat-n" style="font-size:24px;font-weight:700;color:#f59e0b;">{na}</div><div style="font-size:11px;color:#64748b;margin-top:2px;">Cảnh báo</div></div>
    <div><div class="stat-n" style="font-size:24px;font-weight:700;color:#34d399;">{ns}</div><div style="font-size:11px;color:#64748b;margin-top:2px;">Nguồn tin</div></div>
  </div>
</div>

<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px;" id="pills">
  <span class="pill active" onclick="filter('all',this)">Tất cả ({n})</span>
  <span class="pill" onclick="filter('M&A',this)">M&A / PE</span>
  <span class="pill" onclick="filter('Tài chính',this)">Tài chính</span>
  <span class="pill" onclick="filter('Kế toán',this)">Kế toán</span>
  <span class="pill" onclick="filter('Thuế',this)">Thuế</span>
  <span class="pill" onclick="filter('Vĩ mô',this)">Vĩ mô</span>
  <span class="pill" onclick="filter('Pháp lý',this)">Pháp lý</span>
</div>

{alerts_html}
{digest_html}

<div id="cards">{cards}</div>

<div style="border-top:1px solid #e2e8f0;padding-top:20px;margin-top:32px;text-align:center;">
  <p style="font-size:12px;color:#94a3b8;">Cập nhật {NOW.strftime('%H:%M')} ICT · Phân tích bởi Gemini AI · Dành riêng cho Linh Nguyễn · I-Glocal HCM</p>
</div>
</div>

<script>
function filter(cat,el){{
  document.querySelectorAll('.pill').forEach(p=>p.classList.remove('active'));
  el.classList.add('active');
  document.querySelectorAll('#cards .card').forEach(c=>{{
    c.style.display=(cat==='all'||c.dataset.cat.includes(cat))?'':'none';
  }});
}}
</script>
</body>
</html>"""

def send_email(report_url):
    ef = os.environ.get("EMAIL_FROM","")
    et = os.environ.get("EMAIL_TO","")
    ep = os.environ.get("EMAIL_PASSWORD","")
    if not all([ef,et,ep]):
        print("Email credentials missing, skip")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 M&A Intelligence · {DATE_STR}"
    msg["From"] = f"M&A Intelligence <{ef}>"
    msg["To"] = et
    msg.attach(MIMEText(f"M&A Intelligence {DATE_STR}\n{report_url}","plain","utf-8"))
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,sans-serif;background:#f1f5f9;padding:32px 16px;">
<div style="max-width:480px;margin:0 auto;background:#fff;border-radius:16px;padding:32px;border:1px solid #e2e8f0;">
  <div style="font-size:10px;font-weight:700;color:#94a3b8;letter-spacing:2px;margin-bottom:10px;">M&A FINANCIAL INTELLIGENCE</div>
  <h1 style="font-size:22px;font-weight:700;color:#0f172a;margin-bottom:8px;">Báo cáo hôm nay đã sẵn sàng</h1>
  <p style="font-size:14px;color:#475569;line-height:1.65;margin-bottom:24px;">Digest hằng ngày của bạn về M&A, Due Diligence, Tài chính, Kế toán và Thuế vừa được cập nhật.</p>
  <a href="{report_url}" style="display:block;background:#0f172a;color:#fff;text-align:center;padding:14px;border-radius:10px;font-size:15px;font-weight:600;text-decoration:none;margin-bottom:20px;">📖 Đọc báo cáo đầy đủ →</a>
  <p style="font-size:11px;color:#94a3b8;text-align:center;">{NOW.strftime('%H:%M')} ICT · Gemini AI · I-Glocal HCM</p>
</div>
</body></html>"""
    msg.attach(MIMEText(html,"html","utf-8"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
            s.login(ef,ep)
            s.sendmail(ef,et,msg.as_string())
        print(f"Email sent to {et}")
    except Exception as e:
        print(f"Email error: {e}")

def main():
    print(f"=== M&A Intelligence {DATE_STR} ===")
    articles = fetch_articles(SOURCES)
    print(f"Total: {len(articles)} articles")
    analysis = analyze_with_gemini(articles)
    html = build_html(articles, analysis)
    out = Path("docs")
    out.mkdir(exist_ok=True)
    (out/"index.html").write_text(html, encoding="utf-8")
    (out/f"{DATE_FILE}.html").write_text(html, encoding="utf-8")
    print("Saved docs/index.html")
    repo = os.environ.get("GITHUB_REPOSITORY","user/repo")
    user,name = repo.split("/")[0], repo.split("/")[-1]
    send_email(f"https://{user}.github.io/{name}/")
    print("=== Done ===")

if __name__ == "__main__":
    main()
