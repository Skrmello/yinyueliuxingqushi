import requests  # 导入requests库，用于发送HTTP请求
from bs4 import BeautifulSoup  # 导入BeautifulSoup库，用于解析HTML
import csv  # 导入csv库，用于处理CSV文件
import certifi  # 导入certifi库，用于SSL证书验证
import time  # 导入time库，用于添加延时
import os  # 导入os库，用于文件和目录操作
import datetime  # 导入datetime库，用于日期处理
from datetime import timedelta  # 导入timedelta，用于日期计算
from requests.adapters import HTTPAdapter  # 导入HTTPAdapter，用于配置HTTP请求的重试机制
from urllib3.util.retry import Retry  # 导入Retry，用于定义重试策略
import pandas as pd  # 导入pandas库，用于数据分析

# 配置参数
URL_BASE = 'https://www.billboard.com/charts/hot-100/'  # Billboard Hot 100榜单的基础URL
HEADERS = {  # 请求头信息，模拟浏览器访问
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.billboard.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Connection': 'keep-alive'
}
RETRY_STRATEGY = Retry(  # 定义HTTP请求的重试策略
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
CSV_OUTPUT_DIR = r'C:\Users\Administrator\Desktop\tet'  # CSV输出目录路径
CSV_ALL_DATA_PATH = os.path.join(CSV_OUTPUT_DIR, 'dataall.csv')  # 所有数据的CSV文件路径


def get_ssl_session():
    """创建带重试机制的Session"""
    session = requests.Session()  # 创建一个会话对象
    adapter = HTTPAdapter(max_retries=RETRY_STRATEGY)  # 创建一个HTTP适配器，配置重试策略
    session.mount("https://", adapter)  # 将适配器应用于HTTPS请求
    session.mount("http://", adapter)  # 将适配器应用于HTTP请求
    return session  # 返回配置好的会话对象


def extract_song_info(soup, rank, chart_date, year_week):
    """
    直接从页面HTML提取特定排名的歌曲信息
    专门处理Billboard的复杂HTML结构
    """
    try:
        # 获取年份和周数信息
        year, week_num = year_week  # 解包年份和周数

        # 查找所有歌曲行 - 每个排名对应一个o-chart-results-list-row元素
        all_song_rows = soup.select('ul.o-chart-results-list-row')  # 使用CSS选择器获取所有歌曲行

        # 如果找不到足够的行，返回占位数据
        if len(all_song_rows) < rank:  # 检查是否有足够的行
            return {  # 返回占位数据
                'rank': rank,  # 排名
                'name': f"Missing_Song_{rank}",  # 歌曲名称
                'singer': "Data not available",  # 歌手
                'last_week': 'N/A',  # 上周排名
                'peak_pos': 'N/A',  # 最高排名
                'weeks_on_chart': '0',  # 在榜周数
                'chart_date': chart_date,  # 榜单日期
                'year': year,  # 年份
                'week': week_num  # 周数
            }

        # 获取对应排名的行 (0-indexed所以要减1)
        row = all_song_rows[rank - 1]  # 获取特定排名的行

        # 找到显示的排名数字 (第一个带数字的标签，通常是黑色背景)
        rank_span = None  # 初始化排名元素变量
        for span in row.select('.o-chart-results-list__item .c-label'):  # 遍历所有可能的标签
            text = span.get_text(strip=True)  # 获取文本内容并去除空白
            if text.isdigit():  # 检查是否是数字
                rank_span = span  # 如果是数字，则找到了排名元素
                break  # 跳出循环
        displayed_rank = rank_span.get_text(strip=True) if rank_span else str(rank)  # 获取显示的排名

        # 提取歌曲标题
        title_elem = row.select_one('h3#title-of-a-story')  # 使用CSS选择器找到标题元素
        name = title_elem.get_text(strip=True) if title_elem else f"Unknown_Song_{rank}"  # 获取标题文本，如果找不到则使用默认值

        # 提取艺术家 - 尝试多种选择器
        # 1. 先找class中包含a-no-trucate的span
        artist_spans = [span for span in row.select('span.c-label')  # 使用列表推导式找到所有艺术家元素
                        if 'a-no-trucate' in span.get('class', [])]  # 检查class属性
        # 2. 如果没找到，尝试通过位置关系
        if artist_spans:  # 如果找到了艺术家元素
            artist_span = artist_spans[0]  # 使用第一个元素
        else:  # 如果没找到
            artist_span = row.select_one('h3#title-of-a-story + span.c-label')  # 尝试使用相邻选择器

        singer = artist_span.get_text(strip=True) if artist_span else "Unknown Artist"  # 获取艺术家文本，如果找不到则使用默认值

        # 找到所有包含数据的元素 - 移除排名和艺术家元素后的数字元素
        data_spans = []  # 初始化数据元素列表
        for li in row.select('li.o-chart-results-list__item'):  # 遍历所有列表项
            for span in li.select('span.c-label'):  # 遍历所有标签
                text = span.get_text(strip=True)  # 获取文本内容并去除空白
                # 排除已知的非统计数据元素
                if text != displayed_rank and span != artist_span:  # 检查是否是排名或艺术家元素
                    data_spans.append(span)  # 如果不是，则添加到数据元素列表

        # 初始化默认值
        last_week = 'N/A'  # 上周排名默认值
        peak_pos = 'N/A'  # 最高排名默认值
        weeks_on_chart = '0'  # 在榜周数默认值

        # 解析所有找到的span元素，提取数字值
        numeric_data = []  # 初始化数字数据列表
        for span in data_spans:  # 遍历所有数据元素
            text = span.get_text(strip=True)  # 获取文本内容并去除空白
            # 只保留数字或破折号的文本
            if text and (text.isdigit() or text == '-'):  # 检查是否是数字或破折号
                numeric_data.append(text)  # 如果是，则添加到数字数据列表

        # Billboard通常按特定顺序显示数据：上周排名、最高排名、在榜周数
        if len(numeric_data) >= 1:  # 检查是否有上周排名数据
            last_week = numeric_data[0]  # 设置上周排名
        if len(numeric_data) >= 2:  # 检查是否有最高排名数据
            peak_pos = numeric_data[1]  # 设置最高排名
        if len(numeric_data) >= 3:  # 检查是否有在榜周数数据
            weeks_on_chart = numeric_data[2]  # 设置在榜周数

        return {  # 返回歌曲信息字典
            'rank': rank,  # 排名
            'name': name,  # 歌曲名称
            'singer': singer,  # 歌手
            'last_week': last_week,  # 上周排名
            'peak_pos': peak_pos,  # 最高排名
            'weeks_on_chart': weeks_on_chart,  # 在榜周数
            'chart_date': chart_date,  # 榜单日期
            'year': year,  # 年份
            'week': week_num  # 周数
        }
    except Exception as e:  # 捕获所有异常
        # 出错时返回占位数据
        return {  # 返回错误占位数据
            'rank': rank,  # 排名
            'name': f"Error_Song_{rank}",  # 错误歌曲名称
            'singer': f"Error: {str(e)[:50]}",  # 错误歌手
            'last_week': 'N/A',  # 上周排名
            'peak_pos': 'N/A',  # 最高排名
            'weeks_on_chart': '0',  # 在榜周数
            'chart_date': chart_date,  # 榜单日期
            'year': year,  # 年份
            'week': week_num  # 周数
        }


def get_saturday_dates(start_date_str, end_date_str):
    """生成从起始日期到结束日期之间的所有星期六日期"""
    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')  # 将起始日期字符串转换为日期对象
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')  # 将结束日期字符串转换为日期对象

    # 调整到最近的星期六（如果start_date本身不是星期六）
    days_until_saturday = (5 - start_date.weekday()) % 7  # 计算到下一个星期六的天数
    if days_until_saturday > 0:  # 如果当前日期不是星期六
        start_date += datetime.timedelta(days=days_until_saturday)  # 调整到下一个星期六

    # 生成所有星期六的日期
    saturdays = []  # 存储所有星期六日期的列表
    current_date = start_date  # 从第一个星期六开始
    while current_date <= end_date:  # 当当前日期不超过结束日期时继续循环
        saturdays.append(current_date.strftime('%Y-%m-%d'))  # 添加格式化的日期字符串
        current_date += datetime.timedelta(days=7)  # 增加7天到下一个星期六

    return saturdays  # 返回所有星期六的日期列表


def get_year_week(date_str):
    """根据日期获取年份和周数"""
    date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')  # 将日期字符串转换为日期对象
    year = date_obj.year  # 获取年份
    week_num = date_obj.isocalendar()[1]  # 获取ISO周数
    return year, week_num  # 返回年份和周数的元组


def scrape_chart_for_date(date_str):
    """抓取特定日期的Billboard Hot 100榜单"""
    session = get_ssl_session()  # 获取配置好的会话
    url = URL_BASE + date_str  # 构建完整URL

    print(f"正在获取 {date_str} 的Billboard Hot 100数据...")  # 打印当前正在获取的日期

    try:
        # 发送HTTP请求获取页面内容
        response = session.get(
            url,
            headers=HEADERS,
            verify=certifi.where(),  # 使用certifi提供的证书
            timeout=20  # 设置20秒超时
        )
        response.raise_for_status()  # 检查是否有HTTP错误

        # 验证页面内容是否正确
        if "Hot 100" not in response.text:
            print(f"警告：{date_str} 可能无法获取到正确的Hot 100页面")
            year_week = get_year_week(date_str)  # 获取年份和周数
            # 创建100个占位条目并返回
            return [
                {
                    'rank': rank,
                    'name': f"PageError_{rank}",
                    'singer': "Page not available",
                    'last_week': 'N/A',
                    'peak_pos': 'N/A',
                    'weeks_on_chart': '0',
                    'chart_date': date_str,
                    'year': year_week[0],
                    'week': year_week[1]
                }
                for rank in range(1, 101)
            ]

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # 计算年份和周数
        year_week = get_year_week(date_str)

        # 直接从HTML提取每首歌曲的信息
        songs = []
        success_count = 0
        error_count = 0

        for rank in range(1, 101):  # 处理所有100个排名
            song_data = extract_song_info(soup, rank, date_str, year_week)
            songs.append(song_data)

            # 检查是否成功解析
            if "Error_" in song_data['name'] or "Missing_" in song_data['name']:
                error_count += 1
                print(f"[{date_str}] #{rank:3d} 解析失败: {song_data['name']} - {song_data['singer']}")
            else:
                success_count += 1

        print(f"{date_str} 统计: 成功 {success_count} 首, 失败 {error_count} 首")
        return songs

    except Exception as e:
        print(f"抓取 {date_str} 时出错: {str(e)}")
        year_week = get_year_week(date_str)
        # 返回100个错误占位条目
        return [
            {
                'rank': rank,
                'name': f"Error_{rank}",
                'singer': f"Error: {str(e)[:30]}...",
                'last_week': 'N/A',
                'peak_pos': 'N/A',
                'weeks_on_chart': '0',
                'chart_date': date_str,
                'year': year_week[0],
                'week': year_week[1]
            }
            for rank in range(1, 101)
        ]


def save_to_csv(data, filepath, fieldnames=None):
    """将数据保存到CSV文件"""
    # 确保目录存在
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # 如果未提供列名，从第一个数据项中提取
    if fieldnames is None and data:
        fieldnames = data[0].keys()

    # 写入CSV文件
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()  # 写入表头
        writer.writerows(data)  # 写入所有数据行

    print(f"成功保存 {len(data)} 条数据到 {filepath}")


def main():
    start_date = "2015-01-01"  # 起始日期
    end_date = "2025-01-01"  # 结束日期

    # 确保输出目录存在
    os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)

    # 获取所有需要爬取的星期六日期
    saturday_dates = get_saturday_dates(start_date, end_date)
    print(f"将爬取 {len(saturday_dates)} 个星期六的Billboard Hot 100榜单")

    # 保存所有歌曲的列表
    all_songs = []

    # 定义CSV字段名
    fieldnames = ['rank', 'name', 'singer', 'last_week', 'peak_pos', 'weeks_on_chart', 'chart_date', 'year', 'week']

    # 对每个日期进行爬取
    for date_str in saturday_dates:
        songs = scrape_chart_for_date(date_str)  # 爬取当前日期的数据
        all_songs.extend(songs)  # 将当前日期的数据添加到总列表

        # 每爬取一个日期后休息一下，避免被封
        time.sleep(2)

        # 每爬取10个日期（1000首歌曲）保存一次数据块文件
        if len(all_songs) % 1000 == 0:
            chunk_num = len(all_songs) // 1000
            print(f"保存第{chunk_num}千条数据，当前已处理 {len(all_songs) // 100} 个星期六...")

            chunk_path = os.path.join(CSV_OUTPUT_DIR, f'data{chunk_num}k.csv')
            save_to_csv(all_songs[-1000:], chunk_path, fieldnames)
            print(f"数据块{chunk_num}已保存到 {chunk_path}")

    # 保存所有数据到最终dataall.csv文件
    if all_songs:
        save_to_csv(all_songs, CSV_ALL_DATA_PATH, fieldnames)
        print(f"所有数据已保存到 {CSV_ALL_DATA_PATH}")
    else:
        print("未能获取任何数据")


if __name__ == "__main__":
    main()