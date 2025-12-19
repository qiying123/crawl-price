import streamlit as st
import pandas as pd
import pymysql
import numpy as np

# ================= 1. 页面配置 & CSS 美化 =================
st.set_page_config(

    page_title="商品比价系统",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS，美化搜索框等前端元素显示
st.markdown("""
<style>
    /* ... [CSS content remains the same, so it's omitted for brevity] ... */
    .block-container { padding-top: 3rem; padding-bottom: 3rem; }
    div[data-testid="stTextInput"] { position: relative !important; min-height: 75px !important; }
    div[data-testid="stTextInput"] > div { border: none !important; box-shadow: none !important; background: transparent !important; }
    div[data-testid="stTextInput"] input { font-size: 1.5rem !important; padding: 1rem 1.5rem !important; line-height: 1.5; border-radius: 12px !important; border: 2px solid #e0e0e0 !important; box-shadow: 0 4px 6px rgba(0,0,0,0.08) !important; position: absolute; top: 50%; transform: translateY(-50%); width: 100%; box-sizing: border-box; }
    div[data-testid="stTextInput"] input:focus { border-color: #80bdff !important; box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25) !important; outline: none !important; }
    div[data-testid="stTextInput"] div[data-testid="InputInstructions"] { display: none !important; }
    .avatar-img { border-radius: 50%; width: 150px; display: block; margin-left: auto; margin-right: auto; margin-bottom: 20px; }
    .custom-metric-label { font-size: 0.9rem; margin-bottom: -8px; }
    .custom-metric-value { font-size: 1.3rem; font-weight: 600; white-space: normal; word-break: break-word; line-height: 1.4; }
</style>
""", unsafe_allow_html=True)

# ================= 2. 搜索别名配置 =================
SYNONYM_MAP = {
    "拼多多": "PDD",
    "淘宝": "TB",
    "咸鱼": "闲鱼",
    "闲鱼": "XY",
    "京东": "京东",
    "JD": "京东",

    # === 视频会员别名 ===
    "b站": "哔哩哔哩",
    "B站": "哔哩哔哩",
    "小破站": "哔哩哔哩",
    "iqiyi": "爱奇艺",
    "271": "爱奇艺",
    "奇异果": "爱奇艺",
    "腾讯视频": "腾讯视频",
    "鹅厂": "腾讯",
    "youku": "优酷",
    "芒果": "芒果TV",
    "mg": "芒果TV",
    "油管": "YouTube", # 虽然数据里没有，但常备
    "nf": "Netflix",   # 同上
    "南瓜": "南瓜电影",

    # === 音乐音频别名 ===
    "网抑云": "网易云",
    "云村": "网易云",
    "扣扣音乐": "QQ音乐",
    "喜马": "喜马拉雅",
    "猫耳": "猫耳FM",

    # === 社交与通讯 ===
    "企鹅": "QQ",
    "扣扣": "QQ",
    "vx": "微信",
    "wechat": "微信",
    "wb": "微博",
    "渣浪": "新浪微博",

    # === 话费充值 ===
    "移动": "移动话费",
    "联通": "联通充值",
    "电信": "电信充值",
    "话费": "充值缴费区",

    # === 餐饮美食 (英文转中文) ===
    "kfc": "肯德基",
    "KFC": "肯德基",
    "开封菜": "肯德基",
    "mcd": "麦当劳",
    "MCD": "麦当劳",
    "金拱门": "麦当劳",
    "luckin": "瑞幸",
    "星爸": "星巴克",
    "starbucks": "星巴克",
    "heytea": "喜茶",
    "coco": "CoCo",
    "雪王": "蜜雪冰城",
    "饿了么": "饿了么",
    "elm": "饿了么",
    "美团": "美团",
    "mt": "美团",

    # === 网盘与工具 ===
    "度盘": "百度网盘",
    "百度云": "百度网盘",
    "夸克": "夸克",
    "迅雷": "迅雷",
    "115": "115网盘",
    "梯子": "加速器", # 泛指
    "vpn": "加速器",
    "office": "微软office",
    "ppt": "WPS",

    # === 游戏黑话 ===
    "农药": "王者",
    "药水": "王者",
    "王者荣耀": "王者点卷",
    "吃鸡": "和平点卷",
    "和平精英": "和平点卷",
    "LOL": "联盟",
    "撸啊撸": "联盟",
    "英雄联盟": "联盟",
    "原神": "原神",
    "铲子": "金铲",
    "金铲铲": "金铲",
    "dnf": "DNF",
    "地下城": "DNF",
    "cf": "CFM",
    "穿越火线": "CFM",
    "蛋仔": "蛋仔",

    # === 出行与生活 ===
    "滴滴": "滴滴出行",
    "哈罗": "哈啰",
    "单车": "单车", # 泛指
    "打车": "出行", # 泛指
    "e卡": "京东E卡",
    "加油": "团油",
}

# ================= 3. 数据库连接 =================
## 这里连接的是我的云端数据库，如需部署请修改成自己的数据库
def get_spiders_connection():
    """连接到原始的 spiders 数据库"""
    try:
        return pymysql.connect(
            host=st.secrets["db_host"],
            port=st.secrets["db_port"],
            user=st.secrets["db_user"],
            password=st.secrets["db_password"],
            db=st.secrets["db_name"],
            charset='utf8mb4',
            ssl={'ssl': {}}
        )
    except Exception as e:
        st.error(f"数据库 'spiders' 连接失败: {e}")
        return None

def get_ly_card_connection():
    """连接到新的 ly_card 数据库"""
    try:
        return pymysql.connect(
            host=st.secrets["ly_card_db_host"],
            port=st.secrets["ly_card_db_port"],
            user=st.secrets["ly_card_db_user"],
            password=st.secrets["ly_card_db_password"],
            db=st.secrets["ly_card_db_name"],
            charset='utf8mb4',
            ssl={'ssl': {}}
        )
    except Exception as e:
        st.error(f"数据库 'ly_card' 连接失败: {e}")
        return None

# ================= 4. 数据查询逻辑 =================
@st.cache_data(ttl=600)
def fetch_categories():
    """获取所有非空的商品分类列表（从两个数据库合并）"""
    all_categories = set()

    # 从 spiders 获取
    conn_spiders = get_spiders_connection()
    if conn_spiders:
        try:
            df_spiders = pd.read_sql("SELECT DISTINCT category_path FROM products WHERE category_path IS NOT NULL AND category_path != ''", conn_spiders)
            all_categories.update(df_spiders['category_path'].tolist())
        except Exception as e:
            st.warning(f"获取 'spiders' 分类失败: {e}")
        finally:
            conn_spiders.close()

    # 从 ly_card 获取
    conn_ly = get_ly_card_connection()
    if conn_ly:
        try:
            df_ly = pd.read_sql("SELECT DISTINCT category_path FROM products WHERE category_path IS NOT NULL AND category_path != ''", conn_ly)
            all_categories.update(df_ly['category_path'].tolist())
        except Exception as e:
            st.warning(f"获取 'ly_card' 分类失败: {e}")
        finally:
            conn_ly.close()

    return sorted(list(all_categories))


def fetch_data_from_db(conn, db_name, keyword=None, category=None):
    """从单个数据库获取数据的通用函数"""
    if not conn:
        return pd.DataFrame()

    table_name = "products"
    select_cols = "goods_id, goods_name, goods_price, category_path, updated_at"


    try:
        if keyword:
            search_terms = {keyword}
            if keyword in SYNONYM_MAP:
                search_terms.add(SYNONYM_MAP[keyword])
            for k, v in SYNONYM_MAP.items():
                if keyword == v:
                    search_terms.add(k)
            
            where_clauses = []
            params = []
            for term in search_terms:
                where_clauses.append("goods_name LIKE %s")
                params.append(f'%{term}%')
                where_clauses.append("category_path LIKE %s")
                params.append(f'%{term}%')
            
            sql_where_clause = " OR ".join(where_clauses)
            sql = f"SELECT {select_cols} FROM {table_name} WHERE {sql_where_clause} ORDER BY goods_price ASC LIMIT 100"
            params = tuple(params)

        elif category:
            sql = f"SELECT {select_cols} FROM {table_name} WHERE category_path = %s ORDER BY updated_at DESC"
            params = (category,)
        else:
            sql = f"SELECT {select_cols} FROM {table_name} ORDER BY RAND() LIMIT 30"
            params = ()

        df = pd.read_sql(sql, conn, params=params)

        return df

    except Exception as e:
        st.warning(f"在 '{db_name}' 数据库查询出错: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def fetch_data(keyword=None, category=None):
    """从两个数据库获取并合并数据"""
    # 从 spiders 获取数据
    conn_spiders = get_spiders_connection()
    df_spiders = fetch_data_from_db(conn_spiders, "spiders", keyword, category)
    if not df_spiders.empty:
        df_spiders['source'] = 'spiders' # 添加来源标识

    # 从 ly_card 获取数据
    conn_ly = get_ly_card_connection()
    df_ly = fetch_data_from_db(conn_ly, "ly_card", keyword, category)
    if not df_ly.empty:
        df_ly['source'] = 'ly_card' # 添加来源标识

    # 合并两个 DataFrame
    combined_df = pd.concat([df_spiders, df_ly], ignore_index=True)

    if not combined_df.empty:
        # --- 核心修正：根据来源生成不同的 URL ---
        def generate_url(row):
            if row['source'] == 'spiders':
                return f"https://xinqidianqy.cn/goods?id={row['goods_id']}"
            elif row['source'] == 'ly_card':
                return f"https://ly6.sk678.cn/goods/{row['goods_id']}"
            return "" # 默认返回空字符串

        combined_df['url'] = combined_df.apply(generate_url, axis=1)
        
        # 根据不同模式进行最终排序
        if keyword:
            combined_df = combined_df.sort_values(by="goods_price", ascending=True).head(100)
        elif category:
            combined_df = combined_df.sort_values(by="updated_at", ascending=False)
        else: # 默认随机
            combined_df = combined_df.sample(frac=1).reset_index(drop=True).head(30)

    return combined_df


# ================= 5. 左侧栏 =================
with st.sidebar:
    st.markdown("<div style='text-align: center; font-size: 28px;'>🧑‍🎓开发者</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>陈文涛</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>信安2班 3123004477</p>", unsafe_allow_html=True)
    # st.markdown("<p style='text-align: center; color: gray;'>开发者</p>", unsafe_allow_html=True)
    st.info("💡 **操作提示**：在左上方可以切换 商品搜索/实时调价 页面。")
    st.divider()

    # 新增：分类浏览功能
    st.markdown("#### 📂 按分类浏览")
    categories = fetch_categories()
    selected_category = st.selectbox(
        "选择一个商品分类",
        options=[""] + categories,
        format_func=lambda x: "— 显示所有分类 —" if x == "" else x,
        label_visibility="collapsed"
    )
    st.divider()

    st.markdown("#### 🛠️ 技术栈")
    st.caption("Python • Scrapy • mysql • Streamlit")
    st.markdown("#### 📧 联系方式")
    st.caption("3357185099@qq.com")
    st.divider()

    if st.button("🔄 强制刷新数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ================= 6. 主界面布局 =================

# --- 顶部搜索区域 ---
search_query = st.text_input(
    "🔍",
    placeholder="输入“会员”或“账号”试试...",
    label_visibility="collapsed"
)

# --- 动态内容展示区域 ---
# 定义可复用的表格列配置
column_cfg = {
    "goods_name": "商品名称",
    "url": st.column_config.LinkColumn("购买链接",display_text="🔗 直达链接"),
    "goods_price": st.column_config.NumberColumn("售价", format="¥ %.2f"),
    "min_level_price": st.column_config.NumberColumn("会员价（需购买会员）", format="¥ %.2f"),
    "category_path": "所属分类",
    "updated_at": st.column_config.DatetimeColumn("更新时间", format="MM-DD HH:mm"),
}

# 定义列的显示顺序
column_order = ("goods_name", "url", "goods_price", "min_level_price", "category_path", "updated_at")


if search_query:
    # === 场景 A：用户正在搜索 (最高优先级) ===
    with st.spinner(f"正在检索 '{search_query}' ..."):
        df = fetch_data(keyword=search_query)

    st.markdown(f"### 🎯 搜索结果：'{search_query}'")
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        lowest_price_item = df.loc[df['goods_price'].idxmin()]
        col1.metric("找到相关商品", f"{len(df)} 个")
        col2.metric("最低售价", f"¥ {df['goods_price'].min():.2f}")
        with col3:
            st.markdown('<p class="custom-metric-label">最低价商品</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="custom-metric-value">{lowest_price_item["goods_name"]}</p>', unsafe_allow_html=True)

        st.dataframe(df, use_container_width=True, hide_index=True, column_config=column_cfg, column_order=column_order)
    else:
        st.warning(f"🤷‍♂️ 未找到与 “{search_query}” 相关的商品。")

elif selected_category:
    # === 场景 B：用户按分类浏览 ===
    st.markdown(f"## 📂 分类浏览：{selected_category}")
    st.divider()
    df = fetch_data(category=selected_category)
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True, column_config=column_cfg, column_order=column_order)
    else:
        st.warning("该分类下暂无商品。")

else:
    # === 场景 C：默认主页 ===
    st.markdown("## 商品比价系统")
    st.divider()
    st.info("💡 **操作提示**：在上方搜索，或从左侧栏选择分类进行浏览。")
    st.subheader("🎲 随机推荐 (30条)")
    df = fetch_data()
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True, column_config=column_cfg, column_order=column_order)
    else:
        st.warning("暂无数据，请检查爬虫状态。")

# 页脚
st.markdown("---")
st.caption("© 2025 Price Monitor System | Powered by TiDB Serverless")