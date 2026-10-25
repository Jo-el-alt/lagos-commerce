import streamlit as st
from PIL import Image
import urllib.parse
import qrcode
import io

st.set_page_config(
    page_title="Lagos Local Commerce",
    page_icon="🇳🇬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

def compress_image(uploaded_file, max_width=600):
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
    clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    if clean_phone.startswith("0"):
        clean_phone = "234" + clean_phone[1:]
    msg = f"Hello {shop}! I saw *{product}* (₦{price:,}) on Lagos Local Commerce. Is it available?"
    return f"https://wa.me/{clean_phone}?text={urllib.parse.quote(msg)}"

def generate_qr(url: str) -> bytes:
    qr = qrcode.make(url)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

if "offers" not in st.session_state:
    st.session_state.offers = [
        {
            "shop": "Mama Tobi Fresh Spices",
            "category": "Fødevarer",
            "area": "Yaba Market",
            "is_mobile": True,
            "location_note": "Ved hovedindgangen mod Tejuosho i dag",
            "phone": "2348012345678",
            "product": "5L Frisk Palmeolie + Gratis Peber-mix",
            "price": 8500,
            "desc": "🔥 Orijinal village palm oil fresh from Delta state! Buy 5L today make you get free soup spice mix. Fast WhatsApp order! 🍲",
            "hours_left": 36,
            "image_bytes": None
        },
        {
            "shop": "Chinedu Electronics Hub",
            "category": "Elektronik",
            "area": "Ikeja (Computer Village)",
            "is_mobile": False,
            "location_note": "Otigba Street, Shop 12B",
            "phone": "2348098765432",
            "product": "20.000mAh Powerbank (Fast Charge)",
            "price": 14500,
            "desc": "⚡ No NEPA wahala! Heavy-duty fast charge powerbank fit charge your phone 4 times full. 6 months warranty.",
            "hours_left": 18,
            "image_bytes": None
        }
    ]

st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>🇳🇬 Lagos Local Commerce</h2>", unsafe_allow_html=True)
st.caption("<p style='text-align: center;'>Hurtig handel i dit nærområde</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🛒 Find Tilbud", "🏪 Butiksejer Admin", "🛵 Kurér / Bude"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        sel_area = st.selectbox("Område / Marked", ["Alle områder", "Yaba Market", "Ikeja (Computer Village)", "Surulere", "Balogun Market", "Lekki"])
    with c2:
        sel_cat = st.selectbox("Kategori", ["Alle kategorier", "Fødevarer", "Elektronik", "Tøj & Mode", "Husholdning"])

    st.markdown("---")
    shown = 0
    for item in st.session_state.offers:
        if sel_area != "Alle områder" and item["area"] != sel_area:
            continue
        if sel_cat != "Alle kategorier" and item["category"] != sel_cat:
            continue
        shown += 1
        with st.container(border=True):
            if item["image_bytes"]:
                st.image(item["image_bytes"], use_container_width=True)
            st.markdown(f"### {item['product']}")
            st.markdown(f"**Pris: ₦{item['price']:,}**")
            st.write(item["desc"])
            st.caption(f"🏪 **{item['shop']}** ({item['category']}) • ⏳ Udløber om {item['hours_left']}t")
            if item["is_mobile"]:
                st.info(f"📍 **Flytbar bod i dag:** {item['location_note']}")
            else:
                st.caption(f"📍 Adresse: {item['location_note']}")
            wa_url = make_wa_link(item["phone"], item["product"], item["price"], item["shop"])
            st.link_button("💬 Bestil / Spørg via WhatsApp", wa_url, use_container_width=True)
    if shown == 0:
        st.info("Ingen tilbud fundet i dette område lige nu.")

with tab2:
    st.markdown("### Opret nyt tilbud (Udløber om 48 timer)")
    with st.form("new_offer_form"):
        shop_name = st.text_input("Butiksnavn *", value="Iya Basira Store")
        category = st.selectbox("Kategori", ["Fødevarer", "Elektronik", "Tøj & Mode", "Husholdning"])
        area = st.selectbox("Område", ["Yaba Market", "Ikeja (Computer Village)", "Surulere", "Balogun Market", "Lekki"])
        is_mobile = st.checkbox("Dette er en flytbar bod (skifter placering)")
        location_note = st.text_input("Placering / Adresse i dag *", value="Overfor Zenith Bank, Tejuosho")
        phone = st.text_input("WhatsApp-nummer *", value="08012345678")
        st.markdown("---")
        product = st.text_input("Hvad sælger du? *", value="Original Ankara Stof (6 Yards)")
        price = st.number_input("Tilbudspris i Naira (₦) *", min_value=100, value=9500, step=500)
        uploaded_img = st.file_uploader("Tag eller upload et billede", type=["jpg", "jpeg", "png"])
        desc = st.text_area("Annoncetekst:", value=f"🔥 Special offer! High quality {product} for only ₦{price:,} today in {area}. Chat on WhatsApp!")
        submitted = st.form_submit_button("🚀 Offentliggør tilbud nu", use_container_width=True)
        
        if submitted:
            img_data = compress_image(uploaded_img) if uploaded_img else None
            st.session_state.offers.insert(0, {
                "shop": shop_name, "category": category, "area": area, "is_mobile": is_mobile,
                "location_note": location_note, "phone": phone, "product": product, "price": price,
                "desc": desc, "hours_left": 48, "image_bytes": img_data
            })
            st.success("Tilbuddet er oprettet! Gå til fanen 'Find Tilbud' for at se det.")

    st.markdown("---")
    st.markdown("### Butikkens QR-kode")
    qr_img = generate_qr(f"https://lagos-commerce.streamlit.app/?shop={urllib.parse.quote(shop_name.lower())}")
    st.image(qr_img, width=160, caption=f"Scan for {shop_name}")

with tab3:
    st.markdown("### Bude & Kurérpanel")
    with st.container(border=True):
        st.markdown("**Ordre #1042**")
        st.markdown("📦 **Vare:** 5L Frisk Palmeolie")
        st.markdown("📍 **Afhentning:** Mama Tobi Spices (Yaba Market)")
        st.markdown("🎯 **Levering til:** Sabo Yaba (ca. 1,8 km)")
        st.markdown("💵 **Leveringspris:** ₦1.500 *(Bud: ₦1.350 | Provision: ₦150)*")
        if st.button("🛵 Accepter levering", use_container_width=True):
            st.success("Opgave accepteret!")
