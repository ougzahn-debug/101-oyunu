import streamlit as st
import base64
import time
from streamlit_autorefresh import st_autorefresh
from streamlit_javascript import st_javascript

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="101", 
    page_icon="💣", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# ==========================================
#          1. PLATFORM TANIMA (JS)
# ==========================================
# Tarayıcının genişliğini ölçüyoruz.
# Genelde telefonlar 768px'den küçüktür.
ui_width = st_javascript("window.innerWidth")

# Eğer değer okunamazsa varsayılan olarak MOBİL kabul et (Güvenlik önlemi)
if ui_width is None or ui_width == 0:
    is_mobile = True 
else:
    is_mobile = ui_width < 768

# --- CİHAZA GÖRE DEĞİŞKENLER ---
if is_mobile:
    # TELEFON AYARLARI
    GRID_COLS = 4        # 4 Sütun
    BTN_HEIGHT = "auto"  # Kare olması için
    ASPECT_RATIO = "1/1" # Tam Kare
    CONTAINER_PADDING = "0.5rem" # Kenarlar çok dar
    MAX_WIDTH = "100%"   # Ekranı tam kapla
    GAP_SIZE = "0px"     # Boşluk yok
else:
    # PC AYARLARI
    GRID_COLS = 10       # 10 Sütun (Geniş)
    BTN_HEIGHT = "50px"  # Dikdörtgen butonlar
    ASPECT_RATIO = "auto"
    CONTAINER_PADDING = "2rem" 
    MAX_WIDTH = "800px"  # Ekranın ortasında 800px yer kapla
    GAP_SIZE = "0.5rem"  # Hafif boşluk olsun

# ==========================================
#          2. CSS (TASARIM MOTORU)
# ==========================================
st.markdown(f"""
    <style>
    /* GENEL ARKAPLAN */
    .stApp {{ background-color: #ECE5DD; }}
    
    /* ANA KONTEYNER (PC'de Ortalar, Mobilde Yayılır) */
    .block-container {{
        max-width: {MAX_WIDTH} !important;
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        padding-left: {CONTAINER_PADDING} !important;
        padding-right: {CONTAINER_PADDING} !important;
        margin: auto !important; /* Ortala */
    }}
    
    /* SÜTUN YAPISI */
    [data-testid="stHorizontalBlock"] {{
        gap: {GAP_SIZE} !important;
    }}
    
    [data-testid="column"] {{
        padding: 1px !important;
        min-width: 0 !important;
    }}

    /* BUTONLAR */
    div.stButton > button {{
        background-color: #FFFFFF;
        color: #121212;
        border-radius: 6px;
        border: 1px solid #ccc;
        border-bottom: 3px solid #bbb;
        font-weight: 800;
        font-size: 14px;
        width: 100%;
        height: {BTN_HEIGHT} !important;
        aspect-ratio: {ASPECT_RATIO} !important;
        margin: 0px !important;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }}
    div.stButton > button:active {{
        border-bottom: 0px;
        transform: translateY(3px);
    }}
    
    /* INPUT ALANLARI (Küçültülmüş) */
    .stTextInput input, .stNumberInput input {{
        min-height: 0px !important;
        height: 40px !important;
        font-size: 14px !important;
    }}
    
    /* OYUNCU KARTLARI */
    .player-card {{
        background: white; border: 1px solid #ddd; border-radius: 4px; 
        text-align: center; font-size: 12px; padding: 2px;
        white-space: nowrap; overflow: hidden; margin-bottom: 2px;
    }}
    .turn-indicator {{ border: 2px solid #25D366; background: #eaffea; font-weight:bold; }}
    .eliminated {{ background: #ffebeb; text-decoration: line-through; color: red; opacity: 0.6; }}
    
    /* GİZLEME */
    header, footer {{display: none !important;}}
    </style>
""", unsafe_allow_html=True)

# ==========================================
#          3. OYUN MANTIĞI (DEĞİŞMEDİ)
# ==========================================

@st.cache_resource
class GameState:
    def __init__(self):
        self.reset()
    def reset(self):
        self.active = False
        self.players = []
        self.clicked = set()
        self.taken_numbers = set()
        self.max_num = 101
        self.turn_index = 0
        self.game_over = False
        self.loser = ""
        self.boom_trigger = False
        self.logs = []
    def add_player(self, name, number):
        name = name.strip()
        if not name: return "İsim yok!"
        if any(p['name'].lower() == name.lower() for p in self.players): return "İsim dolu!"
        if number in self.taken_numbers: return "Sayı dolu!"
        if not (1 <= number <= self.max_num): return f"1-{self.max_num} arası."
        self.players.append({'name': name, 'number': number, 'status': 'active'})
        self.taken_numbers.add(number)
        return None

if "store" not in st.session_state:
    st.session_state.store = GameState()
store = st.session_state.store

st_autorefresh(interval=2000, key="sync")

def play_sound():
    try:
        with open("patlama.wav", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""<audio autoplay="true"><source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>"""
            st.markdown(md, unsafe_allow_html=True)
    except: pass

def make_move(number, player_name):
    store.clicked.add(number)
    hit_index = None
    for i, p in enumerate(store.players):
        if p['number'] == number and p['status'] == 'active':
            hit_index = i
            break
    if hit_index is not None:
        victim = store.players[hit_index]['name']
        store.players[hit_index]['status'] = 'eliminated'
        store.logs.append(f"💥 {player_name} -> {victim}")
        active_p = [p for p in store.players if p['status'] == 'active']
        if len(active_p) == 1:
            store.game_over = True
            store.loser = active_p[0]['name']
            store.boom_trigger = True
    alive_count = sum(1 for p in store.players if p['status'] == 'active')
    if alive_count > 1:
        next_idx = (store.turn_index + 1) % len(store.players)
        while store.players[next_idx]['status'] != 'active':
            next_idx = (next_idx + 1) % len(store.players)
        store.turn_index = next_idx

# ==========================================
#          4. EKRAN ÇİZİMİ
# ==========================================

# Başlık (Sadece Lobi Modunda Göster)
if not store.active:
    st.markdown("<h3 style='text-align:center; margin:0; color:#075E54;'>💣 101 Lobi</h3>", unsafe_allow_html=True)

# --- A. LOBİ EKRANI ---
if not store.active:
    
    # Kompakt Giriş Satırı
    c1, c2, c3 = st.columns([3, 2, 2])
    with c1: join_name = st.text_input("", placeholder="İsim", label_visibility="collapsed")
    with c2: join_num = st.number_input("", 1, store.max_num, label_visibility="collapsed")
    with c3: 
        if st.button("KATIL", type="primary", use_container_width=True):
            err = store.add_player(join_name, int(join_num))
            if err: st.toast(err)
            else: st.rerun()

    st.caption(f"Bekleyenler: {len(store.players)}")
    
    # Bekleyenler (Mobilde 4'lü sığar mı? Sığar çünkü sadece isim yazıyoruz)
    if store.players:
        p_cols_count = 4 if is_mobile else 6 # PC'de daha çok yan yana koy
        cols = st.columns(p_cols_count)
        for i, p in enumerate(store.players):
            with cols[i % p_cols_count]:
                st.markdown(f"<div class='mini-card'>👤 {p['name']}</div>", unsafe_allow_html=True)
    
    st.write("---")
    if len(store.players) >= 2:
        if st.button("BAŞLAT 🚀", type="secondary", use_container_width=True):
            store.active = True
            store.logs.append("Oyun Başladı!")
            st.rerun()

# --- B. OYUN EKRANI ---
else:
    if store.boom_trigger:
        play_sound()
        time.sleep(1)
        store.boom_trigger = False

    if store.game_over:
        st.balloons()
        st.error(f"KAYBEDEN: {store.loser}")
        if st.button("YENİ OYUN", use_container_width=True):
            store.reset()
            st.rerun()
    else:
        # Kimlik Seçimi
        p_names = ["Kimsin?"] + [p['name'] for p in store.players]
        my_id = st.selectbox("", p_names, label_visibility="collapsed")
        
        # Sıra Göstergesi
        curr_p = store.players[store.turn_index]['name']
        if my_id == curr_p:
            st.markdown(f"<div style='background:#dcf8c6; padding:5px; text-align:center; border-radius:5px; margin-bottom:5px; font-weight:bold; color:#075E54;'>🟢 SIRA SENDE!</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background:#fff; border:1px solid #ccc; padding:5px; text-align:center; border-radius:5px; margin-bottom:5px; font-size:12px;'>⏳ Sıra: {curr_p}</div>", unsafe_allow_html=True)

        # Oyuncu Durumları (Kartlar)
        # Mobilde 4 yan yana (sıkışık), PC'de 6 yan yana
        card_cols = 4 if is_mobile else 6
        p_cols = st.columns(card_cols)
        
        for i, p in enumerate(store.players):
            css = "player-card"
            if p['status'] == 'eliminated': css += " eliminated"
            elif i == store.turn_index: css += " turn-indicator"
            
            with p_cols[i % card_cols]:
                st.markdown(f"<div class='{css}'>{p['name']}</div>", unsafe_allow_html=True)

        # SAYI TABLOSU (KRİTİK KISIM)
        # Mobilde 4 Sütun, PC'de 10 Sütun
        btn_cols = st.columns(GRID_COLS)
        
        for i in range(1, store.max_num + 1):
            idx = (i-1) % GRID_COLS
            col = btn_cols[idx]
            
            if i in store.clicked:
                owner = next((p for p in store.players if p['number'] == i), None)
                if owner:
                    col.error("💥")
                else:
                    # Mobilde kare boşluk, PC'de dikdörtgen boşluk
                    style = "height:100%; width:100%;" if is_mobile else "height:50px;"
                    col.markdown(f"<div style='{style}'></div>", unsafe_allow_html=True)
            else:
                is_turn = (my_id == curr_p)
                if col.button(str(i), key=f"b{i}", disabled=not is_turn):
                    make_move(i, my_id)
                    st.rerun()
