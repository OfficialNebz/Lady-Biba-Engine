import streamlit as st
import requests
import json
import time
from bs4 import BeautifulSoup
import google.generativeai as genai

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="LADY BIBA / INTELLIGENCE",
    page_icon="👠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. LUXURY CSS ENGINE (FIXED) ---
st.markdown("""
    <style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Montserrat:wght@200;300;400;600&display=swap');

    /* GLOBAL RESET */
    html, body, .stApp { 
        background-color: #050505; 
        font-family: 'Montserrat', sans-serif !important; 
    }

    p, div, span, label, button, input, textarea, select {
        font-family: 'Montserrat', sans-serif;
    }

    /* HEADINGS - SERIF & SHARP */
    h1, h2, h3, h4 { 
        font-family: 'Cormorant Garamond', serif !important; 
        letter-spacing: 1px; 
        color: #D4AF37; /* Gold for Biba */
    }

    /* SIDEBAR VISIBILITY FIX - CRITICAL */
    [data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid #333;
    }

    /* UNHIDE THE HEADER SO YOU CAN SEE THE MENU */
    header {visibility: visible !important; background-color: transparent !important;}
    [data-testid="stDecoration"] {visibility: hidden;}

    /* BUTTONS */
    div.stButton > button {
        width: 100%;
        background-color: transparent;
        color: #FFFFFF;
        border: 1px solid #D4AF37;
        padding: 14px 24px;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: all 0.4s ease;
        border-radius: 0px;
    }

    div.stButton > button:hover {
        background-color: #D4AF37;
        color: #000000;
        transform: scale(1.01);
    }

    /* INPUT FIELDS */
    div[data-baseweb="input"] > div, textarea {
        background-color: #0a0a0a !important;
        border: 1px solid #333 !important;
        color: #FFFFFF !important;
        text-align: center;
        border-radius: 0px;
    }

    /* TOASTS */
    div[data-baseweb="toast"] {
        background-color: #D4AF37 !important;
        color: #000000 !important;
    }

    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION & SECRETS ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "results" not in st.session_state: st.session_state.results = None
if "p_name" not in st.session_state: st.session_state.p_name = ""
if "gen_id" not in st.session_state: st.session_state.gen_id = 0

api_key = st.secrets.get("GEMINI_API_KEY")
notion_token = st.secrets.get("NOTION_TOKEN")
notion_db_id = st.secrets.get("NOTION_DB_ID")
NOTION_API_URL = "https://api.notion.com/v1/pages"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("### COMMAND CENTER")
    st.caption("Lady Biba Intelligence v2.0")
    if st.button("🔄 RESET SYSTEM"):
        st.session_state.clear()
        st.rerun()


# --- 5. AUTH LOGIC ---
def login_screen():
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #D4AF37;'>LADY BIBA</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; letter-spacing: 3px; color: #888;'>CORPORATE INTELLIGENCE</p>",
                    unsafe_allow_html=True)
        password = st.text_input("PASSWORD", type="password", label_visibility="collapsed", placeholder="ACCESS KEY")
        st.write("##")
        if st.button("UNLOCK"):
            if password == "neb123":  # Hardcoded as requested
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("⚠️ ACCESS DENIED")


if not st.session_state.authenticated:
    login_screen()
    st.stop()


# --- 6. INTELLIGENCE ENGINE (The Logic) ---

def scrape_website(target_url):
    if "ladybiba.com" not in target_url:
        return None, "❌ ERROR: INVALID DOMAIN. Locked to Lady Biba."

    headers = {'User-Agent': 'Mozilla/5.0'}
    clean_url = target_url.split('?')[0]
    json_url = f"{clean_url}.json"
    title = "Lady Biba Piece"
    desc_text = ""

    # Tier 1: JSON
    try:
        r = requests.get(json_url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json().get('product', {})
            title = data.get('title', title)
            raw_html = data.get('body_html', "")
            soup = BeautifulSoup(raw_html, 'html.parser')
            desc_text = soup.get_text(separator="\n", strip=True)
    except:
        pass

    # Tier 2: HTML
    if not desc_text:
        try:
            r = requests.get(target_url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.content, 'html.parser')
            if soup.find('h1'): title = soup.find('h1').text.strip()
            # Lady Biba specific selectors
            main_block = soup.find('div', class_='product__description') or soup.find('div', class_='rte')
            if main_block: desc_text = main_block.get_text(separator="\n", strip=True)
        except Exception as e:
            return None, f"Scrape Error: {str(e)}"

    if not desc_text: return title, "[NO TEXT FOUND]"

    # Clean Junk
    clean_lines = []
    for line in desc_text.split('\n'):
        upper = line.upper()
        if any(x in upper for x in ["SHIPPING", "DELIVERY", "RETURNS", "SIZE", "WHATSAPP"]): continue
        if len(line) > 5: clean_lines.append(line)
    return title, "\n".join(clean_lines[:25])


def generate_campaign(product_name, description, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-flash-latest')

    # REFINED PERSONA LIST FOR LADY BIBA (Power & Ambition)
    persona_matrix = """
    1. The VI High-Court Lawyer (Tone: Lethal Elegance, 'My billable hour is $500')
    2. The Fintech Founder (Tone: Afro-Futuristic, Efficient, Tech-savvy)
    3. The Oil & Gas Executive (Tone: Old Money, Understated, Boardroom Ready)
    4. The Media Mogul (Tone: Charismatic, Camera-Ready, Bold)
    5. The Diaspora Returnee (Tone: Global Standard, Quality-Obsessed)
    6. The Public Sector Director (Tone: Authoritative, Conservative but Stylish)
    7. The Creative Director (Tone: Structural, Artistic, Unconventional)
    8. The 'Main Character' Wedding Guest (Tone: Show-stopping, Confident)
    """

    prompt = f"""
    Role: Head of Brand Narrative for 'Lady Biba'.
    Brand Voice: "The Woman Who Works." Power dressing. Structural feminism. Ambition.
    Product: {product_name}
    Specs: {description}

    TASK:
    1. Select TOP 3 Personas from the list.
    2. Write 3 Captions (one per persona).
    3. Write 1 "Hybrid Power Caption".

    CRITICAL RULE FOR HYBRID CAPTION:
    Do NOT write a strategy or explain "why". Write the actual caption.
    Blend the "Corporate Authority" of the Lawyer with the "Social Grace" of the Returnee.
    It should sound like a woman who just closed a multi-million Naira deal and is heading to dinner.

    Output JSON ONLY:
    [
        {{"persona": "Persona Name", "post": "Caption text..."}},
        ...
        {{"persona": "Lady Biba Power Hybrid", "post": "The unified caption text..."}}
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

    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # PAYLOAD WITH STATUS: DRAFT
    data = {
        "parent": {"database_id": db_id},
        "properties": {
            "Product Name": {"title": [{"text": {"content": str(p_name)}}]},
            "Persona": {"rich_text": [{"text": {"content": str(persona)}}]},
            "Generated Post": {"rich_text": [{"text": {"content": str(post)[:2000]}}]},
            "Status": {"status": {"name": "Draft"}}
        }
    }

    try:
        response = requests.post(NOTION_API_URL, headers=headers, data=json.dumps(data), timeout=15)
        if response.status_code == 200:
            return True, "Success"
        else:
            return False, f"Notion Error {response.status_code}: {response.text}"
    except Exception as e:
        return False, f"System Error: {str(e)}"


# --- 7. UI LAYOUT ---
st.markdown("<br>", unsafe_allow_html=True)
st.title("LADY BIBA / INTELLIGENCE")
st.markdown("---")

# RESTORED SYSTEM MANUAL
with st.expander("📖 SYSTEM MANUAL (CLICK TO OPEN)"):
    st.markdown("### OPERATIONAL GUIDE")
    st.markdown("---")
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.markdown("**STEP 1: SOURCE**\n\nGo to the Lady Biba site. Open a single product page.")
        st.caption(".../products/name")
    with c2:
        # Make sure these image files are actually in your folder!
        try:
            st.image("Screenshot (449).png", use_container_width=True)
        except:
            st.warning("⚠️ Manual image missing. Check folder.")

    st.markdown("---")
    c3, c4 = st.columns([1, 1.5])
    with c3:
        st.markdown("**STEP 2: ACQUIRE**\n\nCopy the URL from the browser bar.")
    with c4:
        try:
            st.image("Screenshot (450).png", use_container_width=True)
        except:
            pass

    st.markdown("---")
    c5, c6 = st.columns([1, 1.5])
    with c5:
        st.markdown("**STEP 3: INJECT**\n\nPaste the URL below and execute.")
    with c6:
        try:
            st.image("Screenshot (452).png", use_container_width=True)
        except:
            pass

# INPUT FIELD FOLLOWS
url_input = st.text_input("Product URL", placeholder="Paste Lady Biba URL...")
# --- MISSING TRIGGER BLOCK ---
if st.button("GENERATE ASSETS", type="primary"):
    if not url_input:
        st.error("⚠️ PLEASE ENTER A PRODUCT URL")
    else:
        with st.spinner("ANALYZING LADY BIBA ARCHIVES..."):
            # 1. Scrape
            p_name, desc = scrape_website(url_input)

            if p_name:
                # 2. Generate
                st.session_state.p_name = p_name
                # Use the API key we fetched at the top
                results = generate_campaign(p_name, desc, api_key)

                # 3. Store & Refresh
                st.session_state.results = results
                st.session_state.gen_id += 1
                st.rerun()
            else:
                st.error(f"❌ CONNECTION FAILED: {desc}")

if st.session_state.results:
    st.divider()
    st.subheader(st.session_state.p_name.upper())

    # BULK EXPORT
    if st.button("💾 EXPORT CAMPAIGN TO NOTION", type="primary", use_container_width=True):
        if not notion_token:
            st.error("Notion Config Missing")
        else:
            success = 0
            bar = st.progress(0)
            for i, item in enumerate(st.session_state.results):
                p_val = item.get('persona', '')
                final_post = st.session_state.get(f"editor_{i}_{st.session_state.gen_id}", item.get('post', ''))

                if p_val and final_post:
                    s, m = save_to_notion(st.session_state.p_name, final_post, p_val, notion_token, notion_db_id)
                    if s: success += 1
                bar.progress((i + 1) / len(st.session_state.results))

            if success > 0:
                st.success(f"Uploaded {success} Assets.")
                time.sleep(1.5)
                st.rerun()

    st.markdown("---")

    # INDIVIDUAL EDITORS
    current_gen = st.session_state.gen_id
    for i, item in enumerate(st.session_state.results):
        persona = item.get('persona', 'Unknown')
        post = item.get('post', '')

        with st.container():
            c1, c2 = st.columns([0.75, 0.25])
            with c1:
                st.subheader(persona)
                edited = st.text_area(label=persona, value=post, height=200, key=f"editor_{i}_{current_gen}",
                                      label_visibility="collapsed")
            with c2:
                st.write("##");
                st.write("##")
                if st.button("SAVE", key=f"btn_{i}_{current_gen}"):
                    s, m = save_to_notion(st.session_state.p_name, edited, persona, notion_token, notion_db_id)
                    if s:
                        st.toast("✅ Saved")
                    else:
                        st.error(m)
        st.divider()