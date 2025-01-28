import pandas as pd 
import dash 
from dash import dcc, html 
from dash.dependencies import Input, Output 
import dash_bootstrap_components as dbc
import plotly.graph_objs as go  
import mysql.connector  

# Function to connect to the MySQL database and fetch data
def fetch_data(query):
    try:
        connection = mysql.connector.connect(
            host='localhost',  # Replace with your MySQL host
            user='root',  # Replace with your MySQL username
            password='your_new_password',  # Replace with your MySQL password 
            database='newschema1'  # Replace with your database name
        )
        df = pd.read_sql(query, connection)
        connection.close()
        return df
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return pd.DataFrame()

# Load data from MySQL database
combined_df = fetch_data("SELECT * FROM file_using")   #replace file_using with ur actual table name
todaysdate = combined_df.loc[0, 'date_today']  

# Function to group data by crop and date range
def group_data(combined_df):
    grouped_data = {}
    crops = combined_df['CROP'].unique()
    for crop in crops:
        crop_df = combined_df[combined_df['CROP'] == crop]
        # Group by 'State' and 'Today (T)' columns and count districts.
        crop_grouped_day = crop_df.groupby(['State', 'Today (T)'])['District'].count().reset_index()
        # Group by 'State' and 'Till Date' columns and count districts
        crop_grouped_month = crop_df.groupby(['State', 'Till Date'])['District'].count().reset_index() 
        crop_grouped_week = crop_df.groupby(['State', 'Weekly'])['District'].count().reset_index() 
        grouped_data[crop] = {
            'day': crop_grouped_day,
            'month': crop_grouped_month,
            'Weekly':crop_grouped_week
        }
    return grouped_data

# Function to generate matrix-like format for a crop and date range
def generate_matrix(grouped_data, crop, date_range):
    desired_order = ['LD', 'D', 'N', 'E', 'LE', 'NR', 'NO DATA']

    if crop in grouped_data:
        if date_range == 'Today (T)':
            matrix_data = grouped_data[crop]['day'].pivot(index='State', columns='Today (T)', values='District').fillna(0)
        elif date_range == 'Till Date':
            matrix_data = grouped_data[crop]['month'].pivot(index='State', columns='Till Date', values='District').fillna(0)
        else:
            matrix_data = grouped_data[crop]['Weekly'].pivot(index='State', columns='Weekly', values='District').fillna(0)
        
        
        # Reorder columns
        matrix_data = matrix_data.reindex(columns=desired_order, fill_value=0)
        matrix_with_totals = add_totals(matrix_data)
        return matrix_with_totals
    else:
        return pd.DataFrame()

# Function to add a total row and column to the matrix
def add_totals(matrix_data):
    try:
        # Calculate totals for each row
        matrix_data['Total'] = matrix_data.sum(axis=1)
        
        # Calculate totals for each column
        column_totals = matrix_data.sum(axis=0)
        
        # Convert column totals series to a DataFrame with 'Total' as index
        column_total_row = pd.DataFrame(column_totals).transpose()
        column_total_row.index = ['Total']
        
        # Concatenate the column total row to the matrix data
        matrix_with_totals = pd.concat([matrix_data, column_total_row])
        
        # Ensure 'Total' column is at the end
        matrix_with_totals = matrix_with_totals[[col for col in matrix_with_totals.columns if col != 'Total'] + ['Total']]
        
        return matrix_with_totals
    except Exception as e:
        print(f"Error in add_totals function: {e}")
        return pd.DataFrame()

def categorize_and_generate_new_matrix(df, date_column):
    # Define categories
    categories = {
        'NR': (0, 0),
        'VL': (0, 2.4),
        'L': (2.5, 15.5),
        'M': (15.6, 64.4),
        'H': (64.4, 115.5),
        'VH': (115.6, 204.4),
        'ExH': (204.5, float('inf'))
    }
    
    # Function to categorize values
    def categorize(value):
        for category, (low, high) in categories.items():
            if low <= value <= high:
                return category
        return 'NO DATA'
    
    desired_order_new = ['VL', 'L', 'M', 'H', 'VH', 'ExH', 'NR']

    # Use .copy() to avoid SettingWithCopyWarning
    df = df.copy()
    
    # Apply categorization to the selected date column
    df[f'{date_column} Category'] = df[date_column].apply(categorize)
    
    # Create new matrix table
    matrix_data = df.groupby(['State', f'{date_column} Category'])['District'].count().unstack(fill_value=0)
   
    matrix_data = matrix_data.reindex(columns=desired_order_new, fill_value=0)
    matrix_with_totals = add_totals(matrix_data)  # Ensure totals are added correctly
    return matrix_with_totals

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=['https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css'])
# Suppress callback exceptions
app.config.suppress_callback_exceptions=True
category_description1 = html.Div([
    html.H4("Category Descriptions:", style={'color': '#228B22', 'font-size': '18px'}),
    html.Ul([
        html.Li(html.B("REALISED DATA:")),
        html.Li("LD: Largely Deficient Rainfall (-99% to -60%)"),
        html.Li("D: Deficient Rainfall (-59% to -20%)"),
        html.Li("N: Normal Rainfall (-19% to 19%)"),
        html.Li("E: Excessive Rainfall (20% to 59%)"),
        html.Li("LE: Largely Excessive Rainfall (60% or more)"),
        html.Li("NO DATA: No Data Available"),
    ], style={'font-size': '14px'})
], style={'width': '48%', 'display': 'inline-block'})

category_description2 = html.Div([
    html.Ul([
        html.Li(html.B("FORECAST DATA:")),
        html.Li("NR: No Rainfall"),
        html.Li("VL: Very Light Rainfall (0 - 2.4 mm)"),
        html.Li("L: Light Rainfall (2.5 - 15.5 mm)"),
        html.Li("M: Moderate Rainfall (15.6 - 64.4 mm)"),
        html.Li("H: High Rainfall (64.4 - 115.5 mm)"),
        html.Li("VH: Very High Rainfall (115.6 - 204.4 mm)"),
        html.Li("ExH: Extremely High Rainfall (204.5 mm and above)"),
    ], style={'font-size': '14px'})
], style={'width': '48%', 'display': 'inline-block'})

# Added these to a parent Div to display them side by side
category_descriptions = html.Div([
    category_description1,
    category_description2
], style={'display': 'flex', 'justify-content': 'space-between'})

# Add to layout as usual
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    dbc.NavbarSimple(
        brand=[
            html.Div([
                html.Img(src="assets/imd logo-removebg-preview.jpg", height="50px", style={'margin-right': '10px'}),
                f"Crowd Monitor ({todaysdate})"
            ], style={'display': 'flex', 'alignItems': 'center'})
        ],
        color="success",
        dark=True,
        brand_style={'margin': '0', 'padding': '0', 'width': '100%', 'display': 'flex', 'alignItems': 'center'},
        children=[
            dbc.Row(
                [
                    dbc.Col(dbc.NavItem(dbc.NavLink("Home", href="/", style={'fontSize': '18px','margin': '0', 'width': '100%', 'padding': '0'})), width="auto"),
                    dbc.Col(dbc.NavItem(dbc.NavLink("Dashboard", href="/dashboard", style={'fontSize': '18px','margin': '0', 'width': '100%', 'padding': '0'})), width="auto"),
                ],
                className='col-12 col-md-2'
            )
        ]
    ),
    dbc.Container(id='page-content', className='col-12 mt-4', style={'margin': '0', 'width': '100%', 'padding': '0'})
], fluid=True)


landing_page = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Img(src='/assets/imd logo.jpeg', className='center', style={'width': '140px', 'display': 'block', 'margin-left': 'auto', 'margin-right': 'auto', 'margin-top': '5px'}),
            html.H1("Welcome to CROWD: CROp Weather Data Monitor", className='text-center', style={'color': '#228B22', 'font-size': '48px', 'margin-top': '15px'}),
            html.P("By India Meteorological Department (IMD)", className='text-center', style={'color': '#555555', 'font-size': '18px', 'margin-top': '10px', 'font-weight': 'bold'}),
            html.P("It provides you with the latest rainfall information for various districts under each state. Here, you can find both present and next 5 days forecasted data to help you make informed decisions.", className='text-center', style={'color': '#555555', 'font-size': '20px', 'margin-top': '15px'}),
            # Directly include the dashboard details here
            html.Div([
                html.H3("Dashboard Overview", style={'color': '#228B22'}),
                html.P("The dashboard displays:"),
                html.Ul([
                    html.Li([html.B("Realised Data:"), " The values display the number of districts in each state categorized based on the weather for daily, cumulative, and weekly periods."]),
                    html.Li([html.B("Forecast Data:"), " The values display upcoming 5 days' weather forecast"]),
                    html.Li([html.B("Summary Table:"), " A comprehensive table showing the data at a glance."]),
                    html.Li([html.B("Pie Chart:"), " A visual representation of weather among and within the states."]),
                ], style={'font-size': '18px'}),
            ], style={'margin-top': '40px', 'textAlign': 'left', 'color': '#555555', 'font-size': '18px'}),
            dbc.Button("Go to Dashboard", href="/dashboard", color="success", className="d-block mx-auto", style={'margin-top': '30px'}),
        ])
    ])
], fluid=True)

dashboard_page = dbc.Container([
    dcc.Tabs(id="tabs", value='tab-1', children=[
        dcc.Tab(label='Select Crop', value='tab-1', disabled=True),
    ], className='nav nav-tabs'),
    html.Div(style={'backgroundColor': '#E6FFE6', 'padding': '0', 'margin': '0'}, children=[
        html.Div(className='row', style={'margin': '0', 'width': '100%'}, children=[
            html.Div(className='col-12 col-md-6', style={'padding': '20px', 'margin': '0', 'width': '100%'}, children=[
                html.Div(className='card p-3 mb-4', style={'width': '100%', 'backgroundColor': '#F0FFF0', 'box-shadow': '0px 0px 15px 0px rgba(0,0,0,0.1)', 'borderLeft': '5px solid #7CFC00', 'borderRight': '5px solid #7CFC00'}, children=[
                    html.H3("Realised Data: Summary Table", className='card-title text-center', style={'color': '#228B22', 'font-size': '24px', 'margin-bottom': '20px'}),
                    dcc.RadioItems(
                        id='date-range',
                        options=[
                            {'label': 'Daily', 'value': 'Today (T)'},
                            {'label': 'Cumulative', 'value': 'Till Date'},
                            {'label': 'Weekly', 'value': 'Weekly'}
                        ],
                        value='Today (T)',
                        labelStyle={'display': 'inline-block'},
                        className='my-3',
                        style={'width': '100%'}
                    ),
                    html.Div(id='tabs-content'),  # Placeholder for the matrix table
                    html.H3("Realised Data: Pie Chart", className='card-title text-center', style={'color': '#228B22', 'font-size': '24px', 'margin-top': '10px'}),
                    dcc.Dropdown(id='state-dropdown', placeholder='Select a State', clearable=True, style={'backgroundColor': '#E6FFE6'}),
                    dcc.Checklist(
                        id='category-checklist',
                        options=[],
                        value=[],
                        labelStyle={'display': 'inline-block'},
                        className='mb-3'
                    ),
                    dcc.RadioItems(
                        id='view-type',
                        options=[
                            {'label': 'View by State', 'value': 'state'},
                            {'label': 'View as Whole', 'value': 'whole'}
                        ],
                        value='whole',
                        labelStyle={'display': 'inline-block'},
                        className='my-3'
                    ),
                    html.Div(id='state-message', style={'color': '#FF0000', 'font-size': '16px', 'margin-top': '10px'}),
                    dcc.Graph(id='pie-chart', style={'height': '20%', 'width': '100%', 'backgroundColor': '#F0FFF0'})
                ])
            ]),
            html.Div(className='col-12 col-md-6', style={'padding': '20px', 'margin': '0', 'width': '100%'}, children=[
                html.Div(className='card p-3 mb-4', style={'backgroundColor': '#F0FFF0', 'box-shadow': '0px 0px 15px 0px rgba(0,0,0,0.1)', 'borderLeft': '5px solid #7CFC00', 'borderRight': '5px solid #7CFC00'}, children=[
                    html.H3("Forecast Data: Summary Table", className='card-title text-center', style={'color': '#228B22', 'font-size': '24px', 'margin-bottom': '20px'}),
                    dcc.Dropdown(
                        id='forecast-date-dropdown',
                        options=[
                            {'label': 'Day 1', 'value': 'T+1 Day'},
                            {'label': 'Day 2', 'value': 'T+2 Day'},
                            {'label': 'Day 3', 'value': 'T+3 Day'},
                            {'label': 'Day 4', 'value': 'T+4 Day'},
                            {'label': 'Day 5', 'value': 'T+5 Day'}
                        ],
                        value='T+1 Day',
                        className='mb-3',
                        style={'backgroundColor': '#E6FFE6'}
                    ),
                    html.Div(id='new-matrix-content', style={'backgroundColor': '#F0FFF0'}),  # Placeholder for the new matrix
                    html.H3("Forecast Data: Pie Chart", className='card-title text-center', style={'color': '#228B22', 'font-size': '24px', 'margin-top': '10px'}),
                    dcc.Graph(id='new-pie-chart', style={'height': '20%', 'width': '100%', 'backgroundColor': '#E6FFE6'})
                ]),
                html.Div(className='mb-4', children=[
                    category_descriptions,
                ])
            ])
        ])
    ]),
], fluid=True, className='p-0 m-0')

# Define new layout for displaying district names
districts_page = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H3("District Names", style={'color': '#228B22', 'font-size': '24px', 'text-align': 'left'}),
            html.Div(id='district-names-content', style={'text-align': 'left'})
        ])
    ])
], fluid=True)

# Update page layout based on URL
@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/dashboard':
        return dashboard_page
    elif pathname.startswith('/districts/'):
        return districts_page
    else:
        return landing_page

# Callback to update district names content
@app.callback(Output('district-names-content', 'children'),
              [Input('url', 'pathname')])
def display_district_names(pathname):
    try:
        parts = pathname.split('/')
        if len(parts) == 6:
            crop, date_range, state, category = parts[2], parts[3], parts[4], parts[5]

            # Replace any URL encoded characters like %20 with space
            date_range = date_range.replace('%20', ' ')
            state = state.replace('%20', ' ')
            category = category.replace('%20', ' ')

            crop_df = combined_df[(combined_df['CROP'] == crop) & 
                                  (combined_df['State'] == state) & 
                                  (combined_df[date_range] == category)]
            district_names = crop_df['District'].unique()
            if district_names.size > 0:
                return html.Ul([html.Li(district, style={'font-size': '18px', 'margin': '5px','text-allign': 'left'}) for district in district_names])
            else:
                return html.Div("No districts found for the selected criteria.", style={'color': '#FF0000', 'font-size': '16px'})
        else:
            return html.Div("Invalid URL format.", style={'color': '#FF0000', 'font-size': '16px'})
    except Exception as e:
        # Provide detailed error message
        error_message = f"Error in display_district_names callback: {str(e)}"
        return html.Div(error_message, style={'color': '#FF0000', 'font-size': '16px'})


@app.callback(
    Output('state-message', 'children'),
    Input('view-type', 'value'),
    Input('state-dropdown', 'value')
)
def update_message(view_type, state):
    if view_type == 'state' and state is None:
        return "Please select a state to view by state."
    elif view_type == 'whole' and state is not None:
        return "Please select 'View by state' to view for specific state."
    return ""

# Define callback to update the crop selection based on available crops
@app.callback(Output('tabs', 'children'),
              [Input('tabs', 'value')])
def update_tabs(tab):
    # Fetch unique crops from combined_df
    crops = combined_df['CROP'].unique()
    tab_options = [
        dcc.Tab(label=crop, value=crop, className='nav-link',style={'backgroundColor':'#E6FFE6'}) for crop in crops
    ]
    return tab_options

# Define callback to update the state dropdown options based on selected crop and date range
@app.callback(
    Output('state-dropdown', 'options'),
    [Input('tabs', 'value'),
     Input('date-range', 'value')]
)
def update_state_dropdown(crop, date_range):
    if crop and date_range:
        crop_df = combined_df[combined_df['CROP'] == crop]
        states = crop_df['State'].unique()
        style = {
            'backgroundColor': '#E6FFE6'
            }
        return [{'label': state, 'value': state} for state in states]
    else:
        return []

# Define callback to update the matrix-like table and pie chart based on selected crop and date range
@app.callback([Output('tabs-content', 'children'),
               Output('pie-chart', 'figure')],
              [Input('tabs', 'value'),
               Input('date-range', 'value'),
               Input('state-dropdown', 'value'),
               Input('category-checklist', 'value'),
               Input('view-type', 'value')])
def render_content_and_pie_chart(tab, date_range, state, categories, view_type):
    try:
        if tab and date_range:
            grouped_data = group_data(combined_df)
            matrix_data = generate_matrix(grouped_data, tab, date_range)
            
            if not matrix_data.empty:
                # Generate matrix table
                rows = []
                rows.append(html.Tr([html.Th("State")] + [html.Th(col, style={'font-size': '14px', 'padding': '5px'}) for col in matrix_data.columns]))
                
                for state_name, row in matrix_data.iterrows():
                    row_cells = [html.Td(state_name, style={'font-size': '14px', 'padding': '14px','font-weight': 'bold', 'text-align': 'centre'})]
                    for col, value in row.items():
                        if col == 'Total' or state_name == 'Total':
                            # Do not include hyperlink for 'Total' column
                            cell = html.Td(value, style={'font-size': '14px', 'padding': '2px', 'text-align': 'centre'})
                        else:
                            link = f'/districts/{tab}/{date_range}/{state_name}/{col}'
                            cell = html.Td(html.A(value, href=link, style={'font-size': '12px', 'padding': '5px', 'text-align': 'centre'}))
                        row_cells.append(cell)
                    rows.append(html.Tr(row_cells))
                
                matrix_table = html.Table(rows, className='table table-bordered', style={'backgroundColor':'#E6FFE6', 'text-align': 'centre'})
            else:
                matrix_table = html.Div(
                    "Please select the crop from above tabs to view the data.",
                    style={'color': '#FF0000', 'font-size': '16px', 'text-align': 'left'}
                )
            
            # Generate pie chart
            crop_df = combined_df[combined_df['CROP'] == tab]
            if view_type == 'state' and state:
                state_df = crop_df[crop_df['State'] == state]
                if categories:
                    filtered_df = state_df[state_df[date_range].isin(categories)]
                else:
                    filtered_df = state_df
            else:
                if categories:
                    filtered_df = crop_df[crop_df[date_range].isin(categories)]
                else:
                    filtered_df = crop_df

            counts = filtered_df[date_range].value_counts()
            labels = counts.index
            values = counts.values
            
            pie_chart = go.Figure(data=[go.Pie(labels=labels, values=values)])
            pie_chart.update_layout(
                plot_bgcolor='#E6FFE6',  # Set background color of the plot area
                paper_bgcolor='#E6FFE6',  # Set background color of the entire graph area
            )
            
            return matrix_table, pie_chart
        else:
            return "Please select a crop and date range.", {}
    except Exception as e:
        return f"Error in render_content_and_pie_chart callback: {e}", {}

@app.callback([Output('new-matrix-content', 'children'),
               Output('new-pie-chart', 'figure')],
              [Input('tabs', 'value'),
               Input('forecast-date-dropdown', 'value')])
def update_new_matrix_and_pie_chart(crop, date_column):
    try:
        if crop and date_column:
            crop_df = combined_df[combined_df['CROP'] == crop]
            new_matrix_data = categorize_and_generate_new_matrix(crop_df, date_column)
            
            if not new_matrix_data.empty:
                # Generate the new matrix table
                rows = []
                rows.append(html.Tr([html.Th("State")] + [html.Th(col, style={'font-size': '14px', 'padding': '3px',}) for col in new_matrix_data.columns]))  # Adjust font size and padding here
                
                for state, row in new_matrix_data.iterrows():
                    row_cells = [html.Td(state, style={'font-size': '14px', 'padding': '5px','font-weight': 'bold'})] + [html.Td(value, style={'font-size': '14px', 'padding': '3px'}) for value in row]
                    rows.append(html.Tr(row_cells))
                
                matrix_table = html.Table(rows, className='table table-bordered', style={'backgroundColor': '#E6FFE6', 'text-align': 'left'})
                
                # Generate the new pie chart data
                new_pie_chart_data = new_matrix_data.sum().drop('Total')
                labels = new_pie_chart_data.index
                values = new_pie_chart_data.values
                new_pie_chart = go.Figure(data=[go.Pie(labels=labels, values=values)])
                new_pie_chart.update_layout(
                    plot_bgcolor='#E6FFE6',  # Set background color of the plot area
                    paper_bgcolor='#E6FFE6',  # Set background color of the entire graph area
                )

                
                return matrix_table, new_pie_chart
            else:
                return "No data available for the selected crop.", {}
        else:
            return "Please select a crop and date.", {}
    except Exception as e:
        return f"Error in update_new_matrix_and_pie_chart callback: {e}", {}

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)