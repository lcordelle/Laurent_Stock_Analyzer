"""
PDF Report Generator for Stock Analysis
Generates comprehensive, professional stock analysis reports
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import io
import plotly.graph_objects as go
import pandas as pd


def _fmt(v, suffix="", prefix="", decimals=2):
    """Format metric value safely. Returns 'N/A' if None/missing."""
    try:
        if v is None:
            return "N/A"
        if pd.isna(v):
            return "N/A"
    except (ValueError, TypeError):
        return "N/A"
    try:
        return f"{prefix}{v:.{decimals}f}{suffix}"
    except (ValueError, TypeError):
        return "N/A"


def _fmt_market_cap(v):
    """Format market cap as B or M. Returns 'N/A' if None/missing."""
    try:
        if v is None:
            return "N/A"
        if pd.isna(v):
            return "N/A"
    except (ValueError, TypeError):
        return "N/A"
    try:
        if v >= 1e9:
            return f"${v/1e9:.2f}B"
        return f"${v/1e6:.2f}M"
    except (ValueError, TypeError):
        return "N/A"

class StockReportGenerator:
    """Generate professional PDF reports for stock analysis"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Subsection style
        self.styles.add(ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
    
    def generate_single_stock_report(self, ticker, data, metrics, score, output_path):
        """Generate comprehensive report for a single stock"""
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Title page
        story.append(Paragraph("Laurent Stock Analyzer", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        company_name = data['info'].get('longName', ticker)
        story.append(Paragraph(f"<b>{company_name}</b> ({ticker})", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph(
            f"Analysis Report | {datetime.now().strftime('%B %d, %Y')}",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 30))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        summary_data = [
            ['Overall Score', f"{score['total_score']}/100"],
            ['Current Price', f"${_fmt(metrics.get('Current Price'), decimals=2)}"],
            ['Market Cap', _fmt_market_cap(metrics.get('Market Cap'))],
            ['P/E Ratio', _fmt(metrics.get('P/E Ratio'), decimals=2)],
            ['Target Price', f"${_fmt(metrics.get('Target Price'), decimals=2)}"],
            ['Analyst Rating', metrics.get('Analyst Rating', 'N/A').upper() if metrics.get('Analyst Rating') else 'N/A']
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Company Overview
        story.append(Paragraph("Company Overview", self.styles['SectionHeader']))
        business_summary = data['info'].get('longBusinessSummary', 'No description available')
        story.append(Paragraph(business_summary[:1000], self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Score Breakdown
        story.append(Paragraph("Score Breakdown", self.styles['SectionHeader']))
        
        score_data = []
        score_data.append(['Category', 'Points', 'Assessment'])
        
        for category, points in score['components'].items():
            assessment = 'Excellent' if points >= 18 else 'Good' if points >= 12 else 'Fair' if points >= 6 else 'Poor'
            score_data.append([category, str(points), assessment])
        
        score_table = Table(score_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
        ]))
        
        story.append(score_table)
        story.append(PageBreak())
        
        # Valuation Metrics
        story.append(Paragraph("Valuation Metrics", self.styles['SectionHeader']))
        
        valuation_data = [
            ['Metric', 'Value', 'Metric', 'Value'],
            ['P/E Ratio', _fmt(metrics.get('P/E Ratio'), decimals=2), 'Forward P/E', _fmt(metrics.get('Forward P/E'), decimals=2)],
            ['PEG Ratio', _fmt(metrics.get('PEG Ratio'), decimals=2), 'Price/Book', _fmt(metrics.get('Price to Book'), decimals=2)],
            ['Market Cap', _fmt_market_cap(metrics.get('Market Cap')), 'Enterprise Value', 'N/A'],
        ]
        
        val_table = Table(valuation_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        val_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightblue, colors.white])
        ]))
        
        story.append(val_table)
        story.append(Spacer(1, 20))
        
        # Profitability Metrics
        story.append(Paragraph("Profitability & Efficiency", self.styles['SectionHeader']))
        
        prof_data = [
            ['Metric', 'Value'],
            ['Gross Margin', f"{_fmt(metrics.get('Gross Margin'), decimals=2)}%"],
            ['Operating Margin', f"{_fmt(metrics.get('Operating Margin'), decimals=2)}%"],
            ['Profit Margin', f"{_fmt(metrics.get('Profit Margin'), decimals=2)}%"],
            ['Return on Equity (ROE)', f"{_fmt(metrics.get('ROE'), decimals=2)}%"],
            ['Return on Assets (ROA)', f"{_fmt(metrics.get('ROA'), decimals=2)}%"],
        ]
        
        prof_table = Table(prof_data, colWidths=[3*inch, 3*inch])
        prof_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgreen, colors.white])
        ]))
        
        story.append(prof_table)
        story.append(Spacer(1, 20))
        
        # Growth Metrics
        story.append(Paragraph("Growth & Momentum", self.styles['SectionHeader']))
        
        growth_data = [
            ['Metric', 'Value'],
            ['Revenue Growth', f"{_fmt(metrics.get('Revenue Growth'), decimals=2)}%"],
            ['Earnings Growth', f"{_fmt(metrics.get('Earnings Growth'), decimals=2)}%"],
            ['Beta', _fmt(metrics.get('Beta'), decimals=2)],
        ]
        
        growth_table = Table(growth_data, colWidths=[3*inch, 3*inch])
        growth_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightyellow, colors.white])
        ]))
        
        story.append(growth_table)
        story.append(PageBreak())
        
        # Financial Health
        story.append(Paragraph("Financial Health", self.styles['SectionHeader']))
        
        de_val = metrics.get('Debt to Equity')
        cr_val = metrics.get('Current Ratio')
        qr_val = metrics.get('Quick Ratio')

        health_data = [
            ['Metric', 'Value', 'Assessment'],
            ['Debt to Equity', _fmt(de_val, decimals=2),
             'Low' if de_val and de_val < 0.5 else 'Moderate' if de_val and de_val < 1.5 else 'High' if de_val else 'N/A'],
            ['Current Ratio', _fmt(cr_val, decimals=2),
             'Good' if cr_val and cr_val > 1.5 else 'Fair' if cr_val and cr_val > 1.0 else 'Poor' if cr_val else 'N/A'],
            ['Quick Ratio', _fmt(qr_val, decimals=2),
             'Good' if qr_val and qr_val > 1.0 else 'Fair' if qr_val and qr_val > 0.5 else 'Poor' if qr_val else 'N/A'],
        ]
        
        health_table = Table(health_data, colWidths=[2*inch, 2*inch, 2*inch])
        health_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightcoral, colors.white])
        ]))
        
        story.append(health_table)
        story.append(Spacer(1, 30))
        
        # Recommendation
        story.append(Paragraph("Investment Recommendation", self.styles['SectionHeader']))
        
        recommendation = self._generate_recommendation(score['total_score'], metrics)
        story.append(Paragraph(recommendation, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Disclaimer
        story.append(Paragraph("Disclaimer", self.styles['SubSection']))
        disclaimer = """This report is for informational purposes only and does not constitute financial advice. 
        Past performance is not indicative of future results. Please consult with a qualified financial advisor 
        before making investment decisions. Laurent is not responsible for any investment losses."""
        story.append(Paragraph(disclaimer, self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        return output_path
    
    def _generate_recommendation(self, score, metrics):
        """Generate investment recommendation based on analysis"""

        gm = metrics.get('Gross Margin')
        roe = metrics.get('ROE')
        pe = metrics.get('P/E Ratio')

        gm_str = _fmt(gm, decimals=1) if gm else "N/A"
        roe_str = _fmt(roe, decimals=1) if roe else "N/A"
        pe_str = _fmt(pe, decimals=1) if pe else "N/A"

        if score >= 80:
            recommendation = f"""<b>STRONG BUY</b>: This stock scores exceptionally well ({score}/100) across multiple
            fundamental metrics. With strong profitability (Gross Margin: {gm_str}%),
            solid returns (ROE: {roe_str}%), and reasonable valuation (P/E: {pe_str}),
            this represents an attractive investment opportunity for long-term growth."""

        elif score >= 65:
            recommendation = f"""<b>BUY</b>: This stock demonstrates good fundamental strength ({score}/100) with
            above-average performance in key metrics. The profitability margins of {gm_str}%
            and ROE of {roe_str}% indicate solid operational efficiency. Consider adding to portfolio
            with appropriate position sizing."""

        elif score >= 50:
            recommendation = f"""<b>HOLD</b>: This stock shows moderate performance ({score}/100) with mixed signals.
            While some metrics are favorable, others suggest caution. Current valuation at P/E of {pe_str}
            should be evaluated in context of growth prospects. Existing positions can be maintained, but new purchases
            should be carefully considered."""

        elif score >= 35:
            recommendation = f"""<b>REDUCE</b>: This stock scores below average ({score}/100) with several concerning
            fundamental indicators. Profitability metrics and growth indicators suggest potential challenges ahead.
            Consider reducing exposure and reallocating to stronger opportunities."""

        else:
            recommendation = f"""<b>SELL</b>: This stock shows weak fundamental performance ({score}/100) across multiple
            critical metrics. Current financials indicate significant risks. Consider exiting positions and seeking
            alternatives with stronger fundamental profiles."""

        return recommendation
    
    def generate_comparison_report(self, comparison_df, output_path):
        """Generate comparison report for multiple stocks"""
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Laurent Stock Analyzer", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Multi-Stock Comparison Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            f"Analysis Date: {datetime.now().strftime('%B %d, %Y')}",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 30))
        
        # Summary
        story.append(Paragraph("Comparison Summary", self.styles['SectionHeader']))
        story.append(Paragraph(
            f"This report compares {len(comparison_df)} stocks across multiple fundamental metrics.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 20))
        
        # Convert dataframe to table data
        table_data = [comparison_df.columns.tolist()]
        for _, row in comparison_df.iterrows():
            price_val = row.get('Price', None)
            mc_val = row.get('Market Cap', None)
            pe_val = row.get('P/E Ratio', None)
            gm_val = row.get('Gross Margin', None)
            roe_val = row.get('ROE', None)
            rg_val = row.get('Revenue Growth', None)
            de_val = row.get('Debt/Equity', None)
            dy_val = row.get('Dividend Yield', None)

            price_str = f"${_fmt(price_val, decimals=2)}"
            mc_str = _fmt_market_cap(mc_val) if mc_val and not pd.isna(mc_val) else "N/A"
            pe_str = _fmt(pe_val, decimals=1)
            gm_str = f"{_fmt(gm_val, decimals=1)}%"
            roe_str = f"{_fmt(roe_val, decimals=1)}%"
            rg_str = f"{_fmt(rg_val, decimals=1)}%"
            de_str = _fmt(de_val, decimals=2)
            dy_str = f"{_fmt(dy_val, decimals=2)}%"

            table_data.append([
                row['Ticker'],
                row['Company'][:20] + '...' if len(row['Company']) > 20 else row['Company'],
                f"{row['Score']:.0f}",
                price_str,
                mc_str,
                pe_str,
                gm_str,
                roe_str,
                rg_str,
                de_str,
                dy_str
            ])
        
        # Create table with adjusted column widths
        col_widths = [0.5*inch, 1.2*inch, 0.5*inch, 0.7*inch, 0.8*inch, 0.6*inch, 
                     0.7*inch, 0.6*inch, 0.7*inch, 0.7*inch, 0.7*inch]
        
        comparison_table = Table(table_data, colWidths=col_widths)
        comparison_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightblue, colors.white])
        ]))
        
        story.append(comparison_table)
        story.append(Spacer(1, 30))
        
        # Top performers
        story.append(Paragraph("Top Performers", self.styles['SectionHeader']))
        
        top_3 = comparison_df.nlargest(3, 'Score')
        for idx, (_, stock) in enumerate(top_3.iterrows(), 1):
            price_val = stock.get('Price', None)
            pe_val = stock.get('P/E Ratio', None)
            roe_val = stock.get('ROE', None)

            price_str = _fmt(price_val, decimals=2)
            pe_str = _fmt(pe_val, decimals=1)
            roe_str = _fmt(roe_val, decimals=1)

            story.append(Paragraph(
                f"<b>{idx}. {stock['Ticker']}</b> - Score: {stock['Score']:.0f}/100",
                self.styles['Normal']
            ))
            story.append(Paragraph(
                f"   {stock['Company']} | Price: ${price_str} | P/E: {pe_str} | ROE: {roe_str}%",
                self.styles['Normal']
            ))
            story.append(Spacer(1, 10))
        
        # Disclaimer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Disclaimer", self.styles['SubSection']))
        disclaimer = """This comparative analysis is for informational purposes only. Past performance does not 
        guarantee future results. Please consult with a qualified financial advisor before making investment decisions."""
        story.append(Paragraph(disclaimer, self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        return output_path

# Example usage function
def create_report_example():
    """Example of how to use the report generator"""
    generator = StockReportGenerator()
    
    # This would be called from the main app with actual data
    # generator.generate_single_stock_report(ticker, data, metrics, score, "report.pdf")
    
    print("Report generator ready to use")

if __name__ == "__main__":
    create_report_example()
