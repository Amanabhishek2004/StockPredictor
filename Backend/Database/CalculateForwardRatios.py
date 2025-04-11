from .models import *
import numpy as np 


def process_data(row):
        specific_column_data = row.replace("[" , "").replace("]" , "")
        data = specific_column_data.split(",") 
        
        vals =  [float(x)  if x !="nan" else np.nan for x in data][:-1]  if len(data) > 4 else [float(x)  if x !="nan" else np.nan for x in data]
        print("***********************************")
        print(vals[0])
        return vals

def CalculateForwardPe(Ticker, db):
    # Tax rate
    taxrate = 0.3

    # Fetch stock data
    stock = db.query(Stock).filter(Stock.Ticker == Ticker).first()
    if not stock:
        raise ValueError(f"Stock with Ticker {Ticker} not found.")

    # Calculate forward interest expense
    recent_intrest = process_data(stock.expenses[0].Intrest_Expense)[0]
    intrestexpencegrowth = float(stock.expenses[0].InterestExpense_cagr)  # Ensure numeric conversion
    forward_intrest_expense = recent_intrest * (1 + intrestexpencegrowth) * (1 - taxrate)

    # Calculate forward operating expense
    recent_operating_expense = process_data(stock.expenses[0].Operating_Expense)[0]
    operating_expensegrowth = float(stock.earning_metrics[0].OperatingRevenue_Cagr)  # Ensure numeric conversion
    forward_operating_expense = recent_operating_expense * (1 + operating_expensegrowth)

    # Calculate forward sales
    recentsales = process_data(stock.earning_metrics[0].OperatingRevenue)[0]
    salesgrowth = float(stock.earning_metrics[0].OperatingRevenue_Cagr)  # Ensure numeric conversion
    forwardsales = recentsales * (1 + salesgrowth)

    # Calculate net earnings and forward EPS
    stock.CurrentPrice = 485
    num_outstanding_stocks = stock.marketCap // stock.CurrentPrice
    NetEarning = (forwardsales - forward_intrest_expense - forward_operating_expense) * (1 - taxrate)
    forwardeps = NetEarning / num_outstanding_stocks

    # Return forward PE ratio
    return stock.CurrentPrice / forwardeps



