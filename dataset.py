import pandas as pd
from datetime import datetime

def import_dataset():
    print("Data called")

    dtype_dict = {
        'action': 'object',
        'courseid': 'int64',
        'coursename': 'object',
        'finishtime': 'object',
        'grade': 'float64',
        'grade_to_pass': 'float64',
        'membersInCourse': 'float64',
        'nuggetName': 'object',
        'number_of_attempts': 'float64',
        'objectid': 'int64',
        'objecttable': 'object',
        'scromCurrentGrade': 'float64',
        'scromHighestGrade': 'object',
        'starttime': 'object',
        'user_id': 'int64',
        'month': 'object',
        'week': 'UInt32',
        'year-week': 'object',
        'year': 'int32',
        'day': 'object',
        'semester': 'object',
        'is_ln': 'object',
        'description': 'object',
        'contenttype': 'object',
        'difficulty': 'object',
        'activitytopic': 'object',
        'expectedtime': 'object',
        'language': 'object',
        'prerequisites': 'object',
        'keywords': 'object',
        'name': 'object',
        'course_section': 'object',
        'type': 'object'
    }
    
    # Read the dataset using pandas
    df = pd.read_csv('dataset.csv', dtype=dtype_dict)
    
    # Convert 'timecreated' to datetime
    df['timecreated'] = pd.to_datetime(df['timecreated'])
    
    # Create new time-based columns
    df['month'] = df['timecreated'].dt.strftime("%Y-%m")
    df['week'] = df['timecreated'].dt.isocalendar().week
    df['year-week'] = df['timecreated'].dt.strftime("%G-%V")
    df['year'] = df['timecreated'].dt.year
    df['day'] = df['timecreated'].dt.date

    print("Dataset Loaded successfully", datetime.now())
    

    return df
