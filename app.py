import streamlit as st
import base64
import time
from streamlit_autorefresh import st_autorefresh

# --- SAYFA AYARLARI ---
# layout="centered" yaparak otomatikman ortalıyoruz ve daraltıyoruz.
st.set_page_config(
    page_title="101 Lobi", 
    page_icon="💣", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# ==========================================
#          1. OYUN MANTIĞI (LOGIC)
# ==========================================
class GameRoom:
    def __init__(self, room_name, max_num):
        self.name = room_name
        self.active = False
        self.players = []
        self.clicked = set()
        self.taken_numbers = set()
        self.max_num = max_num
        self.turn_index = 0
        self.game_over = False
        self.loser = ""
        self.boom_trigger = False
        self.logs = []

    def add_player(self, name, number):
        name = name.strip()
        if not name: return "İsim giriniz."
        if any(p['name'].lower() == name.lower() for p in self.players): return "Bu isim alınmış."
        if number in self.taken_numbers: return "Bu sayı seçilmiş."
        if not (1 <= number <= self.max_num): return f"1-{self.max_num} arası giriniz."
        
        self.players.append({'name': name, 'number': number, 'status': 'active'})
        self.taken_numbers.add(number)
        return None

    def make_move(self, number, player_name):
        self.clicked.add(number)
        hit_index = None
        for i, p in enumerate(self.players):
            if p['number'] == number and p['status'] == 'active':
                hit_index = i
                break
        
        if hit_index is not None:
            victim = self.players[hit_index]['name']
            self.players[hit_index]['status'] = 'eliminated'
            self.logs.append(f"💥 {player_name} -> {victim}")
            
            active_p = [p for p in self.players if p['status'] == 'active']
            if len(active_p) == 1:
                self.game_over = True
                self.loser = active_p[0]['name']
                self.boom_trigger = True
        
        alive_count = sum(1 for p in self.players if p['status'] == 'active')
        if alive_count > 1:
            next_idx = (self.turn_index + 1) % len(self.players)
            while self.players[next_idx]['status'] != 'active':
                next_idx = (next_idx + 1) % len(self.players)
            self.turn_index = next_idx

@st.cache_resource
class RoomManager:
    def __init__(self):
        self.rooms = {} 
    def create_room(self, room_name, max_num):
        if room_name in self.rooms: return False, "Bu isim dolu!"
        self.rooms[room_name] = GameRoom(room_name, max_num)
        return True, "Oluşturuldu."

if "manager" not in st.session_state:
    st.session_state.manager = RoomManager()
if "current_room_id" not in st.session_state:
    st.session_state.current_room_id = None

manager = st.session_state.manager
st_autorefresh(interval=2000, key="sync")

def play_sound():
    try:
        with open("patlama.wav", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""<audio autoplay="true"><source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>"""
            st.markdown(md, unsafe_allow_html=True)
    except: pass

# ==========================================
#          2. CSS (TASARIM - AYDINLIK)
# ==========================================
st.markdown("""
    <style>
    /* 1. ARKAPLAN (Aydınlık / WhatsApp Tonu) */
    .stApp {
        background-color: #ECE5DD;
        color: #121212;
    }
    
    /* 2. EKRAN GENİŞLİĞİNİ KISITLAMA (SENİN İSTEDİĞİN 1/3 OLAYI) */
    /* Bu kod, siteyi telefondaymış gibi daraltır ve ortalar */
    .block-container {
        max-width: 500px !important; /* Maksimum genişlik 500px */
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin: auto !important; /* Ortala */
        background-color: #ECE5DD; /* Konteyner içi de aynı renk */
    }

    /* 3. INPUT ALANLARI (Sade ve Temiz) */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        color: #121212 !important;
        border: 1px solid #ccc !important;
        border-radius: 8px !important;
        height: 45px !important;
    }

    /* 4. OYUN BUTONLARI (KARE VE DİP DİBE) */
    /* Sadece oyun içindeki sayı butonlarını hedefler */
    div.stButton > button {
        background-color: #FFFFFF;
        color: #121212;
        border-radius: 4px;
        border: 1px solid #ccc;
        border-bottom: 2px solid #aaa;
        font-weight: 800;
        font-size: 16px;
        width: 100%;
        aspect-ratio: 1 / 1; /* Kare */
        padding: 0 !important;
        margin: 0 !important;
        line-height: 1;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    div.stButton > button:active {
        border-bottom: 0px;
        transform: translateY(2px);
        background-color: #f0f0f0;
    }
    div.stButton > button:disabled {
        background-color: transparent;
        border: none;
        color: transparent;
        box-shadow: none;
    }

    /* 5. NORMAL BUTONLAR (BAŞLAT, KATIL VB.) */
    /* Bunların "dev gibi" olmasını engellemek için özel sınıf */
    .normal-btn button {
        height: auto !important;
        aspect-ratio: auto !important;
        width: auto !important;
        padding: 10px 20px !important;
        font-size: 14px !important;
    }

    /* 6. IZGARA (GRID) AYARLARI */
    [data-testid="stHorizontalBlock"] { gap: 2px !important; }
    [data-testid="column"] { padding: 0 !important; min-width: 0 !important; }

    /* 7. OYUNCU KARTLARI */
    .player-card {
        background: white; border: 1px solid #ddd; border-radius: 6px; 
        text-align: center; font-size: 12px; padding: 4px;
        white-space: nowrap; overflow: hidden; margin-bottom: 4px;
        color: #333;
    }
    .active-turn { background: #dcf8c6; border: 1px solid #25D366; font-weight:bold; }
    .eliminated { background: #ffebeb; border: 1px solid #ff3b30; text-decoration: line-through; opacity: 0.6; }

    /* GİZLEME */
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
#               UYGULAMA AKIŞI
# ==========================================

current_room = None
if st.session_state.current_room_id and st.session_state.current_room_id in manager.rooms:
    current_room = manager.rooms[st.session_state.current_room_id]
else:
    st.session_state.current_room_id = None

# --- 1. ANA MENÜ (LOBI) ---
if current_room is None:
    st.markdown("<h2 style='text-align:center; color:#075E54;'>💣 101 Lobi</h2>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["GİRİŞ", "YENİ MASA"])
    
    with tab1:
        if not manager.rooms:
            st.info("Henüz masa yok.")
        else:
            room_list = list(manager.rooms.keys())
            selected_room = st.selectbox("Masa Seç", room_list)
            # Butonu dev gibi yapmamak için st.columns hilesi kullanmıyoruz, direkt yazıyoruz
            if st.button("Masaya Otur", type="primary"):
                st.session_state.current_room_id = selected_room
                st.rerun()

    with tab2:
        new_room_name = st.text_input("Masa Adı", placeholder="Örn: Salon")
        new_room_limit = st.number_input("Bitiş Sayısı", 10, 200, 101)
        if st.button("Oluştur", type="secondary"):
            if new_room_name:
                success, msg = manager.create_room(new_room_name, new_room_limit)
                if success:
                    st.session_state.current_room_id = new_room_name
                    st.rerun()
                else: st.error(msg)

# --- 2. OYUN ODASI ---
else:
    # Üst Bar (Geri Butonu ve Başlık)
    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button("⬅️"):
            st.session_state.current_room_id = None
            st.rerun()
    with c2:
        st.markdown(f"<h3 style='margin:0; padding-top:5px; color:#075E54;'>{current_room.name}</h3>", unsafe_allow_html=True)
    
    st.markdown("---")

    # A. OYUN BAŞLAMADIYSA
    if not current_room.active:
        st.markdown("#### 👋 Katıl")
        
        # Giriş formu
        join_name = st.text_input("İsim", placeholder="Adın...")
        join_num = st.number_input("Gizli Sayı", 1, current_room.max_num)
        
        # Bu butonu da küçülttük (use_container_width=True silindi)
        if st.button("Hazırım", type="primary"):
            err = current_room.add_player(join_name, int(join_num))
            if err: st.error(err)
            else: st.rerun()

        st.caption(f"Bekleyenler: {len(current_room.players)}")
        
        if current_room.players:
            # 2 Sütun yapalım ki isimler rahat okunsun (Sıkışmasın)
            cols = st.columns(2)
            for i, p in enumerate(current_room.players):
                with cols[i % 2]:
                    st.markdown(f"<div class='player-card'>👤 {p['name']}</div>", unsafe_allow_html=True)
        
        if len(current_room.players) >= 2:
            st.write("")
            if st.button("🚀 BAŞLAT"):
                current_room.active = True
                current_room.logs.append("Oyun Başladı!")
                st.rerun()

    # B. OYUN BAŞLADIYSA
    else:
        if current_room.boom_trigger:
            play_sound()
            time.sleep(1)
            current_room.boom_trigger = False

        if current_room.game_over:
            st.balloons()
            st.markdown(f"""
            <div style="background: white; border: 2px solid red; border-radius: 10px; padding: 20px; text-align: center;">
                <h2 style="color: red; margin:0;">KAYBEDEN</h2>
                <h1 style="color: #333; margin:10px;">{current_room.loser}</h1>
                <p>Hesaplar Onda!</p>
            </div>
            """, unsafe_allow_html=True)
            st.write("")
            if st.button("YENİ TUR"):
                manager.rooms[current_room.name] = GameRoom(current_room.name, current_room.max_num)
                st.rerun()
        else:
            # Kimlik ve Sıra
            p_names = ["Kimsin?"] + [p['name'] for p in current_room.players]
            my_id = st.selectbox("", p_names, label_visibility="collapsed")
            curr_p = current_room.players[current_room.turn_index]['name']
            
            if my_id == curr_p:
                st.success("🟢 SIRA SENDE!")
            else:
                st.info(f"⏳ SIRA: {curr_p}")

            # Oyuncu Listesi (Sade)
            p_cols = st.columns(4)
            for i, p in enumerate(current_room.players):
                css = "player-card"
                if p['status'] == 'eliminated': css += " eliminated"
                elif i == current_room.turn_index: css += " active-turn"
                with p_cols[i % 4]:
                    st.markdown(f"<div class='{css}'>{p['name']}</div>", unsafe_allow_html=True)

            st.write("") # Biraz boşluk

            # OYUN GRİDİ (4 SÜTUN)
            # Burada use_container_width=True kullanıyoruz çünkü KARELERİN kutuyu doldurmasını istiyoruz.
            GRID_COLS = 4
            btn_cols = st.columns(GRID_COLS)
            
            for i in range(1, current_room.max_num + 1):
                idx = (i-1) % GRID_COLS
                col = btn_cols[idx]
                
                if i in current_room.clicked:
                    owner = next((p for p in current_room.players if p['number'] == i), None)
                    if owner:
                        col.error("💥")
                    else:
                        # Boş kutu (Görünmez)
                        col.markdown("<div style='height:100%; width:100%; min-height:40px;'></div>", unsafe_allow_html=True)
                else:
                    is_turn = (my_id == curr_p)
                    # Sadece sayı butonları container width kullanır
                    if col.button(str(i), key=f"btn_{i}", disabled=not is_turn, use_container_width=True):
                        current_room.make_move(i, my_id)
                        st.rerun()
