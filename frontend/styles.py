import streamlit as st


def inject_styles():
    st.markdown(
        """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Arvo:wght@400;700&family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {
        --bg-0: #f8fafc;
        --bg-1: #e0f2fe;
        --bg-2: #bae6fd;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --card-bg: rgba(255, 255, 255, 0.65);
        --card-border: rgba(255, 255, 255, 0.4);
        --primary: #0284c7;
        --primary-soft: #38bdf8;
        --accent: #7dd3fc;
        --success: #10b981;
        --danger: #ef4444;
    }

    .stApp {
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
        background:
            radial-gradient(1000px 800px at 0% 0%, rgba(56, 189, 248, 0.15), transparent 60%),
            radial-gradient(800px 600px at 100% 100%, rgba(2, 132, 199, 0.1), transparent 60%),
            linear-gradient(145deg, var(--bg-0) 0%, var(--bg-1) 50%, var(--bg-2) 100%);
        background-attachment: fixed;
    }

    .main .block-container {
        max-width: 1400px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Premium Glassmorphism Cards */
    .glass {
        background: var(--card-bg);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid var(--card-border);
        border-radius: 20px;
        box-shadow: 0 16px 40px rgba(15, 23, 42, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .topbar {
        padding: 0 0 1rem 0;
        margin-bottom: 0.5rem;
    }
    
    .topbar-clean {
        background: transparent;
        border: none;
        box-shadow: none;
        backdrop-filter: none;
        -webkit-backdrop-filter: none;
    }

    .topbar-badges {
        margin-top: 0.6rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .pill {
        font-size: 0.75rem;
        font-weight: 600;
        color: #0284c7;
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 9999px;
        padding: 0.3rem 0.7rem;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
        transition: background 0.2s ease;
    }
    
    .pill:hover {
        background: rgba(255, 255, 255, 1);
    }

    .brand-title {
        font-family: 'Arvo', serif;
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #0f172a 0%, #0284c7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.2rem 0 0 0;
    }

    .brand-sub {
        margin: 0.2rem 0 0 0;
        color: var(--text-secondary);
        font-size: 1.05rem;
        font-weight: 400;
    }

    .status-wrap {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 0.6rem;
        font-size: 0.95rem;
        color: var(--text-secondary);
        font-weight: 600;
        padding-top: 0.5rem;
    }

    .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 10px currentColor; /* glowing dot */
    }

    .section-card {
        padding: 1.5rem 1.8rem;
        margin-bottom: 1.5rem;
    }
    
    .mini-stat {
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.6);
        background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.4) 100%);
        padding: 0.8rem 1rem;
        min-height: 90px;
        box-shadow: 0 4px 15px rgba(15, 23, 42, 0.03);
    }
    
    .mini-stat-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748b;
        margin: 0;
        font-weight: 600;
    }
    
    .mini-stat-value {
        margin: 0.3rem 0 0 0;
        font-size: 1.25rem;
        font-weight: 800;
        color: #0f172a;
    }

    .section-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: -0.01em;
        margin: 0 0 0.3rem 0;
        color: #0f172a;
    }

    .section-subtitle {
        font-size: 0.95rem;
        color: var(--text-secondary);
        margin-bottom: 1.2rem;
    }

    /* Metric Cards in Details Area */
    .metric-card {
        padding: 1.2rem 1.4rem;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.6);
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 1rem;
        height: 100%;
    }

    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
    }

    .metric-label {
        margin: 0;
        font-size: 0.8rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
    }

    .metric-value {
        font-family: 'Arvo', serif;
        margin: 0.4rem 0 0 0;
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }

    .upload-hint {
        border: 2px dashed rgba(2, 132, 199, 0.3);
        background: rgba(255, 255, 255, 0.5);
        border-radius: 18px;
        padding: 1.2rem 1.5rem;
        color: #0f172a;
        font-size: 0.95rem;
        font-weight: 500;
        margin-bottom: 1rem;
        text-align: center;
        transition: all 0.2s ease;
    }
    
    .upload-hint:hover {
        border-color: rgba(2, 132, 199, 0.6);
        background: rgba(255, 255, 255, 0.8);
    }

    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        border-radius: 20px;
        border: 2px dashed rgba(100, 116, 139, 0.2);
        background: rgba(255, 255, 255, 0.4);
        color: #334155;
    }

    .empty-title {
        font-family: 'Arvo', serif;
        font-weight: 700;
        font-size: 1.4rem;
        margin-bottom: 0.5rem;
        color: #0f172a;
    }

    .empty-sub {
        margin: 0;
        font-size: 1.05rem;
        color: #64748b;
        max-width: 500px;
        margin: 0 auto;
    }

    .step-row {
        display: flex;
        justify-content: center;
        gap: 0.8rem;
        margin-top: 1.5rem;
        flex-wrap: wrap;
    }

    .step-chip {
        font-size: 0.8rem;
        border-radius: 9999px;
        padding: 0.3rem 0.8rem;
        border: 1px solid rgba(148, 163, 184, 0.2);
        background: rgba(255, 255, 255, 0.9);
        color: #0f172a;
        font-weight: 700;
        box-shadow: 0 4px 10px rgba(15, 23, 42, 0.04);
    }

    .download-card {
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        background: rgba(255, 255, 255, 0.7);
        padding: 1rem;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 6px 15px rgba(15, 23, 42, 0.02);
    }

    /* Modern Buttons */
    .stButton > button, .stDownloadButton > button {
        border-radius: 12px !important;
        border: none !important;
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 6px 20px rgba(2, 132, 199, 0.25) !important;
        text-transform: none !important;
    }

    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(2, 132, 199, 0.35) !important;
        background: linear-gradient(135deg, #38bdf8 0%, #0369a1 100%) !important;
    }
    
    .stButton > button:active, .stDownloadButton > button:active {
        transform: translateY(0px) !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: rgba(255,255,255,0.5) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.6) !important;
    }
    
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }

    div[data-testid="stImage"] img {
        border-radius: 16px;
        border: 2px solid rgba(255,255,255,0.8);
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
        transition: transform 0.3s ease;
    }

    div[data-testid="stImage"] img:hover {
        transform: scale(1.01);
    }

    /* Customized Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.5);
        border: 1px solid rgba(255,255,255,0.4);
        border-radius: 16px;
        padding: 6px;
        margin-bottom: 1rem;
        flex-wrap: wrap; /* Allows tabs to wrap on small screens */
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 10px 20px;
        font-weight: 700;
        font-size: 0.95rem;
        color: #475569;
        transition: all 0.2s ease;
        white-space: nowrap;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #0f172a;
        background: rgba(255,255,255,0.6);
    }
    
    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #0284c7 !important;
        box-shadow: 0 4px 15px rgba(15, 23, 42, 0.05);
    }

    /* Mobile Responsive Media Queries */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 1rem;
        }

        .brand-title {
            font-size: 1.5rem;
        }
        
        .brand-sub {
            font-size: 0.9rem;
        }
        
        .status-wrap {
            justify-content: flex-start; /* Align left cleanly if wrapped */
            margin-top: 0.5rem;
            font-size: 0.85rem;
        }
        
        div[data-testid="column"] {
            width: 100% !important; /* Force columns to stack */
            flex: 1 1 100% !important;
            margin-bottom: 1rem;
        }

        .section-card {
            padding: 1rem 1.2rem;
        }
        
        .metric-value {
            font-size: 1.4rem;
        }
        
        .metric-card {
            padding: 1rem;
        }

        .pill {
            font-size: 0.7rem;
            padding: 0.25rem 0.6rem;
        }

        .empty-state {
            padding: 2rem 1rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            overflow-x: auto; /* Allow horizontal scroll for tabs */
            flex-wrap: nowrap;
            -webkit-overflow-scrolling: touch;
            padding-bottom: 5px; /* space for scrollbar */
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 8px 12px;
            font-size: 0.85rem;
        }
    }

</style>
        """,
        unsafe_allow_html=True,
    )

