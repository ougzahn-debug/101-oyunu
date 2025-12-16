import streamlit as st
import base64
import time
from streamlit_autorefresh import st_autorefresh

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="101", 
    page_icon="💣", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

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

# --- CSS (MOBİL ZORLAMA MODU) ---
st.markdown("""
    <style>
    /* 1. GENEL ARKAPLAN */
    .stApp { background-color: #ECE5DD; }
    
    /* 2. SÜTUNLARI YAN YANA ZORLA (EN ÖNEMLİ KISIM) */
    /* Streamlit'in mobil modda sütunları alt alta atmasını engeller */
    [data-testid="stHorizontalBlock"] {
        flex-direction: row !important; 
        flex-wrap: nowrap !important;
    }
    
    /* Sütunların küçülmesine izin ver */
    [data-testid="column"] {
        flex: 1 !important;
        width: auto !important;
        min-width: 0px !important;
        padding: 0px 2px !important; /* Sütunlar birbirine yaklaşsın */
    }

    /* 3. BUTON TASARIMI (KARE) */
    div.stButton > button {
        background-color: #FFFFFF;
        color: #121212;
        border-radius: 6px;
        border: 1px solid #ddd;
        border-bottom: 3px solid #999;
        font-weight: 800;
        font-size: 16px; /* Mobilde çok büyük olmasın */
        width: 100%;
        padding: 0;
        aspect-ratio: 1 / 1; /* KARE OLSUN */
        margin: 0px; 
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    div.stButton > button:active {
        border-bottom: 0px;
        transform: translateY(3px);
    }
    
    /* 4. SAYFA KENAR BOŞLUKLARI */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 6rem !important; /* Manage app butonu üstüne gelmesin */
        padding-left: 0.2rem !important;
        padding-right: 0.2rem !important;
    }
    
    /* 5. OYUNCU KARTLARI */
    .player-card {
        background-color: white; padding: 4px; border-radius: 4px;
        text-align: center; margin-bottom: 5px; font-size: 11px;
        color: #333; border-left: 3px solid #ccc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .active-turn { background-color: #dcf8c6; border-left: 3px solid #25D366; font-weight: bold;}
    .eliminated { background-color: #ffe6e6; border-left: 3px solid #ff3b30; text-decoration: line-through; opacity: 0.6; }
    
    /* GİZLEME */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
#               UYGULAMA AKIŞI
# ==========================================

if not store.active:
    # --- LOBİ ---
    st.markdown("<h3 style='text-align: center; color: #075E54; margin:0;'>💣 101 Lobi</h3>", unsafe_allow_html=True)
    
    if len(store.players) == 0:
        store.max_num = st.number_input("Limit", 10, 200, 101)
    
    # Mobilde form yan yana sığsın
    c1, c2 = st.columns([2, 1])
    join_name = c1.text_input("İsim", placeholder="Adın?")
    join_num = c2.number_input("Sayı", 1, store.max_num, step=1)
    
    if st.button("KATIL", type="primary", use_container_width=True):
        err = store.add_player(join_name, int(join_num))
        if err: st.error(err)
        else: st.rerun()

    st.write("---")
    
    # Bekleyenler (Yan yana 3 kişi sığdır)
    if store.players:
        cols = st.columns(3)
        for i, p in enumerate(store.players):
            with cols[i % 3]:
                st.markdown(f"<div class='player-card' style='border-left: 3px solid #128C7E;'>{p['name']}</div>", unsafe_allow_html=True)

    if len(store.players) >= 2:
        st.write("")
        if st.button("BAŞLAT 🚀", type="primary", use_container_width=True):
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
        <div style="background-color: #075E54; color: white; padding: 20px; border-radius: 15px; text-align: center; margin-top: 20px;">
            <h2 style="color:#FFD700; margin:0;">{store.loser}</h2>
            <p>Hesaplar Onda!</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("LOBİYE DÖN ♻️", type="primary", use_container_width=True):
            store.reset()
            st.rerun()
    else:
        # KİMLİK SEÇİMİ
        player_names = [p['name'] for p in store.players]
        my_identity = st.selectbox("Ben Kimim?", ["Seçiniz..."] + player_names, label_visibility="collapsed")
        
        if my_identity == "Seçiniz...":
            st.warning("👆 İsmini seç!")
            st.stop()
            
        current_player_name = store.players[store.turn_index]['name']
        
        # SIRA BİLGİSİ
        if my_identity == current_player_name:
            st.success(f"🟢 SIRA SENDE!")
        else:
            st.info(f"⏳ {current_player_name}")

        # OYUNCU KARTLARI (3 Sütun - Mobilde daha iyi sığar)
        p_cols = st.columns(3)
        for i, p in enumerate(store.players):
            css = "player-card"
            if p['status'] == 'eliminated': css += " eliminated"
            elif i == store.turn_index: css += " active-turn"
            with p_cols[i % 3]:
                st.markdown(f"<div class='{css}'>{p['name']}</div>", unsafe_allow_html=True)

        st.write("---")

        # SAYI TABLOSU (SABİT 4 SÜTUN)
        # CSS ile zorladığımız için artık yan yana duracaklar
        GRID_COLS = 4
        btn_cols = st.columns(GRID_COLS)
        
        for i in range(1, store.max_num + 1):
            c_idx = (i-1) % GRID_COLS
            col = btn_cols[c_idx]
            
            if i in store.clicked:
                owner = next((p for p in store.players if p['number'] == i), None)
                if owner:
                    col.error("💥")
                else:
                    # Boşluğu koru (Görünmez kutu)
                    col.markdown("<div style='height: 40px'></div>", unsafe_allow_html=True)
            else:
                is_my_turn = (my_identity == current_player_name)
                # Buton
                if col.button(str(i), key=f"btn_{i}", disabled=not is_my_turn):
                    make_move(i, my_identity)
                    st.rerun()
