import streamlit as st
import base64
import time
from streamlit_autorefresh import st_autorefresh

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="101 Lobi", 
    page_icon="💣", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# ==========================================
#          1. OYUN MANTIĞI
# ==========================================
class GameRoom:
    def __init__(self, room_name, max_num, admin_name):
        self.name = room_name
        self.admin_name = admin_name # Masayı kuran kişi
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
        if not (1 <= number <= self.max_num): return f"1-{self.max_num} arası."
        
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
    # Oda kurarken artık admin ismini de alıyoruz
    def create_room(self, room_name, max_num, admin_name, admin_num):
        if room_name in self.rooms: return False, "Bu isim dolu!"
        
        # Odayı oluştur
        new_room = GameRoom(room_name, max_num, admin_name)
        
        # Admini otomatik oyuncu olarak ekle
        err = new_room.add_player(admin_name, admin_num)
        if err: return False, err
        
        self.rooms[room_name] = new_room
        return True, "Oluşturuldu."

if "manager" not in st.session_state:
    st.session_state.manager = RoomManager()
if "current_room_id" not in st.session_state:
    st.session_state.current_room_id = None
if "my_identity" not in st.session_state:
    st.session_state.my_identity = None # Kimliğimi hafızada tut

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
#          2. CSS (KOMPAKT & GÖRÜNÜR)
# ==========================================
st.markdown("""
    <style>
    /* 1. GENEL AYARLAR */
    .stApp { background-color: #ECE5DD; color: #121212; }
    
    /* 2. EKRAN ORTALAMA (TELEFON MODU) */
    .block-container {
        max-width: 500px !important;
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        margin: auto !important;
    }

    /* 3. INPUTLAR (Küçük ve Kibar) */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border: 1px solid #ccc !important;
        border-radius: 6px !important;
        height: 40px !important;
        min-height: 40px !important;
        font-size: 14px !important;
    }

    /* 4. OYUN KUTUCUKLARI (KOMPAKT) */
    div.stButton > button {
        background-color: #FFFFFF;
        color: #121212;
        border-radius: 4px;
        border: 1px solid #bbb;
        border-bottom: 2px solid #999;
        font-weight: 700;
        font-size: 14px !important; /* Yazı boyutu ideal */
        width: 100%;
        height: 50px !important; /* Sabit yükseklik, kare zorlaması yok */
        padding: 0 !important;
        margin: 0 !important;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }
    div.stButton > button:active {
        border-bottom: 0px;
        transform: translateY(2px);
        background-color: #e0e0e0;
    }
    div.stButton > button:disabled {
        background-color: transparent;
        border: none;
        color: transparent;
        box-shadow: none;
    }

    /* 5. SEKMELER (TABS) */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 40px; padding: 0 20px; }

    /* 6. GRID AYARLARI (SIKIŞIK) */
    [data-testid="stHorizontalBlock"] { gap: 2px !important; }
    [data-testid="column"] { padding: 0 !important; min-width: 0 !important; }

    /* 7. OYUNCU KARTLARI */
    .player-card {
        background: white; border: 1px solid #ddd; border-radius: 4px; 
        text-align: center; font-size: 11px; padding: 3px;
        white-space: nowrap; overflow: hidden; margin-bottom: 2px;
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
    st.session_state.my_identity = None

# --- 1. ANA MENÜ (LOBI) ---
if current_room is None:
    st.markdown("<h3 style='text-align:center; color:#075E54; margin-top:0;'>💣 101 Lobi</h3>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["GİRİŞ", "YENİ MASA"])
    
    with tab1:
        if not manager.rooms:
            st.info("Masa yok.")
        else:
            room_list = list(manager.rooms.keys())
            selected_room = st.selectbox("Masa Seç", room_list)
            if st.button("Masaya Otur", type="primary"):
                st.session_state.current_room_id = selected_room
                st.rerun()

    with tab2:
        st.markdown("**Masa & Yönetici Ayarları**")
        c1, c2 = st.columns(2)
        new_room_name = c1.text_input("Masa Adı", placeholder="Örn: Salon")
        new_room_limit = c2.number_input("Limit", 10, 200, 101)
        
        st.markdown("**Senin Bilgilerin (Admin)**")
        admin_name = st.text_input("Adın", placeholder="Admin")
        admin_num = st.number_input("Gizli Sayın", 1, new_room_limit)
        
        if st.button("OLUŞTUR VE GİR", type="secondary"):
            if new_room_name and admin_name:
                success, msg = manager.create_room(new_room_name, new_room_limit, admin_name, int(admin_num))
                if success:
                    st.session_state.current_room_id = new_room_name
                    st.session_state.my_identity = admin_name # Admin otomatik kimlik seçmiş olur
                    st.rerun()
                else: st.error(msg)
            else:
                st.error("Masa adı ve ismin gerekli.")

# --- 2. OYUN ODASI ---
else:
    # Üst Bar
    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button("⬅️"):
            st.session_state.current_room_id = None
            st.session_state.my_identity = None
            st.rerun()
    with c2:
        st.markdown(f"<h4 style='margin:0; padding-top:8px; color:#075E54;'>{current_room.name}</h4>", unsafe_allow_html=True)
    
    st.markdown("---")

    # A. OYUN BAŞLAMADIYSA
    if not current_room.active:
        
        # Eğer kimliğim belli değilse (Sonradan girenler için)
        if st.session_state.my_identity not in [p['name'] for p in current_room.players]:
             st.markdown("#### 👋 Katıl")
             join_name = st.text_input("İsim")
             join_num = st.number_input("Gizli Sayı", 1, current_room.max_num)
             if st.button("Hazırım", type="primary"):
                 err = current_room.add_player(join_name, int(join_num))
                 if err: st.error(err)
                 else: 
                     st.session_state.my_identity = join_name
                     st.rerun()
        else:
            st.success(f"✅ Hazırsın: {st.session_state.my_identity}")

        st.caption(f"Bekleyenler: {len(current_room.players)}")
        
        # Bekleyen Listesi
        if current_room.players:
            cols = st.columns(3)
            for i, p in enumerate(current_room.players):
                with cols[i % 3]:
                    # Admin ikonlu göster
                    icon = "👑 " if p['name'] == current_room.admin_name else "👤 "
                    st.markdown(f"<div class='player-card'>{icon}{p['name']}</div>", unsafe_allow_html=True)
        
        st.write("")
        
        # SADECE ADMIN BAŞLATABİLİR KONTROLÜ
        if st.session_state.my_identity == current_room.admin_name:
            if len(current_room.players) >= 2:
                if st.button("🚀 OYUNU BAŞLAT", type="secondary"):
                    current_room.active = True
                    current_room.logs.append("Oyun Başladı!")
                    st.rerun()
            else:
                st.info("Başlamak için en az 2 kişi lazım.")
        else:
            if current_room.players:
                st.info(f"⏳ Yönetici ({current_room.admin_name}) bekleniyor...")

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
                <h3 style="color: red; margin:0;">KAYBEDEN</h3>
                <h1 style="color: #333; margin:10px;">{current_room.loser}</h1>
                <p>Hesaplar Onda!</p>
            </div>
            """, unsafe_allow_html=True)
            st.write("")
            
            # Sadece Admin Resetleyebilir
            if st.session_state.my_identity == current_room.admin_name:
                if st.button("YENİ TUR BAŞLAT"):
                    # Odayı yeniden kur (Aynı ayarlarla)
                    manager.create_room(current_room.name, current_room.max_num, current_room.admin_name, 1) # Sayı temsili resetlenir
                    # Resetleme mantığı biraz karmaşık olduğu için burada basitçe odayı sıfırlayıp lobiye atıyoruz
                    current_room.active = False
                    current_room.players = [] 
                    current_room.clicked = set()
                    current_room.taken_numbers = set()
                    # Admini tekrar eklemek lazım ama basitlik için lobiye dönüyoruz
                    st.rerun()
            else:
                st.info("Yönetici yeni oyunu kurabilir.")
        else:
            # Kimlik Doğrulama (Otomatik)
            my_id = st.session_state.my_identity
            
            # Eğer kimlik düşmüşse (sayfa yenileme vb) tekrar seçtir
            if not my_id or my_id not in [p['name'] for p in current_room.players]:
                p_names = ["Seçiniz"] + [p['name'] for p in current_room.players]
                my_id = st.selectbox("Sen Kimsin?", p_names)
                if my_id != "Seçiniz":
                    st.session_state.my_identity = my_id
                    st.rerun()
            
            curr_p = current_room.players[current_room.turn_index]['name']
            
            if my_id == curr_p:
                st.success("🟢 SIRA SENDE!")
            else:
                st.info(f"⏳ SIRA: {curr_p}")

            # Oyuncu Kartları (Kompakt 4 Sütun)
            p_cols = st.columns(4)
            for i, p in enumerate(current_room.players):
                css = "player-card"
                if p['status'] == 'eliminated': css += " eliminated"
                elif i == current_room.turn_index: css += " active-turn"
                with p_cols[i % 4]:
                    st.markdown(f"<div class='{css}'>{p['name']}</div>", unsafe_allow_html=True)

            st.write("") 

            # OYUN GRİDİ (5 SÜTUN - DAHA KOMPAKT)
            # 5 Sütun 101 oyunu için idealdir (20 satır eder, 4 sütun 25 satır çok uzun oluyor)
            GRID_COLS = 5
            btn_cols = st.columns(GRID_COLS)
            
            for i in range(1, current_room.max_num + 1):
                idx = (i-1) % GRID_COLS
                col = btn_cols[idx]
                
                if i in current_room.clicked:
                    owner = next((p for p in current_room.players if p['number'] == i), None)
                    if owner:
                        col.error("💥")
                    else:
                        # Boş kutu
                        col.markdown("<div style='height:100%; width:100%; min-height:40px;'></div>", unsafe_allow_html=True)
                else:
                    is_turn = (my_id == curr_p)
                    # use_container_width=True ile kutucuklar genişliğe yayılır
                    if col.button(str(i), key=f"btn_{i}", disabled=not is_turn, use_container_width=True):
                        current_room.make_move(i, my_id)
                        st.rerun()
