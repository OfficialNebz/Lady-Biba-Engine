import streamlit as st
import os
import requests
import json
from bs4 import BeautifulSoup
import google.generativeai as genai
from PIL import Image
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Lady Biba AI Content Engine",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- 2026 LUXURY CSS INJECTION ---
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap');

        /* MAIN BACKGROUND */
        .stApp {
            background-color: #050505;
            background-image: radial-gradient(circle at 50% 10%, #1a1a1a 0%, #000000 100%);
            color: #e0e0e0;
        }

        /* TYPOGRAPHY */
        h1, h2, h3 {
            font-family: 'Playfair Display', serif !important;
            color: #D4AF37 !important; /* Gold */
            font-weight: 700;
        }
        p, div, label, input {
            font-family: 'Inter', sans-serif !important;
        }

        /* SIDEBAR STYLING */
        [data-testid="stSidebar"] {
            background-color: #0a0a0a;
            border-right: 1px solid #333;
        }

        /* INPUT FIELDS - MINIMALIST */
        .stTextInput > div > div > input {
            background-color: #111;
            color: #fff;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 10px;
            transition: all 0.3s ease;
        }
        .stTextInput > div > div > input:focus {
            border-color: #D4AF37;
            box-shadow: 0 0 10px rgba(212, 175, 55, 0.2);
        }

        /* BUTTONS - KINETIC GOLD */
        div.stButton > button {
            background: linear-gradient(135deg, #D4AF37 0%, #AA8C2C 100%);
            color: #000;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            width: 100%;
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(212, 175, 55, 0.3);
            color: #000;
        }
        div.stButton > button:active {
            transform: translateY(1px);
        }

        /* CARDS / CONTAINERS (Glassmorphism) */
        div[data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            backdrop-filter: blur(10px);
            margin-bottom: 1rem;
        }

        /* TOAST */
        div[data-testid="stToast"] {
            background-color: #D4AF37;
            color: black;
        }
        </style>
    """, unsafe_allow_html=True)


inject_custom_css()

# --- AUTH LOGIC (THE FIX) ---
# We define these variables globally first
api_key = None
notion_token = None
notion_db_id = None

with st.sidebar:
    st.title("⚙️ Engine Room")

    # Check if Secrets exist in Streamlit Cloud
    if "GEMINI_API_KEY" in st.secrets and "NOTION_TOKEN" in st.secrets:
        st.success("🔒 Secure Access: Active")
        st.caption("Credentials loaded from encrypted cloud storage.")
        # Assign directly from secrets
        api_key = st.secrets["GEMINI_API_KEY"]
        notion_token = st.secrets["NOTION_TOKEN"]
        notion_db_id = st.secrets["NOTION_DB_ID"]
    else:
        st.warning("⚠️ Local Mode")
        api_key = st.text_input("Gemini API Key", type="password")
        notion_token = st.text_input("Notion Secret Token", type="password")
        notion_db_id = st.text_input("Notion Database ID")

    st.markdown("---")
    st.caption("v2.0 | Lady Biba Intelligent Systems")


# --- CORE FUNCTIONS ---
def scrape_website(target_url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(target_url, headers=headers)
        soup = BeautifulSoup(r.content, 'html.parser')
        title = soup.find('h1').text.strip()

        image_urls = []
        # Get all images
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src: continue
            if src.startswith('//'): src = 'https:' + src

            # FILTERS: Remove logos, icons, and tiny images
            lower_src = src.lower()
            if 'logo' in lower_src or 'icon' in lower_src or 'svg' in lower_src: continue

            # Lady Biba specific: products usually have /products/ or specific CDN paths
            # We add a simple check to avoid navigation icons
            if src not in image_urls:
                image_urls.append(src)

        # Return top 4 distinct images (usually the product shots are first)
        return title, image_urls[:4]
    except Exception as e:
        return None, []


def generate_campaign(product_name, image_urls, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model name for better stability

    content_payload = []
    content_payload.append(f"Product Name: {product_name}")

    # Only try to load the first 3 images to save bandwidth/tokens
    for url in image_urls[:3]:
        try:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            content_payload.append(img)
        except:
            continue

    prompt = """
    You are the Head of Marketing for Lady Biba, a premium Nigerian fashion brand.
    Your Voice: Ruthless Elegance. Sophisticated, "Rich Aunty" Vibes, deeply rooted in Lagos culture but appealing to global standards.

    Task: Create 3 distinct Instagram captions and 1 Hybrid Master Strategy.

    The Personas:
    1. The VI High Court Lawyer (Needs structure, power, 'Next Week Friday' pain points)
    2. The Oil & Gas Director (Needs 'Time-Wealth', understated luxury, Lekki-Ikoyi Bridge context)
    3. The Wedding Guest Pro (Needs breathable fabrics for Owambes, standing out without outshining the bride)

    Format:
    Return ONLY valid JSON.
    [
        {"persona": "The VI High Court Lawyer", "post": "Caption text..."},
        {"persona": "The Oil & Gas Director", "post": "Caption text..."},
        {"persona": "The Wedding Guest Pro", "post": "Caption text..."},
        {"persona": "Hybrid Master Strategy", "post": "Caption text..."}
    ]
    """
    content_payload.append(prompt)

    try:
        response = model.generate_content(content_payload)
        # Clean potential markdown code blocks
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        st.error(f"AI Error: {e}")
        return []


def save_to_notion(product_name, sales_post, persona, token, db_id):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": {"database_id": db_id},
        "properties": {
            "Product Name": {"title": [{"text": {"content": product_name}}]},
            "Persona": {"rich_text": [{"text": {"content": persona}}]},
            "Generated Post": {"rich_text": [{"text": {"content": sales_post[:2000]}}]}
        }
    }
    requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(data))


# --- MAIN UI ---
st.title("👗 Lady Biba AI Content Engine")
st.markdown("### The Lagos Luxury Marketing Suite")

# Input Section with stylized container
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        target_url = st.text_input("Product URL", placeholder="Paste the Lady Biba link here...",
                                   label_visibility="collapsed")
    with col2:
        generate_btn = st.button("🚀 IGNITE ENGINE")

# URL Cleaner
if target_url:
    target_url = target_url.split('?')[0]

# SESSION STATE MANAGEMENT
if "results" not in st.session_state:
    st.session_state.results = None
if "p_name" not in st.session_state:
    st.session_state.p_name = None

# LOGIC FLOW
if generate_btn:
    if not api_key or not notion_token:
        st.error("❌ CRITICAL: Credentials missing. Check Secrets or Sidebar.")
    elif not target_url:
        st.error("❌ INPUT ERROR: Paste a URL first.")
    else:
        with st.spinner("💎 Analyzing Fabric, Cut, and Context..."):
            p_name, images = scrape_website(target_url)

            if p_name:
                st.session_state.p_name = p_name
                # Display Images Grid - Dynamic
                if images:
                    valid_imgs = [x for x in images if 'logo' not in x]
                    cols = st.columns(len(valid_imgs))
                    for idx, img in enumerate(valid_imgs):
                        with cols[idx]:
                            st.image(img, use_container_width=True)

                # Generate
                st.session_state.results = generate_campaign(p_name, images, api_key)
            else:
                st.error("❌ SCRAPE FAILED: Website security blocked us or link is invalid.")

# RESULTS DASHBOARD
if st.session_state.results:
    st.divider()
    st.subheader(f"Strategy For: {st.session_state.p_name}")

    # Bulk Action
    if st.button("💾 EXPORT ALL TO NOTION DATABASE"):
        bar = st.progress(0)
        for i, item in enumerate(st.session_state.results):
            save_to_notion(st.session_state.p_name, item['post'], item['persona'], notion_token, notion_db_id)
            bar.progress((i + 1) / len(st.session_state.results))
        st.success("✅ Database Updated Successfully")

    # Cards
    for item in st.session_state.results:
        with st.expander(f"🎯 Target: {item['persona']}", expanded=True):
            st.write(item['post'])
            if st.button(f"Export Only This", key=item['persona']):
                save_to_notion(st.session_state.p_name, item['post'], item['persona'], notion_token, notion_db_id)
                st.toast("Saved to Notion")