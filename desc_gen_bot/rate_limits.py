import datetime
from localdb import file_exists, clear_file

RATE_LIMITS_FOLDER = "rate_limits"

def create_or_append_request_info(filename, request_count):
    # Get the current date
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    clear_file(filename)

    # Open the file in append mode. If it does not exist, it will be created.
    with open(filename, 'a') as file:
        file.write(str(request_count))
        

def get_current_rate_limit(user_id):
    filename = build_filename_for_current_date(user_id)
    if not file_exists(filename):
        return 0
    
    with open(filename, 'r') as file:
        return int(file.read())

def build_filename_for_current_date(user_id):
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    return f"{RATE_LIMITS_FOLDER}/{user_id}_{current_date}"