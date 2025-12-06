import streamlit as st
import pandas as pd
import pymysql

# ================= 页面配置 =================
st.set_page_config(
    page_title="全网商品比价系统",
    page_icon="🛒",
    layout="wide"
)

# ================= 数据库连接  =================

def get_connection():
    try:
        return pymysql.connect(
            host=st.secrets["db_host"],
            port=st.secrets["db_port"],
            user=st.secrets["db_user"],
            password=st.secrets["db_password"],
            db=st.secrets["db_name"],
            charset='utf8mb4',
            # 你原来验证过这个配置能跑，我们就完全不动它
            # cursorclass=pymysql.cursors.DictCursor,
            ssl={'ssl': {}}
        )
    except Exception as e:
        st.error(f"数据库连接失败: {e}")
        return None

# ================= 数据查询函数 =================
def search_products(keyword):
    conn = get_connection()
    if not conn:
        return pd.DataFrame()

    try:
        if keyword:
            sql = """
                  SELECT goods_id, goods_name, face_value, goods_price, min_level_price, category_path, created_at
                  FROM products
                  WHERE goods_name LIKE %s 
                     OR category_path LIKE %s
                  ORDER BY goods_price ASC LIMIT 100
                  """
            params = (f'%{keyword}%', f'%{keyword}%')
        else:
            sql = """
                  SELECT goods_id, goods_name, face_value, goods_price, min_level_price, category_path, created_at
                  FROM products
                  ORDER BY created_at DESC LIMIT 20
                  """
            params = ()

        # pandas read_sql 完美支持 pymysql，不需要改
        df = pd.read_sql(sql, conn, params=params)
        return df

    except Exception as e:
        st.error(f"查询出错: {e}")
        return pd.DataFrame()
    finally:
        # ✅ 用完就关，保证不占用资源，也不会超时
        conn.close()

# ================= 网页 UI 布局 =================
st.title("🛒 内部商品比价查询系统")
st.caption("数据源：TiDB Serverless | 部署：Streamlit Cloud")

# --- 侧边栏 ---
with st.sidebar:
    st.header("🔍 搜索过滤")
    keyword = st.text_input("请输入关键词", placeholder="例如：QQ会员, 70级...")
    st.info(f"💡 提示：支持搜索商品名或分类路径")

    if st.button("刷新数据"):
        st.cache_data.clear()
        st.rerun()

# --- 主内容区 ---
df = search_products(keyword)

if not df.empty:
    if keyword:
        st.success(f"找到 {len(df)} 条关于 '{keyword}' 的结果")
    else:
        st.info("🆕 最新入库的商品列表")

    # 展示漂亮的表格
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "goods_id": "商品ID",
            "goods_name": "商品名称",
            "face_value": st.column_config.NumberColumn("原价", format="¥ %.2f"),
            "goods_price": st.column_config.NumberColumn("售价", format="¥ %.2f"),
            "min_level_price": st.column_config.NumberColumn("最低价", format="¥ %.2f"),
            "category_path": "所属分类",
            "created_at": st.column_config.DatetimeColumn("抓取时间", format="MM-DD HH:mm"),
        }
    )
else:
    if keyword:
        st.warning("没有找到相关商品，请尝试其他关键词。")
    else:
        st.warning("数据库中暂无数据，请检查爬虫是否运行。")