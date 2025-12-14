import streamlit as st
import google.generativeai as genai
import os
import json
import uuid
from datetime import datetime
from streamlit_mermaid import st_mermaid

# ==========================================
# 0. CẤU HÌNH TRANG & CSS (THEME GEN Z DARK MODE)
# ==========================================
st.set_page_config(
    page_title="WeAreOne AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tạo thư mục lưu lịch sử
HISTORY_DIR = "history_data"
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

st.markdown("""
<style>
    @import url('https://f...content-available-to-author-only...s.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

    /* 1. NỀN CHÍNH & FONT */
    .stApp {
        background-color: #0E1117; 
        font-family: 'Outfit', sans-serif;
    }
    h1, h2, h3, h4, p, span, div {
        color: #FAFAFA !important; 
    }

    /* 2. HEADER ẨN MẶC ĐỊNH */
    [data-testid="stHeader"] {
        background-color: transparent;
    }

    /* 3. TIÊU ĐỀ NEON */
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 10px;
        background: linear-gradient(90deg, #A855F7, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(168, 85, 247, 0.3);
    }
    
    .sub-title {
        text-align: center;
        color: #8B949E !important;
        font-size: 1.1rem;
        margin-bottom: 30px;
    }

    /* 4. BUTTON CHÍNH (GRADIENT) */
    .stButton > button {
        background: linear-gradient(90deg, #7C3AED 0%, #2563EB 100%);
        color: white !important;
        border: none;
        border-radius: 12px;
        height: 50px;
        font-weight: 700;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.5);
    }

    /* 5. BUTTON SIDEBAR (LỊCH SỬ - STYLE KHÁC) */
    div[data-testid="stSidebar"] .stButton > button {
        background: #161B22;
        border: 1px solid #30363D;
        color: #C9D1D9 !important;
        height: auto;
        padding: 10px;
        text-align: left;
        justify-content: flex-start;
        box-shadow: none;
    }
    div[data-testid="stSidebar"] .stButton > button:hover {
        border-color: #A855F7;
        color: #A855F7 !important;
        background: #0D1117;
    }

    /* 6. INPUT & CARD STYLE */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #0D1117 !important;
        color: #E6EDF3 !important;
        border: 1px solid #30363D;
        border-radius: 10px;
    }
    
    .custom-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }

    /* 7. TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #161B22;
        border-radius: 8px;
        border: 1px solid #30363D;
        color: #8B949E !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #1F2937;
        border-color: #A855F7;
        color: #A855F7 !important;
    }

    /* SCROLLBAR */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #0E1117; }
    ::-webkit-scrollbar-thumb { background: #30363D; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. CẤU HÌNH API & HÀM HỖ TRỢ
# ==========================================
GOOGLE_API_KEY = "AIzaSyAQM9RNew9K0PHHoF7-siIhIzhOrKDBLhM"

try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    st.error(f"⚠️ Lỗi Key API: {e}")

# ==========================================
# 2. QUẢN LÝ DATA & LỊCH SỬ (JSON)
# ==========================================
def save_current_session():
    if not st.session_state.get('session_id'): return
    data = {
        "id": st.session_state['session_id'],
        "timestamp": st.session_state['timestamp'],
        "title": st.session_state.get('title', 'Cuộc họp không tên'),
        "transcript": st.session_state.get('transcript_part', ''),
        "summary": st.session_state.get('summary_part', ''),
        "sentiment": st.session_state.get('sentiment_part', ''),
        "mermaid_code": st.session_state.get('mermaid_code', ''),
        "chat_history": st.session_state.get('chat_history', []),
        "context_prompt": st.session_state.get('context_prompt', '')
    }
    with open(os.path.join(HISTORY_DIR, f"{st.session_state['session_id']}.json"), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_session_from_file(session_id):
    path = os.path.join(HISTORY_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        st.session_state.update({
            'session_id': data['id'], 'timestamp': data['timestamp'],
            'transcript_part': data['transcript'], 'summary_part': data['summary'],
            'sentiment_part': data['sentiment'], 'mermaid_code': data['mermaid_code'],
            'chat_history': data['chat_history'], 'context_prompt': data['context_prompt'],
            'title': data.get('title', 'Cuộc họp cũ'), 'analysis_done': True
        })

        try:
            model = genai.GenerativeModel(selected_model) 
            st.session_state['chat_session'] = model.start_chat(history=[])
        except: pass
        return True
    return False

def get_all_histories():
    histories = []
    files = [f for f in os.listdir(HISTORY_DIR) if f.endswith('.json')]
    for f in files:
        try:
            with open(os.path.join(HISTORY_DIR, f), 'r', encoding='utf-8') as file:
                d = json.load(file)
                histories.append({"id": d['id'], "title": d.get('title','No Title'), "timestamp": d.get('timestamp','')})
        except: pass
    return sorted(histories, key=lambda x: x['timestamp'], reverse=True)

def create_new_session():
    st.session_state.update({
        'session_id': str(uuid.uuid4()),
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'chat_history': [], 'chat_session': None, 'analysis_done': False,
        'transcript_part': "", 'summary_part': "", 'sentiment_part': "",
        'mermaid_code': None, 'context_prompt': "", 'title': ""
    })
    st.rerun()

def delete_session(session_id):
    """Xóa một file lịch sử cụ thể."""
    path = os.path.join(HISTORY_DIR, f"{session_id}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

def delete_all_histories():
    """Xóa tất cả các file lịch sử."""
    files_deleted = 0
    for f in os.listdir(HISTORY_DIR):
        if f.endswith('.json'):
            os.remove(os.path.join(HISTORY_DIR, f))
            files_deleted += 1
    return files_deleted

if 'session_id' not in st.session_state: create_new_session()

# ==========================================
# 3. SIDEBAR GIAO DIỆN
# ==========================================

with st.sidebar:
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="font-size: 50px;">🌌</div>
            <h2 style="color: #A855F7 !important; margin: 0;">WeAreOne</h2>
            <p style="color: #8B949E !important; font-size: 0.8rem;">Future of Meetings</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("➕ Cuộc họp mới", key="new_meeting_btn", use_container_width=True): # Key cho nút chính
            save_current_session()
            create_new_session()
            
            st.markdown("---")
            st.markdown("<div style='color:#8B949E; margin-bottom:10px; font-size:0.9rem;'>LỊCH SỬ GẦN ĐÂY</div>", unsafe_allow_html=True)
        
    histories = get_all_histories()

    # Thêm nút xóa toàn bộ
    if histories:
        clear_col, _ = st.columns([1, 1])
        with clear_col:
            # Key cho nút xóa toàn bộ
            if st.button("🗑️", help="Xóa TOÀN BỘ lịch sử", key="delete_all_btn_unique"): 
                if delete_all_histories():
                    create_new_session()
                    st.toast("Đã xóa toàn bộ lịch sử!", icon="🗑️")
                else:
                    st.toast("Không có lịch sử để xóa.", icon="❌")

    # Hiển thị danh sách lịch sử
    for idx, h in enumerate(histories):
        col_btn, col_del = st.columns([2, 1])
        is_active = h['id'] == st.session_state.get('session_id')
        label = f"{'⚡' if is_active else '📄'} {h['title'][:22]}..."
        
        # **SỬA LỖI Ở ĐÂY: DÙNG KEY CÓ TIỀN TỐ**
        button_key = f"load_{h['id']}" 
        
        with col_btn:
            # Nút Tải Lịch sử
            if st.button(label, key=button_key, use_container_width=True):
                save_current_session() 
                if load_session_from_file(h['id']): st.rerun()
        
        with col_del:
            # Nút Xóa Từng Mục
            delete_key = f"del_{h['id']}_item" # Key rõ ràng khác
            if st.button("❌", key=delete_key, help=f"Xóa: {h['title']}", use_container_width=True):
                if delete_session(h['id']):
                    if is_active:
                        create_new_session() 
                    else:
                        st.rerun()
                else:
                    st.toast(f"Không thể xóa file {h['id']}", icon="❌")

# ==========================================
# 4. MAIN AREA (LOGIC CHÍNH)
# ==========================================

# --- TRƯỜNG HỢP 1: CHƯA PHÂN TÍCH (MÀN HÌNH CHỜ) ---
if not st.session_state['analysis_done']:
    st.markdown('<div class="main-title">WE ARE ONE ASSISTANT</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Biến giọng nói thành hành động • Tóm tắt • Mindmap</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        # Card upload đẹp
        with st.container():
            st.markdown("""
            <div style="text-align: center; padding: 30px; background: #161B22; border-radius: 20px; border: 1px dashed #30363D; margin-bottom: 20px;">
                <h3 style="color: #A855F7 !important;">👋 Tải lên file ghi âm</h3>
                <p style="color: #8B949E !important;">Hỗ trợ .mp3, .wav, .m4a</p>
            </div>
            """, unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader("", type=["mp3", "wav", "m4a"], label_visibility="collapsed")
            
            if uploaded_file:
                st.audio(uploaded_file)
                
                selected_model = st.selectbox("Chọn mô hình AI:",options = ['gemini-2.5-flash', 'gemini-2.5-pro'], key = "selected_model_option")
                
                if st.button("🚀 KÍCH HOẠT PHÂN TÍCH", type="primary", use_container_width=True):
                    with st.status("🔄 Đang xử lý dữ liệu...", expanded=True):
                        temp_filename = f"temp_{uuid.uuid4()}.mp3"
                        try:
                            with open(temp_filename, "wb") as f: f.write(uploaded_file.getbuffer())
                            myfile = genai.upload_file(temp_filename)
                            
                            model = genai.GenerativeModel(selected_model)
                            prompt = """
                                    Bạn là một thư ký chuyên nghiệp. Hãy xử lý file âm thanh này:
                                    1. Tạo một **Tiêu đề (Title)** ngắn gọn, súc tích (dưới 7 từ) cho cuộc họp này.
                                    2. Tóm tắt các ý chính quan trọng nhất.
                                    3. Gỡ băng với các nội dung được gỡ được trình bày rõ ràng, xuống dòng đúng nơi đúng lúc.
                                    4. Với những dữ liệu không nghe rõ, không tự sinh ra dữ liệu ảo, phải tự kiểm tra dữ liệu đã nghe được xem có hợp lý với ngữ cảnh không.
                                    5. Đánh giá cảm xúc đoạn ghi âm (Vui vẻ/Căng thẳng/Bình thường).
                                    6. Bên cạnh đó, với mỗi nội dung, xuống hàng để nội dung rõ ràng hơn và sử dụng các dấu chú thích nếu cần thiết

                                    Yêu cầu trả về kết quả **ĐÚNG THỨ TỰ** và **ĐÚNG ĐỊNH DẠNG** sau để tôi tách nội dung (không thêm lời dẫn):
                                    ---TITLE---
                                    (Tiêu đề ở đây)
                                    ---TRANSCRIPT---
                                    (Nội dung gỡ băng ở đây)
                                    ---SUMMARY---
                                    (Nội dung tóm tắt ở đây)
                                    ---SENTIMENT---
                                    (Đánh giá cảm xúc ở đây)
                                    """
                            result = model.generate_content([myfile, prompt])
                            text = result.text
                            
                            # 3. Parse Result (Cập nhật để xử lý ---TITLE---)
                            transcript = "Không có nội dung"
                            summary = "Không có tóm tắt"
                            sentiment = "Bình thường"
                            title = "Cuộc họp mới"

                            # Kiểm tra xem TITLE có tồn tại không (vì nó là tag bắt đầu)
                            if "---TITLE---" in text: 
                                try:
                                    # 1. Tách TITLE
                                    parts_title = text.split("---TITLE---")
                                    rest = parts_title[-1]
                                    
                                    # 2. Tách TRANSCRIPT
                                    parts_trans = rest.split("---TRANSCRIPT---")
                                    title = parts_trans[0].strip()
                                    rest = parts_trans[-1]

                                    # 3. Tách SUMMARY
                                    parts_sum = rest.split("---SUMMARY---")
                                    transcript = parts_sum[0].strip()
                                    rest = parts_sum[-1]

                                    # 4. Tách SENTIMENT
                                    parts_sent = rest.split("---SENTIMENT---")
                                    summary = parts_sent[0].strip()
                                    sentiment = parts_sent[-1].strip()
                                        
                                except IndexError:
                                    st.error("Lỗi phân tích cú pháp kết quả từ AI. Định dạng trả về không khớp.")
                                    # Dừng và không cập nhật trạng thái nếu lỗi phân tích
                                    if os.path.exists(temp_filename): os.remove(temp_filename) 
                                    
                                # Cập nhật Session State và Rerun
                                st.session_state.update({
                                    'title': title, 'transcript_part': transcript,
                                    'summary_part': summary, 'sentiment_part': sentiment,
                                    'context_prompt': f"""
                                    Bạn là một trợ lý thông minh có nhiệm vụ trả lời các câu hỏi về nội dung cuộc họp sau.
                                    Tuyệt đối chỉ sử dụng thông tin từ 'Biên bản chi tiết' và 'Tóm tắt ý chính' được cung cấp bên dưới để trả lời.
                                    
                                    Biên bản chi tiết:
                                    {transcript}

                                    Tóm tắt ý chính:
                                    {summary}

                                    Hãy trả lời ngắn gọn, súc tích bằng tiếng Việt và duy trì vai trò trợ lý cuộc họp. 
                                    Bên cạnh đó, với mỗi nội dung, xuống hàng để nội dung rõ ràng hơn và sử dụng các dấu chú thích nếu cần thiết
                                    """,
                                    'analysis_done': True,
                                    'chat_session': model.start_chat(history=[]),
                                })
                                save_current_session()
                                st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}")
                        finally:
                            if os.path.exists(temp_filename): os.remove(temp_filename)
 
        # Feature Icons
        if not uploaded_file:
            st.markdown("""
            <div style="display: flex; justify-content: center; gap: 20px; margin-top: 30px;">
                <div style="text-align: center; color: #8B949E;">
                    <div style="font-size: 2rem;">📝</div><div>Transcript</div>
                </div>
                <div style="text-align: center; color: #8B949E;">
                    <div style="font-size: 2rem;">🧠</div><div>Mindmap</div>
                </div>
                <div style="text-align: center; color: #8B949E;">
                    <div style="font-size: 2rem;">💬</div><div>Q&A AI</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- TRƯỜNG HỢP 2: ĐÃ CÓ KẾT QUẢ (DASHBOARD) ---
else:
    # Header Kết quả
    st.markdown(f'<div class="main-title">{st.session_state.get("title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">📅 {st.session_state.get("timestamp")}</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Tóm tắt", "📝 Gỡ băng", "🗺️ Mindmap"])
    
    with tab1:
        # Badge cảm xúc
        s_text = st.session_state['sentiment_part']
        s_color = "#22c55e" if "Vui" in s_text else "#ef4444" if "Căng" in s_text else "#eab308"
        
        st.markdown(f"""
        <div class="custom-card">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <span style="font-size: 1.2rem; margin-right: 10px;">🎭</span>
                <span style="color: #A855F7; font-weight: bold;">Trạng thái cuộc họp:</span>
                <span style="margin-left: 10px; background: {s_color}20; padding: 5px 15px; border-radius: 20px; color: {s_color}; font-weight: bold; border: 1px solid {s_color};">
                    {s_text}
                </span>
            </div>
            <hr style="border-color: #30363D;">
            <div style="line-height: 1.6; color: #D1D5DB;">
                {st.session_state['summary_part']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        st.text_area("Chi tiết nội dung", st.session_state['transcript_part'], height=500)

    with tab3:
        col_m1, col_m2 = st.columns([1, 3])
        selected_model = st.selectbox("Chọn mô hình AI:",options = ['gemini-2.5-flash', 'gemini-2.5-pro'], key = "selected_model_option")
        with col_m1:
            st.info("AI sẽ vẽ sơ đồ tư duy từ nội dung tóm tắt.")
            if st.button("✨ Vẽ Mindmap"):
                try:
                    model = genai.GenerativeModel(selected_model)
                    mindmap_prompt = f"""
                    Dựa trên Biên bản chi tiết và Tóm tắt ý chính của cuộc họp:

                    Biên bản chi tiết:
                    {st.session_state['transcript_part']}

                    Tóm tắt ý chính:
                    {st.session_state['summary_part']}

                    Hãy tạo mã Sơ đồ Tư duy (Mind Map) bằng ngôn ngữ Mermaid.

                    Yêu cầu BẮT BUỘC:
                    1. Chỉ trả về MÃ NGUỒN MERMAID, không thêm bất kỳ lời giải thích, tiêu đề, hoặc ký tự nào khác ngoài mã nguồn.
                    2. Sử dụng **CHÍNH XÁC 4 khoảng trắng** để thụt lề cho mỗi cấp độ.
                    3. TUYỆT ĐỐI KHÔNG được sử dụng các ký tự như dấu **dấu hai chấm (:), dấu ngoặc đơn/kép ((), []), hoặc ký hiệu đánh số (A), B), 1., 2.)** trong tên của các nút (node), trừ nút gốc (root).
                    4. Sử dụng từ ngữ ngắn gọn, chỉ bao gồm từ khóa cho mỗi nút.

                    Định dạng phải theo ví dụ sau và TUÂN THỦ CÚ PHÁP MERMAID, ĐẢM BẢO CÓ THỂ CHẠY ĐƯỢC MÃ NGUỒN:
                    mindmap
                        root(Ôn Tập Cấu Trúc Đề Thi)
                            Mệnh đề
                                Lập mệnh đề phủ định
                                Mệnh đề Tài liệu 1.1
                                Xét tính đúng sai của suy luận
                            Tập hợp Ánh xạ mờ
                                Chứng minh đẳng thức tập con
                                Tìm Ảnh Ngược của ánh xạ mờ
                            Hướng dẫn Chung
                                Tham khảo bài tập 2.13-2.15
                                Không làm tắt
                    TRẢ VỀ ĐÚNG THEO CHỈ CÓ MÃ NGUỒN MERMAID, KHÔNG BAO GỒM  ```mermaid ``` HAY GÌ KHÁC
                    """
                    response = model.generate_content(mindmap_prompt)
                    mermaid_code = response.text.strip()
        
                    st.session_state['mermaid_code'] = mermaid_code
                    st.success("Tạo Mind Map thành công!")
                    st.toast("Sơ đồ tư duy đã được tạo!")
                    save_current_session()

                    st.rerun()
                except Exception as e: st.error(f"Lỗi: {e}")
        
        with col_m2:
            if st.session_state['mermaid_code']:
                st.markdown('<div style="background:white; padding:15px; border-radius:15px;">', unsafe_allow_html=True)
                st_mermaid(st.session_state['mermaid_code'], height=500)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align:center; padding:50px; color:#555;'>Chưa có sơ đồ hiển thị</div>", unsafe_allow_html=True)

        chat_container = st.container(height=450)
        with chat_container:
            if not st.session_state['chat_history']:
                st.markdown("<div style='text-align:center; color:#555; margin-top:20px;'>Hãy hỏi tôi về nội dung cuộc họp...</div>", unsafe_allow_html=True)
            
            for msg in st.session_state['chat_history']:
                avatar = "👾" if msg['role']=="user" else "🤖"
                with st.chat_message(msg['role'], avatar=avatar):
                    st.markdown(msg['text'])
        
    if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
        st.session_state['chat_history'].append({"role": "user", "text": prompt})
        with chat_container:
            with st.chat_message("user", avatar="👾"): st.markdown(prompt)
            
            with st.chat_message("model", avatar="🤖"):
                with st.spinner("AI đang trả lời..."):
                    try:
                        if not st.session_state.get('chat_session'):
                            current_model_name = st.session_state.selected_model_option.split(" ")[0]
                            st.session_state['chat_session'] = genai.GenerativeModel(current_model_name).start_chat(history=[])
                                
                        full_prompt = st.session_state['context_prompt'] + "\nUser Question: " + prompt + "\n(Hãy trả lời bằng Tiếng Việt)"
                        resp = st.session_state['chat_session'].send_message(full_prompt)
                        
                        st.markdown(resp.text)
                        st.session_state['chat_history'].append({"role": "model", "text": resp.text})
                        save_current_session()
                    except Exception as e: st.error(f"Lỗi: {e}")