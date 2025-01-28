# CROWD
CROWD: CROp Weather Data Dashboard

# INTRODUCTION
The dashboard is designed to provide insights into crop production data across different districts. The application is developed using Dash, a Python framework for building analytical web applications. This manual provides an overview of the dashboard's functionality, data handling, and the specific MySQL table structure used. The goal is to guide users and developers in effectively utilizing and maintaining the dashboard.

# PREREQUISITES
To use and modify this dashboard, ensure the following prerequisites are met:
1. Python 3.8 or above installed.
2. Dash framework installed (version 2.0.0 or above).
3. Dash Bootstrap Components (version 1.6.0).
4. A web browser (Google Chrome, Firefox, etc.).

# DATABASE SCHEMA OVERVIEW
The table structure used for the application is illustrated in the following screenshot:

![Picture1](https://github.com/user-attachments/assets/96cfc091-0289-482b-be16-cace2999b86b)
 
The columns in the table are as follows:
•	State: The name of the state.
•	District: The name of the district.
•	Today (T): Represents today's rainfall categories.
•	Till Date: Cumulative rainfall categories till the current date.
•	T+1 Day to T+5 Day: Forecasted rainfall categories for the next five days.
•	CROP: The name of crop associated with the data.
•	ID: A unique identifier for each record.
•	Weekly: Weekly rainfall categories
•	date_today: The current date in the record.

# INSTRUCTIONS FOR USE
Step 1: Once python is installed, download all the files mentioned here in this link: https://tinyurl.com/CROWD-Monitor
Step 2: Update SQL database as instructed above and update script with your database and table details. 
Step 3: Launch the dashboard application by running the script.
Step 4: Use the navigation bar to access different sections of the dashboard.
Step 5: Click on the values in the matrix table to navigate to the detailed view page showing district-specific data.

# APPLICATION STRUCTURE
The dashboard is structured into the following main components:
1. Layout: The overall structure of the dashboard, including headers, footers, and main content areas.
2. Callbacks: The interactive elements that connect the layout components to the data and allow for dynamic updates.
3. Data Handling: Backend processes that manage and manipulate data before displaying it on the dashboard.
CUSTOMIZATION AND CONFIGURATION
To customize the dashboard, you can modify the layout components and callbacks. To change the data source, update the SQL queries in the data handling section of the code.

# -Shriya Kaushal
