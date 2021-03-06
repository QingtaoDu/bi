# coding:utf-8
#
# The MIT License (MIT)
#
# Copyright (c) 2016-2020 yutiansut/QUANTAXIS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import concurrent
import datetime
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import json
import pandas as pd
import pymongo

from QUANTAXIS.QAFetch import QA_fetch_get_stock_block
from QUANTAXIS.QAFetch.QATdx import (
    QA_fetch_get_option_day,
    QA_fetch_get_option_min,
    QA_fetch_get_index_day,
    QA_fetch_get_index_min,
    QA_fetch_get_stock_day,
    QA_fetch_get_stock_info,
    QA_fetch_get_stock_list,
    QA_fetch_get_future_list,
    QA_fetch_get_index_list,
    QA_fetch_get_future_day,
    QA_fetch_get_future_min,
    QA_fetch_get_stock_min,
    QA_fetch_get_stock_transaction,
    QA_fetch_get_index_transaction,
    QA_fetch_get_stock_xdxr,
    QA_fetch_get_bond_day,
    QA_fetch_get_bond_list,
    QA_fetch_get_bond_min,
    select_best_ip,
    QA_fetch_get_hkstock_day,
    QA_fetch_get_hkstock_list,
    QA_fetch_get_hkstock_min
)

from QUANTAXIS.QAFetch.QATdx import (

    QA_fetch_get_commodity_option_AL_contract_time_to_market,
    QA_fetch_get_commodity_option_AU_contract_time_to_market,
    QA_fetch_get_commodity_option_CU_contract_time_to_market,
    QA_fetch_get_commodity_option_SR_contract_time_to_market,
    QA_fetch_get_commodity_option_M_contract_time_to_market,
    QA_fetch_get_commodity_option_RU_contract_time_to_market,
    QA_fetch_get_commodity_option_CF_contract_time_to_market,
    QA_fetch_get_commodity_option_C_contract_time_to_market,
    QA_fetch_get_option_50etf_contract_time_to_market,
    QA_fetch_get_option_300etf_contract_time_to_market,
    QA_fetch_get_option_all_contract_time_to_market,

    QA_fetch_get_option_list,
)
from QUANTAXIS.QAUtil import (
    DATABASE,
    QA_util_get_next_day,
    QA_util_get_real_date,
    QA_util_log_info,
    QA_util_to_json_from_pandas,
    trade_date_sse
)
from QUANTAXIS.QAData.data_fq import _QA_data_stock_to_fq
from QUANTAXIS.QAFetch.QAQuery import QA_fetch_stock_day
from QUANTAXIS.QAUtil import Parallelism
from QUANTAXIS.QAFetch.QATdx import ping, get_ip_list_by_multi_process_ping, stock_ip_list
from multiprocessing import cpu_count


# ip=select_best_ip()


def now_time():
    return str(QA_util_get_real_date(str(datetime.date.today() - datetime.timedelta(days=1)), trade_date_sse, -1)) + \
           ' 17:00:00' if datetime.datetime.now().hour < 15 else str(QA_util_get_real_date(
        str(datetime.date.today()), trade_date_sse, -1)) + ' 15:00:00'

def QA_SU_save_single_stock_day(code : str, client= DATABASE, ui_log=None):
    '''
     save single stock_day
    ??????????????????????????????
    :param code: ??????????????????????????????
    :param client:
    :param ui_log:  ???GUI qt ????????????
    :param ui_progress: ???GUI qt ????????????
    '''
    #stock_list = QA_fetch_get_stock_list().code.unique().tolist()
    coll_stock_day = client.stock_day
    coll_stock_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_stock_day):
        try:
            QA_util_log_info(
                '##JOB01 Now Saving STOCK_DAY==== {}'.format(str(code)),
                ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            ref = coll_stock_day.find({'code': str(code)[0:6]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ??????????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']

                QA_util_log_info(
                    'UPDATE_STOCK_DAY \n Trying updating {} from {} to {}'
                    .format(code,
                            start_date,
                            end_date),
                    ui_log
                )
                if start_date != end_date:
                    coll_stock_day.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_stock_day(
                                str(code),
                                QA_util_get_next_day(start_date),
                                end_date,
                                '00'
                            )
                        )
                    )

            # ?????????????????????????????????????????????????????? ???1990-01-01 ???????????????????????????
            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_STOCK_DAY \n Trying updating {} from {} to {}'
                    .format(code,
                            start_date,
                            end_date),
                    ui_log
                )
                if start_date != end_date:
                    coll_stock_day.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_stock_day(
                                str(code),
                                start_date,
                                end_date,
                                '00'
                            )
                        )
                    )
        except Exception as error0:
            print(error0)
            err.append(str(code))

    __saving_work(code, coll_stock_day)

    if len(err) < 1:
        QA_util_log_info('SUCCESS save stock day ^_^', ui_log)
    else:
        QA_util_log_info('ERROR CODE \n ', ui_log)
        QA_util_log_info(err, ui_log)


def QA_SU_save_stock_day(client=DATABASE, ui_log=None, ui_progress=None):
    '''
     save stock_day
    ??????????????????
    :param client:
    :param ui_log:  ???GUI qt ????????????
    :param ui_progress: ???GUI qt ????????????
    :param ui_progress_int_value: ???GUI qt ????????????
    '''
    stock_list = QA_fetch_get_stock_list().code.unique().tolist()
    coll_stock_day = client.stock_day
    coll_stock_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_stock_day):
        try:
            QA_util_log_info(
                '##JOB01 Now Saving STOCK_DAY==== {}'.format(str(code)),
                ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            ref = coll_stock_day.find({'code': str(code)[0:6]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ??????????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']

                QA_util_log_info(
                    'UPDATE_STOCK_DAY \n Trying updating {} from {} to {}'
                    .format(code,
                            start_date,
                            end_date),
                    ui_log
                )
                if start_date != end_date:
                    coll_stock_day.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_stock_day(
                                str(code),
                                QA_util_get_next_day(start_date),
                                end_date,
                                '00'
                            )
                        )
                    )

            # ?????????????????????????????????????????????????????? ???1990-01-01 ???????????????????????????
            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_STOCK_DAY \n Trying updating {} from {} to {}'
                    .format(code,
                            start_date,
                            end_date),
                    ui_log
                )
                if start_date != end_date:
                    coll_stock_day.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_stock_day(
                                str(code),
                                start_date,
                                end_date,
                                '00'
                            )
                        )
                    )
        except Exception as error0:
            print(error0)
            err.append(str(code))

    for item in range(len(stock_list)):
        QA_util_log_info('The {} of Total {}'.format(item, len(stock_list)))

        strProgressToLog = 'DOWNLOAD PROGRESS {} {}'.format(
            str(float(item / len(stock_list) * 100))[0:4] + '%',
            ui_log
        )
        intProgressToLog = int(float(item / len(stock_list) * 100))
        QA_util_log_info(
            strProgressToLog,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intProgressToLog
        )

        __saving_work(stock_list[item], coll_stock_day)

    if len(err) < 1:
        QA_util_log_info('SUCCESS save stock day ^_^', ui_log)
    else:
        QA_util_log_info('ERROR CODE \n ', ui_log)
        QA_util_log_info(err, ui_log)


def gen_param(codelist, start_date=None, end_date=None, if_fq='00', frequence='day', IPList=[]):
    # ??????QA.QAFetch.QATdx.QQA_fetch_get_stock_day????????????????????????
    count = len(IPList)
    my_iterator = iter(range(len(codelist)))
    start_date = str(start_date)[0:10]
    end_date = str(end_date)[0:10]
    return [(code, start_date, end_date, if_fq, frequence, IPList[i % count]['ip'], IPList[i % count]['port'])
            for code, i in [(code, next(my_iterator) % count) for code in codelist]]


def QA_SU_save_stock_week(client=DATABASE, ui_log=None, ui_progress=None):
    """save stock_week

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    stock_list = QA_fetch_get_stock_list().code.unique().tolist()
    coll_stock_week = client.stock_week
    coll_stock_week.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_stock_week):
        try:
            QA_util_log_info(
                '##JOB01 Now Saving STOCK_WEEK==== {}'.format(str(code)),
                ui_log=ui_log
            )

            ref = coll_stock_week.find({'code': str(code)[0:6]})
            end_date = str(now_time())[0:10]
            if ref.count() > 0:
                # ??????????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????

                start_date = ref[ref.count() - 1]['date']

                QA_util_log_info(
                    'UPDATE_STOCK_WEEK \n Trying updating {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:
                    coll_stock_week.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_stock_day(
                                str(code),
                                QA_util_get_next_day(start_date),
                                end_date,
                                '00',
                                frequence='week'
                            )
                        )
                    )
            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_STOCK_WEEK \n Trying updating {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:
                    coll_stock_week.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_stock_day(
                                str(code),
                                start_date,
                                end_date,
                                '00',
                                frequence='week'
                            )
                        )
                    )
        except:
            err.append(str(code))

    for item in range(len(stock_list)):
        QA_util_log_info(
            'The {} of Total {}'.format(item,
                                        len(stock_list)),
            ui_log=ui_log
        )
        strProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(item / len(stock_list) * 100))[0:4] + '%'
        )
        intProgress = int(float(item / len(stock_list) * 100))
        QA_util_log_info(
            strProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intProgress
        )

        __saving_work(stock_list[item], coll_stock_week)
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_stock_month(client=DATABASE, ui_log=None, ui_progress=None):
    """save stock_month

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    stock_list = QA_fetch_get_stock_list().code.unique().tolist()
    coll_stock_month = client.stock_month
    coll_stock_month.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_stock_month):
        try:
            QA_util_log_info(
                '##JOB01 Now Saving STOCK_MONTH==== {}'.format(str(code)),
                ui_log=ui_log
            )

            ref = coll_stock_month.find({'code': str(code)[0:6]})
            end_date = str(now_time())[0:10]
            if ref.count() > 0:
                # ??????????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????

                start_date = ref[ref.count() - 1]['date']

                QA_util_log_info(
                    'UPDATE_STOCK_MONTH \n Trying updating {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:
                    coll_stock_month.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_stock_day(
                                str(code),
                                QA_util_get_next_day(start_date),
                                end_date,
                                '00',
                                frequence='month'
                            )
                        )
                    )
            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_STOCK_MONTH \n Trying updating {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:
                    coll_stock_month.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_stock_day(
                                str(code),
                                start_date,
                                end_date,
                                '00',
                                frequence='month'
                            )
                        )
                    )
        except:
            err.append(str(code))

    for item in range(len(stock_list)):
        QA_util_log_info(
            'The {} of Total {}'.format(item,
                                        len(stock_list)),
            ui_log=ui_log
        )
        strProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(item / len(stock_list) * 100))[0:4] + '%'
        )
        intProgress = int(float(item / len(stock_list) * 100))
        QA_util_log_info(
            strProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intProgress
        )

        __saving_work(stock_list[item], coll_stock_month)
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info('ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_stock_year(client=DATABASE, ui_log=None, ui_progress=None):
    """save stock_year

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    stock_list = QA_fetch_get_stock_list().code.unique().tolist()
    coll_stock_year = client.stock_year
    coll_stock_year.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_stock_year):
        try:
            QA_util_log_info(
                '##JOB01 Now Saving STOCK_YEAR==== {}'.format(str(code)),
                ui_log=ui_log
            )

            ref = coll_stock_year.find({'code': str(code)[0:6]})
            end_date = str(now_time())[0:10]
            if ref.count() > 0:
                # ??????????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????

                start_date = ref[ref.count() - 1]['date']

                QA_util_log_info(
                    'UPDATE_STOCK_YEAR \n Trying updating {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:
                    coll_stock_year.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_stock_day(
                                str(code),
                                QA_util_get_next_day(start_date),
                                end_date,
                                '00',
                                frequence='year'
                            )
                        )
                    )
            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_STOCK_YEAR \n Trying updating {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:
                    coll_stock_year.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_stock_day(
                                str(code),
                                start_date,
                                end_date,
                                '00',
                                frequence='year'
                            )
                        )
                    )
        except:
            err.append(str(code))

    for item in range(len(stock_list)):
        QA_util_log_info(
            'The {} of Total {}'.format(item,
                                        len(stock_list)),
            ui_log=ui_log
        )

        strProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(item / len(stock_list) * 100))[0:4] + '%'
        )
        intProgress = int(float(item / len(stock_list) * 100))
        QA_util_log_info(
            strProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intProgress
        )

        __saving_work(stock_list[item], coll_stock_year)
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_stock_xdxr(client=DATABASE, ui_log=None, ui_progress=None):
    """[summary]

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """
    stock_list = QA_fetch_get_stock_list().code.unique().tolist()
    # client.drop_collection('stock_xdxr')

    try:
        coll = client.stock_xdxr
        coll.create_index(
            [('code',
              pymongo.ASCENDING),
             ('date',
              pymongo.ASCENDING)],
            unique=True
        )
        coll_adj = client.stock_adj
        coll_adj.create_index(
            [('code',
                pymongo.ASCENDING),
                ('date',
                pymongo.ASCENDING)],
            unique=True
        )
    except:
        client.drop_collection('stock_xdxr')
        coll = client.stock_xdxr
        coll.create_index(
            [('code',
              pymongo.ASCENDING),
             ('date',
              pymongo.ASCENDING)],
            unique=True
        )
        client.drop_collection('stock_adj')
        coll_adj = client.stock_adj
        coll_adj.create_index(
            [('code',
                pymongo.ASCENDING),
                ('date',
                pymongo.ASCENDING)],
            unique=True
        )

    err = []

    def __saving_work(code, coll):
        QA_util_log_info(
            '##JOB02 Now Saving XDXR INFO ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            xdxr  = QA_fetch_get_stock_xdxr(str(code))
            try:
                coll.insert_many(
                    QA_util_to_json_from_pandas(xdxr),
                    ordered=False
                )
            except:
                pass
            try:
                data = QA_fetch_stock_day(str(code), '1990-01-01',str(datetime.date.today()), 'pd')
                qfq = _QA_data_stock_to_fq(data, xdxr, 'qfq')
                qfq = qfq.assign(date=qfq.date.apply(lambda x: str(x)[0:10]))
                adjdata = QA_util_to_json_from_pandas(qfq.loc[:, ['date','code', 'adj']])
                coll_adj.delete_many({'code': code})
                #print(adjdata)
                coll_adj.insert_many(adjdata)


            except Exception as e:
                print(e)


        except Exception as e:
            print(e)

            err.append(str(code))

    for i_ in range(len(stock_list)):
        QA_util_log_info(
            'The {} of Total {}'.format(i_,
                                        len(stock_list)),
            ui_log=ui_log
        )
        strLogInfo = 'DOWNLOAD PROGRESS {} '.format(
            str(float(i_ / len(stock_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(i_ / len(stock_list) * 100))
        QA_util_log_info(
            strLogInfo,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        __saving_work(stock_list[i_], coll)


def QA_SU_save_stock_min(client=DATABASE, ui_log=None, ui_progress=None):
    """save stock_min

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    stock_list = QA_fetch_get_stock_list().code.unique().tolist()
    coll = client.stock_min
    coll.create_index(
        [
            ('code',
             pymongo.ASCENDING),
            ('time_stamp',
             pymongo.ASCENDING),
            ('date_stamp',
             pymongo.ASCENDING)
        ]
    )
    err = []

    def __saving_work(code, coll):
        QA_util_log_info(
            '##JOB03 Now Saving STOCK_MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:
            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:6], 'type': type})
                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB03.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )
                    if start_time != end_time:
                        __data = QA_fetch_get_stock_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)[1::]
                            )
                else:
                    start_time = '2015-01-01'
                    QA_util_log_info(
                        '##JOB03.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )
                    if start_time != end_time:
                        __data = QA_fetch_get_stock_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except Exception as e:
            QA_util_log_info(e, ui_log=ui_log)
            err.append(code)
            QA_util_log_info(err, ui_log=ui_log)

    executor = ThreadPoolExecutor(max_workers=4)
    # executor.map((__saving_work,  stock_list[i_], coll),URLS)
    res = {
        executor.submit(__saving_work,
                        stock_list[i_],
                        coll)
        for i_ in range(len(stock_list))
    }
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(stock_list)),
            ui_log=ui_log
        )

        strProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(stock_list) * 100))[0:4] + '%'
        )
        intProgress = int(count / len(stock_list) * 10000.0)
        QA_util_log_info(
            strProgress,
            ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

def QA_SU_save_single_stock_min(code : str, client=DATABASE, ui_log=None, ui_progress=None):
    """save single stock_min

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    #stock_list = QA_fetch_get_stock_list().code.unique().tolist()
    stock_list = [code]
    coll = client.stock_min
    coll.create_index(
        [
            ('code',
             pymongo.ASCENDING),
            ('time_stamp',
             pymongo.ASCENDING),
            ('date_stamp',
             pymongo.ASCENDING)
        ]
    )
    err = []

    def __saving_work(code, coll):
        QA_util_log_info(
            '##JOB03 Now Saving STOCK_MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:
            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:6], 'type': type})
                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB03.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )
                    if start_time != end_time:
                        __data = QA_fetch_get_stock_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)[1::]
                            )
                else:
                    start_time = '2015-01-01'
                    QA_util_log_info(
                        '##JOB03.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )
                    if start_time != end_time:
                        __data = QA_fetch_get_stock_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except Exception as e:
            QA_util_log_info(e, ui_log=ui_log)
            err.append(code)
            QA_util_log_info(err, ui_log=ui_log)

    executor = ThreadPoolExecutor(max_workers=4)
    # executor.map((__saving_work,  stock_list[i_], coll),URLS)
    res = {
        executor.submit(__saving_work,
                        stock_list[i_],
                        coll)
        for i_ in range(len(stock_list))
    }
    count = 1
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(stock_list)),
            ui_log=ui_log
        )

        strProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(stock_list) * 100))[0:4] + '%'
        )
        intProgress = int(count / len(stock_list) * 10000.0)
        QA_util_log_info(
            strProgress,
            ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

def QA_SU_save_single_index_day(code : str, client=DATABASE, ui_log=None):
    """save index_day

    Keyword Arguments:
        code : single index code
        client {[type]} -- [description] (default: {DATABASE})
    """

    #__index_list = QA_fetch_get_stock_list('index')
    coll = client.index_day
    coll.create_index(
        [('code',
          pymongo.ASCENDING),
         ('date_stamp',
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll):

        try:
            ref_ = coll.find({'code': str(code)[0:6]})
            end_time = str(now_time())[0:10]
            if ref_.count() > 0:
                start_time = ref_[ref_.count() - 1]['date']

                QA_util_log_info(
                    '##JOB04 Now Saving INDEX_DAY==== \n Trying updating {} from {} to {}'
                        .format(code,
                                start_time,
                                end_time),
                    ui_log=ui_log
                )

                if start_time != end_time:
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_index_day(
                                str(code),
                                QA_util_get_next_day(start_time),
                                end_time
                            )
                        )
                    )
            else:
                try:
                    start_time = '1990-01-01'
                    QA_util_log_info(
                        '##JOB04 Now Saving INDEX_DAY==== \n Trying updating {} from {} to {}'
                            .format(code,
                                    start_time,
                                    end_time),
                        ui_log=ui_log
                    )
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_index_day(
                                str(code),
                                start_time,
                                end_time
                            )
                        )
                    )
                except:
                    start_time = '2009-01-01'
                    QA_util_log_info(
                        '##JOB04 Now Saving INDEX_DAY==== \n Trying updating {} from {} to {}'
                            .format(code,
                                    start_time,
                                    end_time),
                        ui_log=ui_log
                    )
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_index_day(
                                str(code),
                                start_time,
                                end_time
                            )
                        )
                    )
        except Exception as e:
            QA_util_log_info(e, ui_log=ui_log)
            err.append(str(code))
            QA_util_log_info(err, ui_log=ui_log)


    __saving_work(code, coll)
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

def QA_SU_save_index_day(client=DATABASE, ui_log=None, ui_progress=None):
    """save index_day

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    __index_list = QA_fetch_get_stock_list('index')
    coll = client.index_day
    coll.create_index(
        [('code',
          pymongo.ASCENDING),
         ('date_stamp',
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll):

        try:
            ref_ = coll.find({'code': str(code)[0:6]})
            end_time = str(now_time())[0:10]
            if ref_.count() > 0:
                start_time = ref_[ref_.count() - 1]['date']

                QA_util_log_info(
                    '##JOB04 Now Saving INDEX_DAY==== \n Trying updating {} from {} to {}'
                        .format(code,
                                start_time,
                                end_time),
                    ui_log=ui_log
                )

                if start_time != end_time:
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_index_day(
                                str(code),
                                QA_util_get_next_day(start_time),
                                end_time
                            )
                        )
                    )
            else:
                try:
                    start_time = '1990-01-01'
                    QA_util_log_info(
                        '##JOB04 Now Saving INDEX_DAY==== \n Trying updating {} from {} to {}'
                            .format(code,
                                    start_time,
                                    end_time),
                        ui_log=ui_log
                    )
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_index_day(
                                str(code),
                                start_time,
                                end_time
                            )
                        )
                    )
                except:
                    start_time = '2009-01-01'
                    QA_util_log_info(
                        '##JOB04 Now Saving INDEX_DAY==== \n Trying updating {} from {} to {}'
                            .format(code,
                                    start_time,
                                    end_time),
                        ui_log=ui_log
                    )
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_index_day(
                                str(code),
                                start_time,
                                end_time
                            )
                        )
                    )
        except Exception as e:
            QA_util_log_info(e, ui_log=ui_log)
            err.append(str(code))
            QA_util_log_info(err, ui_log=ui_log)

    for i_ in range(len(__index_list)):
        # __saving_work('000001')
        QA_util_log_info(
            'The {} of Total {}'.format(i_,
                                        len(__index_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(i_ / len(__index_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(i_ / len(__index_list) * 10000.0))
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        __saving_work(__index_list.index[i_][0], coll)
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_index_min(client=DATABASE, ui_log=None, ui_progress=None):
    """save index_min

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    __index_list = QA_fetch_get_stock_list('index')
    coll = client.index_min
    coll.create_index(
        [
            ('code',
             pymongo.ASCENDING),
            ('time_stamp',
             pymongo.ASCENDING),
            ('date_stamp',
             pymongo.ASCENDING)
        ]
    )
    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB05 Now Saving Index_MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:6], 'type': type})
                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB05.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_index_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB05.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_index_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(__saving_work,
                        __index_list.index[i_][0],
                        coll)
        for i_ in range(len(__index_list))
    }  # multi index ./.
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(__index_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(__index_list) * 10000.0))
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(__index_list)),
            ui_log=ui_log
        )
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

def QA_SU_save_single_index_min(code : str, client=DATABASE, ui_log=None, ui_progress=None):
    """save single index_min

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    #__index_list = QA_fetch_get_stock_list('index')
    __index_list = [code]
    coll = client.index_min
    coll.create_index(
        [
            ('code',
             pymongo.ASCENDING),
            ('time_stamp',
             pymongo.ASCENDING),
            ('date_stamp',
             pymongo.ASCENDING)
        ]
    )
    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB05 Now Saving Index_MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:6], 'type': type})
                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB05.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_index_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB05.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_index_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(__saving_work,
                        __index_list[i_],
                        coll)
        for i_ in range(len(__index_list))
    }  # multi index ./.
    count = 1
    for i_ in concurrent.futures.as_completed(res):
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(__index_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(__index_list) * 10000.0))
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(__index_list)),
            ui_log=ui_log
        )
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_single_etf_day(code : str, client=DATABASE, ui_log=None):
    """save etf_day

    Keyword Arguments:
        code : single etf code
        client {[type]} -- [description] (default: {DATABASE})
    """

    #__index_list = QA_fetch_get_stock_list('etf')
    coll = client.index_day
    coll.create_index(
        [('code',
          pymongo.ASCENDING),
         ('date_stamp',
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll):

        try:

            ref_ = coll.find({'code': str(code)[0:6]})
            end_time = str(now_time())[0:10]
            if ref_.count() > 0:
                start_time = ref_[ref_.count() - 1]['date']

                QA_util_log_info(
                    '##JOB06 Now Saving ETF_DAY==== \n Trying updating {} from {} to {}'
                        .format(code,
                                start_time,
                                end_time),
                    ui_log=ui_log
                )

                if start_time != end_time:
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_index_day(
                                str(code),
                                QA_util_get_next_day(start_time),
                                end_time
                            )
                        )
                    )
            else:
                start_time = '1990-01-01'
                QA_util_log_info(
                    '##JOB06 Now Saving ETF_DAY==== \n Trying updating {} from {} to {}'
                        .format(code,
                                start_time,
                                end_time),
                    ui_log=ui_log
                )

                if start_time != end_time:
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_index_day(
                                str(code),
                                start_time,
                                end_time
                            )
                        )
                    )
        except:
            err.append(str(code))

    __saving_work(code, coll)
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

def QA_SU_save_etf_day(client=DATABASE, ui_log=None, ui_progress=None):
    """save etf_day

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    __index_list = QA_fetch_get_stock_list('etf')
    coll = client.index_day
    coll.create_index(
        [('code',
          pymongo.ASCENDING),
         ('date_stamp',
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll):

        try:

            ref_ = coll.find({'code': str(code)[0:6]})
            end_time = str(now_time())[0:10]
            if ref_.count() > 0:
                start_time = ref_[ref_.count() - 1]['date']

                QA_util_log_info(
                    '##JOB06 Now Saving ETF_DAY==== \n Trying updating {} from {} to {}'
                        .format(code,
                                start_time,
                                end_time),
                    ui_log=ui_log
                )

                if start_time != end_time:
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_index_day(
                                str(code),
                                QA_util_get_next_day(start_time),
                                end_time
                            )
                        )
                    )
            else:
                start_time = '1990-01-01'
                QA_util_log_info(
                    '##JOB06 Now Saving ETF_DAY==== \n Trying updating {} from {} to {}'
                        .format(code,
                                start_time,
                                end_time),
                    ui_log=ui_log
                )

                if start_time != end_time:
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_index_day(
                                str(code),
                                start_time,
                                end_time
                            )
                        )
                    )
        except:
            err.append(str(code))

    for i_ in range(len(__index_list)):
        # __saving_work('000001')
        QA_util_log_info(
            'The {} of Total {}'.format(i_,
                                        len(__index_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(i_ / len(__index_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(i_ / len(__index_list) * 10000.0))
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )

        __saving_work(__index_list.index[i_][0], coll)
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_etf_min(client=DATABASE, ui_log=None, ui_progress=None):
    """save etf_min

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    __index_list = QA_fetch_get_stock_list('etf')
    coll = client.index_min
    coll.create_index(
        [
            ('code',
             pymongo.ASCENDING),
            ('time_stamp',
             pymongo.ASCENDING),
            ('date_stamp',
             pymongo.ASCENDING)
        ]
    )
    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB07 Now Saving ETF_MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:6], 'type': type})
                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB07.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_index_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB07.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_index_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(__saving_work,
                        __index_list.index[i_][0],
                        coll)
        for i_ in range(len(__index_list))
    }  # multi index ./.
    count = 1
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(__index_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(__index_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(__index_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

def QA_SU_save_single_etf_min(code : str, client=DATABASE, ui_log=None, ui_progress=None):
    """save single etf_min

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    #__index_list = QA_fetch_get_stock_list('etf')
    __index_list = [code]
    coll = client.index_min
    coll.create_index(
        [
            ('code',
             pymongo.ASCENDING),
            ('time_stamp',
             pymongo.ASCENDING),
            ('date_stamp',
             pymongo.ASCENDING)
        ]
    )
    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB07 Now Saving ETF_MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:6], 'type': type})
                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB07.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_index_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB07.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_index_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(__saving_work,
                        __index_list[i_],
                        coll)
        for i_ in range(len(__index_list))
    }  # multi index ./.
    count = 1
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(__index_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(__index_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(__index_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_stock_list(client=DATABASE, ui_log=None, ui_progress=None):
    """save stock_list

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """
    client.drop_collection('stock_list')
    coll = client.stock_list
    coll.create_index('code')

    try:
        # ????todo ?????????????????????????????? JOB01??? ???????????????????????????
        QA_util_log_info(
            '##JOB08 Now Saving STOCK_LIST ====',
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=5000
        )
        stock_list_from_tdx = QA_fetch_get_stock_list()
        pandas_data = QA_util_to_json_from_pandas(stock_list_from_tdx)
        coll.insert_many(pandas_data)
        QA_util_log_info(
            "????????????????????????",
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=10000
        )
    except Exception as e:
        QA_util_log_info(e, ui_log=ui_log)
        print(" Error save_tdx.QA_SU_save_stock_list exception!")

        pass


def QA_SU_save_etf_list(client=DATABASE, ui_log=None, ui_progress=None):
    """save etf_list

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """
    try:
        QA_util_log_info(
            '##JOB16 Now Saving ETF_LIST ====',
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=5000
        )
        etf_list_from_tdx = QA_fetch_get_stock_list(type_="etf")
        pandas_data = QA_util_to_json_from_pandas(etf_list_from_tdx)

        if len(pandas_data) > 0:
            # ???????????????????????????drop collection ??????
            client.drop_collection('etf_list')
            coll = client.etf_list
            coll.create_index('code')
            coll.insert_many(pandas_data)
        QA_util_log_info(
            "??????ETF????????????",
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=10000
        )
    except Exception as e:
        QA_util_log_info(e, ui_log=ui_log)
        print(" Error save_tdx.QA_SU_save_etf_list exception!")
        pass


def QA_SU_save_stock_block(client=DATABASE, ui_log=None, ui_progress=None):
    """save stock_block

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    client.drop_collection('stock_block')
    coll = client.stock_block
    coll.create_index('code')

    try:
        QA_util_log_info(
            '##JOB09 Now Saving STOCK_BlOCK ====',
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=5000
        )
        coll.insert_many(
            QA_util_to_json_from_pandas(QA_fetch_get_stock_block('tdx'))
        )
        QA_util_log_info(
            'tdx Block ====',
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=5000
        )

        # ????todo fixhere here ???????????????????????? ????????????tdx???
        coll.insert_many(
            QA_util_to_json_from_pandas(QA_fetch_get_stock_block('ths'))
        )
        QA_util_log_info(
            'ths Block ====',
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=8000
        )

        # tushare ????????????????????????500???????????????????????????500?????? ????????????
        coll.insert_many(
            QA_util_to_json_from_pandas(QA_fetch_get_stock_block('tushare'))
        )
        QA_util_log_info(
            'tushare Block ====',
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=9000
        )

        QA_util_log_info(
            '????????????????????????=',
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=10000
        )

        coll.insert_many(
            QA_util_to_json_from_pandas(QA_fetch_get_stock_block('QA'))
        )
        QA_util_log_info(
            'QA_Select Block ====',
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=8000
        )

        QA_util_log_info(
            '????????????????????????=',
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=10000
        )
    except Exception as e:
        QA_util_log_info(e, ui_log=ui_log)
        print(" Error save_tdx.QA_SU_save_stock_block exception!")
        pass


def QA_SU_save_stock_info(client=DATABASE, ui_log=None, ui_progress=None):
    """save stock_info

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    client.drop_collection('stock_info')
    stock_list = QA_fetch_get_stock_list().code.unique().tolist()
    coll = client.stock_info
    coll.create_index('code')
    err = []

    def __saving_work(code, coll):
        QA_util_log_info(
            '##JOB10 Now Saving STOCK INFO ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:
            coll.insert_many(
                QA_util_to_json_from_pandas(QA_fetch_get_stock_info(str(code)))
            )

        except:
            err.append(str(code))

    for i_ in range(len(stock_list)):
        # __saving_work('000001')

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(i_ / len(stock_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(i_ / len(stock_list) * 10000.0))
        QA_util_log_info('The {} of Total {}'.format(i_, len(stock_list)))
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )

        __saving_work(stock_list[i_], coll)
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_stock_transaction(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    """save stock_transaction

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    stock_list = QA_fetch_get_stock_list().code.unique().tolist()
    coll = client.stock_transaction
    coll.create_index(
        [
            ('code',
             pymongo.ASCENDING),
            ('time_stamp',
             pymongo.ASCENDING),
            ('date_stamp',
             pymongo.ASCENDING)
        ]
    )
    err = []

    def __saving_work(code):
        QA_util_log_info(
            '##JOB11 Now Saving STOCK_TRANSACTION ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:
            coll.insert_many(
                QA_util_to_json_from_pandas(
                    # ????todo  str(stock_list[code]) ???????????????
                    QA_fetch_get_stock_transaction(
                        str(code),
                        '2019-01-01',
                        str(now_time())[0:10]
                    )
                )
            )
        except:
            err.append(str(code))

    for i_ in range(len(stock_list)):
        # __saving_work('000001')
        QA_util_log_info(
            'The {} of Total {}'.format(i_,
                                        len(stock_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(i_ / len(stock_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(i_ / len(stock_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        __saving_work(stock_list[i_])
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_index_transaction(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    """save index_transaction
    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    index_list = QA_fetch_get_index_list().code.unique().tolist()
    coll = client.index_transaction
    coll.create_index(
        [
            ('code',
             pymongo.ASCENDING),
            ('time_stamp',
             pymongo.ASCENDING),
            ('date_stamp',
             pymongo.ASCENDING)
        ]
    )
    err = []

    def __saving_work(code):
        QA_util_log_info(
            '##JOB11 Now Saving INDEX_TRANSACTION ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:
            coll.insert_many(
                QA_util_to_json_from_pandas(
                    # ????todo  str(stock_list[code]) ???????????????
                    QA_fetch_get_index_transaction(
                        str(code),
                        '2019-01-01',
                        str(now_time())[0:10]
                    )
                )
            )
        except:
            err.append(str(code))

    for i_ in range(len(index_list)):
        # __saving_work('000001')
        QA_util_log_info(
            'The {} of Total {}'.format(i_,
                                        len(index_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(i_ / len(index_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(i_ / len(index_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        __saving_work(index_list[i_])
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

########################################################################################################


def _save_option_commodity_ru_day(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    ##################### ru ???????????? ############################################################################
    option_ru_contract_list = QA_fetch_get_commodity_option_RU_contract_time_to_market()
    coll_option_commodity_ru_day = client.option_commodity_ru_day
    coll_option_commodity_ru_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_option_commodity_ru_day):
        try:
            QA_util_log_info(
                '##JOB12 Now Saving OPTION_DAY_COMMODITY_RU ???????????? ==== {}'.format(
                    str(code)
                ),
                ui_log=ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            ref = coll_option_commodity_ru_day.find({'code': str(code)[0:8]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']
                QA_util_log_info(
                    ' ???????????? ??????ru ???????????? ?????????????????????????????? {}'.format(start_date),
                    ui_log=ui_log
                )

                QA_util_log_info(
                    'UPDATE_OPTION_RU_DAY \n ???????????????????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    start_date0 = QA_util_get_next_day(start_date)
                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date0,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????".format(
                            start_date0,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )
                    coll_option_commodity_ru_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "^?????????????????????????????????^ {}".format(start_date),
                        ui_log=ui_log
                    )

            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_M_OPTION_DAY \n ???????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????^_^ ".format(
                            start_date,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )

                    coll_option_commodity_ru_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "*?????????????????????????????????* {}".format(start_date),
                        ui_log=ui_log
                    )

        except Exception as error0:
            print(error0)
            err.append(str(code))

    for item in range(len(option_ru_contract_list)):
        QA_util_log_info(
            'The {} of Total {}'.format(item,
                                        len(option_ru_contract_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(item / len(option_ru_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(
            float(item / len(option_ru_contract_list) * 10000.0)
        )
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )

        __saving_work(
            option_ru_contract_list[item].code,
            coll_option_commodity_ru_day
        )

    if len(err) < 1:
        QA_util_log_info('SUCCESS save option ru day ^_^ ', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def _save_option_commodity_c_day(
        client=DATABASE,
        ui_log=None,
        ui_progress=None,
):
    ##################### c  ?????? ############################################################################
    option_c_contract_list = QA_fetch_get_commodity_option_C_contract_time_to_market()


    coll_option_commodity_c_day = client.option_commodity_c_day
    coll_option_commodity_c_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_option_commodity_c_day):
        try:
            QA_util_log_info(
                '##JOB12 Now Saving OPTION_DAY_COMMODITY_C ?????? ==== {}'.format(
                    str(code)
                ),
                ui_log=ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            ref = coll_option_commodity_c_day.find({'code': str(code)[0:8]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']
                QA_util_log_info(
                    ' ???????????? ??????C ???????????? ?????????????????????????????? {}'.format(start_date),
                    ui_log=ui_log
                )

                QA_util_log_info(
                    'UPDATE_OPTION_C_DAY \n ???????????????????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    start_date0 = QA_util_get_next_day(start_date)
                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date0,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????".format(
                            start_date0,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )
                    coll_option_commodity_c_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "^?????????????????????????????????^ {}".format(start_date),
                        ui_log=ui_log
                    )

            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_C_OPTION_DAY \n ???????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????^_^ ".format(
                            start_date,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )

                    coll_option_commodity_c_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "*?????????????????????????????????* {}".format(start_date),
                        ui_log=ui_log
                    )

        except Exception as error0:
            print(error0)
            err.append(str(code))

    for item in range(len(option_c_contract_list)):
        QA_util_log_info(
            'The {} of Total {}'.format(item,
                                        len(option_c_contract_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(item / len(option_c_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(
            float(item / len(option_c_contract_list) * 10000.0)
        )
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )

        __saving_work(
            option_c_contract_list[item].code,
            coll_option_commodity_c_day
        )

    if len(err) < 1:
        QA_util_log_info('SUCCESS save option ru day ^_^ ', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def _save_option_commodity_cf_day(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    ##################### cf  ?????? ############################################################################
    option_cf_contract_list = QA_fetch_get_commodity_option_CF_contract_time_to_market()
    coll_option_commodity_cf_day = client.option_commodity_cf_day
    coll_option_commodity_cf_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_option_commodity_cf_day):
        try:
            QA_util_log_info(
                '##JOB12 Now Saving OPTION_DAY_COMMODITY_CF ?????? ==== {}'.format(
                    str(code)
                ),
                ui_log=ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            ref = coll_option_commodity_cf_day.find({'code': str(code)[0:8]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']
                QA_util_log_info(
                    ' ???????????? ??????ru ???????????? ?????????????????????????????? {}'.format(start_date),
                    ui_log=ui_log
                )

                QA_util_log_info(
                    'UPDATE_OPTION_CF_DAY \n ???????????????????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    start_date0 = QA_util_get_next_day(start_date)
                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date0,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????".format(
                            start_date0,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )
                    coll_option_commodity_cf_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "^?????????????????????????????????^ {}".format(start_date),
                        ui_log=ui_log
                    )

            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_M_OPTION_DAY \n ???????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????^_^ ".format(
                            start_date,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )

                    coll_option_commodity_cf_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "*?????????????????????????????????* {}".format(start_date),
                        ui_log=ui_log
                    )

        except Exception as error0:
            print(error0)
            err.append(str(code))

    for item in range(len(option_cf_contract_list)):
        QA_util_log_info(
            'The {} of Total {}'.format(item,
                                        len(option_cf_contract_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(item / len(option_cf_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(
            float(item / len(option_cf_contract_list) * 10000.0)
        )
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )

        __saving_work(
            option_cf_contract_list[item].code,
            coll_option_commodity_cf_day
        )

    if len(err) < 1:
        QA_util_log_info('SUCCESS save option ru day ^_^ ', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def _save_option_commodity_sr_day(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    ##################### sr ?????? ############################################################################
    option_sr_contract_list = QA_fetch_get_commodity_option_SR_contract_time_to_market(
    )
    coll_option_commodity_sr_day = client.option_commodity_sr_day
    coll_option_commodity_sr_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_option_commodity_sr_day):
        try:
            QA_util_log_info(
                '##JOB12 Now Saving OPTION_DAY_COMMODITY_SR ?????? ==== {}'.format(
                    str(code)
                ),
                ui_log=ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            ref = coll_option_commodity_sr_day.find({'code': str(code)[0:8]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']
                QA_util_log_info(
                    ' ??????????????????sr???????????????????????????????????? {}'.format(start_date),
                    ui_log=ui_log
                )

                QA_util_log_info(
                    'UPDATE_OPTION_M_DAY \n ???????????????????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    start_date0 = QA_util_get_next_day(start_date)
                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date0,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????".format(
                            start_date0,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )
                    coll_option_commodity_sr_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "^?????????????????????????????????^ {}".format(start_date),
                        ui_log=ui_log
                    )

            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_M_OPTION_DAY \n ???????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????^_^ ".format(
                            start_date,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )

                    coll_option_commodity_sr_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "*?????????????????????????????????* {}".format(start_date),
                        ui_log=ui_log
                    )

        except Exception as error0:
            print(error0)
            err.append(str(code))

    for item in range(len(option_sr_contract_list)):
        QA_util_log_info(
            'The {} of Total {}'.format(item,
                                        len(option_sr_contract_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(item / len(option_sr_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(
            float(item / len(option_sr_contract_list) * 10000.0)
        )
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )

        __saving_work(
            option_sr_contract_list[item].code,
            coll_option_commodity_sr_day
        )

    if len(err) < 1:
        QA_util_log_info('SUCCESS save option sr day ^_^ ', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def _save_option_commodity_m_day(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    ##################### M ?????? ############################################################################
    option_m_contract_list = QA_fetch_get_commodity_option_M_contract_time_to_market(
    )
    coll_option_commodity_m_day = client.option_commodity_m_day
    coll_option_commodity_m_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_option_commodity_m_day):
        try:
            QA_util_log_info(
                '##JOB12 Now Saving OPTION_DAY_COMMODITY_M ?????? ==== {}'.format(
                    str(code)
                ),
                ui_log=ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            # M XXXXXX ????????????

            ref = coll_option_commodity_m_day.find({'code': str(code)[0:8]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']
                QA_util_log_info(
                    ' ??????????????????M???????????????????????????????????? {}'.format(start_date),
                    ui_log=ui_log
                )

                QA_util_log_info(
                    'UPDATE_OPTION_M_DAY \n ???????????????????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    start_date0 = QA_util_get_next_day(start_date)
                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date0,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????".format(
                            start_date0,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )
                    coll_option_commodity_m_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "^?????????????????????????????????^ {}".format(start_date),
                        ui_log=ui_log
                    )

            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_M_OPTION_DAY \n ???????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????^_^ ".format(
                            start_date,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )

                    coll_option_commodity_m_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "*?????????????????????????????????* {}".format(start_date),
                        ui_log=ui_log
                    )

        except Exception as error0:
            print(error0)
            err.append(str(code))

    for item in range(len(option_m_contract_list)):
        QA_util_log_info(
            'The {} of Total {}'.format(item,
                                        len(option_m_contract_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(item / len(option_m_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(
            float(item / len(option_m_contract_list) * 10000.0)
        )
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )

        __saving_work(
            option_m_contract_list[item].code,
            coll_option_commodity_m_day
        )

    if len(err) < 1:
        QA_util_log_info('SUCCESS save option m day ^_^ ', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def _save_option_commodity_al_day(client=DATABASE,ui_log=None,ui_progress=None):

    ##################### Al ??? ############################################################################

    option_al_contract_list = QA_fetch_get_commodity_option_AL_contract_time_to_market()

    coll_option_commodity_al_day = client.option_commodity_al_day

    coll_option_commodity_al_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_option_commodity_al_day):
        try:
            QA_util_log_info(
                '##JOB13 Now Saving OPTION_DAY_COMMODITY_AL ??? ==== {}'.format(
                    str(code)
                ),
                ui_log=ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            # ???????????? ??? 10000001 ????????????  10001228
            ref = coll_option_commodity_al_day.find({'code': str(code)[0:8]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']
                QA_util_log_info(
                    ' ??????????????????AU?????????????????????????????? {}'.format(start_date),
                    ui_log=ui_log
                )

                QA_util_log_info(
                    'UPDATE_OPTION_AU_DAY \n ???????????????????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    start_date0 = QA_util_get_next_day(start_date)
                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date0,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????".format(
                            start_date0,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )
                    coll_option_commodity_al_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "^?????????????????????????????????^ {}".format(start_date),
                        ui_log=ui_log
                    )

            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_AU_OPTION_DAY \n ???????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????^_^ ".format(
                            start_date,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )

                    coll_option_commodity_al_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "*?????????????????????????????????* {}".format(start_date),
                        ui_log=ui_log
                    )

        except Exception as error0:
            print(error0)
            err.append(str(code))

    for item in range(len(option_al_contract_list)):
        QA_util_log_info(
            'The {} of Total {}'.format(item, len(option_al_contract_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(item / len(option_al_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(
            float(item / len(option_al_contract_list) * 10000.0)
        )
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )

        __saving_work(
            option_al_contract_list[item].code,
            coll_option_commodity_al_day
        )

    if len(err) < 1:
        QA_util_log_info('SUCCESS save option au day ^_^ ', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)




def _save_option_commodity_cu_day(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    ##################### CU ??? ############################################################################
    option_cu_contract_list = QA_fetch_get_commodity_option_CU_contract_time_to_market(
    )
    coll_option_commodity_cu_day = client.option_commodity_cu_day
    coll_option_commodity_cu_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_option_commodity_cu_day):
        try:
            QA_util_log_info(
                '##JOB12 Now Saving OPTION_DAY_COMMODITY_CU ??? ==== {}'.format(
                    str(code)
                ),
                ui_log=ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            # ???????????? ??? 10000001 ????????????  10001228
            ref = coll_option_commodity_cu_day.find({'code': str(code)[0:8]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']
                QA_util_log_info(
                    ' ??????????????????CU?????????????????????????????? {}'.format(start_date),
                    ui_log=ui_log
                )

                QA_util_log_info(
                    'UPDATE_OPTION_CU_DAY \n ???????????????????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    start_date0 = QA_util_get_next_day(start_date)
                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date0,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????".format(
                            start_date0,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )
                    coll_option_commodity_cu_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "^?????????????????????????????????^ {}".format(start_date),
                        ui_log=ui_log
                    )

            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_CU_OPTION_DAY \n ???????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????^_^ ".format(
                            start_date,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )

                    coll_option_commodity_cu_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "*?????????????????????????????????* {}".format(start_date),
                        ui_log=ui_log
                    )

        except Exception as error0:
            print(error0)
            err.append(str(code))

    for item in range(len(option_cu_contract_list)):
        QA_util_log_info(
            'The {} of Total {}'.format(item,
                                        len(option_cu_contract_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(item / len(option_cu_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(
            float(item / len(option_cu_contract_list) * 10000.0)
        )
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )

        __saving_work(
            option_cu_contract_list[item].code,
            coll_option_commodity_cu_day
        )

    if len(err) < 1:
        QA_util_log_info('SUCCESS save option cu day ^_^ ', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def _save_option_commodity_au_day(client=DATABASE,ui_log=None,ui_progress=None):
    ##################### Au ??? ############################################################################
    option_au_contract_list = QA_fetch_get_commodity_option_AU_contract_time_to_market()

    coll_option_commodity_au_day = client.option_commodity_au_day

    coll_option_commodity_au_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_option_commodity_au_day):
        try:
            QA_util_log_info(
                '##JOB13 Now Saving OPTION_DAY_COMMODITY_AU ??? ==== {}'.format(
                    str(code)
                ),
                ui_log=ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            # ???????????? ??? 10000001 ????????????  10001228
            ref = coll_option_commodity_au_day.find({'code': str(code)[0:8]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']
                QA_util_log_info(
                    ' ??????????????????AU?????????????????????????????? {}'.format(start_date),
                    ui_log=ui_log
                )

                QA_util_log_info(
                    'UPDATE_OPTION_AU_DAY \n ???????????????????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    start_date0 = QA_util_get_next_day(start_date)
                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date0,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????".format(
                            start_date0,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )
                    coll_option_commodity_au_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "^?????????????????????????????????^ {}".format(start_date),
                        ui_log=ui_log
                    )

            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_AU_OPTION_DAY \n ???????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????^_^ ".format(
                            start_date,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )

                    coll_option_commodity_au_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "*?????????????????????????????????* {}".format(start_date),
                        ui_log=ui_log
                    )

        except Exception as error0:
            print(error0)
            err.append(str(code))

    for item in range(len(option_au_contract_list)):
        QA_util_log_info(
            'The {} of Total {}'.format(item,
                                        len(option_au_contract_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(item / len(option_au_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(
            float(item / len(option_au_contract_list) * 10000.0)
        )
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )

        __saving_work(
            option_au_contract_list[item].code,
            coll_option_commodity_au_day
        )

    if len(err) < 1:
        QA_util_log_info('SUCCESS save option au day ^_^ ', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_option_commodity_day(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    '''
        :param client:
        :return:
    '''

    _save_option_commodity_cu_day(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress,
    )
    _save_option_commodity_m_day(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress
    )
    _save_option_commodity_sr_day(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress
    )

    _save_option_commodity_ru_day(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress
    )
    _save_option_commodity_cf_day(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress
    )
    _save_option_commodity_c_day(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress
    )

    _save_option_commodity_au_day(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress
    )

    _save_option_commodity_al_day(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress
    )


'''
???????????????
todo: ?????????????????? ??? ?????????????????????????????????
'''


def _save_option_commodity_ru_min(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    '''

    :param client:
    :param ui_log:
    :param ui_progress:
    :return:
    '''
    '''
        :param client:
        :return:
        '''
    option_contract_list = QA_fetch_get_commodity_option_C_contract_time_to_market()
    coll_option_min = client.option_commodity_ru_min
    coll_option_min.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    # ?????? code

    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB13 Now Saving Option RU ?????? MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:8], 'type': type})

                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Option RU ???????????? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ??????????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB13.{} Now Option RU ???????????? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(
            __saving_work,
            option_contract_list[i_]["code"],
            coll_option_min
        )
        for i_ in range(len(option_contract_list))
    }  # multi index ./.
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(option_contract_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(option_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(option_contract_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

    pass


def _save_option_commodity_c_min(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    '''

    :param client:
    :param ui_log:
    :param ui_progress:
    :return:
    '''
    '''
        :param client:
        :return:
        '''
    option_contract_list = QA_fetch_get_commodity_option_C_contract_time_to_market()
    coll_option_min = client.option_commodity_c_min
    coll_option_min.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    # ?????? code

    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB13 Now Saving Option C ?????? MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:8], 'type': type})

                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Option C ?????? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ??????????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB13.{} Now Option C ?????? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(
            __saving_work,
            option_contract_list[i_]["code"],
            coll_option_min
        )
        for i_ in range(len(option_contract_list))
    }  # multi index ./.
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(option_contract_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(option_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(option_contract_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

    pass


def _save_option_commodity_cf_min(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    '''

    :param client:
    :param ui_log:
    :param ui_progress:
    :return:
    '''
    '''
        :param client:
        :return:
        '''
    option_contract_list = QA_fetch_get_commodity_option_CF_contract_time_to_market()
    coll_option_min = client.option_commodity_cf_min
    coll_option_min.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    # ?????? code

    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB13 Now Saving Option CF ?????? MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:8], 'type': type})

                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Option CF ?????? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ??????????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB13.{} Now Option CF ?????? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(
            __saving_work,
            option_contract_list[i_]["code"],
            coll_option_min
        )
        for i_ in range(len(option_contract_list))
    }  # multi index ./.
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(option_contract_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(option_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(option_contract_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

    pass


def _save_option_commodity_ru_min(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    '''

    :param client:
    :param ui_log:
    :param ui_progress:
    :return:
    '''
    '''
        :param client:
        :return:
        '''
    option_contract_list = QA_fetch_get_commodity_option_RU_contract_time_to_market(
    )
    coll_option_min = client.option_commodity_ru_min
    coll_option_min.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    # ?????? code

    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB13 Now Saving Option RU ???????????? MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:8], 'type': type})

                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Option RU ???????????? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ??????????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB13.{} Now Option RU ???????????? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(
            __saving_work,
            option_contract_list[i_]["code"],
            coll_option_min
        )
        for i_ in range(len(option_contract_list))
    }  # multi index ./.
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(option_contract_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(option_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(option_contract_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

    pass


def _save_option_commodity_cu_min(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    '''

    :param client:
    :param ui_log:
    :param ui_progress:
    :return:
    '''
    '''
        :param client:
        :return:
        '''
    option_contract_list = QA_fetch_get_commodity_option_CU_contract_time_to_market(
    )
    coll_option_min = client.option_commodity_cu_min
    coll_option_min.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    # ?????? code

    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB13 Now Saving Option CU ??? MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:8], 'type': type})

                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Option CU ??? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ??????????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB13.{} Now Option CU ??? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(
            __saving_work,
            option_contract_list[i_]["code"],
            coll_option_min
        )
        for i_ in range(len(option_contract_list))
    }  # multi index ./.
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(option_contract_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(option_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(option_contract_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

    pass




def _save_option_commodity_au_min(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    '''

    :param client:
    :param ui_log:
    :param ui_progress:
    :return:
    '''
    '''
        :param client:
        :return:
        '''
    option_contract_list = QA_fetch_get_commodity_option_AU_contract_time_to_market(
    )
    coll_option_min = client.option_commodity_au_min
    coll_option_min.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    # ?????? code

    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB13 Now Saving Option AU ??? MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:8], 'type': type})

                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Option AU ??? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ??????????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB13.{} Now Option AU ??? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(
            __saving_work,
            option_contract_list[i_]["code"],
            coll_option_min
        )
        for i_ in range(len(option_contract_list))
    }  # multi index ./.
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(option_contract_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(option_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(option_contract_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

    pass



def _save_option_commodity_al_min(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    '''

    :param client:
    :param ui_log:
    :param ui_progress:
    :return:
    '''
    '''
        :param client:
        :return:
        '''
    option_contract_list = QA_fetch_get_commodity_option_AL_contract_time_to_market()
    coll_option_min = client.option_commodity_al_min
    coll_option_min.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    # ?????? code

    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB20 Now Saving Option AL ??? MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:8], 'type': type})

                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB20.{} Now Saving Option AL ??? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ??????????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB20.{} Now Option AL ??? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(
            __saving_work,
            option_contract_list[i_]["code"],
            coll_option_min
        )
        for i_ in range(len(option_contract_list))
    }  # multi index ./.
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(option_contract_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(option_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(option_contract_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

    pass


def _save_option_commodity_sr_min(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    '''

    :param client:
    :param ui_log:
    :param ui_progress:
    :return:
    '''
    '''
        :param client:
        :return:
        '''
    option_contract_list = QA_fetch_get_commodity_option_SR_contract_time_to_market(
    )
    coll_option_min = client.option_commodity_sr_min
    coll_option_min.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    # ?????? code

    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB13 Now Saving Option SR ?????? ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:8], 'type': type})

                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Option SR ?????? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ??????????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB13.{} Now Option SR ?????? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(
            __saving_work,
            option_contract_list[i_]["code"],
            coll_option_min
        )
        for i_ in range(len(option_contract_list))
    }  # multi index ./.
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(option_contract_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(option_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(option_contract_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

    pass


def _save_option_commodity_m_min(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    '''

    :param client:
    :param ui_log:
    :param ui_progress:
    :return:
    '''

    option_contract_list = QA_fetch_get_commodity_option_M_contract_time_to_market(
    )
    coll_option_min = client.option_commodity_m_min
    coll_option_min.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    # ?????? code

    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB13 Now Saving Option M ?????? ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:8], 'type': type})

                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Option M ??????  {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ??????????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB13.{} Now Option M ?????? {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(
            __saving_work,
            option_contract_list[i_]["code"],
            coll_option_min
        )
        for i_ in range(len(option_contract_list))
    }  # multi index ./.
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(option_contract_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(option_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(option_contract_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

    pass


def QA_SU_save_option_commodity_min(
        client=DATABASE,
        ui_log=None,
        ui_progress=None
):
    '''
        :param client:
        :return:
    '''
    # ?????????????????? ??????????????????????????????????????????????????????????????? ???????????????ip???????????? ???

    _save_option_commodity_cu_min(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress
    )
    _save_option_commodity_sr_min(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress
    )
    _save_option_commodity_m_min(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress
    )

    _save_option_commodity_ru_min(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress
    )

    _save_option_commodity_cf_min(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress
    )

    _save_option_commodity_c_min(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress
    )

    _save_option_commodity_au_min(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress
    )

    _save_option_commodity_al_min(
        client=client,
        ui_log=ui_log,
        ui_progress=ui_progress
    )

def QA_SU_save_option_50etf_min(client=DATABASE, ui_log=None, ui_progress=None):
    '''
    :param client:
    :return:
    '''
    option_contract_list = QA_fetch_get_option_50etf_contract_time_to_market()
    coll_option_min = client.option_day_min
    coll_option_min.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    # ?????? code

    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB13 Now Saving Option 50ETF MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:8], 'type': type})

                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Option 50ETF {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ??????????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB13.{} Now Option 50ETF {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(
            __saving_work,
            option_contract_list[i_]["code"],
            coll_option_min
        )
        for i_ in range(len(option_contract_list))
    }  # multi index ./.
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(option_contract_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(option_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(option_contract_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_option_50etf_day(client=DATABASE, ui_log=None, ui_progress=None):
    '''
    :param client:
    :return:
    '''
    option_contract_list = QA_fetch_get_option_50etf_contract_time_to_market()
    coll_option_day = client.option_day
    coll_option_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    # ?????? code

    def __saving_work(code, coll_option_day):
        try:
            QA_util_log_info(
                '##JOB12 Now Saving OPTION_DAY==== {}'.format(str(code)),
                ui_log=ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            # ???????????? ??? 10000001 ????????????  10001228
            ref = coll_option_day.find({'code': str(code)[0:8]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']
                QA_util_log_info(
                    ' ???????????????????????????????????????????????? {}'.format(start_date),
                    ui_log=ui_log
                )

                QA_util_log_info(
                    'UPDATE_OPTION_DAY \n ???????????????????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    start_date0 = QA_util_get_next_day(start_date)
                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date0,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????".format(
                            start_date0,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )
                    coll_option_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "^?????????????????????????????????^ {}".format(start_date),
                        ui_log=ui_log
                    )

            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_OPTION_DAY \n ???????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????^_^ ".format(
                            start_date,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )

                    coll_option_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "*?????????????????????????????????* {}".format(start_date),
                        ui_log=ui_log
                    )

        except Exception as error0:
            print(error0)
            err.append(str(code))

    for item in range(len(option_contract_list)):
        QA_util_log_info(
            'The {} of Total {}'.format(item,
                                        len(option_contract_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(item / len(option_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(item / len(option_contract_list) * 10000.0))
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )

        __saving_work(option_contract_list[item].code, coll_option_day)

    if len(err) < 1:
        QA_util_log_info('SUCCESS save option day ^_^ ', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)




def QA_SU_save_option_300etf_min(client=DATABASE, ui_log=None, ui_progress=None):
    '''
    :param client:
    :return:
    '''
    option_contract_list = QA_fetch_get_option_300etf_contract_time_to_market()
    coll_option_min = client.option_day_min
    coll_option_min.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    # ?????? code

    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB13 Now Saving Option shanghai sse 300 ETF MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:8], 'type': type})

                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Option shanghai 300ETF {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ??????????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB13.{} Now Option shanghai sse 300ETF {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(
            __saving_work,
            option_contract_list[i_]["code"],
            coll_option_min
        )
        for i_ in range(len(option_contract_list))
    }  # multi index ./.
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(option_contract_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(option_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(option_contract_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_option_300etf_day(client=DATABASE, ui_log=None, ui_progress=None):
    '''
    :param client:
    :return:
    '''
    option_contract_list = QA_fetch_get_option_300etf_contract_time_to_market()
    coll_option_day = client.option_day
    coll_option_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    # ?????? code

    def __saving_work(code, coll_option_day):
        try:
            QA_util_log_info(
                '##JOB12 Now Saving shanghai sse 300 etf OPTION_DAY==== {}'.format(str(code)),
                ui_log=ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            # ???????????? ??? 10000001 ????????????  10001228
            ref = coll_option_day.find({'code': str(code)[0:8]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']
                QA_util_log_info(
                    ' ???????????????????????????????????????????????? {}'.format(start_date),
                    ui_log=ui_log
                )

                QA_util_log_info(
                    'UPDATE_OPTION_DAY shanghai sse 300 etf \n ???????????????????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    start_date0 = QA_util_get_next_day(start_date)
                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date0,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????".format(
                            start_date0,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )
                    coll_option_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "^?????????????????????????????????^ {}".format(start_date),
                        ui_log=ui_log
                    )

            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_OPTION_DAY shanghai sse 300 etf \n ???????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????^_^ ".format(
                            start_date,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )

                    coll_option_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "*?????????????????????????????????* {}".format(start_date),
                        ui_log=ui_log
                    )

        except Exception as error0:
            print(error0)
            err.append(str(code))

    for item in range(len(option_contract_list)):
        QA_util_log_info(
            'The {} of Total {}'.format(item,
                                        len(option_contract_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(item / len(option_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(item / len(option_contract_list) * 10000.0))
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )

        __saving_work(option_contract_list[item].code, coll_option_day)

    if len(err) < 1:
        QA_util_log_info('SUCCESS save option day ^_^ ', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)



def QA_SU_save_option_contract_list(
        client=DATABASE,
        ui_log=None,
        ui_progress=None):
    rows_of_option = QA_fetch_get_option_all_contract_time_to_market()
    # rows_cu = QA_fetch_get_commodity_option_CU_contract_time_to_market()
    # rows_m = QA_fetch_get_commodity_option_M_contract_time_to_market()
    # rows_sr = QA_fetch_get_commodity_option_SR_contract_time_to_market()
    # rows_cf = QA_fetch_get_commodity_option_CF_contract_time_to_market()
    # rows_ru = QA_fetch_get_commodity_option_RU_contract_time_to_market()
    # rows_c = QA_fetch_get_commodity_option_C_contract_time_to_market()

    try:
        # ????todo ?????????????????????????????? JOB01??? ???????????????????????????
        QA_util_log_info(
            '##JOB15 Now Saving OPTION_CONTRACT_LIST ====',
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=5000
        )

        coll = client.option_contract_list
        coll.create_index([('desc', pymongo.ASCENDING)], unique=True)

        # todo fixhere
        # from_items is deprecated. Please use DataFrame.from_dict(dict(items), ...) instead. DataFrame.from_dict

        try:

            df = pd.DataFrame.from_items([(s.desc, s) for s in rows_of_option])
            df = (df.T)
            js = QA_util_to_json_from_pandas(df)

            # result0 = coll.insert_many(js)
            for a_js_row in js:
                # print(a_js_row)
                akey = a_js_row['desc']
                id0 = coll.find_one({'desc': akey})
                if id0 is None:
                    coll.insert(a_js_row)

            # print(result0)

        except pymongo.errors.BulkWriteError as e:
            # https://ask.helplib.com/python/post_12740530
            panic = filter(
                lambda x: x['code'] != 11000,
                e.details['writeErrors']
            )
            # if len(panic) > 0:
            #     print
            #     "really panic"

        QA_util_log_info(
            "????????????????????????",
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=10000
        )
    except Exception as e:
        QA_util_log_info(e, ui_log=ui_log)
        print(" Error save_tdx.QA_SU_save_option_contract_list exception!")


def QA_SU_save_option_day_all(client=DATABASE,ui_log=None,ui_progress=None):
    option_contract_list = QA_fetch_get_option_all_contract_time_to_market()
    coll_option_day = client.option_day_all
    coll_option_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    # ?????? code

    def __saving_work(code, coll_option_day):
        try:
            QA_util_log_info(
                '##JOB12 Now Saving OPTION_DAY ALL ==== {}'.format(str(code)),
                ui_log=ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            # ???????????? ??? 10000001 ????????????  10001228
            ref = coll_option_day.find({'code': str(code)[0:8]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']
                QA_util_log_info(
                    ' ???????????????????????????????????????????????? {}'.format(start_date),
                    ui_log=ui_log
                )

                QA_util_log_info(
                    'UPDATE_OPTION_DAY \n ???????????????????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    start_date0 = QA_util_get_next_day(start_date)
                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date0,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????".format(
                            start_date0,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )
                    coll_option_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "^?????????????????????????????????^ {}".format(start_date),
                        ui_log=ui_log
                    )

            else:
                start_date = '1990-01-01'
                QA_util_log_info(
                    'UPDATE_OPTION_DAY \n ???????????????????????? Trying update {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log=ui_log
                )
                if start_date != end_date:

                    df0 = QA_fetch_get_option_day(
                        code=code,
                        start_date=start_date,
                        end_date=end_date,
                        frequence='day',
                        ip=None,
                        port=None
                    )
                    retCount = df0.iloc[:, 0].size
                    QA_util_log_info(
                        "???????????????{}-??????{} , ????????????{} , ?????????{}????????? , ?????????????????????^_^ ".format(
                            start_date,
                            end_date,
                            code,
                            retCount
                        ),
                        ui_log=ui_log
                    )

                    coll_option_day.insert_many(
                        QA_util_to_json_from_pandas(df0)
                    )
                else:
                    QA_util_log_info(
                        "*?????????????????????????????????* {}".format(start_date),
                        ui_log=ui_log
                    )

        except Exception as error0:
            print(error0)
            err.append(str(code))

    for item in range(len(option_contract_list)):
        QA_util_log_info(
            'The {} of Total {}'.format(item,
                                        len(option_contract_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(item / len(option_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(item / len(option_contract_list) * 10000.0))
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )

        __saving_work(option_contract_list[item].code, coll_option_day)

    if len(err) < 1:
        QA_util_log_info('SUCCESS save option day all contract ^_^ ', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)






def QA_SU_save_option_min_all(client=DATABASE, ui_log=None, ui_progress=None):
    '''
    :param client:
    :return:
    '''
    option_contract_list = QA_fetch_get_option_all_contract_time_to_market()
    coll_option_min = client.option_min_all
    coll_option_min.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    # ?????? code

    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB15 Now Saving Option ALL MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:8], 'type': type})

                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB99.{} Now Saving Option ALL MIN {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ??????????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB15.{} Now Option ALL MIN {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            QA_util_log_info(
                                " ?????? ????????????????????? {} ".format(len(__data))
                            )
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(
            __saving_work,
            option_contract_list[i_]["code"],
            coll_option_min
        )
        for i_ in range(len(option_contract_list))
    }  # multi index ./.
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(option_contract_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(option_contract_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(option_contract_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


#######################################################################################

def QA_SU_save_future_list(client=DATABASE, ui_log=None, ui_progress=None):
    future_list = QA_fetch_get_future_list()
    coll_future_list = client.future_list
    coll_future_list.create_index("code", unique=True)
    try:
        coll_future_list.insert_many(
            QA_util_to_json_from_pandas(future_list),
            ordered=False
        )
    except:
        pass


def QA_SU_save_index_list(client=DATABASE, ui_log=None, ui_progress=None):
    index_list = QA_fetch_get_index_list()
    coll_index_list = client.index_list
    coll_index_list.create_index("code", unique=True)

    try:
        coll_index_list.insert_many(
            QA_util_to_json_from_pandas(index_list),
            ordered=False
        )
    except:
        pass

def QA_SU_save_single_future_day(code : str, client=DATABASE, ui_log=None, ui_progress=None):
    '''
     save single_future_day
    ????????????????????????????????????
    :param client:
    :param ui_log:  ???GUI qt ????????????
    :param ui_progress: ???GUI qt ????????????
    :param ui_progress_int_value: ???GUI qt ????????????
    :return:
    '''
    coll_future_day = client.future_day
    coll_future_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_future_day):
        try:
            QA_util_log_info(
                '##JOB12 Now Saving Future_DAY==== {}'.format(str(code)),
                ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            ref = coll_future_day.find({'code': str(code)[0:4]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ??????????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']

                QA_util_log_info(
                    'UPDATE_Future_DAY \n Trying updating {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log
                )
                if start_date != end_date:
                    coll_future_day.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_future_day(
                                str(code),
                                QA_util_get_next_day(start_date),
                                end_date
                            )
                        )
                    )

            # ?????????????????????????????????????????????????????? ???1990-01-01 ???????????????????????????
            else:
                start_date = '2001-01-01'
                QA_util_log_info(
                    'UPDATE_Future_DAY \n Trying updating {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log
                )
                if start_date != end_date:
                    coll_future_day.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_future_day(
                                str(code),
                                start_date,
                                end_date
                            )
                        )
                    )
        except Exception as error0:
            print(error0)
            err.append(str(code))


    __saving_work(code, coll_future_day)

    if len(err) < 1:
        QA_util_log_info('SUCCESS save future day ^_^', ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log)
        QA_util_log_info(err, ui_log)

def QA_SU_save_future_day(client=DATABASE, ui_log=None, ui_progress=None):
    '''
     save future_day
    ??????????????????
    :param client:
    :param ui_log:  ???GUI qt ????????????
    :param ui_progress: ???GUI qt ????????????
    :param ui_progress_int_value: ???GUI qt ????????????
    :return:
    '''
    future_list = [
        item for item in QA_fetch_get_future_list().code.unique().tolist()
        if str(item)[-2:] in ['L8',
                              'L9']
    ]
    coll_future_day = client.future_day
    coll_future_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_future_day):
        try:
            QA_util_log_info(
                '##JOB12 Now Saving Future_DAY==== {}'.format(str(code)),
                ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            ref = coll_future_day.find({'code': str(code)[0:4]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ??????????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']

                QA_util_log_info(
                    'UPDATE_Future_DAY \n Trying updating {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log
                )
                if start_date != end_date:
                    coll_future_day.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_future_day(
                                str(code),
                                QA_util_get_next_day(start_date),
                                end_date
                            )
                        )
                    )

            # ?????????????????????????????????????????????????????? ???1990-01-01 ???????????????????????????
            else:
                start_date = '2001-01-01'
                QA_util_log_info(
                    'UPDATE_Future_DAY \n Trying updating {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log
                )
                if start_date != end_date:
                    coll_future_day.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_future_day(
                                str(code),
                                start_date,
                                end_date
                            )
                        )
                    )
        except Exception as error0:
            print(error0)
            err.append(str(code))

    for item in range(len(future_list)):
        QA_util_log_info('The {} of Total {}'.format(item, len(future_list)))

        strProgressToLog = 'DOWNLOAD PROGRESS {} {}'.format(
            str(float(item / len(future_list) * 100))[0:4] + '%',
            ui_log
        )
        intProgressToLog = int(float(item / len(future_list) * 100))
        QA_util_log_info(
            strProgressToLog,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intProgressToLog
        )

        __saving_work(future_list[item], coll_future_day)

    if len(err) < 1:
        QA_util_log_info('SUCCESS save future day ^_^', ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log)
        QA_util_log_info(err, ui_log)


def QA_SU_save_future_day_all(client=DATABASE, ui_log=None, ui_progress=None):
    '''
     save future_day_all
    ??????????????????(??????, ??????????????????)
    :param client:
    :param ui_log:  ???GUI qt ????????????
    :param ui_progress: ???GUI qt ????????????
    :param ui_progress_int_value: ???GUI qt ????????????
    :return:
    '''
    future_list = QA_fetch_get_future_list().code.unique().tolist()
    coll_future_day = client.future_day
    coll_future_day.create_index(
        [("code",
          pymongo.ASCENDING),
         ("date_stamp",
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll_future_day):
        try:
            QA_util_log_info(
                '##JOB12 Now Saving Future_DAY==== {}'.format(str(code)),
                ui_log
            )

            # ????????????????????? ?????? ??? ?????????????????????
            ref = coll_future_day.find({'code': str(code)[0:6]})
            end_date = str(now_time())[0:10]

            # ?????????????????????????????????????????????????????? ??????????????????
            # ??????????????????????????????????????????????????????????????? ???????????????????????? ?????????????????????????????????
            if ref.count() > 0:

                # ???????????????????????????????????????
                start_date = ref[ref.count() - 1]['date']

                QA_util_log_info(
                    'UPDATE_Future_DAY \n Trying updating {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log
                )
                if start_date != end_date:
                    coll_future_day.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_future_day(
                                str(code),
                                QA_util_get_next_day(start_date),
                                end_date
                            )
                        )
                    )

            # ?????????????????????????????????????????????????????? ???1990-01-01 ???????????????????????????
            else:
                start_date = '2001-01-01'
                QA_util_log_info(
                    'UPDATE_Future_DAY \n Trying updating {} from {} to {}'
                        .format(code,
                                start_date,
                                end_date),
                    ui_log
                )
                if start_date != end_date:
                    coll_future_day.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_future_day(
                                str(code),
                                start_date,
                                end_date
                            )
                        )
                    )
        except Exception as error0:
            print(error0)
            err.append(str(code))

    for item in range(len(future_list)):
        QA_util_log_info('The {} of Total {}'.format(item, len(future_list)))

        strProgressToLog = 'DOWNLOAD PROGRESS {} {}'.format(
            str(float(item / len(future_list) * 100))[0:4] + '%',
            ui_log
        )
        intProgressToLog = int(float(item / len(future_list) * 100))
        QA_util_log_info(
            strProgressToLog,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intProgressToLog
        )

        __saving_work(future_list[item], coll_future_day)

    if len(err) < 1:
        QA_util_log_info('SUCCESS save future day ^_^', ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log)
        QA_util_log_info(err, ui_log)

def QA_SU_save_single_future_min(code : str, client=DATABASE, ui_log=None, ui_progress=None):
    """save single_future_min

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """
    coll = client.future_min
    coll.create_index(
        [
            ('code',
             pymongo.ASCENDING),
            ('time_stamp',
             pymongo.ASCENDING),
            ('date_stamp',
             pymongo.ASCENDING)
        ]
    )
    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB13 Now Saving Future_MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:6], 'type': type})
                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Future {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Future {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    __saving_work(code, coll)
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)

def QA_SU_save_future_min(client=DATABASE, ui_log=None, ui_progress=None):
    """save future_min

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    future_list = [
        item for item in QA_fetch_get_future_list().code.unique().tolist()
        if str(item)[-2:] in ['L8',
                              'L9']
    ]
    coll = client.future_min
    coll.create_index(
        [
            ('code',
             pymongo.ASCENDING),
            ('time_stamp',
             pymongo.ASCENDING),
            ('date_stamp',
             pymongo.ASCENDING)
        ]
    )
    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB13 Now Saving Future_MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:6], 'type': type})
                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Future {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Future {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(__saving_work,
                        future_list[i_],
                        coll)
        for i_ in range(len(future_list))
    }  # multi index ./.
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(future_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(future_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(future_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_future_min_all(client=DATABASE, ui_log=None, ui_progress=None):
    """save future_min_all  (??????, ??????????????????)

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    future_list = QA_fetch_get_future_list().code.unique().tolist()
    coll = client.future_min
    coll.create_index(
        [
            ('code',
             pymongo.ASCENDING),
            ('time_stamp',
             pymongo.ASCENDING),
            ('date_stamp',
             pymongo.ASCENDING)
        ]
    )
    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB13 Now Saving Future_MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:6], 'type': type})
                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Future {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB13.{} Now Saving Future {} from {} to {} =={} '
                            .format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_future_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(__saving_work,
                        future_list[i_],
                        coll)
        for i_ in range(len(future_list))
    }  # multi index ./.
    count = 0
    for i_ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(future_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(future_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(future_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_single_bond_day(code : str, client=DATABASE, ui_log=None):
    """save bond_day

    Keyword Arguments:
        code : single bond code
        client {[type]} -- [description] (default: {DATABASE})
    """

    #__bond_list = QA_fetch_get_stock_list('bond')
    coll = client.bond_day
    coll.create_index(
        [('code',
          pymongo.ASCENDING),
         ('date_stamp',
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll):

        try:

            ref_ = coll.find({'code': str(code)[0:6]})
            end_time = str(now_time())[0:10]
            if ref_.count() > 0:
                start_time = ref_[ref_.count() - 1]['date']

                QA_util_log_info(
                    '##JOB06 Now Saving BOND_DAY==== \n Trying updating {} from {} to {}'
                        .format(code,
                                start_time,
                                end_time),
                    ui_log=ui_log
                )

                if start_time != end_time:
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_bond_day(
                                str(code),
                                QA_util_get_next_day(start_time),
                                end_time
                            )
                        )
                    )
            else:
                start_time = '1990-01-01'
                QA_util_log_info(
                    '##JOB06 Now Saving BOND_DAY==== \n Trying updating {} from {} to {}'
                        .format(code,
                                start_time,
                                end_time),
                    ui_log=ui_log
                )

                if start_time != end_time:
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_bond_day(
                                str(code),
                                start_time,
                                end_time
                            )
                        )
                    )
        except:
            err.append(str(code))

    __saving_work(code, coll)
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_bond_day(client=DATABASE, ui_log=None, ui_progress=None):
    """save bond_day

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    __bond_list = QA_fetch_get_bond_list()
    coll = client.bond_day
    coll.create_index(
        [('code',
          pymongo.ASCENDING),
         ('date_stamp',
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll):

        try:

            ref_ = coll.find({'code': str(code)[0:6]})
            end_time = str(now_time())[0:10]
            if ref_.count() > 0:
                start_time = ref_[ref_.count() - 1]['date']

                QA_util_log_info(
                    '##JOB06 Now Saving BOND_DAY==== \n Trying updating {} from {} to {}'
                        .format(code,
                                start_time,
                                end_time),
                    ui_log=ui_log
                )

                if start_time != end_time:
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_bond_day(
                                str(code),
                                QA_util_get_next_day(start_time),
                                end_time
                            )
                        )
                    )
            else:
                start_time = '1990-01-01'
                QA_util_log_info(
                    '##JOB06 Now Saving BOND_DAY==== \n Trying updating {} from {} to {}'
                        .format(code,
                                start_time,
                                end_time),
                    ui_log=ui_log
                )

                if start_time != end_time:
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_bond_day(
                                str(code),
                                start_time,
                                end_time
                            )
                        )
                    )
        except:
            err.append(str(code))

    for i_ in range(len(__bond_list)):
        # __saving_work('000001')
        QA_util_log_info(
            'The {} of Total {}'.format(i_,
                                        len(__bond_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(i_ / len(__bond_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(i_ / len(__bond_list) * 10000.0))
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )

        __saving_work(__bond_list.index[i_][0], coll)
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_bond_min(client=DATABASE, ui_log=None, ui_progress=None):
    """save bond_min

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    __bond_list = QA_fetch_get_bond_list()
    coll = client.bond_min
    coll.create_index(
        [
            ('code',
             pymongo.ASCENDING),
            ('time_stamp',
             pymongo.ASCENDING),
            ('date_stamp',
             pymongo.ASCENDING)
        ]
    )
    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB07 Now Saving BOND_MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:6], 'type': type})
                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB07.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_bond_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB07.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_bond_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(__saving_work,
                        __bond_list.index[i_][0],
                        coll)
        for i_ in range(len(__bond_list))
    }  # multi bond ./.
    count = 1
    for _ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(__bond_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(__bond_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(__bond_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_single_bond_min(code : str, client=DATABASE, ui_log=None, ui_progress=None):
    """save single bond_min

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    #__bond_list = QA_fetch_get_stock_list('bond')
    __bond_list = [code]
    coll = client.bond_min
    coll.create_index(
        [
            ('code',
             pymongo.ASCENDING),
            ('time_stamp',
             pymongo.ASCENDING),
            ('date_stamp',
             pymongo.ASCENDING)
        ]
    )
    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB07 Now Saving BOND_MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:6], 'type': type})
                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB07.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_bond_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB07.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_bond_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(__saving_work,
                        __bond_list[i_],
                        coll)
        for i_ in range(len(__bond_list))
    }  # multi bond ./.
    count = 1
    for _ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(__bond_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(__bond_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(__bond_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_bond_list(client=DATABASE, ui_log=None, ui_progress=None):
    """save bond_list

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """
    try:
        QA_util_log_info(
            '##JOB16 Now Saving BOND_LIST ====',
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=5000
        )
        bond_list_from_tdx = QA_fetch_get_bond_list()
        pandas_data = QA_util_to_json_from_pandas(bond_list_from_tdx)

        if len(pandas_data) > 0:
            # ???????????????????????????drop collection ??????
            client.drop_collection('bond_list')
            coll = client.bond_list
            coll.create_index('code')
            coll.insert_many(pandas_data)
        QA_util_log_info(
            "??????bond????????????",
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=10000
        )
    except Exception as e:
        QA_util_log_info(e, ui_log=ui_log)
        print(" Error save_tdx.QA_SU_save_bond_list exception!")
        pass

###############################################################
# HKSTOCK
###############################################################
def QA_SU_save_single_hkstock_day(code : str, client=DATABASE, ui_log=None):
    """save bond_day

    Keyword Arguments:
        code : single hkstock code
        client {[type]} -- [description] (default: {DATABASE})
    """

    #__hkstock_list = QA_fetch_get_hkstock_list()
    coll = client.hkstock_day
    coll.create_index(
        [('code',
          pymongo.ASCENDING),
         ('date_stamp',
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll):

        try:

            ref_ = coll.find({'code': str(code)[0:6]})
            end_time = str(now_time())[0:10]
            if ref_.count() > 0:
                start_time = ref_[ref_.count() - 1]['date']

                QA_util_log_info(
                    '##JOB06 Now Saving HKSTOCK_DAY==== \n Trying updating {} from {} to {}'
                        .format(code,
                                start_time,
                                end_time),
                    ui_log=ui_log
                )

                if start_time != end_time:
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_hkstock_day(
                                str(code),
                                QA_util_get_next_day(start_time),
                                end_time
                            )
                        )
                    )
            else:
                start_time = '1990-01-01'
                QA_util_log_info(
                    '##JOB06 Now Saving HKSTOCK_DAY==== \n Trying updating {} from {} to {}'
                        .format(code,
                                start_time,
                                end_time),
                    ui_log=ui_log
                )

                if start_time != end_time:
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_hkstock_day(
                                str(code),
                                start_time,
                                end_time
                            )
                        )
                    )
        except:
            err.append(str(code))

    __saving_work(code, coll)
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_hkstock_day(client=DATABASE, ui_log=None, ui_progress=None):
    """save hkstock_day

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    __hkstock_list = QA_fetch_get_hkstock_list().code.unique().tolist()
    coll = client.hkstock_day
    coll.create_index(
        [('code',
          pymongo.ASCENDING),
         ('date_stamp',
          pymongo.ASCENDING)]
    )
    err = []

    def __saving_work(code, coll):

        try:

            ref_ = coll.find({'code': str(code)[0:6]})
            end_time = str(now_time())[0:10]
            if ref_.count() > 0:
                start_time = ref_[ref_.count() - 1]['date']

                QA_util_log_info(
                    '##JOB06 Now Saving HKSTOCK_DAY==== \n Trying updating {} from {} to {}'
                        .format(code,
                                start_time,
                                end_time),
                    ui_log=ui_log
                )

                if start_time != end_time:
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_hkstock_day(
                                str(code),
                                QA_util_get_next_day(start_time),
                                end_time
                            )
                        )
                    )
            else:
                start_time = '1990-01-01'
                QA_util_log_info(
                    '##JOB06 Now Saving HKSTOCK_DAY==== \n Trying updating {} from {} to {}'
                        .format(code,
                                start_time,
                                end_time),
                    ui_log=ui_log
                )

                if start_time != end_time:
                    coll.insert_many(
                        QA_util_to_json_from_pandas(
                            QA_fetch_get_hkstock_day(
                                str(code),
                                start_time,
                                end_time
                            )
                        )
                    )
        except:
            err.append(str(code))

    for i_ in range(len(__hkstock_list)):
        # __saving_work('000001')
        QA_util_log_info(
            'The {} of Total {}'.format(i_,
                                        len(__hkstock_list)),
            ui_log=ui_log
        )

        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(i_ / len(__hkstock_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(i_ / len(__hkstock_list) * 10000.0))
        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )

        __saving_work(__hkstock_list[i_], coll)

    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_hkstock_min(client=DATABASE, ui_log=None, ui_progress=None):
    """save hkstock_min

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    __hkstock_list = QA_fetch_get_hkstock_list().code.unique().tolist()
    coll = client.hkstock_min
    coll.create_index(
        [
            ('code',
             pymongo.ASCENDING),
            ('time_stamp',
             pymongo.ASCENDING),
            ('date_stamp',
             pymongo.ASCENDING)
        ]
    )
    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB07 Now Saving HKSTOCK_MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:6], 'type': type})
                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB07.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_hkstock_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB07.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_hkstock_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(__saving_work,
                        __hkstock_list[i_],
                        coll)
        for i_ in range(len(__hkstock_list))
    }  # multi bond ./.
    count = 1
    for _ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(__hkstock_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(__hkstock_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(__hkstock_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_single_hkstock_min(code : str, client=DATABASE, ui_log=None, ui_progress=None):
    """save single hkstock_min

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """

    #__bond_list = QA_fetch_get_stock_list('bond')
    __hkstock_list = [code]
    coll = client.hkstock_min
    coll.create_index(
        [
            ('code',
             pymongo.ASCENDING),
            ('time_stamp',
             pymongo.ASCENDING),
            ('date_stamp',
             pymongo.ASCENDING)
        ]
    )
    err = []

    def __saving_work(code, coll):

        QA_util_log_info(
            '##JOB07 Now Saving HKSTOCK_MIN ==== {}'.format(str(code)),
            ui_log=ui_log
        )
        try:

            for type in ['1min', '5min', '15min', '30min', '60min']:
                ref_ = coll.find({'code': str(code)[0:6], 'type': type})
                end_time = str(now_time())[0:19]
                if ref_.count() > 0:
                    start_time = ref_[ref_.count() - 1]['datetime']

                    QA_util_log_info(
                        '##JOB07.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_hkstock_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data[1::])
                            )
                else:
                    start_time = '2015-01-01'

                    QA_util_log_info(
                        '##JOB07.{} Now Saving {} from {} to {} =={} '.format(
                            ['1min',
                             '5min',
                             '15min',
                             '30min',
                             '60min'].index(type),
                            str(code),
                            start_time,
                            end_time,
                            type
                        ),
                        ui_log=ui_log
                    )

                    if start_time != end_time:
                        __data = QA_fetch_get_hkstock_min(
                            str(code),
                            start_time,
                            end_time,
                            type
                        )
                        if len(__data) > 1:
                            coll.insert_many(
                                QA_util_to_json_from_pandas(__data)
                            )
        except:
            err.append(code)

    executor = ThreadPoolExecutor(max_workers=4)

    res = {
        executor.submit(__saving_work,
                        __hkstock_list[i_],
                        coll)
        for i_ in range(len(__hkstock_list))
    }  # multi bond ./.
    count = 1
    for _ in concurrent.futures.as_completed(res):
        QA_util_log_info(
            'The {} of Total {}'.format(count,
                                        len(__hkstock_list)),
            ui_log=ui_log
        )
        strLogProgress = 'DOWNLOAD PROGRESS {} '.format(
            str(float(count / len(__hkstock_list) * 100))[0:4] + '%'
        )
        intLogProgress = int(float(count / len(__hkstock_list) * 10000.0))

        QA_util_log_info(
            strLogProgress,
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=intLogProgress
        )
        count = count + 1
    if len(err) < 1:
        QA_util_log_info('SUCCESS', ui_log=ui_log)
    else:
        QA_util_log_info(' ERROR CODE \n ', ui_log=ui_log)
        QA_util_log_info(err, ui_log=ui_log)


def QA_SU_save_hkstock_list(client=DATABASE, ui_log=None, ui_progress=None):
    """save hkstock_list

    Keyword Arguments:
        client {[type]} -- [description] (default: {DATABASE})
    """
    try:
        QA_util_log_info(
            '##JOB16 Now Saving HKSTOCK_LIST ====',
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=5000
        )
        hkstock_list_from_tdx = QA_fetch_get_hkstock_list()
        pandas_data = QA_util_to_json_from_pandas(hkstock_list_from_tdx)

        if len(pandas_data) > 0:
            # ???????????????????????????drop collection ??????
            client.drop_collection('hkstock_list')
            coll = client.hkstock_list
            coll.create_index('code')
            coll.insert_many(pandas_data)
        QA_util_log_info(
            "??????HKSTOCK????????????",
            ui_log=ui_log,
            ui_progress=ui_progress,
            ui_progress_int_value=10000
        )
    except Exception as e:
        QA_util_log_info(e, ui_log=ui_log)
        print(" Error save_tdx.QA_SU_save_hkstock_list exception!")
        pass

if __name__ == '__main__':
    # QA_SU_save_stock_day()
    # QA_SU_save_stock_xdxr()
    # QA_SU_save_stock_min()
    # QA_SU_save_stock_transaction()
    # QA_SU_save_index_day()
    # QA_SU_save_stock_list()
    # QA_SU_save_index_min()
    # QA_SU_save_index_list()
    # QA_SU_save_future_list()

    #QA_SU_save_future_day()

    #QA_SU_save_future_min()
    QA_SU_save_hkstock_list()
    QA_SU_save_hkstock_day()
    #QA_SU_save_hkstock_min()
    #QA_SU_save_single_hkstock_min(code="00338")
