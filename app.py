import streamlit as st
import base64
import time
from streamlit_autorefresh import st_autorefresh

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="101 - Online", page_icon="💣", layout="centered")

# --- GLOBAL HAFIZA (SUNUCU BELLEĞİ) ---
# Bu yapı sayesinde veriler herkes için ortaktır.
@st.cache_resource
class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.active = False
        self.players = []     # [{'name': 'Oğuz', 'number': 55, 'status': 'active'}, ...]
        self.clicked = set()  # Açılan kutular
        self.taken_numbers = set() # Çakışma kontrolü için
        self.max_num = 101
        self.turn_index = 0
        self.game_over = False
        self.loser = ""
        self.boom_trigger = False
        self.logs = []

    def add_player(self, name, number):
        # Kontroller
        name = name.strip()
        if not name: return "İsim boş olamaz."
        if any(p['name'].lower() == name.lower() for p in self.players): return "Bu isim zaten alınmış."
        if number in self.taken_numbers: return "Bu sayı başkası tarafından seçilmiş!"
        if not (1 <= number <= self.max_num): return f"Sayı 1-{self.max_num} arasında olmalı."
        
        # Oyuncuyu ekle
        self.players.append({'name': name, 'number': number, 'status': 'active'})
        self.taken_numbers.add(number)
        return None # Hata yoksa None döner

# Hafızayı başlat
if "store" not in st.session_state:
    st.session_state.store = GameState()

store = st.session_state.store

# --- OTOMATİK YENİLEME (CANLI LOBİ) ---
# 2 saniyede bir sayfayı yeniler ki yeni gelenleri görelim
st_autorefresh(interval=2000, key="lobby_sync")

# --- CSS TEMA (WHATSAPP) ---
st.markdown("""
    <style>
    .stApp { background-color: #ECE5DD; }
    h1, h2, h3 { color: #075E54; font-family: 'Helvetica', sans-serif; text-align: center; }
    
    /* Form Alanları */
    .stTextInput input, .stNumberInput input {
        border-radius: 10px;
        border: 1px solid #128C7E;
    }
    
    /* Butonlar */
    div.stButton > button {
        background-color: #FFFFFF; color: #4a4a4a; border-radius: 10px;
        border: none; border-bottom: 2px solid #d1d1d1; font-weight: bold;
        width: 100%; height: 50px;
    }
    div.stButton > button:hover { background-color: #f0f0f0; color: #075E54; }
    
    /* Lobi Kartları */
    .lobby-card {
        background-color: white; padding: 10px; border-radius: 10px;
        margin-bottom: 5px; color: #075E54; font-weight: bold;
        display: flex; justify-content: space-between; align-items: center;
    }
    
    /* Oyun Kartları */
    .player-card {
        background-color: white; padding: 10px; border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center;
        margin-bottom: 5px; font-weight: bold; color: #121212;
    }
    .active-turn { border: 3px solid #128C7E; background-color: #DCF8C6; transform: scale(1.05); }
    .eliminated { background-color: #ffcccc; border: 2px solid #FF3B30; text-decoration: line-through; opacity: 0.7; }
    </style>
""", unsafe_allow_html=True)

# --- SES ÇALMA ---
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
        store.logs.append(f"💣 {player_name}, {victim}'i patlattı!")
        
        active_p = [p for p in store.players if p['status'] == 'active']
        if len(active_p) == 1:
            store.game_over = True
            store.loser = active_p[0]['name']
            store.boom_trigger = True
            store.logs.append(f"🏁 OYUN BİTTİ! Kaybeden: {store.loser}")
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
    # --- 1. LOBİ EKRANI (HERKES BURADAN KATILIR) ---
    st.title("💣 101 Lobi")
    st.info("İsmini ve gizli sayını gir, 'KATIL'a bas ve bekle.")
    
    # Oyun Ayarı (Sadece ilk başta görünür, opsiyonel)
    if len(store.players) == 0:
        store.max_num = st.number_input("Oyun Kaçta Bitsin?", 10, 200, 101)
    
    st.divider()
    
    # Katılım Formu
    c1, c2 = st.columns([2, 1])
    join_name = c1.text_input("İsminiz")
    join_num = c2.number_input("Gizli Sayın", 1, store.max_num, step=1) # number_input mobilde klavye açtığı için daha iyi
    
    if st.button("👥 OYUNA KATIL"):
        err = store.add_player(join_name, int(join_num))
        if err:
            st.error(err)
        else:
            st.success("Katıldın! Diğerlerini bekle...")
            st.rerun()

    st.markdown("### 🟢 Bekleyen Oyuncular")
    
    # Bekleyenleri Listele
    if len(store.players) == 0:
        st.write("Henüz kimse yok...")
    else:
        for p in store.players:
            st.markdown(f"""
            <div class="lobby-card">
                <span>👤 {p['name']}</span>
                <span>🔒 Sayı Girildi</span>
            </div>
            """, unsafe_allow_html=True)
            
    st.divider()
    
    # Başlatma Butonu (En az 2 kişi varsa görünür)
    if len(store.players) >= 2:
        if st.button("🚀 HERKES HAZIRSA BAŞLAT", type="primary"):
            store.active = True
            store.logs.append("Oyun Başladı!")
            st.rerun()
    else:
        st.caption("Başlamak için en az 2 kişi bekleniyor...")

else:
    # --- 2. OYUN EKRANI (HERKES AYNI ANDA OYNAR) ---
    
    if store.boom_trigger:
        play_sound()
        time.sleep(1)
        store.boom_trigger = False

    if store.game_over:
        st.balloons()
        st.markdown(f"""
        <div style="background-color: #075E54; color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px;">
            <h1>OYUN BİTTİ!</h1>
            <h2 style="color:#FFD700">Kaybeden: {store.loser}</h2>
            <p>Hesaplar ona ait!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("♻️ YENİ OYUN KUR"):
            store.reset()
            st.rerun()
            
    else:
        # Kimlik Seçimi (Tarayıcı hafızasında tutulmaz, her girişte seçilir)
        # Bu basit yöntem, karmaşık kullanıcı giriş sistemlerinden kurtarır.
        st.title(f"💣 101 (Limit: {store.max_num})")
        
        player_names = [p['name'] for p in store.players]
        my_identity = st.selectbox("Ben Kimim?", ["Seçiniz..."] + player_names)
        
        if my_identity == "Seçiniz...":
            st.warning("Lütfen yukarıdan isminizi seçin!")
            st.stop() # İsim seçmeden aşağıyı gösterme
            
        current_player_name = store.players[store.turn_index]['name']
        
        # Sıra Bilgisi
        if my_identity == current_player_name:
            st.success(f"SIRA SENDE, {my_identity.upper()}! BİR KUTU SEÇ.")
        else:
            st.info(f"SIRA: {current_player_name}")

        # Oyuncu Kartları
        cols = st.columns(4)
        for i, p in enumerate(store.players):
            css = "player-card"
            stat = "Online"
            if p['status'] == 'eliminated':
                css += " eliminated"
                stat = "ELENDİ"
            elif i == store.turn_index:
                css += " active-turn"
                stat = "Yazıyor..."
                
            with cols[i % 4]:
                st.markdown(f"""<div class="{css}"><div>{p['name']}</div><small>{stat}</small></div>""", unsafe_allow_html=True)

        if store.logs:
            st.caption(f"Son Olay: {store.logs[-1]}")
        
        st.divider()

        # Sayı Tablosu
        grid_cols = 5
        btn_cols = st.columns(grid_cols)
        
        for i in range(1, store.max_num + 1):
            c_idx = (i-1) % grid_cols
            col = btn_cols[c_idx]
            
            if i in store.clicked:
                owner = None
                for p in store.players:
                    if p['number'] == i:
                        owner = p
                        break
                if owner: col.error("💥")
                else: col.empty()
            else:
                is_my_turn = (my_identity == current_player_name)
                # Buton ID'si unique olmalı
                if col.button(str(i), key=f"b{i}", disabled=not is_my_turn):
                    make_move(i, my_identity)
                    st.rerun()
