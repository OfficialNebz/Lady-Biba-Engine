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


# --- 2. LUXURY VISUALS (CSS) ---
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Montserrat:wght@300;400&display=swap');

        /* RESET & DARK MODE */
        .stApp {
            background-color: #050505;
            color: #E0E0E0;
        }

        /* TYPOGRAPHY */
        h1, h2, h3 {
            font-family: 'Cormorant Garamond', serif !important;
            font-weight: 400 !important;
            letter-spacing: 0.05rem;
            color: #F0F0F0 !important;
        }
        p, div, label, input, button, textarea {
            font-family: 'Montserrat', sans-serif !important;
            font-weight: 300;
        }

        /* INPUTS - SHARP & MINIMAL */
        .stTextInput > div > div > input {
            background-color: #0a0a0a;
            color: #fff;
            border: 1px solid #333;
            border-radius: 0px;
            padding: 12px;
        }
        .stTextInput > div > div > input:focus {
            border-color: #D4AF37; /* Gold focus */
        }

        /* BUTTONS - LUXURY INTERACTION */
        div.stButton > button {
            background-color: #F0F0F0;
            color: #000;
            border: none;
            border-radius: 0px;
            padding: 0.8rem 2rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
            width: 100%;
        }
        div.stButton > button:hover {
            background-color: #D4AF37;
            color: #fff;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2);
        }

        /* IMAGE SPACING */
        div[data-testid="column"] {
            background: rgba(255,255,255,0.02);
            padding: 10px;
            border-radius: 4px; /* Subtle frame */
        }
        img {
            border-radius: 2px;
        }

        /* HIDE JUNK */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)


inject_custom_css()

# --- 3. AUTH SYSTEM ---
api_key = None
notion_token = None
notion_db_id = None

# Auto-load from Secrets
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    notion_token = st.secrets["NOTION_TOKEN"]
    notion_db_id = st.secrets["NOTION_DB_ID"]

# Manual Override (Sidebar)
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


# --- 4. ENGINE (SCRAPER & AI) ---
def get_valid_images(url_list):
    """Filters images by size to kill logos."""
    valid_images = []
    for url in url_list:
        try:
            response = requests.get(url, timeout=3)
            img = Image.open(BytesIO(response.content))
            w, h = img.size
            # Filter: Must be bigger than 300px and not a wide banner
            if w > 300 and h > 300 and 0.5 < (w / h) < 1.5:
                valid_images.append(img)
            if len(valid_images) >= 3:
                break
        except:
            continue
    return valid_images


def scrape_website(target_url):
    """Returns Title, Description, AND Images (3 items)"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(target_url, headers=headers)
        soup = BeautifulSoup(r.content, 'html.parser')

        # 1. Title
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else "Unknown Product"

        # 2. Description (The Ground Truth)
        desc_text = "Lady Biba Fashion Piece."
        possible_descs = soup.find_all('div', class_='product-description')  # Common
        if not possible_descs:
            possible_descs = soup.find_all('div', class_='rte')  # Shopify standard

        if possible_descs:
            desc_text = possible_descs[0].get_text(strip=True)[:800]
        else:
            # Fallback
            ps = soup.find_all('p')
            desc_text = " ".join([p.text.strip() for p in ps[:3]])

        # 3. Images
        possible_urls = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src: continue
            if src.startswith('//'): src = 'https:' + src
            if 'logo' not in src.lower() and 'icon' not in src.lower():
                possible_urls.append(src)

        final_images = get_valid_images(possible_urls)

        return title, desc_text, final_images
    except Exception as e:
        return None, None, []


def generate_campaign(product_name, description, images, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    payload = [f"Product: {product_name}\n\nSpecs: {description}"]
    payload.extend(images)

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
    payload.append(prompt)

    try:
        response = model.generate_content(payload)
        clean = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        return [{"persona": "Error", "post": f"AI Generation Failed: {e}"}]


def save_to_notion(p_name, post, persona, token, db_id):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": {"database_id": db_id},
        "properties": {
            "Product Name": {"title": [{"text": {"content": p_name}}]},
            "Persona": {"rich_text": [{"text": {"content": persona}}]},
            "Generated Post": {"rich_text": [{"text": {"content": post[:2000]}}]}
        }
    }
    requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(data))


# --- 5. MAIN INTERFACE ---
st.title("LADY BIBA / INTELLIGENCE")

if "results" not in st.session_state:
    st.session_state.results = None
if "p_name" not in st.session_state:
    st.session_state.p_name = ""

# Input
col1, col2 = st.columns([4, 1])
with col1:
    url_input = st.text_input("Product URL", placeholder="Paste Link...", label_visibility="collapsed")
with col2:
    run_btn = st.button("GENERATE ASSETS")

if run_btn and url_input:
    clean_url = url_input.split('?')[0]
    if not api_key:
        st.error("MISSING API KEY.")
    else:
        with st.spinner("Analyzing Texture & Context..."):
            # UNPACKING 3 VALUES (Fixes the Crash)
            p_name, p_desc, valid_imgs = scrape_website(clean_url)

            if p_name and valid_imgs:
                st.session_state.p_name = p_name

                # IMAGE DISPLAY (Fixes the "Sandwich")
                st.markdown("### Visual Analysis")
                # Create columns equal to number of images with GAP
                img_cols = st.columns(len(valid_imgs), gap="large")
                for i, col in enumerate(img_cols):
                    with col:
                        # use_container_width makes it responsive
                        st.image(valid_imgs[i], use_container_width=True)

                        # Generate
                st.session_state.results = generate_campaign(p_name, p_desc, valid_imgs, api_key)
            else:
                st.error("Scraping Failed. Check URL.")

# EDITABLE RESULTS
if st.session_state.results:
    st.divider()
    st.subheader(f"CAMPAIGN: {st.session_state.p_name.upper()}")

    with st.form("edit_form"):
        final_posts = []
        for i, item in enumerate(st.session_state.results):
            st.markdown(f"**{item['persona']}**")
            # Editable Text Area
            val = st.text_area("Caption", value=item['post'], height=150, key=f"edit_{i}", label_visibility="collapsed")
            final_posts.append({"persona": item['persona'], "post": val})
            st.markdown("---")

        if st.form_submit_button("💾 APPROVE & EXPORT ALL TO NOTION"):
            for item in final_posts:
                save_to_notion(st.session_state.p_name, item['post'], item['persona'], notion_token, notion_db_id)
            st.success("✅ Database Updated.")