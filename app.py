import streamlit as st
import requests
import json
import time
from bs4 import BeautifulSoup
import google.generativeai as genai
from PIL import Image
from io import BytesIO

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="LADY BIBA / INTELLIGENCE",
    page_icon="👠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. LUXURY CSS ENGINE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Montserrat:wght@200;300;400;600&display=swap');

    html, body, .stApp { 
        background-color: #050505; 
        font-family: 'Montserrat', sans-serif !important; 
    }
    p, div, span, label, button, input, textarea, select {
        font-family: 'Montserrat', sans-serif;
    }
    h1, h2, h3, h4 { 
        font-family: 'Cormorant Garamond', serif !important; 
        letter-spacing: 1px; 
        color: #D4AF37; 
    }
    [data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid #333;
    }
    header {visibility: visible !important; background-color: transparent !important;}
    [data-testid="stDecoration"] {visibility: hidden;}

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
    div[data-baseweb="input"] > div, textarea {
        background-color: #0a0a0a !important;
        border: 1px solid #333 !important;
        color: #FFFFFF !important;
        text-align: center;
        border-radius: 0px;
    }
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
    st.caption("Lady Biba Intelligence v2.3 (Stable Vision)")

    if st.button("🔄 RESET SYSTEM"):
        st.cache_data.clear()  # CLEARS THE CACHE SO YOU CAN RE-RUN IF NEEDED
        st.session_state.clear()
        st.rerun()

    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 12px; margin-top: 5px;'><em>Tap to clear cache & start new analysis.</em></div>",
        unsafe_allow_html=True)


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
            if password == "neb123":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("⚠️ ACCESS DENIED")


if not st.session_state.authenticated:
    login_screen()
    st.stop()


# --- 6. INTELLIGENCE ENGINE (VISION + CACHE) ---

@st.cache_data(show_spinner=False)
def scrape_website(target_url):
    """
    Scrapes title, description AND raw JSON data to find images.
    Cached so it doesn't re-download if you click around.
    """
    if "ladybiba.com" not in target_url:
        return None, "❌ ERROR: INVALID DOMAIN. Locked to Lady Biba.", None

    headers = {'User-Agent': 'Mozilla/5.0'}
    clean_url = target_url.split('?')[0]
    json_url = f"{clean_url}.json"
    title = "Lady Biba Piece"
    desc_text = ""
    raw_json = None

    # Tier 1: JSON (The Gold Mine)
    try:
        r = requests.get(json_url, headers=headers, timeout=5)
        if r.status_code == 200:
            raw_json = r.json().get('product', {})
            title = raw_json.get('title', title)
            raw_html = raw_json.get('body_html', "")
            soup = BeautifulSoup(raw_html, 'html.parser')
            desc_text = soup.get_text(separator="\n", strip=True)
    except:
        pass

    # Tier 2: HTML Fallback
    if not desc_text:
        try:
            r = requests.get(target_url, headers=headers, timeout=5)
            soup = BeautifulSoup(r.content, 'html.parser')
            if soup.find('h1'): title = soup.find('h1').text.strip()
            main_block = soup.find('div', class_='product__description') or soup.find('div', class_='rte')
            if main_block: desc_text = main_block.get_text(separator="\n", strip=True)
        except Exception as e:
            return None, f"Scrape Error: {str(e)}", None

    if not desc_text: return title, "[NO TEXT FOUND]", None

    clean_lines = []
    for line in desc_text.split('\n'):
        upper = line.upper()
        if any(x in upper for x in ["SHIPPING", "DELIVERY", "RETURNS", "SIZE", "WHATSAPP"]): continue
        if len(line) > 5: clean_lines.append(line)

    return title, "\n".join(clean_lines[:25]), raw_json


@st.cache_data(show_spinner=False)
def get_optimized_images(product_json):
    """
    Downloads up to 3 images, resized to 800px width for speed.
    Cached so we don't spam download requests.
    """
    if not product_json: return []

    images = []
    # Shopify stores images in a list under 'images'
    raw_images = product_json.get('images', [])[:3]  # Limit to top 3

    for img in raw_images:
        src = img.get('src', '')
        if src:
            # OPTIMIZATION: Request the 800px wide version from Shopify
            if ".jpg" in src:
                optimized_src = src.replace(".jpg", "_800x.jpg")
            elif ".png" in src:
                optimized_src = src.replace(".png", "_800x.png")
            else:
                optimized_src = src

            try:
                # 3s timeout per image to keep it snappy
                response = requests.get(optimized_src, timeout=3)
                if response.status_code == 200:
                    img_bytes = BytesIO(response.content)
                    images.append(Image.open(img_bytes))
            except:
                continue

    return images


@st.cache_data(show_spinner=False)
def generate_campaign(product_name, description, _images, key):
    """
    The Brain. Uses cache so 1 input = 1 API call max.
    Note: _images starts with underscore to tell Streamlit not to hash the image bytes directly (speed opt).
    """
    genai.configure(api_key=key)
    # UPDATED TO STABLE MODEL - Confirmed by your diagnostics
    model = genai.GenerativeModel('models/gemini-flash-latest')

    prompt_text = f"""
    Role: Head of Brand Narrative for 'Lady Biba'.
    Brand Voice: "The Woman Who Works." Power dressing. Structural feminism. Ambition.
    Product: {product_name}
    Specs: {description}

    TASK:
    1. VISUAL ANALYSIS: Look at the provided images. Identify the cut, fabric texture, fit, and color nuances.
    2. INTEGRATION: Combine the visual details (what you see) with the specs (what you read).
    3. OUTPUT:
       - Select TOP 3 Personas.
       - Write 3 Captions.
       - Write 1 "Hybrid Power Caption".

    PERSONAS: VI Lawyer, Fintech Founder, Oil Exec, Media Mogul, Diaspora Returnee.

    Output JSON ONLY:
    [
        {{"persona": "Persona Name", "post": "Caption text..."}},
        ...
        {{"persona": "Lady Biba Power Hybrid", "post": "The unified caption text..."}}
    ]
    """

    content_payload = [prompt_text]
    if _images:
        content_payload.extend(_images)

    try:
        response = model.generate_content(content_payload)
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
        response = requests.post(NOTION_API_URL, headers=headers, data=json.dumps(data), timeout=5)
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

with st.expander("📖 SYSTEM MANUAL (CLICK TO OPEN)"):
    st.markdown("### OPERATIONAL GUIDE")
    st.markdown("---")

    # RESTORED MANUAL WITH IMAGE PLACEHOLDERS
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.markdown("**STEP 1: SOURCE**\n\nGo to Lady Biba site. Open product page.")
    with c2:
        # If you have the image file locally, ensure it is in the same folder
        # or remove this try/except block if you just want text.
        try:
            st.image("Screenshot (449).png", use_container_width=True)
        except:
            st.info("[Image Placeholder: Lady Biba Product Page]")

    st.markdown("---")
    c3, c4 = st.columns([1, 1.5])
    with c3:
        st.markdown("**STEP 2: INJECT**\n\nPaste URL below.")
    with c4:
        try:
            st.image("Screenshot (452).png", use_container_width=True)
        except:
            st.info("[Image Placeholder: URL Input Field]")

url_input = st.text_input("Product URL", placeholder="Paste Lady Biba URL...")

if st.button("GENERATE ASSETS", type="primary"):
    if not url_input:
        st.error("⚠️ PLEASE ENTER A PRODUCT URL")
    else:
        with st.spinner("CONNECTING TO VISUAL CORTEX..."):
            # 1. Scrape Data + Raw JSON
            p_name, desc, raw_json = scrape_website(url_input)

            if p_name:
                st.session_state.p_name = p_name

                # 2. Extract Optimized Images (Cached)
                images_list = []
                if raw_json:
                    st.toast("📸 Scanning Product Visuals...")
                    images_list = get_optimized_images(raw_json)

                # 3. Generate Campaign (Cached)
                # We pass images_list to the AI.
                results = generate_campaign(p_name, desc, images_list, api_key)

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
            with st.spinner("Initializing Notion Uplink..."):
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
                time.sleep(1)
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
                st.write("##")
                st.write("##")
                if st.button("SAVE", key=f"btn_{i}_{current_gen}"):
                    with st.spinner("Syncing to Notion..."):
                        s, m = save_to_notion(st.session_state.p_name, edited, persona, notion_token, notion_db_id)
                        if s:
                            st.toast("✅ Saved")
                        else:
                            st.error(m)
        st.divider()