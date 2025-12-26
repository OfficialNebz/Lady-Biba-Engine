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
    page_title="Lady Biba Client",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# --- LUXURY CSS OVERRIDE ---
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Montserrat:wght@300;400&display=swap');

        /* RESET & DARK MODE */
        .stApp {
            background-color: #000000;
            color: #E0E0E0;
        }

        /* HEADINGS - SERIF & ELEGANT */
        h1, h2, h3 {
            font-family: 'Cormorant Garamond', serif !important;
            font-weight: 300 !important;
            letter-spacing: 0.05rem;
            color: #F0F0F0 !important;
        }

        /* BODY TEXT - SANS SERIF */
        p, div, label, input, button {
            font-family: 'Montserrat', sans-serif !important;
            font-weight: 300;
        }

        /* INPUTS - REMOVE BORDERS */
        .stTextInput > div > div > input {
            background-color: #111;
            color: #fff;
            border: 1px solid #222;
            border-radius: 0px; /* Sharp edges */
            padding: 12px;
        }
        .stTextInput > div > div > input:focus {
            border-color: #555;
            box-shadow: none;
        }

        /* BUTTONS - MINIMALIST */
        div.stButton > button {
            background-color: #F0F0F0;
            color: #000;
            border: none;
            border-radius: 0px;
            padding: 0.8rem 2rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-size: 12px;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            background-color: #D4AF37; /* Gold on hover */
            color: #fff;
            transform: translateY(-2px);
        }

        /* HIDE UGLY STREAMLIT ELEMENTS */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* IMAGES */
        img {
            filter: brightness(0.9);
            transition: filter 0.3s;
        }
        img:hover {
            filter: brightness(1.1);
        }
        </style>
    """, unsafe_allow_html=True)


inject_custom_css()

# --- AUTH LOGIC (SILENT & DEADLY) ---
# Initialize
api_key = None
notion_token = None
notion_db_id = None

# Check Secrets
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    notion_token = st.secrets["NOTION_TOKEN"]
    notion_db_id = st.secrets["NOTION_DB_ID"]

# Sidebar is for MANUAL OVERRIDE ONLY
with st.sidebar:
    st.header("Settings")
    if not api_key:
        api_key = st.text_input("API Key", type="password")
        notion_token = st.text_input("Notion Token", type="password")
        notion_db_id = st.text_input("Database ID")
    else:
        st.success("System Authenticated")
        if st.button("Reset Session"):
            st.session_state.clear()
            st.rerun()


# --- INTELLIGENCE FUNCTIONS ---
def get_valid_images(url_list):
    """
    Downloads images and filters out logos/icons by PIXEL SIZE.
    This kills the logo bug permanently.
    """
    valid_images = []

    for url in url_list:
        try:
            # Quick fetch
            response = requests.get(url, timeout=5)
            img = Image.open(BytesIO(response.content))

            # THE FILTER:
            # 1. Must be larger than 300x300px (kills icons)
            # 2. Must not be extremely wide/flat (kills banners)
            w, h = img.size
            aspect = w / h

            if w > 300 and h > 300 and 0.5 < aspect < 1.8:
                valid_images.append(img)

            if len(valid_images) >= 3:  # We only need 3 good shots
                break
        except:
            continue

    return valid_images


def scrape_website(target_url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(target_url, headers=headers)
        soup = BeautifulSoup(r.content, 'html.parser')

        # 1. Title
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else "Unknown Product"

        # 2. Text Description (The Ground Truth)
        # Lady Biba uses specific classes, but we'll cast a wide net for paragraphs
        description_text = ""
        desc_div = soup.find('div', class_='product__description')  # Common Shopify class
        if desc_div:
            description_text = desc_div.get_text(strip=True)[:1000]  # Limit to 1000 chars
        else:
            # Fallback: Grab the first few paragraphs
            paragraphs = soup.find_all('p')
            description_text = " ".join([p.text.strip() for p in paragraphs[:5]])

        # 3. Images (Existing Logic)
        possible_urls = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src: continue
            if src.startswith('//'): src = 'https:' + src
            if 'logo' not in src.lower() and 'icon' not in src.lower():
                possible_urls.append(src)

        final_images = get_valid_images(possible_urls)

        return title, description_text, final_images  # Returning 3 things now
    except Exception as e:
        return None, None, []


def generate_campaign(product_name, description, images, key):  # Added description arg
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-flash-latest')

    # Payload: Text Context + Images
    payload = [f"Product: {product_name}\n\nOfficial Description (Use these facts): {description}"]
    payload.extend(images)

    prompt = """
    You are the Senior Creative Director for Lady Biba.
    Tone: High-Fashion, Minimalist, Confident, Lagos-Elite.

    Directives:
    1. ACCURACY: Use the fabric/details from the Official Description. Do not hallucinate features.\n
    2. CONTEXT: Frame the benefits for the Lagos context (Heat, Traffic, Boardrooms).\n
    3. FORMAT: JSON ONLY.\n
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
        st.error(f"Generation Error: {e}")
        return []


def save_to_notion(p_name, post, persona, token, db_id):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    body = {
        "parent": {"database_id": db_id},
        "properties": {
            "Product Name": {"title": [{"text": {"content": p_name}}]},
            "Persona": {"rich_text": [{"text": {"content": persona}}]},
            "Generated Post": {"rich_text": [{"text": {"content": post[:2000]}}]}
        }
    }
    requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(body))


# --- MAIN INTERFACE ---
st.title("LADY BIBA / INTELLIGENCE")

# Clean input state
if "target_url" not in st.session_state:
    st.session_state.target_url = ""

# Input
col1, col2 = st.columns([4, 1])
with col1:
    url_input = st.text_input("Product URL", placeholder="https://ladybiba.com/...", label_visibility="collapsed")
with col2:
    run_btn = st.button("GENERATE ASSETS")

# Processing
if run_btn and url_input:
    # URL Cleaning
    clean_url = url_input.split('?')[0]

    if not api_key:
        st.error("SYSTEM HALTED: Missing Credentials.")
    else:
        with st.spinner("Acquiring Visual Data..."):
            p_name, valid_imgs = scrape_website(clean_url)

            if p_name and valid_imgs:
                st.session_state.p_name = p_name
                st.session_state.imgs = valid_imgs

                # Show Images (Clean Layout)
                st.image(valid_imgs, width=200, caption=["Visual 1", "Visual 2", "Visual 3"][:len(valid_imgs)])

                with st.spinner("Drafting Copy..."):
                    st.session_state.results = generate_campaign(p_name, valid_imgs, api_key)
            else:
                st.error("Acquisition Failed. Link invalid or images too small.")

# Processing Block
if run_btn and url_input:
    # ... (existing auth checks) ...
    with st.spinner("Acquiring Visual & Textual Data..."):
        # Update to unpack 3 values
        p_name, p_desc, valid_imgs = scrape_website(clean_url)

        if p_name and valid_imgs:
            st.session_state.p_name = p_name
            # Store the results
            st.session_state.results = generate_campaign(p_name, p_desc, valid_imgs, api_key)
        # ... (error handling) ...

# Results Display (Editable)
if "results" in st.session_state and st.session_state.results:
    st.divider()
    st.subheader(f"CAMPAIGN: {st.session_state.p_name.upper()}")

    # We use a form so the user can edit EVERYTHING then save ALL
    with st.form("campaign_form"):
        updated_posts = []

        for i, item in enumerate(st.session_state.results):
            st.markdown(f"### 🎯 {item['persona']}")
            # Text Area allows editing
            edited_text = st.text_area(
                f"Edit Caption for {item['persona']}",
                value=item['post'],
                height=150,
                key=f"post_{i}"
            )
            updated_posts.append({"persona": item['persona'], "post": edited_text})
            st.markdown("---")

        # The Big Save Button
        if st.form_submit_button("💾 APPROVE & EXPORT TO DATABASE"):
            for item in updated_posts:
                save_to_notion(st.session_state.p_name, item['post'], item['persona'], notion_token, notion_db_id)
            st.success("✅ All edited posts exported to Notion!")