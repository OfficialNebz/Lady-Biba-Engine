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
        .stApp { background-color: #050505; color: #E0E0E0; }
        h1, h2, h3 { font-family: 'Cormorant Garamond', serif !important; color: #F0F0F0 !important; }
        p, div, label, input, button, textarea { font-family: 'Montserrat', sans-serif !important; font-weight: 300; }
        .stTextInput > div > div > input { background-color: #0a0a0a; color: #fff; border: 1px solid #333; border-radius: 0px; padding: 12px; }
        div.stButton > button { background-color: #F0F0F0; color: #000; border: none; border-radius: 0px; padding: 0.8rem 2rem; text-transform: uppercase; font-weight: 600; width: 100%; }
        div.stButton > button:hover { background-color: #D4AF37; color: #fff; }
        [data-testid="column"] { padding-right: 20px !important; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        /* DEBUG BOX STYLING */
        .debug-box { font-family: monospace; font-size: 10px; color: #666; border: 1px dashed #333; padding: 10px; margin-top: 10px; }
        </style>
    """, unsafe_allow_html=True)


inject_custom_css()

# --- 3. AUTH & STATE ---
if "results" not in st.session_state: st.session_state.results = None
if "p_name" not in st.session_state: st.session_state.p_name = ""
if "p_desc" not in st.session_state: st.session_state.p_desc = ""  # New: Store Description for Debug
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
        st.markdown(
            '<div style="color:#D4AF37; border:1px solid #D4AF37; padding:5px; text-align:center;">SYSTEM AUTHENTICATED</div>',
            unsafe_allow_html=True)
        if st.button("HARD RESET"):
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

        # 1. Title
        title = soup.find('h1').text.strip() if soup.find('h1') else "Lady Biba Piece"

        # 2. Description (UPGRADED FOR BULLET POINTS)
        desc_text = ""

        # Try finding the specific description block
        product_block = soup.find('div', class_='product-description') or \
                        soup.find('div', class_='rte') or \
                        soup.find('div', {'itemprop': 'description'})

        if product_block:
            # Get paragraphs
            ps = [p.get_text(strip=True) for p in product_block.find_all('p')]
            # Get bullet points (The Barrel Pants Fix)
            lis = [li.get_text(strip=True) for li in product_block.find_all('li')]

            # Combine them
            full_text = " ".join(ps) + " " + " ".join(lis)
            desc_text = full_text[:1500]  # Limit char count
        else:
            # Fallback: Scrape all paragraphs in the body
            ps = soup.find_all('p')
            desc_text = " ".join([p.text.strip() for p in ps[:5]])

        if not desc_text: desc_text = "No textual description found. Analyze visual data only."

        # 3. Images
        urls = [img.get('src') for img in soup.find_all('img') if img.get('src')]
        urls = ['https:' + u if u.startswith('//') else u for u in urls]
        valid_urls = [u for u in urls if 'logo' not in u.lower() and 'icon' not in u.lower()]

        return title, desc_text, get_valid_images(valid_urls)
    except Exception as e:
        return None, f"Scrape Error: {e}", []


def generate_campaign(product_name, description, images, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')

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

    INPUT DATA:
    Product: {product_name}
    Specs/Description: {description}

    TASK:
    1. Select TOP 3 Personas from the MASTER LIST below that fit this item.
    2. Write 3 Captions (one per persona) + 1 Hybrid Strategy.

    MASTER LIST:
    {persona_matrix}

    RULES:
    - Use the Description facts (e.g., if it says "Denim", sell Denim. If it says "Silk", sell Silk).
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
        return [{"persona": "Error", "post": f"AI Error: {str(e)}"}]


def save_to_notion(p_name, post, persona, token, db_id):
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
    data = {
        "parent": {"database_id": db_id},
        "properties": {
            "Product Name": {"title": [{"text": {"content": p_name}}]},
            "Persona": {"rich_text": [{"text": {"content": persona}}]},
            "Generated Post": {"rich_text": [{"text": {"content": post[:2000]}}]}
        }
    }
    try:
        response = requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(data))
        if response.status_code != 200: return False, response.text
        return True, "Success"
    except Exception as e:
        return False, str(e)


# --- 5. UI FLOW ---
st.title("LADY BIBA / INTELLIGENCE")


# CALLBACK FUNCTION TO CLEAR STATE
def clear_state():
    st.session_state.results = None
    st.session_state.p_name = ""
    st.session_state.imgs = []
    st.session_state.p_desc = ""


col1, col2 = st.columns([4, 1])
with col1:
    # ADDED on_change TO AUTO-WIPE WHEN URL CHANGES
    url_input = st.text_input("Product URL", placeholder="Paste Link...", label_visibility="collapsed",
                              on_change=clear_state)
with col2:
    run_btn = st.button("GENERATE ASSETS")

if run_btn and url_input:
    clean_url = url_input.split('?')[0]

    if not api_key:
        st.error("MISSING API KEY.")
    else:
        with st.spinner("Extracting DNA..."):
            p_name, p_desc, valid_imgs = scrape_website(clean_url)

            if p_name:
                st.session_state.p_name = p_name
                st.session_state.p_desc = p_desc
                st.session_state.imgs = valid_imgs
                st.session_state.results = generate_campaign(p_name, p_desc, valid_imgs, api_key)
            else:
                st.error("Scraping Failed.")

# --- RESULTS DASHBOARD ---
if st.session_state.results:
    st.divider()
    st.subheader(f"CAMPAIGN: {st.session_state.p_name.upper()}")

    # 1. IMAGES
    if st.session_state.imgs:
        cols = st.columns(len(st.session_state.imgs), gap="large")
        for i, col in enumerate(cols):
            with col: st.image(st.session_state.imgs[i], use_container_width=True)

    # 2. THE TRUTH BOX (Inspector)
    with st.expander("🕵️ INSPECTOR: What did the AI actually read?"):
        st.markdown(f"**Scraped Text:**")
        st.caption(st.session_state.p_desc)
        if "No textual description" in st.session_state.p_desc:
            st.warning("⚠️ Warning: No description text found. AI is guessing based on images only.")
        else:
            st.success("✅ Text Data Acquired.")

    st.divider()

    # 3. GLOBAL EXPORT
    if st.button("💾 EXPORT ALL TO NOTION", type="primary"):
        success = 0
        prog = st.progress(0)
        for i, item in enumerate(st.session_state.results):
            s, m = save_to_notion(st.session_state.p_name, item['post'], item['persona'], notion_token, notion_db_id)
            if s:
                success += 1
            else:
                st.error(f"Failed {item['persona']}: {m}")
            prog.progress((i + 1) / len(st.session_state.results))
        if success == len(st.session_state.results): st.success("Database Updated.")

    # 4. CARDS
    for i, item in enumerate(st.session_state.results):
        st.markdown(f"### {item['persona']}")
        edited = st.text_area("Caption", value=item['post'], height=150, key=f"edit_{i}", label_visibility="collapsed")

        if st.button(f"Export Only This", key=f"save_{i}"):
            s, m = save_to_notion(st.session_state.p_name, edited, item['persona'], notion_token, notion_db_id)
            if s:
                st.toast("Saved!")
            else:
                st.error(f"Error: {m}")
        st.markdown("---")