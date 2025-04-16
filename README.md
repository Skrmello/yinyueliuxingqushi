# Billboard Hot 100 音乐流行趋势分析系统

这是一个基于Python的Billboard Hot 100音乐榜单数据分析系统，包含数据爬取、数据库存储和可视化分析功能。

## 功能特点

1. 数据爬取
   - 支持指定时间范围爬取Billboard Hot 100榜单数据
   - 自动处理网页请求和解析
   - 支持断点续传和错误重试

2. 数据存储
   - 使用MySQL数据库存储榜单数据
   - 支持歌曲、艺术家和排名信息的关联存储
   - 自动处理数据清洗和导入

3. 数据可视化
   - 每年歌曲数量统计
   - 上榜次数最多的艺术家分析
   - 歌曲在榜时长分布
   - 最高排名分布分析
   - 季节性趋势分析
   - 排名波动性分析
   - 歌手影响力热力图
   - 歌名关键词词云图
   - 支持精确查询歌手或歌曲的排名趋势

## 系统要求

- Python 3.7+
- MySQL数据库
- Windows/Linux/MacOS

## 依赖包

```
PyQt5
matplotlib
pandas
pymysql
beautifulsoup4
requests
wordcloud
seaborn
```

## 安装步骤

1. 克隆或下载项目文件

2. 安装依赖包：
```bash
pip install PyQt5 matplotlib pandas pymysql beautifulsoup4 requests wordcloud seaborn
```

3. 配置MySQL数据库：
   - 创建数据库：data
   - 用户名：root
   - 密码：123456
   - 端口：3306

4. 创建必要的数据表（程序会自动创建）：
   - Songs：歌曲信息表
   - Artists：艺术家信息表
   - Charts：排名信息表
   - Song_Artists：歌曲-艺术家关联表

## 使用说明

1. 启动程序：
```bash
python main_gui.py
```

2. 数据爬取：
   - 选择开始日期和结束日期
   - 点击"开始爬取"按钮
   - 等待数据爬取和导入完成

3. 数据可视化：
   - 点击相应的可视化按钮查看不同维度的分析图表
   - 使用搜索框输入歌手或歌名进行精确查询
   - 生成的图表将显示在界面下方

## 文件说明

- `main_gui.py`：主程序界面，整合所有功能
- `pachong.py`：数据爬取模块
- `dada.py`：数据库处理模块
- `keshihua.py`：数据可视化模块

## 注意事项

1. 确保MySQL数据库已正确配置并运行
2. 首次运行时需要等待数据爬取和导入
3. 数据爬取过程中请保持网络连接
4. 图表生成可能需要一定时间，请耐心等待
5. 所有生成的图表将保存在charts目录下

## 错误处理

1. 数据库连接错误：
   - 检查MySQL服务是否运行
   - 验证数据库配置信息是否正确

2. 爬取失败：
   - 检查网络连接
   - 查看是否被目标网站限制访问

3. 图表生成失败：
   - 确保数据库中有足够的数据
   - 检查charts目录是否有写入权限

## 更新日志

### 版本 1.0
- 实现基本的数据爬取功能
- 完成数据库存储模块
- 添加多种可视化分析功能
- 支持精确查询功能
- 提供图形用户界面

## 贡献者

- yukijudai#Neiji
