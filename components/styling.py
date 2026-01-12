"""
Styling Component
Provides consistent styling and UI components across the platform
"""

import streamlit as st

def apply_platform_theme():
    """Apply platform-wide theme and styling"""
    st.markdown("""
    <style>
        /* Main Header Styles */
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            padding: 1rem;
        }
        
        /* Card Styles */
        .info-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 0.75rem;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .success-card {
            background: linear-gradient(135deg, #00c853 0%, #4caf50 100%);
            padding: 1.5rem;
            border-radius: 0.75rem;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .warning-card {
            background: linear-gradient(135deg, #ffa726 0%, #ff9800 100%);
            padding: 1.5rem;
            border-radius: 0.75rem;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        
        /* Color Classes */
        .positive {
            color: #00c853;
        }
        
        .negative {
            color: #ff1744;
        }
        
        .neutral {
            color: #ffa726;
        }
        
        /* Footer Styles */
        .footer {
            text-align: center;
            padding: 2rem 0;
            margin-top: 3rem;
            border-top: 1px solid #e0e0e0;
            color: #666;
        }
        
        /* Header Styles */
        .page-header {
            text-align: center;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }
        
        .page-title {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 0.5rem;
        }
        
        .page-subtitle {
            font-size: 1.2rem;
            color: #666;
            margin-top: 0;
        }
        
        /* Responsive adjustments for iPad/mobile */
        @media (max-width: 768px) {
            .page-title {
                font-size: 2rem;
            }
            
            .page-subtitle {
                font-size: 1rem;
            }
            
            .info-card, .success-card, .warning-card {
                padding: 1rem;
            }
        }
        
        /* Streamlit specific overrides */
        .stButton > button {
            width: 100%;
            border-radius: 0.5rem;
            font-weight: 500;
        }
        
        /* Table improvements */
        .stDataFrame {
            border-radius: 0.5rem;
        }
        
        /* Chart container */
        .plotly-container {
            border-radius: 0.5rem;
            overflow: hidden;
        }
    </style>
    """, unsafe_allow_html=True)

def render_header(title, subtitle=""):
    """Render a consistent page header"""
    st.markdown(f"""
    <div class="page-header">
        <h1 class="page-title">{title}</h1>
        {f'<p class="page-subtitle">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

def render_footer():
    """Render a consistent page footer"""
    st.markdown("""
    <div class="footer">
        <p><strong>VirtualFusion Stock Analyzer Pro</strong> | Version 2.0.0</p>
        <p style="font-size: 0.9rem; color: #999;">Advanced AI-Powered Stock Analysis Platform</p>
    </div>
    """, unsafe_allow_html=True)



