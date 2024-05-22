import pandas as pd
from datetime import datetime

def import_dataset():
    # Define the data types for each column in the CSV file
    dtype_dict = {
        'action': 'object',
        'anonymous': 'float64',
        'component': 'object',
        'contextid': 'float64',
        'contextinstanceid': 'object',
        'contextlevel': 'float64',
        'courseid': 'int64',
        'coursename': 'object',
        'crud': 'object',
        'edulevel': 'float64',
        'eventname': 'object',
        'finishtime': 'object',
        'grade': 'float64',
        'grade_to_pass': 'float64',
        'lectureDate': 'object',
        'membersInCourse': 'float64',
        'nuggetName': 'object',
        'number_of_attempts': 'float64',
        'objectid': 'int64',
        'objecttable': 'object',
        'others': 'object',
        'quizid': 'object',
        'recourceFiletype': 'object',
        'relateduserid': 'object',
        'scromCurrentGrade': 'float64',
        'scromHighestGrade': 'object',
        'scromId': 'object',
        'scromNeeded': 'object',
        'sectionnumber': 'float64',
        'starttime': 'object',
        'target': 'object',
        'user_id': 'int64',
        'month': 'object',
        'week': 'UInt32',
        'year-week': 'object',
        'year': 'int32',
        'day': 'object',
        'semester': 'object',
        'id': 'float64',
        'course': 'float64',
        'module': 'float64',
        'instance': 'float64',
        'is_ln': 'object',
        'example': 'float64',
        'motivation': 'float64',
        'explanation': 'float64',
        'assignment': 'float64',
        'experiment': 'float64',
        'description': 'object',
        'contenttype': 'object',
        'difficulty': 'object',
        'activitytopic': 'object',
        'expectedtime': 'object',
        'language': 'object',
        'prerequisites': 'object',
        'keywords': 'object',
        'resp_id': 'float64',
        'content_name': 'object',
        'name': 'object',
        'course_section': 'object'
    }
    
    # Read the CSV file into a DataFrame with specified data types and parsed date columns
    df = pd.read_csv('dataset.csv', dtype=dtype_dict)
    
    df['timecreated'] = pd.to_datetime(df['timecreated'])
    df['month'] = df['timecreated'].dt.strftime("%Y-%m")
    df['week'] = df['timecreated'].dt.isocalendar().week
    df['year-week'] = df['timecreated'].dt.strftime("%G-%V")
    df['year'] = df['timecreated'].dt.year
    df['day'] = df['timecreated'].dt.date

    print("Dataset Loaded successfully", datetime.now())

    return df
