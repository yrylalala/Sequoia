# -*- encoding: UTF-8 -*-

import data_fetcher
import utils
import strategy.enter as enter
from strategy import turtle_trade
from strategy import backtrace_ma250
from strategy import breakthrough_platform
from strategy import parking_apron
from strategy import low_backtrace_increase
from strategy import keep_increasing
import tushare as ts
import push
import logging
import db
import time
import datetime
import urllib
import settings
import pandas as pd
import os


def process():
    logging.info("************************ process start ***************************************")
    try:
        all_data = ts.get_today_all()
        subset = all_data[['code', 'name', 'nmc']]
        subset.to_csv(settings.config['stocks_file'], index=None, header=True)
        stocks = [tuple(x) for x in subset.values]
        statistics(all_data, stocks)
    except urllib.error.URLError as e:
        subset = pd.read_csv(settings.config['stocks_file'])
        subset['code'] = subset['code'].astype(str)
        stocks = [tuple(x) for x in subset.values]

    if utils.need_update_data():
        utils.prepare()
        data_fetcher.run(stocks)
        check_exit()

    strategies = {
        '海龟交易法则': turtle_trade.check_enter,
        '放量上涨': enter.check_volume,
        '突破平台': breakthrough_platform.check,
        '均线多头': keep_increasing.check,
        '无大幅回撤': low_backtrace_increase.check,
        '停机坪': parking_apron.check,
        '回踩年线': backtrace_ma250.check,
    }

    if datetime.datetime.now().weekday() == 0:
        strategies['均线多头'] = keep_increasing.check

    for strategy, strategy_func in strategies.items():
        check(stocks, strategy, strategy_func)
        time.sleep(2)

    logging.info("************************ process   end ***************************************")


def check(stocks, strategy, strategy_func):
    end = None
    m_filter = check_enter(end_date=end, strategy_fun=strategy_func)
    results = list(filter(m_filter, stocks))
    # push.strategy('**************"{0}"**************\n{1}\n**************"{0}"**************\n'.format(strategy, results))
    save_2_file(results, strategy)


def check_enter(end_date=None, strategy_fun=enter.check_volume):
    def end_date_filter(code_name):
        data = utils.read_data(code_name)
        if data is None:
            return False
        else:
            return strategy_fun(code_name, data, end_date=end_date)
        # if result:
        #     message = turtle_trade.calculate(code_name, data)
        #     push.strategy("{0} {1}".format(code_name, message))

    return end_date_filter


# 统计数据
def statistics(all_data, stocks):
    limitup = len(all_data.loc[(all_data['changepercent'] >= 9.5)])
    limitdown = len(all_data.loc[(all_data['changepercent'] <= -9.5)])

    up5 = len(all_data.loc[(all_data['changepercent'] >= 5)])
    down5 = len(all_data.loc[(all_data['changepercent'] <= -5)])

    def ma250(stock):
        stock_data = utils.read_data(stock)
        return enter.check_ma(stock, stock_data)

    ma250_count = len(list(filter(ma250, stocks)))

    msg = "涨停数：{}   跌停数：{}\n涨幅大于5%数：{}  跌幅大于5%数：{}\n年线以上个股数量：    {}" \
        .format(limitup, limitdown, up5, down5, ma250_count)
    push.statistics(msg)


def check_exit():
    t_shelve = db.ShelvePersistence()
    file = t_shelve.open()
    for key in file:
        code_name = file[key]['code_name']
        data = utils.read_data(code_name)
        if turtle_trade.check_exit(code_name, data):
            push.strategy("{0} 达到退出条件".format(code_name))
            del file[key]
        elif turtle_trade.check_stop(code_name, data, file[key]):
            push.strategy("{0} 达到止损条件".format(code_name))
            del file[key]

    file.close()


# 将不同策略选择结果存到文件中
def save_2_file(results, strategy_name):
    file_path = './' + datetime.date.today().strftime('%m%d')
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    file_name = file_path + '/' + strategy_name + '.ini'
    with open(file_name, mode='a', encoding='utf-8') as f:
        if results is None or not results:
            f.write('今日没有符合条件的股票\n')
        else:
            for result in results:
                f.write(str(result).lstrip('(').rstrip(')') + '\n')


# 统计不同策略结果
def statistical_result():
    data_dict = {}
    data_set = []
    strategies = {
        '海龟交易法则',
        '放量上涨',
        '突破平台',
        '均线多头',
        '无大幅回撤',
        '停机坪',
        '回踩年线',
    }
    file_path = './' + datetime.date.today().strftime('%m%d') + '/'
    for strategy in strategies:
        path = file_path + strategy + ".ini"
        with open(path, "r") as f:
            for line in f:
                data = line[:-1].replace('\'', '').replace(' ', '').split(',')
                if data_dict.get(data[0]):
                    data_dict[data[0]] = [data_dict[data[0]][0] + 1, data[1]]
                else:
                    data_dict[data[0]] = [1, data[1]]

    for id in data_dict:
        if data_dict.get(id)[0] > 2:
            data_set.append([id, data_dict[id][1]])

    result_file_name = file_path + '/result.txt'
    with open(result_file_name, mode='a', encoding='utf-8') as f:
        if data_set is None or not data_set:
            f.write('今日没有符合条件的股票\n')
        else:
            for data in data_set:
                f.write(str(data).lstrip('[').rstrip(']').replace('\'', '') + '\n')
