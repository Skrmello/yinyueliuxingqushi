import pandas as pd
import pymysql
import re
import numpy as np

# 连接数据库
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='123456',
    database='data',
    charset='utf8mb3'
)
cursor = conn.cursor()

# 创建 Songs 表（如果不存在）
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Songs (
        song_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        peak_pos INT
    );
""")

# 创建 Artists 表（如果不存在）
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Artists (
        artist_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255)
    );
""")

# 创建 Charts 表（如果不存在）
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Charts (
        chart_id INT AUTO_INCREMENT PRIMARY KEY,
        song_id INT,
        `rank` INT,
        last_week INT,
        weeks_on_chart INT,
        chart_date DATE,
        year INT,
        week INT,
        FOREIGN KEY (song_id) REFERENCES Songs(song_id)
    );
""")

# 清空表数据（如果需要每次清空）
cursor.execute("DELETE FROM Charts")
cursor.execute("DELETE FROM Songs")
cursor.execute("DELETE FROM Artists")
cursor.execute("DELETE FROM Song_Artists")
conn.commit()
print("已清空表数据")

# 读取 CSV 文件
csv_path = r"C:\\Users\\Administrator\\Desktop\\tet\\dataall.csv"
df = pd.read_csv(csv_path)

# 将 NaN 和 '-' 替换为 None
df['peak_pos'] = df['peak_pos'].replace({np.nan: None, '-': None})
df['last_week'] = df['last_week'].replace({np.nan: None, '-': None})
df['weeks_on_chart'] = df['weeks_on_chart'].replace({np.nan: None, '-': None})
df['chart_date'] = pd.to_datetime(df['chart_date'], errors='coerce')  # 转换日期格式，无法转换的会变成 NaT (Not a Time)

# 插入 Songs 和 Charts 表
for _, row in df.iterrows():
    name = row['name']
    peak_pos = row['peak_pos']

    # 插入 Songs 表
    cursor.execute("INSERT IGNORE INTO Songs (name, peak_pos) VALUES (%s, %s)", (name, peak_pos))
    conn.commit()

    # 获取 song_id
    cursor.execute("SELECT song_id FROM Songs WHERE name = %s", (name,))
    song_id = cursor.fetchone()[0]

    # 插入 Charts 表
    try:
        cursor.execute("""
            INSERT INTO Charts (song_id, `rank`, last_week, weeks_on_chart, chart_date, year, week)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            song_id,
            row['rank'],
            row['last_week'],
            row['weeks_on_chart'],
            row['chart_date'],
            row['year'],
            row['week']
        ))
        conn.commit()
    except Exception as e:
        print(f"插入 Charts 表失败: {e}")

    # 清洗并插入歌手
    singers_raw = str(row['singer'])
    if singers_raw.lower() in ['n/a', '-', 'nan']:
        continue

    cleaned = re.sub(r'\b(Featuring|feat\.?|Ft\.?)\b', '&', singers_raw, flags=re.IGNORECASE)
    artists = re.split(r'&|,|/| and ', cleaned)

    for artist in artists:
        artist = artist.strip()
        if artist == '':
            continue

        # 插入 Artists 表
        cursor.execute("INSERT IGNORE INTO Artists (name) VALUES (%s)", (artist,))
        conn.commit()

        # 获取 artist_id
        cursor.execute("SELECT artist_id FROM Artists WHERE name = %s", (artist,))
        artist_id = cursor.fetchone()[0]

        # 插入 Song_Artists 表
        cursor.execute("INSERT IGNORE INTO Song_Artists (song_id, artist_id) VALUES (%s, %s)", (song_id, artist_id))
        conn.commit()

# 关闭连接
cursor.close()
conn.close()
print("数据导入完成！")
