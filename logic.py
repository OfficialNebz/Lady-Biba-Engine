import requests
import json
from bs4 import BeautifulSoup
import google.generativeai as genai

# --- GLOBAL CONSTANTS ---
NOTION_API_URL = "https://api.notion.com/v1/pages"


def scrape_website(target_url):
    """
    Tiered scraping strategy: JSON > Meta Tags > HTML Fallback.
    Returns: (title, description_text)
    """
    if "ladybiba.com" not in target_url:
        return None, "❌ ERROR: INVALID DOMAIN. This system is locked to Lady Biba assets only."

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    clean_url = target_url.split('?')[0]
    title = "Lady Biba Piece"
    desc_text = ""

    # --- TIER 1: SHOPIFY JSON API ---
    try:
        json_url = f"{clean_url}.json"
        r = requests.get(json_url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json().get('product', {})
            title = data.get('title', title)
            raw_html = data.get('body_html', "")
            soup = BeautifulSoup(raw_html, 'html.parser')
            desc_text = soup.get_text(separator="\n", strip=True)
            if desc_text: return title, _clean_text(desc_text)
    except Exception:
        pass  # Silently fail to Tier 2

    # --- TIER 2 & 3: SEO & HTML ---
    try:
        r = requests.get(target_url, headers=headers, timeout=10)
        if r.status_code != 200: return None, f"❌ SITE ERROR: {r.status_code}"

        soup = BeautifulSoup(r.content, 'html.parser')
        if soup.find('h1'): title = soup.find('h1').text.strip()

        # Meta Description
        meta_desc = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            content = meta_desc.get('content', '').strip()
            if len(content) > 20: return title, content

        # HTML Fallback
        main_block = soup.find('div', class_='product__description') or \
                     soup.find('div', class_='rte') or \
                     soup.find('div', id='description')
        if main_block:
            desc_text = main_block.get_text(separator="\n", strip=True)
            return title, _clean_text(desc_text)

    except Exception as e:
        return None, f"Scrape Error: {str(e)}"

    return title, "[NO DATA FOUND. The site structure may have changed.]"


def _clean_text(raw_text):
    clean_lines = []
    for line in raw_text.split('\n'):
        upper = line.upper()
        if any(x in upper for x in
               ["UK ", "US ", "BUST", "WAIST", "HIP", "XS", "XL", "DELIVERY", "SHIPPING", "RETURNS"]):
            continue
        if len(line) > 5: clean_lines.append(line)
    return "\n".join(clean_lines[:30])


def generate_campaign(product_name, description, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-flash-latest')

    # FULL LADY BIBA MATRIX
    persona_matrix = """
    1. The Tech-Bro VC (Tone: Lethal Precision)
    2. The VI High-Court Lawyer (Tone: British Vogue Sophistication)
    3. The Diaspora Investor (Tone: 'Old Money' Security)
    4. The Eco-Conscious Gen Z (Tone: Aggressive Hype)
    5. The Oil & Gas Director (Tone: Understated Luxury)
    6. The Balogun Market 'Oga' (Tone: Lagos 'No-Nonsense')
    7. The Wedding Guest Pro (Tone: Kinetic Energy)
    8. The Fintech Founder (Tone: Afro-Futuristic)
    9. The High-Society Matriarch (Tone: Maternal Authority)
    10. The Creative Director (Tone: Intellectual Dominance)
    11. The Side-Hustle Queen (Tone: Relatable Hustle)
    12. The Real Estate Mogul (Tone: Unapologetic Power)
    13. The Corporate Librarian (Tone: Quiet Confidence)
    14. The Instagram Influencer (Tone: Viral/Trend-Focused)
    15. The Medical Consultant (Tone: Clinical/Structured)
    16. The Church 'Sister' Elite (Tone: Pious/Premium)
    17. The Media Personality (Tone: Electric/Charismatic)
    18. The Event Planner (Tone: Chaos-Control)
    19. The UN/NGO Official (Tone: Diplomatic/Polished)
    20. The Retail Investor (Tone: Analytical/Speculative)
    """

    prompt = f"""
    Role: Head of Brand Narrative for 'Lady Biba'.
    Product: {product_name}
    Specs: {description}
    TASK: Select TOP 3 Personas. Write 3 Captions + 1 Hybrid Strategy. Each caption should be exactly 80 words.
    MASTER LIST: {persona_matrix}
    CRITICAL RULE: Quote specific fabric/cut details in every caption.
    Output JSON ONLY: [ {{"persona": "Name", "post": "Caption..."}}, ... ]
    """

    try:
        response = model.generate_content(prompt)
        txt = response.text
        if "```json" in txt: txt = txt.split("```json")[1].split("```")[0]
        return json.loads(txt.strip())
    except Exception as e:
        return [{"persona": "Error", "post": f"AI ERROR: {str(e)}"}]


def save_to_notion(p_name, post, persona, token, db_id):
    if not token or not db_id: return False, "Notion Secrets Missing"

    headers = {
        "Authorization": "Bearer " + token.strip(),
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": {"database_id": db_id.strip()},
        "properties": {
            "Product Name": {"title": [{"text": {"content": str(p_name)}}]},
            "Persona": {"rich_text": [{"text": {"content": str(persona)}}]},
            "Generated Post": {"rich_text": [{"text": {"content": str(post)[:2000]}}]}
        }
    }

    try:
        response = requests.post(NOTION_API_URL, headers=headers, data=json.dumps(data), timeout=15)
        if response.status_code == 200:
            return True, "Success"
        elif response.status_code == 401:
            return False, "❌ INVALID TOKEN"
        elif response.status_code == 404:
            return False, "❌ DB NOT FOUND"
        else:
            return False, f"Notion Error {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "⏳ TIMEOUT: Notion slow."
    except requests.exceptions.ConnectionError:
        return False, "🔌 NO INTERNET"
    except Exception as e:
        return False, f"System Error: {str(e)}"