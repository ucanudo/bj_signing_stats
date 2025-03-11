import datetime
from flask import Flask, render_template,Blueprint
import sqlite3


from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# 本地模块导入
import process_real_estate_data_

# 初始化调度器
scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
scheduler.add_job(
    id='daily_contracts_job',
    func=lambda: process_real_estate_data_.parse_html(process_real_estate_data_.get_html_content('http://bjjs.zjw.beijing.gov.cn/eportal/ui?pageId=307749')),
    trigger=IntervalTrigger(hours=24, start_date='2024-01-01 09:59:00'),
    misfire_grace_time=60
)
scheduler.start()

app = Flask(__name__)

def get_real_estate_data():
    conn = sqlite3.connect('real_estate.db')
    cursor = conn.cursor()
    
    # 获取现房数据
    cursor.execute("SELECT createtime, data FROM existing WHERE item='其中住宅套数：'")
    one_homes = cursor.fetchall()
    
    # 获取期房数据  
    cursor.execute("SELECT createtime, data FROM presale WHERE item='其中住宅套数：'")
    presale_homes = cursor.fetchall()

    # 获取存量房数据  
    cursor.execute("SELECT createtime, data FROM second_hand WHERE item='住宅签约套数：'")
    second_homes = cursor.fetchall()

    # 按日期排序
    one_homes.sort(key=lambda x: datetime.datetime.strptime(x[0], '%Y/%m/%d'))
    presale_homes.sort(key=lambda x: datetime.datetime.strptime(x[0], '%Y/%m/%d'))
    second_homes.sort(key=lambda x: datetime.datetime.strptime(x[0], '%Y/%m/%d'))
    
    # 计算每日现房数据和期房数据的和
    new_data = {}
    
    for createtime, data in one_homes:
        # date = datetime.strptime(createtime, '%Y/%m/%d').strftime('%Y-%m-%d')
        
        if createtime not in new_data:
            new_data[createtime] = 0
        new_data[createtime] += int(data)

    
    for createtime, data in presale_homes:
        # createtime = createtimetime.strptime(createtime, '%Y/%m/%d').strftime('%Y-%m-%d')
        if createtime not in new_data:
            new_data[createtime] = 0
        new_data[createtime] +=  int(data)
    
    # 转换为列表格式
    one_homes_sign = [(date, total) for date, total in new_data.items()]
    conn.close()
    return one_homes_sign,second_homes
    

    
    # 处理日期格式
    # existing_homes = [(datetime.strptime(createtime, '%Y/%m/%d').strftime('%Y-%m-%d'), data) 
    #                  for createtime, data in existing_homes]
    # new_homes = [(datetime.strptime(createtime, '%Y/%m/%d').strftime('%Y-%m-%d'), data)
    #             for createtime, data in new_homes]
    
    return existing_homes, new_homes

@app.route('/')
def index():
    # existing_homes, 
    new_homes,second_homes = get_real_estate_data()
    return render_template('index.html', 
                         existing_homes=second_homes,
                         new_homes=new_homes)

if __name__ == '__main__':
    app.run(debug=True)
