import streamlit as st
import pandas as pd
import datetime
import re
from pathlib import Path

# ページ設定
st.set_page_config(
    page_title="日大一メルマガアーカイブ - 2025年4月限定公開",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        color: white;
        padding: 2rem 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .search-container {
        background: #f0f9ff;
        border: 2px solid #3b82f6;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .search-result {
        background: #fef9e7;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    .theme-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .theme-card:hover {
        background: #e2e8f0;
        border-color: #3b82f6;
    }
    .article-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .date-badge {
        background: #3b82f6;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        display: inline-block;
        margin-bottom: 1rem;
    }
    .theme-badge {
        background: #10b981;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 15px;
        font-size: 0.8rem;
        display: inline-block;
        margin-left: 0.5rem;
    }
    .highlight {
        background: #fef3c7;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-weight: bold;
    }
    .content-text {
        line-height: 1.8;
        font-size: 1rem;
        white-space: pre-wrap;
        background: #f9fafb;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
    }
    .sidebar-info {
        background: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .popular-keywords {
        background: #f0f9ff;
        border: 1px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .keyword-tag {
        background: #dbeafe;
        color: #1e40af;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .keyword-tag:hover {
        background: #3b82f6;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_newsletter_data():
    """メルマガデータを読み込む"""
    try:
        # データフォルダからExcelファイルを読み込み
        data_path = Path("data/newsletter_review.xlsx")
        df = pd.read_excel(data_path)
        
        # データを整理
        df.columns = ['月', '日', '曜日', 'タイトル', '本文']
        df = df.dropna()
        
        # 日付文字列を作成
        df['日付表示'] = df.apply(lambda row: f"{int(row['月'])}月{int(row['日'])}日 ({row['曜日']})", axis=1)
        
        return df
    except Exception as e:
        st.error(f"データファイルの読み込みに失敗しました: {e}")
        return pd.DataFrame()

def extract_school_guide_content(content):
    """本文から「今日の学校案内」セクションを抽出"""
    match = re.search(r'今日の学校案内（(.+?)）\s*-----\s*(.*?)\s*-----', content, re.DOTALL)
    if match:
        theme_info = match.group(1)
        guide_content = match.group(2).replace('\\r\\n', '\n').strip()
        return theme_info, guide_content
    return None, None

def get_theme_from_content(content):
    """本文からテーマを抽出"""
    match = re.search(r'今日の学校案内（.+?のテーマ：(.+?)）', content)
    if match:
        return match.group(1)
    return "その他"

def search_in_guide_content(df, search_query):
    """「今日の学校案内」セクション内で検索"""
    if not search_query:
        return pd.DataFrame()
    
    search_results = []
    
    for _, row in df.iterrows():
        theme_info, guide_content = extract_school_guide_content(row['本文'])
        if guide_content:
            # 大文字小文字を区別しない検索
            if search_query.lower() in guide_content.lower():
                # 検索キーワードをハイライト
                highlighted_content = highlight_keywords(guide_content, search_query)
                
                search_results.append({
                    '月': row['月'],
                    '日': row['日'],
                    '曜日': row['曜日'],
                    'タイトル': row['タイトル'],
                    '本文': row['本文'],
                    '日付表示': row['日付表示'],
                    'テーマ情報': theme_info,
                    '学校案内内容': guide_content,
                    'ハイライト内容': highlighted_content
                })
    
    return pd.DataFrame(search_results)

def highlight_keywords(text, keyword):
    """テキスト内のキーワードをハイライト"""
    if not keyword:
        return text
    
    # 大文字小文字を区別しない置換
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    highlighted = pattern.sub(lambda m: f'<span class="highlight">{m.group()}</span>', text)
    return highlighted

def extract_popular_keywords(df):
    """人気キーワードを抽出"""
    all_content = ""
    for _, row in df.iterrows():
        theme_info, guide_content = extract_school_guide_content(row['本文'])
        if guide_content:
            all_content += guide_content + " "
    
    # 主要なキーワードを手動で定義（実際の学校情報に基づく）
    popular_keywords = [
        "入試", "進路", "学校行事", "英検", "合唱祭", "文化祭", "体育祭",
        "日本大学", "付属推薦", "研修旅行", "語学研修", "オーストラリア",
        "中学1年", "中学2年", "中学3年", "高校1年", "高校2年", "高校3年",
        "保護者会", "基礎学力", "生活習慣", "6年間", "一貫教育",
        "両国駅", "墨田区", "通学時間", "駅近", "アクセス",
        "青木校長", "先生", "生徒", "教育", "成長", "将来"
    ]
    
    return popular_keywords

def main():
    # ヘッダー
    st.markdown("""
    <div class="main-header">
        <h1>📧 日本大学第一中学・高等学校</h1>
        <h2>メルマガ『一日一知』アーカイブ</h2>
        <p><strong>2025年4月分 期間限定公開</strong></p>
        <p>毎日配信している学校案内メールマガジンを、テーマ別にご覧いただけます</p>
    </div>
    """, unsafe_allow_html=True)
    
    # データ読み込み
    df = load_newsletter_data()
    
    if df.empty:
        st.error("データが読み込めませんでした。dataフォルダにnewsletter_review.xlsxファイルがあることを確認してください。")
        return
    
    # テーママッピング
    theme_mapping = {
        '月': '日大一の地理情報',
        '火': '日大一の6年間', 
        '水': '日大一の進路',
        '木': '学校行事',
        '金': '日大一の入試',
        '土': '日大一ストーリー'
    }
    
    # テーマ別にデータを整理
    df['テーマ'] = df['曜日'].str[0].map(theme_mapping)
    
    # 検索セクション
    st.markdown("""
    <div class="search-container">
        <h3>🔍 学校案内内容を検索</h3>
        <p>各記事の「今日の学校案内」セクションから知りたい情報を検索できます</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 検索機能
    col_search1, col_search2 = st.columns([3, 1])
    
    with col_search1:
        search_query = st.text_input(
            "検索キーワードを入力してください",
            placeholder="例：入試、進路、英検、文化祭、日本大学など...",
            help="「今日の学校案内」セクションの内容から検索します"
        )
    
    with col_search2:
        search_button = st.button("🔍 検索", type="primary")
    
    # 人気キーワード表示
    popular_keywords = extract_popular_keywords(df)
    st.markdown("""
    <div class="popular-keywords">
        <h4>💡 人気の検索キーワード</h4>
        <p>クリックすると自動で検索されます</p>
    </div>
    """, unsafe_allow_html=True)
    
    # キーワードタグをクリック可能にする
    keyword_cols = st.columns(6)
    for i, keyword in enumerate(popular_keywords[:18]):  # 最初の18個を表示
        col_idx = i % 6
        with keyword_cols[col_idx]:
            if st.button(keyword, key=f"keyword_{i}", help=f"「{keyword}」で検索"):
                search_query = keyword
                search_button = True
    
    # サイドバー
    with st.sidebar:
        st.markdown("### 📚 テーマ別メニュー")
        
        st.markdown("""
        <div class="sidebar-info">
            <strong>🎯 曜日別テーマ</strong><br>
            各曜日で異なるテーマの学校情報をお届けしています
        </div>
        """, unsafe_allow_html=True)
        
        # テーマ選択
        selected_theme = st.selectbox(
            "見たいテーマを選択してください",
            options=['すべて'] + list(theme_mapping.values()),
            index=0
        )
        
        # 統計情報
        st.markdown("### 📊 配信統計")
        st.metric("総配信数", len(df))
        st.metric("配信期間", "2025年4月")
        
        # 検索結果統計
        if search_query and search_button:
            search_results = search_in_guide_content(df, search_query)
            st.metric("検索結果", f"{len(search_results)}件")
        
        # テーマ別記事数
        theme_counts = df['テーマ'].value_counts()
        st.markdown("### 📈 テーマ別記事数")
        for theme, count in theme_counts.items():
            st.write(f"**{theme}**: {count}件")
    
    # 検索結果表示
    if search_query and search_button:
        search_results = search_in_guide_content(df, search_query)
        
        if len(search_results) > 0:
            st.markdown(f"### 🎯 「{search_query}」の検索結果 ({len(search_results)}件)")
            
            for _, result in search_results.iterrows():
                st.markdown(f"""
                <div class="search-result">
                    <strong>📅 {result['日付表示']}</strong> - 
                    <strong>{result['テーマ情報']}</strong>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"📖 {result['日付表示']} の学校案内内容", expanded=False):
                    st.markdown(f"""
                    <div class="content-text">{result['ハイライト内容']}</div>
                    """, unsafe_allow_html=True)
                    
                    # 元の記事へのリンク
                    if st.button(f"📄 完全な記事を見る", key=f"full_{result['日付表示']}"):
                        content_display = result['本文'].replace('\\r\\n', '\n').replace('\n', '<br>')
                        st.markdown(f"""
                        <div class="article-card">
                            <div class="date-badge">{result['日付表示']}</div>
                            <h4>{result['タイトル']}</h4>
                            <div class="content-text">{content_display}</div>
                        </div>
                        """, unsafe_allow_html=True)
            
        else:
            st.warning(f"「{search_query}」に関する情報が見つかりませんでした。別のキーワードをお試しください。")
    
    # メインコンテンツ（テーマ別表示）
    if not (search_query and search_button):
        # ナビゲーションボタン
        if selected_theme != 'すべて':
            col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
            with col_nav2:
                if st.button("🏠 全記事一覧に戻る", type="secondary", use_container_width=True):
                    selected_theme = 'すべて'
                    st.rerun()
        
        # メインコンテンツエリア
            # フィルタリング
            if selected_theme == 'すべて':
                filtered_df = df
                st.markdown("### 📰 全記事一覧")
            else:
                filtered_df = df[df['テーマ'] == selected_theme]
                st.markdown(f"### 📰 {selected_theme} の記事")
            
            # 記事表示
            if len(filtered_df) > 0:
                # 日付順でソート
                filtered_df = filtered_df.sort_values(['月', '日'])
                
                for _, row in filtered_df.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div class="article-card">
                            <div class="date-badge">{row['日付表示']}</div>
                            <span class="theme-badge">{row['テーマ']}</span>
                            <h3>{row['タイトル']}</h3>
                        """, unsafe_allow_html=True)
                        
                        # 今日の学校案内セクションのプレビュー
                        theme_info, guide_content = extract_school_guide_content(row['本文'])
                        if guide_content:
                            st.markdown(f"**🎯 {theme_info}**")
                            preview = guide_content[:150] + "..." if len(guide_content) > 150 else guide_content
                            st.markdown(f"*{preview}*")
                        
                        # 展開可能な本文
                        with st.expander("📖 記事を読む", expanded=False):
                            # 本文を見やすく整形
                            content = row['本文'].replace('\\r\\n', '\n')
                            content = content.replace('-----', '━━━━━━━━━━━━━━━━━━━━')
                            
                            content_html = content.replace('\n', '<br>')
                            st.markdown(f"""
                            <div class="content-text">{content_html}</div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.markdown("---")
            else:
                st.info("選択されたテーマの記事が見つかりませんでした。")
    
    # フッター
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; padding: 2rem;">
        <p><strong>日本大学第一中学・高等学校 入試広報部</strong></p>
        <p>📞 03-3625-0026 | 🌐 <a href="https://www.nichidai-1.ed.jp">公式ホームページ</a></p>
        <p><small>※このアーカイブは2025年4月分のメルマガを期間限定で公開しています</small></p>
        <p><small>メルマガへの新規登録は公式ホームページから受け付けています</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()