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
import pandas as pd
import datetime
import uuid
from pymongo import ASCENDING, DESCENDING
from QUANTAXIS.QAARP.QAPortfolio import QA_Portfolio
from QUANTAXIS.QAUtil.QALogs import QA_util_log_info
from QUANTAXIS.QAUtil.QARandom import QA_util_random_with_topic
from QUANTAXIS.QAUtil.QASetting import QA_Setting, DATABASE
from QUANTAXIS.QAUtil.QADate_trade import QA_util_get_next_day, QA_util_get_real_date
from QUANTAXIS.QAUtil.QAParameter import MARKET_TYPE, FREQUENCE


class QA_User():
    """QA_User 
    User-->Portfolio-->Account/Strategy



    user ==> username / user_cookie
                            ||
                        portfolio  ==> portfolio_cookie
                                            ||
                                        accounts ==> account_cookie

    :::::::::::::::::::::::::::::::::::::::::::::::::
    ::        :: Portfolio 1 -- Account/Strategy 1 ::
    ::  USER  ::             -- Account/Strategy 2 ::
    ::        :: Portfolio 2 -- Account/Strategy 3 ::
    :::::::::::::::::::::::::::::::::::::::::::::::::

    :: ??????????????????QA_USER?????????

    USER????????????????????????, ?????????????????? ??????Portfolio (???????????????),?????? ??????Portfolio

    @yutiansut 
    2018/05/08

    @jerryw  ?????????????????? ????todo list
    2018/05/16

    @royburns  1.???????????????user_cookie??????user??? 2.?????????????????????????????? 3.????????????
    2018/05/18
    """

    def __init__(
            self,
            user_cookie=None,
            username='defalut',
            phone='defalut',
            level='l1',
            utype='guests',
            password='default',
            coins=10000,
            wechat_id=None,
            money=0,
            *args,
            **kwargs
    ):
        """[summary]

        Keyword Arguments:
            user_cookie {[type]} -- [description] (default: {None}) ??????????????? user_cookie ?????? Acc+4??????id+4??????????????????
            username {str} -- [description] (default: {'defalut'})
            phone {str} -- [description] (default: {'defalut'})
            level {str} -- [description] (default: {'l1'})
            utype {str} -- [description] (default: {'guests'})
            password {str} -- [description] (default: {'default'})
            coins {int} -- [description] (default: {10000})

        ??????????????????:

        ??????????????????????????????, ??????????????????????????????????????????

        """

        #self.setting = QA_Setting()
        self.client = DATABASE.user

        ## user_cookie/ username / wechat_id
        self.client.create_index(
            [
                ("user_cookie",
                 ASCENDING),
                ("username",
                 ASCENDING),
                ("wechat_id",
                 ASCENDING)
            ],
            unique=True
        )
        self.portfolio_list = []

        # ==============================
        self.phone = phone
        self.level = level
        self.utype = utype
        self.password = password
        self.username = username
        self.wechat_id = wechat_id

        if wechat_id is not None:

            if self.username == 'default':
                """??????web????????????
                """

                self.username = wechat_id
                self.password = 'admin'
        else:
            """
            ????????? ??? WECHATID ?????????, ????????????python?????????
            @yutiansut
            """
            if self.username == 'default':
                """??????web????????????
                """

                self.username = 'admin'
                self.password = 'admin'

        self.user_cookie = QA_util_random_with_topic(
            'USER'
        ) if user_cookie is None else user_cookie
        self.coins = coins  # ??????
        self.money = money  # ???

        # ==============================
        self._subscribed_strategy = {}

        """
        self._subscribed_code: {
            'stock_cn': {
                '000001': ['1min','5min'],
                '600010': ['tick']
            },
            'future_cn': {
                'rb1910.SHFE':['tick','60min'],
                'IF1909.IFFEX':['tick','1min']
            },
            'index_cn': {
                '000300': ['1min']
            }
        }

        """
        self._subscribed_code = {
            MARKET_TYPE.STOCK_CN: [],
            MARKET_TYPE.FUTURE_CN: [],
            MARKET_TYPE.INDEX_CN: [],
            MARKET_TYPE.OPTION_CN: []
        }
        self._signals = []  # ?????????????????????
        self._cash = []
        self._history = []

        # ===============================

        self.coins_history = []
        self.coins_history_headers = [
            'cost_coins',
            'strategy_id',
            'start',
            'last',
            'strategy_uuid',
            'event'
        ]
        self.sync()

    def __repr__(self):
        return '< QA_USER {} with {} portfolio: {} >'.format(
            self.user_cookie,
            len(self.portfolio_list),
            self.portfolio_list
        )

    def __getitem__(self, portfolio_cookie: str):
        """??????user??????portfolio

        Arguments:
            portfolio_cookie {str} -- [description]

        Returns:
            [type] -- [description]
        """

        try:
            return self.get_portfolio(portfolio_cookie)
        except:
            return None

    @property
    def table(self):
        return pd.concat(
            [self.get_portfolio(po).table for po in self.portfolio_list],
            axis=1
        )

    def add_coins(self, coins):
        """????????????
        Arguments:
            coins {[type]} -- [description]
        """

        self.coins += int(coins)

    @property
    def coins_table(self):
        return pd.DataFrame(
            self.coins_history,
            columns=self.coins_history_headers
        )

    def subscribe_strategy(
            self,
            strategy_id: str,
            last: int,
            today=datetime.date.today(),
            cost_coins=10
    ):
        """??????????????????

        ?????????????????????

        Arguments:
            strategy_id {str} -- [description]
            last {int} -- [description]

        Keyword Arguments:
            today {[type]} -- [description] (default: {datetime.date.today()})
            cost_coins {int} -- [description] (default: {10})
        """

        if self.coins > cost_coins:
            order_id = str(uuid.uuid1())
            self._subscribed_strategy[strategy_id] = {
                'lasttime':
                last,
                'start':
                str(today),
                'strategy_id':
                strategy_id,
                'end':
                QA_util_get_next_day(
                    QA_util_get_real_date(str(today),
                                          towards=1),
                    last
                ),
                'status':
                'running',
                'uuid':
                order_id
            }
            self.coins -= cost_coins
            self.coins_history.append(
                [
                    cost_coins,
                    strategy_id,
                    str(today),
                    last,
                    order_id,
                    'subscribe'
                ]
            )
            return True, order_id
        else:
            # return QAERROR.
            return False, 'Not Enough Coins'

    def unsubscribe_stratgy(self, strategy_id):
        """???????????????????????????

        Arguments:
            strategy_id {[type]} -- [description]
        """

        today = datetime.date.today()
        order_id = str(uuid.uuid1())
        if strategy_id in self._subscribed_strategy.keys():
            self._subscribed_strategy[strategy_id]['status'] = 'canceled'

        self.coins_history.append(
            [0,
             strategy_id,
             str(today),
             0,
             order_id,
             'unsubscribe']
        )

    @property
    def subscribed_strategy(self):
        """??????(?????????????????????)??????

        Returns:
            [type] -- [description]
        """

        return pd.DataFrame(list(self._subscribed_strategy.values()))

    @property
    def subscribing_strategy(self):
        """??????????????????

        Returns:
            [type] -- [description]
        """

        res = self.subscribed_strategy.assign(
            remains=self.subscribed_strategy.end.apply(
                lambda x: pd.Timestamp(x) - pd.Timestamp(datetime.date.today())
            )
        )
        #res['left'] = res['end_time']
        # res['remains']
        res.assign(
            status=res['remains'].apply(
                lambda x: 'running'
                if x > datetime.timedelta(days=0) else 'timeout'
            )
        )
        return res.query('status=="running"')

    def change_wechatid(self, id):
        """??????wechat

        Arguments:
            id {[type]} -- [description]
        """

        self.wechat_id = id

    def sub_code(self, code, market_type=MARKET_TYPE.STOCK_CN):
        """??????????????????
        """
        if code not in self._subscribed_code[market_type]:
            self._subscribed_code[market_type].append(code)

    def unsub_code(self, code, market_type=MARKET_TYPE.STOCK_CN):
        """??????????????????

        Arguments:
            code {[type]} -- [description]
        """
        try:
            self._subscribed_code[market_type].remove(code)
        except:
            pass

    @property
    def subscribed_code(self):
        """
        ???????????????
        Returns:
            [type] -- [description]
        """

        return self._subscribed_code

    def new_portfolio(self, portfolio_cookie=None):
        '''
        ?????? self.user_cookie ???????????? portfolio
        :return:
        ???????????? ?????? ????????? QA_Portfolio
        ?????????????????? ?????? ??????portfolio
        '''

        if portfolio_cookie not in self.portfolio_list:
            self.portfolio_list.append(portfolio_cookie)
            return QA_Portfolio(
                user_cookie=self.user_cookie,
                portfolio_cookie=portfolio_cookie
            )
        else:
            print(
                " prortfolio with user_cookie ",
                self.user_cookie,
                " already exist!!"
            )
            return self.get_portfolio(portfolio_cookie)

    def get_account(self, portfolio_cookie: str, account_cookie: str):
        """???????????????????????????account

        Arguments:
            portfolio_cookie {str} -- [description]
            account_cookie {str} -- [description]

        Returns:
            [type] -- [description]
        """
        #                 QA_Portfolio(
        #                     user_cookie=self.user_cookie,
        #                     portfolio_cookie=item
        #                 )
        try:
            return self.get_portfolio(portfolio_cookie).get_account(account_cookie)
        except:
            return None

    def get_portfolio(self, portfolio_cookie: str):
        '''
        'get a portfolio'
        ??? portfolio_list dict????????? ?????? portfolio key ??????
        :param portfolio: QA_Portfolio??????
        :return: QA_Portfolio??????
        '''
        # return self.portfolio_list[portfolio]
        # fix here use cookie as key to find value in dict
        return QA_Portfolio(user_cookie=self.user_cookie, portfolio_cookie=portfolio_cookie)

    def generate_simpleaccount(self):
        """make a simple account with a easier way
        ????????????user???????????????portfolio, ???????????????portfolio,?????????portfolio????????????account
        ???????????????????????????portfolio,??????????????????portfolio???????????????account
        """
        if len(self.portfolio_list) < 1:
            po = self.new_portfolio()
        else:
            po = self.get_portfolio(self.portfolio_list[0])
        ac = po.new_account()
        return ac, po

    def register_account(self, account, portfolio_cookie=None):
        '''
        ????????????account???portfolio?????????
        account ??????????????????????????????????????? on_bar ??????
        :param account: ????????????account
        :return:
        '''
        # ?????? portfolio
        if len(self.portfolio_list) < 1:
            po = self.new_portfolio()
        elif portfolio_cookie is not None:
            po = self.get_portfolio(portfolio_cookie)
        else:
            po = self.get_portfolio(self.portfolio_list[0])
        # ???account ????????? portfolio??????
        po.add_account(account)
        return (po, account)

    @property
    def message(self):
        return {
            'user_cookie': self.user_cookie,
            'username': self.username,
            'password': self.password,
            'wechat_id': self.wechat_id,
            'phone': self.phone,
            'level': self.level,
            'utype': self.utype,
            'coins': self.coins,
            'coins_history': self.coins_history,
            'money': self.money,
            'subuscribed_strategy': self._subscribed_strategy,
            'subscribed_code': self.subscribed_code,
            'portfolio_list': self.portfolio_list,
            'lastupdatetime': str(datetime.datetime.now())
        }

    def save(self):
        """
        ???QA_USER????????????????????????

        ATTENTION:

        ???save user?????????, ??????????????????  user/portfolio/account?????????????????????????????? ??????save

        """
        if self.wechat_id is not None:
            self.client.update(
                {'wechat_id': self.wechat_id},
                {'$set': self.message},
                upsert=True
            )
        else:
            self.client.update(
                {
                    'username': self.username,
                    'password': self.password
                },
                {'$set': self.message},
                upsert=True
            )

        # user ==> portfolio ?????????
        # account????????????  portfolio.save ==> account.save ???
        # for portfolio in list(self.portfolio_list.values()):
        #     portfolio.save()

    def sync(self):
        """????????????/?????????sync?????????
        """
        if self.wechat_id is not None:

            res = self.client.find_one({'wechat_id': self.wechat_id})
        else:
            res = self.client.find_one(
                {
                    'username': self.username,
                    'password': self.password
                }
            )
        if res is None:

            if self.client.find_one({'username': self.username}) is None:
                self.client.insert_one(self.message)
                return self
            else:
                raise RuntimeError('??????????????????????????????????????????')

        else:
            self.reload(res)

            return self

    # @property
    # def node_view(self):

    #     links = [
    #         {
    #             'source': self.username,
    #             'target': item
    #         } for item in self.portfolio_list.keys()
    #     ]
    #     data = [{'name': self.username, 'symbolSize': 100, 'value': 1}]
    #     for port in self.portfolio_list.values():
    #         links.extend(port.node_view['links'])
    #         data.append(
    #             {
    #                 'name': port.portfolio_cookie,
    #                 'symbolSize': 80,
    #                 'value': 2
    #             }
    #         )
    #         for acc in port.accounts.values():
    #             data.append(
    #                 {
    #                     'name': acc.account_cookie,
    #                     'symbolSize': 50,
    #                     'value': 3
    #                 }
    #             )

    #     return {
    #         'node_name':
    #         self.username,
    #         'sub_node':
    #         [portfolio.node_view for portfolio in self.portfolio_list.values()],
    #         'links':
    #         links,
    #         'data':
    #         data
    #     }

    def reload(self, message):
        """????????????

        Arguments:
            message {[type]} -- [description]
        """

        self.phone = message.get('phone')
        self.level = message.get('level')
        self.utype = message.get('utype')
        self.coins = message.get('coins')
        self.wechat_id = message.get('wechat_id')
        self.coins_history = message.get('coins_history')
        self.money = message.get('money')
        self._subscribed_strategy = message.get('subuscribed_strategy')
        subscribed_code = message.get('subscribed_code')
        if isinstance(subscribed_code, list):
            pass
        else:
            self._subscribed_code = subscribed_code
        self.username = message.get('username')
        self.password = message.get('password')
        self.user_cookie = message.get('user_cookie')
        #
        self.portfolio_list = list(set([
            item['portfolio_cookie'] for item in DATABASE.portfolio.find(
                {'user_cookie': self.user_cookie},
                {
                    'portfolio_cookie': 1,
                    '_id': 0
                }
            )
        ]))

        # portfolio_list = message.get('portfolio_list')
        # if len(portfolio_list) > 0:
        #     self.portfolio_list = dict(
        #         zip(
        #             portfolio_list,
        #             [
        #                 QA_Portfolio(
        #                     user_cookie=self.user_cookie,
        #                     portfolio_cookie=item
        #                 ) for item in portfolio_list
        #             ]
        #         )
        #     )
        # else:
        #     self.portfolio_list = {}


if __name__ == '__main__':

    # ????????????
    user = QA_User(user_cookie='user_admin')
    folio = user.new_portfolio('folio_admin')
    ac1 = user.get_portfolio(folio).new_account('account_admin')

    print(user)
    print(user.get_portfolio(folio))
    print(user.get_portfolio(folio).get_account(ac1))
