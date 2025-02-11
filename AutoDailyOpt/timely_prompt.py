﻿# encoding=utf-8

"""
本脚本用于定时提示now表中的stk数据
"""


""" =========================== 将当前路径及工程的跟目录添加到路径中 ============================ """
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = curPath[:curPath.find("MoDeng\\")+len("MoDeng\\")]  # 获取myProject，也就是项目的根路径

sys.path.append('..')
sys.path.append(rootPath)

# 对配置文件进行检测
from Config.AutoGenerateConfigFile import checkConfigFile
checkConfigFile()

import matplotlib
matplotlib.use('agg')
import jqdatasdk as jq

from DataSource.Code2Name import code2name
from Experiment.MiddlePeriodLevelCheck.Demo1 import concerned_stk_middle_check, update_middle_period_hour_data

from Experiment.CornerDetectAndAutoEmail.Sub import genStkIdxPicForQQ, genStkPicForQQ
from Experiment.MACD_Stray_Analysis.Demo1 import send_W_M_MACD, checkWeekStrayForAll
from Experiment.RelativeRank.Sub import relativeRank, get_k_data_JQ, calRealtimeRankWithGlobal, get_current_price_JQ, \
    get_RT_price, sendHourMACDToQQ, updateConcernStkMData
from Experiment.Reseau.StdForReseau.Sub import getSigleStkReseau
from SDK.MyTimeOPT import get_current_date_str


from Config.Sub import readConfig
from AutoDailyOpt.Sub import readLastP, saveLastP, JudgeSingleStk, calRSVRank
from AutoDailyOpt.p_diff_ratio_last import p_diff_ratio_last_dic, RSV_Record
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger
from pylab import *
from SendMsgByQQ.QQGUI import send_qq
from SendMsgByQQ.SendPicByQQ import send_pic_qq


""" =========================== 子函数 ============================ """
basic_earn_threshold = 120      # 100 IS ENOUGH
remind_ratio = 0.8              # 操作提前提醒

basic_ratio = 4                 # 获取的每只stk的权值，除以基础ratio，即得到最终加权！
money_each_opt = 5000


def printStkListPic2QQ(code_list, towho, title=None):

    if title is not None:
        title_str = title
    else:
        title_str = ''

    for x in code_list:
        df = get_k_data_JQ(x, 400)
        fig, _ = genStkPicForQQ(df)

        plt.title(str(x)+title_str)
        send_pic_qq(towho, fig)
        plt.close()

        fig, _ = genStkIdxPicForQQ(df)

        plt.title(str(x)+title_str)
        send_pic_qq(towho, fig)
        plt.close()


def sendBillBoardPic2QQ():

    df_today = jq.get_billboard_list(start_date=get_current_date_str())

    abnor_list = list(df_today.groupby(by='abnormal_name'))

    # 打印4类
    df_duplicate_4 = abnor_list[4][1].loc[~abnor_list[4][1]['code'].duplicated(), :]
    code_list_4 = [x[:6] for x in list(df_duplicate_4['code'].values)]

    printStkListPic2QQ(code_list_4, '影子2', title=abnor_list[4][0])

    # 打印1类
    df_duplicate_1 = abnor_list[1][1].loc[~abnor_list[1][1]['code'].duplicated(), :]
    code_list_1 = [x[:6] for x in list(df_duplicate_1['code'].values)]

    printStkListPic2QQ(code_list_1, '影子2', title=abnor_list[1][0])


def printMainRank():
    """
        打印重要的index
    """
    r = [(x, '%.2f' % (calRealtimeRankWithGlobal(
            stk_code=x)[0])) for x in ['sh', 'sz', 'cyb']]

    send_qq('影子', "Main_Index:\n" + str(r))


def sendConcernedStkPicToSelf_V2():

    """
    将自己关心的数据打印出图，发送到qq
    相较于之前版本，本次改进为：
    1、使用json文件中的code列表代替数据库中的列表
    2、进行判断，出发发送条件再予以发送
    :return:
    """
    towho = '影子2'
    send_qq(towho, '以下是已入的stk的形势图：')
    code_list = readConfig()['buy_stk']

    for x in code_list + ['sh', 'sz', 'cyb']:

        df = get_k_data_JQ(x, 400)
        fig, _ = genStkPicForQQ(df)

        plt.title(str(x))
        send_pic_qq(towho, fig)
        # plt.show()
        plt.close()

        fig, _ = genStkIdxPicForQQ(df)

        plt.title(str(x))
        send_pic_qq(towho, fig)
        # plt.show()
        plt.close()

        send_W_M_MACD(x, towho)


def sendConcernedStkPicToSelf_T():

    """
    将自己关心的数据打印出图，发送到qq
    :return:
    """
    towho = '影子2'
    send_qq(towho, '以下是已入的stk的形势图：')

    stk_buy = readConfig()['buy_stk']

    for x in stk_buy + ['sh', 'sz', 'cyb']:

        df = get_k_data_JQ(x, 400)
        fig, _, attention = genStkPicForQQ(df, x)

        if attention:
            send_pic_qq(towho, fig)
            send_W_M_MACD(x, towho)
        plt.close()

        # 打印第二张套图
        fig, _, attention = genStkIdxPicForQQ(df, x)
        if attention:
            send_pic_qq(towho, fig)

        plt.close()


def sendMainIndexStkPic2Public():

    """
    将自己关心的数据打印出图，发送到qq
    :return:
    """

    for x in ['sh', 'sz', 'cyb']:

        df = get_k_data_JQ(x, 400)
        fig, _ = genStkPicForQQ(df)

        plt.title(str(x))
        send_pic_qq('大盘上涨概率公示', fig)
        plt.close()

        fig, _ = genStkIdxPicForQQ(df)

        plt.title(str(x))
        send_pic_qq('大盘上涨概率公示', fig)
        plt.close()


def printMainRankForPublic():
    """
        打印重要的index
    """
    r = [(x, '%.2f' % (calRealtimeRankWithGlobal(stk_code=x)[0]),
             '%.2f' % (calRealtimeRankWithGlobal(stk_code=x)[2])) for x in ['sh', 'sz', 'cyb']]

    note = str([x[0]+'\n'+'上涨概率：'+str(x[1])+'%\n'+'当前值：'+str(x[2])+'\n' for x in r])\
        .replace('sh', '上证')\
        .replace('sz', '深证')\
        .replace('cyb', '创业板')\
        .replace('[', '')\
        .replace(']', '')\
        .replace("'", '')\
        .replace('\\n', "\n")\
        .replace(',', '--------------------\n')

    send_qq('大盘上涨概率公示', '\n\n--------------------\n' + note)


# def JudgePChangeRatio(stk_code, price_diff_ratio, str_gui, debug=True, gui=False):
#     """
#     判断stk的变化是否达到一定的幅度，以杜绝反复上报
#     :param stk_code:
#     :return:
#     """
#     global price_diff_ratio_last_dic
#     if debug:
#         str_temp = '函数JudgeSingleStk：进入函数！'
#         if gui:
#             str_gui['msg'] = str_gui['msg'] + str_temp + '\n'
#         else:
#             print('函数JudgeSingleStk：进入函数！')
#
#     # 变化1个百分点再报，避免重复报
#     if stk_code in p_diff_ratio_last_dic.keys():
#         if math.fabs(price_diff_ratio - p_diff_ratio_last_dic[stk_code])*100 > readConfig()['pcr']:
#
#             p_diff_ratio_last_dic[stk_code] = price_diff_ratio
#             if debug:
#                 str_temp = '函数JudgeSingleStk：' + str(stk_code) + '价格变化幅度达标，允许推送，并更新振幅记忆！' +\
#                       '\np_ratio_now:'+str(price_diff_ratio) +\
#                       '\np_ratio_last:'+str(p_diff_ratio_last_dic[stk_code])
#                 if gui:
#                     str_gui['msg'] = str_gui['msg'] + str_temp + '\n'
#                 else:
#                     print(str_temp)
#
#             return True, str_gui
#         else:
#             str_temp = '函数JudgeSingleStk：' + str(stk_code) + '价格变化幅度不够，不许推送！' +\
#                   '\np_ratio_now:' + str(price_diff_ratio) +\
#                   '\np_ratio_last:' + str(p_diff_ratio_last_dic[stk_code])
#             if gui:
#                 str_gui['msg'] = str_gui['msg'] + str_temp + '\n'
#             else:
#                 print(str_temp)
#
#             return False, str_gui
#     else:
#         p_diff_ratio_last_dic[stk_code] = price_diff_ratio
#         if debug:
#             str_temp = '函数JudgeSingleStk：' + str(stk_code) + '首次运行，允许推送！'
#             if gui:
#                 str_gui['msg'] = str_gui['msg'] + str_temp + '\n'
#             else:
#                 print(str_temp)
#
#         return True, str_gui


def myPrint(str_gui, str_temp, method='n', towho=''):
    """

    :param gui:
    :param str_gui:
    :param method:
    :param towho:
    :return:
    """
    if method is 'n':
        print(str_temp)

    elif method is 'gm':
        str_gui['msg'] = str_gui['msg'] + str_temp + '\n\n'

    elif method is 'gn':
        str_gui['note'] = str_gui['note'] + str_temp + '\n\n'

    elif method is 'qq':
        send_qq(towho, str_temp)

    return str_gui


# def JudgeSingleStk(stk_code, stk_amount_last,  qq, debug=True, gui=False):
#
#     str_gui = {
#         'note': '',
#         'msg': ''
#     }
#
#     # 获取该stk的实时价格,如果是大盘指数，使用聚宽数据，否则有限使用tushare
#     if stk_code in ['sh', 'sz', 'cyb']:
#         current_price = get_current_price_JQ(stk_code)
#     else:
#         try:
#             current_price = get_RT_price(stk_code, source='ts')
#         except:
#
#             str_gui = myPrint(str_gui, stk_code + '获取实时price失败！', method={True:'gm', False:'n'}[gui])
#             return str_gui
#
#     # 获取上次price
#     stk_price_last = readLastP(stk_code)
#     if stk_price_last < 0:
#         saveLastP(stk_code, current_price)
#         stk_price_last = current_price
#
#     # 实时计算价差
#     price_diff = current_price - stk_price_last
#     price_diff_ratio = price_diff/stk_price_last
#
#     if debug:
#         str_gui = myPrint(
#             str_gui,
#             '\n\n' + stk_code + ':\np_now:' + str(current_price) + '\np_last:' + str(
#                 stk_price_last) + '\np_change_ratio:' + str(price_diff_ratio),
#             method={True: 'gm', False: 'n'}[gui])
#
#     if current_price == 0.0:
#
#         str_gui = myPrint(
#             str_gui,
#             stk_code + 'price==0.0! 返回！',
#             method={True: 'gm', False: 'n'}[gui])
#
#         return str_gui
#
#     buy_amount = math.floor((money_each_opt/current_price)/100)*100
#
#     # 实时计算网格大小
#     earn_threshold_unit = getSigleStkReseau(stk_code)
#
#     # 调节 buy 和 sale 的threshold
#     if stk_code in RSV_Record.keys():
#         thh_sale = earn_threshold_unit*2*RSV_Record[stk_code]
#         thh_buy = earn_threshold_unit * 2 * (1-RSV_Record[stk_code])
#     else:
#         RSV_Record[stk_code] = calRSVRank(stk_code, 5)/100
#         thh_sale = 1
#         thh_buy = -1
#
#     # 计算其离心度分数
#     try:
#         # rank9, _, _, _ = calRealtimeRankWithGlobal(stk_code=stk_code)
#         rank9 = -1
#     except:
#         rank9 = -1
#
#     if debug:
#
#         str_gui = myPrint(
#             str_gui,
#             stk_code +
#             ':\np_change:' + str(price_diff * stk_amount_last) +
#             '\nthreshold:' + str(earn_threshold_unit) +
#             '\nthh_sale:' + str(thh_sale) +
#             '\nthh_buy:' + str(thh_buy),
#             method={True: 'gm', False: 'n'}[gui])
#
#     if price_diff > thh_sale:
#         # if JudgePChangeRatio(stk_code, price_diff_ratio):
#
#         str_temp = "Reach! S! "+stk_code + code2name(stk_code) +\
#                 '\nAmount:' + str(stk_amount_last) +\
#                 '\nP_now:' + str(current_price) +\
#                 '\nP_last:' + str(stk_price_last) +\
#                 '\nthreshold_b:' + '%0.2f' % thh_buy +\
#                 '\nthreshold_s:' + '%0.2f' % thh_sale +\
#                 '\nM9_rank:' + str('%0.2f' % rank9)
#
#         str_gui = myPrint(
#             str_gui,
#             str_temp,
#             method={True: 'gn', False: 'qq'}[gui],
#             towho=qq)
#
#         if not gui:
#             sendHourMACDToQQ(stk_code, qq, source='jq')
#
#         saveLastP(stk_code, current_price)
#
#     elif price_diff < -thh_buy:
#         # if JudgePChangeRatio(stk_code, price_diff_ratio):
#
#         str_temp= "Reach! B! " + stk_code + code2name(stk_code) +\
#                 '\nAmount:' + str(buy_amount) +\
#                 '\nP_now:' + str(current_price) +\
#                 '\nP_last:' + str(stk_price_last) +\
#                 '\nthreshold_b:' + '%0.1f' % thh_buy +\
#                 '\nthreshold_s:' + '%0.1f' % thh_sale +\
#                 '\nM9_rank:' + str('%0.2f' % rank9)
#
#         str_gui = myPrint(
#             str_gui,
#             str_temp,
#             method={True: 'gn', False: 'qq'}[gui],
#             towho=qq)
#
#         if not gui:
#             sendHourMACDToQQ(stk_code, qq, source='jq')
#
#         saveLastP(stk_code, current_price)
#
#     else:
#         str_gui = myPrint(
#             str_gui,
#             stk_code + ':未触发任何警戒线！',
#             method={True: 'gm', False: 'n'}[gui])
#
#     # 波动检测
#     change_flag, str_gui = JudgePChangeRatio(stk_code, price_diff_ratio, str_gui=str_gui, gui=gui)
#     if change_flag:
#
#         str_temp = "波动推送! " + stk_code + code2name(stk_code) +\
#                 '\nAmount:' + str(buy_amount) +\
#                 '\nP_now:' + str(current_price) +\
#                 '\nP_last:' + str(stk_price_last) +\
#                 '\nthreshold_b:' + '%0.1f' % thh_buy +\
#                 '\nthreshold_s:' + '%0.1f' % thh_sale +\
#                 '\nM9_rank:' + str('%0.2f' % rank9)
#
#         str_gui = myPrint(
#             str_gui,
#             str_temp,
#             method={True: 'gn', False: 'qq'}[gui],
#             towho=qq)
#
#         if not gui:
#             sendHourMACDToQQ(stk_code, qq, source='jq')
#
#     return str_gui


def updateRSVRecord():
    try:
        code_list = readConfig()['buy_stk']

        # global  RSV_Record
        for stk in code_list:
            RSV_Record[stk] = calRSVRank(stk, 5)

    except Exception as e:
        send_qq('影子2', 'RSV数据更新失败！\n' + str(e))


# def calRSVRank(stk_code, Mdays, history_length=400):
#
#     df = get_k_data_JQ(stk_code, count=history_length, end_date=get_current_date_str())
#
#     # 移动平均线+RSV（未成熟随机值）
#     M = Mdays
#
#     df['low_M'+str(M)] = df['low'].rolling(window=M).mean()
#     df['high_M'+str(M)] = df['high'].rolling(window=M).mean()
#     df['close_M'+str(M)] = df['close'].rolling(window=M).mean()
#
#     for idx in df.index:
#         if (df.loc[idx, 'high_M'+str(M)] - df.loc[idx, 'low_M'+str(M)] ==0) | (df.loc[idx, 'close_M'+str(M)] - df.loc[idx, 'low_M'+str(M)] ==0):
#             df.loc[idx, 'RSV'] = 0.5
#
#         else:
#             df.loc[idx, 'RSV'] = (df.loc[idx, 'close_M'+str(M)] - df.loc[idx, 'low_M'+str(M)])/(df.loc[idx, 'high_M'+str(M)] - df.loc[idx, 'low_M'+str(M)])
#
#     # df['RSV'] = df.apply(lambda x: (x['close_M'+str(M)] - x['low_M'+str(M)])/(x['high_M'+str(M)] - x['low_M'+str(M)]), axis=1)
#
#     return df.tail(1)['RSV'].values[0]


def callback():
    towho = '影子2'
    buy_stk_list = readConfig()['buy_stk'] + readConfig()['concerned_stk']
    for stk in buy_stk_list:
        JudgeSingleStk(stk_code=stk, stk_amount_last=400, qq=towho)


def callback_gui():
    towho = '影子2'
    buy_stk_list = readConfig()['buy_stk'] + readConfig()['concerned_stk']
    for stk in buy_stk_list:
        str_gui = JudgeSingleStk(stk_code=stk, stk_amount_last=400, qq=towho, gui=True)


def autoShutdown():
    send_qq('影子', '120秒后将自动关机！')
    os.system('shutdown -s -f -t 120')


""" =========================== 定时器相关 ============================ """
sched = BlockingScheduler()

trigger_1 = OrTrigger([
    CronTrigger(hour='9', minute='31'),
    CronTrigger(hour='10', minute='1,31'),
    CronTrigger(hour='11', minute='1,31'),
    CronTrigger(hour='13', minute='31'),
    CronTrigger(hour='14', minute='1,31'),
    CronTrigger(hour='14', minute='1')
])
trigger_RT = OrTrigger([
    CronTrigger(hour='9', minute='31-59', second='*/30'),
    CronTrigger(hour='10', minute='*', second='*/30'),
    CronTrigger(hour='11', minute='1-29', second='*/30'),
    CronTrigger(hour='13-14', minute='*', second='*/30')
])

sched.add_job(concerned_stk_middle_check,
              trigger_1,
              day_of_week='mon-fri',
              max_instances=10)

# 定时打印中期水平
sched.add_job(callback,
              trigger_RT,
              day_of_week='mon-fri',
              minute='*/2',
              max_instances=10)

# 打印已有的stk情况
sched.add_job(func=sendConcernedStkPicToSelf_T, trigger='cron', day_of_week='mon-fri', hour=18, minute=50, misfire_grace_time=3600, coalesce=True)

# 定时更新中期价格小时数据
sched.add_job(func=update_middle_period_hour_data, trigger='cron', day_of_week='mon-fri', hour=3, minute=50, misfire_grace_time=3600, coalesce=True)

# 打印save stk 的相对水平，低位囤货
# sched.add_job(func=sendRelaLevel2QQ, trigger='cron', day_of_week='mon-fri', hour=18, minute=20, misfire_grace_time=3600, coalesce=True)

# 检测周背离 checkWeekStrayForAll
sched.add_job(func=checkWeekStrayForAll, trigger='cron', day_of_week='mon-fri', hour=19, minute=15, misfire_grace_time=3600, coalesce=True)

# 更新离心度历史数据
sched.add_job(func=updateConcernStkMData, trigger='cron', day_of_week='mon-fri', hour=5, minute=30, misfire_grace_time=3600, coalesce=True)

# 更新RSV数据
sched.add_job(func=updateRSVRecord, trigger='cron', day_of_week='mon-fri', hour=6, minute=15, misfire_grace_time=3600, coalesce=True)

# 周六自动关机
sched.add_job(func=autoShutdown, trigger='cron', day_of_week='sat', hour=1, minute=30, misfire_grace_time=3600, coalesce=True)

# 打印深度学习的预测
# sched.add_job(func=printPredict2Public, trigger='cron', day_of_week='mon-fri', hour=19, minute=30, misfire_grace_time=3600, coalesce=True)


if __name__ == '__main__':

    # 对配置文件进行检测
    checkConfigFile()

    # 导入聚宽数据
    from DataSource.auth_info import *

    # concerned_stk_middle_check()
    # sendConcernedStkPicToSelf_T()
    # printPredict2Public()
    # checkWeekStrayForAll()
    # updateConcernStkMData()
    updateRSVRecord()

    sched.start()
