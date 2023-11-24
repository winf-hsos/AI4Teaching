import colorama
import datetime
import os

def log(message, type='info'):
    if type == 'info':
        color = colorama.Fore.WHITE
    elif type == 'error':
        color = colorama.Fore.RED 
    elif type == 'warning':
        color = colorama.Fore.YELLOW
    elif type == 'success':
        color = colorama.Fore.GREEN
    elif type == 'debug':
        color = colorama.Fore.CYAN

    # Get the current datetime
    current_datetime = datetime.datetime.now()

    # Format it to include only minutes
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S: ")

    print(color + formatted_datetime + str(message) + colorama.Fore.RESET)

def make_sure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)