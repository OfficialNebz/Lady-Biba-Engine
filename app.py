import streamlit as st
import os
import requests
import json
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


# --- 2. LUXURY CSS ---
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
        </style>
    """, unsafe_allow_html=True)


inject_custom_css()

# --- 3. AUTH & STATE ---
# Initialize Session State Variables if they don't exist
if "results" not in st.session_state: st.session_state.results = None
if "p_name" not in st.session_state: st.session_state.p_name = ""
if "imgs" not in st.session_state: st.session_state.imgs = []  # Store images here!

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
        st.success("System Authenticated")
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
        title = soup.find('h1').text.strip() if soup.find('h1') else "Lady Biba Piece"

        desc_text = "Lady Biba Fashion Piece."
        descs = soup.find_all('div', class_='product-description') or soup.find_all('div', class_='rte')
        if descs: desc_text = descs[0].get_text(strip=True)[:800]

        urls = [img.get('src') for img in soup.find_all('img') if img.get('src')]
        urls = ['https:' + u if u.startswith('//') else u for u in urls]
        valid_urls = [u for u in urls if 'logo' not in u.lower() and 'icon' not in u.lower()]

        return title, desc_text, get_valid_images(valid_urls)
    except:
        return None, None, []


def generate_campaign(product_name, description, images, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-flash-latest')

    # We stripped your prompt down to the essentials to stop the "Corny" output.
    # It now strictly forbids meta-commentary.
    prompt = """
    You are the Senior Copywriter for Lady Biba. 
    Write 3 High-Conversion Instagram Captions + 1 Hybrid Strategy.

    CRITICAL RULES:
    1. DO NOT explain the tone (e.g., never say "We combined X with Y"). JUST WRITE THE CAPTION.
    2. Speak directly to the customer's pain: "Next Week Friday" lies, Tailor disappointment, Looking cheap in a boardroom.
    3. Use these Personas:
       - The VI High Court Lawyer (Authority, Precision)
       - The Oil & Gas Director (Understated Wealth, Time-Efficiency)
       - The Wedding Guest (Breathable fabric, Owambe dominance)

    Output JSON ONLY:
    [
        {"persona": "The VI Lawyer", "post": "Caption content..."},
        {"persona": "The Oil Director", "post": "Caption content..."},
        {"persona": "The Wedding Guest", "post": "Caption content..."},
        {"persona": "Hybrid Strategy", "post": "Caption content..."}
    ]
    """

    payload = [f"Product: {product_name}\nSpecs: {description}", prompt]
    payload.extend(images)

    try:
        response = model.generate_content(payload)
        clean = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        return [{"persona": "Error", "post": f"Failed: {e}"}]


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
    requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(data))


# --- 5. UI FLOW ---
st.title("LADY BIBA / INTELLIGENCE")

col1, col2 = st.columns([4, 1])
with col1:
    url_input = st.text_input("Product URL", placeholder="Paste Link...", label_visibility="collapsed")
with col2:
    run_btn = st.button("GENERATE ASSETS")

# --- LOGIC: EXECUTE ONLY ON CLICK ---
if run_btn and url_input:
    clean_url = url_input.split('?')[0]
    if not api_key:
        st.error("MISSING API KEY.")
    else:
        with st.spinner("Analyzing..."):
            p_name, p_desc, valid_imgs = scrape_website(clean_url)
            if p_name and valid_imgs:
                # SAVE TO SESSION STATE (This fixes the vanishing images)
                st.session_state.p_name = p_name
                st.session_state.imgs = valid_imgs
                st.session_state.results = generate_campaign(p_name, p_desc, valid_imgs, api_key)
            else:
                st.error("Scraping Failed.")

# --- DISPLAY: ALWAYS RUNS IF DATA EXISTS ---
if st.session_state.p_name and st.session_state.imgs:
    st.divider()
    st.subheader(f"CAMPAIGN: {st.session_state.p_name.upper()}")

    # 1. SHOW IMAGES (Outside the button logic, so they stay)
    cols = st.columns(len(st.session_state.imgs), gap="large")
    for i, col in enumerate(cols):
        with col:
            st.image(st.session_state.imgs[i], use_container_width=True)

    st.divider()

    # 2. SHOW RESULTS (Individual Controls)
    if st.session_state.results:
        for i, item in enumerate(st.session_state.results):
            st.markdown(f"### {item['persona']}")

            # Text Area for Editing
            # We use a unique key for each text area so it remembers edits
            edited_text = st.text_area(
                "Caption",
                value=item['post'],
                height=150,
                key=f"edit_{i}",
                label_visibility="collapsed"
            )

            # INDIVIDUAL EXPORT BUTTON (This fixes your "Loss of Control")
            if st.button(f"💾 EXPORT '{item['persona']}' TO NOTION", key=f"save_{i}"):
                save_to_notion(st.session_state.p_name, edited_text, item['persona'], notion_token, notion_db_id)
                st.toast(f"✅ {item['persona']} Saved!")

            st.markdown("---")