# AI-Based Data Analysis using Django

## 📋 Project Overview

This is a beginner-friendly Django web application that allows users to:
1. Upload CSV files
2. Analyze data using pandas (statistics)
3. Visualize data with charts (matplotlib/seaborn)
4. Apply Machine Learning (Linear Regression) for predictions

---

## 🗂️ Project Structure

```
ai_data_project/
├── manage.py                 # Django management script
├── requirements.txt         # Python dependencies
├── sample_data.csv          # Sample data for testing
├── ai_data_project/         # Django project settings
│   ├── __init__.py
│   ├── settings.py          # Project configuration
│   ├── urls.py              # Main URL routing
│   └── wsgi.py              # WSGI application
├── dataapp/                 # Django application
│   ├── __init__.py
│   ├── admin.py             # Admin configuration
│   ├── models.py            # Database models
│   ├── urls.py              # App URL routing
│   └── views.py             # Main logic (CSV, analysis, ML)
└── templates/
    └── dataapp/             # HTML templates
        ├── base.html        # Base template
        ├── home.html       # Upload page
        ├── upload_success.html
        ├── statistics.html # Statistics page
        ├── visualize.html  # Charts page
        └── predict.html    # ML prediction page
```

---

## 🚀 How to Run the Project

### Step 1: Install Dependencies
```bash
pip install django pandas matplotlib seaborn scikit-learn
```

### Step 2: Navigate to Project
```bash
cd ai_data_project
```

### Step 3: Run Migrations
```bash
python manage.py migrate
```

### Step 4: Start Server
```bash
python manage.py runserver
```

### Step 5: Open Browser
Go to: http://127.0.0.1:8000/

---

## 📖 File Explanations

### 1. `settings.py`
- **Purpose**: Main Django configuration file
- **What it does**: 
  - Defines installed apps
  - Database configuration (SQLite)
  - Template settings
  - Static and media file paths
- **Viva Explanation**: "This is the main configuration file that tells Django about our project settings, installed apps, and database configuration."

### 2. `urls.py` (Main)
- **Purpose**: URL routing for the entire project
- **What it does**: Maps URLs to their corresponding views
- **Viva Explanation**: "This file handles URL routing. It directs the browser request to the appropriate view function."

### 3. `views.py`
- **Purpose**: Contains all the main business logic
- **Functions**:
  - `home()`: Displays upload form
  - `upload_file()`: Handles CSV file upload using pandas
  - `analyze_data()`: Calculates statistics (mean, median, min, max)
  - `visualize_data()`: Creates charts using matplotlib
  - `predict()`: Applies Linear Regression using scikit-learn
- **Viva Explanation**: "This is the core of our application. It contains all the functions that process user requests, analyze data, create visualizations, and apply machine learning."

### 4. `models.py`
- **Purpose**: Defines database structure
- **What it does**: Contains the UploadedFile model to track uploaded files
- **Viva Explanation**: "We use Django's ORM to define database models. The UploadedFile model stores information about uploaded CSV files."

### 5. `urls.py` (App)
- **Purpose**: URL patterns for the dataapp
- **Viva Explanation**: "This file defines the specific URLs for our data analysis features."

### 6. Templates (HTML files)
- **Purpose**: Define the user interface
- **Viva Explanation**: "Templates define what the user sees in the browser. We use Django template language to display dynamic data."

---

## 🔬 Key Technologies Used

| Technology | Purpose |
|------------|---------|
| Django | Web framework |
| Pandas | Data analysis |
| Matplotlib/Seaborn | Data visualization |
| Scikit-learn | Machine Learning (Linear Regression) |

---

## 🎯 Features Explained

### 1. CSV Upload
- User selects a CSV file
- Django reads the file
- Pandas converts it to DataFrame
- Data is stored in session

### 2. Statistics Analysis
- Uses `df.describe()` for basic stats
- Calculates mean, median, min, max for each column
- Displays in table format

### 3. Visualization
- **Bar Chart**: Shows distribution
- **Line Chart**: Shows trends
- **Scatter Plot**: Shows relationship between variables
- **Histogram**: Shows frequency distribution

### 4. Machine Learning
- **Algorithm**: Linear Regression
- **Process**:
  1. Select feature (X) and target (Y) columns
  2. Split data into training and testing sets
  3. Train the model
  4. Make predictions
  5. Calculate metrics (R², RMSE)

---

## 🎓 Viva Questions & Answers

### Q1: What is the purpose of this project?
**Answer**: This project allows users to upload CSV files and analyze them using AI/ML techniques. It provides statistics, visualizations, and prediction capabilities.

### Q2: What is Django and why did you use it?
**Answer**: Django is a Python web framework that helps build web applications quickly. It provides built-in features for URL routing, template rendering, and database management. We chose it because it's beginner-friendly and has good documentation.

### Q3: How does pandas help in data analysis?
**Answer**: Pandas is a Python library for data manipulation and analysis. It provides DataFrame structure which makes it easy to:
- Read CSV files
- Calculate statistics (mean, median, etc.)
- Filter and transform data

### Q4: What is Linear Regression?
**Answer**: Linear Regression is a machine learning algorithm that finds the best straight line relationship between input (X) and output (Y). The equation is: `y = mx + c` where:
- m = slope (coefficient)
- c = intercept

### Q5: What do R² and RMSE mean?
**Answer**:
- **R² (R-squared)**: Measures how well the model fits the data. Values range from 0 to 1, where 1 is perfect.
- **RMSE (Root Mean Square Error)**: Measures prediction error. Lower values mean better predictions.

### Q6: How do you handle the CSV file in Django?
**Answer**: 
1. User uploads file through HTML form
2. Django's `request.FILES` captures the file
3. Pandas reads the CSV using `pd.read_csv()`
4. Data is converted to JSON and stored in session

### Q7: What is the flow of your application?
**Answer**: 
1. User visits home page
2. Uploads CSV file
3. System reads and displays data preview
4. User can view statistics, charts, or ML predictions
5. Clear button resets the session

### Q8: Why did you use session to store data?
**Answer**: For a simple mini project, using sessions is easier than setting up a full database. It allows us to temporarily store the uploaded data during the user's session.

### Q9: What charts have you implemented?
**Answer**: We implemented:
- Bar Chart: For comparing values
- Line Chart: For showing trends
- Scatter Plot: For showing relationship between two variables
- Histogram: For showing frequency distribution

### Q10: What is the difference between GET and POST methods?
**Answer**:
- **GET**: Used to request data from a specified resource
- **POST**: Used to send data to create or update a resource
We use POST for file upload (for security) and GET for viewing pages.

---

## 🔧 Future Improvements

Here are some improvements you can mention in your viva:

1. **More ML Models**: Add Decision Tree, Random Forest, K-Means clustering
2. **Export Features**: Allow exporting analysis as PDF or Excel
3. **User Authentication**: Add login/logout for multiple users
4. **Multiple File Formats**: Support Excel (.xlsx), JSON files
5. **Interactive Charts**: Use Plotly for interactive charts
6. **Data Cleaning**: Add features to handle missing values, outliers
7. **Database Storage**: Store uploaded files in database instead of session
8. **API Development**: Create REST API for mobile app integration

---

## 📝 Sample Data for Testing

A sample CSV file (`sample_data.csv`) is included with columns:
- Name, Age, Salary, Experience

You can use this to test all features:
- Statistics: Analyze Age, Salary, Experience
- Charts: Visualize Salary vs Experience
- ML: Predict Salary based on Experience

---

## ✅ Quick Test Checklist

- [ ] Install all dependencies
- [ ] Run `python manage.py migrate`
- [ ] Start server with `python manage.py runserver`
- [ ] Open http://127.0.0.1:8000/
- [ ] Upload sample_data.csv
- [ ] Check Statistics page
- [ ] Check Charts page
- [ ] Try ML Prediction (Experience → Salary)

---

## 📚 References

- Django Documentation: https://docs.djangoproject.com/
- Pandas Documentation: https://pandas.pydata.org/
- Scikit-learn Documentation: https://scikit-learn.org/
- Matplotlib Documentation: https://matplotlib.org/

---

**Project Created for PBL (Project Based Learning)**
**2nd Year Computer Science Engineering**