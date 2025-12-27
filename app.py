import streamlit as st
import os
import requests
import json
import re
from bs4 import BeautifulSoup
import google.generativeai as genai
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="LADY BIBA / INTELLIGENCE",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. GLOBAL STYLING (The "Luxury" Upgrade) ---
# CHANGED: Added extensive CSS for fonts, button animations, and the glassmorphism auth screen.
st.markdown("""
    <style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,400&family=Montserrat:wght@200;300;400;600&display=swap');

    /* GLOBAL RESET */
    * { font-family: 'Montserrat', sans-serif; }
    h1, h2, h3, h4, h5, h6 { font-family: 'Cormorant Garamond', serif !important; letter-spacing: 1px; }

    /* BACKGROUND */
    .stApp {
        background-color: #050505;
        color: #E0E0E0;
    }

    /* BUTTON ANIMATIONS (FIXED: "Disgusting" static buttons removed) */
    div.stButton > button {
        width: 100%;
        background-color: #1a1a1a;
        color: #D4AF37; /* Gold */
        border: 1px solid #D4AF37;
        padding: 15px 20px;
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        border-radius: 0px; /* Sharp edges for luxury */
    }

    div.stButton > button:hover {
        background-color: #D4AF37;
        color: #000;
        transform: translateY(-2px); /* Lift effect */
        box-shadow: 0 10px 20px rgba(212, 175, 55, 0.2); /* Gold glow */
    }

    div.stButton > button:active {
        transform: translateY(0px);
    }

    /* INPUT FIELDS */
    .stTextInput > div > div > input {
        background-color: #0a0a0a;
        color: #fff;
        border: 1px solid #333;
        font-family: 'Montserrat', sans-serif;
        text-align: center;
    }

    /* SIDEBAR STYLING */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid #222;
    }

    /* AUTH SCREEN STYLES */
    .auth-bg {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background: linear-gradient(135deg, #000000 0%, #1a0b00 100%); /* Abstract Dark Gradient */
        z-index: 0;
    }
    .auth-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px); /* Glassmorphism */
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(212, 175, 55, 0.3);
        padding: 60px;
        border-radius: 0px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        text-align: center;
        max-width: 500px;
        margin: 15vh auto;
        position: relative;
        z-index: 2;
        animation: fadeIn 1.5s ease-out;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
""", unsafe_allow_html=True)


# --- 3. THE VELVET ROPE (Authentication) ---
# IMPROVED: New "Glassmorphism" UI, removed stock photo, added notifications.
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # Render the Abstract Gradient Background
    st.markdown('<div class="auth-bg"></div>', unsafe_allow_html=True)

    # Render the Glass Modal
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown("<h1 style='color:#D4AF37; margin-bottom:10px;'>ATELIER ACCESS</h1>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size:10px; letter-spacing:2px; color:#888; margin-bottom:30px;'>LADY BIBA INTERNAL INTELLIGENCE</p>",
            unsafe_allow_html=True)

        with st.form("login_form"):
            password = st.text_input("ACCESS KEY", type="password", label_visibility="collapsed",
                                     placeholder="ENTER KEY")
            submit = st.form_submit_button("UNLOCK SYSTEM")

        st.markdown('</div>', unsafe_allow_html=True)

    if submit:
        if password == "neb123":
            st.session_state.authenticated = True
            st.toast("✨ ACCESS GRANTED: Welcome to the Atelier.")
            time.sleep(1)
            st.rerun()
        else:
            st.error("⚠️ ACCESS DENIED: Invalid Credentials.")  # Notification added

    return False


if not check_password():
    st.stop()

# --- 4. SIDEBAR SETTINGS (Requested Item #3) ---
# ADDED: Sidebar with reset functionality and badge.
with st.sidebar:
    st.markdown("<h3 style='color:#D4AF37;'>COMMAND CENTER</h3>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Status:** 🟢 ONLINE")
    st.markdown("**Model:** Gemini 1.5 Pro")
    st.markdown("---")

    if st.button("🔄 FORCE SYSTEM RESET"):
        st.session_state.clear()
        st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption("Lady Biba / Internal Tool v2.0")

# --- 5. STATE MANAGEMENT ---
if "results" not in st.session_state: st.session_state.results = None
if "p_name" not in st.session_state: st.session_state.p_name = ""
if "p_desc" not in st.session_state: st.session_state.p_desc = ""

# --- 6. SECRETS LOADING ---
api_key = None
notion_token = None
notion_db_id = None

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    notion_token = st.secrets.get("NOTION_TOKEN")
    notion_db_id = st.secrets.get("NOTION_DB_ID")
else:
    st.error("🚨 CRITICAL: Secrets file not found.")


# --- 7. ENGINE FUNCTIONS ---

def scrape_website(target_url):
    # ADDED: URL Validation (Requested Item #1)
    if "ladybiba.com" not in target_url:
        return None, "INVALID URL: Access Denied. This system is locked to Lady Biba assets only."

    headers = {'User-Agent': 'Mozilla/5.0'}
    clean_url = target_url.split('?')[0]
    json_url = f"{clean_url}.json"

    title = "Lady Biba Piece"
    desc_text = ""

    # JSON Backdoor Method
    try:
        r = requests.get(json_url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json().get('product', {})
            title = data.get('title', title)
            raw_html = data.get('body_html', "")
            soup = BeautifulSoup(raw_html, 'html.parser')
            raw_text = soup.get_text(separator="\n", strip=True)

            clean_lines = []
            for line in raw_text.split('\n'):
                upper = line.upper()
                if any(x in upper for x in
                       ["UK ", "US ", "BUST", "WAIST", "HIP", "XS", "XL", "DELIVERY", "SHIPPING", "RETURN"]):
                    continue
                if len(line) > 5: clean_lines.append(line)
            desc_text = "\n".join(clean_lines)
    except:
        pass

    # HTML Fallback
    if not desc_text:
        try:
            r = requests.get(target_url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.content, 'html.parser')
            title = soup.find('h1').text.strip() if soup.find('h1') else title
            main_block = soup.find('div', class_='product__description')
            if not main_block: main_block = soup.find('div', class_='rte')
            if main_block:
                desc_text = main_block.get_text(separator="\n", strip=True)
                clean_lines = [l for l in desc_text.split('\n') if "SHIPPING" not in l.upper() and len(l) > 5]
                desc_text = "\n".join(clean_lines[:25])
        except Exception as e:
            return None, f"Scrape Error: {str(e)}"

    if not desc_text: desc_text = "[NO TEXT FOUND.]"
    return title, desc_text


def generate_campaign(product_name, description, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-flash-latest')

    # RESTORED: Full 20 Persona Matrix
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

    # IMPROVED: Explicitly asking for Hybrid Strategy in the structure (Requested Item #2)
    prompt = f"""
    Role: Head of Brand Narrative for 'Lady Biba'.
    Product: {product_name}
    Specs: {description}
    TASK: Select TOP 3 Personas from the MASTER LIST. Write 3 Captions + 1 Hybrid Strategy. Each caption should be exactly 70 words.
    MASTER LIST: {persona_matrix}

    CRITICAL RULE: You MUST quote specific fabric/cut/fit details from the Specs (e.g., 'crepe', 'peplum', 'fitted') in every caption.

    Output JSON ONLY. Follow this EXACT structure: 
    [ 
      {{"persona": "Name", "post": "Caption..."}},
      {{"persona": "Name", "post": "Caption..."}},
      {{"persona": "Name", "post": "Caption..."}},
      {{"persona": "Hybrid Strategy", "post": "Caption..."}}
    ]
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
        # FIXED: Removed the Markdown syntax that caused the crash
        response = requests.post("[https://api.notion.com/v1/pages](https://api.notion.com/v1/pages)", headers=headers,
                                 data=json.dumps(data))
        if response.status_code != 200: return False, response.text
        return True, "Success"
    except Exception as e:
        return False, str(e)


# --- 8. MAIN UI LAYOUT ---
st.title("LADY BIBA / INTELLIGENCE")
url_input = st.text_input("Product URL", placeholder="Paste Link...")

if st.button("GENERATE ASSETS"):
    if not api_key:
        st.error("API Key Missing.")
    elif not url_input:
        st.error("Paste a URL first.")
    else:
        with st.spinner("Analyzing Construction..."):
            p_name, p_desc = scrape_website(url_input)

            # ADDED: Check for URL validation error from scraper
            if "INVALID URL" in p_desc:
                st.error(p_desc)
            else:
                st.session_state.p_name = p_name
                st.session_state.p_desc = p_desc
                st.session_state.results = generate_campaign(p_name, p_desc, api_key)

if st.session_state.results:
    st.divider()
    st.subheader(st.session_state.p_name.upper())

    if st.button("💾 EXPORT CAMPAIGN TO NOTION", type="primary"):
        success_count = 0
        progress_bar = st.progress(0)
        for i, item in enumerate(st.session_state.results):
            p_val = item.get('persona', item.get('Persona', ''))
            post_val = item.get('post', item.get('Post', ''))
            if p_val and post_val:
                s, m = save_to_notion(st.session_state.p_name, post_val, p_val, notion_token, notion_db_id)
                if s: success_count += 1
            progress_bar.progress((i + 1) / len(st.session_state.results))

        if success_count > 0:
            st.success(f"SUCCESS: {success_count} Assets Uploaded.")
            time.sleep(2)
            st.rerun()

    for i, item in enumerate(st.session_state.results):
        p_val = item.get('persona', item.get('Persona', ''))
        post_val = item.get('post', item.get('Post', ''))

        if p_val and post_val:
            st.markdown(f"### {p_val}")
            edited = st.text_area("Caption", value=post_val, height=140, key=f"edit_{i}")
            if st.button(f"Export Only This", key=f"save_{i}"):
                s, m = save_to_notion(st.session_state.p_name, edited, p_val, notion_token, notion_db_id)
                if s:
                    st.toast("Saved!")
                else:
                    st.error(f"Error: {m}")
            st.markdown("---")