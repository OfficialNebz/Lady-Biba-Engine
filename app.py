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
    st.title("Credentials Room")

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
Act as a high-end luxury fashion brand Lagos copywriter. You are able to generate the perfect mix of tones e.g. [Tone 1, e.g., British Vogue Sophistication] and [Tone 2, e.g., Lagos 'No-Nonsense' Confidence] for an instagram post.\n
    You are able to identify core insecurities in the selected persona and your expertise enables you to carry out psychological triggers for High-Net-Worth Individuals (HNWIs).\n
    You are able to identify "Naija" Pain Points: The local frustration it solves, e.g., Tailor lies, fabric fading, or poor finishing\n
    You must identify the time-Wealth Factor: How much time/stress they save by buying ready-to-wear. Use AIDA model (Attention, Interest, Desire, Action). Apply the specific Tone and Pain Points relevant to THAT persona. Focus CTA on scarcity and time-wealth.\n
    Do not use generic AI words.\n
    Write ONE "Hybrid Master Post" that blends all 3 appeals into a universal narrative.
    Reference at least two Mandatory Local Markers: Eko Atlantic, Yellow Buses, Danfo, Owambe, Victoria Island, Banana Island].\n
    Emoji Strategy: Max 3 to 5 emojis. Keep it premium, not cluttered\n
    The Task: Draft an Instagram Sales Post using the AIDA: Attention, Interest, Desire, Action model. Analyze the images. Select the Top 3 Personas.\n
    For each persona you must incorporate this tone, Lagos markers and Hooks/Pain before adding another Tone, Lagos Marker or Hooks/Pains of your choice of your choice\n
    1. The VI High Court Lawyer\nTone:British Vogue Sophistication\nLagos Marker: RSVP Ikoyi Ambience\nHooks/Pain Points (The Trigger): "Next Week Friday" Lies\n
    2. The Diaspora Investor\nTone: "Old Money" Security\nLagos Markers: Banana Island Gatehouse\nHooks/Pain Points (The Trigger): Invisible in Gray Suits\n
    3. The Eco-Conscious Gen Z\nTone: Aggressive Hype\nLagos Markers: The 3rd Mainland Grid\nHooks/Pain Points (The Trigger): Decision Fatigue\n
    4. The The Oil & Gas Director\nTone: Understated Luxury\nLagos Markers: Lekki-Ikoyi Link Bridge\nHooks/Pain Points (The Trigger): Time-Wealth Depletion\n
    5. The Balogun Market 'Oga'\nTone: Lagos 'No-Nonsense'\nLagos Markers: Danfo Bistro Vibes\nHooks/Pain Points (The Trigger): Fabric Fading Shame\n
    6. The Wedding Guest (Pro)\nTone: Kinetic Energy\nLagos Markers: Eko Hotel Grand Ballroom\nHooks/Pain Points (The Trigger): Heat/Humidity Armor\n
    7. The FinTech Founder\nTone: Afro-Futuristic\nLagos Markers: Yaba "Silicon" Tech Hub\nHooks/Pain Points (The Trigger): Poor Finishing Scars\n
    8. The High-Society Matriarch\nTone: Maternal Authority\nLagos Markers: Sunday Brunch at Wheatbaker\nHooks/Pain Points (The Trigger): Economic Friction\n
    9. The Creative Director\nTone: Intellectual Dominance\nLagos Markers: Alara Lagos Aesthetic\nHooks/Pain Points (The Trigger): 'Fast Fashion' Fragility\n
    10. The Side-Hustle Queen\nTone: Relatable Hustle\nLagos Markers: Ikeja Along Traffic\nHooks/Pain Points (The Trigger): Office TGIF-to-Party Crisis\n
    11. The Real-Estate Mogul\nTone: Unapologetic Power\nLagos Markers: Landmark Beach Lounge\nHooks/Pain Points (The Trigger): Impostor Syndrome\n
    12. The Corporate Librarian\nTone: Quiet Confidence\nLagos Markers: Victoria Island Skyline\nHooks/Pain Points (The Trigger): The 9AM Boardroom Fear\n
    13. The Instagram Influencer\nTone: Viral-Trend-Focused\nLagos Markers: Shiro Lagos Lighting\nHooks/Pain Points (The Trigger): "Sold-Out" Anxiety\n
    14. The Medical Consultant\nTone: Clinical and Structured\nLagos Markers: LUTH/Private Clinic VI\nHooks/Pain Points (The Trigger): 24-Hour Style Durability\n
    15. The Church 'Sister' (Elite)\nTone: Pious/Premium\nLagos Markers: House on the Rock Energy\nHooks/Pain Points (The Trigger): Modesty vs Style Battle\n
    16. The Media Personality\nTone: Electric/Charismatic\nLagos Markers: SilverBird/Terra Kulture\nHooks/Pain Points (The Trigger): Narrative Inconsistency\n
    17. The Event Planner\nTone: Chaos-Control\nLagos Markers: Oriental Hotel Tunnels\nHooks/Pain Points (The Trigger): Opportunity Cost of Waiting\n
    18. The UN/NGO Official\nTone: Diplomatic/Polished\nLagos Markers: Abuja-Lagos Air Peace Flight\nHooks/Pain Points (The Trigger): Cultural Identity Gap\n
    19. The Retail Investor\nTone: Analytical/Speculative\nLagos Markers: NSE Marina View\nHooks/Pain Points (The Trigger): ROI on Self-Presentation\n
    OUTPUT FORMAT:
    You must return a valid JSON object. Do not use markdown formatting or markdown blocks. 
    Structure:
    [
        {{"persona": "Name of Persona 1", "post": "Content of post 1..."}},
        {{"persona": "Name of Persona 2", "post": "Content of post 2..."}},
        {{"persona": "Name of Persona 3", "post": "Content of post 3..."}},
        {{"persona": "Hybrid Strategy", "post": "Content of hybrid post..."}}
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
        generate_btn = st.button("Create Description...")

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