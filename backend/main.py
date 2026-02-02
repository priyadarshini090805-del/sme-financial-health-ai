from fastapi import FastAPI, UploadFile, File
import pandas as pd

app = FastAPI(title="SME Financial Health AI")

@app.get("/")
def root():
    return {"message": "SME Financial Health AI Backend is running"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        return {"error": "Only CSV files are supported"}

    df = pd.read_csv(file.file)
    df.columns = [c.lower().strip() for c in df.columns]

    # Detect market/trading data
    market_columns = {"open", "high", "low", "close"}
    if market_columns.issubset(set(df.columns)):
        return {
            "dataset_type": "market_data",
            "message": (
                "This file appears to be trading/market data (OHLC). "
                "Financial health analysis is designed for SME cash flow, "
                "bank statements, or expense data."
            ),
            "suggestion": (
                "Please upload a bank statement, expense sheet, or "
                "transaction CSV for financial health assessment."
            ),
            "detected_columns": list(df.columns)
        }

    # Bank statement: debit & credit
    if "debit" in df.columns and "credit" in df.columns:
        df["debit"] = pd.to_numeric(df["debit"], errors="coerce").fillna(0)
        df["credit"] = pd.to_numeric(df["credit"], errors="coerce").fillna(0)
        df["amount"] = df["credit"] - df["debit"]

    # Single amount column
    else:
        possible_amount_cols = ["amount", "value", "transaction_amount"]
        amount_col = next((c for c in possible_amount_cols if c in df.columns), None)

        if amount_col is None:
            return {
                "dataset_type": "unsupported",
                "message": (
                    "No financial amount columns found. "
                    "This platform supports SME financial data."
                ),
                "available_columns": list(df.columns)
            }

        df["amount"] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0)

    # Financial calculations
    total_revenue = df[df["amount"] > 0]["amount"].sum()
    total_expense = abs(df[df["amount"] < 0]["amount"].sum())
    net_cashflow = total_revenue - total_expense

    risks = []
    if total_expense > total_revenue * 0.8:
        risks.append("High expense ratio")
    if net_cashflow < 0:
        risks.append("Negative cash flow")

    return {
        "dataset_type": "sme_financial",
        "total_revenue": round(float(total_revenue), 2),
        "total_expense": round(float(total_expense), 2),
        "net_cashflow": round(float(net_cashflow), 2),
        "risk_flags": risks
    }
from pydantic import BaseModel

class FinancialSummary(BaseModel):
    total_revenue: float
    total_expense: float
    net_cashflow: float
    risk_flags: list[str] = []

@app.post("/ai-insights")
def ai_insights(data: FinancialSummary):
    insights = []

    if data.net_cashflow > 0:
        insights.append(
            "Your business is generating positive cash flow, which is a good sign."
        )
    else:
        insights.append(
            "Your business is facing negative cash flow. Immediate attention is required."
        )

    if "High expense ratio" in data.risk_flags:
        insights.append(
            "Expenses are consuming a large portion of revenue. Cost optimization is recommended."
        )

    recommendations = [
        "Review recurring expenses and identify non-essential costs.",
        "Negotiate better payment terms with suppliers.",
        "Improve customer payment collection timelines."
    ]

    return {
        "plain_english_summary": " ".join(insights),
        "actionable_recommendations": recommendations
    }
class HealthScoreInput(BaseModel):
    total_revenue: float
    total_expense: float
    net_cashflow: float
    risk_flags: list[str] = []

@app.post("/health-score")
def health_score(data: HealthScoreInput):
    score = 100

    if data.net_cashflow < 0:
        score -= 40

    expense_ratio = 0
    if data.total_revenue > 0:
        expense_ratio = data.total_expense / data.total_revenue

    if expense_ratio > 0.8:
        score -= 30
    elif expense_ratio > 0.6:
        score -= 15

    if "Negative cash flow" in data.risk_flags:
        score -= 20

    if score < 0:
        score = 0

    if score >= 80:
        label = "Healthy"
    elif score >= 50:
        label = "Moderate"
    else:
        label = "At Risk"

    return {
        "financial_health_score": score,
        "status": label
    }
class CreditAssessmentInput(BaseModel):
    financial_health_score: int
    net_cashflow: float
    risk_flags: list[str] = []

@app.post("/creditworthiness")
def creditworthiness(data: CreditAssessmentInput):
    if data.financial_health_score >= 75 and data.net_cashflow > 0:
        status = "Credit Ready"
        reason = "Strong financial health and positive cash flow."
    elif data.financial_health_score >= 50:
        status = "Caution"
        reason = "Moderate financial health. Credit possible with conditions."
    else:
        status = "High Risk"
        reason = "Weak financial indicators or negative cash flow."

    return {
        "credit_status": status,
        "explanation": reason
    }
class ProductRecommendationInput(BaseModel):
    credit_status: str
    net_cashflow: float
    total_revenue: float
    total_expense: float

@app.post("/product-recommendation")
def product_recommendation(data: ProductRecommendationInput):
    recommendations = []

    expense_ratio = 0
    if data.total_revenue > 0:
        expense_ratio = data.total_expense / data.total_revenue

    if data.credit_status == "Credit Ready":
        if data.net_cashflow > 0:
            recommendations.append("Working Capital Loan")
            recommendations.append("Business Credit Card")
        else:
            recommendations.append("Invoice Discounting")
    elif data.credit_status == "Caution":
        recommendations.append("Overdraft Facility")
    else:
        recommendations.append(
            "Not eligible for credit currently. Focus on improving cash flow and reducing expenses."
        )

    return {
        "recommended_products": recommendations,
        "note": "Recommendations are indicative and based on financial indicators."
    }
