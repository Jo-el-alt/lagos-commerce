import streamlit as st
from PIL import Image, ImageOps
from supabase import create_client, Client
from datetime import datetime, timezone, timedelta
import urllib.parse
import urllib.request
import json
import qrcode
import io
import base64
import re
import random
import hashlib
import secrets
import hmac
from openai import OpenAI

# Tema-tilstand
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

is_dark = st.session_state.dark_mode

# Mobil opsætning
st.set_page_config(
    page_title="Vendora 🇳🇬",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# Farver
bg_color = "#111827" if is_dark else "#ffffff"
text_color = "#f9fafb" if is_dark else "#111827"
card_bg = "#1f2937" if is_dark else "#f9fafb"
border_color = "#374151" if is_dark else "#e5e7eb"
btn_bg = "#374151" if is_dark else "#f3f4f6"
btn_text = "#ffffff" if is_dark else "#111827"
hover_bg = "#4b5563" if is_dark else "#e5e7eb"
hover_border = "#6b7280" if is_dark else "#d1d5db"

# CSS
st.html(f"""
<style>
    .stApp {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5,
    label[data-testid="stWidgetLabel"] p,
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label span,
    div[data-testid="stCheckbox"] label p,
    [data-testid="stCaptionContainer"] p {{
        color: {text_color} !important;
        -webkit-text-fill-color: {text_color} !important;
    }}
    
    /* Gør fanerne (Tabs) og Metrics (Pengedelen) tydelige og lyse i mørk tilstand */
    button[data-baseweb="tab"] p, 
    button[data-baseweb="tab"] span,
    button[data-baseweb="tab"] div,
    div[data-testid="stMetricLabel"] *,
    div[data-testid="stMetricValue"] *,
    div[data-testid="stMetricDelta"] * {{
        color: {text_color} !important;
        -webkit-text-fill-color: {text_color} !important;
    }}
    
    /* Rettelse til code/backtick-felter i mørk tilstand */
    code, span[data-testid="stMarkdownContainer"] code {{
        background-color: {"#374151" if is_dark else "#f3f4f6"} !important;
        color: {text_color} !important;
        -webkit-text-fill-color: {text_color} !important;
        border: 1px solid {border_color} !important;
        border-radius: 4px !important;
        padding: 2px 6px !important;
        font-family: monospace !important;
    }}
    
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"] textarea,
    div[data-baseweb="select"] span,
    input[type="text"], input[type="password"], textarea, div[data-baseweb="select"] > div {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        -webkit-text-fill-color: {text_color} !important;
    }}
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"],
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {{
        background-color: {card_bg} !important;
        border-color: {border_color} !important;
        color: {text_color} !important;
        border-radius: 8px !important;
    }}
    div[data-baseweb="popover"], div[data-baseweb="popover"] > div, div[data-testid="stPopoverBody"] {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
        border-radius: 8px !important;
    }}

    /* Kompakte knapper i toppen */
    .stButton > button,
    div[data-testid="stPopover"] > button,
    div[data-testid="stPopover"] > div > button {{
        background-color: {btn_bg} !important;
        color: {btn_text} !important;
        -webkit-text-fill-color: {btn_text} !important;
        border: 1px solid {border_color} !important;
        font-weight: 600 !important;
        width: 100% !important;
        min-height: 25px !important;
        height: 25px !important;
        max-height: 25px !important;
        padding: 0px 4px !important;
        font-size: 0.70rem !important;
        line-height: 23px !important;
        border-radius: 5px !important;
        box-shadow: none !important;
        outline: none !important;
    }}

    .stButton > button:hover,
    div[data-testid="stPopover"] > button:hover,
    div[data-testid="stPopover"] > div > button:hover {{
        background-color: {hover_bg} !important;
        border-color: {hover_border} !important;
    }}

    div[data-testid="stButton"],
    div[data-testid="stPopover"] {{
        margin: 0 !important;
        padding: 0 !important;
    }}

    div[data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 4px !important;
        width: 100% !important;
    }}

    div[data-testid="stHorizontalBlock"] > div,
    div[data-testid="stColumn"],
    div[data-testid="column"] {{
        flex: 1 1 0% !important;
        min-width: 0 !important;
        width: 0 !important;
    }}

    .grid-img-box {{ width: 100%; height: 125px; overflow: hidden; border-radius: 8px; margin-bottom: 8px; background-color: {card_bg}; display: flex; align-items: center; justify-content: center; }}
    .grid-img-box img {{ width: 100%; height: 100%; object-fit: cover; }}
    .grid-title {{ font-size: 0.95rem; font-weight: 700; line-height: 1.2; margin-bottom: 4px; color: {text_color} !important; -webkit-text-fill-color: {text_color} !important; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 2.4em; }}
    .grid-price {{ font-size: 1.05rem; font-weight: 800; color: {"#4ade80" if is_dark else "#16a34a"}; margin-bottom: 4px; }}
    .member-badge, .escrow-badge, .referral-badge, .trial-badge {{
        display: inline-block; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.9rem; margin-bottom: 8px;
    }}
    .member-badge {{ background-color: {"#064e3b" if is_dark else "#dcfce7"}; color: {"#6ee7b7" if is_dark else "#15803d"} !important; -webkit-text-fill-color: {"#6ee7b7" if is_dark else "#15803d"} !important; border: 1px solid {"#047857" if is_dark else "#bbf7d0"}; }}
    .trial-badge {{ background-color: {"#1e3a8a" if is_dark else "#dbeafe"}; color: {"#93c5fd" if is_dark else "#1d4ed8"} !important; -webkit-text-fill-color: {"#93c5fd" if is_dark else "#1d4ed8"} !important; border: 1px solid {"#1d4ed8" if is_dark else "#bfdbfe"}; }}
    .escrow-badge {{ background-color: {"#064e3b" if is_dark else "#dcfce7"}; color: {"#34d399" if is_dark else "#166534"} !important; -webkit-text-fill-color: {"#34d399" if is_dark else "#166534"} !important; border: 1px solid {"#059669" if is_dark else "#86efac"}; }}
    .referral-badge {{ background-color: {"#451a03" if is_dark else "#ffedd5"}; color: {"#fdba74" if is_dark else "#c2410c"} !important; -webkit-text-fill-color: {"#fdba74" if is_dark else "#c2410c"} !important; border: 1px solid {"#9a3412" if is_dark else "#fed7aa"}; }}
    .disclaimer-box {{ font-size: 0.8rem; background-color: {card_bg}; color: {text_color} !important; -webkit-text-fill-color: {text_color} !important; opacity: 0.85; padding: 12px; border-radius: 8px; border: 1px solid {border_color}; margin-top: 15px; }}
    .pin-box {{ background-color: #fef08a; color: #854d0e; padding: 15px; border-radius: 8px; text-align: center; border: 2px dashed #eab308; margin-top: 10px; margin-bottom: 10px; }}
</style>
""")

# Supabase forbindelse
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

PAYSTACK_SECRET = st.secrets.get("PAYSTACK_SECRET_KEY", "")

def initialize_paystack_payment(email: str, amount_naira: int, order_id: int):
    if not PAYSTACK_SECRET:
        return None, "Paystack API key missing in Secrets"
    
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET.strip()}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "amount": int(amount_naira * 100),
        "reference": f"VND-{order_id}-{int(datetime.now().timestamp())}",
        "callback_url": "https://lagos-commerce-pzru6e8tsftfmt72gbjnhz.streamlit.app/",
        "metadata": {"order_id": order_id}
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status"):
                return data["data"], None
            return None, data.get("message", "Payment init failed")
    except Exception as e:
        return None, str(e)

def verify_paystack_payment(reference: str):
    if not PAYSTACK_SECRET:
        return False, "Paystack key missing"
    
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET.strip()}",
        "Content-Type": "application/json"
    }
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") and data["data"]["status"] == "success":
                return True, data["data"]
            return False, data.get("message", "Not paid")
    except Exception as e:
        return False, str(e)

# Sikker PIN-kryptering
def hash_pin(pin: str) -> str:
    salt = secrets.token_hex(16)
    pin_hash = hashlib.pbkdf2_hmac("sha256", pin.strip().encode("utf-8"), salt.encode("utf-8"), 200000).hex()
    return f"{salt}:{pin_hash}"

def verify_pin(pin: str, stored_val: str) -> bool:
    if not stored_val:
        return False
    clean_pin = pin.strip()
    stored_str = str(stored_val).strip()
    if ":" not in stored_str:
        return hmac.compare_digest(clean_pin, stored_str)
    try:
        salt, expected_hash = stored_str.split(":", 1)
        actual_hash = hashlib.pbkdf2_hmac("sha256", clean_pin.encode("utf-8"), salt.encode("utf-8"), 200000).hex()
        return hmac.compare_digest(actual_hash, expected_hash)
    except (ValueError, AttributeError):
        return False

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

def get_shop_access_status(shop: dict):
    status = shop.get("subscription_status", "trial")
    expires_at_str = shop.get("trial_ends_at")
    
    if expires_at_str:
        try:
            clean_str = expires_at_str.replace("Z", "+00:00")
            exp_time = datetime.fromisoformat(clean_str)
            now_time = datetime.now(timezone.utc)
            diff = exp_time - now_time
            days_left = int(diff.total_seconds() // 86400)
            
            if diff.total_seconds() > 0:
                if status == "trial":
                    return "trial", f"🎉 Free Promo ({days_left}d left)", days_left
                else:
                    return "active_paid", f"🟢 Active ({days_left}d left)", days_left
            else:
                return "expired", "🔴 Expired", 0
        except Exception:
            pass
            
    return "expired", "🔴 Needs Setup", 0

def render_broadcast_alerts(target: str):
    try:
        notices = supabase.table("broadcast_messages").select("*").eq("is_active", True).in_("target_audience", [target, "All"]).order("id", desc=True).execute().data or []
        for n in notices:
            st.info(f"**{n['notice_type']} — {n['title']}**\n\n{n['message']}")
    except Exception:
        pass

# Routing parametre
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

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if "sel_area" not in st.session_state:
    st.session_state.sel_area = "All Areas"
if "sel_cat" not in st.session_state:
    st.session_state.sel_cat = "All Categories"

# ====================================================
# KOMPAKT HEADER & TOP-BAR
# ====================================================
st.markdown("<h1 style='text-align: center; font-size: 2.4rem; font-weight: 800; margin-bottom: 0px; padding-bottom: 0px;'>🛍️ Vendora</h1>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; margin-top: -4px; margin-bottom: 14px;'><span style='font-size: 0.8rem; color: #9ca3af;'>by Debbie</span> • <span style='font-size: 0.8rem; color: #10b981; font-weight: 700;'>✨ AI</span> • <span style='font-size: 0.8rem; color: #9ca3af;'>🇳🇬 Lagos</span></div>", unsafe_allow_html=True)

top_c1, top_c2, top_c3 = st.columns(3)

with top_c1:
    theme_btn_label = "☀️ Day" if st.session_state.dark_mode else "🌙 Night"
    if st.button(theme_btn_label, key="theme_toggle_btn", use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

with top_c2:
    with st.popover("🔑 Log In", use_container_width=True):
        st.markdown("**Select Portal:**")
        if st.button("🏪 Store Owner", key="top_login_store", use_container_width=True):
            st.session_state.current_view = "🏪 Store Owner Admin"
            st.session_state.auth_tab_choice = "login"
            st.rerun()
        if st.button("🛵 Courier / Rider", key="top_login_rider", use_container_width=True):
            st.session_state.current_view = "🛵 Courier / Dispatch"
            st.session_state.rider_tab_choice = "login"
            st.rerun()
        if st.button("🛡️ Admin", key="top_login_admin", use_container_width=True):
            st.session_state.current_view = "🛡️ Platform Admin"
            st.rerun()
        if st.button("💬 Support", key="top_login_sup", use_container_width=True):
            st.session_state.current_view = "💬 Support"
            st.rerun()

with top_c3:
    with st.popover("📝 Register", use_container_width=True):
        st.markdown("**New Account:**")
        if st.button("🏪 Store (30d Free)", key="top_reg_store", use_container_width=True):
            st.session_state.current_view = "🏪 Store Owner Admin"
            st.session_state.auth_tab_choice = "register"
            st.rerun()
        if st.button("🛵 Courier / Rider", key="top_reg_rider", use_container_width=True):
            st.session_state.current_view = "🛵 Courier / Dispatch"
            st.session_state.rider_tab_choice = "register"
            st.rerun()

# Returknap til forsiden fra andre sektioner
if st.session_state.current_view != "🛒 Browse Deals":
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Browse Deals", key="back_to_deals_btn", use_container_width=True):
        st.session_state.current_view = "🛒 Browse Deals"
        st.rerun()

# ====================================================
# MODAL TIL DETALJER, BESTILLING & PAYSTACK CHECKOUT
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
    
    wa_msg = f"Hello {item['shop']}! I saw *{item['product']}* (₦{item['price']:,}) on Vendora. Is it available?"
    wa_url = make_wa_link(item["phone"], wa_msg)
    st.link_button("💬 Order Directly via WhatsApp (Free)", wa_url, use_container_width=True)
    
    st.markdown("#### 🛵 Or Order with Dispatch & Escrow Payment")
    
    order_key = f"active_pay_order_{item['id']}"
    if order_key not in st.session_state:
        st.session_state[order_key] = None

    if st.session_state[order_key] is None:
        with st.form(f"modal_order_form_{item['id']}"):
            cust_name = st.text_input("Your Full Name *", placeholder="e.g. Tunde Bakare")
            cust_email = st.text_input("Your Email (For Paystack receipt) *", placeholder="tunde@example.com")
            cust_phone = st.text_input("Your WhatsApp Phone *", placeholder="080...")
            cust_area = st.selectbox("Your Neighborhood *", ["Yaba / Sabo", "Ikeja / Allen", "Surulere", "Victoria Island / Lekki", "Other"])
            cust_addr = st.text_area("Full Address & Nearby Landmark *")
            
            suggested_delivery = st.number_input("Your Offered Delivery Fee (₦) *", min_value=1200, value=1500, step=100)
            total_naira = item['price'] + suggested_delivery
            st.markdown(f"**Total to Pay (Item + Delivery): ₦{total_naira:,}**")
            
            c_consent = st.checkbox("I agree to terms: Vendora acts solely as an intermediary directory.", value=True)
            submit_btn = st.form_submit_button("💳 Proceed to Paystack Escrow Payment", type="primary", use_container_width=True)
            
            if submit_btn:
                if not cust_name or not cust_email or not cust_phone or not cust_addr or not c_consent:
                    st.error("Please fill all required details, provide an email, and accept terms.")
                else:
                    p_fee = 150
                    r_payout = max(0, int(suggested_delivery) - p_fee)
                    delivery_pin = str(random.randint(1000, 9999))
                    
                    new_order = {
                        "offer_id": item["id"], "product": item["product"], "shop": item["shop"],
                        "shop_phone": item["phone"], "pickup_location": pickup_loc,
                        "customer_name": cust_name.strip(), "customer_phone": cust_phone.strip(),
                        "customer_area": cust_area, "delivery_address": cust_addr.strip(),
                        "item_price": item["price"], "delivery_fee": int(suggested_delivery),
                        "rider_payout": r_payout, "platform_fee": p_fee, 
                        "status": "pending", "payment_status": "unpaid",
                        "delivery_pin": delivery_pin
                    }
                    ins = supabase.table("orders").insert(new_order).execute()
                    if ins.data:
                        created_order = ins.data[0]
                        p_data, p_err = initialize_paystack_payment(cust_email.strip(), total_naira, created_order["id"])
                        if p_data:
                            supabase.table("orders").update({
                                "paystack_reference": p_data["reference"]
                            }).eq("id", created_order["id"]).execute()
                            
                            st.session_state[order_key] = {
                                "order_id": created_order["id"],
                                "auth_url": p_data["authorization_url"],
                                "reference": p_data["reference"],
                                "total": total_naira,
                                "delivery_pin": delivery_pin
                            }
                            st.rerun()
                        else:
                            st.error(f"Paystack initialization error: {p_err}")
    else:
        pay_info = st.session_state[order_key]
        
        check_status = supabase.table("orders").select("payment_status").eq("id", pay_info["order_id"]).execute()
        is_already_funded = check_status.data and check_status.data[0]["payment_status"] == "escrow_funded"

        if is_already_funded:
            st.success("🎉 Payment Confirmed! Your order is secured.")
            st.markdown(f"""
            <div class="pin-box">
                <h3 style="margin:0; color:#854d0e;">YOUR DELIVERY PIN: {pay_info['delivery_pin']}</h3>
                <p style="margin:0; font-size:0.9rem;">Do NOT share this PIN with the rider until they arrive with your items.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Close Order"):
                st.session_state[order_key] = None
                st.rerun()
        else:
            with st.container(border=True):
                st.success(f"📦 Order #{pay_info['order_id']} created! Total: **₦{pay_info['total']:,}**")
                st.markdown("Click below to open Paystack secure checkout:")
                st.link_button("💳 Open Paystack Checkout Window", pay_info["auth_url"], use_container_width=True)
                
                st.markdown("---")
                st.caption("Once you have paid in the window above, verify here:")
                if st.button("🔄 Verify Payment Status", type="primary", use_container_width=True):
                    is_paid, ver_data = verify_paystack_payment(pay_info["reference"])
                    if is_paid:
                        now_iso = datetime.now(timezone.utc).isoformat()
                        supabase.table("orders").update({
                            "payment_status": "escrow_funded",
                            "paid_at": now_iso
                        }).eq("id", pay_info["order_id"]).execute()
                        st.rerun()
                    else:
                        st.warning("Payment not registered yet. Try again in a moment.")

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
            with st.popover(f"📍 {st.session_state.sel_area}", use_container_width=True):
                areas = ["All Areas", "Yaba Market", "Ikeja (Computer Village)", "Surulere", "Balogun Market", "Lekki"]
                for a in areas:
                    if st.button(a, key=f"area_btn_{a}", use_container_width=True):
                        st.session_state.sel_area = a
                        st.rerun()
        with c2:
            with st.popover(f"📂 {st.session_state.sel_cat}", use_container_width=True):
                cats = ["All Categories", "Groceries & Food", "Electronics", "Fashion & Clothing", "Home & Living"]
                for c in cats:
                    if st.button(c, key=f"cat_btn_{c}", use_container_width=True):
                        st.session_state.sel_cat = c
                        st.rerun()

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

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    with st.expander("ℹ️ How Vendora Works (Customer Guide)"):
        st.markdown("""
        **Welcome to Vendora!** Here is how you shop safely:
        1. **Browse & Order:** Find a deal and click 'View Deal'.
        2. **Safe Escrow Payment:** When you pay online via Paystack, your money is held securely in our Escrow system. The store does not get paid until you receive your items.
        3. **Delivery PIN:** After payment, you receive a **4-digit PIN**. 
        4. **Receive Items:** When the dispatch rider arrives, check your items. Only give the rider your 4-digit PIN if everything is correct. The PIN unlocks the payment for the rider and the store.
        """)

# ====================================================
# VISNING 2: BUTIKSEJER ADMIN & OPRETTELSE
# ====================================================
elif st.session_state.current_view == "🏪 Store Owner Admin":
    
    with st.expander("ℹ️ Store Owner Guide (How to sell)"):
        st.markdown("""
        **Welcome Store Owners!**
        1. **Post Deals:** Upload your daily deals. They expire automatically after 48 hours to keep the market fresh.
        2. **Escrow Orders:** If you get an order marked as `PAID ONLINE (Escrow Funded)`, **give the item to the rider without asking for cash**. The money is already secured in our platform account.
        3. **Payouts:** Once the rider delivers the item to the customer (and enters the PIN), your money is automatically credited and sent to your OPay/Bank by the Vendora Admin.
        4. **Airtime Rewards:** Invite other stalls using your `Store ID`. Every 5 stores you invite earns you ₦1,000 airtime!
        """)
        
    if not st.session_state.logged_shop:
        default_auth_idx = 1 if st.session_state.get("auth_tab_choice") == "register" else 0
        auth_mode = st.radio("Choose action:", ["🔑 Log In to Existing Store", "📝 Register New Store / Stall (30 Days Free)"], index=default_auth_idx, horizontal=True)
        
        if auth_mode == "🔑 Log In to Existing Store":
            st.markdown("### Store Owner Login")
            with st.container(border=True):
                phone_input = st.text_input("WhatsApp / Phone Number", placeholder="08012345678", value="")
                pin_input = st.text_input("4-Digit PIN", type="password", placeholder="1234", value="")
                if st.button("Log In Now", type="primary", use_container_width=True):
                    clean_phone = phone_input.strip()
                    res = supabase.table("shops").select("*").eq("phone", clean_phone).execute()
                    if res.data and verify_pin(pin_input, res.data[0].get("pin")):
                        st.session_state.logged_shop = res.data[0]
                        st.success(f"Welcome back, {res.data[0]['name']}!")
                        st.rerun()
                    else:
                        st.error("Incorrect phone number or PIN.")
        else:
            st.markdown("### 📝 Register New Store — 30 Days Free Launch Promo")
            st.info("🎉 Welcome to Vendora! All stalls registered during launch receive 30 days of 100% free access. No upfront fees.")
            with st.container(border=True):
                new_shop_name = st.text_input("Store or Stall Name *", placeholder="e.g. Mama Funke Provisions")
                new_phone = st.text_input("WhatsApp Number *", placeholder="08012345678")
                new_pin = st.text_input("Create 4-Digit Secret PIN *", type="password", max_chars=4, placeholder="4 digits e.g. 2468")
                new_pin_confirm = st.text_input("Confirm 4-Digit PIN *", type="password", max_chars=4, placeholder="4 digits e.g. 2468")
                new_area = st.selectbox("Market / Area *", ["Yaba Market", "Ikeja (Computer Village)", "Surulere", "Balogun Market", "Lekki"])
                new_cat = st.selectbox("Main Category *", ["Groceries & Food", "Electronics", "Fashion & Clothing", "Home & Living"])
                
                referred_code = st.text_input("Partner Referral ID? (Referred by another stall, optional)", placeholder="e.g. SHOP-1002")
                shop_consent = st.checkbox("I accept Platform Terms: Vendora acts as a discovery intermediary directory.")
                
                if st.button("🚀 Register & Activate 30-Day Free Access", type="primary", use_container_width=True):
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
                            
                            now_time = datetime.now(timezone.utc)
                            trial_end = now_time + timedelta(days=30)
                            
                            shop_record = {
                                "slug": unique_slug, "name": new_shop_name.strip(), "phone": clean_phone,
                                "pin": hash_pin(new_pin), "area": new_area, "category": new_cat,
                                "member_id": new_member_code, "referred_by": clean_ref,
                                "airtime_paid_count": 0,
                                "subscription_status": "trial",
                                "trial_ends_at": trial_end.isoformat()
                            }
                            ins = supabase.table("shops").insert(shop_record).execute()
                            if ins.data:
                                st.session_state.logged_shop = ins.data[0]
                                st.rerun()
    else:
        fresh_shop = supabase.table("shops").select("*").eq("id", st.session_state.logged_shop["id"]).execute().data
        shop = fresh_shop[0] if fresh_shop else st.session_state.logged_shop
        member_id = shop.get("member_id") or f"SHOP-{1000 + shop.get('id', 1)}"
        
        render_broadcast_alerts("Stores")
        
        s_code, s_badge, days_left = get_shop_access_status(shop)
        
        ref_count_res = supabase.table("shops").select("id").eq("referred_by", member_id).execute()
        total_referred = len(ref_count_res.data or [])
        already_paid = shop.get("airtime_paid_count") or 0
        unpaid_refs = max(0, total_referred - already_paid)
        current_progress = unpaid_refs % 5
        
        col_hdr1, col_hdr2 = st.columns([3, 1])
        with col_hdr1:
            st.markdown(f"### 🏪 {shop['name']}")
            st.markdown(f'<div class="member-badge">🏪 Store ID: {member_id}</div>', unsafe_allow_html=True)
            
            if s_code == "trial":
                st.markdown(f'<div class="trial-badge">{s_badge}</div>', unsafe_allow_html=True)
            elif s_code == "active_paid":
                st.markdown(f'<div class="status-light-green">{s_badge}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="status-light-red">{s_badge} — Contact coordinator</div>', unsafe_allow_html=True)

            if unpaid_refs >= 5:
                ready_payouts = unpaid_refs // 5
                st.markdown(f'<div class="referral-badge" style="background-color: #e8f5e9; color:#1b5e20;">🎉 Target Met! You have <b>₦{ready_payouts * 1000:,} Airtime</b> ready for payout!</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="referral-badge">🎁 Referral Airtime Progress: <b>{current_progress}/5 stalls</b> (Refer {5 - current_progress} more to earn ₦1,000 Airtime)</div>', unsafe_allow_html=True)
                
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
        product = st.text_input("Product Name *", placeholder="e.g. 5L Kings Cooking Oil, Nike Air, Original 20W Charger")
        price = st.number_input("Deal Price in Naira (₦) *", min_value=50, value=1000, step=50)
        uploaded_file = st.file_uploader("Photo (Optional)", type=["jpg", "jpeg", "png", "webp"])
        
        # AI Copywriter
        if "ai_ad_text" not in st.session_state:
            st.session_state.ai_ad_text = ""

        c_ai1, c_ai2 = st.columns([3, 1])
        with c_ai1:
            ai_keywords = st.text_input("Highlights for AI (optional)", placeholder="e.g. fresh stock, direct from distributor")
        with c_ai2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("✨ Write with AI", use_container_width=True):
                openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
                if not openai_api_key:
                    st.error("OpenAI API key missing in Secrets.")
                elif not product:
                    st.warning("Enter product name first.")
                else:
                    try:
                        client = OpenAI(api_key=openai_api_key)
                        prompt = f"Write a short, punchy Nigerian sales caption (max 2 sentences) for a market deal on Vendora Lagos. Store: {shop['name']}, Market/Area: {shop['area']}, Product: {product}, Price: NGN {price:,}. Highlights: {ai_keywords}."
                        resp = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=80
                        )
                        st.session_state.ai_ad_text = resp.choices[0].message.content.strip()
                        st.rerun()
                    except Exception as e:
                        st.error(f"AI error: {e}")

        default_ad_text = st.session_state.ai_ad_text or f"🔥 Quality {product} now available at {shop['name']} on Vendora for only NGN {price:,}! Limited stock today in {shop['area']}."
        desc = st.text_area("Ad Description:", value=default_ad_text, height=85)
        
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
                st.session_state.ai_ad_text = ""
                st.session_state.go_to_deals = True
                st.rerun()

        st.markdown("---")
        st.markdown("### Store QR Code")
        direct_shop_url = f"https://lagos-commerce-pzru6e8tsftfmt72gbjnhz.streamlit.app/?shop={shop['slug']}"
        st.image(generate_qr(direct_shop_url), width=160, caption=f"Scan for {shop['name']}")

# ====================================================
# VISNING 3: BUDE & KURÉR (MED PIN-LÅS)
# ====================================================
elif st.session_state.current_view == "🛵 Courier / Dispatch":
    
    with st.expander("ℹ️ Courier Guide (How to deliver safely)"):
        st.markdown("""
        **Welcome Verified Riders!**
        1. **Accept Jobs:** Browse 'Open Delivery Requests' and accept the ones that fit your route.
        2. **Escrow Safety:** If an order says `PAID ONLINE (Escrow Funded)`, **do NOT pay the store with your own money**. The items are already paid for! Just pick them up.
        3. **Delivery PIN:** When you arrive at the customer, ask them for their **4-digit PIN**. 
        4. **Get Paid:** Enter the customer's PIN to mark the order as delivered. This guarantees your payout!
        """)

    if not st.session_state.logged_courier:
        default_rider_idx = 1 if st.session_state.get("rider_tab_choice") == "register" else 0
        courier_auth = st.radio("Rider Action:", ["🔑 Rider Log In", "📝 Register New Rider / Courier"], index=default_rider_idx, horizontal=True)
        
        if courier_auth == "🔑 Rider Log In":
            st.markdown("### 🛵 Dispatch Rider Login")
            with st.container(border=True):
                r_phone = st.text_input("Phone Number", placeholder="080...")
                r_pin = st.text_input("4-Digit PIN", type="password", placeholder="1234")
                if st.button("Rider Log In", type="primary", use_container_width=True):
                    res = supabase.table("couriers").select("*").eq("phone", r_phone.strip()).execute()
                    if res.data and verify_pin(r_pin, res.data[0].get("pin")):
                        st.session_state.logged_courier = res.data[0]
                        st.success(f"Welcome back, {res.data[0]['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid phone or PIN.")
        else:
            st.markdown("### 📝 Register as Verified Dispatch Rider")
            with st.container(border=True):
                r_name = st.text_input("Rider / Company Full Name *", placeholder="e.g. Ibrahim Babatunde")
                r_phone_new = st.text_input("Phone Number (WhatsApp) *", placeholder="080...")
                r_pin_new = st.text_input("Create 4-Digit PIN *", type="password", max_chars=4, placeholder="1234")
                r_pin_confirm = st.text_input("Confirm 4-Digit PIN *", type="password", max_chars=4, placeholder="1234")
                r_area = st.selectbox("Primary Operating Area", ["Yaba / Sabo", "Ikeja / Maryland", "Surulere", "Island / Lekki", "All Lagos"])
                vehicle = st.selectbox("Vehicle Type", ["Motorcycle (Okada)", "Bicycle", "Van / Car"])
                
                id_file = st.file_uploader("Upload Government ID (NIN, Voter's Card, License) *", type=["jpg", "jpeg", "png", "webp"])
                rider_consent = st.checkbox("I agree to terms: Riders operate as independent contractors.")
                
                if st.button("🚀 Submit Profile for Verification", type="primary", use_container_width=True):
                    if not r_name or not r_phone_new or not r_pin_new or not r_pin_confirm or not id_file:
                        st.error("Please fill all details, upload ID, and set PIN.")
                    elif r_pin_new != r_pin_confirm:
                        st.error("PIN codes do not match!")
                    elif not rider_consent:
                        st.error("Please accept platform terms.")
                    else:
                        id_base64 = convert_to_base64_img(id_file, target_size=(600, 400))
                        r_data = {
                            "name": r_name.strip(), "phone": r_phone_new.strip(),
                            "pin": hash_pin(r_pin_new), "area": r_area, "vehicle": vehicle,
                            "id_card_img": id_base64, "is_approved": False,
                            "member_id": generate_member_code("RIDER")
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
            st.markdown(f'<div class="member-badge">🛵 Rider ID: {r_member_id}</div>', unsafe_allow_html=True)
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
            
            st.markdown("#### 📦 Your Active Deliveries")
            my_jobs = supabase.table("orders").select("*").eq("courier_id", rider["id"]).neq("status", "delivered").order("id", desc=True).execute().data or []
            
            if not my_jobs:
                st.info("No active delivery runs right now.")
            else:
                for job in my_jobs:
                    with st.container(border=True):
                        st.markdown(f"**Order #{job['id']} — {job['product']}**")
                        
                        p_stat = job.get("payment_status", "unpaid")
                        if p_stat == "escrow_funded":
                            st.markdown('<div class="escrow-badge">🛡️ PAID IN ESCROW (Do NOT pay shop with own money)</div>', unsafe_allow_html=True)
                        else:
                            st.caption(f"Payment Status: `{p_stat}`")

                        st.markdown(f"🏪 **Pickup:** {job['shop']} — 📞 `{job['shop_phone']}`")
                        st.markdown(f"🎯 **Drop-off:** {job['customer_name']} — 📞 `{job['customer_phone']}`")
                        st.markdown(f"📍 **Address:** {job['delivery_address']}")
                        st.markdown(f"💵 **Your Payout:** **₦{job['rider_payout']:,}** *(Platform fee ₦{job.get('platform_fee', 150):,} deducted)*")
                        
                        wa_pickup = make_wa_link(job['shop_phone'], f"Hello {job['shop']}, rider {rider['name']} arriving to pick up Order #{job['id']} ({job['product']}).")
                        wa_cust = make_wa_link(job['customer_phone'], f"Hello {job['customer_name']}, verified rider {rider['name']} is on the way with your {job['product']}.")
                        
                        cw1, cw2 = st.columns(2)
                        with cw1:
                            st.link_button("💬 WA Shop", wa_pickup, use_container_width=True)
                        with cw2:
                            st.link_button("💬 WA Customer", wa_cust, use_container_width=True)
                            
                        if job["status"] == "accepted":
                            if st.button("📦 Mark Picked Up", key=f"pk_{job['id']}", use_container_width=True):
                                supabase.table("orders").update({"status": "picked_up"}).eq("id", job["id"]).execute()
                                st.rerun()
                                
                        elif job["status"] == "picked_up":
                            st.info("🚚 On the way to customer. Ask customer for 4-digit PIN upon arrival.")
                            entered_pin = st.text_input("Enter 4-Digit Customer PIN", key=f"pin_input_{job['id']}", max_chars=4)
                            if st.button("✅ Verify PIN & Mark Delivered", key=f"dl_{job['id']}", type="primary", use_container_width=True):
                                if entered_pin.strip() == str(job.get("delivery_pin")):
                                    supabase.table("orders").update({"status": "delivered"}).eq("id", job["id"]).execute()
                                    st.success("✅ PIN Verified! Order delivered successfully.")
                                    st.rerun()
                                else:
                                    st.error("❌ Incorrect PIN. Please ask the customer again.")

            st.markdown("---")
            st.markdown("#### ⚡ Open Delivery Requests & InDrive Bidding")
            open_jobs = supabase.table("orders").select("*").eq("status", "pending").order("id", desc=True).execute().data or []
            if not open_jobs:
                st.write("No pending delivery jobs right now.")
            else:
                for ojob in open_jobs:
                    with st.container(border=True):
                        st.markdown(f"**{ojob['product']}** (Item: ₦{ojob['item_price']:,})")
                        
                        p_stat = ojob.get("payment_status", "unpaid")
                        if p_stat == "escrow_funded":
                            st.markdown('<div class="escrow-badge">🛡️ PAID ONLINE (Escrow Funded)</div>', unsafe_allow_html=True)

                        st.markdown(f"📍 **Pickup:** {ojob['shop']} — {ojob['pickup_location']}")
                        st.markdown(f"🎯 **Drop-off Area:** {ojob['customer_area']}")
                        st.markdown(f"💵 **Customer Delivery Offer:** **₦{ojob['delivery_fee']:,}** *(You get: ₦{ojob['rider_payout']:,})*")
                        
                        c_bid1, c_bid2 = st.columns(2)
                        with c_bid1:
                            if st.button("✅ Accept Customer Offer", key=f"acc_{ojob['id']}", type="primary", use_container_width=True):
                                supabase.table("orders").update({
                                    "status": "accepted", "courier_id": rider["id"]
                                }).eq("id", ojob["id"]).execute()
                                st.rerun()
                        with c_bid2:
                            wa_counter = make_wa_link(ojob['customer_phone'], f"Hello {ojob['customer_name']}! I am verified rider {rider['name']} on Vendora. I can deliver your {ojob['product']} to {ojob['customer_area']} right now for ₦{ojob['delivery_fee'] + 500:,}. Would that work?")
                            st.link_button("💬 Propose Counter-Offer on WA", wa_counter, use_container_width=True)

# ====================================================
# VISNING 4: BRUGER-SUPPORT
# ====================================================
elif st.session_state.current_view == "💬 Support":
    st.markdown("### 💬 User Support & Helpdesk")
    st.caption("Need help, stall listing assistance, or referral airtime questions? Message our coordinator team.")
    
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
        
    with st.container(border=True):
        u_name = st.text_input("Your Name / Business Name *", value=default_name)
        u_phone = st.text_input("WhatsApp / Phone Number *", value=default_phone)
        u_role = st.selectbox("I am a:", ["Customer / Buyer", "Store Owner", "Courier / Rider", "Other"])
        u_subject = st.selectbox("Topic / Subject *", ["Free Trial / Subscription", "Referral Airtime Reward", "Order Issue", "Courier Verification", "Forgotten PIN", "General Inquiry"])
        u_message = st.text_area("Your Message / Question *", placeholder="Describe your inquiry...")
        
        if st.button("📨 Send Message to Vendora Team", type="primary", use_container_width=True):
            if not u_name or not u_phone or not u_message:
                st.error("Please fill in your name, phone, and message.")
            else:
                msg_data = {
                    "sender_name": u_name.strip(), "sender_phone": u_phone.strip(),
                    "user_type": u_role, "subject": u_subject, "message": u_message.strip(),
                    "status": "open"
                }
                supabase.table("support_messages").insert(msg_data).execute()
                st.success("✅ Message sent to Vendora support! We will contact you on WhatsApp shortly.")

# ====================================================
# VISNING 5: PLATFORM SUPER ADMIN (INKL. TEST-SIMULERING OG RYD-OP)
# ====================================================
elif st.session_state.current_view == "🛡️ Platform Admin":
    st.markdown("### 🛡️ Vendora Platform Admin")
    
    if not st.session_state.admin_logged_in:
        admin_pass = st.text_input("Admin PIN", type="password", placeholder="Master key")
        if st.button("Unlock Admin Panel", type="primary"):
            master_admin_pin = str(st.secrets.get("ADMIN_PASSWORD", "")).strip()
            if master_admin_pin and hmac.compare_digest(admin_pass.strip(), master_admin_pin):
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Incorrect Admin PIN.")
    else:
        c_a1, c_a2 = st.columns([3, 1])
        with c_a1:
            st.success("🔓 Super Admin Mode Active")
        with c_a2:
            if st.button("🔒 Lock Admin"):
                st.session_state.admin_logged_in = False
                st.rerun()

        st.markdown("---")
        admin_tabs = st.tabs(["🧪 Quick Test Simulation", "📢 Broadcasts", "🎁 Airtime Rewards", "🚦 Subscriptions & Trials", "💰 Escrow & Settlements", "📬 Messages", "🛵 Couriers", "🏪 Stores", "📦 Orders"])

        all_shops_list = supabase.table("shops").select("*").execute().data or []

        # --- FANE 0: TEST-SIMULERING FOR HURTIG AFPRØVNING ---
        with admin_tabs[0]:
            st.markdown("#### 🧪 Developer & Admin Simulation Hub")
            st.info("Her kan du med ét klik oprette test-data direkte i databasen, logge ind som bod/bud, eller lave en fiktiv betalt ordre.")
            
            tcol1, tcol2 = st.columns(2)
            with tcol1:
                with st.container(border=True):
                    st.markdown("##### 🏪 1-Klik: Test Bod & Vare")
                    st.caption("Opretter 'Mama Tunde Test' med 30 dages gratis adgang og lægger straks 1 vare online.")
                    if st.button("⚡ Opret Test-Bod & Vare", use_container_width=True):
                        t_phone = f"080{random.randint(10000000, 99999999)}"
                        t_trial_end = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
                        new_s = {
                            "slug": f"mama-tunde-test-{random.randint(100, 999)}",
                            "name": "Mama Tunde Provisions (Test)",
                            "phone": t_phone,
                            "pin": hash_pin("1234"),
                            "area": "Yaba Market",
                            "category": "Groceries & Food",
                            "member_id": generate_member_code("SHOP"),
                            "subscription_status": "trial",
                            "trial_ends_at": t_trial_end
                        }
                        ins_s = supabase.table("shops").insert(new_s).execute()
                        if ins_s.data:
                            shop_rec = ins_s.data[0]
                            supabase.table("offers").insert({
                                "shop": shop_rec["name"],
                                "category": shop_rec["category"],
                                "area": shop_rec["area"],
                                "is_mobile": False,
                                "location_note": "Stall 14, Yaba Main Market",
                                "phone": shop_rec["phone"],
                                "product": "5L Kings Cooking Oil (Test)",
                                "price": 4500,
                                "description": "Test deal generated automatically from Admin Panel.",
                                "status": "active"
                            }).execute()
                            st.session_state.logged_shop = shop_rec
                            st.success(f"✅ Oprettet og logget ind som '{shop_rec['name']}'! PIN er 1234.")
                            st.rerun()

            with tcol2:
                with st.container(border=True):
                    st.markdown("##### 🛵 1-Klik: Test Verificeret Bud")
                    st.caption("Opretter et færdig-godkendt bud 'Ibrahim Dispatch (Test)', klar til at tage opgaver.")
                    if st.button("⚡ Opret & Godkend Test-Bud", use_container_width=True):
                        r_phone = f"081{random.randint(10000000, 99999999)}"
                        new_r = {
                            "name": "Ibrahim Dispatch (Test)",
                            "phone": r_phone,
                            "pin": hash_pin("1234"),
                            "area": "Yaba / Sabo",
                            "vehicle": "Motorcycle (Okada)",
                            "is_approved": True,
                            "member_id": generate_member_code("RIDER")
                        }
                        ins_r = supabase.table("couriers").insert(new_r).execute()
                        if ins_r.data:
                            st.session_state.logged_courier = ins_r.data[0]
                            st.success(f"✅ Oprettet og logget ind som '{ins_r.data[0]['name']}'! PIN er 1234.")
                            st.rerun()

            st.markdown("---")
            with st.container(border=True):
                st.markdown("##### 💳 1-Klik: Simuler Betalt Escrow-Ordre")
                st.caption("Genererer en fiktiv ordre med status 'Paid Online'. Budet skal bruge koden **1234** ved levering.")
                if st.button("🚀 Simuler Færdigbetalt Ordre (₦6.000)", type="primary", use_container_width=True):
                    offer_check = supabase.table("offers").select("id").limit(1).execute()
                    safe_offer_id = offer_check.data[0]["id"] if offer_check.data else None

                    sim_order = {
                        "offer_id": safe_offer_id,
                        "product": "5L Kings Cooking Oil (Test)",
                        "shop": "Mama Tunde Provisions (Test)",
                        "shop_phone": "08012345678",
                        "pickup_location": "Stall 14, Yaba Main Market",
                        "customer_name": "Chioma Adeleke (Test)",
                        "customer_phone": "08098765432",
                        "customer_area": "Surulere",
                        "delivery_address": "12 Adeniran Ogunsanya St, Surulere",
                        "item_price": 4500,
                        "delivery_fee": 1500,
                        "rider_payout": 1350,
                        "platform_fee": 150,
                        "status": "pending",
                        "payment_status": "escrow_funded",
                        "paystack_reference": f"SIM-{random.randint(10000, 99999)}",
                        "paid_at": datetime.now(timezone.utc).isoformat(),
                        "delivery_pin": "1234"
                    }
                    supabase.table("orders").insert(sim_order).execute()
                    st.success("✅ Fiktiv betalt ordre oprettet! Tjek fanerne '💰 Escrow & Settlements' og '🛵 Courier / Dispatch'. (PIN: 1234)")

            st.markdown("---")
            with st.container(border=True):
                st.markdown("##### 🧹 Ryd op efter test")
                st.caption("Sletter KUN data genereret via test-knapperne (ordrer med 'SIM-' og brugere med '(Test)'). Rigtige kunders ordrer og regnskaber bliver ikke rørt.")
                if st.button("🗑️ Slet al test-data & nulstil regnskab", type="primary", use_container_width=True):
                    supabase.table("orders").delete().like("paystack_reference", "SIM-%").execute()
                    supabase.table("offers").delete().like("shop", "%(Test)%").execute()
                    supabase.table("shops").delete().like("name", "%(Test)%").execute()
                    supabase.table("couriers").delete().like("name", "%(Test)%").execute()
                    st.success("✅ Al test-data er fjernet! Escrow-regnskabet og listerne er ryddet for test-tal.")

        # --- FANE 1: BROADCASTS ---
        with admin_tabs[1]:
            st.markdown("#### 📢 Platform Broadcast Alerts")
            with st.expander("➕ Create New Alert"):
                b_target = st.selectbox("Target Audience:", ["Stores", "Couriers", "All"])
                b_type = st.selectbox("Badge:", ["🎁 Airtime Promotion", "📢 Platform Update", "⚠️ Notice"])
                b_title = st.text_input("Title *")
                b_body = st.text_area("Message *")
                if st.button("🚀 Publish Alert", type="primary"):
                    if b_title and b_body:
                        supabase.table("broadcast_messages").insert({
                            "target_audience": b_target, "notice_type": b_type,
                            "title": b_title.strip(), "message": b_body.strip(), "is_active": True
                        }).execute()
                        st.success("Published!")
                        st.rerun()

            broadcasts = supabase.table("broadcast_messages").select("*").order("id", desc=True).execute().data or []
            for b in broadcasts:
                with st.container(border=True):
                    st.markdown(f"**{b['notice_type']} — {b['title']}** (`{b['target_audience']}`)")
                    st.write(b["message"])
                    if st.button("🗑️ Delete Alert", key=f"del_b_{b['id']}"):
                        supabase.table("broadcast_messages").delete().eq("id", b["id"]).execute()
                        st.rerun()

        # --- FANE 2: AIRTIME REWARDS ---
        with admin_tabs[2]:
            st.markdown("#### 🎁 Referral Airtime Payouts")
            referral_map = {}
            for s in all_shops_list:
                ref_by = s.get("referred_by")
                if ref_by:
                    referral_map[ref_by] = referral_map.get(ref_by, 0) + 1

            pending_payouts = []
            for s in all_shops_list:
                s_id = s.get("member_id") or f"SHOP-{1000 + s.get('id', 1)}"
                total_refs = referral_map.get(s_id, 0)
                paid_refs = s.get("airtime_paid_count") or 0
                unpaid = max(0, total_refs - paid_refs)
                if unpaid >= 5:
                    portions = unpaid // 5
                    pending_payouts.append({
                        "id": s["id"], "name": s["name"], "phone": s["phone"],
                        "member_id": s_id, "reward_naira": portions * 1000,
                        "advance_by": portions * 5, "paid_refs": paid_refs, "unpaid": unpaid
                    })

            if not pending_payouts:
                st.info("No stores currently have 5+ unrewarded referrals.")
            else:
                for p in pending_payouts:
                    with st.container(border=True):
                        st.markdown(f"**{p['name']}** (`{p['member_id']}`) — 📞 `{p['phone']}`")
                        st.success(f"🎉 Ready for Payout: **₦{p['reward_naira']:,} Airtime**")
                        wa_air = make_wa_link(p["phone"], f"Hello {p['name']}! Your ₦{p['reward_naira']:,} referral airtime has been sent.")
                        st.link_button("💬 Send WA Receipt", wa_air, use_container_width=True)
                        if st.button(f"✅ Mark ₦{p['reward_naira']:,} Airtime Sent", key=f"p_{p['id']}", type="primary"):
                            supabase.table("shops").update({"airtime_paid_count": p["paid_refs"] + p["advance_by"]}).eq("id", p["id"]).execute()
                            st.rerun()

        # --- FANE 3: ABONNEMENTER & GRATIS PRØVEPERIODE ---
        with admin_tabs[3]:
            st.markdown("#### 🚦 Store Access & Subscription Monitor")
            
            trials = []
            paid_active = []
            expired_shops = []
            
            for s in all_shops_list:
                st_code, st_label, d_left = get_shop_access_status(s)
                entry = {"shop": s, "label": st_label, "days_left": d_left}
                if st_code == "trial":
                    trials.append(entry)
                elif st_code == "active_paid":
                    paid_active.append(entry)
                else:
                    expired_shops.append(entry)

            sm1, sm2, sm3 = st.columns(3)
            with sm1:
                st.metric("🎉 Active Free Trials", len(trials))
            with sm2:
                st.metric("🟢 Paid Subscriptions", len(paid_active))
            with sm3:
                st.metric("🔴 Expired / Needs Renewal", len(expired_shops))

            st.markdown("---")
            st.markdown("##### 🏪 Stores on Active Subscription or Promo")
            if not trials and not paid_active:
                st.info("No active stores.")
            else:
                for t in trials + paid_active:
                    s_data = t["shop"]
                    with st.container(border=True):
                        col_t1, col_t2 = st.columns([2, 1.5])
                        with col_t1:
                            st.markdown(f"**{s_data['name']}** (`{s_data.get('member_id', 'N/A')}`) — 📞 `{s_data['phone']}`")
                            st.info(f"⏳ {t['label']}")
                        with col_t2:
                            st.markdown("<div style='font-size: 0.8rem; margin-bottom: 2px;'><b>Add time:</b></div>", unsafe_allow_html=True)
                            ext_c1, ext_c2, ext_c3 = st.columns(3)
                            with ext_c1:
                                if st.button("+7d", key=f"ext7_{s_data['id']}", use_container_width=True):
                                    new_exp = datetime.now(timezone.utc) + timedelta(days=7)
                                    supabase.table("shops").update({
                                        "subscription_status": "active_paid", "trial_ends_at": new_exp.isoformat()
                                    }).eq("id", s_data["id"]).execute()
                                    st.rerun()
                            with ext_c2:
                                if st.button("+14d", key=f"ext14_{s_data['id']}", use_container_width=True):
                                    new_exp = datetime.now(timezone.utc) + timedelta(days=14)
                                    supabase.table("shops").update({
                                        "subscription_status": "active_paid", "trial_ends_at": new_exp.isoformat()
                                    }).eq("id", s_data["id"]).execute()
                                    st.rerun()
                            with ext_c3:
                                if st.button("+30d", key=f"ext30_{s_data['id']}", use_container_width=True):
                                    new_exp = datetime.now(timezone.utc) + timedelta(days=30)
                                    supabase.table("shops").update({
                                        "subscription_status": "active_paid", "trial_ends_at": new_exp.isoformat()
                                    }).eq("id", s_data["id"]).execute()
                                    st.rerun()

            st.markdown("##### 🔴 Expired Access (Needs Renewal)")
            if not expired_shops:
                st.write("No expired stores.")
            else:
                for ex in expired_shops:
                    s_data = ex["shop"]
                    with st.container(border=True):
                        col_e1, col_e2 = st.columns([1.5, 1])
                        with col_e1:
                            st.markdown(f"**{s_data['name']}** (`{s_data.get('member_id', 'N/A')}`) — 📞 `{s_data['phone']}`")
                            wa_renew = make_wa_link(s_data['phone'], f"Hello {s_data['name']}! Your free launch period on Vendora has concluded. Would you like to renew for ₦1,000/week to keep receiving orders?")
                            st.link_button("💬 WhatsApp Follow-up", wa_renew, use_container_width=True)
                        with col_e2:
                            st.markdown("<div style='font-size: 0.8rem; margin-bottom: 2px;'><b>Renew Access:</b></div>", unsafe_allow_html=True)
                            re_c1, re_c2, re_c3 = st.columns(3)
                            with re_c1:
                                if st.button("+7d", key=f"re7_{s_data['id']}", use_container_width=True):
                                    new_exp = datetime.now(timezone.utc) + timedelta(days=7)
                                    supabase.table("shops").update({
                                        "subscription_status": "active_paid", "trial_ends_at": new_exp.isoformat()
                                    }).eq("id", s_data["id"]).execute()
                                    st.rerun()
                            with re_c2:
                                if st.button("+14d", key=f"re14_{s_data['id']}", use_container_width=True):
                                    new_exp = datetime.now(timezone.utc) + timedelta(days=14)
                                    supabase.table("shops").update({
                                        "subscription_status": "active_paid", "trial_ends_at": new_exp.isoformat()
                                    }).eq("id", s_data["id"]).execute()
                                    st.rerun()
                            with re_c3:
                                if st.button("+30d", key=f"re30_{s_data['id']}", use_container_width=True):
                                    new_exp = datetime.now(timezone.utc) + timedelta(days=30)
                                    supabase.table("shops").update({
                                        "subscription_status": "active_paid", "trial_ends_at": new_exp.isoformat()
                                    }).eq("id", s_data["id"]).execute()
                                    st.rerun()

        # --- FANE 4: ESCROW & SETTLEMENTS ---
        with admin_tabs[4]:
            st.markdown("#### 💰 Paystack Escrow & Settlement Ledger")
            paid_orders = supabase.table("orders").select("*").in_("payment_status", ["escrow_funded", "settled"]).order("id", desc=True).execute().data or []
            
            tot_platform_cut = sum(o.get("platform_fee", 150) for o in paid_orders)
            tot_shop_payout = sum(o.get("item_price", 0) for o in paid_orders)
            tot_rider_payout = sum(o.get("rider_payout", 0) for o in paid_orders)

            e1, e2, e3 = st.columns(3)
            with e1:
                st.metric("💼 Debbie's Revenue (₦150 fees)", f"₦{tot_platform_cut:,}")
            with e2:
                st.metric("🏪 Store Payables", f"₦{tot_shop_payout:,}")
            with e3:
                st.metric("🛵 Rider Payables", f"₦{tot_rider_payout:,}")

            st.markdown("---")
            if not paid_orders:
                st.info("No online-paid orders yet.")
            else:
                for po in paid_orders:
                    with st.container(border=True):
                        st.markdown(f"**Order #{po['id']} — {po['product']}** (`Ref: {po.get('paystack_reference', 'N/A')}`)")
                        st.caption(f"Status: `{po['status']}` • Escrow: `{po['payment_status']}`")
                        st.markdown(f"• **Store ({po['shop']}):** ₦{po['item_price']:,} (📞 `{po['shop_phone']}`)")
                        st.markdown(f"• **Rider (ID: {po.get('courier_id', 'N/A')}):** ₦{po.get('rider_payout', 0):,}")
                        st.markdown(f"• **Debbie's Fee:** ₦{po.get('platform_fee', 150):,}")
                        
                        if po["status"] == "delivered" and po["payment_status"] == "escrow_funded":
                            if st.button(f"💸 Mark Settled (OPay Transferred)", key=f"set_{po['id']}", type="primary"):
                                supabase.table("orders").update({"payment_status": "settled"}).eq("id", po["id"]).execute()
                                st.rerun()

        # --- FANE 5: BESKEDER ---
        with admin_tabs[5]:
            st.markdown("#### Support Messages")
            msgs = supabase.table("support_messages").select("*").order("id", desc=True).execute().data or []
            for m in msgs:
                with st.container(border=True):
                    st.markdown(f"**{m['subject']}** — From `{m['sender_name']}` ({m['user_type']})")
                    st.write(m['message'])
                    st.caption(f"Phone: `{m['sender_phone']}`")
                    if st.button("🗑️ Delete", key=f"del_m_{m['id']}"):
                        supabase.table("support_messages").delete().eq("id", m["id"]).execute()
                        st.rerun()

        # --- FANE 6: KURIERER ---
        with admin_tabs[6]:
            st.markdown("#### Courier Verification")
            couriers = supabase.table("couriers").select("*").order("id", desc=True).execute().data or []
            for c in couriers:
                with st.container(border=True):
                    st.markdown(f"**{c.get('name')}** (🎟️ `{c.get('member_id')}`) — 📞 `{c.get('phone')}`")
                    st.caption(f"Area: {c.get('area')} • Status: {'🟢 Approved' if c.get('is_approved') else '⏳ Pending'}")
                    if not c.get("is_approved"):
                        if st.button("✅ Approve Courier", key=f"ap_{c['id']}"):
                            supabase.table("couriers").update({"is_approved": True}).eq("id", c["id"]).execute()
                            st.rerun()
                    if c.get("id_card_img"):
                        with st.expander("🪪 View ID"):
                            st.image(c["id_card_img"], width=280)

        # --- FANE 7: BUTIKKER ---
        with admin_tabs[7]:
            st.markdown("#### All Stores")
            for s in all_shops_list:
                with st.container(border=True):
                    st.markdown(f"**{s.get('name')}** (`{s.get('member_id')}`) — 📞 `{s.get('phone')}` — Area: `{s.get('area')}`")
                    if st.button("🗑️ Remove Store", key=f"del_s_{s['id']}"):
                        supabase.table("offers").delete().eq("shop", s["name"]).execute()
                        supabase.table("shops").delete().eq("id", s["id"]).execute()
                        st.rerun()

        # --- FANE 8: ORDRER ---
        with admin_tabs[8]:
            st.markdown("#### All Orders Overview")
            ords = supabase.table("orders").select("*").order("id", desc=True).execute().data or []
            for o in ords:
                with st.container(border=True):
                    st.markdown(f"**Order #{o['id']}** — {o['product']} (Fee: ₦{o['delivery_fee']:,})")
                    st.caption(f"From `{o['shop']}` to `{o['customer_name']}` ({o['customer_phone']}) • Delivery: **{o['status']}** • Pay: **{o.get('payment_status', 'unpaid')}**")
                    if st.button("🗑️ Delete Order", key=f"del_o_{o['id']}"):
                        supabase.table("orders").delete().eq("id", o["id"]).execute()
                        st.rerun()

# FOOTER
st.markdown("---")
footer_html = (
    "<div class='disclaimer-box'>"
    "<strong>Vendora Platform Terms & Marketplace Intermediary Notice:</strong><br>"
    "Vendora (by Debbie) is an AI-powered digital marketplace directory connecting merchants, dispatch couriers, and consumers in Lagos. "
    "Vendora does not buy, sell, warehouse, inspect, or manufacture listed goods. All transactions exist exclusively between buyer and merchant. "
    "Couriers operate as independent contractors under Nigerian commercial regulations."
    "</div>"
)
st.markdown(footer_html, unsafe_allow_html=True)
