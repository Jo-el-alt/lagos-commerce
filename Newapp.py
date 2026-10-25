import streamlit as st
from PIL import Image, ImageOps
from supabase import create_client, Client
from datetime import datetime, timezone
import urllib.parse
import qrcode
import io
import base64
import re

# Mobil opsætning
st.set_page_config(
    page_title="Lagos Local Commerce",
    page_icon="🇳🇬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS til faste mobilbilleder og footer
st.markdown("""
<style>
    .product-img-box {
        width: 100%;
        max-width: 400px;
        height: 200px;
        overflow: hidden;
        border-radius: 10px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #f0f2f6;
    }
    .product-img-box img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .privacy-notice {
        font-size: 0.82rem;
        color: #555;
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        margin-top: 25px;
    }
</style>
""", unsafe_allow_html=True)

# Supabase forbindelse
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# --- HJÆLPEFUNKTIONER ---
def make_slug(name: str) -> str:
    clean = re.sub(r'[^a-zA-Z0-9\s-]', '', name).strip().lower()
    return re.sub(r'[\s-]+', '-', clean)

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

# URL Parametre & Sessions
query_params = st.query_params
active_shop_slug = query_params.get("shop", None)

if "current_view" not in st.session_state:
    st.session_state.current_view = "🛒 Browse Deals"

if "logged_shop" not in st.session_state:
    st.session_state.logged_shop = None

if "logged_courier" not in st.session_state:
    st.session_state.logged_courier = None

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>🇳🇬 Lagos Local Commerce</h2>", unsafe_allow_html=True)
st.caption("<p style='text-align: center;'>Discover top deals & order directly from nearby stores</p>", unsafe_allow_html=True)

views = ["🛒 Browse Deals", "🏪 Store Owner Admin", "🛵 Courier / Dispatch", "🛡️ Platform Admin"]
current_tab = st.radio("Nav", views, index=views.index(st.session_state.current_view), horizontal=True, label_visibility="collapsed")
st.session_state.current_view = current_tab

# ====================================================
# VISNING 1: KUNDEPORTAL & BESTILLING
# ====================================================
if st.session_state.current_view == "🛒 Browse Deals":
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
            sel_area = st.selectbox("Market / Area", ["All Areas", "Yaba Market", "Ikeja (Computer Village)", "Surulere", "Balogun Market", "Lekki"])
        with c2:
            sel_cat = st.selectbox("Category", ["All Categories", "Groceries & Food", "Electronics", "Fashion & Clothing", "Home & Living"])

        st.markdown("---")
        now_iso = datetime.now(timezone.utc).isoformat()
        query = supabase.table("offers").select("*").gt("expires_at", now_iso).order("id", desc=True)
        if sel_area != "All Areas":
            query = query.eq("area", sel_area)
        if sel_cat != "All Categories":
            query = query.eq("category", sel_cat)
        res = query.execute()
        offers = res.data or []

    if not offers:
        st.info("No active deals found right now. Check back soon!")

    for item in offers:
        hours_left = calculate_hours_left(item["expires_at"])
        status = item.get("status", "active")
        
        with st.container(border=True):
            if item.get("img_src"):
                st.markdown(
                    f'<div class="product-img-box"><img src="{item["img_src"]}" alt="Product"></div>',
                    unsafe_allow_html=True
                )
                
            st.markdown(f"### {item['product']}")
            st.markdown(f"**Price: ₦{item['price']:,}**")
            st.write(item.get("description", ""))
            
            if status == "sold_out":
                st.error("⛔ Sold Out for Today")
            elif status == "back_tomorrow":
                st.warning("⏳ Sold Out – Back Fresh Tomorrow Morning!")
            else:
                st.success("🟢 In Stock Now")
            
            st.caption(f"🏪 **{item['shop']}** ({item['category']}) • ⏳ Expires in {hours_left}h")
            
            pickup_loc = item.get("location_note") or f"{item['shop']}, {item['area']}"
            if item.get("is_mobile"):
                st.info(f"📍 **Mobile Stall Today:** {pickup_loc}")
            else:
                st.caption(f"📍 Address: {pickup_loc}")
                
            if status == "active":
                wa_msg = f"Hello {item['shop']}! I saw *{item['product']}* (₦{item['price']:,}) on Lagos Local Commerce. Is it available?"
                wa_url = make_wa_link(item["phone"], wa_msg)
                st.link_button("💬 Chat on WhatsApp", wa_url, use_container_width=True)
                
                with st.expander("🛵 Request Dispatch Delivery to Your Door"):
                    with st.form(f"order_form_{item['id']}"):
                        cust_name = st.text_input("Your Full Name *", placeholder="e.g. Tunde Bakare")
                        cust_phone = st.text_input("Your Phone Number (WhatsApp) *", placeholder="080...")
                        cust_area = st.selectbox("Your Area / Neighborhood *", ["Yaba / Sabo", "Ikeja / Allen", "Surulere", "Victoria Island / Lekki", "Other"], key=f"area_{item['id']}")
                        cust_addr = st.text_area("Full Delivery Address & Landmark *", placeholder="e.g. 14 Commercial Ave, Sabo, opposite First Bank")
                        
                        st.markdown(f"**Item Price:** ₦{item['price']:,}")
                        st.markdown("**Estimated Delivery Fee:** ₦1,500")
                        st.markdown(f"**Total to Pay:** ₦{item['price'] + 1500:,}")
                        
                        order_consent = st.checkbox("I consent to share my contact & delivery details with the merchant and assigned rider for order fulfillment.", value=True)
                        
                        btn_order = st.form_submit_button("🚀 Confirm Delivery Order", type="primary", use_container_width=True)
                        if btn_order:
                            if not cust_name or not cust_phone or not cust_addr:
                                st.error("Please fill in your Name, Phone, and Delivery Address.")
                            elif not order_consent:
                                st.error("Please agree to the delivery data consent.")
                            else:
                                new_order = {
                                    "offer_id": item["id"],
                                    "product": item["product"],
                                    "shop": item["shop"],
                                    "shop_phone": item["phone"],
                                    "pickup_location": pickup_loc,
                                    "customer_name": cust_name.strip(),
                                    "customer_phone": cust_phone.strip(),
                                    "customer_area": cust_area,
                                    "delivery_address": cust_addr.strip(),
                                    "item_price": item["price"],
                                    "delivery_fee": 1500,
                                    "rider_payout": 1350,
                                    "platform_fee": 150,
                                    "status": "pending"
                                }
                                supabase.table("orders").insert(new_order).execute()
                                st.success("✅ Delivery order placed! A verified dispatch rider will pick it up.")
            else:
                st.button("Item Unavailable", disabled=True, use_container_width=True)

# ====================================================
# VISNING 2: BUTIKSEJER ADMIN & OPRETTELSE
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
                new_pin = st.text_input("Create a 4-Digit Secret PIN *", type="password", max_chars=4, placeholder="4 digits e.g. 2468")
                new_area = st.selectbox("Market / Area *", ["Yaba Market", "Ikeja (Computer Village)", "Surulere", "Balogun Market", "Lekki"])
                new_cat = st.selectbox("Main Category *", ["Groceries & Food", "Electronics", "Fashion & Clothing", "Home & Living"])
                
                # NDPA Samtykkeboks
                shop_consent = st.checkbox("I agree that my shop details and phone number are displayed to customers for business and orders in accordance with NDPA.")
                
                if st.button("🚀 Complete Registration & Enter", type="primary", use_container_width=True):
                    if not new_shop_name or not new_phone or not new_pin or len(new_pin) != 4:
                        st.error("Please fill all required fields and ensure PIN is 4 digits.")
                    elif not shop_consent:
                        st.error("Please accept the data processing terms to register.")
                    else:
                        clean_phone = new_phone.strip()
                        existing = supabase.table("shops").select("id").eq("phone", clean_phone).execute()
                        if existing.data:
                            st.error("Phone number already registered. Please log in.")
                        else:
                            unique_slug = f"{make_slug(new_shop_name)}-{clean_phone[-4:]}"
                            shop_record = {
                                "slug": unique_slug, "name": new_shop_name.strip(), "phone": clean_phone,
                                "pin": new_pin.strip(), "area": new_area, "category": new_cat
                            }
                            ins = supabase.table("shops").insert(shop_record).execute()
                            if ins.data:
                                st.session_state.logged_shop = ins.data[0]
                                st.rerun()
    else:
        shop = st.session_state.logged_shop
        col_hdr1, col_hdr2 = st.columns([3, 1])
        with col_hdr1:
            st.markdown(f"### 🏪 {shop['name']}")
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
        product = st.text_input("Product Name *")
        price = st.number_input("Deal Price in Naira (₦) *", min_value=50, value=1000, step=50)
        uploaded_file = st.file_uploader("Photo (Optional)", type=["jpg", "jpeg", "png", "webp"])
        ai_language = st.radio("Ad language:", ["Nigerian Pidgin (Recommended)", "Standard English"], horizontal=True)
        
        if ai_language == "Nigerian Pidgin (Recommended)":
            default_copy = f"🔥 Sweet deal for {shop['area']}! High quality {product} for just ₦{price:,}. Chat on WhatsApp sharp!"
        else:
            default_copy = f"✨ Fresh {product} available at {shop['name']} for ₦{price:,}. Order via WhatsApp!"
        desc = st.text_area("Ad Description:", value=default_copy, height=70)
        
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
                st.session_state.current_view = "🛒 Browse Deals"
                st.rerun()

        st.markdown("---")
        st.markdown("### Store QR Code")
        direct_shop_url = f"https://lagos-commerce-pzru6e8tsftfmt72gbjnhz.streamlit.app/?shop={shop['slug']}"
        st.image(generate_qr(direct_shop_url), width=160, caption=f"Scan for {shop['name']}")

# ====================================================
# VISNING 3: BUDE & KURÉR (MED NDPA SAMTYKKE)
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
            st.caption("To prevent fraud and protect stores, all riders must upload a valid ID card for admin verification.")
            with st.container(border=True):
                r_name = st.text_input("Rider / Company Full Name *", placeholder="e.g. Ibrahim Babatunde")
                r_phone_new = st.text_input("Phone Number (WhatsApp) *", placeholder="080...")
                r_pin_new = st.text_input("Create 4-Digit PIN *", type="password", max_chars=4, placeholder="1234")
                r_area = st.selectbox("Primary Operating Area", ["Yaba / Sabo", "Ikeja / Maryland", "Surulere", "Island / Lekki", "All Lagos"])
                vehicle = st.selectbox("Vehicle Type", ["Motorcycle (Okada)", "Bicycle", "Van / Car"])
                
                st.markdown("**Upload Government ID (NIN Slip, Voter's Card, or Driver's License) ***")
                id_file = st.file_uploader("Snap or upload clear photo of ID", type=["jpg", "jpeg", "png", "webp"], key="id_uploader")
                if id_file:
                    st.image(id_file, width=220, caption="Uploaded ID Preview")
                
                # NDPA Samtykkeboks for bude
                rider_consent = st.checkbox("I consent to upload my ID solely for verification under Nigeria Data Protection Act (NDPA). I understand I can request profile deletion anytime.")
                
                if st.button("🚀 Submit Profile for Verification", type="primary", use_container_width=True):
                    if not r_name or not r_phone_new or not r_pin_new or len(r_pin_new) != 4 or not id_file:
                        st.error("Please fill in all details, 4-digit PIN, and upload your ID card.")
                    elif not rider_consent:
                        st.error("Please acknowledge the data consent to register.")
                    else:
                        id_base64 = convert_to_base64_img(id_file, target_size=(600, 400))
                        r_data = {
                            "name": r_name.strip(),
                            "phone": r_phone_new.strip(),
                            "pin": r_pin_new.strip(),
                            "area": r_area,
                            "vehicle": vehicle,
                            "id_card_img": id_base64,
                            "is_approved": False
                        }
                        ins = supabase.table("couriers").insert(r_data).execute()
                        if ins.data:
                            st.session_state.logged_courier = ins.data[0]
                            st.rerun()
    else:
        rider_res = supabase.table("couriers").select("*").eq("id", st.session_state.logged_courier["id"]).execute()
        rider = rider_res.data[0] if rider_res.data else st.session_state.logged_courier
        
        c_hdr1, c_hdr2 = st.columns([3, 1])
        with c_hdr1:
            st.markdown(f"### 🛵 Rider: {rider['name']}")
            st.caption(f"📍 Area: {rider['area']} • 🛵 {rider.get('vehicle', 'Motorcycle')}")
        with c_hdr2:
            if st.button("🚪 Log Out", key="rider_logout", use_container_width=True):
                st.session_state.logged_courier = None
                st.rerun()

        st.markdown("---")
        
        if not rider.get("is_approved", False):
            st.warning("⏳ **Account Under Review (Pending Verification)**")
            st.info("Your ID document has been submitted. For safety reasons, our local coordinator in Lagos must review and verify your identity before you can see or accept delivery jobs.")
            st.caption("You will receive a WhatsApp message once your profile is approved.")
        else:
            st.success("🛡️ **Verified Dispatch Rider (Approved)**")
            
            st.markdown("#### 📦 Your Accepted Deliveries")
            my_jobs = supabase.table("orders").select("*").eq("courier_id", rider["id"]).neq("status", "delivered").order("id", desc=True).execute().data or []
            
            if not my_jobs:
                st.info("You don't have any active delivery runs right now.")
            else:
                for job in my_jobs:
                    with st.container(border=True):
                        st.markdown(f"**Order #{job['id']} — {job['product']}**")
                        st.markdown(f"🏪 **Pickup:** {job['shop']} ({job['pickup_location']}) — 📞 `{job['shop_phone']}`")
                        st.markdown(f"🎯 **Drop-off:** {job['customer_name']} ({job['customer_area']}) — 📞 `{job['customer_phone']}`")
                        st.markdown(f"📍 **Address:** {job['delivery_address']}")
                        st.markdown(f"💵 **Collect from Customer:** ₦{job['item_price'] + job['delivery_fee']:,} *(Your pay: ₦{job['rider_payout']:,})*")
                        st.caption(f"Status: **{job['status'].upper()}**")
                        
                        wa_pickup = make_wa_link(job['shop_phone'], f"Hello {job['shop']}, I am verified rider {rider['name']}. I am coming to pick up Order #{job['id']}.")
                        wa_cust = make_wa_link(job['customer_phone'], f"Hello {job['customer_name']}, I am verified rider {rider['name']} delivering your {job['product']}.")
                        
                        cw1, cw2 = st.columns(2)
                        with cw1:
                            st.link_button("💬 WhatsApp Shop", wa_pickup, use_container_width=True)
                        with cw2:
                            st.link_button("💬 WhatsApp Customer", wa_cust, use_container_width=True)
                            
                        cb1, cb2 = st.columns(2)
                        with cb1:
                            if job["status"] == "accepted":
                                if st.button("📦 Mark as Picked Up", key=f"pk_{job['id']}", use_container_width=True):
                                    supabase.table("orders").update({"status": "picked_up"}).eq("id", job["id"]).execute()
                                    st.rerun()
                        with cb2:
                            if st.button("✅ Mark as Delivered", key=f"dl_{job['id']}", type="primary", use_container_width=True):
                                supabase.table("orders").update({"status": "delivered"}).eq("id", job["id"]).execute()
                                st.success(f"Delivery completed! ₦{job['rider_payout']:,} credited to your summary.")
                                st.rerun()

            st.markdown("---")
            st.markdown("#### ⚡ Available Delivery Jobs Nearby")
            open_jobs = supabase.table("orders").select("*").eq("status", "pending").order("id", desc=True).execute().data or []
            
            if not open_jobs:
                st.write("No pending delivery jobs right now. Check back shortly!")
            else:
                for ojob in open_jobs:
                    with st.container(border=True):
                        st.markdown(f"**{ojob['product']}** (₦{ojob['item_price']:,})")
                        st.markdown(f"📍 **Pickup:** {ojob['shop']} — {ojob['pickup_location']}")
                        st.markdown(f"🎯 **Drop-off Area:** {ojob['customer_area']}")
                        st.markdown(f"💵 **Your Payout:** **₦{ojob['rider_payout']:,}** *(Total fee: ₦{ojob['delivery_fee']:,})*")
                        
                        if st.button("🛵 Accept Delivery Job", key=f"acc_{ojob['id']}", type="primary", use_container_width=True):
                            supabase.table("orders").update({
                                "status": "accepted",
                                "courier_id": rider["id"],
                                "courier_name": rider["name"]
                            }).eq("id", ojob["id"]).execute()
                            st.rerun()

# ====================================================
# VISNING 4: PLATFORM SUPER ADMIN
# ====================================================
elif st.session_state.current_view == "🛡️ Platform Admin":
    st.markdown("### 🛡️ Platform Super Admin")
    
    if not st.session_state.admin_logged_in:
        st.caption("Enter Super Admin PIN to manage database records, shops, and couriers.")
        admin_pass = st.text_input("Admin PIN", type="password", placeholder="Master key")
        
        if st.button("Unlock Admin Panel", type="primary"):
            if admin_pass == "lagos2026":
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Incorrect Admin PIN! (Default is: lagos2026)")
                
    else:
        c_a1, c_a2 = st.columns([3, 1])
        with c_a1:
            st.success("🔓 Super Admin Mode Active")
        with c_a2:
            if st.button("🔒 Lock Admin"):
                st.session_state.admin_logged_in = False
                st.rerun()

        st.markdown("---")
        
        st.markdown("#### 🔍 Quick Lookup (Forgotten PIN / Support)")
        search_query = st.text_input("Search by phone number or name (Store or Rider):", placeholder="e.g. 08012345678 or Ibrahim")
        
        if search_query.strip():
            sq = search_query.strip().lower()
            clean_sq = re.sub(r'[^0-9]', '', sq)
            
            all_shops_lookup = supabase.table("shops").select("*").execute().data or []
            matched_shops = [s for s in all_shops_lookup if (sq in s["name"].lower()) or (clean_sq and clean_sq in s["phone"])]
            
            all_couriers_lookup = supabase.table("couriers").select("*").execute().data or []
            matched_couriers = [c for c in all_couriers_lookup if (sq in c["name"].lower()) or (clean_sq and clean_sq in c["phone"])]
            
            if not matched_shops and not matched_couriers:
                st.warning(f"No shop or courier found matching '{search_query}'.")
            else:
                for s in matched_shops:
                    with st.container(border=True):
                        st.markdown(f"🏪 **STORE: {s['name']}**")
                        st.markdown(f"📞 **Phone:** `{s['phone']}` | 🔑 **PIN:** `{s['pin']}`")
                        wa_pin_msg = f"Hello {s['name']}! Your login PIN for Lagos Local Commerce is: {s['pin']}."
                        st.link_button(f"💬 Send PIN on WhatsApp", make_wa_link(s['phone'], wa_pin_msg), use_container_width=True)

                for c in matched_couriers:
                    with st.container(border=True):
                        st.markdown(f"🛵 **COURIER: {c['name']}**")
                        st.markdown(f"📞 **Phone:** `{c['phone']}` | 🔑 **PIN:** `{c['pin']}` | Status: **{'✅ Approved' if c.get('is_approved') else '⏳ Pending'}**")
                        wa_rider_pin = f"Hello {c['name']}! Your rider PIN for Lagos Local Commerce is: {c['pin']}."
                        st.link_button(f"💬 Send PIN on WhatsApp", make_wa_link(c['phone'], wa_rider_pin), use_container_width=True)
                        
        st.markdown("---")

        admin_tabs = st.tabs(["🛵 Riders Verification & Management", "🏪 All Stores", "📦 All Orders", "🔥 All Offers"])

        with admin_tabs[0]:
            st.markdown("#### Couriers & Identity Verification")
            all_couriers = supabase.table("couriers").select("*").order("id", desc=True).execute().data or []
            if not all_couriers:
                st.info("No couriers registered yet.")
            for c in all_couriers:
                with st.container(border=True):
                    is_appr = c.get("is_approved", False)
                    col_cr1, col_cr2 = st.columns([2, 1])
                    with col_cr1:
                        st.markdown(f"**{c['name']}** — 📞 `{c['phone']}`")
                        st.caption(f"Area: {c['area']} • Vehicle: {c.get('vehicle', 'Okada')} • PIN: `{c['pin']}`")
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
                            if st.button("⛔ Revoke Approval", key=f"rev_{c['id']}", use_container_width=True):
                                supabase.table("couriers").update({"is_approved": False}).eq("id", c["id"]).execute()
                                st.rerun()
                                
                        if st.button("🗑️ Delete Rider", key=f"adm_del_c_{c['id']}", type="secondary", use_container_width=True):
                            supabase.table("couriers").delete().eq("id", c["id"]).execute()
                            st.rerun()
                            
                    if c.get("id_card_img"):
                        with st.expander("🪪 View Uploaded ID Document"):
                            st.image(c["id_card_img"], width=300, caption=f"ID Document: {c['name']}")
                    else:
                        st.caption("*(No ID document uploaded)*")

        with admin_tabs[1]:
            st.markdown("#### Registered Shops")
            all_shops = supabase.table("shops").select("*").order("id", desc=True).execute().data or []
            if not all_shops:
                st.info("No shops found.")
            for s in all_shops:
                with st.container(border=True):
                    col_s1, col_s2 = st.columns([3, 1])
                    with col_s1:
                        st.markdown(f"**{s['name']}**")
                        st.caption(f"Phone: `{s['phone']}` • PIN: `{s['pin']}` • Area: `{s['area']}`")
                    with col_s2:
                        if st.button("🗑️ Delete", key=f"adm_del_shop_{s['id']}", type="secondary"):
                            supabase.table("offers").delete().eq("shop", s["name"]).execute()
                            supabase.table("shops").delete().eq("id", s["id"]).execute()
                            st.success(f"Deleted {s['name']}")
                            st.rerun()

        with admin_tabs[2]:
            st.markdown("#### All Orders / Deliveries")
            all_orders = supabase.table("orders").select("*").order("id", desc=True).execute().data or []
            if not all_orders:
                st.info("No orders found.")
            for o in all_orders:
                with st.container(border=True):
                    col_o1, col_o2 = st.columns([3, 1])
                    with col_o1:
                        st.markdown(f"**Order #{o['id']}** — {o['product']} (₦{o['item_price']:,})")
                        st.caption(f"Customer: `{o['customer_name']}` ({o['customer_phone']}) • Status: **{o['status']}**")
                        st.caption(f"From: `{o['shop']}` ➡️ To: `{o['delivery_address']}`")
                    with col_o2:
                        if st.button("🗑️ Delete", key=f"adm_del_ord_{o['id']}"):
                            supabase.table("orders").delete().eq("id", o["id"]).execute()
                            st.rerun()

        with admin_tabs[3]:
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
# GLOBAL PRIVACY FOOTER (NDPA COMPLIANCE NOTICE)
# ====================================================
st.markdown("---")
st.markdown("""
<div class="privacy-notice">
    <strong>🔒 Privacy & Data Protection Notice (NDPA / NDPR Compliance)</strong><br>
    Lagos Local Commerce processes user data (phone numbers, store locations, delivery addresses, and courier accreditation documents) strictly for commerce enablement, security vetting, and order delivery. We do not sell or disclose personal data to unauthorized third parties. All registered users reserve the right to access, rectify, or request immediate permanent deletion of their account records by contacting support.
</div>
""", unsafe_allow_html=True)
