import pandas as pd
from flask import Flask, flash, redirect, render_template,request, session, url_for
import plotly.express as px
from pymongo import MongoClient
import api,predict

app = Flask(__name__)
app.secret_key = 'Test'
client = MongoClient("mongodb://localhost:27017/")
db = client["admin"]
app.config['db'] = db

month_order = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]
 
app.register_blueprint(api.api_bp)

@app.before_request
def check_session():
    global user
    if 'user' in session:
        user = session.get('user',None)
    else:
        user=None

@app.route('/injection',methods=['GET'])
def injection():
    return render_template('injection.html')

@app.route('/')
def home():
    data = db.Injections.find()

    df = pd.DataFrame(data)
    df['count'] = df.groupby(['latitude', 'longitude']).latitude.transform('count')

    fig = px.density_mapbox(
        df,
        lat='latitude',
        lon='longitude',
        radius=10,  # Adjust the radius based on your preference
        center={'lat': df['latitude'].mean(), 'lon': df['longitude'].mean()},
        zoom=5,
        hover_name='city',
        color_continuous_scale="Viridis",
        color_continuous_midpoint=df['count'].mean(),
        mapbox_style='carto-positron',
        title='Injections around the world'
    )

    graph_html = fig.to_html(full_html=False)
    return render_template('index.html', graph_html=graph_html)

@app.route('/dashboard')
def dashboard():
    if user == None:
        return redirect(url_for('login'))

    selected_sector = request.args.get('sector', default='Financial', type=str)
    selected_year = request.args.get('year', default='2024', type=str)
    
    data_user = list(db.Injections.find({'customer': session['user']}))
    
    pipeline = [
        {
            "$lookup": {
                "from": "Company",
                "localField": "customer",
                "foreignField": "Login",
                "as": "company_info"
            }
        },
        {
            "$unwind": "$company_info"
        },
        {
            "$project": {
                "ip": 1,
                "city": 1,
                "country": 1,
                "longitude": 1,
                "latitude": 1,
                "customer": "$company_info.CompanyName",
                "type": 1,
                "string": 1,
                "entry_time": 1,
                "company_info.CompanyName": 1,
                "company_info.CompanyType": 1  # Include flattened fields
            }
        }
    ]
    data_sector = list(db['Injections'].aggregate(pipeline))
    
    if not data_user:
        chloropeth_html = bar_html = False
    else:
        df1 = pd.DataFrame(data_user)
        df1['entry_time'] = pd.to_datetime(df1['entry_time'])
        df1['Year'] = df1['entry_time'].dt.year
        if selected_year != 'all':
            df_selected_year = df1[df1['Year'] == int(selected_year)]
        else:
            df_selected_year = df1
        bar_html, chloropeth_html = create_bar_and_map_plots(df_selected_year,
                                                         f'{selected_year if selected_year != "all" else "All Years"}')

    
    df2 = pd.json_normalize(data_sector)
    df2['entry_time'] = pd.to_datetime(df2['entry_time'])
    df2['Year'] = df2['entry_time'].dt.year
    
    unique_years = df2['Year'].unique()
    unique_sectors = df2['company_info.CompanyType'].unique()
    
    if selected_year != 'all':
        df_selected_year2 = df2[df2['Year'] == int(selected_year)]
    else:
        df_selected_year2 = df2

    df_selected_year2 = df_selected_year2[df_selected_year2['company_info.CompanyType'] == selected_sector]

    bar_html2, chloropeth_html2 = create_bar_and_map_plots(df_selected_year2,
                                                           f'{selected_year if selected_year != "all" else "All Years"}',
                                                           selected_sector)

    graph,graphcomp, mean, rmse = predict.predict(db, user)

    return render_template('dashboard.html', bar=bar_html, chloropeth=chloropeth_html,
                           selected_year=selected_year, unique_years=unique_years, unique_sectors=unique_sectors,
                           bar2=bar_html2, chloropeth2=chloropeth_html2,
                           graph=graph,graphcomp=graphcomp, mean=mean, rmse=rmse)

@app.route('/login',methods=['GET', 'POST'])
def login():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        user = db.Company.find_one({'Login': username})
        
        if user and password==user['pwd']:
            session['user']=username
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Invalid credentials.', 'login_error')
    return render_template('Login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


def create_bar_and_map_plots(df, title_suffix, selected_sector=None):
    if selected_sector is None:
        selected_sector = user
    df['Month'] = df['entry_time'].dt.strftime('%B')
    df['Month'] = pd.Categorical(df['Month'], categories=month_order, ordered=True)

    grouped_df = df.groupby(['Month', 'type']).size().reset_index(name='Count')

    fig_bar = px.bar(grouped_df, x='Month', y='Count', color='type',
                     title=f'Number of Injections per Month and Type ({selected_sector},{title_suffix})',
                     labels={'Count': 'Number of Injections', 'Month': 'Month', 'type': 'Type'},
                     barmode='group',
                     opacity=0.8
                     )

    bar_html = fig_bar.to_html(full_html=False)

    df['count'] = df.groupby(['latitude', 'longitude']).latitude.transform('count')

    fig_map = px.density_mapbox(
        df,
        lat='latitude',
        lon='longitude',
        radius=10,
        center={'lat': df['latitude'].mean(), 'lon': df['longitude'].mean()},
        zoom=5,
        hover_name='city',
        color_continuous_scale="Viridis",
        color_continuous_midpoint=df['count'].mean(),
        mapbox_style='carto-positron',
        title=f'Injections around the world ({selected_sector},{title_suffix})'
    )
    map_html = fig_map.to_html(full_html=False)

    return bar_html, map_html


if __name__ == '__main__':
    app.run(debug=True)