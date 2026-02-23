import anthropic
import requests
import datetime
import os
import re

# ── Config ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
RESEND_API_KEY    = os.environ["RESEND_API_KEY"]
TO_EMAIL          = os.environ["TO_EMAIL"]
FROM_EMAIL        = os.environ["FROM_EMAIL"]
# ─────────────────────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body { margin: 0; padding: 0; background: #f4f4f4; font-family: Georgia, serif; }
  .wrapper { max-width: 600px; margin: 0 auto; background: #ffffff; }
  .header { background: #111111; color: #ffffff; padding: 32px 40px 24px; }
  .header-label { font-family: Arial, sans-serif; font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: #888888; margin-bottom: 10px; }
  .header h1 { margin: 0 0 8px 0; font-size: 26px; font-weight: bold; line-height: 1.2; }
  .header .subline { font-family: Arial, sans-serif; font-size: 13px; color: #aaaaaa; }
  .body { padding: 32px 40px; }
  .section-label { font-family: Arial, sans-serif; font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: #e05c2a; margin-bottom: 12px; margin-top: 32px; }
  .lead-headline { font-size: 22px; font-weight: bold; margin: 0 0 12px 0; line-height: 1.3; }
  .lead-body { font-size: 15px; line-height: 1.7; color: #333333; margin-bottom: 12px; }
  .source-link { font-family: Arial, sans-serif; font-size: 12px; }
  .source-link a { color: #e05c2a; text-decoration: none; }
  .divider { border: none; border-top: 1px solid #eeeeee; margin: 28px 0; }
  .story { margin-bottom: 24px; }
  .story h3 { font-size: 17px; font-weight: bold; margin: 0 0 8px 0; line-height: 1.3; }
  .story p { font-size: 14px; line-height: 1.7; color: #444444; margin: 0 0 8px 0; }
  .story .src { font-family: Arial, sans-serif; font-size: 12px; }
  .story .src a { color: #e05c2a; text-decoration: none; }
  .focus-box { background: #111111; color: #ffffff; padding: 24px 28px; margin: 28px 0; }
  .focus-box .focus-label { font-family: Arial, sans-serif; font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: #e05c2a; margin-bottom: 16px; }
  .focus-box ul { margin: 0; padding-left: 18px; }
  .focus-box li { font-size: 14px; line-height: 1.7; margin-bottom: 10px; color: #dddddd; }
  .citations { border-top: 1px solid #eeeeee; padding-top: 20px; margin-top: 28px; }
  .citations h4 { font-family: Arial, sans-serif; font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: #999999; margin-bottom: 12px; }
  .citations ol { margin: 0; padding-left: 18px; }
  .citations li { font-family: Arial, sans-serif; font-size: 12px; color: #999999; margin-bottom: 6px; }
  .citations li a { color: #999999; }
  .footer { background: #f4f4f4; padding: 20px 40px; font-family: Arial, sans-serif; font-size: 11px; color: #aaaaaa; text-align: center; }
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <div class="header-label">AI Prototyping Weekly</div>
    <h1>{{HEADER_TITLE}}</h1>
    <div class="subline">For builders shipping AI-powered products &middot; {{DATE}}</div>
  </div>
  <div class="body">
    {{CONTENT}}
  </div>
  <div class="footer">You're receiving this because you set it up. Built with Claude + GitHub Actions.</div>
</div>
</body>
</html>"""

def generate_digest() -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    today  = datetime.date.today().strftime("%B %d, %Y")

    prompt = f"""Today is {today} (Friday). You are an expert AI research analyst covering 
the AI prototyping ecosystem for practitioners who build AI-powered products.

Search the web and produce a cited weekly digest of the most important AI prototyping 
news from the past 7 days. Focus on what directly affects someone building AI-powered 
product prototypes: new model releases & APIs, developer tools & SDKs, prompt engineering 
breakthroughs, multimodal capabilities, agent frameworks, open-source releases, pricing 
changes, performance benchmarks, and UX patterns in AI interfaces.

Return ONLY a JSON object with this exact structure (no markdown, no backticks, just raw JSON):
{{
  "week_range": "Feb 17-23, 2026",
  "lead": {{
    "headline": "headline here",
    "body": "2-3 sentence summary here",
    "source_label": "Site Name",
    "source_url": "https://..."
  }},
  "stories": [
    {{
      "headline": "headline",
      "body": "1-2 sentence summary",
      "source_label": "Site Name",
      "source_url": "https://..."
    }}
  ],
  "focus": [
    "Actionable bullet 1",
    "Actionable bullet 2",
    "Actionable bullet 3"
  ],
  "citations": [
    {{"label": "Article title — Site name", "url": "https://..."}}
  ]
}}

Include 3-4 stories. Use only real URLs from your web search."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )

    full_text = "\n".join(
        block.text for block in response.content if block.type == "text"
    )

    # Strip any accidental markdown fences
    full_text = re.sub(r'```json', '', full_text)
    full_text = re.sub(r'```', '', full_text).strip()

    data = __import__('json').loads(full_text)
    return build_html(data, today)


def build_html(data: dict, today: str) -> str:
    # Build lead story
    content = f"""
    <div class="section-label">🔥 Lead Story</div>
    <div class="lead-headline">{data['lead']['headline']}</div>
    <div class="lead-body">{data['lead']['body']}</div>
    <div class="source-link">🔗 <a href="{data['lead']['source_url']}">{data['lead']['source_label']}</a></div>
    <hr class="divider">
    <div class="section-label">📌 Also This Week</div>
    """

    # Build secondary stories
    for story in data['stories']:
        content += f"""
    <div class="story">
      <h3>{story['headline']}</h3>
      <p>{story['body']}</p>
      <div class="src">🔗 <a href="{story['source_url']}">{story['source_label']}</a></div>
    </div>
        """

    # Build focus box
    focus_items = "\n".join(f"<li>{item}</li>" for item in data['focus'])
    content += f"""
    <div class="focus-box">
      <div class="focus-label">⏱ If You Only Have 30 Minutes</div>
      <ul>{focus_items}</ul>
    </div>
    """

    # Build citations
    cite_items = "\n".join(
        f'<li><a href="{c["url"]}">{c["label"]}</a></li>'
        for c in data['citations']
    )
    content += f"""
    <div class="citations">
      <h4>Sources &amp; Citations</h4>
      <ol>{cite_items}</ol>
    </div>
    """

    html = HTML_TEMPLATE
    html = html.replace("{{HEADER_TITLE}}", f"Week of {data['week_range']}")
    html = html.replace("{{DATE}}", today)
    html = html.replace("{{CONTENT}}", content)
    return html


def send_email(html_body: str):
    today   = datetime.date.today().strftime("%B %d, %Y")
    subject = f"AI Prototyping Weekly — {today}"

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": FROM_EMAIL,
            "to":   [TO_EMAIL],
            "subject": subject,
            "html": html_body,
        },
    )
    response.raise_for_status()
    print(f"Email sent — status {response.status_code}")


if __name__ == "__main__":
    print("Generating digest...")
    digest = generate_digest()
    print("Sending email...")
    send_email(digest)
    print("Done.")
