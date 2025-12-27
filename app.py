import streamlit as st
import time
# IMPORT THE BRAIN (logic.py)
import logic

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="LADY BIBA / INTELLIGENCE",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. LUXURY CSS ENGINE (RESTORED & FIXED) ---
st.markdown("""
    <style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Montserrat:wght@200;300;400;600&display=swap');

    /* GLOBAL RESET - THE NUCLEAR OPTION */
    /* This forces Montserrat on EVERYTHING, restoring the luxury feel */
    * { 
        font-family: 'Montserrat', sans-serif !important; 
    }

    /* EXCEPTION: Fix Streamlit Icons (prevent 'keyboard_arrow_down' glitch) */
    /* We tell the browser to ignore Montserrat for specific icon containers */
    div[data-testid="stExpander"] details summary span, 
    div[data-testid="stExpander"] details summary svg {
        font-family: "Source Sans Pro", sans-serif !important;
    }

    /* HEADINGS - SERIF & SHARP */
    h1, h2, h3, h4 { 
        font-family: 'Cormorant Garamond', serif !important; 
        letter-spacing: 1px; 
        color: #F0F0F0; 
    }

    /* APP BACKGROUND */
    .stApp { background-color: #050505; }

    /* AUTH SCREEN CARD */
    .auth-card {
        background: rgba(20, 20, 20, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid #D4AF37;
        padding: 50px;
        text-align: center;
        border-radius: 0px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }

    /* BUTTONS: TACTILE & ANIMATED */
    div.stButton > button {
        width: 100%;
        background-color: transparent;
        color: #D4AF37;
        border: 1px solid #D4AF37;
        padding: 12px 24px;
        font-family: 'Montserrat', sans-serif;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 2px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        border-radius: 0px;
    }

    div.stButton > button:hover {
        background-color: #D4AF37;
        color: #050505;
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 10px 20px rgba(212, 175, 55, 0.2);
    }

    div.stButton > button:active { transform: scale(0.98); }

    /* INPUT FIELDS - GOLD & BLACK */
    div[data-baseweb="input"] > div, textarea {
        background-color: #0a0a0a !important;
        border: 1px solid #333 !important;
        color: #D4AF37 !important;
        text-align: center;
        border-radius: 0px;
    }

    /* MANUAL EXPANDER HEADER */
    .streamlit-expanderHeader {
        background-color: #111 !important;
        color: #D4AF37 !important;
        border: 1px solid #333;
        font-family: 'Montserrat', sans-serif !important;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #080808;
        border-right: 1px solid #222;
    }

    /* HIDE JUNK */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION & SECRETS ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "results" not in st.session_state: st.session_state.results = None
if "p_name" not in st.session_state: st.session_state.p_name = ""
if "gen_id" not in st.session_state: st.session_state.gen_id = 0

api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else None
notion_token = st.secrets.get("NOTION_TOKEN")
notion_db_id = st.secrets.get("NOTION_DB_ID")

# --- 4. AUTH LOGIC ---
if not st.session_state.authenticated:
    st.markdown(
        """<style>.stApp {background-image: url("https://images.unsplash.com/photo-1550614000-4b9519e02d48?q=80&w=2070&auto=format&fit=crop"); background-size: cover;}</style>""",
        unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.container():
            st.markdown(
                '<div class="auth-card"><h1 style="text-align: center; margin:0;">LADY BIBA</h1><p style="text-align: center; font-size: 10px; letter-spacing: 3px; color: #aaa; margin-bottom: 30px;">INTELLIGENCE ACCESS</p>',
                unsafe_allow_html=True)
            password = st.text_input("PASSWORD", type="password", label_visibility="collapsed", placeholder="ENTER KEY")
            if st.button("UNLOCK SYSTEM"):
                if password == "neb123":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("⚠️ ACCESS DENIED")
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 5. MAIN SYSTEM ---
with st.sidebar:
    st.markdown("### COMMAND CENTER")
    st.caption("Lady Biba / Internal Tool v3.1 (Luxury)")
    st.markdown("---")
    if st.button("🔄 FORCE RESET"): st.session_state.clear(); st.rerun()

st.title("LADY BIBA / INTELLIGENCE")

with st.expander("📖 SYSTEM MANUAL"):
    st.markdown("### OPERATIONAL GUIDE")
    st.markdown("---")
    # UPDATED COLUMN RATIOS TO FIX SQUISHING
    c1, c2 = st.columns([1.2, 1.8])
    with c1: st.markdown("**STEP 1: SOURCE**\n\nGo to Lady Biba site. Open product page."); st.caption(
        ".../products/name")
    with c2: st.image("Screenshot (449).png", use_container_width=True)
    st.markdown("---")
    c3, c4 = st.columns([1.2, 1.8])
    with c3: st.markdown("**STEP 2: ACQUIRE**\n\nCopy URL from browser bar.")
    with c4: st.image("Screenshot (450).png", use_container_width=True)
    st.markdown("---")
    c5, c6 = st.columns([1.2, 1.8])
    with c5: st.markdown("**STEP 3: INJECT**\n\nPaste below and execute.")
    with c6: st.image("Screenshot (452).png", use_container_width=True)

url_input = st.text_input("Product URL", placeholder="Paste Lady Biba URL...")

if st.button("GENERATE ASSETS"):
    if not api_key:
        st.error("API Key Missing.")
    elif not url_input:
        st.error("Paste a URL first.")
    else:
        with st.spinner("Analyzing Construction..."):
            st.session_state.gen_id += 1
            # CALLING THE BRAIN
            p_name, p_desc = logic.scrape_website(url_input)
            if p_name is None:
                st.error(p_desc)
            else:
                st.session_state.p_name = p_name
                st.session_state.results = logic.generate_campaign(p_name, p_desc, api_key)

if st.session_state.results:
    st.divider()
    st.subheader(st.session_state.p_name.upper())

    if st.button("💾 EXPORT ALL ASSETS", type="primary", use_container_width=True):
        success, fail = 0, 0
        bar = st.progress(0)
        current_gen = st.session_state.gen_id

        for i, item in enumerate(st.session_state.results):
            p_val = item.get('persona', '')
            original = item.get('post', '')
            # Retrieve edited value or fallback to original
            final_post = st.session_state.get(f"editor_{i}_{current_gen}", original)

            if p_val and final_post:
                # CALLING THE BRAIN
                s, m = logic.save_to_notion(st.session_state.p_name, final_post, p_val, notion_token, notion_db_id)
                if s:
                    success += 1
                else:
                    fail += 1; st.error(f"Failed {p_val}: {m}")
            bar.progress((i + 1) / len(st.session_state.results))

        if success > 0: st.success(f"SUCCESS: {success} Uploaded."); time.sleep(2); st.rerun()

    st.markdown("---")
    current_gen = st.session_state.gen_id
    for i, item in enumerate(st.session_state.results):
        persona = item.get('persona', 'Unknown')
        post = item.get('post', '')
        with st.container():
            c1, c2 = st.columns([0.7, 0.3])
            with c1:
                st.subheader(persona)
                edited = st.text_area(label=persona, value=post, height=250, key=f"editor_{i}_{current_gen}",
                                      label_visibility="collapsed")
            with c2:
                st.write("##");
                st.write("##")
                if st.button("💾 SAVE THIS", key=f"btn_{i}_{current_gen}"):
                    with st.spinner("Saving..."):
                        s, m = logic.save_to_notion(st.session_state.p_name, edited, persona, notion_token,
                                                    notion_db_id)
                        if s:
                            st.toast(f"✅ Saved: {persona}")
                        else:
                            st.error(m)
        st.divider()