import streamlit as st
import base64
import time
from streamlit_autorefresh import st_autorefresh

# --- SAYFA AYARLARI (MOBİL İÇİN ÖNEMLİ) ---
st.set_page_config(
    page_title="101 Mobil", 
    page_icon="💣", 
    layout="wide", # Ekranı tam kapla
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
st_autorefresh(interval=2000, key="mobile_sync")

# --- MOBİL UYUMLU CSS (SİHİR BURADA) ---
st.markdown("""
    <style>
    /* 1. GENEL ZEMİN */
    .stApp { background-color: #ECE5DD; }
    
    /* 2. GEREKSİZ BOŞLUKLARI SİL (HACK) */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
    }
    
    /* 3. BUTONLARI KARE VE BÜYÜK YAP */
    div.stButton > button {
        background-color: #FFFFFF;
        color: #121212;
        border-radius: 12px;
        border: none;
        border-bottom: 3px solid #cfcfcf; /* 3D Efekt */
        font-weight: 900;
        font-size: 18px;
        width: 100%;
        aspect-ratio: 1 / 1; /* Kare Oranı */
        margin-bottom: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    div.stButton > button:active {
        border-bottom: none;
        transform: translateY(3px);
    }
    div.stButton > button:disabled {
        background-color: transparent;
        border: none;
        color: transparent;
    }
    
    /* 4. OYUNCU KARTLARI */
    .player-card {
        background-color: white; 
        padding: 8px; 
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2); 
        text-align: center;
        margin-bottom: 8px;
        font-size: 14px;
        color: #333;
        border-left: 5px solid #ccc;
    }
    .active-turn { 
        background-color: #dcf8c6; 
        border-left: 5px solid #25D366;
        transform: scale(1.02);
        font-weight: bold;
    }
    .eliminated { 
        background-color: #ffe6e6; 
        border-left: 5px solid #ff3b30;
        color: #ff3b30;
        text-decoration: line-through; 
    }
    
    /* 5. INPUT ALANLARI GÜZELLEŞTİRME */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 12px;
        border: 2px solid #128C7E;
        padding: 10px;
    }
    
    /* 6. BAŞLIKLAR */
    h1 { font-size: 1.8rem; text-align: center; color: #075E54; margin-bottom: 10px; }
    .status-bar { text-align: center; font-weight: bold; color: #555; margin-bottom: 10px; }

    /* 7. MOBİLDE GİZLE (Header/Footer) */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    </style>
""", unsafe_allow_html=True)

# --- SES ---
def play_sound():
    try:
        with open("patlama.wav", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""<audio autoplay="true"><source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>"""
            st.markdown(md, unsafe_allow_html=True)
    except: pass

# --- OYUN MANTIĞI ---
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
    else:
        pass

    alive_count = sum(1 for p in store.players if p['status'] == 'active')
    if alive_count > 1:
        next_idx = (store.turn_index + 1) % len(store.players)
        while store.players[next_idx]['status'] != 'active':
            next_idx = (next_idx + 1) % len(store.players)
        store.turn_index = next_idx

# ==========================================
#               UYGULAMA AKIŞI
# ==========================================

if not store.active:
    # --- LOBİ ---
    st.markdown("<h1>💣 101 Lobi</h1>", unsafe_allow_html=True)
    
    if len(store.players) == 0:
        store.max_num = st.number_input("Oyun Limiti", 10, 200, 101)
    
    c1, c2 = st.columns([2, 1])
    join_name = c1.text_input("İsim", placeholder="Adın ne?")
    join_num = c2.number_input("Sayı", 1, store.max_num, step=1, label_visibility="visible") 
    
    if st.button("K A T I L", type="primary", use_container_width=True):
        err = store.add_player(join_name, int(join_num))
        if err: st.error(err)
        else: st.rerun()

    st.markdown("---")
    st.markdown(f"<div class='status-bar'>Bekleyenler: {len(store.players)} Kişi</div>", unsafe_allow_html=True)
    
    # Bekleyenleri şık kartlarla göster
    if store.players:
        cols = st.columns(2) # Mobilde yan yana 2 kişi
        for i, p in enumerate(store.players):
            with cols[i % 2]:
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
        <div style="background-color: #075E54; color: white; padding: 30px; border-radius: 20px; text-align: center; margin-top: 50px;">
            <h1 style="color:white; font-size: 3rem;">KAYBEDEN</h1>
            <h2 style="color:#FFD700; font-size: 2.5rem; text-transform: uppercase;">{store.loser}</h2>
            <p>Hesaplar Onda!</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        if st.button("♻️ LOBİYE DÖN", type="secondary", use_container_width=True):
            store.reset()
            st.rerun()
            
    else:
        # KİMLİK SEÇİMİ (MOBİL İÇİN SELECTBOX EN İYİSİDİR)
        player_names = [p['name'] for p in store.players]
        # Label'ı gizle, placeholder kullan
        my_identity = st.selectbox("Ben Kimim?", ["Seçiniz..."] + player_names, label_visibility="collapsed")
        
        if my_identity == "Seçiniz...":
            st.warning("👆 Önce yukarıdan ismini seç!")
            st.stop()
            
        current_player_name = store.players[store.turn_index]['name']
        
        # SIRA BİLGİSİ
        if my_identity == current_player_name:
            st.success(f"🟢 SIRA SENDE! BİR KUTU SEÇ.")
        else:
            st.info(f"⏳ SIRA: {current_player_name}")

        # OYUNCU KARTLARI (MOBİL İÇİN 2 SÜTUN)
        # 4 sütun mobilde çok sıkışır, 2 idealdir.
        p_cols = st.columns(2)
        for i, p in enumerate(store.players):
            css = "player-card"
            stat = "Online"
            if p['status'] == 'eliminated':
                css += " eliminated"
                stat = "ELENDİ"
            elif i == store.turn_index:
                css += " active-turn"
                stat = "YAZIYOR..."
                
            with p_cols[i % 2]:
                st.markdown(f"""
                <div class="{css}">
                    <div>{p['name']}</div>
                    <div style="font-size:10px; color:#666;">{stat}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # SAYI TABLOSU (GRID)
        # Mobilde en rahat basılan oran 4 sütundur. 5 bazen parmak kalınsa zorlar.
        # Ama 101 sayısı için 5 daha simetrik. Butonları kare yaptığımız için 5 de kurtarır.
        grid_cols = 5
        btn_cols = st.columns(grid_cols)
        
        for i in range(1, store.max_num + 1):
            c_idx = (i-1) % grid_cols
            col = btn_cols[c_idx]
            
            if i in store.clicked:
                # Tıklananları kontrol et
                owner = next((p for p in store.players if p['number'] == i), None)
                if owner:
                    col.error("💥") # Patlama ikonu
                else:
                    # Boş buton (Görünmez ama yer kaplar)
                    col.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
            else:
                is_my_turn = (my_identity == current_player_name)
                # Buton oluştur
                if col.button(str(i), key=f"b{i}", disabled=not is_my_turn):
                    make_move(i, my_identity)
                    st.rerun()
