import numpy as np
import pandas as pd
import math

DATE_TIME_COLUMN = 'date'
CLOSE_COLUMN = 'close'
RETURN_COLUMN = 'return'
WEIGHTED_RETURN_COLUMN = 'weightedReturn'


def datetime64FromYYYYMMDD(x):
    return pd.to_datetime(str(x), format='%Y%m%d')


def yyyymmdd(dt):
    return dt.strftime('%Y%m%d')


class MarketFactor:
    # Represents the historical observations of a market variable
    def __init__(self, ticker_, data_):
        self.ticker = ticker_
        close = data_[CLOSE_COLUMN]
        data_[RETURN_COLUMN] = np.log(close / close.shift(1))
        data_ = data_.ix[1:]  # drop first row because it has NaN log return
        self.data = data_  # [::-1] #reverse so that most recent data is first
        self.data.index = self.data[DATE_TIME_COLUMN]

    def __repr__(self):
        return 'MarketFactor(' + self.ticker + ',' + yyyymmdd(self.data.index[0]) \
               + ' to ' + yyyymmdd(self.data.index[-1]) + ',' + str(len(self.data)) + ' days)'


class MarketFactorVector:
    # The weighted subset of historical observations of a market used for Monte Carlo simulation
    def __init__(self, marketFactor_, startDate_, endDate_, decay_):
        self.marketFactor = marketFactor_
        self.startDate = startDate_
        self.endDate = endDate_
        returnsDataFrame = marketFactor_.data[startDate_:endDate_]
        numDays = len(returnsDataFrame)
        if decay_ < 1:
            sqrtSumOfWeights = math.sqrt((1 + decay_ ** numDays) / (1 - decay_))
            weights = [decay_ ** (numDays - i) / sqrtSumOfWeights for i in range(numDays)]
            self.weightedReturns = np.multiply(returnsDataFrame[RETURN_COLUMN].values, weights)
        else:
            self.weightedReturns = np.divide(returnsDataFrame[RETURN_COLUMN].values, math.sqrt(numDays))

    def __repr__(self):
        return 'MarketFactorVector(' + self.marketFactor.ticker + ', ' + yyyymmdd(self.startDate) \
               + ', ' + yyyymmdd(self.endDate) + ',' + str(len(self.weightedReturns)) + ' returns)'


class MarketUniverse:
    def __init__(self):
        self.tickerToMarketFactorDict = {}

    def initializeFromFileNames(self, dataFileNames):
        fileCount = 0
        columnNames = [DATE_TIME_COLUMN, 'time', 'open', 'high', 'low', CLOSE_COLUMN, 'volume']
        for dataFileName in dataFileNames:
            fileCount += 1
            if fileCount > 3:
                break
            ticker = dataFileName[6:dataFileName.find('.')].upper()
            # print ticker
            data = pd.read_csv('daily/' + dataFileName)
            data.columns = columnNames
            data[DATE_TIME_COLUMN] = data[DATE_TIME_COLUMN].apply(lambda x: datetime64FromYYYYMMDD(x))
            for columnName in columnNames:
                if columnName != 'date' and columnName != 'close':
                    data.drop(columnName, axis=1, inplace=True)
            self.tickerToMarketFactorDict[ticker] = MarketFactor(ticker, data)

    def initializeFromTickers(self, tickers):
        self.initializeFromFileNames(['table_' + ticker + '.csv' for ticker in tickers])
