"""
Enterprise-Grade Styling Component
Day mode (light theme) only
"""

import streamlit as st

def apply_platform_theme():
    """Apply day mode theme - light background, dark text"""
    
    # Day mode colors only
    bg_primary = "#ffffff"
    bg_secondary = "#f8fafc"
    bg_tertiary = "#f1f5f9"
    bg_elevated = "#e2e8f0"
    
    text_primary = "#0f172a"
    text_secondary = "#1e293b"
    text_tertiary = "#475569"
    
    border_subtle = "#e2e8f0"
    border_medium = "#cbd5e1"
    
    nav_bg = "#ffffff"
    nav_border = "#e2e8f0"
    nav_text = "#0f172a"
    nav_text_secondary = "#475569"
    nav_hover = "#f1f5f9"
    nav_active = "#3b82f6"
    nav_text_active = "#ffffff"
    
    shadow = "0 1px 3px rgba(0, 0, 0, 0.1)"
    shadow_lg = "0 10px 15px -3px rgba(0, 0, 0, 0.1)"
    
    st.markdown(f"""
    <style>
        /* ===== CSS VARIABLES ===== */
        :root {{
            --bg-primary: {bg_primary};
            --bg-secondary: {bg_secondary};
            --bg-tertiary: {bg_tertiary};
            --bg-elevated: {bg_elevated};
            
            --text-primary: {text_primary};
            --text-secondary: {text_secondary};
            --text-tertiary: {text_tertiary};
            
            --accent-primary: #3b82f6;
            --accent-success: #10b981;
            --accent-warning: #f59e0b;
            --accent-danger: #ef4444;
            
            --border-subtle: {border_subtle};
            --border-medium: {border_medium};
            
            --nav-bg: {nav_bg};
            --nav-border: {nav_border};
            --nav-text: {nav_text};
            --nav-text-secondary: {nav_text_secondary};
            --nav-hover: {nav_hover};
            --nav-active: {nav_active};
            --nav-text-active: {nav_text_active};
            
            --shadow: {shadow};
            --shadow-lg: {shadow_lg};
        }}
        
        /* ===== GLOBAL STYLES ===== */
        * {{
            box-sizing: border-box;
        }}
        
        .stApp {{
            background: var(--bg-primary);
        }}
        
        .main .block-container {{
            padding-top: calc(2rem + 64px);
            padding-bottom: 2rem;
            max-width: 1600px;
        }}
        
        /* ===== TYPOGRAPHY ===== */
        h1, h2, h3, h4, h5, h6 {{
            color: var(--text-primary) !important;
            font-weight: 600;
            letter-spacing: -0.02em;
            line-height: 1.3;
        }}
        
        h1 {{ font-size: 2.25rem; font-weight: 700; }}
        h2 {{ font-size: 1.875rem; font-weight: 600; }}
        h3 {{ font-size: 1.5rem; font-weight: 600; }}
        h4 {{ font-size: 1.25rem; font-weight: 600; }}
        
        p, span, div, label, li {{
            color: var(--text-secondary) !important;
        }}
        
        /* ===== TOP NAVIGATION ===== */
        .top-nav {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 64px;
            background: var(--nav-bg);
            border-bottom: 1px solid var(--nav-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 2rem;
            z-index: 999;
            box-shadow: var(--shadow);
        }}
        
        .nav-brand {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--nav-text);
        }}
        
        .nav-links {{
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}
        
        .nav-link {{
            padding: 0.5rem 1rem;
            color: var(--nav-text-secondary);
            text-decoration: none;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s ease;
            white-space: nowrap;
        }}
        
        .nav-link:hover {{
            background: var(--nav-hover);
            color: var(--nav-text);
        }}
        
        .nav-link.active {{
            background: var(--nav-active);
            color: var(--nav-text-active);
        }}
        
        .nav-spacer {{
            height: 64px;
        }}
        
        /* ===== HIDE SIDEBAR ===== */
        [data-testid="stSidebar"] {{
            display: none !important;
        }}
        
        /* ===== CARDS ===== */
        .enterprise-card {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 1.5rem;
            transition: all 0.2s ease;
        }}
        
        .enterprise-card:hover {{
            border-color: var(--border-medium);
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }}
        
        /* ===== BUTTONS ===== */
        .stButton > button {{
            background: linear-gradient(135deg, var(--accent-primary) 0%, #2563eb 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            font-size: 0.9375rem !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
            text-transform: none !important;
            letter-spacing: 0.01em !important;
        }}
        
        .stButton > button:hover {{
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important;
            transform: translateY(-2px) !important;
        }}
        
        .stButton > button:active {{
            transform: translateY(0px) !important;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3) !important;
        }}
        
        /* Primary buttons */
        button[kind="primary"] {{
            background: linear-gradient(135deg, var(--accent-primary) 0%, #2563eb 100%) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
        }}
        
        button[kind="primary"]:hover {{
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important;
        }}
        
        /* Secondary buttons - enhanced visibility */
        button[kind="secondary"] {{
            background: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
            border: 2px solid var(--border-medium) !important;
            border-radius: 10px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            font-size: 0.9375rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        }}
        
        button[kind="secondary"]:hover {{
            background: var(--bg-elevated) !important;
            border-color: var(--accent-primary) !important;
            box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2) !important;
            transform: translateY(-2px) !important;
        }}
        
        /* Feature card buttons - enhanced with gradients and better visibility */
        button[kind="secondary"][data-testid*="nav"] {{
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-elevated) 100%) !important;
            border: 2px solid var(--accent-primary) !important;
            border-radius: 16px !important;
            padding: 2.5rem 2rem !important;
            text-align: center !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            width: 100% !important;
            min-height: 220px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            cursor: pointer !important;
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            font-size: 1.125rem !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15) !important;
            position: relative !important;
            overflow: hidden !important;
        }}
        
        button[kind="secondary"][data-testid*="nav"]::before {{
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.1), transparent) !important;
            transition: left 0.5s ease !important;
        }}
        
        button[kind="secondary"][data-testid*="nav"]:hover::before {{
            left: 100% !important;
        }}
        
        button[kind="secondary"][data-testid*="nav"]:hover {{
            transform: translateY(-10px) scale(1.02) !important;
            box-shadow: 0 16px 40px rgba(59, 130, 246, 0.3) !important;
            border-color: var(--accent-primary) !important;
            background: linear-gradient(135deg, var(--bg-elevated) 0%, var(--bg-secondary) 100%) !important;
        }}
        
        button[kind="secondary"][data-testid*="nav"]:active {{
            transform: translateY(-6px) scale(1.01) !important;
        }}
        
        /* Feature card button text styling */
        button[kind="secondary"][data-testid*="nav"] strong {{
            font-size: 1.375rem !important;
            font-weight: 700 !important;
            color: var(--text-primary) !important;
            display: block !important;
            margin-bottom: 0.75rem !important;
            letter-spacing: -0.02em !important;
        }}
        
        button[kind="secondary"][data-testid*="nav"] p {{
            font-size: 0.9375rem !important;
            color: var(--text-secondary) !important;
            line-height: 1.6 !important;
            margin: 0 !important;
            font-weight: 400 !important;
        }}
        
        /* Legacy feature-card-button class */
        .feature-card-button {{
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-elevated) 100%) !important;
            border: 2px solid var(--accent-primary) !important;
            border-radius: 16px !important;
            padding: 2.5rem 2rem !important;
            text-align: center !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            width: 100% !important;
            min-height: 220px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            cursor: pointer !important;
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            font-size: 1.125rem !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15) !important;
        }}
        
        .feature-card-button:hover {{
            transform: translateY(-10px) scale(1.02) !important;
            box-shadow: 0 16px 40px rgba(59, 130, 246, 0.3) !important;
            border-color: var(--accent-primary) !important;
            background: linear-gradient(135deg, var(--bg-elevated) 0%, var(--bg-secondary) 100%) !important;
        }}
        
        /* ===== INPUTS ===== */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div {{
            background: var(--bg-tertiary);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            color: var(--text-primary);
            padding: 0.625rem 0.875rem;
        }}
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }}
        
        /* ===== METRICS ===== */
        [data-testid="stMetricValue"] {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary) !important;
        }}
        
        [data-testid="stMetricLabel"] {{
            font-size: 0.875rem;
            color: var(--text-secondary) !important;
            font-weight: 500;
        }}
        
        /* ===== TABS ===== */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.5rem;
            border-bottom: 1px solid var(--border-subtle);
        }}
        
        .stTabs [data-baseweb="tab"] {{
            padding: 0.75rem 1.5rem;
            border-radius: 8px 8px 0 0;
            font-weight: 500;
            color: var(--text-secondary) !important;
            transition: all 0.2s ease;
        }}
        
        .stTabs [aria-selected="true"] {{
            background: var(--bg-elevated);
            color: var(--accent-primary) !important;
            border-bottom: 2px solid var(--accent-primary);
        }}
        
        /* ===== DATA TABLES ===== */
        .stDataFrame {{
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        /* ===== EXPANDERS ===== */
        .streamlit-expanderHeader {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 1rem;
            font-weight: 500;
            color: var(--text-primary) !important;
        }}
        
        .streamlit-expanderContent {{
            color: var(--text-secondary) !important;
        }}
        
        /* ===== FORMS ===== */
        form[data-testid="stForm"] button[type="submit"],
        div[data-testid="stForm"] button[kind="formSubmit"] {{
            display: block !important;
            background: linear-gradient(135deg, var(--accent-primary) 0%, #2563eb 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.875rem 2rem !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
            margin-top: 1rem !important;
        }}
        
        form[data-testid="stForm"] button[type="submit"]:hover,
        div[data-testid="stForm"] button[kind="formSubmit"]:hover {{
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important;
            transform: translateY(-2px) !important;
        }}
        
        /* Download buttons */
        .stDownloadButton > button {{
            background: linear-gradient(135deg, var(--accent-success) 0%, #059669 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            font-size: 0.9375rem !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
        }}
        
        .stDownloadButton > button:hover {{
            background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4) !important;
            transform: translateY(-2px) !important;
        }}
        
        /* Link buttons */
        .stLinkButton > button {{
            background: transparent !important;
            color: var(--accent-primary) !important;
            border: 2px solid var(--accent-primary) !important;
            border-radius: 10px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            font-size: 0.9375rem !important;
            transition: all 0.3s ease !important;
        }}
        
        .stLinkButton > button:hover {{
            background: var(--accent-primary) !important;
            color: white !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
            transform: translateY(-2px) !important;
        }}
        
        /* ===== STREAMLIT TEXT ELEMENTS ===== */
        .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div {{
            color: var(--text-secondary) !important;
        }}
        
        .stSubheader {{
            color: var(--text-primary) !important;
        }}
        
        .stCaption {{
            color: var(--text-tertiary) !important;
        }}
        
        /* ===== INFO/WARNING/SUCCESS ===== */
        .stAlert, .stInfo, .stWarning, .stSuccess, .stError {{
            color: var(--text-secondary) !important;
        }}
        
        /* ===== HIDE STREAMLIT BRANDING ===== */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        header {{ visibility: hidden; }}
        
        /* ===== RESPONSIVE ===== */
        @media (max-width: 768px) {{
            .main .block-container {{
                padding-left: 1rem;
                padding-right: 1rem;
            }}
            
            .top-nav {{
                padding: 0 1rem;
            }}
            
            .nav-links {{
                gap: 0.125rem;
            }}
            
            .nav-link {{
                padding: 0.5rem 0.75rem;
                font-size: 0.8125rem;
            }}
            
            /* Larger buttons on mobile for better touch targets */
            .stButton > button,
            button[kind="primary"],
            button[kind="secondary"] {{
                padding: 1rem 1.5rem !important;
                font-size: 1rem !important;
                min-height: 48px !important;
            }}
            
            /* Feature cards on mobile */
            button[kind="secondary"][data-testid*="nav"] {{
                min-height: 180px !important;
                padding: 2rem 1.5rem !important;
            }}
            
            button[kind="secondary"][data-testid*="nav"] strong {{
                font-size: 1.25rem !important;
            }}
            
            button[kind="secondary"][data-testid*="nav"] p {{
                font-size: 0.875rem !important;
            }}
        }}
        
        /* Tablet optimizations */
        @media (min-width: 769px) and (max-width: 1024px) {{
            button[kind="secondary"][data-testid*="nav"] {{
                min-height: 200px !important;
                padding: 2.25rem 1.75rem !important;
            }}
        }}
        
        /* Enhanced focus states for accessibility */
        .stButton > button:focus,
        button[kind="primary"]:focus,
        button[kind="secondary"]:focus,
        button[kind="secondary"][data-testid*="nav"]:focus {{
            outline: 3px solid rgba(59, 130, 246, 0.5) !important;
            outline-offset: 2px !important;
        }}
        
        /* Loading state for buttons */
        .stButton > button:disabled,
        button[kind="primary"]:disabled,
        button[kind="secondary"]:disabled {{
            opacity: 0.6 !important;
            cursor: not-allowed !important;
            transform: none !important;
        }}
    </style>
    """, unsafe_allow_html=True)

def render_header(title, subtitle=""):
    """Render clean enterprise header"""
    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <h1 style="margin: 0 0 0.5rem 0; font-size: 2.5rem; font-weight: 700; color: var(--text-primary); letter-spacing: -0.03em;">
            {title}
        </h1>
        {f'<p style="margin: 0; font-size: 1.125rem; color: var(--text-secondary); font-weight: 400;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

def render_footer():
    """Render minimal footer"""
    st.markdown("""
    <div style="margin-top: 4rem; padding-top: 2rem; border-top: 1px solid var(--border-subtle); text-align: center;">
        <p style="color: var(--text-tertiary); font-size: 0.875rem; margin: 0;">Laurent Stock Analyzer Pro</p>
    </div>
    """, unsafe_allow_html=True)

def render_trading_signal_card(label, value, subtitle="", signal_type="neutral", format_currency=True):
    """Render clean trading signal card"""
    colors = {
        "buy": {"bg": "rgba(16, 185, 129, 0.1)", "border": "#10b981", "text": "#10b981"},
        "sell": {"bg": "rgba(239, 68, 68, 0.1)", "border": "#ef4444", "text": "#ef4444"},
        "neutral": {"bg": "var(--bg-secondary)", "border": "var(--border-subtle)", "text": "var(--text-primary)"}
    }
    color = colors.get(signal_type, colors["neutral"])
    
    value_str = f"${value:,.2f}" if format_currency and isinstance(value, (int, float)) else str(value)
    
    st.markdown(f"""
    <div style="background: {color['bg']}; border: 1px solid {color['border']}; border-radius: 12px; padding: 1.5rem; text-align: center;">
        <p style="color: var(--text-secondary); font-size: 0.875rem; font-weight: 500; margin: 0 0 0.5rem 0; text-transform: uppercase; letter-spacing: 0.05em;">
            {label}
        </p>
        <h2 style="color: {color['text']}; font-size: 2rem; font-weight: 700; margin: 0;">
            {value_str}
        </h2>
        {f'<p style="color: var(--text-tertiary); font-size: 0.875rem; margin: 0.5rem 0 0 0;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

def render_buy_sell_badge(signal_type, text=""):
    """Render clean badge"""
    colors = {
        "buy": {"bg": "#10b981", "text": "white"},
        "sell": {"bg": "#ef4444", "text": "white"}
    }
    color = colors.get(signal_type, {"bg": "#64748b", "text": "white"})
    display_text = text if text else signal_type.upper()
    
    st.markdown(f"""
    <span style="background: {color['bg']}; color: {color['text']}; padding: 0.375rem 0.875rem; border-radius: 6px; 
                font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
        {display_text}
    </span>
    """, unsafe_allow_html=True)

def render_analyst_ranking_panel(ratings_result, current_price, ticker="", data=None, intrinsic_value=None):
    """
    Render enterprise-grade analyst ranking panel with trends and projections
    """
    if not ratings_result:
        st.markdown("""
        <div style="background: var(--bg-secondary); padding: 1.5rem; border-radius: 12px; border: 1px solid var(--border-subtle); text-align: center;">
            <p style="color: var(--text-secondary); margin: 0;">Analyst ratings not available</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    composite_rating = ratings_result.get('composite_rating', 'N/A')
    avg_score = ratings_result.get('average_rating_score', 0)
    num_sources = ratings_result.get('number_of_sources', 0)
    ratings_list = ratings_result.get('ratings', [])
    
    # Get target prices
    target_mean = 0
    target_high = 0
    target_low = 0
    num_analysts = 0
    
    for rating in ratings_list:
        if rating.get('target_price', 0) > 0:
            if target_mean == 0:
                target_mean = rating.get('target_price', 0)
            else:
                target_mean = (target_mean + rating.get('target_price', 0)) / 2
        if rating.get('target_high', 0) > 0:
            target_high = max(target_high, rating.get('target_high', 0))
        if rating.get('target_low', 0) > 0:
            if target_low == 0:
                target_low = rating.get('target_low', 0)
            else:
                target_low = min(target_low, rating.get('target_low', 0))
        num_analysts = max(num_analysts, rating.get('analysts', 0))
    
    # Calculate trend
    if target_mean > 0 and current_price > 0:
        price_change_pct = ((target_mean - current_price) / current_price) * 100
        if price_change_pct > 10:
            trend = "Strong Bullish"
            trend_color = "#10b981"
        elif price_change_pct > 5:
            trend = "Bullish"
            trend_color = "#10b981"
        elif price_change_pct > -5:
            trend = "Neutral"
            trend_color = "#f59e0b"
        elif price_change_pct > -10:
            trend = "Bearish"
            trend_color = "#ef4444"
        else:
            trend = "Strong Bearish"
            trend_color = "#ef4444"
    else:
        trend = "N/A"
        trend_color = "#64748b"
        price_change_pct = 0
    
    # Rating colors
    if "STRONG BUY" in composite_rating or avg_score >= 4.5:
        rating_color = "#10b981"
        rating_bg = "rgba(16, 185, 129, 0.1)"
    elif "BUY" in composite_rating or avg_score >= 3.5:
        rating_color = "#3b82f6"
        rating_bg = "rgba(59, 130, 246, 0.1)"
    elif "HOLD" in composite_rating or 2.5 <= avg_score < 3.5:
        rating_color = "#f59e0b"
        rating_bg = "rgba(245, 158, 11, 0.1)"
    else:
        rating_color = "#ef4444"
        rating_bg = "rgba(239, 68, 68, 0.1)"
    
    # Rating distribution
    rating_distribution = {}
    for rating in ratings_list:
        rating_key = rating.get('rating', 'N/A')
        rating_distribution[rating_key] = rating_distribution.get(rating_key, 0) + 1
    
    # Format targets
    target_low_str = f"${target_low:.2f}" if target_low > 0 else "N/A"
    target_mean_str = f"${target_mean:.2f}" if target_mean > 0 else "N/A"
    target_high_str = f"${target_high:.2f}" if target_high > 0 else "N/A"
    
    # Build rating dist HTML
    rating_dist_html = ""
    for rating_key, count in rating_distribution.items():
        if rating_key != 'N/A':
            if "STRONG BUY" in rating_key or "BUY" in rating_key:
                dist_color = "#10b981"
            elif "HOLD" in rating_key:
                dist_color = "#f59e0b"
            else:
                dist_color = "#ef4444"
            
            rating_dist_html += (
                f'<div style="background: var(--bg-tertiary); padding: 0.5rem 1rem; border-radius: 6px; '
                f'border: 1px solid {dist_color}; display: inline-block; margin: 0.25rem;">'
                f'<span style="color: {dist_color}; font-weight: 600; font-size: 0.875rem;">{rating_key}</span>'
                f'<span style="color: var(--text-secondary); margin-left: 0.5rem; font-size: 0.875rem;">({count})</span>'
                f'</div>'
            )
    
    # Price change HTML
    price_change_html = ""
    if target_mean > 0 and current_price > 0:
        price_change_color = "#10b981" if price_change_pct > 0 else "#ef4444"
        price_change_html = f'<p style="color: {price_change_color}; margin: 0.5rem 0 0 0; font-size: 0.875rem;">{price_change_pct:+.1f}% from current</p>'
    
    # Render panel
    panel_html = (
        f'<div style="background: var(--bg-secondary); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 2rem; margin: 1.5rem 0;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem;">'
        f'<h3 style="color: var(--text-primary); margin: 0; font-size: 1.5rem; font-weight: 600;">Analyst Consensus</h3>'
        f'<div style="background: {rating_bg}; padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid {rating_color};">'
        f'<span style="color: {rating_color}; font-weight: 600; font-size: 1rem;">{composite_rating}</span>'
        f'</div></div>'
        f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">'
        f'<div style="background: {rating_bg}; padding: 1rem; border-radius: 8px; border-left: 3px solid {rating_color};">'
        f'<p style="color: var(--text-secondary); margin: 0 0 0.5rem 0; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">Consensus Score</p>'
        f'<h2 style="color: {rating_color}; margin: 0; font-size: 1.75rem; font-weight: 700;">{avg_score:.2f}/5.0</h2>'
        f'</div>'
        f'<div style="background: rgba(59, 130, 246, 0.1); padding: 1rem; border-radius: 8px; border-left: 3px solid #3b82f6;">'
        f'<p style="color: var(--text-secondary); margin: 0 0 0.5rem 0; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">Analysts</p>'
        f'<h2 style="color: #3b82f6; margin: 0; font-size: 1.75rem; font-weight: 700;">{num_analysts if num_analysts > 0 else num_sources}</h2>'
        f'</div>'
        f'<div style="background: rgba(245, 158, 11, 0.1); padding: 1rem; border-radius: 8px; border-left: 3px solid {trend_color};">'
        f'<p style="color: var(--text-secondary); margin: 0 0 0.5rem 0; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">Price Trend</p>'
        f'<h2 style="color: {trend_color}; margin: 0; font-size: 1.25rem; font-weight: 700;">{trend}</h2>'
        f'</div>'
        f'<div style="background: rgba(100, 116, 139, 0.1); padding: 1rem; border-radius: 8px; border-left: 3px solid #64748b;">'
        f'<p style="color: var(--text-secondary); margin: 0 0 0.5rem 0; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">Sources</p>'
        f'<h2 style="color: #64748b; margin: 0; font-size: 1.75rem; font-weight: 700;">{num_sources}</h2>'
        f'</div></div>'
        f'<div style="background: var(--bg-tertiary); padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem;">'
        f'<h4 style="color: var(--text-primary); margin: 0 0 1rem 0; font-size: 1rem; font-weight: 600;">Price Predictions</h4>'
        f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">'
        f'<div style="text-align: center; padding: 1rem; background: rgba(239, 68, 68, 0.1); border-radius: 6px; border: 1px solid #ef4444;">'
        f'<p style="color: var(--text-secondary); margin: 0 0 0.5rem 0; font-size: 0.75rem;">Low Target</p>'
        f'<p style="color: #ef4444; margin: 0; font-size: 1.25rem; font-weight: 700;">{target_low_str}</p>'
        f'</div>'
        f'<div style="text-align: center; padding: 1rem; background: rgba(59, 130, 246, 0.1); border-radius: 6px; border: 1px solid #3b82f6;">'
        f'<p style="color: var(--text-secondary); margin: 0 0 0.5rem 0; font-size: 0.75rem;">Mean Target</p>'
        f'<p style="color: #3b82f6; margin: 0; font-size: 1.25rem; font-weight: 700;">{target_mean_str}</p>'
        f'{price_change_html}'
        f'</div>'
        f'<div style="text-align: center; padding: 1rem; background: rgba(16, 185, 129, 0.1); border-radius: 6px; border: 1px solid #10b981;">'
        f'<p style="color: var(--text-secondary); margin: 0 0 0.5rem 0; font-size: 0.75rem;">High Target</p>'
        f'<p style="color: #10b981; margin: 0; font-size: 1.25rem; font-weight: 700;">{target_high_str}</p>'
        f'</div></div></div>'
        f'<div style="background: var(--bg-tertiary); padding: 1.5rem; border-radius: 8px;">'
        f'<h4 style="color: var(--text-primary); margin: 0 0 1rem 0; font-size: 1rem; font-weight: 600;">Rating Distribution</h4>'
        f'<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">{rating_dist_html}</div>'
        f'</div></div>'
    )
    
    st.markdown(panel_html, unsafe_allow_html=True)
    
    # Add projection chart
    if data and data.get('history') is not None and len(data.get('history', [])) > 0:
        from utils.visualizations import create_analyst_projection_chart
        try:
            projection_chart = create_analyst_projection_chart(
                data, ratings_result, intrinsic_value, current_price, ticker
            )
            if projection_chart:
                st.markdown("---")
                st.markdown("### Price Evolution Projections")
                st.plotly_chart(projection_chart, use_container_width=True)
        except Exception as e:
            pass
