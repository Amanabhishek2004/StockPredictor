from sqlalchemy.orm import joinedload
from fastapi import APIRouter, UploadFile, HTTPException, Depends , FastAPI
from sqlalchemy.orm import Session
import pandas as pd
from typing import List 
from Database.Schemas.StockSchema import StockSchema    
from Database.database import Base, engine, get_db
from Database.models import Stock, EarningMetric, Comparables, Expenses, Financials, ValuationMetrics
from uuid import uuid4
import math 
from Database.Stock import *
from typing import Dict
from statistics import median   
from Database.StockDictSchema import *
from Database.StockCashFlowCalculator import  *
from Database.CalculateForwardRatios import *



def safe_get_as_float(value, default=0.0):
    try:
        if value is None:
            value = 0.0
        return float(value) if value is not None else default
    except ValueError:
        return default

def safe_get_as_string(value, default="0"):
    return str(value) if value is not None else default

app = FastAPI()

@app.post("/upload/")
async def upload_data(file: UploadFile, db: Session = Depends(get_db)):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")

    try:
        df = pd.read_excel(file.file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading Excel file: {str(e)}")

    try:
        for _, row in df.iterrows():
            stock = Stock(
                id=str(uuid4()),
                Ticker=safe_get_as_string(row.get("tickers")),
                CurrentPrice=safe_get_as_float(row.get("Current Price"),0),
                marketCap=safe_get_as_float(row.get("marketCap"), 0),
                twoHundredDayAverage=safe_get_as_float(row.get("twoHundredDayAverage"), 0),
                fiftyDayAverage=safe_get_as_float(row.get("fiftyDayAverage"), "0"),
                grossProfits=safe_get_as_float(row.get("grossProfits"), 0),
                sector=safe_get_as_string(row.get("sector"), "Unknown"),
                beta=safe_get_as_float(row.get("beta"), 0)
            )
            db.add(stock)
            db.commit()
            db.refresh(stock)

            earning_metric = EarningMetric(
                id=str(uuid4()),
                stock_id=stock.id,
                EBIT_cagr=safe_get_as_float(row.get("EBIT_cagr"), 0),
                EBITDA_cagr=safe_get_as_float(row.get("EBITDA_cagr"), 0),
                OperatingRevenue_Cagr=safe_get_as_float(row.get("Operating Revenue_cagr"), 0),
                OperatingRevenue = safe_get_as_string(row.get("Operating Revenue") , 0 ) , 
                BasicEps_Cagr=safe_get_as_float(row.get("Basic EPS_cagr"), 0),
                operatingMargins=safe_get_as_float(row.get("operatingMargins"), 0),
                grossMargins=safe_get_as_float(row.get("grossMargins"), 0),
                epsTrailingTwelveMonths=safe_get_as_float(row.get("epsTrailingTwelveMonths"), 0),
                epsForward=safe_get_as_float(row.get("epsForward"), 0),
                FreeCashFlow_cagr=safe_get_as_float(row.get("Free Cash Flow_cagr"), 0),
                NetIncomeFromContinuingOperations_cagr=safe_get_as_float(row.get("Net Income From Continuing Operations_cagr"), 0),
                NetIncome_cagr=safe_get_as_float(row.get("Net Income_cagr"), 0)
            )
            db.add(earning_metric)
            db.commit()
            print(earning_metric.stock.Ticker)
        
            comparables = Comparables(
                id=str(uuid4()),
                stock_id=stock.id,
                trailingPE=safe_get_as_float(row.get("trailingPE"), 0),
                forwardPE=safe_get_as_float(row.get("forwardPE"), 0),
                pricetoBook=safe_get_as_float(row.get("bookValue"), 0),
                pricetoFreeCashFlow=safe_get_as_float(row.get("Free Cash Flow_avggrowth"), 0),
                pricetoSales=safe_get_as_float(row.get("Free Cash Flow_cagr"), 0),
                DebttoEquity=safe_get_as_float(row.get("debtToEquity"), 0),
                trailingAnnualDividendYield=safe_get_as_float(row.get("trailingAnnualDividendYield"), 0),
                dividendYield=safe_get_as_float(row.get("dividendYield"), 0),
                dividendRate=safe_get_as_float(row.get("dividendRate"), 0),
                fiveYearAvgDividendYield=safe_get_as_float(row.get("fiveYearAvgDividendYield"), 0),
                payoutRatio=safe_get_as_float(row.get("payoutRatio"), 0)
            )
            db.add(comparables)
            db.commit()

            expenses = Expenses(
                id=str(uuid4()),
                stock_id=stock.id,
                CurrentDebt_cagr=safe_get_as_float(row.get("Current Debt_cagr"), 0),
                CapitalExpenditure_cagr=safe_get_as_float(row.get("Capital Expenditure Reported"), 0),
                InterestExpense_cagr=safe_get_as_float(row.get("Interest Expense_cagr"), 0),
                Intrest_Expense = safe_get_as_string(row.get("Interest Expense") ,"0" ) , 
                Operating_Expense = safe_get_as_string(row.get('Operating Expense') , "0" ) , 
                TotalExpenses_cagr=safe_get_as_float(row.get("Total Expenses"), 0),
                WACC=safe_get_as_float(row.get("WACC"), 0)
            )
            db.add(expenses)
            db.commit()

            financials = Financials(
                id=str(uuid4()),
                stock_id=stock.id,
                NetTangibleAssets_cagr=safe_get_as_float(row.get("Net Tangible Assets_cagr"), 0),
                InvestedCapital=safe_get_as_string(row.get("Invested Capital"), "0"),
                InvestedCapital_cagr=safe_get_as_float(row.get("Invested Capital_cagr"), 0),
                RetainedEarnings_cagr=safe_get_as_float(row.get("Retained Earnings_cagr"), 0),
                TotalAssets=safe_get_as_string(row.get("Total Assets_cagr"), "0"),
                TaxRateForCalcs=safe_get_as_string(row.get("Tax Rate For Calcs"), "0")
            )
            db.add(financials)
            db.commit()
            metrics = ValuationMetrics(
                id=str(uuid4()),
                stock_id=stock.id,
                ROE=safe_get_as_float(row.get("ROE"), 0),
                ROA=safe_get_as_float(row.get("ROA"), 0),
                ROIC=safe_get_as_float(row.get("ROIC"), 0),
                WACC=safe_get_as_float(row.get("WACC"), 0),
                COD=safe_get_as_float(row.get("COD"), 0),
                ICR=safe_get_as_float(row.get("ICR"), 0),
                EFF=safe_get_as_float(row.get("EFF"), 0),
                ATR=safe_get_as_float(row.get("ATR"), 0)
            )
            db.add(metrics)
            db.commit()
        db.commit()
        return {"message": "Data uploaded successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")


from fastapi import Depends
from sqlalchemy.orm import Session
from statistics import median
from typing import List

@app.post("/calculate/")
def calculate_median_for_metrics(peers: List[str], db: Session = Depends(get_db)):
    peer_stocks = db.query(Stock).filter(Stock.Ticker.in_(peers)).all()

    metrics = {
        "earning_metric": {},
        "expense_metric": {},
        "valuation_metric": {},
        "operational_metric": {},
        "efficiency_metric": {},
    }

    for stock in peer_stocks:
        for em in stock.earning_metrics:
            for column, value in em.__dict__.items():
                if column not in ["id", "stock_id"] and column in eaningparams:
                    try:
                        metrics["earning_metric"].setdefault(column, []).append(float(value))
                    except (ValueError, TypeError):
                        print(f"[❌ SKIPPED] earning_metric.{column} - Invalid value: {value}")

        for exp in stock.expenses:
            for column, value in exp.__dict__.items():
                if column not in ["id", "stock_id"] and column in expensesparams:
                    try:
                        metrics["expense_metric"].setdefault(column, []).append(float(value))
                    except (ValueError, TypeError):
                        print(f"[❌ SKIPPED] expense_metric.{column} - Invalid value: {value}")

        for fin in stock.financials:
            for column, value in fin.__dict__.items():
                if column not in ["id", "stock_id"] and column in financialsparams:
                    try:
                        metrics["efficiency_metric"].setdefault(column, []).append(float(value))
                    except (ValueError, TypeError):
                        print(f"[❌ SKIPPED] efficiency_metric.{column} - Invalid value: {value}")

        for val in stock.metrics:
            for column, value in val.__dict__.items():
                if column not in ["id", "stock_id"] and column in efficiencyparams:
                    try:
                        metrics["valuation_metric"].setdefault(column, []).append(float(value))
                    except (ValueError, TypeError):
                        print(f"[❌ SKIPPED] valuation_metric.{column} - Invalid value: {value}")

        for comp in stock.comparables:
            for column, value in comp.__dict__.items():
                if column not in ["id", "stock_id"] and column in comparablesparams:
                    try:
                        metrics["operational_metric"].setdefault(column, []).append(float(value))
                    except (ValueError, TypeError):
                        print(f"[❌ SKIPPED] operational_metric.{column} - Invalid value: {value}")

    # Calculate medians with error reporting
    medians = {}
    for metric_name, data in metrics.items():
        medians[metric_name] = {}
        for key, values in data.items():
            try:
                medians[metric_name][key] = median(values)
            except Exception as e:
                print(f"[❌ ERROR] Failed to compute median for: {metric_name} -> {key}")
                print(f"   Values: {values}")
                print(f"   Error: {e}")

    return medians




def calculate_median_value(benchmark, stock):
    negative_impact = [
        "trailingPE", "pricetoFreeCashFlow", "pricetoSales", "DebttoEquity",
        "trailingAnnualDividendYield", "CapitalExpenditure_Cagr",
        "TotalExpenses_Cagr", "InterestExpense_Cagr", "WACC",
        "Debt_Cagr", "COD", "enterpriseToEbitda", "pricetobook"
    ]

    scores = {}

    for metric, data in benchmark.items():
        scores[metric] = {}
        for key, benchmark_value in data.items():
            stock_value = stock.get(metric, {}).get(key, None)
            if stock_value is None:
                continue

            if key in negative_impact:
                scores[metric][key] = benchmark_value - stock_value 
            else:
                scores[metric][key] = stock_value - benchmark_value
                  
    return scores


def CalculateAllscores(data) :
    metrics = {metric : 0 in metric for metric in data.keys()}

    for key in metrics.keys() :
        metrics[key] = sum(data[key].values())

    for key in metrics.keys() :
        total_score = sum(metrics[key].values())    
    return metrics  , total_score  






@app.post("/peerstocks/", response_model=List[StockSchema])
def GetPeers(ticker: List[str], db: Session = Depends(get_db)):
    for stock in ticker:
        if not isinstance(stock, str):
            raise HTTPException(status_code=400, detail="Ticker must be a string")
        elif db.query(Stock).filter(Stock.Ticker == stock).first() is None:
           data =  CreateStockDataBaseInstance(stock, db)
           print(data)
           if data.get("error"):
                raise HTTPException(status_code=400, detail=data["error"])
    
    stocks = db.query(Stock).filter(Stock.Ticker.in_(ticker)).all()
    
    if not stocks:
        raise HTTPException(status_code=404, detail="No stocks found")
    
    return stocks




@app.get("/stocks", response_model=List[StockSchema])
def get_all_stocks(db: Session = Depends(get_db)):
    stocks = db.query(Stock).all()
    for stock in stocks:
        for field, value in stock.__dict__.items():
            if isinstance(value, float) and math.isnan(value):  # NaN check
                print(f"NaN detected in field: {field} for stock {stock.Ticker}")
    return stocks 


@app.get("/FCFF/{ticker}")
def get_the_cashflows(ticker: str, db: Session = Depends(get_db)):
    """
    Endpoint to calculate and return the Free Cash Flow to Firm (FCFF) for a given stock ticker.

    Args:
        ticker (str): Stock ticker symbol.
        db (Session): Database session dependency.

    Returns:
        dict: A dictionary containing the ticker and its calculated FCFF value.
    """
    try:
        # Call the FCFF calculation function
        fcff = CalculateFCFF(ticker, db)
        
        if fcff is None:
            raise HTTPException(
                status_code=404,
                detail=f"FCFF calculation failed for ticker: {ticker}"
            )
        
        return {
            "TICKER": ticker,
            "FCFF": fcff
        }
    
    except Exception as e:
        # Generic error handling
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )



@app.get("/CalculateForwardPe/{ticker}")
def FPE(ticker: str, db: Session = Depends(get_db)):
     
     forwardpe = CalculateForwardPe(ticker , db)

     return {
         "Ticker" : ticker , 
         "forwardpe" : forwardpe
     }