import streamlit as st
import os
import requests
import json
import re
from bs4 import BeautifulSoup
import google.generativeai as genai
from PIL import Image
from io import BytesIO
import time

# --- 1. CONFIGURATION (MUST BE FIRST) ---
st.set_page_config(
    page_title="LADY BIBA / INTELLIGENCE",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# --- THE VELVET ROPE (SECURITY LAYER) ---
def check_password():
    """Returns `True` if the user had the correct password."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # --- CSS FOR THE LOGIN SCREEN (STATIC LUXURY) ---
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Montserrat:wght@300;400&display=swap');

        [data-testid="stSidebar"] { display: none; }
        header { visibility: hidden; }
        footer { visibility: hidden; }

        .stApp {
            background-image: url("https://images.unsplash.com/photo-1445205170230-053b83016050?q=80&w=2071&auto=format&fit=crop"); 
            background-size: cover;
            background-position: center;
        }

        .stApp::before {
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(5px);
            z-index: -1;
        }

        @keyframes subtleFade {
            0% { opacity: 0; }
            100% { opacity: 1; }
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
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        }

        div[data-baseweb="input"] > div {
            background-color: #111 !important;
            border: 1px solid #333 !important;
            color: #D4AF37 !important;
            font-family: 'Montserrat', sans-serif !important;
            text-align: center;
        }

        div.stButton > button {
            width: 100%;
            border: 1px solid #D4AF37 !important;
            color: #D4AF37 !important;
            background-color: transparent !important;
            font-family: 'Montserrat', sans-serif;
            font-weight: 600;
            letter-spacing: 2px;
            transition: all 0.3s ease;
            margin-top: 25px;
            padding: 15px 0;
        }

        div.stButton > button:hover {
            background-color: #D4AF37 !important;
            color: #000 !important;
            transform: scale(1.02);
            box-shadow: 0 0 20px rgba(212, 175, 55, 0.4);
        }

        h1 { font-family: 'Cormorant Garamond', serif !important; color: #D4AF37 !important; letter-spacing: 1px; }
        p { font-family: 'Montserrat', sans-serif !important; color: #888; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; }
        </style>
        """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("<h1>ATELIER ACCESS</h1>", unsafe_allow_html=True)
        st.markdown("<p>Authorized Personnel Only</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("login_form"):
            password = st.text_input("ACCESS KEY", type="password", label_visibility="collapsed",
                                     placeholder="ENTER KEY")
            submit = st.form_submit_button("UNLOCK SYSTEM")
        st.markdown('</div>', unsafe_allow_html=True)

    if submit:
        if password == "neb123":  # <--- YOUR PASSWORD
            st.session_state.authenticated = True
            st.toast("✨ ACCESS GRANTED")
            time.sleep(1)
            st.rerun()
        else:
            st.toast("⚠️ ACCESS DENIED")
            time.sleep(1)

    return False


if not check_password():
    st.stop()

# =========================================================
# 🎬 THE MAIN APP (STEALTH FADE IN)
# =========================================================

st.markdown("""
    <style>
    @keyframes deepFade {
        0% { opacity: 0; }
        100% { opacity: 1; }
    }

    .block-container {
        animation: deepFade 1.5s ease-out forwards;
    }

    .stApp {
        background-image: none !important;
        background-color: #050505 !important;
    }

    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Montserrat:wght@300;400&display=swap');

    h1, h2, h3 { font-family: 'Cormorant Garamond', serif !important; color: #F0F0F0 !important; font-weight: 400; }
    p, div, label, textarea { font-family: 'Montserrat', sans-serif !important; font-weight: 300; }

    .stTextInput > div > div > input { 
        background-color: #0a0a0a; 
        color: #fff; 
        border: 1px solid #333; 
        font-family: 'Montserrat', sans-serif;
    }

    div.stButton > button { 
        background-color: #F0F0F0; 
        color: #000; 
        border: none; 
        font-family: 'Montserrat', sans-serif;
        font-weight: 600; 
        text-transform: uppercase;
        transition: transform 0.2s ease;
    }
    div.stButton > button:hover { 
        background-color: #D4AF37; 
        color: #fff; 
        transform: scale(1.02);
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
    }

    .auth-badge {
        background-color: #D4AF37; color: #000; padding: 10px; text-align: center;
        font-family: 'Montserrat', sans-serif;
        font-weight: 700; text-transform: uppercase; letter-spacing: 1px; font-size: 11px;
        margin-bottom: 20px; border: 1px solid #AA8C2C;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. MAIN APP LOGIC ---
if "results" not in st.session_state: st.session_state.results = None
if "p_name" not in st.session_state: st.session_state.p_name = ""
if "imgs" not in st.session_state: st.session_state.imgs = []
if "p_desc" not in st.session_state: st.session_state.p_desc = ""
if "last_url" not in st.session_state: st.session_state.last_url = ""

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
        st.markdown('<div class="auth-badge">SYSTEM AUTHENTICATED</div>', unsafe_allow_html=True)
        if st.button("Force Reset"):
            st.session_state.clear()
            st.rerun()


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
            if len(valid_images) >= 4: break
        except:
            continue
    return valid_images


def scrape_website(target_url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(target_url, headers=headers)
        soup = BeautifulSoup(r.content, 'html.parser')
        title = soup.find('h1').text.strip() if soup.find('h1') else "Lady Biba Piece"

        desc_text = ""
        main_block = soup.find('div', class_='product__description')
        if not main_block: main_block = soup.find('div', class_='rte')

        if main_block:
            raw_text = main_block.get_text(separator="\n", strip=True)
            is_policy = any(x in raw_text[:100].upper() for x in ["DELIVERY", "RETURN", "SHIPPING", "PRE-ORDER"])
            if not is_policy and len(raw_text) > 10:
                desc_text = raw_text[:2500]
            else:
                desc_text = ""

        if not desc_text:
            ps = soup.find_all('p')
            clean_ps = []
            for p in ps:
                t = p.text.strip()
                if "Shipping" in t or "Returns" in t or "Delivery" in t: break
                if len(t) > 3: clean_ps.append(t)
            desc_text = "\n".join(clean_ps[:8])

        if not desc_text: desc_text = "[NO TEXT DESCRIPTION. DETECT FABRIC, CUT, AND VIBE FROM IMAGES ONLY.]"

        urls = [img.get('src') for img in soup.find_all('img') if img.get('src')]
        urls = ['https:' + u if u.startswith('//') else u for u in urls]
        valid_urls = [u for u in urls if 'logo' not in u.lower() and 'icon' not in u.lower()]

        return title, desc_text, get_valid_images(valid_urls)
    except Exception as e:
        return None, f"Error: {str(e)}", []


def generate_campaign(product_name, description, images, key):
    genai.configure(api_key=key)
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
    Specs: {description}
    TASK: Select TOP 3 Personas from the MASTER LIST below that fit this item. Write 3 Captions (one per persona) + 1 Hybrid Strategy.
    MASTER LIST: {persona_matrix}
    RULES: Use scraped specs (fabric, cut, fit). JSON OUTPUT ONLY.
    Structure: [ {{"persona": "Name", "post": "Caption..."}}, {{"persona": "Name", "post": "Caption..."}}, {{"persona": "Name", "post": "Caption..."}}, {{"persona": "Hybrid Strategy", "post": "Caption..."}} ]
    """

    payload = [prompt]
    if images: payload.extend(images[:4])

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


st.title("LADY BIBA / INTELLIGENCE")

col1, col2 = st.columns([4, 1])
with col1:
    url_input = st.text_input("Product URL", placeholder="Paste Link...", label_visibility="collapsed")
with col2:
    run_btn = st.button("GENERATE ASSETS")

if url_input != st.session_state.last_url:
    st.session_state.results = None
    st.session_state.p_name = ""
    st.session_state.imgs = []
    st.session_state.p_desc = ""
    st.session_state.last_url = url_input

if run_btn and url_input:
    clean_url = url_input.split('?')[0]
    if not api_key:
        st.error("MISSING API KEY.")
    else:
        with st.spinner("Scanning Fabric & Context..."):
            p_name, p_desc, valid_imgs = scrape_website(clean_url)
            if p_name:
                st.session_state.p_name = p_name
                st.session_state.imgs = valid_imgs
                st.session_state.p_desc = p_desc
                st.session_state.results = generate_campaign(p_name, p_desc, valid_imgs, api_key)
            else:
                st.error("Scraping Failed.")

if st.session_state.results:
    st.divider()
    st.subheader(f"CAMPAIGN: {st.session_state.p_name.upper()}")

    with st.expander("👁️ View Raw Scraped Data"):
        st.markdown(f"**Product Name:** {st.session_state.p_name}")
        st.code(st.session_state.p_desc)

    if st.session_state.imgs:
        cols = st.columns(len(st.session_state.imgs), gap="large")
        for i, col in enumerate(cols):
            with col: st.image(st.session_state.imgs[i], use_container_width=True)

    st.divider()

    if st.button("💾 EXPORT ALL TO NOTION", type="primary"):
        success = 0
        prog = st.progress(0)
        for i, item in enumerate(st.session_state.results):
            # --- CRASH GUARD 1: SAFE ACCESS ---
            p_val = item.get('persona', item.get('Persona', 'Unknown Persona'))
            post_val = item.get('post', item.get('Post', item.get('caption', '')))

            s, m = save_to_notion(st.session_state.p_name, post_val, p_val, notion_token, notion_db_id)
            if s:
                success += 1
            else:
                st.error(f"Failed {p_val}: {m}")
            prog.progress((i + 1) / len(st.session_state.results))
        if success == len(st.session_state.results): st.success("Database Updated.")

    for i, item in enumerate(st.session_state.results):
        # --- CRASH GUARD 2: SAFE ACCESS ---
        p_val = item.get('persona', item.get('Persona', 'Unknown Persona'))
        post_val = item.get('post', item.get('Post', item.get('caption', '')))

        st.markdown(f"### {p_val}")
        edited = st.text_area("Caption", value=post_val, height=150, key=f"edit_{i}", label_visibility="collapsed")
        if st.button(f"Export Only This", key=f"save_{i}"):
            s, m = save_to_notion(st.session_state.p_name, edited, p_val, notion_token, notion_db_id)
            if s:
                st.toast("Saved!")
            else:
                st.error(f"Error: {m}")
        st.markdown("---")