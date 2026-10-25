import streamlit as st
from PIL import Image
import urllib.parse
import qrcode
import io

# Mobile configuration
st.set_page_config(
    page_title="Lagos Local Commerce",
    page_icon="🇳🇬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- HELPER FUNCTIONS ---
def compress_image(uploaded_file, max_width=600):
    """Compresses uploaded images to web-friendly JPEG to save mobile data."""
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    if img.width > max_width:
        ratio = max_width / float(img.width)
        height = int(float(img.height) * ratio)
        img = img.resize((max_width, height), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=75, optimize=True)
    return output.getvalue()

def make_wa_link(phone: str, product: str, price: int, shop: str) -> str:
    """Creates a direct WhatsApp link with prefilled order inquiry."""
    clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    if clean_phone.startswith("0"):
        clean_phone = "234" + clean_phone[1:]
    
    msg = f"Hello {shop}! I saw *{product}* (₦{price:,}) on Lagos Local Commerce. Is it available for delivery/pickup?"
    return f"https://wa.me/{clean_phone}?text={urllib.parse.quote(msg)}"

def generate_qr(url: str) -> bytes:
    """Generates a shop QR code as PNG bytes."""
    qr = qrcode.make(url)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

# --- INITIAL DATA (SESSION STATE) ---
if "offers" not in st.session_state:
    st.session_state.offers = [
        {
            "shop": "Mama Tobi Fresh Spices",
            "category": "Groceries & Food",
            "area": "Yaba Market",
            "is_mobile": True,
            "location_note": "Near Tejuosho main entrance today",
            "phone": "2348012345678",
            "product": "5L Pure Palm Oil + Free Pepper Mix",
            "price": 8500,
            "desc": "🔥 Original village palm oil fresh from Delta state! Buy 5L today and get free soup spice mix. Chat on WhatsApp sharp-sharp before market closes! 🍲",
            "hours_left": 36,
            "image_bytes": None
        },
        {
            "shop": "Chinedu Electronics Hub",
            "category": "Electronics",
            "area": "Ikeja (Computer Village)",
            "is_mobile": False,
            "location_note": "Otigba Street, Shop 12B",
            "phone": "2348098765432",
            "product": "20,000mAh Powerbank (Fast Charge)",
            "price": 14500,
            "desc": "⚡ No NEPA wahala! Heavy-duty fast charge powerbank can charge your phone 4 times full. 6 months shop warranty included.",
            "hours_left": 18,
            "image_bytes": None
        }
    ]

# --- UI HEADER ---
st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>🇳🇬 Lagos Local Commerce</h2>", unsafe_allow_html=True)
st.caption("<p style='text-align: center;'>Discover top deals & order directly from nearby stores</p>", unsafe_allow_html=True)

# Top navigation tabs
tab1, tab2, tab3 = st.tabs(["🛒 Browse Deals", "🏪 Store Owner Admin", "🛵 Courier / Dispatch"])

# ----------------------------------------------------
# TAB 1: CUSTOMER DISCOVERY
# ----------------------------------------------------
with tab1:
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        selected_area = st.selectbox(
            "Market / Area", 
            ["All Areas", "Yaba Market", "Ikeja (Computer Village)", "Surulere", "Balogun Market", "Lekki"]
        )
    with col_filter2:
        selected_cat = st.selectbox(
            "Category", 
            ["All Categories", "Groceries & Food", "Electronics", "Fashion & Clothing", "Home & Living"]
        )

    st.markdown("---")
    shown_count = 0
    for item in st.session_state.offers:
        if selected_area != "All Areas" and item["area"] != selected_area:
            continue
        if selected_cat != "All Categories" and item["category"] != selected_cat:
            continue
            
        shown_count += 1
        with st.container(border=True):
            if item["image_bytes"]:
                st.image(item["image_bytes"], use_container_width=True)
                
            st.markdown(f"### {item['product']}")
            st.markdown(f"**Price: ₦{item['price']:,}**")
            st.write(item["desc"])
            
            st.caption(f"🏪 **{item['shop']}** ({item['category']}) • ⏳ Expires in {item['hours_left']}h")
            
            if item["is_mobile"]:
                st.info(f"📍 **Mobile Stall Today:** {item['location_note']}")
            else:
                st.caption(f"📍 Address: {item['location_note']}")
                
            wa_url = make_wa_link(item["phone"], item["product"], item["price"], item["shop"])
            st.link_button("💬 Order via WhatsApp", wa_url, use_container_width=True)

    if shown_count == 0:
        st.info("No active deals found for this selection right now.")

# ----------------------------------------------------
# TAB 2: STORE OWNER ADMIN & AI GENERATOR
# ----------------------------------------------------
with tab2:
    st.markdown("### Post a New Deal (Active for 48 Hours)")
    
    with st.form("new_offer_form"):
        shop_name = st.text_input("Store Name *", value="Iya Basira Store")
        category = st.selectbox("Category", ["Groceries & Food", "Electronics", "Fashion & Clothing", "Home & Living"])
        area = st.selectbox("Area / Market", ["Yaba Market", "Ikeja (Computer Village)", "Surulere", "Balogun Market", "Lekki"])
        
        is_mobile = st.checkbox("This is a mobile stall (moves location daily)")
        location_note = st.text_input("Today's Location / Address *", value="Opposite Zenith Bank, Tejuosho")
        phone = st.text_input("WhatsApp Number (e.g., 08012345678) *", value="08012345678")
        
        st.markdown("---")
        product = st.text_input("What are you selling? *", value="Original Ankara Fabric (6 Yards)")
        price = st.number_input("Deal Price in Naira (₦) *", min_value=100, value=9500, step=500)
        uploaded_img = st.file_uploader("Upload product photo", type=["jpg", "jpeg", "png"])
        
        ai_language = st.radio("Ad tone & language:", ["Nigerian Pidgin (Recommended)", "Standard English"], horizontal=True)
        
        # Pre-generated AI ad template
        if ai_language == "Nigerian Pidgin (Recommended)":
            default_copy = f"🔥 Sweet deal for {area}! High quality {product} now going for just ₦{price:,}. Very limited quantity available today. Chat me sharp on WhatsApp before e finish!"
        else:
            default_copy = f"✨ Special limited-time offer at {shop_name}! Get your authentic {product} for only ₦{price:,} today in {area}. Send a direct WhatsApp message to order."
            
        desc = st.text_area("Ad Description (feel free to edit):", value=default_copy, height=100)
        
        submitted = st.form_submit_button("🚀 Publish Deal Now", use_container_width=True)
        
        if submitted:
            if not product or not shop_name or not phone:
                st.error("Please fill in all required fields marked with *.")
            else:
                img_data = compress_image(uploaded_img) if uploaded_img else None
                new_item = {
                    "shop": shop_name,
                    "category": category,
                    "area": area,
                    "is_mobile": is_mobile,
                    "location_note": location_note,
                    "phone": phone,
                    "product": product,
                    "price": price,
                    "desc": desc,
                    "hours_left": 48,
                    "image_bytes": img_data
                }
                st.session_state.offers.insert(0, new_item)
                st.success("Your deal is live for 48 hours! Check the 'Browse Deals' tab to view it.")

    st.markdown("---")
    st.markdown("### Store QR Code")
    st.caption("Print and place this on your stall counter:")
    clean_shop_slug = urllib.parse.quote(shop_name.lower().replace(" ", "-"))
    shop_demo_url = f"https://lagos-commerce.streamlit.app/?shop={clean_shop_slug}"
    qr_img = generate_qr(shop_demo_url)
    st.image(qr_img, width=160, caption=f"Scan to view {shop_name}")

# ----------------------------------------------------
# TAB 3: DISPATCH & COURIERS (PHASE 4 PREVIEW)
# ----------------------------------------------------
with tab3:
    st.markdown("### Courier & Dispatch Portal")
    st.caption("Shows how local dispatch riders (Okada / Couriers) can accept delivery runs:")
    
    with st.container(border=True):
        st.markdown("**Order #1042**")
        st.markdown("📦 **Item:** 5L Pure Palm Oil")
        st.markdown("📍 **Pickup:** Mama Tobi Spices (Yaba Market)")
        st.markdown("🎯 **Drop-off:** 14 Commercial Avenue, Sabo Yaba (approx. 1.8 km)")
        st.markdown("💵 **Delivery Fee:** ₦1,500")
        st.caption("*(Rider Payout: ₦1,350 • Platform Fee: ₦150)*")
        
        if st.button("🛵 Accept Delivery Request", key="accept_1", use_container_width=True):
            st.success("Delivery run accepted! Store and customer have been notified.")
