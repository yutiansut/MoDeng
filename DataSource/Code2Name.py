# encoding = utf-8

"""
将code2name信息本地json化
"""
from Config.AutoGenerateConfigFile import data_dir
import json
import tushare as ts
import os

json_code2name_dir = data_dir + 'code2name.json'


def update_code2name_info():

    # 下载基本信息
    stk_info_df = ts.get_stock_basics().reset_index()

    # 生成code2name字典
    code2name = dict(stk_info_df.loc[:, ['code', 'name']].to_dict(orient='split')['data'])

    # 将信息保存到json文件
    with open(json_code2name_dir, 'w') as f:
        json.dump(code2name, f)


def read_code2name():

    if os.path.exists(json_code2name_dir):

        # 读取json文件
        with open(json_code2name_dir, 'r') as f:
            return json.load(f)
    else:
        update_code2name_info()

        # 读取json文件
        with open(json_code2name_dir, 'r') as f:
            return json.load(f)


dict_code2name = read_code2name()


def code2name(code):
    if code in dict_code2name.keys():
        return dict_code2name[code]
    elif code in ['sh', 'sz', 'cyb']:
        return {
            'sh': '上证',
            'sz': '深证',
            'cyb': '创业板'
        }[code]
    else:
        return '未知名字'


if __name__ == '__main__':
    update_code2name_info()
    code2name = read_code2name()

    
    end = 0
