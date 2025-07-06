import plotly.graph_objs as go
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# Function to format market capitalization
def format_market_cap(market_cap, currency):
    if market_cap is None:
        return "N/A"
    
    units = ["", "K", "M", "B", "T"]
    i = 0
    while market_cap >= 1000 and i < len(units) - 1:
        market_cap /= 1000.0
        i += 1
    
    return f"{currency} {market_cap:.2f}{units[i]}"

# Function to plot Moving Averages
def plot_moving_averages(data, ticker, currency):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close Price'))
    
    if '50MA' in data.columns and not data['50MA'].isnull().all():
        fig.add_trace(go.Scatter(x=data.index, y=data['50MA'], mode='lines', name='50-day MA'))
    
    if '200MA' in data.columns and not data['200MA'].isnull().all():
        fig.add_trace(go.Scatter(x=data.index, y=data['200MA'], mode='lines', name='200-day MA'))

    fig.update_layout(title=f"{ticker} Moving Averages", xaxis_title="Date", yaxis_title=f"Price ({currency})")
    return fig

# Function to plot RSI
def plot_rsi(data, ticker):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], mode='lines', name='RSI'))
    fig.update_layout(title=f"{ticker} RSI", xaxis_title="Date", yaxis_title="RSI")
    return fig

# Function to plot Bollinger Bands
def plot_bollinger_bands(data, ticker, currency):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close Price'))
    fig.add_trace(go.Scatter(x=data.index, y=data['Upper Band'], mode='lines', name='Upper Band'))
    fig.add_trace(go.Scatter(x=data.index, y=data['Lower Band'], mode='lines', name='Lower Band'))
    fig.update_layout(title=f"{ticker} Bollinger Bands", xaxis_title="Date", yaxis_title=f"Price ({currency})")
    return fig

# Function to plot MACD
def plot_macd(data, ticker):
    fig = go.Figure()
    
    # MACD line in blue
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=data['MACD'], 
        mode='lines', 
        name='MACD',
        line=dict(color='blue')
    ))
    
    # Signal line in orange
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=data['Signal Line'], 
        mode='lines', 
        name='Signal Line',
        line=dict(color='orange')
    ))
    
    fig.update_layout(
        title=f"{ticker} MACD",
        xaxis_title="Date",
        yaxis_title="MACD",
        showlegend=True
    )
    return fig

# Function to plot Stochastic Oscillator
def plot_stochastic_oscillator(data, ticker):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['%K'], mode='lines', name='%K'))
    fig.add_trace(go.Scatter(x=data.index, y=data['%D'], mode='lines', name='%D'))
    fig.update_layout(title=f"{ticker} Stochastic Oscillator", xaxis_title="Date", yaxis_title="Value")
    return fig

# Function to plot Volume
def plot_volume(data, ticker):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume'))
    fig.update_layout(title=f"{ticker} Trading Volume", xaxis_title="Date", yaxis_title="Volume")
    return fig

# Function to plot Average True Range (ATR)
def plot_atr(data, ticker):
    high_low = data['High'] - data['Low']
    high_close = (data['High'] - data['Close'].shift()).abs()
    low_close = (data['Low'] - data['Close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(window=14).mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=atr, mode='lines', name='ATR'))
    fig.update_layout(title=f"{ticker} Average True Range (ATR)", xaxis_title="Date", yaxis_title="ATR")
    return fig

# Function to plot OBV (On-Balance Volume)
def plot_obv(data, ticker):
    obv = (data['Volume'] * (data['Close'].diff() > 0).astype(int)).cumsum()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=obv, mode='lines', name='OBV'))
    fig.update_layout(title=f"{ticker} On-Balance Volume (OBV)", xaxis_title="Date", yaxis_title="OBV")
    return fig

# Function to plot ADX (Average Directional Index)
def plot_adx(data, ticker):
    plus_dm = data['High'].diff()
    minus_dm = data['Low'].diff().abs()
    tr = data[['High', 'Low', 'Close']].max(axis=1) - data[['High', 'Low', 'Close']].min(axis=1)
    atr = tr.rolling(window=14).mean()
    plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.rolling(window=14).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=adx, mode='lines', name='ADX'))
    fig.update_layout(title=f"{ticker} Average Directional Index (ADX)", xaxis_title="Date", yaxis_title="ADX")
    return fig

def calculate_rsi(prices, period=14):
    """Calculate RSI with error handling"""
    try:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # Handle division by zero
        rs = gain / loss.replace(0, float('inf'))
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)  # Fill NaN values with neutral RSI
        
    except Exception as e:
        print(f"RSI calculation error: {str(e)}")
        return pd.Series(50, index=prices.index)  # Return neutral RSI on error

def calculate_macd(prices):
    """Calculate MACD"""
    exp1 = prices.ewm(span=12, adjust=False).mean()
    exp2 = prices.ewm(span=26, adjust=False).mean()
    return exp1 - exp2

def predict_next_days(data, days=7):
    """Simple prediction for next few days based on recent trends"""
    try:
        # Use last 30 days for trend analysis
        recent_data = data[-30:].copy()
        
        # Calculate basic trend indicators
        recent_data['SMA5'] = recent_data['Close'].rolling(window=5).mean()
        recent_data['SMA20'] = recent_data['Close'].rolling(window=20).mean()
        
        # Calculate average daily change
        daily_changes = recent_data['Close'].pct_change().dropna()
        avg_daily_change = daily_changes.mean()
        volatility = daily_changes.std()
        
        # Get last closing price
        last_price = recent_data['Close'].iloc[-1]
        
        # Generate predictions
        predictions = []
        current_price = last_price
        
        for _ in range(days):
            # Predict next day with some randomness based on volatility
            change = avg_daily_change + np.random.normal(0, volatility/2)
            # Limit daily change to ±3%
            change = max(min(change, 0.03), -0.03)
            next_price = current_price * (1 + change)
            predictions.append(next_price)
            current_price = next_price
        
        return predictions, volatility
        
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        return [], 0

def plot_simple_forecast(data, ticker, currency):
    """Plot recent prices and short-term forecast"""
    try:
        # Get predictions for next 7 days
        predictions, volatility = predict_next_days(data, days=7)
        
        if not predictions:
            return go.Figure()
        
        fig = go.Figure()
        
        # Plot last 30 days of actual prices
        recent_data = data[-30:].copy()
        fig.add_trace(go.Scatter(
            x=recent_data.index,
            y=recent_data['Close'],
            mode='lines',
            name='Recent Prices',
            line=dict(color='blue')
        ))
        
        # Plot predictions
        future_dates = pd.date_range(
            start=data.index[-1] + pd.Timedelta(days=1),
            periods=len(predictions),
            freq='D'
        )
        
        # Add prediction line
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=predictions,
            mode='lines+markers',
            name='Forecast',
            line=dict(color='orange', dash='dash')
        ))
        
        # Add confidence interval
        upper_bound = [p * (1 + volatility) for p in predictions]
        lower_bound = [p * (1 - volatility) for p in predictions]
        
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=upper_bound,
            fill=None,
            mode='lines',
            line=dict(width=0),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=lower_bound,
            fill='tonexty',
            mode='lines',
            line=dict(width=0),
            name='Possible Range',
            fillcolor='rgba(255, 165, 0, 0.2)'
        ))
        
        fig.update_layout(
            title=f"{ticker} - 7-Day Forecast",
            xaxis_title="Date",
            yaxis_title=f"Price ({currency})",
            hovermode='x'
        )
        
        return fig
        
    except Exception as e:
        print(f"Plotting error: {str(e)}")
        return go.Figure()
