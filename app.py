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


# --- THE VELVET ROPE ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True

    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Montserrat:wght@300;400&display=swap');
        [data-testid="stSidebar"] { display: none; }
        .stApp { 
            background-image: url("https://images.unsplash.com/photo-1445205170230-053b83016050?q=80&w=2071&auto=format&fit=crop"); 
            background-size: cover;
            background-position: center;
        }
        .stApp::before {
            content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(5px); z-index: -1;
        }
        .login-container {
            animation: subtleFade 2s ease-out forwards;
            background-color: rgba(5, 5, 5, 0.95);
            border: 1px solid #D4AF37;
            padding: 60px;
            text-align: center;
            margin-top: 15vh;
            max-width: 550px;
            margin-left: auto;
            margin-right: auto;
        }
        @keyframes subtleFade { 0% { opacity: 0; } 100% { opacity: 1; } }
        div[data-baseweb="input"] > div { background-color: #111 !important; color: #D4AF37 !important; text-align: center; }
        div.stButton > button { background-color: transparent !important; border: 1px solid #D4AF37 !important; color: #D4AF37 !important; width: 100%; }
        div.stButton > button:hover { background-color: #D4AF37 !important; color: #000 !important; }
        h1 { font-family: 'Cormorant Garamond', serif !important; color: #D4AF37 !important; }
        </style>
        """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("<h1>ATELIER ACCESS</h1>", unsafe_allow_html=True)
        with st.form("login_form"):
            password = st.text_input("ACCESS KEY", type="password", label_visibility="collapsed")
            submit = st.form_submit_button("UNLOCK SYSTEM")
        st.markdown('</div>', unsafe_allow_html=True)

    if submit:
        if password == "neb123":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.toast("⚠️ ACCESS DENIED")
    return False


if not check_password():
    st.stop()

# --- 2. STYLING ---
st.markdown("""
    <style>
    @keyframes deepFade { 0% { opacity: 0; } 100% { opacity: 1; } }
    .block-container { animation: deepFade 1.5s ease-out forwards; }
    .stApp { background-image: none !important; background-color: #050505 !important; }
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Montserrat:wght@300;400&display=swap');
    h1, h2, h3 { font-family: 'Cormorant Garamond', serif !important; color: #F0F0F0 !important; }
    p, div, label, textarea { font-family: 'Montserrat', sans-serif !important; }
    .stTextInput > div > div > input { background-color: #0a0a0a; color: #fff; border: 1px solid #333; }
    div.stButton > button { background-color: #F0F0F0; color: #000; border: none; font-weight: 600; }
    div.stButton > button:hover { background-color: #D4AF37; color: #fff; transform: scale(1.02); }
    </style>
""", unsafe_allow_html=True)

# --- 3. STATE & SECRETS ---
if "results" not in st.session_state: st.session_state.results = None
if "p_name" not in st.session_state: st.session_state.p_name = ""
if "p_desc" not in st.session_state: st.session_state.p_desc = ""

api_key = None
notion_token = None
notion_db_id = None

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    notion_token = st.secrets.get("NOTION_TOKEN")
    notion_db_id = st.secrets.get("NOTION_DB_ID")
else:
    st.error("🚨 CRITICAL: Secrets file not found.")


# --- 4. ENGINE ---
def scrape_website(target_url):
    # SHOPIFY JSON BYPASS
    headers = {'User-Agent': 'Mozilla/5.0'}
    clean_url = target_url.split('?')[0]
    json_url = f"{clean_url}.json"

    title = "Lady Biba Piece"
    desc_text = ""

    # 1. JSON Method
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

    # 2. HTML Fallback
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

    # FULL 20 PERSONA MATRIX
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
    Role: Head of Brand Narrative for 'Lady Biba'.
    Product: {product_name}
    Specs: {description}
    TASK: Select TOP 3 Personas from the MASTER LIST below that fit this item. Write 3 Captions (one per persona) + 1 Hybrid Strategy.
    MASTER LIST: {persona_matrix}

    CRITICAL RULE: You MUST quote specific fabric/cut/fit details from the Specs (e.g., 'crepe', 'peplum', 'fitted') in every caption. Do not be generic.

    Output JSON ONLY. Format: 
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
        # FIXED URL: No markdown brackets
        response = requests.post("[https://api.notion.com/v1/pages](https://api.notion.com/v1/pages)", headers=headers,
                                 data=json.dumps(data))
        if response.status_code != 200: return False, response.text
        return True, "Success"
    except Exception as e:
        return False, str(e)


# --- 5. UI LAYOUT ---
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