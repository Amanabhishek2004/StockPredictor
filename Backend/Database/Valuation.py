import numpy as np
import pandas as pd


def CalculateAvgGrowth(values):
    """Calculate average growth rate."""
    values = np.array(values)
    values = values[~np.isnan(values)]
    if len(values) < 2:
        return 0
    growth_rates = -np.diff(values) / values[:-1]
    return np.mean(growth_rates)


def ApplyDCF(cashflows, beta, payoutratio):
    """Apply Discounted Cash Flow model."""
    cashflows = pd.Series(cashflows).dropna().values
    if len(cashflows) < 5:
        return np.nan

    g = CalculateAvgGrowth(cashflows)
    r = beta * 7.27 + 7.57  # Cost of equity
    sustainable_growth = g * (1 - payoutratio)
    print(g , sustainable_growth, r)
    total_val = 0
    for i in range(10):
        total_val += (cashflows[-1] * (1 + g) ** i) / (1 + r) ** i

    terminal_value = (
        cashflows[4] * (1 + sustainable_growth) / (r - sustainable_growth)
    )
    total_val += terminal_value / (1 + r) ** 5
    return total_val



