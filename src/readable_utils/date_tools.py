

import os


import sys


from datetime import date, datetime, timedelta




from pytz import timezone


if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))




def get_datetime_format_string(format):
    """
    Returns a datetime format string based on a more readable format string.

    Args:
        format (str): The format option, which can be one of the following:
            - "%Y%m%d%H%M%S" or "number"
            - "%Y%m%d" or "YYYYMMDD"
            - "%H%M%S" or "HHMMSS" or "time_number"
            - "%Y-%m-%d %H:%M:%S" or "readable"
            - "%Y-%m-%d" or "YYYY-MM-DD"
            - "%H:%M" or "hour_mins"
            - "%A" or "Weekday"

    Returns:
        str: The corresponding datetime format string.
    """
    if format == "%Y%m%d%H%M%S" or format == "number":
        return "%Y%m%d%H%M%S"
    elif format == "%Y%m%d" or format == "YYYYMMDD":
        return "%Y%m%d"
    elif format == "%H%M%S" or format == "HHMMSS" or format == "time_number":
        return "%H%M%S"
    elif (
        format == "%Y-%m-%d %H:%M:%S"
        or format == "%Y-%m-%d %H:%M:%S %Z"
        or format == "readable"
    ):
        return "%Y-%m-%d %H:%M:%S %Z"
    elif format == "%Y-%m-%d" or format == "YYYY-MM-DD":
        return "%Y-%m-%d"
    elif format == "%H:%M" or format == "hour_mins":
        return "%H:%M"
    elif format == "%A" or format == "Weekday":
        return "%A"
    else:
        print("Invalid format string")
        return format


def get_current_datetime(format="%Y%m%d%H%M%S"):
    """
    Returns the current datetime in the specified format string, always in CST timezone.

    Args:
        format (str): The format option for the datetime string
            which can be one of the following:
            - "%Y%m%d%H%M%S" or "number"
            - "%Y%m%d" or "YYYYMMDD"
            - "%H%M%S" or "HHMMSS" or "time_number"
            - "%Y-%m-%d %H:%M:%S" or "readable"
            - "%Y-%m-%d" or "YYYY-MM-DD"
            - "%H:%M" or "hour_mins"
            - "%A" or "Weekday"

    Returns:
        str: The current datetime formatted according to the string passed in.
    """
    cst = timezone("America/Chicago")
    now_cst = datetime.now().astimezone(cst)

    return now_cst.strftime(get_datetime_format_string(format))


def parse_mixed_date(date_str):
    # List of allowed date formats
    formats = ["%m/%d/%Y", "%Y-%m-%d"]

    # Try each format
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%m/%d/%Y")
        except ValueError:
            pass

    # Handle Excel serial date format
    try:
        # Check if date_str is a number
        serial_date = int(date_str)
        # Excel serial date base (Windows default)
        base_date = datetime(1899, 12, 30)
        parsed_date = base_date + timedelta(days=serial_date)
        return parsed_date.strftime("%m/%d/%Y")
    except ValueError:
        pass

    # If all formats fail, print an error message
    print(f"Error: {date_str} does not match allowed formats.")
    return None


currentDT = get_current_datetime(get_datetime_format_string("number"))


current_date_time_readable = get_current_datetime(
    get_datetime_format_string("readable")
)


dict_days = {
    "Sunday": "7 - Sunday",
    "Monday": "1 - Monday",
    "Tuesday": "2 - Tuesday",
    "Wednesday": "3 - Wednesday",
    "Thursday": "4 - Thursday",
    "Friday": "5 - Friday",
    "Saturday": "6 - Saturday",
}


dict_day_sort_order = {
    "Sunday": 1,
    "Monday": 2,
    "Tuesday": 3,
    "Wednesday": 4,
    "Thursday": 5,
    "Friday": 6,
    "Saturday": 7,
}


dict_day_abbrev_to_day = {
    "Mon": "Monday",
    "Tue": "Tuesday",
    "Wed": "Wednesday",
    "Thu": "Thursday",
    "Fri": "Friday",
    "Sat": "Saturday",
    "Sun": "Sunday",
}


dict_month_numbers = {
    "TOTAL": "00",
    "January": "01",
    "February": "02",
    "March": "03",
    "April": "04",
    "May": "05",
    "June": "06",
    "July": "07",
    "August": "08",
    "September": "09",
    "October": "10",
    "November": "11",
    "December": "12",
}


def floatHourToTime(fh):
    """
    Converts a float hour value to a time tuple in the format of:
        (hours, minutes, seconds).

    Args:
        fh (float): The float hour to convert.

    Returns:
        tuple: A time represented as a tuple in the format (hours, minutes, seconds).
    """
    hours, hourSeconds = divmod(fh, 1)
    minutes, seconds = divmod(hourSeconds * 60, 1)
    return (
        int(hours),
        int(minutes),
        int(seconds * 60),
    )


def convert_week(convert_week):
    """
    Converts a week from the Sanders format ('2242') to the standard ISO format:
        ('2022-W42').

    Args:
        convert_week (str): The week to convert, in Sanders format
            (e.g., '2242' representing the 42nd week of 2022).

    Returns:
        str: The converted week in the standard ISO format (e.g., '2022-W42').
    """
    WeekString = "20" + convert_week[0:2] + "-W" + convert_week[2:4]
    return WeekString


def fix_weeks(df):
    """
    Fixes the weeks in a DataFrame, converting from the Sanders format:
        ('2242') to the standard ISO format ('2022-W42').

    Args:
        df (DataFrame): The DataFrame with weeks in the Sanders format to be fixed.

    Returns:
        DataFrame: The DataFrame with weeks converted to the standard ISO format.
    """
    df["WeekString"] = df["WeekString"].apply(convert_week)
    return df


def get_today_date(format_string="YYYY-MM-DD"):
    """
    Returns the current date in the format specified by the format_string.

    Args:
        format_string (str): The format to return the date in. Currently
            the only option is "YYYY-MM-DD".

    Returns:
        str: The current date in the format specified by format_string.
    """
    dict_formats = {"YYYY-MM-DD": "%Y-%m-%d"}
    today = date.today()
    return today.strftime(dict_formats[format_string])


def excel_date_to_datetime(excel_date):
    """
    Converts an Excel date to a datetime object.

    Args:
        excel_date (int): The Excel date to convert.

    Returns:
        datetime: The converted datetime object.
    """
    dt = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(excel_date) - 2)
    hour, minute, second = floatHourToTime(excel_date % 1)
    dt = dt.replace(hour=hour, minute=minute, second=second)
    return dt


def date_string_to_excel_date(date_string):
    """
    Converts a date from the format "YYYY-MM-DD" to an Excel date.

    Args:
        date_string (str): The date to convert, in the format "YYYY-MM-DD".

    Returns:
        int: The converted Excel date.
    """
    dt = datetime.strptime(date_string, "%Y-%m-%d")
    dt = (dt - datetime(1900, 1, 1)).days + 2
    return dt


def excel_date_to_date_string(excel_date):
    """
    Converts an Excel date to a date in the format "YYYY-MM-DD".

    Args:
        excel_date (int): The Excel date to convert.

    Returns:
        str: The converted date in the format "YYYY-MM-DD".
    """
    dt = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(excel_date) - 2)
    hour, minute, second = floatHourToTime(excel_date % 1)
    dt = dt.replace(hour=hour, minute=minute, second=second)
    return str(dt.strftime("%Y-%m-%d"))


def get_year_quarter_from_week_string(week_string):
    year = week_string.split("-")[0]
    week = week_string.split("-")[1].replace("W", "")
    quarter = (int(week) - 1) // 13 + 1
    return year, quarter


def get_year_quarter_from_date(date_string):
    year = date_string.split("-")[0]
    month = date_string.split("-")[1]
    quarter = str(int(month) // 4 + 1)
    return year, quarter


def get_quarter_string_from_date(date_string):
    year = date_string.split("-")[0]
    month = date_string.split("-")[1]
    quarter = str(int(month) // 4 + 1)
    return f"{year}-Q{quarter}"


def get_week_from_yearweek(yearweek):
    yearweek = str(yearweek)
    year = f"20{yearweek[:2]}"
    week = yearweek[-2:]
    week = f"{year}-W{week}"
    return week


def get_month_name_from_num(month_num):
    """
    Returns the name of the month corresponding to the given month number.

    Args:
        month_num (int or str): The month number, which can be an integer from 1 to 12

    Returns:
        str: The name of the month.

    Raises:
        KeyError: If the given month number is not found in the dictionary.

    """
    month_num = str(month_num)
    for month_name in dict_month_numbers:
        if dict_month_numbers[month_name] == month_num:
            return month_name


def get_current_time_in_timezone(timezone_str="US/Central"):
    return datetime.now(timezone(timezone_str))


def is_thursday_before_5pm_cst():
    # Get current UTC time
    now_cst = get_current_time_in_timezone("US/Central")

    # Get current day of the week
    day_of_week = now_cst.weekday()

    # Check if it is Thursday
    if day_of_week != 3:
        return False

    # Check if it is before 5 PM
    if now_cst.hour < 17:
        return True
    else:
        return False


def get_last_month_details():
    today = datetime.now()
    first_day_of_current_month = today.replace(day=1)
    last_month_date = first_day_of_current_month - timedelta(days=1)
    month_num = last_month_date.strftime("%m")
    month_name = get_month_name_from_num(month_num)
    year = last_month_date.strftime("%Y")
    return year, month_num, month_name


if __name__ == "__main__":
    print("Running as main")
    print(get_current_datetime("YYYYMMDD"))
    print(get_current_datetime("Weekday"))

    print(excel_date_to_date_string(44924))
