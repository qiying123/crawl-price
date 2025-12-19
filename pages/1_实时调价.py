import streamlit as st
import pandas as pd
import pymysql

# ================= 1. 页面配置 =================
st.set_page_config(
    page_title="实时调价监控",
    page_icon="📈",
    layout="wide"
)

st.title("📈 实时调价监控")
st.caption("数据来源于 `current_price_update` 表，记录了各商品的价格变动历史。")

# ================= 2. 数据库连接 =================
# @st.cache_resource
def get_price_update_connection():
    """连接到存储价格变动记录的数据库"""
    try:
        # 注意：这里使用了与主应用不同的数据库配置
        return pymysql.connect(
            host=st.secrets["db_host"],
            port=st.secrets["db_port"],
            user=st.secrets["db_user"],
            password=st.secrets["db_password"],
            db=st.secrets["db_name"],
            charset='utf8mb4',
            ssl={'ssl': {}}
        )
    # try:
    #     # 注意：这里使用了本地数据库来调试
    #     return pymysql.connect(
    #         host="localhost",  # 直接指定主机名
    #         port=3306,  # 直接指定端口号
    #         user="root",  # 直接指定用户名
    #         password="123",  # 直接指定密码
    #         db="xinqidian_index",
    #         charset='utf8mb4',
    #         ssl={'ssl': {}}
    #     )
    except Exception as e:
        st.error(f"数据库 'xinqidian_index' 连接失败: {e}")
        return None

# ================= 3. 数据查询逻辑 =================
@st.cache_data(ttl=300) # 缓存5分钟
def fetch_price_updates(price_change_filter, source_filter):
    """从数据库获取价格变动数据"""
    conn = get_price_update_connection()
    if not conn:
        return pd.DataFrame()

    # 基础查询
    query = "SELECT * FROM current_price_update"
    
    # 构建筛选条件
    conditions = []
    params = []
    
    # 调价类型筛选
    if price_change_filter == "📈 仅看涨价":
        conditions.append("price_change > 0")
    elif price_change_filter == "📉 仅看降价":
        conditions.append("price_change < 0")

    # 来源筛选 (通过goods_type来区分)
    if source_filter == "来源: XQD":
        conditions.append("goods_type IS NOT NULL") # XQD有goods_type
    elif source_filter == "来源: LY":
        conditions.append("goods_type IS NULL") # LY没有goods_type

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY create_time DESC LIMIT 500" # 按时间倒序，最多显示500条

    try:
        df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        st.warning(f"查询价格变动数据时出错: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

# ================= 4. 侧边栏筛选器 =================
with st.sidebar:
    st.header("⚙️ 筛选选项")
    
    # 调价类型筛选
    price_change_filter = st.radio(
        "调价类型",
        ["所有变动", "📈 仅看涨价", "📉 仅看降价"],
        horizontal=True,
        label_visibility="collapsed"
    )

    # 来源筛选
    source_filter = st.selectbox(
        "选择数据来源",
        ["所有来源", "来源: XQD", "来源: LY"]
    )

    if st.button("🔄 强制刷新数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ================= 5. 主界面展示 =================
df = fetch_price_updates(price_change_filter, source_filter)

if not df.empty:
    st.metric("总记录数", f"{len(df)} 条")

    # 数据高亮显示
    def highlight_price_change(val):
        color = ''
        if val > 0:
            color = 'red'
        elif val < 0:
            color = 'green'
        return f'color: {color}; font-weight: bold;'

    st.dataframe(
        df.style.applymap(highlight_price_change, subset=['price_change']),
        use_container_width=True,
        hide_index=True,
        column_config={
            "goods_name": "商品名称",
            "before_price": st.column_config.NumberColumn("原价", format="¥%.2f"),
            "price_change": st.column_config.NumberColumn("价格变动", format="%.2f"),
            "after_price": st.column_config.NumberColumn("现价", format="¥%.2f"),
            "create_time": st.column_config.DatetimeColumn("变动时间", format="YYYY-MM-DD HH:mm:ss"),
        },
        column_order=("goods_name", "before_price", "price_change", "after_price", "create_time")
    )
else:
    st.info("在当前筛选条件下，没有找到价格变动记录。")

# 页脚
st.markdown("---")
st.caption("数据每 5 分钟自动刷新一次。")
