from dataclasses import dataclass

@dataclass
class ProfitAndLossReportModel:
    period: int
    revenue: int
    accumulated_revenue: int
    profit: int
    accumulated_profit: int
