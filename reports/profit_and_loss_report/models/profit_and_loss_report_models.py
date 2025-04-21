from dataclasses import dataclass

@dataclass
class ProfitAndLossReportModel:
    period: int
    profit: int
    accumulated_profit: int
