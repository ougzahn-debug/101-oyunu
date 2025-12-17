import streamlit as st
import base64
import time
from streamlit_autorefresh import st_autorefresh

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="101 Lobi", 
    page_icon="💣", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# ==========================================
#          1. OYUN ODASI SINIFI
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
        self.created_at = time.time()

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

# ==========================================
#          2. ODA YÖNETİCİSİ
# ==========================================
@st.cache_resource
class RoomManager:
    def __init__(self):
        self.rooms = {} 

    def create_room(self, room_name, max_num):
        if room_name in self.rooms:
            return False, "Bu isim dolu!"
        self.rooms[room_name] = GameRoom(room_name, max_num)
        return True, "Oluşturuldu."

if "manager" not in st.session_state:
    st.session_state.manager = RoomManager()
    
if "current_room_id" not in st.session_state:
    st.session_state.current_room_id = None

manager = st.session_state.manager

# --- SENKRONİZASYON ---
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

# --- CSS (MOBİL UYUMLU & SIKIŞIK) ---
st.markdown("""
    <style>
    .stApp { background-color: #ECE5DD; }
    
    /* Konteyner */
    .block-container {
        padding-top: 0.5rem !important; padding-bottom: 2rem !important;
        padding-left: 0.2rem !important; padding-right: 0.2rem !important;
    }
    
    /* Sütunlar (Dip Dibe) */
    [data-testid="stHorizontalBlock"] { gap: 0px !important; }
    [data-testid="column"] { 
        padding: 1px !important; 
        min-width: 0 !important; 
        width: 25% !important; 
        flex: 1 1 25% !important; 
    }

    /* Oyun Butonları */
    div.stButton > button {
        background-color: #FFFFFF; color: #121212; border-radius: 4px;
        border: 1px solid #ccc; border-bottom: 2px solid #999;
        font-weight: 800; font-size: 14px; width: 100%; padding: 0;
        aspect-ratio: 1 / 1; margin: 0px; line-height: 1;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }
    div.stButton > button:active { border-bottom: 0px; transform: translateY(2px); }

    /* Inputlar (Lobi) */
    .stTextInput input, .stNumberInput input, .stSelectbox div { min-height: 40px !important; font-size: 14px !important; }
    
    /* Kartlar */
    .player-card { background: white; border: 1px solid #ddd; border-radius: 4px; text-align: center; font-size: 11px; padding: 2px; white-space: nowrap; overflow: hidden; }
    .active-turn { background: #dcf8c6; border-left: 3px solid #25D366; font-weight:bold; }
    .eliminated { background: #ffebeb; border-left: 3px solid #ff3b30; text-decoration: line-through; opacity: 0.6; }
    
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

# --- 1. ANA MENÜ (ODADA DEĞİLSEK) ---
if current_room is None:
    st.markdown("<h3 style='text-align:center; color:#075E54; margin:0;'>💣 101 Lobi</h3>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🚪 GİR", "➕ KUR"])
    
    with tab1:
        if not manager.rooms:
            st.info("Masa yok. Yan sekmeden kur.")
        else:
            room_list = list(manager.rooms.keys())
            selected_room = st.selectbox("Masa Seç", room_list, label_visibility="collapsed")
            if st.button("MASAYA OTUR", type="primary", use_container_width=True):
                st.session_state.current_room_id = selected_room
                st.rerun()

    with tab2:
        new_room_name = st.text_input("Masa Adı", placeholder="Örn: Oğuz")
        new_room_limit = st.number_input("Limit", 10, 200, 101)
        if st.button("OLUŞTUR", type="secondary", use_container_width=True):
            if new_room_name:
                success, msg = manager.create_room(new_room_name, new_room_limit)
                if success:
                    st.session_state.current_room_id = new_room_name
                    st.rerun()
                else: st.error(msg)

# --- 2. OYUN ODASI ---
else:
    # Üst Bar
    c_back, c_title = st.columns([1, 4])
    with c_back:
        if st.button("⬅️"):
            st.session_state.current_room_id = None
            st.rerun()
    with c_title:
        st.markdown(f"<h4 style='margin:0; padding-top:5px; color:#075E54;'>{current_room.name}</h4>", unsafe_allow_html=True)
    
    st.write("---")

    # A. OYUN BAŞLAMADIYSA (LOBİ)
    if not current_room.active:
        c1, c2, c3 = st.columns([3, 2, 2])
        with c1: join_name = st.text_input("", placeholder="İsim", label_visibility="collapsed")
        with c2: join_num = st.number_input("", 1, current_room.max_num, label_visibility="collapsed")
        with c3: 
            if st.button("KATIL", type="primary", use_container_width=True):
                err = current_room.add_player(join_name, int(join_num))
                if err: st.toast(err)
                else: st.rerun()

        st.caption(f"Bekleyen: {len(current_room.players)}")
        if current_room.players:
            cols = st.columns(4)
            for i, p in enumerate(current_room.players):
                with cols[i % 4]:
                    st.markdown(f"<div class='player-card'>👤 {p['name']}</div>", unsafe_allow_html=True)
        
        st.write("---")
        if len(current_room.players) >= 2:
            if st.button("BAŞLAT 🚀", type="secondary", use_container_width=True):
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
            st.error(f"KAYBEDEN: {current_room.loser}")
            if st.button("YENİ OYUN", use_container_width=True):
                manager.rooms[current_room.name] = GameRoom(current_room.name, current_room.max_num)
                st.rerun()
        else:
            # Kimlik
            p_names = ["Kimsin?"] + [p['name'] for p in current_room.players]
            my_id = st.selectbox("", p_names, label_visibility="collapsed")
            curr_p = current_room.players[current_room.turn_index]['name']
            
            if my_id == curr_p:
                st.markdown(f"<div style='background:#dcf8c6; padding:5px; text-align:center; border-radius:5px; margin-bottom:5px; font-weight:bold; color:#075E54;'>🟢 SIRA SENDE!</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='background:#fff; border:1px solid #ccc; padding:5px; text-align:center; border-radius:5px; margin-bottom:5px; font-size:12px;'>⏳ Sıra: {curr_p}</div>", unsafe_allow_html=True)

            # Kartlar
            p_cols = st.columns(4)
            for i, p in enumerate(current_room.players):
                css = "player-card"
                if p['status'] == 'eliminated': css += " eliminated"
                elif i == current_room.turn_index: css += " active-turn"
                with p_cols[i % 4]:
                    st.markdown(f"<div class='{css}'>{p['name']}</div>", unsafe_allow_html=True)

            # Grid
            GRID_COLS = 4
            btn_cols = st.columns(GRID_COLS)
            for i in range(1, current_room.max_num + 1):
                idx = (i-1) % GRID_COLS
                col = btn_cols[idx]
                
                if i in current_room.clicked:
                    owner = next((p for p in current_room.players if p['number'] == i), None)
                    if owner: col.error("💥")
                    else: col.markdown("<div style='height:100%; width:100%;'></div>", unsafe_allow_html=True)
                else:
                    is_turn = (my_id == curr_p)
                    if col.button(str(i), key=f"b{i}", disabled=not is_turn):
                        current_room.make_move(i, my_id)
                        st.rerun()
