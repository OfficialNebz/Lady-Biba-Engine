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

# --- 2. THE VISUAL ENGINE (CSS OVERHAUL) ---
# This block aggressively overrides Streamlit's defaults to create the "Luxury" feel.
st.markdown("""
    <style>
    /* IMPORT FONTS: Cormorant (Serif) for Luxury, Montserrat (Sans) for Modernity */
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,400&family=Montserrat:wght@200;300;400;600&display=swap');

    /* GLOBAL TYPOGRAPHY FORCE */
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif;
    }

    h1, h2, h3 {
        font-family: 'Cormorant Garamond', serif !important;
        font-weight: 400 !important;
        letter-spacing: 1px !important;
        color: #F5F5F5 !important;
    }

    /* BACKGROUND OVERRIDE */
    .stApp {
        background-color: #050505; /* Deepest Black */
    }

    /* BUTTONS: THE "FEEL" UPGRADE */
    /* We target the specific Streamlit button class */
    div[data-testid="stBaseButton-secondary"] > button {
        width: 100%;
        background-color: transparent;
        color: #D4AF37; /* Gold */
        border: 1px solid #D4AF37;
        padding: 12px 24px;
        font-family: 'Montserrat', sans-serif;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-size: 12px;
        transition: all 0.3s ease-in-out;
        border-radius: 0px;
    }

    div[data-testid="stBaseButton-secondary"] > button:hover {
        background-color: #D4AF37;
        color: #000;
        transform: scale(1.02); /* This is the animation you wanted */
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.4);
    }

    div[data-testid="stBaseButton-secondary"] > button:active {
        transform: scale(0.98);
    }

    /* AUTHENTICATION OVERLAY (GLASSMORPHISM) */
    /* This creates the blurred layer on top of everything */
    .auth-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(15px);
        z-index: 9998;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .auth-box {
        background: rgba(20, 20, 20, 0.6);
        border: 1px solid #333;
        padding: 50px;
        width: 400px;
        text-align: center;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        animation: slideUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
    }

    @keyframes slideUp {
        from { opacity: 0; transform: translateY(50px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* INPUT FIELDS */
    .stTextInput > div > div > input {
        background-color: #0F0F0F;
        color: #D4AF37;
        border: 1px solid #333;
        text-align: center;
        font-family: 'Montserrat', sans-serif;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid #222;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. THE VELVET ROPE (AUTH) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def check_password():
    if st.session_state.authenticated:
        return True

    # This container sits ON TOP of the app due to the CSS z-index
    placeholder = st.empty()
    with placeholder.container():
        st.markdown('<div class="auth-overlay">', unsafe_allow_html=True)

        # We use standard columns to center the login box inside the overlay
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)  # Spacer
            st.markdown("<h1 style='text-align: center; color: #D4AF37;'>LADY BIBA</h1>", unsafe_allow_html=True)
            st.markdown(
                "<p style='text-align: center; letter-spacing: 3px; font-size: 10px; color: #666;'>INTELLIGENCE ACCESS</p>",
                unsafe_allow_html=True)

            password = st.text_input("PASSWORD", type="password", label_visibility="collapsed",
                                     placeholder="ENTER ACCESS KEY")

            if st.button("UNLOCK SYSTEM"):
                if password == "neb123":
                    st.session_state.authenticated = True
                    st.toast("ACCESS GRANTED")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("INVALID CREDENTIALS")

        st.markdown('</div>', unsafe_allow_html=True)
    return False


if not check_password():
    st.stop()

# --- 4. SECRETS ---
api_key = None
notion_token = None
notion_db_id = None

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    notion_token = st.secrets.get("NOTION_TOKEN")
    notion_db_id = st.secrets.get("NOTION_DB_ID")
else:
    st.error("🚨 CRITICAL: Secrets file not found.")

# --- 5. SIDEBAR SETTINGS ---
with st.sidebar:
    st.markdown("### SETTINGS")
    st.caption("Lady Biba / Intelligence v2.1")
    if st.button("FORCE SYSTEM RESET"):
        st.session_state.clear()
        st.rerun()
    st.divider()
    st.success("AUTHENTICATED")


# --- 6. ENGINE FUNCTIONS ---

def scrape_website(target_url):
    # --- GUARD: WRONG URL DETECTION ---
    if "ladybiba.com" not in target_url:
        return None, "❌ ERROR: This URL belongs to another domain. Access restricted to Lady Biba assets only."

    headers = {'User-Agent': 'Mozilla/5.0'}
    clean_url = target_url.split('?')[0]
    json_url = f"{clean_url}.json"

    title = "Lady Biba Piece"
    desc_text = ""

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
    model = genai.GenerativeModel('gemini-1.5-flash')

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
    TASK: Select TOP 3 Personas. Write 3 Captions + 1 Hybrid Strategy.
    MASTER LIST: {persona_matrix}

    CRITICAL RULE: You MUST quote specific fabric/cut/fit details from the Specs (e.g., 'crepe', 'peplum', 'fitted') in every caption.

    Output JSON ONLY: 
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
        response = requests.post("[https://api.notion.com/v1/pages](https://api.notion.com/v1/pages)", headers=headers,
                                 data=json.dumps(data))
        if response.status_code != 200: return False, response.text
        return True, "Success"
    except Exception as e:
        return False, str(e)


# --- 7. MAIN UI LAYOUT ---
if "results" not in st.session_state: st.session_state.results = None
if "p_name" not in st.session_state: st.session_state.p_name = ""

st.title("LADY BIBA / INTELLIGENCE")
url_input = st.text_input("Product URL", placeholder="Paste Lady Biba URL...", label_visibility="collapsed")

if st.button("GENERATE ASSETS"):
    if not api_key:
        st.error("API Key Missing.")
    elif not url_input:
        st.error("Paste a URL first.")
    else:
        with st.spinner("Analyzing Construction..."):
            p_name, p_desc = scrape_website(url_input)

            # GUARD: STOP IF URL IS WRONG
            if "INVALID URL" in str(p_desc):
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