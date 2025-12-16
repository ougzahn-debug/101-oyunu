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

# --- EKRAN GENİŞLİĞİNİ ÖLÇ (JS) ---
# Bu kod tarayıcının genişliğini alır.
# Genelde telefonlar 768px'den küçüktür.
ui_width = st_javascript("window.innerWidth")

# Eğer JS yüklenmediyse veya ilk açılışsa varsayılan olarak Mobil kabul et (Güvenli mod)
if ui_width is None:
    ui_width = 400 

is_mobile = ui_width < 768

# --- DİNAMİK AYARLAR ---
if is_mobile:
    GRID_COLS = 4       # Mobilde 4 sütun (Kare ve büyük butonlar)
    PLAYER_COLS = 2     # Mobilde oyuncular 2'li dizilir
    BTN_HEIGHT = "60px" # Mobilde buton yüksekliği
    FONT_SIZE = "20px"  # Mobilde yazı boyutu
else:
    GRID_COLS = 10      # PC'de 10 sütun (Geniş görünüm)
    PLAYER_COLS = 4     # PC'de oyuncular 4'lü dizilir
    BTN_HEIGHT = "50px"
    FONT_SIZE = "16px"

# --- CSS (CİHAZA GÖRE DEĞİŞEN STİL) ---
st.markdown(f"""
    <style>
    /* GENEL */
    .stApp {{ background-color: #ECE5DD; }}
    
    /* ÜST BOŞLUKLARI YOK ET (MOBİL İÇİN KRİTİK) */
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }}
    
    /* BUTON TASARIMI */
    div.stButton > button {{
        background-color: #FFFFFF;
        color: #121212;
        border-radius: 12px;
        border: none;
        border-bottom: 4px solid #cfcfcf;
        font-weight: 900;
        font-size: {FONT_SIZE};
        width: 100%;
        height: {BTN_HEIGHT}; /* Cihaza göre değişir */
        margin-bottom: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.1s;
    }}
    div.stButton > button:active {{
        border-bottom: 0px;
        transform: translateY(4px);
    }}
    
    /* OYUNCU KARTLARI */
    .player-card {{
        background-color: white; 
        padding: 8px; 
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1); 
        text-align: center;
        margin-bottom: 8px;
        font-size: 14px;
        color: #333;
        border-left: 5px solid #ccc;
    }}
    .active-turn {{ 
        background-color: #dcf8c6; 
        border-left: 5px solid #25D366;
        font-weight: bold;
        transform: scale(1.02);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }}
    .eliminated {{ 
        background-color: #ffe6e6; 
        border-left: 5px solid #ff3b30;
        color: #ff3b30;
        text-decoration: line-through; 
        opacity: 0.7;
    }}
    
    /* INPUT ALANLARI */
    .stTextInput input, .stNumberInput input {{
        border-radius: 10px;
        border: 2px solid #128C7E;
        padding: 10px;
        font-size: 16px; /* Mobilde zoom yapmaması için 16px */
    }}
    
    /* HEADER/FOOTER GİZLE */
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    </style>
""", unsafe_allow_html=True)

# --- GLOBAL HAFIZA ---
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
        if not name: return "İsim boş olamaz."
        if any(p['name'].lower() == name.lower() for p in self.players): return "İsim alınmış."
        if number in self.taken_numbers: return "Bu sayı seçildi!"
        if not (1 <= number <= self.max_num): return f"Sayı 1-{self.max_num} arası olmalı."
        
        self.players.append({'name': name, 'number': number, 'status': 'active'})
        self.taken_numbers.add(number)
        return None

if "store" not in st.session_state:
    st.session_state.store = GameState()
store = st.session_state.store

# --- CANLI SENKRONİZASYON ---
st_autorefresh(interval=2000, key="sync")

# --- SES ---
def play_sound():
    try:
        with open("patlama.wav", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""<audio autoplay="true"><source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>"""
            st.markdown(md, unsafe_allow_html=True)
    except: pass

# --- OYUN FONKSİYONLARI ---
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
#               UYGULAMA AKIŞI
# ==========================================

# EKRAN MODU BİLGİSİ (DEBUG İÇİN DEĞİL, KULLANICI GÖRSÜN DİYE)
# st.caption(f"Cihaz Modu: {'📱 Mobil' if is_mobile else '💻 PC'} (Genişlik: {ui_width}px)")

if not store.active:
    # --- LOBİ ---
    st.markdown("<h1 style='text-align: center; color: #075E54;'>💣 101 Lobi</h1>", unsafe_allow_html=True)
    
    if len(store.players) == 0:
        store.max_num = st.number_input("Oyun Limiti", 10, 200, 101)
    
    c1, c2 = st.columns([2, 1])
    join_name = c1.text_input("İsim", placeholder="Adın ne?")
    # Mobilde sayı klavyesi açılması için step=1 önemli
    join_num = c2.number_input("Gizli Sayı", 1, store.max_num, step=1) 
    
    if st.button("K A T I L", type="primary", use_container_width=True):
        err = store.add_player(join_name, int(join_num))
        if err: st.error(err)
        else: st.rerun()

    st.markdown("---")
    st.markdown(f"<div style='text-align:center; font-weight:bold; color:#555;'>Bekleyenler: {len(store.players)} Kişi</div>", unsafe_allow_html=True)
    
    if store.players:
        # Lobi kartları da cihaza göre dizilsin
        cols = st.columns(PLAYER_COLS) 
        for i, p in enumerate(store.players):
            with cols[i % PLAYER_COLS]:
                st.markdown(f"""
                <div class="player-card" style="border-left: 5px solid #128C7E;">
                    👤 {p['name']} <br> 🔒 Hazır
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    
    if len(store.players) >= 2:
        if st.button("🚀 BAŞLAT", type="primary", use_container_width=True):
            store.active = True
            store.logs.append("Oyun Başladı!")
            st.rerun()
    else:
        st.info("En az 2 kişi bekleniyor...")

else:
    # --- OYUN EKRANI ---
    if store.boom_trigger:
        play_sound()
        time.sleep(1)
        store.boom_trigger = False

    if store.game_over:
        st.balloons()
        st.markdown(f"""
        <div style="background-color: #075E54; color: white; padding: 30px; border-radius: 20px; text-align: center; margin-top: 20px;">
            <h1 style="color:white; font-size: 2.5rem;">KAYBEDEN</h1>
            <h2 style="color:#FFD700; font-size: 2rem; text-transform: uppercase;">{store.loser}</h2>
            <p>Hesaplar Onda!</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        if st.button("♻️ LOBİYE DÖN", type="secondary", use_container_width=True):
            store.reset()
            st.rerun()
            
    else:
        # KİMLİK & SIRA
        player_names = [p['name'] for p in store.players]
        my_identity = st.selectbox("Ben Kimim?", ["Seçiniz..."] + player_names, label_visibility="collapsed")
        
        if my_identity == "Seçiniz...":
            st.warning("👆 Lütfen yukarıdan ismini seç!")
            st.stop()
            
        current_player_name = store.players[store.turn_index]['name']
        
        # SIRA BİLGİSİ (YAPIŞKAN GİBİ ÜSTTE)
        if my_identity == current_player_name:
            st.success(f"🟢 SIRA SENDE! BİR KUTU SEÇ.")
        else:
            st.info(f"⏳ SIRA: {current_player_name}")

        # OYUNCU KARTLARI (DİNAMİK KOLON)
        p_cols = st.columns(PLAYER_COLS)
        for i, p in enumerate(store.players):
            css = "player-card"
            stat = "Online"
            if p['status'] == 'eliminated':
                css += " eliminated"
                stat = "ELENDİ"
            elif i == store.turn_index:
                css += " active-turn"
                stat = "YAZIYOR..."
                
            with p_cols[i % PLAYER_COLS]:
                st.markdown(f"""
                <div class="{css}">
                    <div>{p['name']}</div>
                    <div style="font-size:10px; color:#666;">{stat}</div>
                </div>
                """, unsafe_allow_html=True)

        if store.logs:
            st.caption(f"Son: {store.logs[-1]}")
        
        st.divider()

        # SAYI TABLOSU (GRID - CİHAZA GÖRE DEĞİŞİR)
        # Mobilde 4 sütun, PC'de 10 sütun
        btn_cols = st.columns(GRID_COLS)
        
        for i in range(1, store.max_num + 1):
            c_idx = (i-1) % GRID_COLS
            col = btn_cols[c_idx]
            
            if i in store.clicked:
                owner = next((p for p in store.players if p['number'] == i), None)
                if owner:
                    col.error("💥")
                else:
                    # Boş buton ama yükseklik korunmalı
                    col.markdown(f"<div style='height: {BTN_HEIGHT};'></div>", unsafe_allow_html=True)
            else:
                is_my_turn = (my_identity == current_player_name)
                if col.button(str(i), key=f"b{i}", disabled=not is_my_turn):
                    make_move(i, my_identity)
                    st.rerun()
