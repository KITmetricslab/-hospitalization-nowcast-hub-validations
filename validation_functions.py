import os
import pandas as pd
import numpy as np

LOCATION_CODES = ['DE', 'DE-BW', 'DE-BY', 'DE-HB', 'DE-HH', 'DE-HE', 'DE-NI',
                  'DE-NW', 'DE-RP', 'DE-SL', 'DE-SH', 'DE-BB', 'DE-MV', 'DE-SN',
                  'DE-ST', 'DE-TH', 'DE-BE']

VALID_QUANTILES = [0.025, 0.1, 0.25, 0.5, 0.75, 0.9, 0.975]
VALID_TYPES = ['mean', 'quantile']
VALID_AGE_GROUPS = ['00+', '00-04', '05-14', '15-34', '35-59', '60-79', '80+']
VALID_TARGETS = [f'{_} wk ahead inc hosp' for _ in range(-2, 2)]
VALID_PATHOGENS = ['COVID-19']

def filename_match_forecast_date(filepath):
    df = pd.read_csv(filepath)

    if df.forecast_date.nunique() > 1:
        return True, f"FORECAST DATE ERROR: {filepath} has multiple forecast dates: {df.forecast_date.unique()}." \
            f"Forecast date must be unique." 
    else:
        file_forecast_date = pd.to_datetime(os.path.basename(filepath)[:10]).date()
        column_forecast_date = pd.to_datetime(df.forecast_date.iloc[0]).date()
        today = pd.Timestamp('today', tz='Europe/Berlin').date()
        
        if file_forecast_date != column_forecast_date:
            return True, f"FORECAST DATE ERROR: date of filename {filepath} does not match " \
                f"forecast_date column {column_forecast_date}." 
        
        if abs(file_forecast_date - today).days > 1:
            warning = f"Warning: The forecast is not made today. Date of the forecast - {file_forecast_date}, today - {today}."
            print(f"::warning file={os.path.basename(filepath)}::{warning}")
            return True, warning
        else:
            return False, "no errors"

def check_header(filepath):
    df = pd.read_csv(filepath)
    missing_cols = [c for c in VALID_COLUMNS if c not in df.columns]
    additional_cols = [c for c in df.columns if c not in VALID_COLUMNS]
    
    errors=[]
    
    if len(missing_cols) > 0:
        errors.append(f'The following columns are missing: {missing_cols}. Please add them.')
    
    if len(additional_cols) > 0:
        errors.append(f'The following columns are not accepted: {additional_cols}. Please remove them.')
        
    if len(errors) > 0:
        return errors
        
def check_column_values(filepath):
    df = pd.read_csv(filepath)
    
    invalid_values = dict()
    invalid_values['location'] = [_ for _ in df.location.unique() if _ not in LOCATION_CODES]
    invalid_values['quantile'] = [_ for _ in df['quantile'].dropna().unique() if _ not in VALID_QUANTILES]
    invalid_values['type'] = [_ for _ in df.type.unique() if _ not in VALID_TYPES]
    invalid_values['age_group'] = [_ for _ in df.age_group.unique() if _ not in VALID_AGE_GROUPS]
    invalid_values['target'] = [_ for _ in df.target.unique() if _ not in VALID_TARGETS]
    invalid_values['pathogen'] = [_ for _ in df.pathogen.unique() if _ not in VALID_PATHOGENS]
    
    errors = []
    for key, value in invalid_values.items():
        if len(value) > 0:
            errors.append(f'Invalid entries in column \'{key}\': {value}')
    
    if len(errors) > 0:
        return errors
    
def check_target_dates(df):
    df['invalid_target_date'] = df.apply(lambda x: x.target_end_date != x.forecast_date + 
                                   pd.Timedelta(weeks = int(x.target.split(' ')[0]), days = -1), axis = 1)
    
    invalid_target_dates = df.loc[df.invalid_target_date, ['forecast_date', 'target_end_date', 'target']].drop_duplicates()
    if len(invalid_target_dates) > 0:
        error = 'The following target_end_dates are wrong:\n\n' + invalid_target_dates.to_string(index = False)
        return [error]
    
def check_values(df):
    errors = []
    if df.value.isnull().sum():
        errors.append(f'Missing values in column \'value\' are not allowed. {df.value.isnull().sum()} values are missing.')
    
    if not all(df.value.astype(str).str.isnumeric()):
        non_numeric_values = df.value[~df.value.astype(str).str.isnumeric()].dropna().to_list()
        errors.append(f'Non-numeric entries in column \'value\' are not allowed: {non_numeric_values}.')
    
    if len(errors) > 0:
        return errors

def check_quantiles(df):
    df.loc[df.type != 'mean', 'no_quantiles'] = df[df.type != 'mean'].groupby(['location', 'age_group', 'target', 
                                                                           'target_end_date'])['quantile'].transform('nunique')
    
    # note that we've already checked that no invalid quantiles are present
    incomplete_quantiles = df[(df.no_quantiles != 7) & df.no_quantiles.notnull()]
    
    if len(incomplete_quantiles) > 0:
        error = 'Not all quantiles were provided in the following setting(s):\n\n' + \
            incomplete_quantiles.groupby(['location', 'age_group', 'target', 'target_end_date']
                                        )['quantile'].unique().to_string()
        return [error]
    
def check_forecast(df):
    errors = []

    for check in [check_values, check_target_dates, check_quantiles]:
        result = check(df)
        if result:
            errors.extend(result)

    if len(errors) == 0:
        print('No errors.')

    else:
        for e in errors:
            print(e)
            print('__________')