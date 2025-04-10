# Sales Forecasting Application

A web-based application for time series forecasting of sales data using Facebook's Prophet algorithm. This tool allows users to upload sales data, generate forecasts, and visualize trends and seasonal patterns.

## Features

- **Data Upload**: Support for CSV files with date and sales data
- **Automated Forecasting**: Generate 30-day sales forecasts with confidence intervals
- **Interactive Visualizations**: View historical vs. predicted sales in interactive charts
- **Seasonal Decomposition**: Analyze yearly, weekly, monthly, and quarterly patterns
- **Performance Metrics**: Evaluate forecast quality with MAE, RMSE, R², and MAPE
- **Data Export**: Download forecast results as CSV files

## Technology Stack

- **Backend**: Python, Flask
- **Forecasting**: Facebook Prophet, Scikit-learn
- **Data Processing**: Pandas, NumPy
- **Frontend**: JavaScript, Chart.js, Bootstrap 5
- **Visualization**: Interactive charts for trends and seasonal patterns

## Installation

### Prerequisites
- Python 3.7+
- pip package manager

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sales-forecasting-app.git
   cd sales-forecasting-app
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Upload your CSV file:
   - The file must have at least two columns: `ORDERDATE` and `SALES`
   - Date formats supported: MM/DD/YYYY, YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY
   - Sales can include currency symbols and formatting (e.g., $1,234.56)

4. View and analyze the forecast results:
   - Main forecast chart with confidence intervals
   - Key performance metrics
   - Seasonal decomposition patterns
   - Download the forecast for further analysis

## CSV File Format

Your CSV file should contain at least these two columns:

The application will automatically handle:
- Different date formats
- Currency symbols and thousand separators in sales values
- Missing values and data cleaning

## Technical Details

### Forecasting Model

The application uses Facebook's Prophet algorithm which is particularly well-suited for:
- Time series data with strong seasonal patterns
- Data with missing values or outliers
- Multiple seasonality periods (yearly, weekly, etc.)
- Growth trend changes

### Performance Metrics

- **MAE (Mean Absolute Error)**: Average absolute difference between predicted and actual values
- **RMSE (Root Mean Square Error)**: Square root of the average squared difference
- **R² Score**: Proportion of variance in the dependent variable predictable from the independent variable
- **MAPE (Mean Absolute Percentage Error)**: Average percentage difference between predicted and actual values

## Development

### Project Structure

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Facebook Prophet](https://facebook.github.io/prophet/) for the forecasting algorithm
- [Chart.js](https://www.chartjs.org/) for interactive visualizations
- [Bootstrap](https://getbootstrap.com/) for the responsive UI
