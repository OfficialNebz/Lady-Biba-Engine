import streamlit as st
import os
import requests
import json
import re
from bs4 import BeautifulSoup
import google.generativeai as genai
from PIL import Image
from io import BytesIO

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Lady Biba Client",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# --- 2. LUXURY VISUALS ---
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Montserrat:wght@300;400&display=swap');

        /* DARK MODE RESET */
        .stApp { background-color: #050505; color: #E0E0E0; }

        /* TYPOGRAPHY */
        h1, h2, h3 { font-family: 'Cormorant Garamond', serif !important; color: #F0F0F0 !important; }
        p, div, label, input, button, textarea { font-family: 'Montserrat', sans-serif !important; font-weight: 300; }

        /* INPUTS */
        .stTextInput > div > div > input { background-color: #0a0a0a; color: #fff; border: 1px solid #333; border-radius: 0px; padding: 12px; }

        /* BUTTONS */
        div.stButton > button { background-color: #F0F0F0; color: #000; border: none; border-radius: 0px; padding: 0.8rem 2rem; text-transform: uppercase; font-weight: 600; width: 100%; }
        div.stButton > button:hover { background-color: #D4AF37; color: #fff; }

        /* CUSTOM AUTH BADGE */
        .auth-badge {
            background-color: #D4AF37;
            color: #000000;
            padding: 10px;
            text-align: center;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 12px;
            margin-bottom: 20px;
            border: 1px solid #AA8C2C;
        }

        /* IMAGES & SPACING */
        [data-testid="column"] { padding-right: 20px !important; }

        /* HIDE JUNK */
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)


inject_custom_css()

# --- 3. AUTH & STATE ---
if "results" not in st.session_state: st.session_state.results = None
if "p_name" not in st.session_state: st.session_state.p_name = ""
if "imgs" not in st.session_state: st.session_state.imgs = []

api_key = None
notion_token = None
notion_db_id = None

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    notion_token = st.secrets["NOTION_TOKEN"]
    notion_db_id = st.secrets["NOTION_DB_ID"]

with st.sidebar:
    st.header("Atelier Settings")

    if not api_key:
        api_key = st.text_input("API Key", type="password")
        notion_token = st.text_input("Notion Token", type="password")
        notion_db_id = st.text_input("Database ID")
    else:
        # THE GOLD BADGE YOU REQUESTED
        st.markdown('<div class="auth-badge">SYSTEM AUTHENTICATED</div>', unsafe_allow_html=True)

        if st.button("Reset Session"):
            st.session_state.clear()
            st.rerun()


# --- 4. ENGINE ---
def get_valid_images(url_list):
    valid_images = []
    seen = set()
    for url in url_list:
        if url in seen: continue
        try:
            response = requests.get(url, timeout=3)
            img = Image.open(BytesIO(response.content))
            w, h = img.size
            # Filter: Must be bigger than 300px and not a banner
            if w > 300 and h > 300 and 0.5 < (w / h) < 1.5:
                valid_images.append(img)
                seen.add(url)
            if len(valid_images) >= 3: break
        except:
            continue
    return valid_images


def scrape_website(target_url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(target_url, headers=headers)
        soup = BeautifulSoup(r.content, 'html.parser')

        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else "Lady Biba Piece"

        descs = soup.find_all('div', class_='product-description') or soup.find_all('div', class_='rte')
        desc_text = descs[0].get_text(strip=True)[:1000] if descs else "Luxury fashion piece."

        urls = [img.get('src') for img in soup.find_all('img') if img.get('src')]
        urls = ['https:' + u if u.startswith('//') else u for u in urls]
        valid_urls = [u for u in urls if 'logo' not in u.lower() and 'icon' not in u.lower()]

        return title, desc_text, get_valid_images(valid_urls)
    except:
        return None, None, []


def generate_campaign(product_name, description, images, key):
    genai.configure(api_key=key)

    # REVERTING TO STABLE MODEL NAME
    model = genai.GenerativeModel('gemini-flash-latest')

    persona_matrix = """
    1. The Tech-Bro VC (Tone: Lethal Precision | Pain: 'Tailor Story' Trauma)
    2. The VI High-Court Lawyer (Tone: British Vogue Sophistication | Pain: 'Next Week Friday' Lies)
    3. The Diaspora Investor (Tone: 'Old Money' Security | Pain: Invisible in Grey Suits)
    4. The Eco-Conscious Gen Z (Tone: Aggressive Hype | Pain: Decision Fatigue)
    5. The Oil & Gas Director (Tone: Understated Luxury | Pain: Time-Wealth Depletion)
    6. The Balogun Market 'Oga' (Tone: Lagos 'No-Nonsense' | Pain: Fabric Fading Shame)
    7. The Wedding Guest Pro (Tone: Kinetic Energy | Pain: Heat/Humidity Armor)
    8. The Fintech Founder (Tone: Afro-Futuristic | Pain: Poor Finishing Scars)
    9. The High-Society Matriarch (Tone: Maternal Authority | Pain: Economic Friction)
    10. The Creative Director (Tone: Intellectual Dominance | Pain: 'Fast-Fashion' Fragility)
    11. The Side-Hustle Queen (Tone: Relatable Hustle | Pain: Office TGIF-to-Party Crisis)
    12. The Real Estate Mogul (Tone: Unapologetic Power | Pain: Imposter Syndrome)
    13. The Corporate Librarian (Tone: Quiet Confidence | Pain: The 9AM Boardroom Fear)
    14. The Instagram Influencer (Tone: Viral/Trend-Focused | Pain: 'Sold Out' Anxiety)
    15. The Medical Consultant (Tone: Clinical/Structured | Pain: 24-Hour Style Durability)
    16. The Church 'Sister' Elite (Tone: Pious/Premium | Pain: Modesty vs Style Battle)
    17. The Media Personality (Tone: Electric/Charismatic | Pain: Narrative Inconsistency)
    18. The Event Planner (Tone: Chaos-Control | Pain: Opportunity Cost of Waiting)
    19. The UN/NGO Official (Tone: Diplomatic/Polished | Pain: Cultural Identity Gap)
    20. The Retail Investor (Tone: Analytical/Speculative | Pain: ROI on Self-Presentation)
    """

    prompt = f"""
    Role: Senior Creative Director for Lady Biba.

    Product: {product_name}
    Details: {description}

    TASK:
    1. Select TOP 3 Personas from the MASTER LIST below that fit this item.
    2. Write 3 Captions (one per persona) + 1 Hybrid Strategy.

    MASTER LIST:
    {persona_matrix}

    RULES:
    - No fluff. Speak to the pain point directly.
    - JSON OUTPUT ONLY.

    Structure:
    [
        {{"persona": "Name", "post": "Caption..."}},
        {{"persona": "Name", "post": "Caption..."}},
        {{"persona": "Name", "post": "Caption..."}},
        {{"persona": "Hybrid Strategy", "post": "Caption..."}}
    ]
    """

    payload = [prompt]
    if images: payload.extend(images[:3])

    try:
        response = model.generate_content(payload)
        txt = response.text
        if "```json" in txt:
            txt = txt.split("```json")[1].split("```")[0]
        elif "```" in txt:
            txt = txt.split("```")[1].split("```")[0]
        return json.loads(txt.strip())
    except Exception as e: