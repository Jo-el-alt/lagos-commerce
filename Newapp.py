import streamlit as st
from PIL import Image
import urllib.parse
import qrcode
import io
import base64

# Mobile configuration
st.set_page_config(
    page_title="Lagos Local Commerce",
    page_icon="🇳🇬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- HELPER FUNCTIONS ---
def convert_to_base64_img(uploaded_file, max_width=600):
    """Krymper billedet og laver det til en ren base64-streng, så det aldrig forsvinder."""
    try:
        img = Image.open(uploaded_file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        if img.width > max_width:
            ratio = max_width / float(img.width)
            height = int(float(img.height) * ratio)
            img = img.resize((max_width, height), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75, optimize=True)
        encoded = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{encoded}"
    except Exception:
        # Hvis billedet fejler, gemmes raw data som fallback
        try:
            encoded = base64.b64encode(uploaded_file.getvalue()).decode()
            return f"data:image/jpeg;base64,{encoded}"
        except Exception:
            return None

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
            "shop": "Sweet Debbie & Mom's Kitchen",
            "category": "Groceries & Food",
            "area": "Yaba Market",
            "is_mobile": True,
            "location_note": "Near Tejuosho main entrance today",
            "phone": "2348012345678",
            "product": "Fresh Homemade Abacha with Coconut",
            "price": 200,
            "desc": "🥗 100% fresh, homemade Abacha with sweet crunchy coconut! Prepared daily with clean village ingredients. Only ₦200 per portion. We also produce & deliver bulk orders for events, meetings, and parties! Chat us on WhatsApp now to place your order.",
            "hours_left": 48,
            "img_src": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80"
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
            "img_src": "https://images.unsplash.com/photo-1609592424109-dd9892f1b177?w=600&auto=format&fit=crop&q=80"
        }
    ]

# Styrer hvilken fane der er aktiv
if "current_view" not in st.session_state:
    st.session_state.current_view = "🛒 Browse Deals"

# --- UI HEADER ---
st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>🇳🇬 Lagos Local Commerce</h2>", unsafe_allow_html=True)
st.caption("<p style='text-align: center;'>Discover top deals & order directly from nearby stores</p>", unsafe_allow_html=True)

# Radio knapper i toppen fungerer mere stabilt end standard tabs ved opdateringer
views = ["🛒 Browse Deals", "🏪 Store Owner Admin", "🛵 Courier / Dispatch"]
current_tab = st.radio(
    "Navigation", 
    views, 
    index=views.index(st.session_state.current_view), 
    horizontal=True, 
    label_visibility="collapsed"
)
st.session_state.current_view = current_tab

# ----------------------------------------------------
# VISNING 1: CUSTOMER DISCOVERY
# ----------------------------------------------------
if st.session_state.current_view == "🛒 Browse Deals":
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
            if item.get("img_src"):
                st.image(item["img_src"], use_container_width=True)
                
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
# VISNING 2: STORE OWNER ADMIN
# ----------------------------------------------------
elif st.session_state.current_view == "🏪 Store Owner Admin":
    st.markdown("### Post a New Deal (Active for 48 Hours)")
    
    shop_name = st.text_input("Store Name *", value="Sweet Debbie & Mom's Kitchen")
    category = st.selectbox("Category", ["Groceries & Food", "Electronics", "Fashion & Clothing", "Home & Living"])
    area = st.selectbox("Area / Market", ["Yaba Market", "Ikeja (Computer Village)", "Surulere", "Balogun Market", "Lekki"])
    
    is_mobile = st.checkbox("This is a mobile stall (moves location daily)", value=True)
    location_note = st.text_input("Today's Location / Address *", value="Near Tejuosho main entrance today")
    phone = st.text_input("WhatsApp Number *", value="08012345678")
    
    st.markdown("---")
    product = st.text_input("What are you selling? *", value="Fresh Jollof Rice & Fried Fish")
    price = st.number_input("Deal Price in Naira (₦) *", min_value=50, value=1500, step=50)
    
    st.markdown("**Product Photo (Optional)**")
    uploaded_file = st.file_uploader("Select or snap photo", type=["jpg", "jpeg", "png", "webp"], key="img_uploader")
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Selected photo preview", width=220)

    ai_language = st.radio("Ad tone & language:", ["Nigerian Pidgin (Recommended)", "Standard English"], horizontal=True)
    
    if ai_language == "Nigerian Pidgin (Recommended)":
        default_copy = f"🔥 Correct deal for {area}! Sweet {product} ready now for only ₦{price:,}. Send WhatsApp sharp before e finish!"
    else:
        default_copy = f"🥗 Fresh and hot {product} available today at {shop_name} for just ₦{price:,}! Order directly on WhatsApp."
        
    desc = st.text_area("Ad Description:", value=default_copy, height=100)
    
    if st.button("🚀 Publish Deal Now", type="primary", use_container_width=True):
        if not product or not shop_name or not phone:
            st.error("Please fill in Store Name, Product Name, and WhatsApp Number.")
        else:
            final_img = convert_to_base64_img(uploaded_file) if uploaded_file else None
            
            new_offer = {
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
                "img_src": final_img
            }
            # Indsæt øverst
            st.session_state.offers.insert(0, new_offer)
            # Skift automatisk visning til forsiden
            st.session_state.current_view = "🛒 Browse Deals"
            st.rerun()

    st.markdown("---")
    st.markdown("### Store QR Code")
    clean_shop_slug = urllib.parse.quote(shop_name.lower().replace(" ", "-"))
    shop_demo_url = f"https://lagos-commerce-pzru6e8tsftfmt72gbjnhz.streamlit.app/?shop={clean_shop_slug}"
    qr_img = generate_qr(shop_demo_url)
    st.image(qr_img, width=160, caption=f"Scan for {shop_name}")

# ----------------------------------------------------
# VISNING 3: DISPATCH & COURIERS
# ----------------------------------------------------
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
