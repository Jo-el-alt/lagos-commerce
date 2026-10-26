import streamlit as st
from PIL import Image, ImageOps
from supabase import create_client, Client
from datetime import datetime, timezone, timedelta
import urllib.parse
import qrcode
import io
import base64
import re
import random
from openai import OpenAI

# Tema-tilstand (skal sættes FØR set_page_config for at styre Streamlits indbyggede tema)
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

is_dark = st.session_state.dark_mode

# Mobil opsætning med dynamisk tema
st.set_page_config(
    page_title="Sweet Debbie Deals 🇳🇬",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# Farver tilpasset sol vs. mørke
bg_color = "#111827" if is_dark else "#ffffff"
text_color = "#f9fafb" if is_dark else "#111827"
card_bg = "#1f2937" if is_dark else "#f9fafb"
border_color = "#374151" if is_dark else "#e5e7eb"
btn_bg = "#374151" if is_dark else "#f3f4f6"
btn_text = "#ffffff" if is_dark else "#111827"

# Fuld og korrekt CSS-styling
st.markdown(f"""
<style>
    /* Global baggrund og tekst */
    .stApp {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}

    /* Tekstfarver overalt */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5,
    label[data-testid="stWidgetLabel"] p,
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label span,
    div[data-testid="stCheckbox"] label p,
    [data-testid="stCaptionContainer"] p,
    .stTabs [data-baseweb="tab"] p {{
        color: {text_color} !important;
        -webkit-text-fill-color: {text_color} !important;
    }}

    /* Tving input-felter og select-bokse */
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"] textarea,
    div[data-baseweb="select"] span,
    input[type="text"], input[type="password"], textarea, div[data-baseweb="select"] > div {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        -webkit-text-fill-color: {text_color} !important;
    }}
    
    div[data-baseweb="input"],
    div[data-baseweb="base-input"],
    div[data-baseweb="select"],
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea {{
        background-color: {card_bg} !important;
        border-color: {border_color} !important;
        color: {text_color} !important;
        border-radius: 8px !important;
    }}

    /* Popover knap styling i lukket tilstand */
    div[data-testid="stPopover"] button, 
    div[data-testid="stPopover"] > div > button {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        -webkit-text-fill-color: {text_color} !important;
        border: 1px solid {border_color} !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100% !important;
    }}
    div[data-testid="stPopover"] button:hover {{
        background-color: {"#4b5563" if is_dark else "#e5e7eb"} !important;
        border-color: {border_color} !important;
    }}

    /* Åbne popover-menuer og bokse (PopoverBody) */
    div[data-baseweb="popover"], 
    div[data-baseweb="popover"] > div, 
    div[data-testid="stPopoverBody"] {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
        border-radius: 8px !important;
    }}

    /* Knapper - fastlåst farve, så de aldrig forsvinder */
    .stButton button, .stButton button:focus, .stButton button:active {{
        background-color: {btn_bg} !important;
        color: {btn_text} !important;
        -webkit-text-fill-color: {btn_text} !important;
        border: 1px solid {border_color} !important;
        font-weight: 600 !important;
        outline: none !important;
        box-shadow: none !important;
    }}
    .stButton button:hover {{
        background-color: {"#4b5563" if is_dark else "#e5e7eb"} !important;
        color: {btn_text} !important;
        border-color: {border_color} !important;
    }}
    .stButton {{
        min-height: 45px;
    }}
    div[data-testid="stButton"] button {{
        width: 100% !important;
        transition: none !important;
    }}

    /* Produktgrid */
    .grid-img-box {{
        width: 100%;
        height: 125px;
        overflow: hidden;
        border-radius: 8px;
        margin-bottom: 8px;
        background-color: {"#374151" if is_dark else "#f3f4f6"};
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .grid-img-box img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
    }}
    .grid-title {{
        font-size: 0.95rem;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 4px;
        color: {text_color} !important;
        -webkit-text-fill-color: {text_color} !important;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        height: 2.4em;
    }}
    .grid-price {{
        font-size: 1.05rem;
        font-weight: 800;
        color: {"#4ade80" if is_dark else "#16a34a"};
        margin-bottom: 4px;
    }}

    /* Badges */
    .member-badge {{
        display: inline-block;
        background-color: {"#064e3b" if is_dark else "#dcfce7"};
        color: {"#6ee7b7" if is_dark else "#15803d"} !important;
        -webkit-text-fill-color: {"#6ee7b7" if is_dark else "#15803d"} !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.9rem;
        margin-bottom: 8px;
        border: 1px solid {"#047857" if is_dark else "#bbf7d0"};
    }}
    .referral-badge {{
        display: inline-block;
        background-color: {"#451a03" if is_dark else "#ffedd5"};
        color: {"#fdba74" if is_dark else "#c2410c"} !important;
        -webkit-text-fill-color: {"#fdba74" if is_dark else "#c2410c"} !important;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 700;
        border: 1px solid {"#9a3412" if is_dark else "#fed7aa"};
        margin-bottom: 6px;
    }}
    .status-light-red {{
        background-color: {"#450a0a" if is_dark else "#fee2e2"};
        color: {"#fca5a5" if is_dark else "#b91c1c"} !important;
        -webkit-text-fill-color: {"#fca5a5" if is_dark else "#b91c1c"} !important;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: bold;
        border: 1px solid {"#991b1b" if is_dark else "#fecaca"};
        display: inline-block;
        margin-bottom: 6px;
    }}
    .status-light-green {{
        background-color: {"#064e3b" if is_dark else "#dcfce7"};
        color: {"#6ee7b7" if is_dark else "#15803d"} !important;
        -webkit-text-fill-color: {"#6ee7b7" if is_dark else "#15803d"} !important;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: bold;
        border: 1px solid {"#047857" if is_dark else "#bbf7d0"};
        display: inline-block;
        margin-bottom: 6px;
    }}

    /* Footer & Disclaimer */
    .disclaimer-box {{
        font-size: 0.8rem;
        background-color: {card_bg};
        color: {text_color} !important;
        -webkit-text-fill-color: {text_color} !important;
        opacity: 0.85;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid {border_color};
        margin-top: 25px;
    }}
</style>
""", unsafe_allow_html=True)

# Supabase forbindelse
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# OpenAI klient
@st.cache_resource
def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY", None)
    if api_key:
        return OpenAI(api_key=api_key)
    return None

openai_client = get_openai_client()

# Hjælpefunktioner
def make_slug(name: str) -> str:
    clean = re.sub(r'[^a-zA-Z0-9\s-]', '', name).strip().lower()
    return re.sub(r'[\s-]+', '-', clean)

def generate_member_code(prefix: str) -> str:
    num = random.randint(1000, 9999)
    return f"{prefix}-{num}"

def convert_to_base64_img(uploaded_file, target_size=(500, 375)):
    try:
        img = Image.open(uploaded_file)
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75, optimize=True)
        encoded = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{encoded}"
    except Exception:
        return None

def make_wa_link(phone: str, message: str) -> str:
    clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    if clean_phone.startswith("0"):
        clean_phone = "234" + clean_phone[1:]
    return f"https://wa.me/{clean_phone}?text={urllib.parse.quote(message)}"

def generate_qr(url: str) -> bytes:
    qr = qrcode.make(url)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def calculate_hours_left(expires_at_str: str) -> int:
    try:
        clean_str = expires_at_str.replace("Z", "+00:00")
        exp_time = datetime.fromisoformat(clean_str)
        now_time = datetime.now(timezone.utc)
        diff = exp_time - now_time
        return max(0, int(diff.total_seconds() // 3600))
    except Exception:
        return 48

def get_billing_status(valid_until_str: str, is_paid: bool):
    if not is_paid or not valid_until_str:
        return False, "🔴 UNPAID / NOT REGISTERED", 0
    try:
        clean_str = valid_until_str.replace("Z", "+00:00")
        valid_until = datetime.fromisoformat(clean_str)
        now_time = datetime.now(timezone.utc)
        diff = valid_until - now_time
        days_left = int(diff.total_seconds() // 86400)
        if diff.total_seconds() > 0:
            return True, f"🟢 ACTIVE ({days_left}d left)", days_left
        else:
            return False, "🔴 EXPIRED (Time Over)", 0
    except Exception:
        return False, "🔴 STATUS UNKNOWN", 0

def generate_ai_ad_copy(product_name: str, price_val: int, shop_name: str, market_area: str, tone_style: str) -> str:
    if not openai_client:
        if "Pidgin" in tone_style:
            return f"🔥 Omo! Sweet deal don land for {market_area}! Quality {product_name} now going for NGN {price_val:,}. Chat me sharp on WhatsApp before stock finish!"
        return f"✨ Premium quality {product_name} now available at {shop_name} ({market_area}) for only NGN {price_val:,}! Send a WhatsApp message to order."
    
    prompt = (
        f"You are an expert market copywriter in Lagos, Nigeria for 'Sweet Debbie Deals'.\n"
        f"Write a short, high-converting ad description (max 3 sentences).\n"
        f"Product: {product_name}\n"
        f"Price: NGN {price_val:,}\n"
        f"Store: {shop_name}\n"
        f"Area: {market_area}\n"
        f"Style: {tone_style}\n"
        f"Output ONLY the text."
    )
    try:
        response = openai_client.chat.completions.create(
            model="gpt-6-luna",
            messages=[
                {"role": "system", "content": "You write engaging marketplace ad copy for Lagos traders."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return f"🔥 Better deal on {product_name} at {shop_name} ({market_area}) for NGN {price_val:,}! Chat sharp on WhatsApp before e finish!"

def render_broadcast_alerts(target: str):
    try:
        notices = supabase.table("broadcast_messages").select("*").eq("is_active", True).in_("target_audience", [target, "All"]).order("id", desc=True).execute().data or []
        for n in notices:
            st.info(f"**{n['notice_type']} — {n['title']}**\n\n{n['message']}")
    except Exception:
        pass

# URL parametre & Session State
query_params = st.query_params
active_shop_slug = query_params.get("shop", None)

if "current_view" not in st.session_state:
    st.session_state.current_view = "🛒 Browse Deals"

if st.session_state.get("go_to_deals", False):
    st.session_state.current_view = "🛒 Browse Deals"
    st.session_state.go_to_deals = False

if "logged_shop" not in st.session_state:
    st.session_state.logged_shop = None

if "logged_courier" not in st.session_state:
    st.session_state.logged_courier = None

if "logged_customer" not in st.session_state:
    st.session_state.logged_customer = None

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# Session state til popover filtre
if "sel_area" not in st.session_state:
    st.session_state.sel_area = "All Areas"
if "sel_cat" not in st.session_state:
    st.session_state.sel_cat = "All Categories"

# HEADER MED STABIL TEMA-KNAP
st.markdown("<h2 style='margin-bottom: 0;'>🛍️ Sweet Debbie Deals</h2>", unsafe_allow_html=True)
st.caption("🇳🇬 Lagos Local Market • *Powered by AI*")

current_label = "☀️ Switch to Day Mode" if st.session_state.dark_mode else "🌙 Night Mode"
if st.button(current_label, key="theme_toggle_btn"):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

st.markdown("---")

# Navigationsmenu
views = ["🛒 Browse Deals", "🎁 Customer Prizes & Referrals", "🏪 Store Owner Admin", "🛵 Courier / Dispatch", "💬 Support", "🛡️ Platform Admin"]
st.radio("Nav", views, key="current_view", horizontal=True, label_visibility="collapsed")

# ====================================================
# MODAL TIL DETALJEVISNING
# ====================================================
@st.dialog("Product Details & Order")
def show_offer_modal(item):
    if item.get("img_src"):
        st.image(item["img_src"], use_container_width=True)
    st.markdown(f"### {item['product']}")
    st.markdown(f"**Price: ₦{item['price']:,}**")
    st.write(item.get("description", ""))
    
    hours_left = calculate_hours_left(item["expires_at"])
    st.caption(f"🏪 **{item['shop']}** ({item['category']}) • ⏳ Expires in {hours_left}h")
    
    pickup_loc = item.get("location_note") or f"{item['shop']}, {item['area']}"
    if item.get("is_mobile"):
        st.info(f"📍 **Mobile Stall Today:** {pickup_loc}")
    else:
        st.caption(f"📍 Address: {pickup_loc}")
        
    st.markdown("---")
    
    wa_msg = f"Hello {item['shop']}! I saw *{item['product']}* (₦{item['price']:,}) on Sweet Debbie Deals. Is it available?"
    wa_url = make_wa_link(item["phone"], wa_msg)
    st.link_button("💬 Order Directly via WhatsApp", wa_url, use_container_width=True)
    
    st.markdown("#### 🛵 Or Order with Dispatch Delivery")
    with st.form(f"modal_order_form_{item['id']}"):
        cust_name = st.text_input("Your Full Name *", placeholder="e.g. Tunde Bakare")
        cust_phone = st.text_input("Your Phone (WhatsApp) *", placeholder="080...")
        cust_area = st.selectbox("Your Neighborhood *", ["Yaba / Sabo", "Ikeja / Allen", "Surulere", "Victoria Island / Lekki", "Other"])
        cust_addr = st.text_area("Full Address & Nearby Landmark *")
        st.markdown(f"**Total to Pay (Item + Delivery):** ₦{item['price'] + 1500:,}")
        
        c_consent = st.checkbox("I agree to terms: Platform acts solely as a discovery intermediary (NDPA Consent).", value=True)
        if st.form_submit_button("🚀 Confirm Dispatch Delivery", type="primary", use_container_width=True):
            if not cust_name or not cust_phone or not cust_addr or not c_consent:
                st.error("Please fill all required delivery details and accept terms.")
            else:
                new_order = {
                    "offer_id": item["id"], "product": item["product"], "shop": item["shop"],
                    "shop_phone": item["phone"], "pickup_location": pickup_loc,
                    "customer_name": cust_name.strip(), "customer_phone": cust_phone.strip(),
                    "customer_area": cust_area, "delivery_address": cust_addr.strip(),
                    "item_price": item["price"], "delivery_fee": 1500,
                    "rider_payout": 1350, "platform_fee": 150, "status": "pending"
                }
                supabase.table("orders").insert(new_order).execute()
                st.success("✅ Order placed! A verified rider will contact you.")

# ====================================================
# VISNING 1: KUNDEPORTAL
# ====================================================
if st.session_state.current_view == "🛒 Browse Deals":
    render_broadcast_alerts("All")
    
    if active_shop_slug:
        shop_info = supabase.table("shops").select("*").eq("slug", active_shop_slug).execute()
        shop_name = shop_info.data[0]["name"] if shop_info.data else active_shop_slug
        st.info(f"📍 Viewing deals directly from **{shop_name}**")
        if st.button("⬅️ Show all deals in Lagos"):
            st.query_params.clear()
            st.rerun()
            
        now_iso = datetime.now(timezone.utc).isoformat()
        res = supabase.table("offers").select("*").eq("shop", shop_name).gt("expires_at", now_iso).order("id", desc=True).execute()
        offers = res.data or []
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<div style='font-size: 0.85rem; font-weight: bold; color: {text_color}; margin-bottom: 4px;'>Market / Area</div>", unsafe_allow_html=True)
            with st.popover(f"📍 {st.session_state.sel_area}", use_container_width=True):
                areas = ["All Areas", "Yaba Market", "Ikeja (Computer Village)", "Surulere", "Balogun Market", "Lekki"]
                for a in areas:
                    if st.button(a, key=f"area_btn_{a}", use_container_width=True):
                        st.session_state.sel_area = a
                        st.rerun()
        with c2:
            st.markdown(f"<div style='font-size: 0.85rem; font-weight: bold; color: {text_color}; margin-bottom: 4px;'>Category</div>", unsafe_allow_html=True)
            with st.popover(f"📂 {st.session_state.sel_cat}", use_container_width=True):
                cats = ["All Categories", "Groceries & Food", "Electronics", "Fashion & Clothing", "Home & Living"]
                for c in cats:
                    if st.button(c, key=f"cat_btn_{c}", use_container_width=True):
                        st.session_state.sel_cat = c
                        st.rerun()

        st.markdown("---")
        now_iso = datetime.now(timezone.utc).isoformat()
        query = supabase.table("offers").select("*").gt("expires_at", now_iso).order("id", desc=True)
        if st.session_state.sel_area != "All Areas":
            query = query.eq("area", st.session_state.sel_area)
        if st.session_state.sel_cat != "All Categories":
            query = query.eq("category", st.session_state.sel_cat)
        res = query.execute()
        offers = res.data or []

    if not offers:
        st.info("No active deals found right now. Check back soon!")
    else:
        for i in range(0, len(offers), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(offers):
                    deal = offers[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            if deal.get("img_src"):
                                st.markdown(f'<div class="grid-img-box"><img src="{deal["img_src"]}"></div>', unsafe_allow_html=True)
                            else:
                                st.markdown('<div class="grid-img-box" style="font-size:1.5rem;">🛍️</div>', unsafe_allow_html=True)
                                
                            st.markdown(f'<div class="grid-title">{deal["product"]}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="grid-price">₦{deal["price"]:,}</div>', unsafe_allow_html=True)
                            st.caption(f"🏪 {deal['shop']}")
                            
                            status = deal.get("status", "active")
                            if status == "sold_out":
                                st.error("⛔ Sold Out")
                            elif status == "back_tomorrow":
                                st.warning("⏳ Back Tomorrow")
                            else:
                                if st.button("👀 View Deal", key=f"view_btn_{deal['id']}", use_container_width=True):
                                    show_offer_modal(deal)

# ====================================================
# VISNING 2: KUNDE PRÆMIER & HENVISNING
# ====================================================
elif st.session_state.current_view == "🎁 Customer Prizes & Referrals":
    st.markdown("### 🎁 Customer Cash Prizes & Referrals")
    st.caption("Refer friends, family, or market stalls and win cash prizes in our weekly lucky draw!")
    
    render_broadcast_alerts("All")

    if not st.session_state.logged_customer:
        cust_auth = st.radio("Choose action:", ["🔑 Customer Log In", "📝 Register New Customer Profile"], horizontal=True)
        
        if cust_auth == "🔑 Customer Log In":
            with st.container(border=True):
                c_phone = st.text_input("WhatsApp / Phone Number", placeholder="080...")
                c_pin = st.text_input("4-Digit PIN", type="password", placeholder="1234")
                if st.button("Log In to Customer Portal", type="primary", use_container_width=True):
                    res = supabase.table("customers").select("*").eq("phone", c_phone.strip()).eq("pin", c_pin.strip()).execute()
                    if res.data:
                        st.session_state.logged_customer = res.data[0]
                        st.success(f"Welcome back, {res.data[0]['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid phone number or PIN.")
        else:
            with st.container(border=True):
                c_name = st.text_input("Full Name (Must match ID) *", placeholder="e.g. Chioma Adebayo")
                c_phone_new = st.text_input("WhatsApp / Phone Number *", placeholder="080...")
                c_pin_new = st.text_input("Create 4-Digit Secret PIN *", type="password", max_chars=4, placeholder="1234")
                c_pin_confirm = st.text_input("Confirm 4-Digit PIN *", type="password", max_chars=4, placeholder="1234")
                c_referred = st.text_input("Referred by? (Enter friend/stall ID, optional)", placeholder="e.g. CUST-1042 or SHOP-1002")
                
                if st.button("🚀 Register Profile & Get Customer ID", type="primary", use_container_width=True):
                    if not c_name or not c_phone_new or not c_pin_new or not c_pin_confirm:
                        st.error("Please fill in all required fields.")
                    elif c_pin_new != c_pin_confirm:
                        st.error("PIN codes do not match! Please check your input.")
                    elif len(c_pin_new) != 4:
                        st.error("PIN must be exactly 4 digits.")
                    else:
                        existing = supabase.table("customers").select("id").eq("phone", c_phone_new.strip()).execute()
                        if existing.data:
                            st.error("Phone number already registered. Please log in.")
                        else:
                            cust_code = generate_member_code("CUST")
                            new_cust = {
                                "name": c_name.strip(),
                                "phone": c_phone_new.strip(),
                                "pin": c_pin_new.strip(),
                                "member_id": cust_code,
                                "referred_by": c_referred.strip().upper() if c_referred else None
                            }
                            ins = supabase.table("customers").insert(new_cust).execute()
                            if ins.data:
                                st.session_state.logged_customer = ins.data[0]
                                st.success("🎉 Profile created successfully!")
                                st.rerun()
    else:
        cust = st.session_state.logged_customer
        c_member_id = cust.get("member_id") or f"CUST-{cust.get('id', 1000)}"
        
        ref_res = supabase.table("customers").select("id").eq("referred_by", c_member_id).execute()
        my_referrals = len(ref_res.data or [])
        total_tickets = 1 + my_referrals

        col_ch1, col_ch2 = st.columns([3, 1])
        with col_ch1:
            st.markdown(f"### 👤 {cust['name']}")
            st.markdown(f'<div class="member-badge">🎟️ Your Customer ID: {c_member_id}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="referral-badge">🤝 Referrals: {my_referrals} friend(s)/stall(s) • 🎟️ Raffle Tickets: <b>{total_tickets}</b></div>', unsafe_allow_html=True)
            st.caption(f"📞 {cust['phone']}")
        with col_ch2:
            if st.button("🚪 Log Out", use_container_width=True):
                st.session_state.logged_customer = None
                st.rerun()

        st.markdown("---")
        st.markdown("#### 💵 Cash Prize & Referral Program")
        st.info(f"💡 **How to win cash:** Share your Customer ID (`{c_member_id}`) with friends or market stalls when they sign up or buy. Every time someone enters your ID, you get **1 extra ticket** in the weekly cash prize lucky draw!")

        share_text = f"Hey! Check out Sweet Debbie Deals for cheap market prices in Lagos. Use my referral ID *{c_member_id}* when you sign up so we both get extra raffle tickets!"
        wa_share_url = f"https://wa.me/?text={urllib.parse.quote(share_text)}"
        st.link_button("📤 Share your ID on WhatsApp with friends", wa_share_url, use_container_width=True)

# ====================================================
# VISNING 3: BUTIKSEJER ADMIN
# ====================================================
elif st.session_state.current_view == "🏪 Store Owner Admin":
    if not st.session_state.logged_shop:
        auth_mode = st.radio("Choose action:", ["🔑 Log In to Existing Store", "📝 Register New Store / Stall"], horizontal=True)
        
        if auth_mode == "🔑 Log In to Existing Store":
            st.markdown("### Store Owner Login")
            with st.container(border=True):
                phone_input = st.text_input("WhatsApp / Phone Number", placeholder="08012345678", value="")
                pin_input = st.text_input("4-Digit PIN", type="password", placeholder="1234", value="")
                if st.button("Log In Now", type="primary", use_container_width=True):
                    clean_phone = phone_input.strip()
                    res = supabase.table("shops").select("*").eq("phone", clean_phone).eq("pin", pin_input.strip()).execute()
                    if res.data:
                        st.session_state.logged_shop = res.data[0]
                        st.success(f"Welcome back, {res.data[0]['name']}!")
                        st.rerun()
                    else:
                        st.error("Incorrect phone number or PIN.")
        else:
            st.markdown("### 📝 Register New Store or Stall")
            with st.container(border=True):
                new_shop_name = st.text_input("Store or Stall Name *", placeholder="e.g. Mama Funke Provisions")
                new_phone = st.text_input("WhatsApp Number *", placeholder="08012345678")
                new_pin = st.text_input("Create 4-Digit Secret PIN *", type="password", max_chars=4, placeholder="4 digits e.g. 2468")
                new_pin_confirm = st.text_input("Confirm 4-Digit PIN *", type="password", max_chars=4, placeholder="4 digits e.g. 2468")
                new_area = st.selectbox("Market / Area *", ["Yaba Market", "Ikeja (Computer Village)", "Surulere", "Balogun Market", "Lekki"])
                new_cat = st.selectbox("Main Category *", ["Groceries & Food", "Electronics", "Fashion & Clothing", "Home & Living"])
                
                referred_code = st.text_input("Referred by another Store or Customer ID? (Optional)", placeholder="e.g. SHOP-1002 or CUST-1042")
                shop_consent = st.checkbox("I accept Platform Terms: Sweet Debbie Deals acts as discovery intermediary.")
                
                if st.button("🚀 Complete Registration & Enter", type="primary", use_container_width=True):
                    if not new_shop_name or not new_phone or not new_pin or not new_pin_confirm:
                        st.error("Please fill all required fields.")
                    elif new_pin != new_pin_confirm:
                        st.error("PIN codes do not match! Please check your input.")
                    elif len(new_pin) != 4:
                        st.error("PIN must be exactly 4 digits.")
                    elif not shop_consent:
                        st.error("Please accept the terms to register.")
                    else:
                        clean_phone = new_phone.strip()
                        existing = supabase.table("shops").select("id").eq("phone", clean_phone).execute()
                        if existing.data:
                            st.error("Phone number already registered. Please log in.")
                        else:
                            unique_slug = f"{make_slug(new_shop_name)}-{clean_phone[-4:]}"
                            new_member_code = generate_member_code("SHOP")
                            clean_ref = referred_code.strip().upper() if referred_code else None
                            
                            shop_record = {
                                "slug": unique_slug, "name": new_shop_name.strip(), "phone": clean_phone,
                                "pin": new_pin.strip(), "area": new_area, "category": new_cat,
                                "member_id": new_member_code, "referred_by": clean_ref
                            }
                            ins = supabase.table("shops").insert(shop_record).execute()
                            if ins.data:
                                st.session_state.logged_shop = ins.data[0]
                                st.rerun()
    else:
        shop = st.session_state.logged_shop
        member_id = shop.get("member_id") or f"SHOP-{1000 + shop.get('id', 1)}"
        
        render_broadcast_alerts("Stores")
        
        ref_count_res = supabase.table("shops").select("id").eq("referred_by", member_id).execute()
        referred_count = len(ref_count_res.data or [])
        
        col_hdr1, col_hdr2 = st.columns([3, 1])
        with col_hdr1:
            st.markdown(f"### 🏪 {shop['name']}")
            st.markdown(f'<div class="member-badge">🎟️ Store ID: {member_id}</div>', unsafe_allow_html=True)
            
            if referred_count >= 5:
                st.markdown(f'<div class="referral-badge" style="background-color: #e8f5e9; color:#1b5e20;">🎯 Referral Target Met: {referred_count}/5 stores referred! (Qualified for Lucky Draw)</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="referral-badge">🤝 Referred Stores: {referred_count}/5 (Refer {5 - referred_count} more for Lucky Draw)</div>', unsafe_allow_html=True)
                
            st.caption(f"📍 {shop['area']} • 📞 {shop['phone']}")
        with col_hdr2:
            if st.button("🚪 Log Out", use_container_width=True):
                st.session_state.logged_shop = None
                st.rerun()

        st.markdown("---")
        st.markdown("#### Your Active Deals")
        my_offers = supabase.table("offers").select("*").eq("shop", shop["name"]).order("id", desc=True).execute().data or []
        
        if not my_offers:
            st.info("No active deals posted yet.")
        else:
            for deal in my_offers:
                with st.container(border=True):
                    st.markdown(f"**{deal['product']}** — ₦{deal['price']:,}")
                    st.caption(f"Status: `{deal.get('status', 'active')}` • Expires in: {calculate_hours_left(deal['expires_at'])}h")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("🟢 In Stock", key=f"s_{deal['id']}"):
                            supabase.table("offers").update({"status": "active"}).eq("id", deal["id"]).execute()
                            st.rerun()
                    with c2:
                        if st.button("⛔ Sold Out", key=f"so_{deal['id']}"):
                            supabase.table("offers").update({"status": "sold_out"}).eq("id", deal["id"]).execute()
                            st.rerun()
                    with c3:
                        if st.button("⏳ Tomorrow", key=f"bt_{deal['id']}"):
                            supabase.table("offers").update({"status": "back_tomorrow"}).eq("id", deal["id"]).execute()
                            st.rerun()
                    if st.button("🗑️ Delete Deal", key=f"del_{deal['id']}", type="secondary"):
                        supabase.table("offers").delete().eq("id", deal["id"]).execute()
                        st.rerun()

        st.markdown("---")
        st.markdown("#### Post a New 48-Hour Deal")
        is_mobile = st.checkbox("This is a mobile stall", value=True)
        location_note = st.text_input("Today's Location / Address *", value="At our stall / market spot")
        product = st.text_input("Product Name *", placeholder="e.g. 5L Power Oil, Nike Air, Original 20W Charger")
        price = st.number_input("Deal Price in Naira (₦) *", min_value=50, value=1000, step=50)
        uploaded_file = st.file_uploader("Photo (Optional)", type=["jpg", "jpeg", "png", "webp"])
        
        st.markdown("##### ✨ AI Ad Copy Generator (GPT-6 Luna)")
        c_tone1, c_tone2 = st.columns([2, 1])
        with c_tone1:
            tone_style = st.selectbox(
                "Select Tone & Language:", 
                ["Nigerian Pidgin (High Conversion)", "Standard English (Clean & Formal)", "Urgent Flash Deal (FOMO 48h)"]
            )
        with c_tone2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🪄 Generate Text", use_container_width=True):
                if not product:
                    st.warning("Please enter product name first!")
                else:
                    with st.spinner("GPT-6 Luna is generating your ad..."):
                        ai_result = generate_ai_ad_copy(product, int(price), shop["name"], shop["area"], tone_style)
                        st.session_state["ai_ad_copy"] = ai_result

        default_ad_text = st.session_state.get(
            "ai_ad_copy", 
            f"🔥 Quality {product} now available at {shop['name']} for only NGN {price:,}! Limited stock today in {shop['area']}."
        )
        desc = st.text_area("Ad Description (Review or edit before posting):", value=default_ad_text, height=85)
        
        if st.button("🚀 Publish Deal Now", type="primary", use_container_width=True):
            if not product:
                st.error("Please enter a product name.")
            else:
                final_img = convert_to_base64_img(uploaded_file) if uploaded_file else None
                new_data = {
                    "shop": shop["name"], "category": shop["category"], "area": shop["area"],
                    "is_mobile": is_mobile, "location_note": location_note, "phone": shop["phone"],
                    "product": product, "price": int(price), "description": desc,
                    "img_src": final_img, "status": "active"
                }
                supabase.table("offers").insert(new_data).execute()
                if "ai_ad_copy" in st.session_state:
                    del st.session_state["ai_ad_copy"]
                st.session_state.go_to_deals = True
                st.rerun()

        st.markdown("---")
        st.markdown("### Store QR Code")
        direct_shop_url = f"https://lagos-commerce-pzru6e8tsftfmt72gbjnhz.streamlit.app/?shop={shop['slug']}"
        st.image(generate_qr(direct_shop_url), width=160, caption=f"Scan for {shop['name']}")

# ====================================================
# VISNING 4: BUDE & KURÉR
# ====================================================
elif st.session_state.current_view == "🛵 Courier / Dispatch":
    if not st.session_state.logged_courier:
        courier_auth = st.radio("Rider Action:", ["🔑 Rider Log In", "📝 Register New Rider / Courier"], horizontal=True)
        
        if courier_auth == "🔑 Rider Log In":
            st.markdown("### 🛵 Dispatch Rider Login")
            with st.container(border=True):
                r_phone = st.text_input("Phone Number", placeholder="080...")
                r_pin = st.text_input("4-Digit PIN", type="password", placeholder="1234")
                if st.button("Rider Log In", type="primary", use_container_width=True):
                    res = supabase.table("couriers").select("*").eq("phone", r_phone.strip()).eq("pin", r_pin.strip()).execute()
                    if res.data:
                        st.session_state.logged_courier = res.data[0]
                        st.success(f"Welcome back, {res.data[0]['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid phone or PIN.")
        else:
            st.markdown("### 📝 Register as Verified Dispatch Rider")
            st.caption("Upload a valid government ID for local verification.")
            with st.container(border=True):
                r_name = st.text_input("Rider / Company Full Name *", placeholder="e.g. Ibrahim Babatunde")
                r_phone_new = st.text_input("Phone Number (WhatsApp) *", placeholder="080...")
                r_pin_new = st.text_input("Create 4-Digit PIN *", type="password", max_chars=4, placeholder="1234")
                r_pin_confirm = st.text_input("Confirm 4-Digit PIN *", type="password", max_chars=4, placeholder="1234")
                r_area = st.selectbox("Primary Operating Area", ["Yaba / Sabo", "Ikeja / Maryland", "Surulere", "Island / Lekki", "All Lagos"])
                vehicle = st.selectbox("Vehicle Type", ["Motorcycle (Okada)", "Bicycle", "Van / Car"])
                
                st.markdown("**Upload Government ID (NIN, Voter's Card, or Driver's License) ***")
                id_file = st.file_uploader("Upload clear photo of ID", type=["jpg", "jpeg", "png", "webp"], key="id_uploader")
                if id_file:
                    st.image(id_file, width=220, caption="Uploaded ID Preview")
                
                rider_consent = st.checkbox("I agree to terms: Riders operate as independent agents.")
                
                if st.button("🚀 Submit Profile for Verification", type="primary", use_container_width=True):
                    if not r_name or not r_phone_new or not r_pin_new or not r_pin_confirm or not id_file:
                        st.error("Please fill all details, upload ID, and set PIN.")
                    elif r_pin_new != r_pin_confirm:
                        st.error("PIN codes do not match! Please check your input.")
                    elif len(r_pin_new) != 4:
                        st.error("PIN must be exactly 4 digits.")
                    elif not rider_consent:
                        st.error("Please accept the platform terms.")
                    else:
                        id_base64 = convert_to_base64_img(id_file, target_size=(600, 400))
                        new_rider_code = generate_member_code("RIDER")
                        
                        r_data = {
                            "name": r_name.strip(), "phone": r_phone_new.strip(),
                            "pin": r_pin_new.strip(), "area": r_area, "vehicle": vehicle,
                            "id_card_img": id_base64, "is_approved": False,
                            "member_id": new_rider_code
                        }
                        ins = supabase.table("couriers").insert(r_data).execute()
                        if ins.data:
                            st.session_state.logged_courier = ins.data[0]
                            st.rerun()
    else:
        rider_res = supabase.table("couriers").select("*").eq("id", st.session_state.logged_courier["id"]).execute()
        rider = rider_res.data[0] if rider_res.data else st.session_state.logged_courier
        r_member_id = rider.get("member_id") or f"RIDER-{2000 + rider.get('id', 1)}"
        
        render_broadcast_alerts("Couriers")
        
        c_hdr1, c_hdr2 = st.columns([3, 1])
        with c_hdr1:
            st.markdown(f"### 🛵 Rider: {rider['name']}")
            st.markdown(f'<div class="member-badge">🎟️ Rider ID: {r_member_id}</div>', unsafe_allow_html=True)
            st.caption(f"📍 Area: {rider['area']} • 🛵 {rider.get('vehicle', 'Motorcycle')}")
        with c_hdr2:
            if st.button("🚪 Log Out", key="rider_logout", use_container_width=True):
                st.session_state.logged_courier = None
                st.rerun()

        st.markdown("---")
        
        if not rider.get("is_approved", False):
            st.warning("⏳ **Account Under Review (Pending Verification)**")
            st.info("Your ID document has been submitted. Our local coordinator must verify your identity before you can take delivery jobs.")
        else:
            st.success("🛡️ **Verified Dispatch Rider (Approved)**")
            
            st.markdown("#### 📦 Your Accepted Deliveries")
            my_jobs = supabase.table("orders").select("*").eq("courier_id", rider["id"]).neq("status", "delivered").order("id", desc=True).execute().data or []
            
            if not my_jobs:
                st.info("No active delivery runs right now.")
            else:
                for job in my_jobs:
                    with st.container(border=True):
                        st.markdown(f"**Order #{job['id']} — {job['product']}**")
                        st.markdown(f"🏪 **Pickup:** {job['shop']} — 📞 `{job['shop_phone']}`")
                        st.markdown(f"🎯 **Drop-off:** {job['customer_name']} — 📞 `{job['customer_phone']}`")
                        st.markdown(f"📍 **Address:** {job['delivery_address']}")
                        st.markdown(f"💵 **Collect:** ₦{job['item_price'] + job['delivery_fee']:,} *(Your pay: ₦{job['rider_payout']:,})*")
                        
                        wa_pickup = make_wa_link(job['shop_phone'], f"Hello {job['shop']}, rider {rider['name']} picking up Order #{job['id']}.")
                        wa_cust = make_wa_link(job['customer_phone'], f"Hello {job['customer_name']}, rider {rider['name']} delivering your {job['product']}.")
                        
                        cw1, cw2 = st.columns(2)
                        with cw1:
                            st.link_button("💬 WA Shop", wa_pickup, use_container_width=True)
                        with cw2:
                            st.link_button("💬 WA Customer", wa_cust, use_container_width=True)
                            
                        cb1, cb2 = st.columns(2)
                        with cb1:
                            if job["status"] == "accepted":
                                if st.button("📦 Mark Picked Up", key=f"pk_{job['id']}", use_container_width=True):
                                    supabase.table("orders").update({"status": "picked_up"}).eq("id", job["id"]).execute()
                                    st.rerun()
                        with cb2:
                            if st.button("✅ Mark Delivered", key=f"dl_{job['id']}", type="primary", use_container_width=True):
                                supabase.table("orders").update({"status": "delivered"}).eq("id", job["id"]).execute()
                                st.rerun()

            st.markdown("---")
            st.markdown("#### ⚡ Available Delivery Jobs Nearby")
            open_jobs = supabase.table("orders").select("*").eq("status", "pending").order("id", desc=True).execute().data or []
            if not open_jobs:
                st.write("No pending delivery jobs right now.")
            else:
                for ojob in open_jobs:
                    with st.container(border=True):
                        st.markdown(f"**{ojob['product']}** (₦{ojob['item_price']:,})")
                        st.markdown(f"📍 **Pickup:** {ojob['shop']} — {ojob['pickup_location']}")
                        st.markdown(f"🎯 **Drop-off Area:** {ojob['customer_area']}")
                        st.markdown(f"💵 **Your Payout:** **₦{ojob['rider_payout']:,}**")
                        if st.button("🛵 Accept Job", key=f"acc_{ojob['id']}", type="primary", use_container_width=True):
                            supabase.table("orders").update({
                                "status": "accepted", "courier_id": rider["id"], "courier_name": rider["name"]
                            }).eq("id", ojob["id"]).execute()
                            st.rerun()

# ====================================================
# VISNING 5: BRUGER-SUPPORT
# ====================================================
elif st.session_state.current_view == "💬 Support":
    st.markdown("### 💬 User Support & Helpdesk")
    st.caption("Need help, billing inquiry, or forgotten PIN? Send a message to our coordinator team.")
    
    default_name = ""
    default_phone = ""
    user_category = "Customer"
    
    if st.session_state.logged_shop:
        default_name = st.session_state.logged_shop["name"]
        default_phone = st.session_state.logged_shop["phone"]
        user_category = "Store Owner"
    elif st.session_state.logged_courier:
        default_name = st.session_state.logged_courier["name"]
        default_phone = st.session_state.logged_courier["phone"]
        user_category = "Courier / Rider"
    elif st.session_state.logged_customer:
        default_name = st.session_state.logged_customer["name"]
        default_phone = st.session_state.logged_customer["phone"]
        user_category = "Customer"
        
    with st.container(border=True):
        u_name = st.text_input("Your Name / Business Name *", value=default_name)
        u_phone = st.text_input("WhatsApp / Phone Number *", value=default_phone)
        u_role = st.selectbox("I am a:", ["Store Owner", "Courier / Rider", "Customer", "Other"], index=["Store Owner", "Courier / Rider", "Customer", "Other"].index(user_category) if user_category in ["Store Owner", "Courier / Rider", "Customer"] else 0)
        u_subject = st.selectbox("Topic / Subject *", ["Payment & Subscription Inquiry", "Referral Program & Raffle", "Forgotten PIN", "Account Verification", "Order Issue", "General Suggestion"])
        u_message = st.text_area("Your Message / Question *", placeholder="Describe your inquiry...")
        
        if st.button("📨 Send Message to Admin", type="primary", use_container_width=True):
            if not u_name or not u_phone or not u_message:
                st.error("Please fill in your name, phone, and message.")
            else:
                msg_data = {
                    "sender_name": u_name.strip(),
                    "sender_phone": u_phone.strip(),
                    "user_type": u_role,
                    "subject": u_subject,
                    "message": u_message.strip(),
                    "status": "open"
                }
                supabase.table("support_messages").insert(msg_data).execute()
                st.success("✅ Message sent to the admin team! We will contact you on WhatsApp shortly.")

# ====================================================
# VISNING 6: PLATFORM SUPER ADMIN
# ====================================================
elif st.session_state.current_view == "🛡️ Platform Admin":
    st.markdown("### 🛡️ Platform Super Admin")
    
    if not st.session_state.admin_logged_in:
        admin_pass = st.text_input("Admin PIN", type="password", placeholder="Master key")
        if st.button("Unlock Admin Panel", type="primary"):
            # Sikkerhedstjek mod st.secrets i stedet for hårdkodet tekst
            master_admin_pin = st.secrets.get("ADMIN_PASSWORD", "lagos2026")
            if admin_pass == master_admin_pin:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Incorrect Admin PIN!")
    else:
        c_a1, c_a2 = st.columns([3, 1])
        with c_a1:
            st.success("🔓 Super Admin Mode Active")
        with c_a2:
            if st.button("🔒 Lock Admin"):
                st.session_state.admin_logged_in = False
                st.rerun()

        st.markdown("---")

        try:
            total_cust_count = len(supabase.table("customers").select("id", count="exact").execute().data or [])
        except Exception:
            total_cust_count = 0
            
        try:
            total_shops_count = len(supabase.table("shops").select("id", count="exact").execute().data or [])
        except Exception:
            total_shops_count = 0
            
        try:
            total_couriers_count = len(supabase.table("couriers").select("id", count="exact").execute().data or [])
        except Exception:
            total_couriers_count = 0

        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric("👥 Total Customers", total_cust_count)
        with m_col2:
            st.metric("🏪 Total Stores", total_shops_count)
        with m_col3:
            st.metric("🛵 Total Riders", total_couriers_count)

        st.markdown("---")

        admin_tabs = st.tabs(["📢 Broadcasts", "🤝 Customer Cash Raffle", "🚦 Subscriptions", "🎉 Lucky Draw (Stores)", "📬 Messages", "🛵 Riders", "🏪 Stores", "👤 Customers", "📦 Orders", "🔥 Offers"])

        # --- FANE 0: BROADCASTS ---
        with admin_tabs[0]:
            st.markdown("#### 📢 Platform Broadcast Messages & Reminders")
            with st.expander("➕ Create New Broadcast Message"):
                b_target = st.selectbox("Send To Audience:", ["Stores", "Couriers", "All"])
                b_type = st.selectbox("Notice Type / Badge:", ["🎉 Event / Raffle", "⏳ Referral Reminder", "⚠️ Important Notice", "📢 Platform Update"])
                b_title = st.text_input("Notice Title *", placeholder="e.g. ₦50,000 Friday Market Raffle Draw!")
                b_body = st.text_area("Notice Message *", placeholder="e.g. Remember to refer 5 stores with your ID before Friday 6PM!")
                
                if st.button("🚀 Publish Broadcast Alert", type="primary"):
                    if not b_title or not b_body:
                        st.error("Please fill in title and message.")
                    else:
                        new_alert = {
                            "target_audience": b_target,
                            "notice_type": b_type,
                            "title": b_title.strip(),
                            "message": b_body.strip(),
                            "is_active": True
                        }
                        supabase.table("broadcast_messages").insert(new_alert).execute()
                        st.success("Broadcast message published live!")
                        st.rerun()

            st.markdown("##### Active Broadcasts")
            broadcasts = supabase.table("broadcast_messages").select("*").order("id", desc=True).execute().data or []
            if not broadcasts:
                st.info("No active broadcast messages.")
            else:
                for b in broadcasts:
                    with st.container(border=True):
                        col_b1, col_b2 = st.columns([3, 1])
                        with col_b1:
                            st.markdown(f"**{b['notice_type']} — {b['title']}** (Audience: `{b['target_audience']}`)")
                            st.write(b["message"])
                            st.caption(f"Created: {b['created_at'][:10]} • Status: **{'🟢 Active' if b['is_active'] else '⚪ Disabled'}**")
                        with col_b2:
                            if b["is_active"]:
                                if st.button("Turn Off", key=f"dis_{b['id']}", use_container_width=True):
                                    supabase.table("broadcast_messages").update({"is_active": False}).eq("id", b["id"]).execute()
                                    st.rerun()
                            else:
                                if st.button("Turn On", key=f"ena_{b['id']}", use_container_width=True):
                                    supabase.table("broadcast_messages").update({"is_active": True}).eq("id", b["id"]).execute()
                                    st.rerun()
                            if st.button("🗑️ Delete", key=f"del_bc_{b['id']}", type="secondary", use_container_width=True):
                                supabase.table("broadcast_messages").delete().eq("id", b["id"]).execute()
                                st.rerun()

        # --- FANE 1: CUSTOMER CASH RAFFLE ---
        with admin_tabs[1]:
            st.markdown("#### 🎁 Customer Cash Prize Raffle (Weighted)")
            st.caption("The more friends or stores referred, the more tickets the customer has in the pool!")
            
            all_customers = supabase.table("customers").select("*").execute().data or []
            all_shops_for_ref = supabase.table("shops").select("*").execute().data or []
            
            customer_pool = []
            for c in all_customers:
                c_id = c.get("member_id") or f"CUST-{c.get('id', 1000)}"
                cust_refs = len([x for x in all_customers if x.get("referred_by") == c_id])
                shop_refs = len([x for x in all_shops_for_ref if x.get("referred_by") == c_id])
                total_refs = cust_refs + shop_refs
                tickets = 1 + total_refs
                
                customer_pool.append({
                    "name": c["name"],
                    "phone": c["phone"],
                    "id": c_id,
                    "referrals": total_refs,
                    "tickets": tickets
                })
            
            total_tickets_sum = sum([item["tickets"] for item in customer_pool])
            st.metric("👥 Total Registered Customers", len(customer_pool))
            st.metric("🎟️ Total Tickets in Pool (Weighted)", total_tickets_sum)
            
            st.markdown("---")
            if st.button("🎲 Draw Cash Prize Winner Among Customers", type="primary", use_container_width=True):
                if not customer_pool:
                    st.warning("No customers registered yet.")
                else:
                    weighted_list = []
                    for item in customer_pool:
                        for _ in range(item["tickets"]):
                            weighted_list.append(item)
                    
                    winner = random.choice(weighted_list)
                    st.balloons()
                    st.success(f"🏆 **CASH WINNER FOUND!**\n\n**{winner['name']}**\n\n🎟️ Customer ID: `{winner['id']}`\n🤝 Referrals: **{winner['referrals']}** (Tickets in play: {winner['tickets']})\n📞 Phone: `{winner['phone']}`")
                    win_wa = make_wa_link(winner['phone'], f"Congratulations {winner['name']}! Your ID ({winner['id']}) has won the Sweet Debbie Deals Customer Cash Prize!")
                    st.link_button("💬 Send Prize Message on WhatsApp", win_wa, use_container_width=True)

            st.markdown("##### Customer Tickets Overview")
            for item in customer_pool:
                with st.container(border=True):
                    st.markdown(f"**{item['name']}** (`{item['id']}`) — 📞 `{item['phone']}`")
                    st.write(f"Referrals: **{item['referrals']}** • Total tickets in pool: **{item['tickets']} pcs.**")

        # --- FANE 2: ABONNEMENTER ---
        with admin_tabs[2]:
            st.markdown("#### 🚦 Subscription Status & Fee Collection")
            bills = supabase.table("billing_records").select("*").order("id", desc=True).execute().data or []
            
            active_count = 0
            expired_count = 0
            for b in bills:
                is_active, _, _ = get_billing_status(b.get("valid_until"), b.get("is_paid", False))
                if is_active:
                    active_count += 1
                else:
                    expired_count += 1
                    
            m1, m2 = st.columns(2)
            with m1:
                st.metric("🟢 Active Subscriptions", f"{active_count}")
            with m2:
                st.metric("🔴 Expired / Unpaid", f"{expired_count}")
                
            st.markdown("---")
            with st.expander("➕ Register New Subscription / Fee"):
                all_couriers = supabase.table("couriers").select("*").execute().data or []
                target_payer_type = st.radio("Bill to:", ["Store", "Courier"], horizontal=True)
                
                all_shops_list = supabase.table("shops").select("*").execute().data or []
                if target_payer_type == "Store" and all_shops_list:
                    shop_names = [f"{s.get('name', 'Shop')} ({s.get('member_id', '')})" for s in all_shops_list]
                    sel_s_idx = st.selectbox("Select Store:", range(len(shop_names)), format_func=lambda x: shop_names[x])
                    chosen_payer = all_shops_list[sel_s_idx]
                elif target_payer_type == "Courier" and all_couriers:
                    c_names = [f"{c.get('name', 'Rider')} ({c.get('member_id', '')})" for c in all_couriers]
                    sel_c_idx = st.selectbox("Select Courier:", range(len(c_names)), format_func=lambda x: c_names[x])
                    chosen_payer = all_couriers[sel_c_idx]
                else:
                    chosen_payer = None
                    st.info("No records found.")
                    
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    period_choice = st.selectbox("Period Duration:", ["Weekly (7 Days)", "Monthly (30 Days)"])
                with col_p2:
                    default_amount = 1000 if "Weekly" in period_choice else 3500
                    fee_val = st.number_input("Fee in Naira (₦):", min_value=100, value=default_amount, step=100)
                    
                fee_title = st.text_input("Fee Description:", value=f"{'Weekly' if 'Weekly' in period_choice else 'Monthly'} Stall Access Fee")
                
                if st.button("📝 Create Subscription Record", type="primary"):
                    if chosen_payer:
                        new_bill = {
                            "payer_type": target_payer_type,
                            "payer_name": chosen_payer.get("name", "Unknown"),
                            "payer_phone": chosen_payer.get("phone", ""),
                            "member_id": chosen_payer.get("member_id"),
                            "fee_description": fee_title,
                            "amount": int(fee_val),
                            "period_type": "Weekly" if "Weekly" in period_choice else "Monthly",
                            "is_paid": False
                        }
                        supabase.table("billing_records").insert(new_bill).execute()
                        st.success(f"Subscription recorded for {chosen_payer.get('name')}!")
                        st.rerun()

            st.markdown("#### Live Subscriptions & Payment Records")
            if not bills:
                st.info("No subscription records created yet.")
            else:
                for b in bills:
                    is_active, status_label, _ = get_billing_status(b.get("valid_until"), b.get("is_paid", False))
                    period = b.get("period_type", "Weekly")
                    
                    with st.container(border=True):
                        cb_col1, cb_col2 = st.columns([3, 2])
                        with cb_col1:
                            if is_active:
                                st.markdown(f'<div class="status-light-green">{status_label}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="status-light-red">{status_label}</div>', unsafe_allow_html=True)
                                
                            st.markdown(f"**{b['payer_name']}** ({b.get('member_id', 'N/A')}) — `{b['payer_type']}`")
                            st.markdown(f"📌 **{b['fee_description']}** ({period}) — **₦{b['amount']:,}**")
                            st.caption(f"Phone: `{b['payer_phone']}` • Valid until: `{b.get('valid_until', 'Not started')[:10]}`")
                                
                        with cb_col2:
                            if not is_active:
                                days_to_add = 7 if period == "Weekly" else 30
                                btn_label = f"✅ Mark Paid (+{days_to_add} days)"
                                if st.button(btn_label, key=f"pay_btn_{b['id']}", type="primary", use_container_width=True):
                                    now_paid = datetime.now(timezone.utc)
                                    new_valid_until = now_paid + timedelta(days=days_to_add)
                                    supabase.table("billing_records").update({
                                        "is_paid": True,
                                        "paid_at": now_paid.isoformat(),
                                        "valid_until": new_valid_until.isoformat()
                                    }).eq("id", b["id"]).execute()
                                    st.success(f"Payment marked! Extended by {days_to_add} days.")
                                    st.rerun()
                                    
                                wa_reminder = f"Hello {b['payer_name']}! Your {period.lower()} subscription for Sweet Debbie Deals ({b.get('member_id')}) is currently due/expired. Please renew with our coordinator."
                                st.link_button("💬 WhatsApp Reminder", make_wa_link(b['payer_phone'], wa_reminder), use_container_width=True)
                            else:
                                wa_receipt = f"Official Receipt: Hello {b['payer_name']}, payment confirmed for {period.lower()} access (₦{b['amount']:,}). Valid until {b.get('valid_until', '')[:10]}."
                                st.link_button("🧾 WhatsApp Receipt", make_wa_link(b['payer_phone'], wa_receipt), use_container_width=True)
                                
                            if st.button("🗑️ Delete", key=f"del_b_{b['id']}", type="secondary", use_container_width=True):
                                supabase.table("billing_records").delete().eq("id", b["id"]).execute()
                                st.rerun()

        # --- FANE 3: LODTRÆKNING BODER ---
        with admin_tabs[3]:
            st.markdown("#### 🎉 Store Lucky Draw (Stores)")
            all_shops_ref = supabase.table("shops").select("*").execute().data or []
            referral_counts = {}
            for s in all_shops_ref:
                ref_by = s.get("referred_by")
                if ref_by:
                    referral_counts[ref_by] = referral_counts.get(ref_by, 0) + 1
                    
            qualified_stores = []
            for s in all_shops_ref:
                s_id = s.get("member_id") or f"SHOP-{1000 + s.get('id', 1)}"
                cnt = referral_counts.get(s_id, 0)
                if cnt >= 5:
                    qualified_stores.append({"name": s.get("name"), "phone": s.get("phone"), "id": s_id, "count": cnt})

            st.write(f"Qualified stores (5+ referrals): **{len(qualified_stores)}**")
            if st.button("🎲 Draw Store Winner Now", type="primary", use_container_width=True):
                if not qualified_stores:
                    st.warning("No stores have met 5 referrals yet.")
                else:
                    winner = random.choice(qualified_stores)
                    st.balloons()
                    st.success(f"🏆 **STORE WINNER!**\n\n**{winner['name']}**\n\n🎟️ ID: `{winner['id']}`\n📞 Phone: `{winner['phone']}`")
                    win_wa = make_wa_link(winner['phone'], f"Congratulations {winner['name']}! Your store ({winner['id']}) has won the Lucky Draw!")
                    st.link_button("💬 WhatsApp Message", win_wa, use_container_width=True)

        # --- FANE 4: SUPPORT BESKEDER ---
        with admin_tabs[4]:
            st.markdown("#### Support Inbox")
            msgs = supabase.table("support_messages").select("*").order("id", desc=True).execute().data or []
            if not msgs:
                st.info("No incoming messages.")
            for m in msgs:
                with st.container(border=True):
                    col_m1, col_m2 = st.columns([3, 1])
                    with col_m1:
                        st.markdown(f"**{m['subject']}** — From: `{m['sender_name']}` ({m['user_type']})")
                        st.write(m['message'])
                        st.caption(f"Phone: `{m['sender_phone']}` • Status: **{m['status']}**")
                    with col_m2:
                        wa_reply = make_wa_link(m['sender_phone'], f"Hello {m['sender_name']}, regarding '{m['subject']}': ")
                        st.link_button("💬 Reply WhatsApp", wa_reply, use_container_width=True)
                        if st.button("🗑️ Delete", key=f"del_msg_{m['id']}", type="secondary", use_container_width=True):
                            supabase.table("support_messages").delete().eq("id", m["id"]).execute()
                            st.rerun()

        # --- FANE 5: KURIER VERIFIKATION ---
        with admin_tabs[5]:
            st.markdown("#### Couriers Verification")
            all_couriers = supabase.table("couriers").select("*").order("id", desc=True).execute().data or []
            for c in all_couriers:
                with st.container(border=True):
                    is_appr = c.get("is_approved", False)
                    r_id_val = c.get("member_id") or f"RIDER-{2000 + c['id']}"
                    col_cr1, col_cr2 = st.columns([2, 1])
                    with col_cr1:
                        st.markdown(f"**{c.get('name', 'Rider')}** (🎟️ `{r_id_val}`) — 📞 `{c.get('phone', '')}`")
                        st.caption(f"Area: {c.get('area', '')} • PIN: `{c.get('pin', '')}`")
                        if is_appr:
                            st.success("✅ Status: Approved & Active")
                        else:
                            st.warning("⏳ Status: Pending ID Verification")
                    with col_cr2:
                        if not is_appr:
                            if st.button("✅ Approve Rider", key=f"appr_{c['id']}", type="primary", use_container_width=True):
                                supabase.table("couriers").update({"is_approved": True}).eq("id", c["id"]).execute()
                                st.rerun()
                        else:
                            if st.button("⛔ Revoke", key=f"rev_{c['id']}", use_container_width=True):
                                supabase.table("couriers").update({"is_approved": False}).eq("id", c["id"]).execute()
                                st.rerun()
                        if st.button("🗑️ Delete", key=f"adm_del_c_{c['id']}", type="secondary", use_container_width=True):
                            supabase.table("couriers").delete().eq("id", c["id"]).execute()
                            st.rerun()
                    if c.get("id_card_img"):
                        with st.expander("🪪 View ID"):
                            st.image(c["id_card_img"], width=300)

        # --- FANE 6: BUTIKKER ---
        with admin_tabs[6]:
            st.markdown("#### Registered Shops")
            all_shops_admin = supabase.table("shops").select("*").execute().data or []
            for s in all_shops_admin:
                with st.container(border=True):
                    s_id_val = s.get("member_id") or f"SHOP-{1000 + s.get('id', 1)}"
                    col_s1, col_s2 = st.columns([3, 1])
                    with col_s1:
                        ref_info = f" • Referred by: `{s.get('referred_by')}`" if s.get('referred_by') else ""
                        st.markdown(f"**{s.get('name', 'Shop')}** (🎟️ `{s_id_val}`){ref_info}")
                        st.caption(f"📞 `{s.get('phone', '')}` — PIN: `{s.get('pin', '')}` — Area: `{s.get('area', '')}`")
                    with col_s2:
                        if st.button("🗑️ Delete", key=f"adm_del_shop_{s['id']}", type="secondary"):
                            supabase.table("offers").delete().eq("shop", s["name"]).execute()
                            supabase.table("shops").delete().eq("id", s["id"]).execute()
                            st.rerun()

        # --- FANE 7: KUNDER ---
        with admin_tabs[7]:
            st.markdown("#### Registered Customers")
            all_cust_admin = supabase.table("customers").select("*").execute().data or []
            if not all_cust_admin:
                st.info("No customers registered yet.")
            for cu in all_cust_admin:
                with st.container(border=True):
                    cu_id = cu.get("member_id") or f"CUST-{cu['id']}"
                    st.markdown(f"**{cu['name']}** (🎟️ `{cu_id}`)")
                    st.caption(f"📞 `{cu['phone']}` • Referred by: `{cu.get('referred_by', 'None')}`")
                    if st.button("🗑️ Delete Customer", key=f"del_cu_{cu['id']}", type="secondary"):
                        supabase.table("customers").delete().eq("id", cu["id"]).execute()
                        st.rerun()

        # --- FANE 8: ORDRER ---
        with admin_tabs[8]:
            st.markdown("#### All Orders")
            all_orders = supabase.table("orders").select("*").order("id", desc=True).execute().data or []
            for o in all_orders:
                with st.container(border=True):
                    col_o1, col_o2 = st.columns([3, 1])
                    with col_o1:
                        st.markdown(f"**Order #{o['id']}** — {o['product']} (₦{o['item_price']:,})")
                        st.caption(f"Customer: `{o['customer_name']}` ({o['customer_phone']}) • Status: **{o['status']}**")
                    with col_o2:
                        if st.button("🗑️ Delete", key=f"adm_del_ord_{o['id']}"):
                            supabase.table("orders").delete().eq("id", o["id"]).execute()
                            st.rerun()

        # --- FANE 9: TILBUD ---
        with admin_tabs[9]:
            st.markdown("#### All Product Deals")
            all_deals = supabase.table("offers").select("*").order("id", desc=True).execute().data or []
            for d in all_deals:
                with st.container(border=True):
                    col_d1, col_d2 = st.columns([3, 1])
                    with col_d1:
                        st.markdown(f"**{d['product']}** (₦{d['price']:,}) — Shop: `{d['shop']}`")
                    with col_d2:
                        if st.button("🗑️ Delete", key=f"adm_del_deal_{d['id']}"):
                            supabase.table("offers").delete().eq("id", d["id"]).execute()
                            st.rerun()

# ====================================================
# GLOBAL FOOTER: PRIVACY & ANSVARSFRASKRIVELSE
# ====================================================
st.markdown("---")
footer_html = (
    "<div class='disclaimer-box'>"
    "<strong>Platform Disclaimer, Terms & Limitation of Liability:</strong><br>"
    "Sweet Debbie Deals is an intermediary discovery and connection platform. "
    "We do not manufacture, sell, store, or inspect the products listed. "
    "All sale agreements and warranties exist strictly between the merchant and the customer. "
    "Dispatch couriers operate as independent contractors. To the maximum extent permitted under Nigerian law, "
    "Sweet Debbie Deals shall not be liable for any product defect, delivery loss, delayed dispatch, personal injury, "
    "road incident, or transaction dispute.<br><br>"
    "<strong>Cash Prizes, Raffles & Referral Terms (18+ Only):</strong><br>"
    "Participation in cash prize draws and referral programs requires users to be at least 18 years of age. "
    "<strong>Identity Verification Rule:</strong> The full name registered on any user or merchant profile <em>must strictly match</em> "
    "the official government-issued ID (NIN, Voter's Card, or Driver's License) provided upon verification or prize claim. "
    "Any discrepancy, fake account, or fraudulent referral activity will result in immediate disqualification and forfeiture of cash prizes.<br><br>"
    "<strong>Privacy (NDPA / NDPR):</strong> User data is processed strictly for commerce fulfillment, identity accreditation, and prize delivery. "
    "Registered users retain the right to rectify or request full deletion of records anytime."
    "</div>"
)
st.markdown(footer_html, unsafe_allow_html=True)
