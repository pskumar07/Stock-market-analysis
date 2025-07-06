import streamlit as st
import yfinance as yf
import requests
from requests.exceptions import RequestException
from utils import (
    format_market_cap,
    plot_moving_averages,
    plot_rsi,
    plot_bollinger_bands,
    plot_macd,
    plot_stochastic_oscillator,
    plot_volume,
    plot_atr,
    plot_obv,
    plot_adx,
    predict_next_days,
    plot_simple_forecast,
)
import json
from datetime import datetime
import os
import pandas as pd
from io import BytesIO
import time
import numpy as np

try:
    import openpyxl
except ImportError:
    st.error("Please install openpyxl: pip install openpyxl")
    st.stop()

# Add this at the top of your file
st.set_page_config(
    page_title="Stock Price Visualizer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App Title
st.title("📊 Stock Price Visualizer with Technical Indicators Knowledge")

# Add these near the top, after the title
st.markdown("""
### 📈 Welcome to Stock Price Visualizer!
This tool helps you analyze stocks using technical indicators and predictive analysis.
""")

# Add a quick guide section
with st.expander("🔍 Quick Guide - How to Use"):
    st.markdown("""
    1. **Enter Stock Symbol**: Type a stock symbol (e.g., AAPL for Apple) in the input box
    2. **Select Time Period**: Choose how far back you want to analyze
    3. **Click Show Stock Data**: View comprehensive analysis including:
        - Company Information
        - Price Predictions
        - Technical Indicators
        
    **Pro Tips:**
    - Use the sidebar for quick stock suggestions
    - Expand each indicator section to learn more about its interpretation
    - Hover over charts for detailed values
    """)

# Sidebar with Stock Suggestions
st.sidebar.title("💡 Stock Suggestions")
stock_suggestions = {
    "Apple": "AAPL",
    "Tesla": "TSLA",
    "Google": "GOOGL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "NVIDIA": "NVDA",
    "Meta (Facebook)": "META",
    "Netflix": "NFLX",
}
for name, symbol in stock_suggestions.items():
    st.sidebar.write(f"**{name}** - {symbol}")

# User input for stock ticker
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, TSLA, GOOGL):", "AAPL").upper()

# Add this after the ticker input
if not ticker:
    st.info("💡 Not sure what to look for? Check the stock suggestions in the sidebar!")

# Select time period or custom date range
period_options = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"]
period = st.selectbox("Select Time Period:", period_options, index=3)

# Add smooth transitions between sections
st.markdown("""
<style>
    /* Smooth transitions */
    .stButton>button {
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    /* Animated expandable sections */
    .streamlit-expanderHeader {
        transition: background-color 0.3s ease;
    }
    .streamlit-expanderHeader:hover {
        background-color: #f0f2f6;
    }
    
    /* Smooth chart animations */
    .js-plotly-plot {
        transition: all 0.3s ease;
    }
    
    /* Loading animation */
    .stSpinner {
        animation: spinner 1s linear infinite;
    }
</style>
""", unsafe_allow_html=True)

# Function to fetch stock data with retry mechanism
def fetch_stock_data(ticker, period, retries=5, backoff_factor=1):
    for i in range(retries):
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            if data.empty:
                raise Exception("No data received")
            return stock, data
        except requests.exceptions.HTTPError as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                wait_time = backoff_factor * (2 ** i)
                st.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                st.error(f"HTTP error occurred: {str(e)}")
                break
        except RequestException as e:
            st.error(f"Network error occurred: {str(e)}")
            break
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            break
    st.error("Failed to fetch stock data after multiple attempts. Please try again later.")
    return None, None

# Add loading state
if st.button("Show Stock Data"):
    with st.spinner("Loading stock data... Please wait..."):
        stock, data = fetch_stock_data(ticker, period)

    if data is not None and not data.empty:
        # Add success message
        st.success(f"Successfully loaded data for {ticker}")
        
        # Add a download button for the data
        csv = data.to_csv()
        st.download_button(
            label="📥 Download Stock Data",
            data=csv,
            file_name=f'{ticker}_stock_data.csv',
            mime='text/csv',
        )

        # Fetch Stock Information
        info = stock.info # type: ignore
        company_name = info.get('longName', 'N/A')
        sector = info.get('sector', 'N/A')
        industry = info.get('industry', 'N/A')
        country = info.get('country', 'N/A')
        currency = info.get('currency', 'USD')
        market_cap = info.get('marketCap', None)
        website = info.get('website', 'N/A')
        summary = info.get('longBusinessSummary', 'N/A')

        market_cap_str = format_market_cap(market_cap, currency)

        # Display Stock Information
        with st.expander("Stock Information", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Company Name:** {company_name}")
                st.write(f"**Sector:** {sector}")
                st.write(f"**Industry:** {industry}")
                st.write(f"**Country:** {country}")
            with col2:
                st.write(f"**Market Cap:** {market_cap_str}")
                st.write(f"**Currency:** {currency}")
                st.write(f"**Website:** [Visit Website]({website})")

        # Display Overview in Separate Expander
        with st.expander("Company Overview"):
            st.markdown(f"**Overview:** {summary}")

        # Simple Price Forecast
        with st.expander("📊 7-Day Price Forecast"):
            st.markdown("""
            ### Simple Price Forecast 📈

            #### What You're Looking At:
            - **Blue Line**: Recent actual prices (last 30 days)
            - **Orange Line**: Estimated future prices (next 7 days)
            - **Shaded Area**: Possible price range based on market volatility

            #### How This Forecast Works:
            1. Analyzes recent price trends
            2. Considers market volatility
            3. Calculates possible price ranges
            4. Updates daily with new data

            ⚠️ **Important Warnings:**
            - Past performance doesn't guarantee future results
            - Market conditions can change rapidly
            - External events can impact prices significantly
            - This is just one of many analysis tools
            - Never invest based solely on predictions

            💡 **Best Practices:**
            1. Use multiple sources of information
            2. Consider market news and events
            3. Monitor company fundamentals
            4. Understand your risk tolerance
            """)
            
            try:
                fig_forecast = plot_simple_forecast(data, ticker, currency)
                st.plotly_chart(fig_forecast)
                
                # Show basic stats with enhanced context
                predictions, volatility = predict_next_days(data, days=7)
                if predictions:
                    last_price = data['Close'].iloc[-1]
                    pred_change = ((predictions[-1] - last_price) / last_price) * 100
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "Current Price",
                            f"{currency} {last_price:.2f}"
                        )
                        st.write(f"Market Volatility: {volatility*100:.1f}%")
                        if volatility*100 > 3:
                            st.warning("⚠️ High volatility detected - exercise caution!")
                        elif volatility*100 < 1:
                            st.info("ℹ️ Low volatility period - typically more stable")
                    
                    with col2:
                        st.metric(
                            "7-Day Estimate",
                            f"{currency} {predictions[-1]:.2f}",
                            f"{pred_change:+.2f}%"
                        )
                        if abs(pred_change) > 10:
                            st.warning("⚠️ Large price movement predicted - higher uncertainty!")
                    
                    # Add market context
                    st.markdown("""
                    #### Understanding Volatility:
                    - **Low** (<1%): Market is relatively calm
                    - **Medium** (1-3%): Normal market conditions
                    - **High** (>3%): Market showing significant uncertainty
                    
                    *Remember: Higher volatility means higher risk!*
                    """)
                        
            except Exception as e:
                st.error("Unable to generate forecast. Please try again with different data.")

        # Technical Indicators Section
        st.header("📊 Technical Indicators Guide")
        
        # Enhanced Educational Overview
        with st.expander("❓ New to Technical Analysis? Start Here!", expanded=True):
            st.markdown("""
            # Welcome to Technical Analysis! 📈

            ### What is Technical Analysis?
            Technical analysis is a method to analyze and forecast market trends by studying historical price and volume data.

            ### Key Benefits:
            1. 📊 Helps identify trends
            2. 🎯 Spots potential entry/exit points
            3. 📉 Manages risk
            4. 🔄 Times market movements

            ### Important Principles:
            - **Price Action**: Markets move in trends
            - **History**: Patterns tend to repeat
            - **Volume**: Confirms price movements
            - **Momentum**: Trends continue until they don't

            ### ⚠️ Essential Warnings:
            1. No indicator is perfect
            2. Past performance doesn't guarantee future results
            3. Different indicators may give conflicting signals
            4. Market conditions can change rapidly
            5. Always use multiple indicators together

            ### 🎓 Best Practices:
            1. Start with basic indicators
            2. Practice with historical data
            3. Combine multiple indicators
            4. Consider fundamental analysis too
            5. Keep learning and adapting

            ### 🚫 Common Mistakes to Avoid:
            - Relying on a single indicator
            - Ignoring market context
            - Over-trading based on indicators
            - Not setting stop-losses
            - Fighting the trend

            ### 💡 Pro Tips:
            - Start with longer timeframes
            - Look for confirmation from multiple indicators
            - Always consider the broader market context
            - Use indicators as tools, not absolute signals
            - Maintain a trading journal
            """)

        # Moving Averages with enhanced explanation
        with st.expander("📈 Moving Averages - Trend Analysis"):
            st.markdown("""
            ### Understanding Moving Averages
            
            #### What It Shows:
            - **50-day MA (Blue Line)**: Short-term trend
            - **200-day MA (Orange Line)**: Long-term trend
            
            #### How to Read:
            1. **Uptrend**: When shorter MA is above longer MA
            2. **Downtrend**: When shorter MA is below longer MA
            3. **Golden Cross**: Short MA crosses above long MA (Bullish)
            4. **Death Cross**: Short MA crosses below long MA (Bearish)
            
            #### Trading Signals:
            - **Buy**: When price crosses above MAs
            - **Sell**: When price crosses below MAs
            """)
            fig = plot_moving_averages(data, ticker, currency)
            st.plotly_chart(fig)

        # RSI with educational content
        with st.expander("💪 RSI - Momentum Indicator"):
            # Calculate RSI
            delta = data["Close"].astype(float).diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data["RSI"] = 100 - (100 / (1 + rs))
            
            st.markdown("""
            ### Relative Strength Index (RSI)
            
            #### What It Measures:
            Speed and magnitude of recent price changes to evaluate overvalued or undervalued conditions.
            
            #### Key Levels:
            - **Above 70**: Overbought (Consider Selling)
            - **Below 30**: Oversold (Consider Buying)
            - **50 Level**: Neutral
            
            #### Best Used For:
            - Finding entry/exit points
            - Spotting potential reversals
            - Confirming trends
            """)
            fig_rsi = plot_rsi(data, ticker)
            st.plotly_chart(fig_rsi)

        # Bollinger Bands with clear explanation
        with st.expander("🎯 Bollinger Bands - Volatility & Price Ranges"):
            # Calculate Bollinger Bands
            data["20MA"] = data["Close"].rolling(window=20).mean()
            data["Upper Band"] = data["20MA"] + (data["Close"].rolling(window=20).std() * 2)
            data["Lower Band"] = data["20MA"] - (data["Close"].rolling(window=20).std() * 2)
            
            st.markdown("""
            ### Understanding Bollinger Bands
            
            #### What They Show:
            Three lines that help you see:
            1. **Middle Band**: 20-day moving average
            2. **Upper Band**: High price range
            3. **Lower Band**: Low price range
            
            #### How to Use:
            - **Wide Bands**: High volatility
            - **Narrow Bands**: Low volatility
            - **Price near Upper Band**: Potentially overbought
            - **Price near Lower Band**: Potentially oversold
            
            #### Trading Signals:
            - Consider buying when price touches lower band
            - Consider selling when price touches upper band
            """)
            fig_bb = plot_bollinger_bands(data, ticker, currency)
            st.plotly_chart(fig_bb)

        # MACD with beginner-friendly explanation
        with st.expander("🔄 MACD - Trend & Momentum Combined"):
            # Calculate MACD
            data["12EMA"] = data["Close"].ewm(span=12, adjust=False).mean()
            data["26EMA"] = data["Close"].ewm(span=26, adjust=False).mean()
            data["MACD"] = data["12EMA"] - data["26EMA"]
            data["Signal Line"] = data["MACD"].ewm(span=9, adjust=False).mean()
            
            st.markdown("""
            ### Moving Average Convergence Divergence (MACD)
            
            #### Simple Explanation:
            MACD helps you spot trend changes and momentum shifts.
            
            #### Key Components:
            1. **MACD Line**: Fast line (Blue)
            2. **Signal Line**: Slow line (Orange)
            3. **Histogram**: Bars showing difference between lines
            
            #### Trading Signals:
            - **Buy Signal**: MACD crosses above Signal Line
            - **Sell Signal**: MACD crosses below Signal Line
            
            #### Pro Tip:
            *Stronger signals occur when crossovers happen far from the zero line*
            """)
            fig_macd = plot_macd(data, ticker)
            st.plotly_chart(fig_macd)

        # Volume Analysis with clear explanation
        with st.expander("📊 Volume - Trading Activity"):
            st.markdown("""
            ### Understanding Volume
            
            #### What Is Volume?
            Number of shares traded during a specific period.
            
            #### Why It's Important:
            - Confirms price movements
            - Shows trading interest
            - Helps validate trends
            
            #### How to Read:
            - **High Volume**: Strong market interest
            - **Low Volume**: Weak market interest
            - **Rising Volume**: Trend likely to continue
            - **Falling Volume**: Trend might reverse
            """)
            fig_volume = plot_volume(data, ticker)
            st.plotly_chart(fig_volume)

        # Add a glossary of terms
        with st.expander("📚 Technical Analysis Glossary"):
            st.markdown("""
            ### Common Terms Explained
            
            #### Basic Concepts:
            - **Trend**: Overall direction of price movement
            - **Support**: Price level where buying pressure is strong
            - **Resistance**: Price level where selling pressure is strong
            - **Volume**: Number of shares traded
            - **Volatility**: Rate of price change
            
            #### Pattern Types:
            - **Bullish**: Indicating potential price increase
            - **Bearish**: Indicating potential price decrease
            - **Consolidation**: Sideways price movement
            
            #### Trading Terms:
            - **Long Position**: Buying shares
            - **Short Position**: Selling borrowed shares
            - **Stop Loss**: Price level to exit losing trade
            - **Take Profit**: Price level to exit winning trade
            """)

        # Update the Learning Resources section
        with st.expander("📚 Learning Resources"):
            st.markdown("""
            ### Educational Resources
            
            #### Free Learning Platforms
            - [Investopedia Technical Analysis Course](https://www.investopedia.com/technical-analysis-4689657)
            - [TradingView Educational Articles](https://www.tradingview.com/education/)
            - [Yahoo Finance Market Analysis](https://finance.yahoo.com/education/)
            
            #### Technical Analysis Basics
            - [Understanding Chart Patterns](https://www.investopedia.com/articles/technical/112601.asp)
            - [Technical Indicators Guide](https://www.investopedia.com/terms/t/technicalindicator.asp)
            - [Candlestick Patterns](https://www.investopedia.com/trading/candlestick-charting-what-is-it/)
            
            #### Recommended Tools
            - [TradingView Charts](https://www.tradingview.com/chart/)
            - [Yahoo Finance](https://finance.yahoo.com/)
            - [MarketWatch](https://www.marketwatch.com/)
            
            #### Practice & Paper Trading
            - [TD Ameritrade paperMoney](https://www.tdameritrade.com/tools-and-platforms/thinkorswim/papermoney.html)
            - [Webull Paper Trading](https://www.webull.com/introduce)
            - [Trading Game](https://www.marketwatch.com/game)
            
            ⚠️ **Disclaimer**: These resources are for educational purposes only. Always do your own research and consider consulting with a financial advisor before making investment decisions.
            """)

    else:
        st.error("Invalid ticker or no data available.")

# Add this near the bottom, above the footer
st.sidebar.markdown("""
### 📊 Additional Resources
- [Yahoo Finance](https://finance.yahoo.com/)
- [Investopedia](https://www.investopedia.com/)
- [Trading View](https://www.tradingview.com/)
""")

# Create a feedback storage file if it doesn't exist
FEEDBACK_FILE = "feedback.json"
if not os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, "w") as f:
        json.dump([], f)

# Modify the feedback section in the sidebar
with st.sidebar.expander("📝 Feedback"):
    st.markdown("""
    We'd love to hear your thoughts!
    - What features would you like to see?
    - Found any issues?
    - General suggestions?
    """)
    user_name = st.text_input("Your Name (optional):", key="feedback_name")
    feedback_text = st.text_area("Your feedback:", key="feedback_text")
    feedback_type = st.selectbox(
        "Feedback Type:",
        ["General", "Bug Report", "Feature Request", "Suggestion"]
    )
    
    if st.button("Submit Feedback"):
        if feedback_text.strip():
            # Read existing feedback
            with open(FEEDBACK_FILE, "r") as f:
                feedback_data = json.load(f)
            
            # Add new feedback
            feedback_data.append({
                "name": user_name if user_name else "Anonymous",
                "type": feedback_type,
                "feedback": feedback_text,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Save updated feedback
            with open(FEEDBACK_FILE, "w") as f:
                json.dump(feedback_data, f, indent=4)
            
            st.success("Thank you for your feedback! 🙏")
            
            # Clear the form by using empty values in a new run
            st.rerun()
        else:
            st.error("Please enter some feedback before submitting.")

# Add a feedback viewer section (only visible to admins)
if st.sidebar.checkbox("View Feedback (Admin)", key="show_feedback"):
    admin_password = st.sidebar.text_input("Admin Password:", type="password", key="admin_pass")
    if admin_password == "admin123":  # Replace with a secure password in production
        st.sidebar.subheader("📊 Feedback Dashboard")
        
        try:
            with open(FEEDBACK_FILE, "r") as f:
                all_feedback = json.load(f)
            
            if all_feedback:
                # Add Excel download button
                df = pd.DataFrame(all_feedback)
                output = BytesIO()
                df.to_excel(output, index=False)
                excel_data = output.getvalue()
                st.sidebar.download_button(
                    label="📥 Download Feedback as Excel",
                    data=excel_data,
                    file_name="feedback_data.xlsx",
                    mime="application/vnd.ms-excel"
                )
                
                # Filter options
                feedback_types = ["All"] + list(set(f["type"] for f in all_feedback))
                selected_type = st.sidebar.selectbox("Filter by Type:", feedback_types)
                
                # Filter feedback
                filtered_feedback = all_feedback
                if selected_type != "All":
                    filtered_feedback = [f for f in all_feedback if f["type"] == selected_type]
                
                # Display feedback with delete option
                for idx, feedback in enumerate(reversed(filtered_feedback)):
                    with st.sidebar.expander(f"{feedback['type']} - {feedback['timestamp']}"):
                        st.write(f"**From:** {feedback['name']}")
                        st.write(f"**Feedback:** {feedback['feedback']}")
                        
                        # Simple delete button without password check
                        if st.button(f"🗑️ Delete Feedback #{idx+1}", key=f"delete_{idx}"):
                            try:
                                # Find and remove the feedback
                                for i, f in enumerate(all_feedback):
                                    if (f['timestamp'] == feedback['timestamp'] and 
                                        f['feedback'] == feedback['feedback']):
                                        all_feedback.pop(i)
                                        break
                                
                                # Save updated feedback
                                with open(FEEDBACK_FILE, "w") as f:
                                    json.dump(all_feedback, f, indent=4)
                                st.success("✅ Feedback deleted!")
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                
                # Add feedback statistics
                st.sidebar.subheader("📈 Feedback Statistics")
                feedback_counts = {}
                for f in all_feedback:
                    feedback_counts[f["type"]] = feedback_counts.get(f["type"], 0) + 1
                
                for ftype, count in feedback_counts.items():
                    st.sidebar.write(f"{ftype}: {count}")
            else:
                st.sidebar.info("No feedback submitted yet.")
                
        except Exception as e:
            st.sidebar.error(f"Error loading feedback: {str(e)}")
    elif admin_password:
        st.sidebar.error("Incorrect password!")

# Update the footer with more information
st.markdown("""
<div style="position: fixed; bottom: 0; left: 0; width: 100%; background-color: black; color: white; text-align: center; padding: 10px;">
    <div style="font-size: 16px; font-weight: bold;">Stock Visualizer</div>
    <div style="font-size: 12px;">Powered by Yahoo Finance | Data updates every 24 hours</div>
    <div style="font-size: 12px;">⚠️ This tool is for educational purposes only. Not financial advice.</div>
</div>
""", unsafe_allow_html=True)

