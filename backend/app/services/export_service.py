import csv
import io
from datetime import datetime
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


def generate_csv(transactions: List[dict]) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "id", "date", "type", "category", "description",
        "merchant", "amount", "currency", "is_anomaly"
    ])
    writer.writeheader()
    for tx in transactions:
        writer.writerow({
            "id": tx.get("id"),
            "date": tx.get("created_at", "")[:10],
            "type": tx.get("type"),
            "category": tx.get("category"),
            "description": tx.get("description", ""),
            "merchant": tx.get("merchant", ""),
            "amount": tx.get("amount"),
            "currency": tx.get("currency", "USD"),
            "is_anomaly": tx.get("is_anomaly", False),
        })
    return output.getvalue().encode("utf-8")


def generate_pdf_report(user_name: str, transactions: List[dict], summary: dict, month: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("FMWP Financial Report", styles["Title"]))
    story.append(Paragraph(f"Account: {user_name} | Period: {month}", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("Summary", styles["Heading2"]))
    summary_data = [
        ["Metric", "Value"],
        ["Total Income",    f"${summary.get('income', 0):,.2f}"],
        ["Total Expenses",  f"${summary.get('expenses', 0):,.2f}"],
        ["Net Savings",     f"${summary.get('net', 0):,.2f}"],
        ["Savings Rate",    f"{summary.get('savings_rate', 0):.1f}%"],
        ["Anomalies Found", str(summary.get("anomaly_count", 0))],
    ]
    summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING",    (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("Transaction History", styles["Heading2"]))
    tx_data = [["Date", "Type", "Category", "Amount", "Anomaly"]]
    for tx in transactions[:50]:
        tx_data.append([
            str(tx.get("created_at", ""))[:10],
            tx.get("type", "").upper(),
            tx.get("category", ""),
            f"${tx.get('amount', 0):,.2f}",
            "YES" if tx.get("is_anomaly") else "",
        ])
    tx_table = Table(tx_data, colWidths=[1.2*inch, 1*inch, 1.3*inch, 1*inch, 0.8*inch])
    tx_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTSIZE",   (0, 0), (-1, -1), 8),
        ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
        ("PADDING",    (0, 0), (-1, -1), 5),
    ]))
    story.append(tx_table)
    doc.build(story)
    return buffer.getvalue()