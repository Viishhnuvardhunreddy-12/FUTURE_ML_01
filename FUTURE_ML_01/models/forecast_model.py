import pandas as pd
from prophet import Prophet
import os
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import json
from datetime import datetime

def calculate_metrics(actual, predicted):
    """Calculate forecast accuracy metrics"""
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    r2 = r2_score(actual, predicted)
    mape = np.mean(np.abs((actual - predicted) / actual)) * 100
    return {
        'mae': round(mae, 2),
        'rmse': round(rmse, 2),
        'r2': round(r2, 4),
        'mape': round(mape, 2)
    }

def serialize_dates(obj):
    """Helper function to serialize datetime objects"""
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.strftime('%Y-%m-%d')
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def generate_forecast(df):
    try:
        print("Starting forecast generation")
        # Prepare data for Prophet
        df_prophet = pd.DataFrame()
        
        # Convert ORDERDATE to datetime, handling various formats
        try:
            # Try multiple date formats
            date_formats = ['%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y']
            converted = False
            
            for date_format in date_formats:
                try:
                    df_prophet['ds'] = pd.to_datetime(df['ORDERDATE'], format=date_format)
                    converted = True
                    print(f"Successfully converted dates using format: {date_format}")
                    break
                except:
                    continue
            
            if not converted:
                # Try pandas' automatic parsing
                df_prophet['ds'] = pd.to_datetime(df['ORDERDATE'])
                print("Successfully converted dates using automatic parsing")
                
        except Exception as e:
            print(f"Error converting dates: {str(e)}")
            raise Exception("Could not parse dates. Please ensure dates are in a standard format (e.g., MM/DD/YYYY)")

        # Convert SALES to numeric, handling various formats
        try:
            # Remove any currency symbols and commas
            sales_str = df['SALES'].astype(str).str.replace('$', '', regex=False)
            sales_str = sales_str.str.replace(',', '', regex=False)
            sales_str = sales_str.str.strip()
            
            # Convert to numeric
            df_prophet['y'] = pd.to_numeric(sales_str, errors='coerce')
            
            # Check for negative values
            if (df_prophet['y'] < 0).any():
                print("Warning: Negative sales values found")
            
            # Remove any rows with NaN values
            df_prophet = df_prophet.dropna()
            
        except Exception as e:
            print(f"Error converting sales: {str(e)}")
            raise Exception("Could not convert sales to numeric values. Please ensure sales are numeric.")

        if len(df_prophet) == 0:
            raise Exception("No valid data points after cleaning")

        print(f"Processing {len(df_prophet)} valid data points")
        
        # Group by date and sum the sales for each date
        df_prophet = df_prophet.groupby('ds')['y'].sum().reset_index()
        
        # Sort by date
        df_prophet = df_prophet.sort_values('ds')
        
        print("Fitting Prophet model")
        # Initialize and fit the model with appropriate parameters
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative',
            interval_width=0.95,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10
        )
        
        # Add custom seasonalities if enough data
        if len(df_prophet) > 90:  # At least 3 months of data
            model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
            model.add_seasonality(name='quarterly', period=91.25, fourier_order=5)
        
        model.fit(df_prophet)
        
        print("Generating future dates")
        # Create future dates for forecasting
        future_dates = model.make_future_dataframe(periods=30)
        
        print("Making predictions")
        # Generate forecast
        forecast = model.predict(future_dates)
        
        # Ensure no negative values in forecast
        forecast['yhat'] = forecast['yhat'].clip(lower=0)
        forecast['yhat_lower'] = forecast['yhat_lower'].clip(lower=0)
        forecast['yhat_upper'] = forecast['yhat_upper'].clip(lower=0)
        
        # Calculate accuracy metrics for historical data
        historical_forecast = forecast[forecast['ds'].isin(df_prophet['ds'])]
        metrics = calculate_metrics(df_prophet['y'].values, historical_forecast['yhat'].values)
        
        # Extract seasonality components
        seasonality = {
            'yearly': forecast['yearly'].tolist() if 'yearly' in forecast.columns else [],
            'weekly': forecast['weekly'].tolist() if 'weekly' in forecast.columns else [],
            'monthly': forecast['monthly'].tolist() if 'monthly' in forecast.columns else [],
            'quarterly': forecast['quarterly'].tolist() if 'quarterly' in forecast.columns else []
        }
        
        # Prepare forecast data for JSON serialization
        forecast_data = []
        for _, row in forecast.iterrows():
            forecast_data.append({
                'ds': row['ds'].strftime('%Y-%m-%d'),
                'yhat': float(row['yhat']),
                'yhat_lower': float(row['yhat_lower']),
                'yhat_upper': float(row['yhat_upper'])
            })
        
        # Prepare original data for JSON serialization
        original_data = []
        for _, row in df_prophet.iterrows():
            original_data.append({
                'ds': row['ds'].strftime('%Y-%m-%d'),
                'y': float(row['y'])
            })
        
        # Save detailed results
        results = {
            'forecast_data': forecast_data,
            'original_data': original_data,
            'metrics': metrics,
            'seasonality': seasonality,
            'changepoints': [cp.strftime('%Y-%m-%d') for cp in model.changepoints],
            'trend': forecast['trend'].tolist()
        }
        
        # Save results to JSON for frontend visualization
        with open(os.path.join('uploads', 'forecast_details.json'), 'w') as f:
            json.dump(results, f)
        
        # Save forecast to CSV
        forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_csv(
            os.path.join('uploads', 'forecast.csv'),
            index=False,
            float_format='%.2f'
        )
        
        print("Forecast generation complete")
        return results
        
    except Exception as e:
        print(f"Error in generate_forecast: {str(e)}")
        raise 