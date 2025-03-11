import re
from bs4 import BeautifulSoup
import sqlite3

import requests

def get_html_content(url):
    """
    从指定的 URL 获取 HTML 内容。

    :param url: 网页的 URL
    :return: 网页的 HTML 内容，如果请求出错则返回 None
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response.text
    except requests.RequestException as e:
        print(f"请求网页时出错: {e}")
        return None
    
def parse_html(html_content):
    # soup = BeautifulSoup(html_content, 'html.parser')
    """
    从 HTML 内容中提取合同数据。

    :param html_content: 网页的 HTML 内容
    :return: 提取的合同数据
    """
    if not html_content:
        return []
    soup = BeautifulSoup(html_content, 'html.parser')
    result = {
        "presale": {},
        "existing": {},
        "second_hand": {},
        "historical": {}
    }
    # 解析可售期房统计
    presale_table = soup.find('table', {'bgcolor': '#FFFFFF'})
    # if presale_table:
        # result["presale"]["available"] = parse_presale_table(presale_table)
    # 解析2025年2月预售许可
    presale_license_table = presale_table.find_next('table', {'bgcolor': '#FFFFFF'})
    # if presale_license_table:
    #    result["presale"]["2025_02_license"] = parse_presale_table(presale_license_table)
    # 解析2025/3/7期房网上认购
    presale_subscribe_table = presale_license_table.find_next('table', {'bgcolor': '#FFFFFF'})
    # if presale_subscribe_table:
        # date = get_date(presale_subscribe_table)
        # result["presale"][date+"_subscribe"] = parse_presale_table(presale_subscribe_table)
    # 解析2025/3/7期房网上签约
    presale_sign_table = presale_subscribe_table.find_next('table', {'bgcolor': '#FFFFFF'})
    if presale_sign_table:
        date = get_date(presale_subscribe_table)
        result["presale"][date] = parse_presale_table(presale_sign_table)
    # 解析未签约现房统计
    existing_unsigned_table = presale_sign_table.find_next('table', {'bgcolor': '#FFFFFF'})
    # if existing_unsigned_table:
        # result["existing"]["unsigned"] = parse_existing_table(existing_unsigned_table)
    # 解析现房项目情况
    existing_projects_table = existing_unsigned_table.find_next('table', {'bgcolor': '#FFFFFF'})
    # if existing_projects_table:
        # result["existing"]["projects"] = parse_existing_table(existing_projects_table)
    # 解析2025/3/7现房网上认购
    existing_subscribe_table = existing_projects_table.find_next('table', {'bgcolor': '#FFFFFF'})
    # if existing_subscribe_table:
        # date = get_date(existing_subscribe_table)
        # result["existing"][date+"_subscribe"] = parse_existing_table(existing_subscribe_table)
    # 解析2025/3/7现房网上签约
    existing_sign_table = existing_subscribe_table.find_next('table', {'bgcolor': '#FFFFFF'})
    if existing_sign_table:
        date = get_date(existing_subscribe_table)
        result["existing"][date] = parse_existing_table(existing_sign_table)
    # 解析2025年2月存量房网上签约
    second_hand_license = existing_sign_table.find_next('table', {'bgcolor': '#ffffff'})
    # if second_hand_license:
    #     result["second_hand"]["2025_02"] = parse_second_hand_table(second_hand_license)
    # 解析2025/3/7存量房网上签约
    second_hand_table = second_hand_license.find_next('table', {'bgcolor': '#ffffff'})
    if second_hand_table:
        date = get_date(second_hand_table)
        result["second_hand"][date] = parse_second_hand_table(second_hand_table)
    # 解析历史数据
    historical_tables = soup.find_all('table', {'id': ['table_001', 'table_002']})
    if historical_tables:
        result["historical"] = parse_historical_tables(historical_tables)
    create_database()
    insert_data_into_database(result)

    print('数据已成功存储到数据库！')
    return result

def get_date(table):
    rows0 = table.find_all('tr')[0]
    # 定义正则表达式模式来匹配日期
    pattern = r'(\d{4}/\d{1,2}/\d{1,2})'
    
    
    # 使用 re.search 函数查找匹配的日期
    match = re.search(pattern, rows0.get_text(strip=True))

    if match:
        # 如果找到匹配项，提取日期
        date = match.group(1) 
        print(date)
        return date
    else:
        return ''

def parse_presale_table(table):
    data = {}

    rows = table.find_all('tr')[1:]  # 跳过标题行
    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 2:
            key = cols[0].get_text(strip=True).replace('\u00a0', '')
            value = cols[1].get_text(strip=True).replace('\u00a0', '')
            data[key] = value
    return data


def parse_existing_table(table):
    data = {}
    rows = table.find_all('tr')[1:]  # 跳过标题行
    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 2:
            key = cols[0].get_text(strip=True).replace('\u00a0', '')
            value = cols[1].get_text(strip=True).replace('\u00a0', '')
            data[key] = value
    return data


def parse_second_hand_table(table):
    data = {}
    rows = table.find_all('tr')[1:]  # 跳过标题行
    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 2:
            key = cols[0].get_text(strip=True).replace('\u00a0', '')
            value = cols[1].get_text(strip=True).replace('\u00a0', '')
            data[key] = value
    return data


def parse_historical_tables(tables):
    # 创建一个空字典，用于存储解析后的数据
    data = {}
    # 遍历传入的表格列表
    for table in tables:
        # 如果表格的id为'table_001'，则调用parse_historical_table函数解析该表格，并将解析后的数据存储在data字典的'new_housing'键中
        if table['id'] == 'table_001':
            data['new_housing'] = parse_historical_table(table)
        # 如果表格的id为'table_002'，则调用parse_historical_table函数解析该表格，并将解析后的数据存储在data字典的'second_hand'键中
        elif table['id'] == 'table_002':
            data['second_hand'] = parse_historical_table(table)
    # 返回解析后的数据
    return data


def parse_historical_table(table):
    data = []
    rows = table.find_all('tr')[2:]  # 跳过标题行
    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 4:
            year = cols[0].get_text(strip=True)
            residential_units = cols[1].get_text(strip=True)
            residential_area = cols[2].get_text(strip=True)
            non_residential_area = cols[3].get_text(strip=True)
            data.append({
                'year': year,
                'residential_units': residential_units,
                'residential_area': residential_area,
                'non_residential_area': non_residential_area
            })
    return data


def create_database():
    conn = sqlite3.connect('real_estate.db')
    c = conn.cursor()
    # 创建期房综合表
    c.execute('''CREATE TABLE IF NOT EXISTS presale (
        item TEXT,
        data TEXT,
        createtime TEXT,
        PRIMARY KEY (item, createtime)
    )''')
    # 创建现房综合表
    c.execute('''CREATE TABLE IF NOT EXISTS existing (
        item TEXT,
        data TEXT,
        createtime TEXT,
        PRIMARY KEY (item, createtime)
    )''')
    # 创建存量房综合表
    c.execute('''CREATE TABLE IF NOT EXISTS second_hand (
        item TEXT,
        data TEXT,
        createtime TEXT,
        PRIMARY KEY (item, createtime)
    )''')
    # 创建历史数据表
    c.execute('''CREATE TABLE IF NOT EXISTS historical (
        year TEXT,
        residential_units TEXT,
        residential_area TEXT,
        non_residential_area TEXT,
        createtime TEXT,
        PRIMARY KEY (year, createtime)
    )''')

    # c.execute('''CREATE TABLE IF NOT EXISTS historical_new_housing (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     year TEXT,
    #     residential_units TEXT,
    #     residential_area TEXT,
    #     non_residential_area TEXT
    # )''')
    # c.execute('''CREATE TABLE IF NOT EXISTS historical_second_hand (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     year TEXT,
    #     residential_units TEXT,
    #     residential_area TEXT,
    #     non_residential_area TEXT
    # )''')


def insert_data_into_database(result):
    conn = sqlite3.connect('real_estate.db')
    c = conn.cursor()

    # 插入期房综合数据
    if 'presale' in result:
        for sub_type, sub_data in result['presale'].items():
            for key, value in sub_data.items():
                c.execute("INSERT OR REPLACE INTO presale (item, data, createtime) VALUES (?, ?, ?)", (key, value, sub_type))
    # 插入现房综合数据
    if 'existing' in result:
        for sub_type, sub_data in result['existing'].items():
            for key, value in sub_data.items():
                c.execute("INSERT OR REPLACE INTO existing (item, data, createtime) VALUES (?, ?, ?)", (key, value, sub_type))
    # 插入存量房综合数据
    if 'second_hand' in result:
        for sub_type, sub_data in result['second_hand'].items():
            for key, value in sub_data.items():
                c.execute("INSERT OR REPLACE INTO second_hand (item, data, createtime) VALUES (?, ?, ?)", (key, value, sub_type))
    # 插入历史综合数据
    if result['historical']:
        if 'new_housing' in result['historical']:
            for data in result['historical']['new_housing']:
                c.execute("INSERT OR REPLACE INTO historical (year, residential_units, residential_area, non_residential_area, createtime) VALUES (?, ?, ?, ?, 'new_housing')", (data['year'], data['residential_units'], data['residential_area'], data['non_residential_area']))
        if 'second_hand' in result['historical']:
            for data in result['historical']['second_hand']:
                c.execute("INSERT OR REPLACE INTO historical (year, residential_units, residential_area, non_residential_area, createtime) VALUES (?, ?, ?, ?, 'second_hand')", (data['year'], data['residential_units'], data['residential_area'], data['non_residential_area']))
    # // 删除原有的各表数据插入语句
    conn.commit()
    conn.close()


if __name__ == '__main__':
     # with open('3.8.html', 'r', encoding='utf-8') as f:
     #     html_content = f.read()
     html_url = 'http://bjjs.zjw.beijing.gov.cn/eportal/ui?pageId=307749'
     content = get_html_content(html_url)
     result = parse_html(content)

