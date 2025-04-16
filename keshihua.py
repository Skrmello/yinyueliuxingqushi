# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.dates as mdates
import os
import warnings

# 屏蔽 seaborn 关于 palette 参数的 FutureWarning
warnings.filterwarnings("ignore", message="Passing palette without assigning hue is deprecated")

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei']  # 正常显示中文
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

# 导入 wordcloud 库（用于生成词云）
from wordcloud import WordCloud

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'test'
}

# 创建输出文件夹
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'charts')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_data_from_query(query):
    """使用 SQLAlchemy 引擎从数据库中获取数据"""
    try:
        from sqlalchemy import create_engine
        engine = create_engine(
            f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        df = pd.read_sql_query(query, engine)
        return df
    except Exception as e:
        print(f"查询执行错误: {e}")
        return None


def plot_yearly_songs_count():
    """绘制每年歌曲数量统计图"""
    query = """
    SELECT year, COUNT(DISTINCT song_id) AS song_count
    FROM chart_entries
    GROUP BY year
    ORDER BY year
    """
    df = get_data_from_query(query)
    if df is None or df.empty:
        print("无法获取年度歌曲数据")
        return
    plt.figure(figsize=(12, 7))
    # 将 'year' 同时传入 hue，并关闭 dodge 参数生成单一颜色的条形图
    bar = sns.barplot(x='year', y='song_count', data=df, hue='year', dodge=False, palette='viridis')
    if bar.get_legend() is not None:
        bar.legend_.remove()
    for i, v in enumerate(df['song_count']):
        bar.text(i, v + 10, str(v), ha='center')
    plt.title('每年Billboard Hot 100上榜歌曲数量', fontsize=16)
    plt.xlabel('年份', fontsize=14)
    plt.ylabel('歌曲数量', fontsize=14)
    plt.xticks(rotation=45)
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'yearly_songs_count.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"图表已保存至: {output_path}")


def plot_top_artists():
    """绘制上榜次数最多的艺术家统计图"""
    query = """
    SELECT a.name as artist_name, COUNT(DISTINCT ce.song_id) as song_count
    FROM artists a
    JOIN song_artists sa ON a.artist_id = sa.artist_id
    JOIN chart_entries ce ON sa.song_id = ce.song_id
    GROUP BY a.artist_id
    ORDER BY song_count DESC
    LIMIT 15
    """
    df = get_data_from_query(query)
    if df is None or df.empty:
        print("无法获取艺术家数据")
        return
    plt.figure(figsize=(14, 8))
    bars = plt.barh(df['artist_name'], df['song_count'], color=sns.color_palette("viridis", len(df)))
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.5, bar.get_y() + bar.get_height() / 2,
                 f'{width:.0f}', ha='left', va='center', fontsize=10)
    plt.title('Billboard Hot 100上榜次数最多的艺术家', fontsize=16)
    plt.xlabel('上榜歌曲数量', fontsize=14)
    plt.ylabel('艺术家', fontsize=14)
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'top_artists.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"图表已保存至: {output_path}")


def plot_songs_longevity():
    """绘制歌曲在榜时长分布图"""
    query = """
    SELECT s.name as song_name, s.singer, COUNT(ce.chart_date) as weeks_on_chart
    FROM songs s
    JOIN chart_entries ce ON s.song_id = ce.song_id
    GROUP BY s.song_id
    ORDER BY weeks_on_chart DESC
    LIMIT 20
    """
    df = get_data_from_query(query)
    if df is None or df.empty:
        print("无法获取歌曲在榜时长数据")
        return
    df['title'] = df['song_name'] + '\n' + df['singer']
    plt.figure(figsize=(14, 10))
    bars = plt.barh(df['title'], df['weeks_on_chart'], color=sns.color_palette("plasma", len(df)))
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.5, bar.get_y() + bar.get_height() / 2,
                 f'{width:.0f}周', ha='left', va='center', fontsize=9)
    plt.title('Billboard Hot 100在榜周数最长的歌曲', fontsize=16)
    plt.xlabel('在榜周数', fontsize=14)
    plt.ylabel('歌曲 (歌手)', fontsize=14)
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'songs_longevity.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"图表已保存至: {output_path}")


def plot_peak_positions_distribution():
    """绘制歌曲最高排名分布"""
    query = """
    SELECT peak_range, COUNT(song_id) as song_count FROM (
        SELECT s.song_id,
           CASE 
             WHEN MIN(ce.rank) BETWEEN 1 AND 10 THEN '1-10'
             WHEN MIN(ce.rank) BETWEEN 11 AND 20 THEN '11-20'
             WHEN MIN(ce.rank) BETWEEN 21 AND 30 THEN '21-30'
             WHEN MIN(ce.rank) BETWEEN 31 AND 40 THEN '31-40'
             WHEN MIN(ce.rank) BETWEEN 41 AND 50 THEN '41-50'
             WHEN MIN(ce.rank) BETWEEN 51 AND 60 THEN '51-60'
             WHEN MIN(ce.rank) BETWEEN 61 AND 70 THEN '61-70'
             WHEN MIN(ce.rank) BETWEEN 71 AND 80 THEN '71-80'
             WHEN MIN(ce.rank) BETWEEN 81 AND 90 THEN '81-90'
             WHEN MIN(ce.rank) BETWEEN 91 AND 100 THEN '91-100'
           END AS peak_range
        FROM songs s
        JOIN chart_entries ce ON s.song_id = ce.song_id
        GROUP BY s.song_id
    ) as sub
    GROUP BY peak_range
    ORDER BY peak_range;
    """
    df = get_data_from_query(query)
    if df is None or df.empty:
        print("无法获取最高排名分布数据")
        return
    plt.figure(figsize=(12, 8))
    bars = plt.bar(df['peak_range'], df['song_count'], color=sns.color_palette("coolwarm", len(df)))
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height + 5,
                 f'{height:.0f}', ha='center', va='bottom', fontsize=10)
    plt.title('歌曲最高排名分布', fontsize=16)
    plt.xlabel('最高排名范围', fontsize=14)
    plt.ylabel('歌曲数量', fontsize=14)
    plt.xticks(rotation=45)
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'peak_positions_distribution.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"图表已保存至: {output_path}")


def plot_artist_rank_trend(artist_name):
    """绘制指定艺术家的排名趋势图"""
    query = f"""
    SELECT ce.chart_date, CONCAT(s.name, '(', s.singer, ')') AS unique_song, ce.rank
    FROM chart_entries ce
    JOIN songs s ON ce.song_id = s.song_id
    JOIN song_artists sa ON s.song_id = sa.song_id
    JOIN artists a ON sa.artist_id = a.artist_id
    WHERE a.name = '{artist_name}'
    ORDER BY ce.chart_date, ce.rank
    """
    trend_df = get_data_from_query(query)
    if trend_df is None or trend_df.empty:
        print(f"无法获取艺术家 {artist_name} 的排名趋势数据")
        return
    top_songs_query = f"""
    SELECT CONCAT(s.name, '(', s.singer, ')') AS unique_song, MIN(ce.rank) as best_rank
    FROM songs s
    JOIN chart_entries ce ON s.song_id = ce.song_id
    JOIN song_artists sa ON s.song_id = sa.song_id
    JOIN artists a ON sa.artist_id = a.artist_id
    WHERE a.name = '{artist_name}'
    GROUP BY unique_song
    ORDER BY best_rank
    LIMIT 5
    """
    top_songs_df = get_data_from_query(top_songs_query)
    if top_songs_df is None or top_songs_df.empty:
        print(f"无法获取艺术家 {artist_name} 的热门歌曲数据")
        return
    top_songs_list = top_songs_df['unique_song'].tolist()
    filtered_df = trend_df[trend_df['unique_song'].isin(top_songs_list)]
    plt.figure(figsize=(15, 10))
    colors = sns.color_palette("husl", len(top_songs_list))
    color_map = {song: color for song, color in zip(top_songs_list, colors)}
    for song in top_songs_list:
        song_data = filtered_df[filtered_df['unique_song'] == song]
        if not song_data.empty:
            plt.plot(song_data['chart_date'], song_data['rank'], 'o-',
                     label=song, color=color_map[song], linewidth=2, markersize=5)
    plt.gca().invert_yaxis()
    plt.ylim(100, 1)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.title(f'{artist_name} 热门歌曲的Billboard排名趋势', fontsize=16)
    plt.xlabel('日期', fontsize=14)
    plt.ylabel('排名', fontsize=14)
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='upper right', fontsize=10)
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, f'{artist_name}_rank_trend.png'.replace(' ', '_'))
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"图表已保存至: {output_path}")


def plot_seasonal_trends():
    """绘制季节性趋势图：不同月份的新歌上榜数量"""
    query = """
    SELECT MONTH(chart_date) as month, COUNT(DISTINCT song_id) as new_songs
    FROM chart_entries
    WHERE last_week_rank IS NULL OR last_week_rank > 100
    GROUP BY MONTH(chart_date)
    ORDER BY month
    """
    df = get_data_from_query(query)
    if df is None or df.empty:
        print("无法获取季节性数据")
        return
    month_names = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
    full_months = pd.DataFrame({'month': range(1, 13)})
    df = pd.merge(full_months, df, on='month', how='left').fillna(0)
    df['month_name'] = df['month'].apply(lambda x: month_names[int(x) - 1])
    plt.figure(figsize=(12, 8))
    bars = plt.bar(df['month_name'], df['new_songs'], color=sns.color_palette("YlOrRd", 12))
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height + 5,
                 f'{height:.0f}', ha='center', va='bottom', fontsize=10)
    plt.title('不同月份新歌上榜数量分布', fontsize=16)
    plt.xlabel('月份', fontsize=14)
    plt.ylabel('新上榜歌曲数量', fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'seasonal_trends.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"图表已保存至: {output_path}")


def plot_rank_volatility():
    """绘制排名波动性图：统计歌曲排名上升和下降的幅度"""
    query = """
    SELECT 
        s.name as song_name,
        s.singer,
        MAX(ABS(ce.rank - ce.last_week_rank)) as max_change,
        AVG(ABS(ce.rank - ce.last_week_rank)) as avg_change
    FROM songs s
    JOIN chart_entries ce ON s.song_id = ce.song_id
    WHERE ce.last_week_rank IS NOT NULL
    GROUP BY s.song_id
    HAVING COUNT(ce.entry_id) > 5
    ORDER BY max_change DESC
    LIMIT 15
    """
    df = get_data_from_query(query)
    if df is None or df.empty:
        print("无法获取排名波动性数据")
        return
    df['title'] = df['song_name'] + '\n' + df['singer']
    plt.figure(figsize=(14, 10))
    bars = plt.barh(df['title'], df['max_change'], color=sns.color_palette("plasma", len(df)))
    for i, (_, row) in enumerate(df.iterrows()):
        plt.plot([0, row['avg_change']], [i, i], 'k--', alpha=0.6)
        plt.plot(row['avg_change'], i, 'ro', ms=7)
    for i, bar in enumerate(bars):
        width = bar.get_width()
        avg = df.iloc[i]['avg_change']
        plt.text(width + 2, bar.get_y() + bar.get_height() / 2,
                 f'最大: {width:.0f}, 平均: {avg:.1f}', ha='left', va='center', fontsize=9)
    plt.title('Billboard Hot 100排名波动性最大的歌曲', fontsize=16)
    plt.xlabel('排名变化（位）', fontsize=14)
    plt.ylabel('歌曲 (歌手)', fontsize=14)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'rank_volatility.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"图表已保存至: {output_path}")


def plot_song_artist_heatmap():
    """绘制歌名和歌手的热力图"""
    # 首先获取上榜次数最多的前15位歌手
    top_artists_query = """
    SELECT a.name as artist_name, COUNT(DISTINCT ce.song_id) as song_count
    FROM artists a
    JOIN song_artists sa ON a.artist_id = sa.artist_id
    JOIN chart_entries ce ON sa.song_id = ce.song_id
    GROUP BY a.artist_id
    ORDER BY song_count DESC
    LIMIT 15
    """
    top_artists_df = get_data_from_query(top_artists_query)
    if top_artists_df is None or top_artists_df.empty:
        print("无法获取顶级艺术家数据")
        return

    # 获取这些歌手的歌曲数据（每个歌手只取前3首最热门的歌曲）
    top_artists_list = top_artists_df['artist_name'].tolist()
    songs_query = f"""
    WITH RankedSongs AS (
        SELECT 
            s.singer,
            s.name as song_name,
            COUNT(ce.entry_id) as appearances,
            ROW_NUMBER() OVER (PARTITION BY s.singer ORDER BY COUNT(ce.entry_id) DESC) as rn
        FROM songs s
        JOIN chart_entries ce ON s.song_id = ce.song_id
        WHERE s.singer IN ({','.join([f"'{artist}'" for artist in top_artists_list])})
        GROUP BY s.singer, s.name
    )
    SELECT singer, song_name, appearances
    FROM RankedSongs
    WHERE rn <= 3
    ORDER BY singer, appearances DESC
    """
    df = get_data_from_query(songs_query)
    if df is None or df.empty:
        print("无法获取歌名和歌手的热力图数据")
        return

    # 创建歌手和歌曲的交叉表
    heatmap_data = pd.pivot_table(
        df,
        values='appearances',
        index='singer',
        columns='song_name',
        aggfunc='sum',
        fill_value=0
    )

    # 确保所有单元格都有值
    heatmap_data = heatmap_data.fillna(0)

    # 设置图表大小和样式
    plt.figure(figsize=(15, 12))

    # 创建热力图
    sns.heatmap(
        heatmap_data,
        annot=False,  # 不显示数字标注
        cmap="YlOrRd",  # 使用更鲜艳的颜色方案
        cbar_kws={'label': '上榜次数'},
        linewidths=0.5,  # 添加单元格边框
        linecolor='white',  # 边框颜色
        center=heatmap_data.values.mean()  # 设置颜色中心点
    )

    # 设置标题和标签
    plt.title("Top 15 歌手的最热门3首歌曲在榜出现次数", fontsize=16, pad=20)
    plt.xlabel("歌曲名称", fontsize=12, labelpad=10)
    plt.ylabel("歌手", fontsize=12, labelpad=10)

    # 调整x轴标签
    plt.xticks(rotation=30, ha='right')

    # 调整布局
    plt.tight_layout()

    # 保存图表
    output_path = os.path.join(OUTPUT_DIR, 'song_artist_heatmap.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"图表已保存至: {output_path}")


def plot_song_name_wordcloud():
    """绘制基于歌名数据的热词图（词云）"""
    query = "SELECT name as song_name FROM songs"
    df = get_data_from_query(query)
    if df is None or df.empty:
        print("无法获取歌名数据")
        return
    text = " ".join(df['song_name'].tolist())
    try:
        import jieba
        text = " ".join(jieba.cut(text))
    except ImportError:
        pass
    wc = WordCloud(font_path="simhei.ttf", background_color="white", width=800, height=600)
    wc.generate(text)
    plt.figure(figsize=(10, 8))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.title("基于歌名的热词图", fontsize=16)
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'song_name_wordcloud.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"图表已保存至: {output_path}")


def plot_search_trend(search_str):
    """
    根据用户输入的搜索字符串进行精确匹配，
    使用 CONCAT(s.name, '(', s.singer, ')') 生成唯一标识，
    查询热门的歌曲（取前10）并绘制这些歌曲的排名趋势图。
    """
    query = f"""
    SELECT ce.chart_date, CONCAT(s.name, '(', s.singer, ')') AS unique_song, ce.rank, ce.last_week_rank
    FROM chart_entries ce
    JOIN songs s ON ce.song_id = s.song_id
    WHERE s.singer = '{search_str}' OR s.name = '{search_str}'
    ORDER BY ce.chart_date, ce.rank
    """
    trend_df = get_data_from_query(query)
    if trend_df is None or trend_df.empty:
        print(f"未找到与 [{search_str}] 完全匹配的歌曲或歌手的排名趋势数据")
        return

    top_songs_query = f"""
    SELECT CONCAT(s.name, '(', s.singer, ')') AS unique_song, MIN(ce.rank) as best_rank
    FROM chart_entries ce
    JOIN songs s ON ce.song_id = s.song_id
    WHERE s.singer = '{search_str}' OR s.name = '{search_str}'
    GROUP BY unique_song
    ORDER BY best_rank
    LIMIT 10
    """
    top_songs_df = get_data_from_query(top_songs_query)
    if top_songs_df is None or top_songs_df.empty:
        print(f"未找到与 [{search_str}] 完全匹配的热门歌曲数据")
        return

    top_songs_list = top_songs_df['unique_song'].tolist()
    filtered_df = trend_df[trend_df['unique_song'].isin(top_songs_list)]

    plt.figure(figsize=(15, 10))
    colors = sns.color_palette("husl", len(top_songs_list))
    color_map = {song: color for song, color in zip(top_songs_list, colors)}

    for song in top_songs_list:
        song_data = filtered_df[filtered_df['unique_song'] == song].sort_values('chart_date')
        if not song_data.empty:
            # 找出连续上榜的段
            segments = []
            current_segment = []

            for idx, row in song_data.iterrows():
                if not current_segment:
                    current_segment.append((row['chart_date'], row['rank']))
                else:
                    # 检查是否连续上榜
                    if row['last_week_rank'] is not None and row['last_week_rank'] <= 100:
                        current_segment.append((row['chart_date'], row['rank']))
                    else:
                        if current_segment:
                            segments.append(current_segment)
                        current_segment = [(row['chart_date'], row['rank'])]

            if current_segment:
                segments.append(current_segment)

            # 绘制每个连续段
            for segment in segments:
                dates, ranks = zip(*segment)
                plt.plot(dates, ranks, 'o-', label=song if segment == segments[0] else None,
                         color=color_map[song], linewidth=2, markersize=5)

    plt.gca().invert_yaxis()
    plt.ylim(100, 1)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.title(f'精确匹配 [{search_str}] 的热门歌曲的Billboard排名趋势', fontsize=16)
    plt.xlabel('日期', fontsize=14)
    plt.ylabel('排名', fontsize=14)
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='upper right', fontsize=10)
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, f'{search_str}_search_trend.png'.replace(' ', '_'))
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"图表已保存至: {output_path}")


def interactive_loop():
    """
    交互模块循环：持续提示用户输入精确的歌手或歌名，
    根据输入生成排名趋势图；输入 'q' 或 'Q' 时退出循环。
    """
    while True:
        user_input = input("请输入精确的歌手或歌名（输入 'q' 退出）：").strip()
        if user_input.lower() == 'q':
            print("退出交互模块。")
            break
        if user_input:
            plot_search_trend(user_input)
        else:
            print("输入为空，请重新输入。")


def main():
    """主函数"""
    print("Billboard Hot 100数据可视化工具")
    print("=" * 40)
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"创建输出目录: {OUTPUT_DIR}")
    print("\n1. 绘制每年歌曲数量统计图")
    plot_yearly_songs_count()
    print("\n2. 绘制上榜次数最多的艺术家图")
    plot_top_artists()
    print("\n3. 绘制歌曲在榜时长分布图")
    plot_songs_longevity()
    print("\n4. 绘制歌曲最高排名分布图")
    plot_peak_positions_distribution()
    print("\n5. 绘制知名艺术家排名趋势图")
    top_artist_query = """
    SELECT a.name, COUNT(*) as appearance_count
    FROM artists a
    JOIN song_artists sa ON a.artist_id = sa.artist_id
    JOIN chart_entries ce ON sa.song_id = ce.song_id
    GROUP BY a.name
    ORDER BY appearance_count DESC
    LIMIT 1
    """
    top_artist_df = get_data_from_query(top_artist_query)
    if top_artist_df is not None and not top_artist_df.empty:
        plot_artist_rank_trend(top_artist_df.iloc[0]['name'])
    print("\n6. 绘制季节性趋势图")
    plot_seasonal_trends()
    print("\n7. 绘制排名波动性图")
    plot_rank_volatility()
    print("\n8. 绘制歌名和歌手热力图")
    plot_song_artist_heatmap()
    print("\n9. 绘制基于歌名的热词图")
    plot_song_name_wordcloud()
    print("\n10. 进入交互模块：持续输入精确的歌手或歌名生成排名趋势图")
    interactive_loop()
    print("\n所有图表生成完成，请查看 charts 目录！")


if __name__ == "__main__":
    main() 