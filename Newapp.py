import streamlit as st
from PIL import Image, ImageOps
from supabase import create_client, Client
from datetime import datetime, timezone
import urllib.parse
import qrcode
import io
import base64

# Mobil opsætning
st.set_page_config(
    page_title="Lagos Local Commerce",
    page_icon="🇳🇬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS der tvinger produktbilleder til et kompakt, pænt kort-format på både mobil og PC
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
</style>
""", unsafe_allow_html=True)

# Forbindelse til Supabase
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# --- HJÆLPEFUNKTIONER ---
def convert_to_base64_img(uploaded_file, target_size=(500, 375)):
    """Beskærer og skalerer nye billeder, så de fylder minimalt i databasen."""
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

def make_wa_link(phone: str, product: str, price: int, shop: str) -> str:
    clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    if clean_phone.startswith("0"):
        clean_phone = "234" + clean_phone[1:]
    msg = f"Hello {shop}! I saw *{product}* (₦{price:,}) on Lagos Local Commerce. Is it available for delivery/pickup?"
    return f"https://wa.me/{clean_phone}?text={urllib.parse.quote(msg)}"

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

# --- NAVIGATION ---
if "current_view" not in st.session_state:
    st.session_state.current_view = "🛒 Browse Deals"

st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>🇳🇬 Lagos Local Commerce</h2>", unsafe_allow_html=True)
st.caption("<p style='text-align: center;'>Discover top deals & order directly from nearby stores</p>", unsafe_allow_html=True)

views = ["🛒 Browse Deals", "🏪 Store Owner Admin", "🛵 Courier / Dispatch"]
current_tab = st.radio("Nav", views, index=views.index(st.session_state.current_view), horizontal=True, label_visibility="collapsed")
st.session_state.current_view = current_tab

# ====================================================
# VISNING 1: KUNDEPORTAL
# ====================================================
if st.session_state.current_view == "🛒 Browse Deals":
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
            # Viser billedet i den kompakte ramme (max 200px høj)
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
            
            if item.get("is_mobile"):
                st.info(f"📍 **Mobile Stall Today:** {item.get('location_note')}")
            else:
                st.caption(f"📍 Address: {item.get('location_note')}")
                
            if status == "active":
                wa_url = make_wa_link(item["phone"], item["product"], item["price"], item["shop"])
                st.link_button("💬 Order via WhatsApp", wa_url, use_container_width=True)
            else:
                st.button("Item Unavailable", disabled=True, use_container_width=True)

# ====================================================
# VISNING 2: BUTIKSEJER ADMIN
# ====================================================
elif st.session_state.current_view == "🏪 Store Owner Admin":
    st.markdown("### Manage Store Deals")
    
    current_shop = st.selectbox(
        "Select your shop to manage:",
        ["Sweet Debbie & Mom's Kitchen", "Chinedu Electronics Hub"]
    )
    
    st.markdown("#### Your Active Deals")
    my_offers_res = supabase.table("offers").select("*").eq("shop", current_shop).order("id", desc=True).execute()
    my_offers = my_offers_res.data or []
    
    if not my_offers:
        st.write("You don't have any deals posted right now.")
    else:
        for deal in my_offers:
            with st.container(border=True):
                st.markdown(f"**{deal['product']}** — ₦{deal['price']:,}")
                st.caption(f"Status: `{deal.get('status', 'active')}` • Expires in: {calculate_hours_left(deal['expires_at'])}h")
                
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if st.button("🟢 In Stock", key=f"stock_{deal['id']}"):
                        supabase.table("offers").update({"status": "active"}).eq("id", deal["id"]).execute()
                        st.rerun()
                with col_btn2:
                    if st.button("⛔ Sold Out", key=f"sold_{deal['id']}"):
                        supabase.table("offers").update({"status": "sold_out"}).eq("id", deal["id"]).execute()
                        st.rerun()
                with col_btn3:
                    if st.button("⏳ Back Tomorrow", key=f"tom_{deal['id']}"):
                        supabase.table("offers").update({"status": "back_tomorrow"}).eq("id", deal["id"]).execute()
                        st.rerun()
                
                if st.button("🗑️ Delete Deal", key=f"del_{deal['id']}", type="secondary"):
                    supabase.table("offers").delete().eq("id", deal["id"]).execute()
                    st.success("Deal deleted permanently!")
                    st.rerun()

    st.markdown("---")
    
    st.markdown("#### Post a New 48-Hour Deal")
    category = st.selectbox("Category", ["Groceries & Food", "Electronics", "Fashion & Clothing", "Home & Living"])
    area = st.selectbox("Area / Market", ["Yaba Market", "Ikeja (Computer Village)", "Surulere", "Balogun Market", "Lekki"])
    
    is_mobile = st.checkbox("This is a mobile stall (moves location daily)", value=True)
    location_note = st.text_input("Today's Location / Address *", value="Near Tejuosho main entrance today")
    phone = st.text_input("WhatsApp Number *", value="08012345678")
    
    product = st.text_input("What are you selling? *", value="Fresh Homemade Abacha with Coconut")
    price = st.number_input("Deal Price in Naira (₦) *", min_value=50, value=200, step=50)
    
    uploaded_file = st.file_uploader("Product Photo (Optional)", type=["jpg", "jpeg", "png", "webp"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Preview", width=180)
        
    ai_language = st.radio("Ad tone & language:", ["Nigerian Pidgin (Recommended)", "Standard English"], horizontal=True)
    if ai_language == "Nigerian Pidgin (Recommended)":
        default_copy = f"🔥 Sweet deal for {area}! High quality {product} now going for just ₦{price:,}. Very limited quantity available today. Chat me sharp on WhatsApp before e finish!"
    else:
        default_copy = f"🥗 Fresh homemade {product} for only ₦{price:,} today in {area}! Bulk orders available on demand. Chat with us on WhatsApp to order!"
    desc = st.text_area("Ad Description:", value=default_copy, height=80)
    
    if st.button("🚀 Publish to Lagos Commerce (Saves Forever)", type="primary", use_container_width=True):
        if not product or not phone:
            st.error("Please enter both product name and WhatsApp number.")
        else:
            final_img = convert_to_base64_img(uploaded_file) if uploaded_file else None
            
            new_data = {
                "shop": current_shop,
                "category": category,
                "area": area,
                "is_mobile": is_mobile,
                "location_note": location_note,
                "phone": phone,
                "product": product,
                "price": int(price),
                "description": desc,
                "img_src": final_img,
                "status": "active"
            }
            supabase.table("offers").insert(new_data).execute()
            st.session_state.current_view = "🛒 Browse Deals"
            st.rerun()

    st.markdown("---")
    st.markdown("### Store QR Code")
    clean_shop_slug = urllib.parse.quote(current_shop.lower().replace(" ", "-"))
    shop_demo_url = f"https://lagos-commerce-pzru6e8tsftfmt72gbjnhz.streamlit.app/?shop={clean_shop_slug}"
    qr_img = generate_qr(shop_demo_url)
    st.image(qr_img, width=160, caption=f"Scan to view {current_shop}")

# ====================================================
# VISNING 3: BUDE & KURÉR
# ====================================================
elif st.session_state.current_view == "🛵 Courier / Dispatch":
    st.markdown("### Courier & Dispatch Portal")
    with st.container(border=True):
        st.markdown("**Order #1042**")
        st.markdown("📦 **Item:** Fresh Homemade Abacha with Coconut (Bulk Order: 10 packs)")
        st.markdown("📍 **Pickup:** Sweet Debbie & Mom's Kitchen (Yaba Market)")
        st.markdown("🎯 **Drop-off:** 14 Commercial Avenue, Sabo Yaba (approx. 1.8 km)")
        st.markdown("💵 **Delivery Fee:** ₦1,500")
        st.caption("*(Rider Payout: ₦1,350 • Platform Fee: ₦150)*")
        if st.button("🛵 Accept Delivery Request", key="accept_1", use_container_width=True):
            st.success("Delivery run accepted! Store and customer have been notified.")
