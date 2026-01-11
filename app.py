import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import requests
from map_utils import search_shops, upload_shop_image, delete_shop_image, get_signed_image_url
from supabase import create_client, Client
import time
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="店铺地图管理",
    page_icon="🗺️",
    layout="wide"
)

# Constants
CSV_FILE = "shops_data.csv"
GAODE_URL = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}'

# Supabase Credentials - loaded from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Default columns for the CSV/Data Frame
COLUMNS = ['shop_name', 'city', 'address', 'latitude', 'longitude', 'shop_type', 'type', 'visit_status', 'notes', 'rating', 'image_url']

def init_supabase():
    if 'supabase' not in st.session_state:
        st.session_state.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def init_session_state():
    init_supabase()
    # Handle OAuth callback if present
    handle_oauth_callback()
    
    if 'user' not in st.session_state:
        try:
            # First check if handle_oauth_callback already set the user
            # If not, check the backend for a persistent session
            session = st.session_state.supabase.auth.get_session()
            if session:
                st.session_state.user = session.user
            else:
                st.session_state.user = None
        except:
            st.session_state.user = None
            
    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'auth_view' not in st.session_state:
        st.session_state.auth_view = None # 'login' or 'signup'
    if 'selected_shop_index' not in st.session_state:
        st.session_state.selected_shop_index = None
    if 'last_click_data' not in st.session_state:
        st.session_state.last_click_data = None

def handle_oauth_callback():
    """Handle the redirect back from Supabase OAuth."""
    # Handle the OAuth code in the URL
    if "code" in st.query_params:
        code = st.query_params["code"]
        verifier = st.session_state.get("pkce_verifier")
        
        try:
            # We explicitly pass the verifier that we saved before redirecting
            if verifier:
                res = st.session_state.supabase.auth.exchange_code_for_session({
                    "auth_code": code,
                    "code_verifier": verifier
                })
            else:
                # Fallback to automatic exchange
                res = st.session_state.supabase.auth.exchange_code_for_session({
                    "auth_code": code,
                })

            if res and res.user:
                st.session_state.user = res.user
                st.session_state.data = None # Force reload
                st.session_state.auth_view = None # Close dialog
                # Cleanup verifier
                if "pkce_verifier" in st.session_state:
                    del st.session_state["pkce_verifier"]
                try:
                    st.query_params.clear()
                except:
                    pass
                st.rerun()
        except Exception as e:
            # Check if session was already established anyway
            session = st.session_state.supabase.auth.get_session()
            if session and session.user:
                st.session_state.user = session.user
                st.session_state.auth_view = None
                try:
                    st.query_params.clear()
                except:
                    pass
                st.rerun()
            else:
                 st.error(f"Google 登录失败: {str(e)}")
                 try:
                    st.query_params.clear()
                 except:
                    pass

@st.dialog("🔒 用户登录")
def login_dialog():
    with st.form("login_form_dialog"):
        email = st.text_input("邮箱", key="login_email_dlg")
        password = st.text_input("密码", type="password", key="login_password_dlg")
        submit = st.form_submit_button("登录", use_container_width=True, type="primary")
        
        if submit:
            authenticate_user(email, password)

    st.markdown("<div style='text-align: center; margin: 10px 0;'>或</div>", unsafe_allow_html=True)
    
    # Google Login Button
    try:
        # Determine the base URL
        # For local development, it's usually localhost:8501 or 8503.
        # For production, it is https://china-map.streamlit.app/
        # We can try to detect or just set it based on a simple check or environment variable.
        
        # Default to the production URL if we are not clearly on localhost
        # (You can also set this in .env)
        redirect_url = "https://china-map.streamlit.app/"
        
        # If running locally (simple check), override
        # Note: This is a hacky check; ideally use an ENV var like APP_URL
        if "localhost" in str(st.query_params) or os.getenv("IS_LOCAL"):
             redirect_url = "http://localhost:8503" # Or 8501
        
        # FORCE override for testing per your request
        # redirect_url = "http://localhost:8503" 
        
        # Better strategy: Use the production URL by default now that you gave it to me
        # But for your local testing to work, you must add http://localhost:8503 to Supabase Redirect URLs
        # Since I cannot see your browser URL bar for sure, I will let you toggle or set it via ENV.
        # For now, I'll update it to check an environment variable or default to the hosted one.
        
        redirect_url = os.getenv("APP_URL", "https://china-map.streamlit.app/")

        res = st.session_state.supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirectTo": redirect_url,
                "skip_browser_redirect": True
            }
        })
        
        # Save the code_verifier
        if hasattr(res, 'code_verifier'):
            st.session_state.pkce_verifier = res.code_verifier

        if res.url:
            st.link_button("🚀 使用 Google 账号登录", res.url, use_container_width=True)
    except Exception as e:
        st.warning(f"Google 登录暂时不可用: {str(e)}")

    st.divider()
    if st.button("没有账号？去注册", use_container_width=True):
        st.session_state.auth_view = 'signup'
        st.rerun()

@st.dialog("📝 用户注册")
def signup_dialog():
    with st.form("signup_form_dialog"):
        email = st.text_input("邮箱", key="signup_email_dlg")
        password = st.text_input("密码", type="password", key="signup_password_dlg")
        submit = st.form_submit_button("注册", use_container_width=True, type="primary")
        
        if submit:
            authenticate_user(email, password, is_signup=True)
            
    st.divider()
    if st.button("已有账号？去登录", use_container_width=True):
        st.session_state.auth_view = 'login'
        st.rerun()

def authenticate_user(email, password, is_signup=False):
    supabase = st.session_state.supabase
    try:
        if is_signup:
            response = supabase.auth.sign_up({"email": email, "password": password})
            if response.user:
                st.success("注册成功！请到邮箱点击确认链接。")
                time.sleep(2)
                st.session_state.auth_view = 'login'
                st.rerun()
        else:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if response.user:
                st.session_state.user = response.user
                st.session_state.data = None # Force reload from Cloud
                st.session_state.auth_view = None # Clear auth view on success
                st.rerun()
    except Exception as e:
        st.error(f"认证失败: {str(e)}")

def load_data():
    """Load shop data from Supabase (if logged in) or CSV file (local)."""
    supabase = st.session_state.supabase
    
    if st.session_state.user:
        # Load from Supabase
        try:
            # Check session validity
            try:
                session = supabase.auth.get_session()
                if not session:
                    raise Exception("Session expired")
            except Exception:
                 st.warning("会话已过期，请重新登录")
                 st.session_state.user = None
                 st.rerun()

            response = supabase.table('user_shops').select("*").execute()
            data = response.data
            
            if not data and os.path.exists(CSV_FILE):
                # Migration logic: If DB is empty but local file exists, migrate it
                st.info("首次登录，正在同步本地数据到云端...")
                local_df = pd.read_csv(CSV_FILE)
                # Clean local data to match DB schema
                local_df = normalize_dataframe(local_df)
                if not local_df.empty:
                    records = local_df.to_dict('records')
                    # Insert to Supabase
                    # Clean records for insert (NaN to None)
                    cleaned_records = []
                    for record in records:
                        if pd.isna(record['latitude']): record['latitude'] = None
                        if pd.isna(record['longitude']): record['longitude'] = None
                        if pd.isna(record['rating']): record['rating'] = 0
                        cleaned_records.append(record)

                    supabase.table('user_shops').insert(cleaned_records).execute()
                    # Re-fetch
                    response = supabase.table('user_shops').select("*").execute()
                    data = response.data
                st.success("同步完成！")
            
            if data:
                df = pd.DataFrame(data)
                # Ensure columns present
                df = normalize_dataframe(df)
                return df
            else:
                return create_empty_dataframe()
                
        except Exception as e:
            st.error(f"加载数据失败: {str(e)}")
            return create_empty_dataframe()
    else:
        # Load Local CSV
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            return normalize_dataframe(df)
        else:
            return create_empty_dataframe()

def normalize_dataframe(df):
    """Ensure dataframe has correct columns and types."""
    # Add missing columns
    for col in COLUMNS:
        if col not in df.columns:
            if col == 'visit_status':
                df[col] = "Want to Visit"
            elif col == 'rating':
                df[col] = 0
            elif col == 'city':
                df[col] = ""
            elif col == 'type':
                df[col] = "Coffee"
            elif col == 'image_url':
                df[col] = None
            else:
                df[col] = ""
    
    # Filter only relevant columns (drop Supabase system cols like id, created_at for the UI view)
    # But wait, if we drop ID, we can't update specific rows easily.
    # We will keep 'id' if it exists but handle it carefully.
    
    # Enforce data types
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0).astype(int)
    df['notes'] = df['notes'].astype(str).replace('nan', '')
    df['city'] = df['city'].astype(str).replace('nan', '')
    
    return df

def create_empty_dataframe():
    df = pd.DataFrame(columns=COLUMNS)
    df['rating'] = df['rating'].astype(int)
    df['notes'] = df['notes'].astype(str)
    df['city'] = df['city'].astype(str)
    return df

def save_data(df):
    """Save shop data to Supabase (if logged in) or CSV file. Returns True if successful."""
    
    if st.session_state.user:
        supabase = st.session_state.supabase
        try:
            # Sync strategy: Delete all for user and re-insert.
            user_id = st.session_state.user.id
            
            # Prepare data for insertion
            save_df = df[COLUMNS].copy()
            records = save_df.to_dict('records')
            
            cleaned_records = []
            for record in records:
                # Sanitization
                cleaned_record = {}
                cleaned_record['user_id'] = user_id # Explicitly set owner
                
                # Copy fields with cleaning and type enforcement
                for key, value in record.items():
                    if key in ['latitude', 'longitude']:
                        if pd.isna(value) or value == '':
                            cleaned_record[key] = None
                        else:
                            try:
                                cleaned_record[key] = float(value)
                            except:
                                cleaned_record[key] = None
                    
                    elif key == 'rating':
                        try:
                            # Handle empty string or nan
                            if pd.isna(value) or str(value).strip() == '':
                                cleaned_record[key] = 0
                            else:
                                cleaned_record[key] = int(float(value)) # Handle '4.0' strings
                        except:
                            cleaned_record[key] = 0
                            
                    elif key == 'visit_status':
                        cleaned_record[key] = str(value) if pd.notna(value) else "Want to Visit"
                        
                    elif key == 'type':
                        cleaned_record[key] = str(value) if pd.notna(value) else "Coffee"
                        
                    elif key == 'image_url':
                        cleaned_record[key] = str(value) if pd.notna(value) and value != '' else None

                    else:
                         cleaned_record[key] = str(value) if pd.notna(value) else ""
                
                cleaned_records.append(cleaned_record)

            # Transaction-ish
            # 1. Delete all existing
            supabase.table('user_shops').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            
            # 2. Insert new
            if cleaned_records:
                supabase.table('user_shops').insert(cleaned_records).execute()
            
            return True
                
        except Exception as e:
            st.error(f"Failed to save to cloud: {str(e)}")
            return False
    else:
        try:
            df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            st.error(f"Failed to save local file: {str(e)}")
            return False

def add_shop_to_data(current_df, shop_data, journey_type="Coffee"):
    """Add a new shop to the dataframe."""
    new_row = pd.DataFrame([{
        'shop_name': shop_data['name'],
        'city': shop_data.get('city', ''),
        'address': shop_data['address'],
        'latitude': shop_data['latitude'],
        'longitude': shop_data['longitude'],
        'shop_type': shop_data.get('type', '其他'),
        'type': journey_type,
        'visit_status': 'Want to Visit',
        'notes': '',
        'visit_status': 'Want to Visit',
        'notes': '',
        'rating': 0,
        'image_url': None
    }])
    return pd.concat([current_df, new_row], ignore_index=True)

def create_map(df):
    """Create a Folium map with Gaode tiles and shop markers."""
    center_lat = 39.9042
    center_lon = 116.4074

    valid_rows = df.dropna(subset=['latitude', 'longitude'])
    if not valid_rows.empty:
        center_lat = valid_rows['latitude'].iloc[0]
        center_lon = valid_rows['longitude'].iloc[0]

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles=None,
        attribution_control=False
    )

    folium.TileLayer(
        tiles=GAODE_URL,
        attr='Amap',
        name='高德地图',
        overlay=False,
        control=False
    ).add_to(m)

    ICON_MAP = {
        "餐饮": "cutlery",
        "餐饮服务": "cutlery",
        "零售": "shopping-cart",
        "服务": "wrench",
        "娱乐": "gamepad",
        "教育": "book",
        "医疗": "medkit",
        "风景名胜": "camera",
        "其他": "info-circle"
    }

    for _, row in df.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']):
            try:
                lat = float(row['latitude'])
                lon = float(row['longitude'])
                status = row.get('visit_status', 'Want to Visit')
                color = 'red' if status == 'Visited' else 'green'
                shop_type = row.get('shop_type', '其他')
                icon_name = ICON_MAP.get(shop_type, "info-circle")
                rating = row.get('rating', 0)
                stars = "⭐" * int(rating) if rating > 0 else "无评分"

                popup_html = f"""
                <div style="min-width: 200px; font-family: sans-serif;">
                    <h4 style="margin: 0 0 10px 0; color: #333;">{row.get('shop_name', 'N/A')}</h4>
                    <p style="margin: 5px 0;"><b>地址:</b> {row.get('address', 'N/A')}</p>
                    <p style="margin: 5px 0;"><b>类型:</b> {row.get('shop_type', 'N/A')}</p>
                    <p style="margin: 5px 0;"><b>状态:</b> <span style="color: {'#d9534f' if status == 'Visited' else '#5cb85c'};">{status}</span></p>
                    <p style="margin: 5px 0;"><b>评分:</b> {stars}</p>
                    <hr style="margin: 10px 0; border: none; border-top: 1px solid #eee;">
                    <p style="margin: 5px 0;"><b>备注:</b><br>{row.get('notes', '无')}</p>
                </div>
                """

                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=row.get('shop_name', '店铺'),
                    icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
                ).add_to(m)
            except (ValueError, TypeError):
                continue
    return m

def manage_shop_image_dialog(index):
    # Fetch latest row from session state
    if index not in st.session_state.data.index:
        st.error("店铺未找到")
        st.session_state.selected_shop_index = None
        return

    row = st.session_state.data.loc[index]
    
    with st.container(border=True):
        col_head, col_close = st.columns([0.9, 0.1])
        with col_head:
            st.write(f"### {row['shop_name']}")
        with col_close:
            if st.button("✖️", key=f"close_details_{index}", help="关闭"):
                st.session_state.selected_shop_index = None
                st.rerun()

        st.write(f"📍 {row['address']}")
        
        # Parse images
        raw_images = row.get('image_url')
        image_list = []
        if pd.notna(raw_images) and raw_images:
            try:
                # Try to parse as JSON list
                parsed = json.loads(str(raw_images))
                if isinstance(parsed, list):
                    image_list = parsed
                else:
                    # Single string legacy
                    image_list = [str(raw_images)]
            except:
                # Not JSON, treat as single string
                if str(raw_images).strip():
                    image_list = [str(raw_images)]
        
        if image_list:
            st.write(f"**图片 ({len(image_list)})**")
            cols = st.columns(3)
            for i, img_url in enumerate(image_list):
                with cols[i % 3]:
                    # Use signed URL logic (works for both Public and Private buckets if user is logged in)
                    display_url = img_url
                    if st.session_state.user:
                        display_url = get_signed_image_url(st.session_state.supabase, img_url)
                        
                    st.image(display_url, use_container_width=True)
                    if st.button("🗑️", key=f"del_{index}_{i}", help="删除这张图片"):
                        # Delete logic
                        target_url = image_list[i]
                        
                        # Delete from Cloud Storage if logged in
                        if st.session_state.user:
                            delete_shop_image(st.session_state.supabase, target_url)
                            
                        new_list = image_list.copy()
                        new_list.pop(i)
                        
                        # Save back
                        if not new_list:
                            st.session_state.data.at[index, 'image_url'] = None
                        else:
                            st.session_state.data.at[index, 'image_url'] = json.dumps(new_list)
                            
                        if save_data(st.session_state.data):
                            st.success("已删除")
                            time.sleep(0.5)
                            st.rerun()
        else:
            st.info("暂无图片")
        
        st.divider()
        
        # State management for uploader visibility
        upload_state_key = f"show_upload_{index}"
        if upload_state_key not in st.session_state:
            st.session_state[upload_state_key] = False

        if not st.session_state[upload_state_key]:
            if st.button("📸 上传新图片", use_container_width=True, key=f"btn_show_upload_{index}"):
                st.session_state[upload_state_key] = True
                st.rerun()
        else:
            st.info("请选择图片文件上传")
            uploaded_file = st.file_uploader("选择图片", type=['png', 'jpg', 'jpeg', 'webp'], key=f"uploader_{index}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ 取消", key=f"btn_cancel_{index}"):
                    st.session_state[upload_state_key] = False
                    st.rerun()
            with col2:
                if uploaded_file:
                    if st.button("☁️ 上传并保存", type="primary", key=f"btn_upload_{index}"):
                         if not st.session_state.user:
                             st.error("请先登录以使用云端存储功能。")
                         else:
                             with st.spinner("正在上传图片到 Supabase..."):
                                 user_id = st.session_state.user.id
                                 # Use shop name hash or just name for folder structure
                                 url = upload_shop_image(st.session_state.supabase, uploaded_file, user_id, row['shop_name'])
                                 
                                 if url:
                                     # Append to existing list
                                     current_list = image_list.copy()
                                     current_list.append(url)
                                     
                                     st.session_state.data.at[index, 'image_url'] = json.dumps(current_list)
                                     # Trigger save
                                     if save_data(st.session_state.data):
                                         st.success("上传成功！")
                                         st.session_state[upload_state_key] = False # Reset
                                         time.sleep(1)
                                         st.rerun()
                                 else:
                                     st.error("上传失败，请重试。")

def get_shop_index_from_click(click_data, df):
    if not click_data:
        return None
    
    lat = click_data['lat']
    lng = click_data['lng']
    
    # Find closest match within small tolerance
    # epsilon = 0.0001 (~10 meters)
    epsilon = 0.0001
    
    for idx, row in df.iterrows():
        try:
            d_lat = abs(float(row['latitude']) - lat)
            d_lng = abs(float(row['longitude']) - lng)
            if d_lat < epsilon and d_lng < epsilon:
                return idx
        except:
            continue
            
    return None

def main():
    init_session_state()
    
    # Sidebar: Search & Settings
    with st.sidebar:
        st.header("🔍 地点搜索")
        with st.form(key="search_form", clear_on_submit=False):
            search_keyword = st.text_input("地点名称", placeholder="例如: 深圳星巴克")
            if st.form_submit_button("搜索", use_container_width=True):
                if search_keyword:
                    with st.spinner("正在搜索..."):
                        results = search_shops(search_keyword)
                        if results:
                            st.session_state.search_results = results
                        else:
                            st.warning("未找到相关地点")
                            st.session_state.search_results = []

        if 'search_results' in st.session_state and st.session_state.search_results:
            st.divider()
            st.subheader("搜索结果")
            for i, result in enumerate(st.session_state.search_results):
                with st.container():
                    st.markdown(f"**{i+1}. {result['name']}**")
                    if result.get('city'):
                        st.markdown(f"🏙️ 城市: {result['city']}")
                    st.markdown(f"📍 地址: {result['address']}")
                    st.markdown(f"🌐 坐标: {result['latitude']:.6f}, {result['longitude']:.6f}")
                    st.markdown(f"🏷️ 类型: {result['type']}")

                    if st.button(f"➕ 添加到列表", key=f"add_{i}"):
                        st.session_state.data = add_shop_to_data(st.session_state.data, result, journey_type)
                        if save_data(st.session_state.data):
                            st.success(f"已添加: {result['name']}")
                            st.rerun()
                    st.divider()

        st.divider()
        st.header("⚙️ 地图设置")
        journey_type = st.selectbox("Journey Type", ["Coffee", "Scenery", "Food", "Bar", "Other"], index=0)
        
        st.divider()
        st.header("👤 用户中心")
        if st.session_state.user:
            st.success(f"已登录: {st.session_state.user.email}")
            if st.button("退出登录", use_container_width=True):
                st.session_state.supabase.auth.sign_out()
                st.session_state.user = None
                st.session_state.data = None # Clear data to trigger reload
                st.rerun()
        else:
            if st.button("🔐 登录 / 注册", use_container_width=True, type="primary"):
                st.session_state.auth_view = 'login'
                st.rerun()
            
            # Persist dialog if state is set
            auth_v = st.session_state.get('auth_view')
            if auth_v == 'login':
                login_dialog()
            elif auth_v == 'signup':
                signup_dialog()

            st.info("💡 当前为本地模式。登录后可切换到云端模式。")

    # Emoji mapping
    emoji_map = {
        "Coffee": "☕︎",
        "Scenery": "🏞️",
        "Food": "🍛",
        "Bar": "🍸",
        "Other": "📍"
    }
    selected_emoji = emoji_map.get(journey_type, "")

    st.title(f"My {selected_emoji} {journey_type} Journeys")

    # Initialize data if needed
    if st.session_state.data is None:
        st.session_state.data = load_data()

    # Create tabs
    tab_map, tab_table = st.tabs(["🗺️ 地图视图", "📋 数据表格"])

    # Map Tab
    with tab_map:
        current_data = edited_df if 'edited_df' in locals() else st.session_state.data
        if not current_data.empty:
            map_data = current_data[current_data['type'] == journey_type] if 'type' in current_data.columns else current_data
            if not map_data.empty:
                map_obj = create_map(map_data)
                output = st_folium(map_obj, use_container_width=True, height=600)
                
                # Handle Interactions
                # Handle Interactions
                click_data = output.get('last_object_clicked')
                if click_data and click_data != st.session_state.get('last_click_data'):
                     st.session_state.last_click_data = click_data
                     clicked_idx = get_shop_index_from_click(click_data, st.session_state.data)
                     if clicked_idx is not None:
                         st.session_state.selected_shop_index = clicked_idx
                         st.rerun()
                
                if st.session_state.get('selected_shop_index') is not None:
                     manage_shop_image_dialog(st.session_state.selected_shop_index)
                valid_count = map_data.dropna(subset=['latitude', 'longitude']).shape[0]
                st.info(f"📍 地图上显示 {valid_count} 个 {journey_type} 店铺位置")
            else:
                st.warning(f"暂无 {journey_type} 店铺数据。")
        else:
            st.warning("暂无数据。")

    # Table Tab Setup
    with tab_table:
        st.subheader("店铺数据管理")
        st.markdown("在下方表格中添加、编辑或删除店铺信息。" + (" (数据已同步至云端)" if st.session_state.user else " (本地模式)"))

        column_config = {
            "shop_name": st.column_config.TextColumn("店铺名称", required=True),
            "city": st.column_config.TextColumn("城市"),
            "address": st.column_config.TextColumn("地址"),
            "shop_type": st.column_config.TextColumn("店铺类型"),
            "type": st.column_config.SelectboxColumn("Journey Type", options=["Coffee", "Scenery", "Food", "Bar", "Other"], required=True),
            "visit_status": st.column_config.SelectboxColumn("访问状态", options=["Want to Visit", "Visited"], required=True),
            "notes": st.column_config.TextColumn("备注"),
            "rating": st.column_config.NumberColumn("评分", min_value=0, max_value=5, format="%d ⭐")
        }

        # Show table
        display_columns = ['shop_name', 'city', 'address', 'shop_type', 'type', 'visit_status', 'notes', 'rating']

        if not st.session_state.data.empty:
            display_df = st.session_state.data[display_columns].copy()
            
            edited_display_df = st.data_editor(
                display_df,
                column_config=column_config,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key="data_editor"
            )

            # Process edits
            if not edited_display_df.equals(display_df):
                # We need to reconstruct the full dataframe including hidden columns (lat/long)
                # This logic is tricky because rows might be added or deleted.
                # However, our save_data strategy for cloud is "Replcae All", so we just need to preserve lat/lon for existing rows.
                
                new_df = edited_display_df.copy()
                new_df['latitude'] = None
                new_df['longitude'] = None
                new_df['image_url'] = None

                # Match with old data to recover lat/lon
                # We assume row order/content helps matching or we just accept that edited rows might lose lat/lon if we can't match?
                # Actually, standard Streamlit pattern for this is to keep the original index.
                # But we did hide_index=True and re-generated display_df.
                # Robust way: Treat it as a fresh dataset where possible.
                # But we don't want to lose lat/lon.
                
                # Let's try to match by 'shop_name' + 'address' as a composite key if possible? No, names change.
                # Since we passed `display_df` (a copy) to `data_editor`, the returned `edited_display_df` has the SAME index as `display_df` (which is the original index of `st.session_state.data` if we didn't reset it).
                # `display_df = st.session_state.data[display_columns].copy()` retains the original index.
                # So `edited_display_df` should also have the original index for modified rows.
                # New rows will have new indices.
                
                for idx in new_df.index:
                    if idx in st.session_state.data.index:
                        new_df.at[idx, 'latitude'] = st.session_state.data.at[idx, 'latitude']
                        new_df.at[idx, 'longitude'] = st.session_state.data.at[idx, 'longitude']
                        new_df.at[idx, 'image_url'] = st.session_state.data.at[idx, 'image_url']
                
                # Save
                if save_data(new_df):
                    st.session_state.data = new_df
                    st.rerun()
        else:
            # Empty table case
            edited_display_df = st.data_editor(
                pd.DataFrame(columns=display_columns),
                column_config=column_config,
                num_rows="dynamic",
                use_container_width=True,
                key="empty_editor"
            )
            if not edited_display_df.empty:
                # User added first row
                 # Reconstruct full DF
                new_df = edited_display_df.copy()
                new_df['latitude'] = None 
                new_df['longitude'] = None
                new_df['image_url'] = None
                if save_data(new_df):
                    st.session_state.data = new_df
                    st.rerun()

    # Search and User Center moved to top of main for better sidebar flow

if __name__ == "__main__":
    main()
