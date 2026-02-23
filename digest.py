import anthropic
import requests
import datetime
import os
import re

# ── Config ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
RESEND_API_KEY    = os.environ["RESEND_API_KEY"]
TO_EMAIL          = os.environ["TO_EMAIL"]          # your email address
FROM_EMAIL        = os.environ["FROM_EMAIL"]         # e.g. onboarding@resend.dev
# ─────────────────────────────────────────────────────────────────────────────

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

Format your response as clean HTML for an email (no markdown). Structure it as:

1. A bold header: "AI Prototyping Weekly — Week of [date range]"
2. ONE lead story (2-3 sentences + source link)
3. 3-4 additional stories, each with a headline, 1-2 sentence summary, and source link
4. A "If you only have 30 minutes" section with 3 specific, actionable bullets
5. A citations section with numbered links to all sources

Use only real URLs from your web search. Keep the tone direct and practical — written 
for a builder, not a journalist. Output only the raw HTML with no introduction, 
explanation, or commentary before or after it."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract all text blocks from the response
    full_text = "\n".join(
        block.text for block in response.content if block.type == "text"
    )
    # Strip any markdown code fences Claude might add around the HTML
    full_text = re.sub(r'```html', '', full_text)
    full_text = re.sub(r'```', '', full_text)
    return full_text.strip()


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
