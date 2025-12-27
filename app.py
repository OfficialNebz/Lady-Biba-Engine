import streamlit as st
import os
import requests
import json
import time
from bs4 import BeautifulSoup
import google.generativeai as genai

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="LADY BIBA / INTELLIGENCE",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- GLOBAL CONSTANTS ---
NOTION_API_URL = "https://api.notion.com/v1/pages".strip()

# --- 2. LUXURY CSS ENGINE (FIXED) ---
st.markdown("""
    <style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Montserrat:wght@200;300;400;600&display=swap');

    /* GLOBAL RESET - SAFE VERSION */
    .stApp {
        background-color: #050505;
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Apply fonts to text only, protecting icons */
    h1, h2, h3, h4, h5, h6, p, div, span, button, input, label, textarea {
        font-family: 'Montserrat', sans-serif;
    }

    /* HEADINGS */
    h1, h2, h3, h4 { 
        font-family: 'Cormorant Garamond', serif !important; 
        letter-spacing: 1px; 
        color: #F0F0F0; 
    }

    /* AUTH SCREEN CARD */
    .auth-card {
        background: rgba(20, 20, 20, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid #D4AF37;
        padding: 50px;
        text-align: center;
        border-radius: 0px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }

    /* BUTTONS */
    div.stButton > button {
        width: 100%;
        background-color: transparent;
        color: #D4AF37;
        border: 1px solid #D4AF37;
        padding: 12px 24px;
        font-family: 'Montserrat', sans-serif;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 2px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        border-radius: 0px;
    }

    div.stButton > button:hover {
        background-color: #D4AF37;
        color: #050505;
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 10px 20px rgba(212, 175, 55, 0.2);
    }

    div.stButton > button:active { transform: scale(0.98); }

    /* INPUT FIELDS */
    div[data-baseweb="input"] > div, textarea {
        background-color: #0a0a0a !important;
        border: 1px solid #333 !important;
        color: #D4AF37 !important;
        border-radius: 0px;
    }

    /* EXPANDER STYLING */
    .streamlit-expanderHeader {
        background-color: #111 !important;
        color: #D4AF37 !important;
        border: 1px solid #333;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #080808;
        border-right: 1px solid #222;
    }

    /* HIDE JUNK */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION & SECRETS ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "results" not in st.session_state: st.session_state.results = None
if "p_name" not in st.session_state: st.session_state.p_name = ""
if "gen_id" not in st.session_state: st.session_state.gen_id = 0

api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else None
notion_token = st.secrets.get("NOTION_TOKEN")
notion_db_id = st.secrets.get("NOTION_DB_ID")


# --- 4. AUTH LOGIC ---
def login_screen():
    st.markdown("""
        <style>
        .stApp {
            background-image: url("https://images.unsplash.com/photo-1550614000-4b9519e02d48?q=80&w=2070&auto=format&fit=crop");
            background-size: cover;
            background-position: center;
        }
        .stApp::before {
            content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.7); backdrop-filter: blur(5px); z-index: -1;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="auth-card">', unsafe_allow_html=True)
            st.markdown("<h1 style='text-align: center; margin:0;'>LADY BIBA</h1>", unsafe_allow_html=True)
            st.markdown(
                "<p style='text-align: center; font-size: 10px; letter-spacing: 3px; color: #aaa; margin-bottom: 30px;'>INTELLIGENCE ACCESS</p>",
                unsafe_allow_html=True)

            password = st.text_input("PASSWORD", type="password", label_visibility="collapsed", placeholder="ENTER KEY")

            if st.button("UNLOCK SYSTEM"):
                if password == "neb123":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("⚠️ ACCESS DENIED")
            st.markdown('</div>', unsafe_allow_html=True)


if not st.session_state.authenticated:
    login_screen()
    st.stop()

# =========================================================
# 🏛️ THE MAIN SYSTEM
# =========================================================

with st.sidebar:
    st.markdown("### COMMAND CENTER")
    st.caption("Lady Biba / Internal Tool v2.7 (Stable)")
    st.markdown("---")
    st.success("🟢 SYSTEM ONLINE")
    if st.button("🔄 FORCE RESET"):
        st.session_state.clear()
        st.rerun()


# --- 5. ROBUST ENGINE FUNCTIONS ---

def scrape_website(target_url):
    # GUARD: Strict URL Validation
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
    except:
        pass

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

    url = NOTION_API_URL.strip()
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
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=15)
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


# --- 6. UI LAYOUT ---
st.title("LADY BIBA / INTELLIGENCE")

with st.expander("📖 SYSTEM MANUAL (CLICK TO OPEN)"):
    st.markdown("### OPERATIONAL GUIDE")
    st.markdown("---")

    # STEP 1
    c1, c2 = st.columns([0.8, 2])
    with c1:
        st.markdown("**STEP 1: SOURCE**")
        st.caption("Locate the target.")
        st.markdown("Go to the Lady Biba site. Open a single product page.\n*URL Structure:* `.../products/name`")
    with c2:
        st.image("Screenshot (449).png", use_container_width=True)

    st.markdown("---")

    # STEP 2
    c3, c4 = st.columns([0.8, 2])
    with c3:
        st.markdown("**STEP 2: ACQUIRE**")
        st.caption("Secure the asset link.")
        st.markdown("Copy the URL directly from your browser's address bar.")
    with c4:
        st.image("Screenshot (450).png", use_container_width=True)

    st.markdown("---")

    # STEP 3
    c5, c6 = st.columns([0.8, 2])
    with c5:
        st.markdown("**STEP 3: INJECT**")
        st.caption("Run the intelligence.")
        st.markdown("Paste into the terminal below and execute 'Generate Assets'.")
    with c6:
        st.image("Screenshot (452).png", use_container_width=True)

    st.markdown("---")
    st.info("💡 TIP: You can edit the generated text directly in the dashboard before exporting.")

# INPUT SECTION
url_input = st.text_input("Product URL", placeholder="Paste Lady Biba URL...")

if st.button("GENERATE ASSETS"):
    if not api_key:
        st.error("API Key Missing.")
    elif not url_input:
        st.error("Paste a URL first.")
    else:
        with st.spinner("Analyzing Construction..."):
            st.session_state.gen_id += 1
            p_name, p_desc = scrape_website(url_input)
            if p_name is None:
                st.error(p_desc)
            else:
                st.session_state.p_name = p_name
                st.session_state.results = generate_campaign(p_name, p_desc, api_key)

# RESULTS SECTION
if st.session_state.results:
    st.divider()
    st.subheader(st.session_state.p_name.upper())

    if st.button("💾 EXPORT ALL ASSETS", type="primary", use_container_width=True):
        success_count = 0
        fail_count = 0
        progress_bar = st.progress(0)
        status_text = st.empty()
        current_gen = st.session_state.gen_id

        for i, item in enumerate(st.session_state.results):
            p_val = item.get('persona', item.get('Persona', ''))
            widget_key = f"editor_{i}_{current_gen}"
            original_post = item.get('post', item.get('Post', ''))
            final_post = st.session_state.get(widget_key, original_post)

            if p_val and final_post:
                status_text.text(f"Uploading: {p_val}...")
                s, m = save_to_notion(st.session_state.p_name, final_post, p_val, notion_token, notion_db_id)
                if s:
                    success_count += 1
                else:
                    fail_count += 1
                    st.error(f"Failed to upload {p_val}: {m}")
            progress_bar.progress((i + 1) / len(st.session_state.results))

        status_text.empty()
        if success_count > 0:
            st.success(f"SUCCESS: {success_count} Assets Uploaded.")
            time.sleep(2)
            st.rerun()

    st.markdown("---")
    current_gen = st.session_state.gen_id

    for i, item in enumerate(st.session_state.results):
        persona = item.get('persona', item.get('Persona', 'Unknown'))
        original_post = item.get('post', item.get('Post', ''))

        with st.container():
            col1, col2 = st.columns([0.7, 0.3])
            with col1:
                st.subheader(persona)
                edited_text = st.text_area(
                    label=f"Edit Copy for {persona}",
                    value=original_post,
                    height=250,
                    key=f"editor_{i}_{current_gen}",
                    label_visibility="collapsed"
                )
            with col2:
                st.write("##")
                st.write("##")
                if st.button("💾 SAVE THIS ONE", key=f"btn_{i}_{current_gen}"):
                    with st.spinner("Saving..."):
                        s, m = save_to_notion(st.session_state.p_name, edited_text, persona, notion_token, notion_db_id)
                        if s:
                            st.toast(f"✅ Saved: {persona}")
                        else:
                            st.error(f"Failed: {m}")
        st.divider()