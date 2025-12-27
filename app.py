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
# We define this here to prevent any URL syntax errors later
NOTION_API_URL = "https://api.notion.com/v1/pages"



# --- 2. LUXURY CSS ENGINE ---
st.markdown("""
    <style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Montserrat:wght@200;300;400;600&display=swap');

    /* GLOBAL RESET */
    * { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3, h4 { font-family: 'Cormorant Garamond', serif !important; letter-spacing: 1px; color: #F0F0F0; }

    /* APP BACKGROUND */
    .stApp { background-color: #050505; }

    /* AUTH SCREEN CARD (Glassmorphism) */
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

    /* BUTTONS: TACTILE & ANIMATED */
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

    div.stButton > button:active {
        transform: scale(0.98);
    }

    /* INPUT FIELDS */
    div[data-baseweb="input"] > div {
        background-color: #0a0a0a !important;
        border: 1px solid #333 !important;
        color: #D4AF37 !important;
        text-align: center;
        border-radius: 0px;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #080808;
        border-right: 1px solid #222;
    }

    /* HIDE DEFAULT STREAMLIT JUNK */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION & SECRETS ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "results" not in st.session_state: st.session_state.results = None
if "p_name" not in st.session_state: st.session_state.p_name = ""

api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else None
notion_token = st.secrets.get("NOTION_TOKEN")
notion_db_id = st.secrets.get("NOTION_DB_ID")


# --- 4. THE GATEKEEPER (AUTH LOGIC) ---
def login_screen():
    # BACKGROUND IMAGE ONLY FOR LOGIN
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
        # We simulate a "card" by styling the container
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
# 🏛️ THE MAIN SYSTEM (ONLY RUNS AFTER AUTH)
# =========================================================

# --- 5. SIDEBAR SETTINGS ---
with st.sidebar:
    st.markdown("### COMMAND CENTER")
    st.caption("Lady Biba / Internal Tool v2.5")
    st.markdown("---")
    st.success("🟢 SYSTEM ONLINE")

    if st.button("🔄 FORCE RESET"):
        st.session_state.clear()
        st.rerun()


# --- 6. ENGINE FUNCTIONS ---

def scrape_website(target_url):
    # GUARD: Strict URL Validation
    if "ladybiba.com" not in target_url:
        return None, "❌ ERROR: INVALID DOMAIN. This system is locked to Lady Biba assets only."

    headers = {'User-Agent': 'Mozilla/5.0'}
    clean_url = target_url.split('?')[0]
    json_url = f"{clean_url}.json"

    title = "Lady Biba Piece"
    desc_text = ""

    # Try JSON Backdoor
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
                if any(x in upper for x in ["UK ", "US ", "BUST", "WAIST", "HIP", "XS", "XL", "DELIVERY", "SHIPPING"]):
                    continue
                if len(line) > 5: clean_lines.append(line)
            desc_text = "\n".join(clean_lines)
    except:
        pass

    # Fallback
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
    """

    prompt = f"""
    Role: Head of Brand Narrative for 'Lady Biba'.
    Product: {product_name}
    Specs: {description}
    TASK: Select TOP 3 Personas. Write 3 Captions + 1 Hybrid Strategy. Each caption should be exactly 80 words.
    MASTER LIST: {persona_matrix}

    CRITICAL RULE: Quote specific fabric/cut details (e.g., 'crepe', 'peplum', 'fitted') in every caption.

    Output JSON ONLY. Use this EXACT structure: 
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
        # GLOBAL URL VARIABLE USED HERE
        response = requests.post(NOTION_API_URL, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            return True, "Success"
        elif response.status_code == 401:
            return False, "❌ INVALID NOTION TOKEN. Check secrets.toml."
        else:
            return False, f"Notion Error: {response.text}"
    except Exception as e:
        return False, str(e)


# --- 7. UI LAYOUT ---
st.title("LADY BIBA / INTELLIGENCE")
url_input = st.text_input("Product URL", placeholder="Paste Lady Biba URL...")

if st.button("GENERATE ASSETS"):
    if not api_key:
        st.error("API Key Missing.")
    elif not url_input:
        st.error("Paste a URL first.")
    else:
        with st.spinner("Analyzing Construction..."):
            p_name, p_desc = scrape_website(url_input)

            # GUARD: STOP IF URL IS WRONG
            if p_name is None:  # Scraper returns None on fail
                st.error(p_desc)
            else:
                st.session_state.p_name = p_name
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