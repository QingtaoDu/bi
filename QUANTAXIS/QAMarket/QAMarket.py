# coding :utf-8
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

import datetime
import time
import numpy as np
import sched
import threading

# from QUANTAXIS.QAARP.QAAccount import QA_Account
from QUANTAXIS.QAEngine.QAEvent import QA_Event
from QUANTAXIS.QAEngine.QATask import QA_Task
from QUANTAXIS.QAMarket.QABacktestBroker import QA_BacktestBroker
from QUANTAXIS.QAMarket.QAOrder import QA_Order
from QUANTAXIS.QAMarket.QAOrderHandler import QA_OrderHandler
from QUANTAXIS.QAMarket.QARandomBroker import QA_RandomBroker
from QUANTAXIS.QAMarket.QARealBroker import QA_RealBroker
from QUANTAXIS.QAMarket.QAShipaneBroker import QA_SPEBroker
from QUANTAXIS.QAMarket.QASimulatedBroker import QA_SimulatedBroker
from QUANTAXIS.QAMarket.QATTSBroker import QA_TTSBroker
from QUANTAXIS.QAMarket.QATrade import QA_Trade
from QUANTAXIS.QAUtil.QALogs import QA_util_log_info
from QUANTAXIS.QAUtil.QAParameter import (
    ACCOUNT_EVENT,
    AMOUNT_MODEL,
    ORDER_STATUS,
    BROKER_EVENT,
    BROKER_TYPE,
    ENGINE_EVENT,
    FREQUENCE,
    MARKET_EVENT,
    ORDER_EVENT,
    ORDER_MODEL,
    RUNNING_ENVIRONMENT
)
from QUANTAXIS.QAUtil.QARandom import QA_util_random_with_topic


class QA_Market(QA_Trade):
    """
    QUANTAXIS MARKET ??????

    ????????????/??????????????????broker???
    ???????????????????????????engine??????

    session ???????????? QAAccout ??????
    """

    def __init__(self, if_start_orderthreading=True, *args, **kwargs):
        """MARKET??????????????????

        Keyword Arguments:
            if_start_orderthreading {bool} -- ????????????????????????????????????????????????(????????????) (default: {False})

        @2018-08-06 change : ????????????????????????????????? market???????????? ?????????????????????
        """

        super().__init__()
        # ??????????????????????????????session
        self.session = {}
        # ???????????????????????????????????????
        self._broker = {
            BROKER_TYPE.BACKETEST: QA_BacktestBroker,
            BROKER_TYPE.RANDOM: QA_RandomBroker,
            BROKER_TYPE.REAL: QA_RealBroker,
            BROKER_TYPE.SIMULATION: QA_SimulatedBroker,
            BROKER_TYPE.SHIPANE: QA_SPEBroker,
            BROKER_TYPE.TTS: QA_TTSBroker,
        }
        self.broker = {}
        self.running_time = None
        self.last_query_data = None
        self.if_start_orderthreading = if_start_orderthreading
        self.order_handler = QA_OrderHandler()

    def __repr__(self):
        '''
        ??????market????????????????????????
        '''
        return '<QA_Market with {} QA_Broker >'.format(list(self.broker.keys()))

    def upcoming_data(self, broker, data):
        '''
        ??????????????????
        broker ????????????
        data ???????????????
        ??? QABacktest ???run ???????????? upcoming_data
        '''

        self.running_time = data.datetime[0]
        for account in self.session.values():
            account.run(QA_Event(
                event_type=ENGINE_EVENT.UPCOMING_DATA,
                # args ???????????????
                market_data=data,
                broker_name=broker,
                send_order=self.insert_order,  # ????todo insert_order = insert_order
                query_data=self.query_data_no_wait,
                query_order=self.query_order,
                query_assets=self.query_assets,
                query_trade=self.query_trade
            ))

    def start(self):
        self.trade_engine.start()
        if self.if_start_orderthreading:
            """?????????????????????
            """
            self.start_order_threading()
        print(threading.enumerate())

    def connect(self, broker):
        if broker in self._broker.keys():

            self.broker[broker] = self._broker[broker]() # ??????????????????
                                                         # 2018-08-06 change : ????????????????????????????????? market???????????? ?????????????????????
                                                         # self.trade_engine.create_kernel('{}'.format(broker), daemon=True)
                                                         # self.trade_engine.start_kernel('{}'.format(broker))

            # 2019-02-08 change: ?????? ???????????????BROKER??????????????????

            # ??????????????????????????????
            # ??????trade???????????????
            return True
        else:
            return False

    def next_tradeday(self):
        self.order_handler.run(
            QA_Event(
                event_type=BROKER_EVENT.NEXT_TRADEDAY,
                event_queue=self.trade_engine.kernels_dict['ORDER'].queue
            )
        )

    def register(self, broker_name, broker):
        if broker_name not in self._broker.keys():
            self.broker[broker_name] = broker
            # self.trade_engine.create_kernel(
            #     '{}'.format(broker_name),
            #     daemon=True
            # )
            # self.trade_engine.start_kernel('{}'.format(broker_name))
            return True
        else:
            return False

    def start_order_threading(self):
        """?????????????????????(????????????)
        """

        self.if_start_orderthreading = True

        self.order_handler.if_start_orderquery = True
        self.trade_engine.create_kernel('ORDER', daemon=True)
        self.trade_engine.start_kernel('ORDER')
        self.sync_order_and_deal()
        # self._update_orders()

    def get_account(self, account_cookie):
        try:
            return self.session[account_cookie]
        except KeyError:
            print(
                'QAMARKET: this account {} is logoff, please login and retry'
                .format(account_cookie)
            )

    def login(self, broker_name, account_cookie, account=None):
        """login ?????????????????????

        2018-07-02 ????????????,????????????????????????,????????????????????????

        Arguments:
            broker_name {[type]} -- [description]
            account_cookie {[type]} -- [description]

        Keyword Arguments:
            account {[type]} -- [description] (default: {None})

        Returns:
            [type] -- [description]
        """
        res = False
        if account is None:
            if account_cookie not in self.session.keys():

                # self.session[account_cookie] = QA_Account(
                #     account_cookie=account_cookie,
                #     broker=broker_name
                # )
                if self.sync_account(broker_name, account_cookie):
                    res = True

                if self.if_start_orderthreading and res:
                    #
                    self.order_handler.subscribe(
                        self.session[account_cookie],
                        self.broker[broker_name]
                    )

        else:
            if account_cookie not in self.session.keys():
                account.broker = broker_name
                self.session[account_cookie] = account
                if self.sync_account(broker_name, account_cookie):
                    res = True
                if self.if_start_orderthreading and res:
                    #
                    self.order_handler.subscribe(
                        account,
                        self.broker[broker_name]
                    )

        if res:
            return res
        else:
            try:
                self.session.pop(account_cookie)
            except:
                pass
            return False

    def sync_order_and_deal(self):
        self.order_handler.if_start_orderquery = True
        self._sync_orders()

    def stop_sync_order_and_deal(self):
        self.order_handler.if_start_orderquery = False

    def sync_account(self, broker_name, account_cookie):
        """??????????????????

        Arguments:
            broker_id {[type]} -- [description]
            account_cookie {[type]} -- [description]
        """
        try:
            if isinstance(self.broker[broker_name], QA_BacktestBroker):
                pass
            else:
                self.session[account_cookie].sync_account(
                    self.broker[broker_name].query_positions(account_cookie)
                )
            return True
        except Exception as e:
            print(e)
            return False

    def logout(self, account_cookie, broker_name):
        if account_cookie not in self.session.keys():
            return False
        else:
            self.order_handler.unsubscribe(
                self.session[account_cookie],
                self.broker[broker_name]
            )
            self.session.pop(account_cookie)

    def get_trading_day(self):
        return self.running_time

    def get_account_cookie(self):
        return list(self.session.keys())

    def insert_order(
            self,
            account_cookie,
            amount,
            amount_model,
            time,
            code,
            price,
            order_model,
            towards,
            market_type,
            frequence,
            broker_name,
            money=None
    ):
        #strDbg = QA_util_random_with_topic("QA_Market.insert_order")
        print(
            ">-----------------------insert_order----------------------------->",
            "QA_Market.insert_order"
        )

        flag = False

        # ???????????? bar/tick/realtime

        price_slice = self.query_data_no_wait(
            broker_name=broker_name,
            frequence=frequence,
            market_type=market_type,
            code=code,
            start=time
        )
        price_slice = price_slice if price_slice is None else price_slice[0]

        if order_model in [ORDER_MODEL.CLOSE, ORDER_MODEL.NEXT_OPEN]:
            if isinstance(price_slice, np.ndarray):
                if (price_slice != np.array(None)).any():
                    price = float(price_slice[4])
                    flag = True
                else:
                    QA_util_log_info(
                        'MARKET WARING: SOMEING WRONG WITH ORDER \n '
                    )
                    QA_util_log_info(
                        'code {} date {} price {} order_model {} amount_model {}'
                        .format(code,
                                time,
                                price,
                                order_model,
                                amount_model)
                    )
            elif isinstance(price_slice, dict):
                if price_slice is not None:
                    price = float(price_slice['close'])
                    flag = True
                else:
                    QA_util_log_info(
                        'MARKET WARING: SOMEING WRONG WITH ORDER \n '
                    )
                    QA_util_log_info(
                        'code {} date {} price {} order_model {} amount_model {}'
                        .format(code,
                                time,
                                price,
                                order_model,
                                amount_model)
                    )
            elif isinstance(price_slice, list):
                if price_slice is not None:
                    price = float(price_slice[4])
                    flag = True
                else:
                    QA_util_log_info(
                        'MARKET WARING: SOMEING WRONG WITH ORDER \n '
                    )
                    QA_util_log_info(
                        'code {} date {} price {} order_model {} amount_model {}'
                        .format(code,
                                time,
                                price,
                                order_model,
                                amount_model)
                    )

        elif order_model is ORDER_MODEL.MARKET:
            if isinstance(price_slice, np.ndarray):
                if (price_slice != np.array(None)).any():
                    price = float(price_slice[1])
                    flag = True
                else:
                    QA_util_log_info(
                        'MARKET WARING: SOMEING WRONG WITH ORDER \n '
                    )
                    QA_util_log_info(
                        'code {} date {} price {} order_model {} amount_model {}'
                        .format(code,
                                time,
                                price,
                                order_model,
                                amount_model)
                    )
            elif isinstance(price_slice, dict):

                if price_slice is not None:
                    price = float(price_slice['open'])
                    flag = True
                else:
                    QA_util_log_info(
                        'MARKET WARING: SOMEING WRONG WITH ORDER \n '
                    )
                    QA_util_log_info(
                        'code {} date {} price {} order_model {} amount_model {}'
                        .format(code,
                                time,
                                price,
                                order_model,
                                amount_model)
                    )
        elif order_model is ORDER_MODEL.LIMIT:
            flag = True
        print(
            amount,
            amount_model,
            time,
            code,
            price,
            order_model,
            towards,
            money
        )
        if flag:
            order = self.get_account(account_cookie).send_order(
                amount=amount,
                amount_model=amount_model,
                time=time,
                code=code,
                price=price,
                order_model=order_model,
                towards=towards,
                money=money
            )
            if order:
                self.order_handler.run(
                    QA_Event(
                        broker=self.broker[self.get_account(account_cookie
                                                           ).broker],
                        event_type=BROKER_EVENT.RECEIVE_ORDER,
                        order=order,
                        market_data=price_slice,
                        callback=self.on_insert_order
                    )
                )
        else:
            pass

    def on_insert_order(self, order: QA_Order):
        print(order)
        print(order.status)
        if order.status == ORDER_STATUS.FAILED:
            """????????????????????????, ????????????

            ??????????????????  ???????????? money

            ??????????????????  ???????????? sell_available
            """

            self.session[order.account_cookie].cancel_order(order)
        else:
            if order.order_model in [ORDER_MODEL.MARKET,
                                     ORDER_MODEL.CLOSE,
                                     ORDER_MODEL.LIMIT]:
                self.order_handler._trade(
                    order,
                    self.session[order.account_cookie]
                )                                      # ????????????
            elif order.order_model in [ORDER_MODEL.NEXT_OPEN]:
                pass

    def _renew_account(self):
        for account in self.session.values():
            account.run(QA_Event(event_type=ACCOUNT_EVENT.SETTLE))

    def _sync_position(self):
        self.order_handler.run(
            QA_Event(
                event_type=MARKET_EVENT.QUERY_POSITION,
                account_cookie=list(self.session.keys()),
                broker=[
                    self.broker[item.broker] for item in self.session.values()
                ]
            )
        )

    def _sync_deals(self):

        self.order_handler.run(
            QA_Event(
                event_type=MARKET_EVENT.QUERY_DEAL,
                account_cookie=list(self.session.keys()),
                broker=[
                    self.broker[item.broker] for item in self.session.values()
                ],
                event_queue=self.trade_engine.kernels_dict['ORDER'].queue
            )
        )

    def _sync_orders(self):
        # account_cookie=list(self.session.keys()),
        # broker=[self.broker[item.broker]
        #         for item in self.session.values()],
        # ??????: ??????????????????????????????@@@!!!
        # 2018-08-08 yutiansut
        # ??????callback??????????????????????????????????????????????????????
        self.order_handler.run(
            QA_Event(
                event_type=MARKET_EVENT.QUERY_ORDER,
                event_queue=self.trade_engine.kernels_dict['ORDER'].queue
            )
        )

    def sync_strategy(self, broker_name, account_cookie):
        """??????  ??????/??????/??????

        Arguments:
            broker_name {[type]} -- [description]
            account_cookie {[type]} -- [description]
        """
        pass

    def cancel_order(self, broker_name, account_cookie, order_id):
        pass

    def cancel_all(self, broker_name, account_cookie):
        try:
            self.broker[broker_name].cancel_all(account_cookie)
        except Exception as e:
            print(e)

    def query_orders(self, account_cookie):
        return self.order_handler.order_status.xs(account_cookie)

    def query_order(self, account_cookie, realorder_id):
        return self.order_handler.order_status.loc[account_cookie, realorder_id]

    def query_assets(self, account_cookie):
        return self.get_account(account_cookie).init_assets

    def query_position(self, account_cookie):
        return self.get_account(account_cookie).hold

    def query_cash(self, account_cookie):
        return self.get_account(account_cookie).cash_available

    def query_data_no_wait(
            self,
            broker_name,
            frequence,
            market_type,
            code,
            start,
            end=None
    ):
        return self.broker[broker_name].run(
            event=QA_Event(
                event_type=MARKET_EVENT.QUERY_DATA,
                frequence=frequence,
                market_type=market_type,
                code=code,
                start=start,
                end=end
            )
        )

    query_data = query_data_no_wait

    def query_currentbar(self, broker_name, market_type, code):
        return self.broker[broker_name].run(
            event=QA_Event(
                event_type=MARKET_EVENT.QUERY_DATA,
                frequence=FREQUENCE.CURRENT,
                market_type=market_type,
                code=code,
                start=self.running_time,
                end=None
            )
        )

    def on_query_data(self, data):
        print('ON QUERY')
        print(data)
        self.last_query_data = data

    def on_trade_event(self, event):
        print('ON TRADE')
        print(event.res)

    def _trade(self, event):
        "????????????"
        print('==================================market enging: trade')
        print(self.order_handler.order_queue.pending)
        print('==================================')
        self.order_handler._trade()
        print('done')

    def _settle(self, broker_name, callback=False):
        #strDbg = QA_util_random_with_topic("QA_Market._settle")
        print(
            ">-----------------------_settle----------------------------->",
            "QA_Market._settle"
        )

        # ?????????????????????BROKER???SETTLE??????
        # ?????????????????????ACCOUNT???SETTLE??????

        for account in self.session.values():
            """t0???????????????????????????
            """
            if account.broker == broker_name:
                if account.running_environment == RUNNING_ENVIRONMENT.TZERO:
                    for order in account.close_positions_order:
                        price_slice = self.query_data_no_wait(
                            broker_name=order.broker,
                            frequence=order.frequence,
                            market_type=order.market_type,
                            code=order.code,
                            start=order.datetime
                        )
                        price_slice = price_slice if price_slice is None else price_slice[
                            0]
                        self.order_handler.run(
                            QA_Event(
                                broker=self.broker[account.broker],
                                event_type=BROKER_EVENT.RECEIVE_ORDER,
                                order=order,
                                market_data=price_slice,
                                callback=self.on_insert_order
                            )
                        )

        self._trade(event=QA_Event(broker_name=broker_name))

        self.broker[broker_name].run(
            QA_Event(
                event_type=BROKER_EVENT.SETTLE,
                broker=self.broker[broker_name],
                callback=callback
            )
        )

        for account in self.session.values():
            print(account.history)
            account.settle()

        print('===== SETTLED {} ====='.format(self.running_time))

    def settle_order(self):
        """??????????????????

        1. ??????: ??????????????????,?????????????????????SETTLE
        2. ??????????????????
        3. broker????????????
        """

        if self.if_start_orderthreading:

            self.order_handler.run(
                QA_Event(
                    event_type=BROKER_EVENT.SETTLE,
                    event_queue=self.trade_engine.kernels_dict['ORDER'].queue
                )
            )

    def every_day_start(self):
        """????????????

        1. ??????????????????
        2. ????????????
        """
        pass

    def _close(self):
        pass

    def clear(self):
        return self.trade_engine.clear()


if __name__ == '__main__':

    import QUANTAXIS as QA

    user = QA.QA_Portfolio()
    # ????????????account

    a_1 = user.new_account()
    a_2 = user.new_account()
    market = QA_Market()

    market.connect(QA.RUNNING_ENVIRONMENT.BACKETEST)
    #
