from langchain_core.tools import tool
from datetime import datetime

@tool
def get_current_time():
    """Gets the current time in the local timezone. Use this when the user asks specifically for the time."""
    now = datetime.now()
    formatted_time = now.strftime('%I:%M %p')
    print(f"\n[Tool] Time used: {formatted_time}\n")
    return f"The current time is {formatted_time}"

@tool
def get_current_date():
    """Gets the current date, month, and year in the local timezone. Use this when the user asks for date."""
    now = datetime.now()
    formatted_date = now.strftime('%A, %B %d, %Y')
    print(f"\n[Tool] Date used: {formatted_date}\n")
    return f"The current date is {formatted_date}"
