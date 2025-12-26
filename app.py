import streamlit as st
import os
import requests
import json
from bs4 import BeautifulSoup
import google.generativeai as genai
from PIL import Image
from io import BytesIO


def inject_custom_css():
    st.markdown("""
        <style>
        /* Import a fancy font */
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Lato:wght@300;400&display=swap');

        /* Main Background - Dark Luxury */
        .stApp {
            background-color: #0e0e0e;
            color: #f0f0f0;
        }

        /* Headings - Gold & Serif */
        h1, h2, h3 {
            font-family: 'Playfair Display', serif;
            color: #d4af37 !important; /* Lady Biba Gold */
        }

        /* Buttons - Gold Gradient */
        div.stButton > button {
            background: linear-gradient(45deg, #d4af37, #aa8c2c);
            color: black;
            border: none;
            font-weight: bold;
            font-family: 'Lato', sans-serif;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4);
        }

        /* Inputs */
        .stTextInput > div > div > input {
            background-color: #1a1a1a;
            color: white;
            border: 1px solid #333;
        }

        /* Expander Styling */
        .streamlit-expanderHeader {
            font-family: 'Playfair Display', serif;
            color: #d4af37;
        }
        </style>
    """, unsafe_allow_html=True)


# CALL THIS RIGHT AFTER set_page_config
# inject_custom_css()
# --- PAGE CONFIG ---
st.set_page_config(page_title="Lady Biba AI Content Engine", page_icon="👗", layout="wide")
inject_custom_css()

# --- SIDEBAR: SETTINGS (The "Hookup") ---
# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.header("⚙️ Configuration")

    # Try to load from secrets first, otherwise ask user
    if "GEMINI_API_KEY" in st.secrets:
        st.success("✅ Credentials Loaded from Secrets")
        api_key_input = st.secrets["GEMINI_API_KEY"]
        notion_token_input = st.secrets["NOTION_TOKEN"]
        notion_db_input = st.secrets["NOTION_DB_ID"]
    else:
        st.warning("⚠️ No secrets found. Enter manually.")
        api_key_input = st.text_input("Gemini API Key", type="password")
        notion_token_input = st.text_input("Notion Secret Token", type="password")
        notion_db_input = st.text_input("Notion Database ID")

    # User inputs their own keys (or you hardcode yours if you sell access)
    api_key_input = st.text_input("Gemini API Key", type="password")
    notion_token_input = st.text_input("Notion Secret Token", type="password")
    notion_db_input = st.text_input("Notion Database ID")

    st.markdown("---")
    st.caption("Powered by Gemini 1.5 Flash")


# --- CORE FUNCTIONS (Reuse your logic) ---
def scrape_website(target_url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(target_url, headers=headers)
        soup = BeautifulSoup(r.content, 'html.parser')
        title = soup.find('h1').text.strip()
        image_urls = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src: continue
            if src.startswith('//'): src = 'https:' + src
            if 'logo' in src.lower() or 'icon' in src.lower(): continue
            if '/products/' in src or '/files/' in src:
                if src not in image_urls:
                    image_urls.append(src)
        return title, image_urls[:3]
    except Exception as e:
        return None, []


def generate_campaign(product_name, image_urls, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')

    content_payload = []
    for url in image_urls:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        content_payload.append(img)

    prompt = f"""
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
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except:
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
st.markdown("Paste a product link below to generate **Lagos-Targeted Marketing Assets** instantly.")

# INPUT
target_url = st.text_input("👉 Paste Product URL", placeholder="https://ladybiba.com/products/...")
if target_url:
    target_url = target_url.split('?')[0] # Removes everything after the '?'

# INITIALIZE SESSION STATE
if "generated_results" not in st.session_state:
    st.session_state.generated_results = None
if "product_name" not in st.session_state:
    st.session_state.product_name = None

# BUTTON CLICK LOGIC
if st.button("🚀 Generate Campaign"):
    if not api_key_input or not notion_token_input or not notion_db_input:
        st.error("❌ Please fill in the Settings in the sidebar first.")
    elif not target_url:
        st.error("❌ Please enter a URL.")
    else:
        with st.spinner("👁️ Scanning Website & Analyzing Visuals..."):
            product_name, images = scrape_website(target_url)

            if product_name:
                st.session_state.product_name = product_name  # SAVE TO STATE

                # Show images
                # Dynamic Layout
                if images:
                    # Filter out likely logo/junk images that might have slipped through
                    # (Lady Biba logos usually have 'logo' or are small, but let's be safer)
                    valid_images = [img for img in images if "logo" not in img.lower()]

                    # Create exactly as many columns as valid images found
                    cols = st.columns(len(valid_images))

                    for i, img_url in enumerate(valid_images):
                        with cols[i]:
                            st.image(img_url, use_container_width=True)

                with st.spinner("🧠 Dreaming up strategy... (This takes 10s)"):
                    results = generate_campaign(product_name, images, api_key_input)
                    if results:
                        st.session_state.generated_results = results  # SAVE TO STATE
                    else:
                        st.error("AI Generation Failed. Check your API Key.")
            else:
                st.error("Could not scrape website. Check the link.")

# DISPLAY RESULTS (PERSISTENT)
if st.session_state.generated_results:
    st.divider()
    st.subheader(f"📝 Generated Content for: {st.session_state.product_name}")

    results = st.session_state.generated_results

    # Auto-Save All Button
    if st.button("💾 Save ALL to Notion Database", type="primary"):
        progress_bar = st.progress(0)
        for i, item in enumerate(results):
            save_to_notion(st.session_state.product_name, item['post'], item['persona'], notion_token_input,
                           notion_db_input)
            progress_bar.progress((i + 1) / len(results))
        st.success("All posts exported successfully!")

    for item in results:
        with st.expander(f"Target: {item['persona']}", expanded=True):
            st.write(item['post'])
            # Individual Save Button
            if st.button(f"Export {item['persona']} to Notion", key=item['persona']):
                save_to_notion(st.session_state.product_name, item['post'], item['persona'], notion_token_input,
                               notion_db_input)
                st.toast(f"✅ Saved to Notion!")