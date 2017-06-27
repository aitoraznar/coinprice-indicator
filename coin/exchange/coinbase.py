# -*- coding: utf-8 -*-

# Coinbase
# https://developers.coinbase.com/api/v2

__author__ = "aitor@aitoraznar.com"

from gi.repository import GLib

import requests

import utils
from exchange.error import Error
from alarm import Alarm

CONFIG = {
  'ticker': 'https://api.coinbase.com/v2/prices/:currency_pair/buy',
  'asset_pairs': [
    {
      'code': 'BTC-USD',
      'name': 'BTC to USD',
      'currency': utils.currency['usd']
    },
    {
      'code': 'ETH-USD',
      'name': 'ETH to USD',
      'currency': utils.currency['usd']
    }
  ]
}

class Coinbase:

  def __init__(self, config, indicator):
    self.indicator = indicator

    self.timeout_id = 0
    self.alarm = Alarm(config['app']['name'])

    self.error = Error(self)

  def start(self, error_refresh=None):
    refresh = error_refresh if error_refresh else self.indicator.refresh_frequency
    self.timeout_id = GLib.timeout_add_seconds(refresh, self.check_price)

  def stop(self):
    if self.timeout_id:
      GLib.source_remove(self.timeout_id)

  def check_price(self):
    self.asset_pair = self.indicator.active_asset_pair

    try:
      res = requests.get(CONFIG['ticker'].replace(':currency_pair', self.asset_pair))
      
      data = res.json()
      if data['data']:
        self._parse_result(data['data'])

    except Exception as e:
      print(e)
      self.error.increment()

    return self.error.is_ok()

  def _parse_result(self, data):
    self.error.clear()

    print(data)
    asset = data
    currency = [item['currency'] for item in CONFIG['asset_pairs'] if item['code'] == self.asset_pair][0]

    label = currency + asset['amount']

    bid = utils.category['bid'] + currency + utils.decimal_round(asset['amount'])
    high = utils.category['high'] + currency + utils.decimal_round(asset['amount'])
    low = utils.category['low'] + currency + utils.decimal_round(asset['amount'])
    ask = utils.category['ask'] + currency + utils.decimal_round(asset['amount'])

    # if self.alarm:
    #   self.alarm.check(float(data["last"]))

    self.indicator.set_data(label, bid, high, low, ask)

  def _handle_error(self, error):
    print("Coinbase API error: " + error[0])
