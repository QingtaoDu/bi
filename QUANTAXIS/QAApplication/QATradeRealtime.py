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

import time
from functools import lru_cache
import datetime
from QUANTAXIS.QAARP.QAPortfolio import QA_Portfolio
from QUANTAXIS.QAARP.QAUser import QA_User
from QUANTAXIS.QAEngine.QAEvent import QA_Event
from QUANTAXIS.QAFetch.QAQuery_Advance import (QA_fetch_stock_day_adv,
                                               QA_fetch_stock_min_adv)
from QUANTAXIS.QAMarket.QAMarket import QA_Market
from QUANTAXIS.QAMarket.QAShipaneBroker import QA_SPEBroker
from QUANTAXIS.QAUtil import (QA_Setting, QA_util_log_info,
                              QA_util_mongo_initial)
from QUANTAXIS.QAUtil.QAError import (QAError_database_connection,
                                      QAError_market_enging_down,
                                      QAError_web_connection)
from QUANTAXIS.QAUtil.QAParameter import (AMOUNT_MODEL, BROKER_EVENT,
                                          BROKER_TYPE, ENGINE_EVENT, FREQUENCE,
                                          MARKET_TYPE, ORDER_DIRECTION,
                                          ORDER_MODEL)
from QUANTAXIS.QAUtil.QADate_trade import QA_util_if_tradetime


class QA_RealTrade():
    def __init__(self, code, market_type, frequence, broker_name=BROKER_TYPE.SHIPANE, broker=None,):
        self.user = QA_User()
        self.if_settled = False
        self.account = None
        self.portfolio = None

        self.market = QA_Market(if_start_orderthreading=True)
        self.market_type = market_type

        self.frequence = frequence

        #self.broker = QA_SPEBroker()
        self.broker_name = broker_name

        self.ingest_data = None

    @property
    def now(self):
        return datetime.datetime.now()

    def load_account(self, account):
        # ?????? broke?????? ??????????????? QAAccount ???????????? session????????? session ??? { 'cookie' , QAAccount }
        self.market.login(self.broker_name, account.account_cookie, account)

    def start_market(self):
        """
        start the market thread and register backtest broker thread
        QAMarket ??????QATrader??? QATrader ?????? trade_engine?????? ??? trade_engine?????????QA_Engine??? QA_Thread??????
        """
        # ?????? trade_engine ??????
        self.market.start()

        # ?????? backtest_broker ?????????????????????????????????QAThread ????????? kernels ???????????? { 'broker_name': QAThread }
        #self.market.register(self.broker_name, self.broker)
        self.market.connect(self.broker_name)

    def run(self):
        """generator driven data flow
        """
        # ?????????????????????????????? ???????????????????????????
        _date = None

        while QA_util_if_tradetime(self.now):
            for data in self.ingest_data:  # ?????????ingest_data????????????
                # <class 'QUANTAXIS.QAData.QADataStruct.QA_DataStruct_Stock_day'>
                date = data.date[0]
                if self.market_type is MARKET_TYPE.STOCK_CN:  # ?????????????????????
                    if _date != date:  # ????????????date
                        # ?????????????????????????????????
                        # ??? broker ??? account ?????? settle ??????
                        try:
                            self.market.trade_engine.join()
                            # time.sleep(2)
                            self.market._settle(self.broker_name)

                        except Exception as e:
                            raise e
                # ?????? ?????? ??????
                elif self.market_type in [MARKET_TYPE.FUND_CN, MARKET_TYPE.INDEX_CN, MARKET_TYPE.FUTURE_CN]:
                    self.market._settle(self.broker_name)
                # print(data)
                self.broker.run(
                    QA_Event(event_type=ENGINE_EVENT.UPCOMING_DATA, market_data=data))
                # ?????? UPCOMING_DATA ???????????? ??????????????????

                self.market.upcoming_data(self.broker_name, data)

                self.market.trade_engine.join()

                _date = date
