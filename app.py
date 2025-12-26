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
        /* Error Box Styling */
        .stAlert { background-color: #330000; border: 1px solid #ff0000; color: #ffcccc; }
        </style>
    """, unsafe_allow_html=True)


inject_custom_css()

# --- 3. AUTH & STATE ---
if "results" not in st.session_state: st.session_state.results = None
if "p_name" not in st.session_state: st.session_state.p_name = ""
if "imgs" not in st.session_state: st.session_state.imgs = []

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

    # THE FULL ARSENAL (20 Personas)
    persona_matrix = """
    1. The Tech-Bro VC (Tone: Lethal Precision | Hook: 'Tailor Story' Trauma)
    2. The VI High-Court Lawyer (Tone: British Vogue Sophistication | Hook: 'Next Week Friday' Lies)
    3. The Diaspora Investor (Tone: 'Old Money' Security | Hook: Invisible in Grey Suits)
    4. The Eco-Conscious Gen Z (Tone: Aggressive Hype | Hook: Decision Fatigue)
    5. The Oil & Gas Director (Tone: Understated Luxury | Hook: Time-Wealth Depletion)
    6. The Balogun Market 'Oga' (Tone: Lagos 'No-Nonsense' | Hook: Fabric Fading Shame)
    7. The Wedding Guest Pro (Tone: Kinetic Energy | Hook: Heat/Humidity Armor)
    8. The Fintech Founder (Tone: Afro-Futuristic | Hook: Poor Finishing Scars)
    9. The High-Society Matriarch (Tone: Maternal Authority | Hook: Economic Friction)
    10. The Creative Director (Tone: Intellectual Dominance | Hook: 'Fast-Fashion' Fragility)
    11. The Side-Hustle Queen (Tone: Relatable Hustle | Hook: Office TGIF-to-Party Crisis)
    12. The Real Estate Mogul (Tone: Unapologetic Power | Hook: Imposter Syndrome)
    13. The Corporate Librarian (Tone: Quiet Confidence | Hook: The 9AM Boardroom Fear)
    14. The Instagram Influencer (Tone: Viral/Trend-Focused | Hook: 'Sold Out' Anxiety)
    15. The Medical Consultant (Tone: Clinical/Structured | Hook: 24-Hour Style Durability)
    16. The Church 'Sister' Elite (Tone: Pious/Premium | Hook: Modesty vs Style Battle)
    17. The Media Personality (Tone: Electric/Charismatic | Hook: Narrative Inconsistency)
    18. The Event Planner (Tone: Chaos-Control | Hook: Opportunity Cost of Waiting)
    19. The UN/NGO Official (Tone: Diplomatic/Polished | Hook: Cultural Identity Gap)
    20. The Retail Investor (Tone: Analytical/Speculative | Hook: ROI on Self-Presentation)
    """

    prompt = f"""
    You are the Senior Creative Director for Lady Biba.

    STEP 1: ANALYZE THE PRODUCT
    Look at the product name: '{product_name}' and description: '{description}'.
    Is it office wear? A party dress? A power suit?

    STEP 2: SELECT THE TARGETS
    From the MASTER LIST below, select the TOP 3 personas that would actually buy this specific item. 
    (e.g., Do not sell a mini-skirt to 'The Church Sister'. Do not sell a ballgown to 'The Corporate Librarian'.)

    MASTER LIST:
    {persona_matrix}

    STEP 3: EXECUTE
    Write 3 High-Conversion Captions (one for each selected persona) + 1 Hybrid Strategy.

    CRITICAL RULES:
    1. USE THE SPECIFIC TONE & HOOK defined in the list for that persona.
    2. REFERENCE LOCAL MARKERS (e.g., Eko Hotel, 3rd Mainland, Alara, Wheatbaker) relevant to that persona.
    3. NO FLUFF. Go straight for the kill (The pain point).

    Output JSON ONLY:
    [
        {{"persona": "Selected Persona Name 1", "post": "Caption content..."}},
        {{"persona": "Selected Persona Name 2", "post": "Caption content..."}},
        {{"persona": "Selected Persona Name 3", "post": "Caption content..."}},
        {{"persona": "Hybrid Strategy", "post": "Caption content..."}}
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
    """
    Saves to Notion and RETURNS the status.
    NO MORE LYING.
    """
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # Payload
    data = {
        "parent": {"database_id": db_id},
        "properties": {
            # CHECK YOUR DATABASE COLUMNS MATCH THESE NAMES EXACTLY
            "Product Name": {"title": [{"text": {"content": p_name}}]},
            "Persona": {"rich_text": [{"text": {"content": persona}}]},
            "Generated Post": {"rich_text": [{"text": {"content": post[:2000]}}]}
        }
    }

    try:
        response = requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(data))

        # DEBUGGING: If it fails, return the error message
        if response.status_code != 200:
            return False, f"Error {response.status_code}: {response.text}"
        return True, "Success"

    except Exception as e:
        return False, str(e)


# --- 5. UI FLOW ---
st.title("LADY BIBA / INTELLIGENCE")

col1, col2 = st.columns([4, 1])
with col1:
    url_input = st.text_input("Product URL", placeholder="Paste Link...", label_visibility="collapsed")
with col2:
    run_btn = st.button("GENERATE ASSETS")

# --- LOGIC ---
if run_btn and url_input:
    clean_url = url_input.split('?')[0]
    if not api_key:
        st.error("MISSING API KEY.")
    else:
        with st.spinner("Analyzing..."):
            p_name, p_desc, valid_imgs = scrape_website(clean_url)
            if p_name and valid_imgs:
                st.session_state.p_name = p_name
                st.session_state.imgs = valid_imgs
                st.session_state.results = generate_campaign(p_name, p_desc, valid_imgs, api_key)
            else:
                st.error("Scraping Failed.")

# --- DISPLAY ---
if st.session_state.p_name and st.session_state.imgs:
    st.divider()
    st.subheader(f"CAMPAIGN: {st.session_state.p_name.upper()}")

    # 1. IMAGES
    cols = st.columns(len(st.session_state.imgs), gap="large")
    for i, col in enumerate(cols):
        with col:
            st.image(st.session_state.imgs[i], use_container_width=True)

    st.divider()

    # 2. GLOBAL EXPORT BUTTON (The "Save All" you wanted)
    if st.button("💾 EXPORT ALL TO NOTION", type="primary"):
        success_count = 0
        error_log = []

        progress_bar = st.progress(0)
        for i, item in enumerate(st.session_state.results):
            # Using the value from the dictionary, assuming no edits for "Bulk Save"
            # OR you can loop through the keys if you want saved edits.
            # For simplicity, we save the generated raw text here.
            status, msg = save_to_notion(st.session_state.p_name, item['post'], item['persona'], notion_token,
                                         notion_db_id)
            if status:
                success_count += 1
            else:
                error_log.append(f"{item['persona']}: {msg}")
            progress_bar.progress((i + 1) / len(st.session_state.results))

        if success_count == len(st.session_state.results):
            st.success("✅ All assets exported successfully!")
        else:
            st.error(f"⚠️ Failed to export {len(error_log)} items.")
            for err in error_log:
                st.code(err, language="json")

    st.markdown("---")

    # 3. INDIVIDUAL CARDS
    if st.session_state.results:
        for i, item in enumerate(st.session_state.results):
            st.markdown(f"### {item['persona']}")

            edited_text = st.text_area(
                "Caption",
                value=item['post'],
                height=150,
                key=f"edit_{i}",
                label_visibility="collapsed"
            )

            if st.button(f"Export Only This", key=f"save_{i}"):
                status, msg = save_to_notion(st.session_state.p_name, edited_text, item['persona'], notion_token,
                                             notion_db_id)
                if status:
                    st.toast(f"✅ {item['persona']} Saved!")
                else:
                    st.error(f"❌ Failed: {msg}")  # SHOWS THE ACTUAL ERROR

            st.markdown("---")