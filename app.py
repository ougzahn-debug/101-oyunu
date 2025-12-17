import streamlit as st
import base64
import time
from streamlit_autorefresh import st_autorefresh

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="101", 
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
        self.admin_name = admin_name
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
    def create_room(self, room_name, max_num, admin_name, admin_num):
        if room_name in self.rooms: return False, "Bu isim dolu!"
        new_room = GameRoom(room_name, max_num, admin_name)
        err = new_room.add_player(admin_name, admin_num)
        if err: return False, err
        self.rooms[room_name] = new_room
        return True, "Oluşturuldu."

if "manager" not in st.session_state:
    st.session_state.manager = RoomManager()
if "current_room_id" not in st.session_state:
    st.session_state.current_room_id = None
if "my_identity" not in st.session_state:
    st.session_state.my_identity = None

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
#          2. CSS (MİNİMALİST & KÜÇÜK)
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #ECE5DD; color: #121212; }
    
    /* EKRAN GENİŞLİĞİ VE KENAR BOŞLUKLARI */
    .block-container {
        max-width: 450px !important; /* Ekranı iyice daralttım */
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        margin: auto !important;
    }

    /* OYUN BUTONLARI (MİNİK) */
    div.stButton > button {
        background-color: #FFFFFF;
        color: #121212;
        border: 1px solid #ccc;
        border-radius: 4px;
        font-weight: 700;
        font-size: 12px !important; /* Yazı boyutu MİNİ */
        width: 100%;
        height: 35px !important;    /* Yükseklik SABİT ve KISA */
        min-height: 0px !important;
        padding: 0 !important;
        margin: 0 !important;
        line-height: 1;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }
    div.stButton > button:active {
        background-color: #ddd;
        border-color: #bbb;
    }
    div.stButton > button:disabled {
        background-color: transparent; border: none; color: transparent; box-shadow: none;
    }

    /* NORMAL BUTONLAR (BAŞLAT VB) - Bunlar biraz daha belirgin olsun */
    .normal-btn button {
        height: 40px !important;
        font-size: 14px !important;
    }

    /* IZGARA BOŞLUKLARI */
    [data-testid="stHorizontalBlock"] { gap: 2px !important; }
    [data-testid="column"] { padding: 0 !important; min-width: 0 !important; }

    /* OYUNCU KARTLARI */
    .player-card {
        background: white; border: 1px solid #ddd; border-radius: 4px; 
        text-align: center; font-size: 11px; padding: 2px;
        white-space: nowrap; overflow: hidden; margin-bottom: 2px;
    }
    .active-turn { background: #dcf8c6; border: 1px solid #25D366; }
    .eliminated { background: #ffebeb; border: 1px solid #ff3b30; text-decoration: line-through; opacity: 0.6; }
    
    header, footer {display: none !important;}
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

# --- LOBI ---
if current_room is None:
    st.markdown("<h4 style='text-align:center; color:#075E54; margin:0;'>💣 101</h4>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["GİRİŞ", "MASA KUR"])
    
    with tab1:
        if not manager.rooms: st.info("Masa yok.")
        else:
            room_list = list(manager.rooms.keys())
            selected_room = st.selectbox("Masa Seç", room_list)
            if st.button("Masaya Otur", type="primary"):
                st.session_state.current_room_id = selected_room
                st.rerun()
    with tab2:
        c1, c2 = st.columns(2)
        new_room_name = c1.text_input("Masa Adı", placeholder="Masa")
        new_room_limit = c2.number_input("Limit", 10, 200, 101)
        
        c3, c4 = st.columns(2)
        admin_name = c3.text_input("Adın", placeholder="Sen")
        admin_num = c4.number_input("Sayın", 1, new_room_limit)
        
        if st.button("OLUŞTUR", type="secondary"):
            if new_room_name and admin_name:
                success, msg = manager.create_room(new_room_name, new_room_limit, admin_name, int(admin_num))
                if success:
                    st.session_state.current_room_id = new_room_name
                    st.session_state.my_identity = admin_name
                    st.rerun()
                else: st.error(msg)

# --- OYUN ---
else:
    # Üst Bar
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("🔙"):
            st.session_state.current_room_id = None; st.session_state.my_identity = None; st.rerun()
    with c2:
        st.markdown(f"<h5 style='margin:0; padding-top:8px; color:#075E54;'>{current_room.name}</h5>", unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)

    # OYUN BAŞLAMADIYSA
    if not current_room.active:
        if st.session_state.my_identity not in [p['name'] for p in current_room.players]:
             join_name = st.text_input("İsim")
             join_num = st.number_input("Gizli Sayı", 1, current_room.max_num)
             if st.button("Hazırım", type="primary"):
                 err = current_room.add_player(join_name, int(join_num))
                 if err: st.error(err)
                 else: 
                     st.session_state.my_identity = join_name
                     st.rerun()
        else:
            st.success(f"Bekleniyor: {len(current_room.players)} Kişi")

        if current_room.players:
            cols = st.columns(3)
            for i, p in enumerate(current_room.players):
                with cols[i % 3]:
                    icon = "👑 " if p['name'] == current_room.admin_name else ""
                    st.markdown(f"<div class='player-card'>{icon}{p['name']}</div>", unsafe_allow_html=True)
        
        if st.session_state.my_identity == current_room.admin_name and len(current_room.players) >= 2:
            st.write("")
            if st.button("🚀 OYUNU BAŞLAT"):
                current_room.active = True
                current_room.logs.append("Başladı!")
                st.rerun()

    # OYUN BAŞLADIYSA
    else:
        if current_room.boom_trigger:
            play_sound()
            time.sleep(1)
            current_room.boom_trigger = False

        if current_room.game_over:
            st.error(f"KAYBEDEN: {current_room.loser}")
            if st.session_state.my_identity == current_room.admin_name:
                if st.button("YENİ TUR"):
                    manager.create_room(current_room.name, current_room.max_num, current_room.admin_name, 1)
                    st.rerun()
        else:
            my_id = st.session_state.my_identity
            if not my_id:
                p_names = ["Seç"] + [p['name'] for p in current_room.players]
                my_id = st.selectbox("", p_names)
                if my_id != "Seç": st.session_state.my_identity = my_id; st.rerun()
            
            curr_p = current_room.players[current_room.turn_index]['name']
            
            if my_id == curr_p: st.success("SIRA SENDE!")
            else: st.info(f"Sıra: {curr_p}")

            p_cols = st.columns(4)
            for i, p in enumerate(current_room.players):
                css = "player-card"
                if p['status'] == 'eliminated': css += " eliminated"
                elif i == current_room.turn_index: css += " active-turn"
                with p_cols[i % 4]: st.markdown(f"<div class='{css}'>{p['name']}</div>", unsafe_allow_html=True)

            st.write("") 

            # --- SIKIŞTIRILMIŞ IZGARA (6 SÜTUN) ---
            # 6 Sütun = Daha dar butonlar
            # Yükseklik = 35px sabitlendi (CSS'de)
            GRID_COLS = 6 
            btn_cols = st.columns(GRID_COLS)
            
            for i in range(1, current_room.max_num + 1):
                idx = (i-1) % GRID_COLS
                col = btn_cols[idx]
                
                if i in current_room.clicked:
                    owner = next((p for p in current_room.players if p['number'] == i), None)
                    if owner: col.error("💥")
                    else: col.markdown("<div style='height:35px;'></div>", unsafe_allow_html=True)
                else:
                    is_turn = (my_id == curr_p)
                    # use_container_width=True KULLANMIYORUZ. CSS ile genişletiyoruz.
                    if col.button(str(i), key=f"btn_{i}", disabled=not is_turn):
                        current_room.make_move(i, my_id)
                        st.rerun()
