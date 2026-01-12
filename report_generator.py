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
        story.append(Paragraph("VirtualFusion Stock Analyzer", self.styles['CustomTitle']))
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
            ['Current Price', f"${metrics['Current Price']:.2f}"],
            ['Market Cap', f"${metrics['Market Cap']/1e9:.2f}B" if metrics['Market Cap'] > 1e9 else f"${metrics['Market Cap']/1e6:.2f}M"],
            ['P/E Ratio', f"{metrics['P/E Ratio']:.2f}"],
            ['Target Price', f"${metrics['Target Price']:.2f}"],
            ['Analyst Rating', metrics['Analyst Rating'].upper()]
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
            ['P/E Ratio', f"{metrics['P/E Ratio']:.2f}", 'Forward P/E', f"{metrics['Forward P/E']:.2f}"],
            ['PEG Ratio', f"{metrics['PEG Ratio']:.2f}", 'Price/Book', f"{metrics['Price to Book']:.2f}"],
            ['Market Cap', f"${metrics['Market Cap']/1e9:.2f}B", 'Enterprise Value', 'N/A'],
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
            ['Gross Margin', f"{metrics['Gross Margin']:.2f}%"],
            ['Operating Margin', f"{metrics['Operating Margin']:.2f}%"],
            ['Profit Margin', f"{metrics['Profit Margin']:.2f}%"],
            ['Return on Equity (ROE)', f"{metrics['ROE']:.2f}%"],
            ['Return on Assets (ROA)', f"{metrics['ROA']:.2f}%"],
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
            ['Revenue Growth', f"{metrics['Revenue Growth']:.2f}%"],
            ['Earnings Growth', f"{metrics['Earnings Growth']:.2f}%"],
            ['Beta', f"{metrics['Beta']:.2f}"],
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
        
        health_data = [
            ['Metric', 'Value', 'Assessment'],
            ['Debt to Equity', f"{metrics['Debt to Equity']:.2f}", 
             'Low' if metrics['Debt to Equity'] < 0.5 else 'Moderate' if metrics['Debt to Equity'] < 1.5 else 'High'],
            ['Current Ratio', f"{metrics['Current Ratio']:.2f}",
             'Good' if metrics['Current Ratio'] > 1.5 else 'Fair' if metrics['Current Ratio'] > 1.0 else 'Poor'],
            ['Quick Ratio', f"{metrics['Quick Ratio']:.2f}",
             'Good' if metrics['Quick Ratio'] > 1.0 else 'Fair' if metrics['Quick Ratio'] > 0.5 else 'Poor'],
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
        before making investment decisions. VirtualFusion is not responsible for any investment losses."""
        story.append(Paragraph(disclaimer, self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        return output_path
    
    def _generate_recommendation(self, score, metrics):
        """Generate investment recommendation based on analysis"""
        
        if score >= 80:
            recommendation = f"""<b>STRONG BUY</b>: This stock scores exceptionally well ({score}/100) across multiple 
            fundamental metrics. With strong profitability (Gross Margin: {metrics['Gross Margin']:.1f}%), 
            solid returns (ROE: {metrics['ROE']:.1f}%), and reasonable valuation (P/E: {metrics['P/E Ratio']:.1f}), 
            this represents an attractive investment opportunity for long-term growth."""
        
        elif score >= 65:
            recommendation = f"""<b>BUY</b>: This stock demonstrates good fundamental strength ({score}/100) with 
            above-average performance in key metrics. The profitability margins of {metrics['Gross Margin']:.1f}% 
            and ROE of {metrics['ROE']:.1f}% indicate solid operational efficiency. Consider adding to portfolio 
            with appropriate position sizing."""
        
        elif score >= 50:
            recommendation = f"""<b>HOLD</b>: This stock shows moderate performance ({score}/100) with mixed signals. 
            While some metrics are favorable, others suggest caution. Current valuation at P/E of {metrics['P/E Ratio']:.1f} 
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
        story.append(Paragraph("VirtualFusion Stock Analyzer", self.styles['CustomTitle']))
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
            table_data.append([
                row['Ticker'],
                row['Company'][:20] + '...' if len(row['Company']) > 20 else row['Company'],
                f"{row['Score']:.0f}",
                f"${row['Price']:.2f}",
                f"${row['Market Cap']/1e9:.1f}B" if row['Market Cap'] > 1e9 else f"${row['Market Cap']/1e6:.0f}M",
                f"{row['P/E Ratio']:.1f}",
                f"{row['Gross Margin']:.1f}%",
                f"{row['ROE']:.1f}%",
                f"{row['Revenue Growth']:.1f}%",
                f"{row['Debt/Equity']:.2f}",
                f"{row['Dividend Yield']:.2f}%"
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
            story.append(Paragraph(
                f"<b>{idx}. {stock['Ticker']}</b> - Score: {stock['Score']:.0f}/100",
                self.styles['Normal']
            ))
            story.append(Paragraph(
                f"   {stock['Company']} | Price: ${stock['Price']:.2f} | P/E: {stock['P/E Ratio']:.1f} | ROE: {stock['ROE']:.1f}%",
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
