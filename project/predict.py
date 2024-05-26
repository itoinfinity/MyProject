import pandas as pd
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly
from statsmodels.tools.eval_measures import rmse
from sklearn.model_selection import train_test_split


pipeline = [
    {
        "$project": {
            "ip": 1,
            'customer': 1,
            "entry_time": {
                "$dateToString": {
                    "format": "%Y-%m-%d",
                    "date": "$entry_time"
                }
            }
        }
    },
    {
        "$group": {
            "_id": {
                "entry_time": "$entry_time",
                "customer": "$customer"
            },
            "count": {
                "$sum": 1
            }
        }
    },
    {
        "$project": {
            "_id": 0,
            'customer': '$_id.customer',
            "ds": "$_id.entry_time",
            "y": "$count"
        }
    }
]

def predict(db,user):
    data = list(db.Injections.aggregate(pipeline))

    df = pd.DataFrame(data)
    df = df.sort_values(by='ds')  # Sort data by 'ds'

    df = df[df['customer'] == user]

    if len(df)<2:
        return False,False,False

    #fig = px.line(df, x='ds', y='y', title='Time Series Data', labels={'y': 'Count'})
    #graph1=fig.to_html(full_html=False)

    # Splitting the data by a percentage
    #df = pd.read_csv('C:/Users/Work/SQLInjectionNLP/InjectionsAggFormatted.csv')
    train, test = train_test_split(df, train_size=0.8, test_size=0.2, shuffle=False)
    m = Prophet(weekly_seasonality=False)
    m.fit(train)
    future = m.make_future_dataframe(periods=7)
    forecast = m.predict(future)

    fig = plot_plotly(m, forecast)
    figcomp = plot_components_plotly(m,forecast)
    graph=fig.to_html(full_html=False)

    #fig = plot_components_plotly(m, forecast)
    graphcomp=figcomp.to_html(full_html=False)

    predictions = forecast.iloc[-len(test['y']):]['yhat']

    return graph,graphcomp,test['y'].mean(),rmse(predictions, test['y'])
