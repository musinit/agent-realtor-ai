import platform
import os

user_data_path = "user_data/"

def append_line_to_file(filename, line_to_append):
    """
    Appends a new line to the specified file.

    Args:
        filename (str): The name of the file to which the line will be appended.
        line_to_append (str): The line that will be appended to the file.
    """
    try:
        with open(filename, 'a') as file:  # Open the file in append mode
            file.write(line_to_append + '\n')  # Write the line and add a newline character
        print(f"Successfully appended the line to {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")


def make_file_append_only(filename):
    """Set the file to append-only mode on Linux."""
    if platform.system() == 'Linux':
        try:
            os.system(f'chattr +a {filename}')
            print(f"The file '{filename}' is now set to append-only mode.")
        except Exception as e:
            print(f"Failed to set append-only mode: {e}")
    else:
        print("Append-only mode is only supported on Linux systems.")


def create_and_set_append_only(filename):
    """Create a file and set it to append-only mode."""
    try:
        with open(filename, 'w') as f:
            f.write("")  # Create an empty file
        make_file_append_only(filename)  # Set the file to append-only mode
    except Exception as e:
        print(f"An error occurred while creating the file: {e}")


def read_file(filename):
    try:
        with open(filename, 'r') as file:
            content = file.read()
            return content
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except IOError:
        print("An error occurred while reading the file.")


def clear_file(filename):
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            pass

    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
    except IOError as e:
        print(f"Error while clearing the file: {e}")


def file_exists(filename):
    """Check if the specified file exists."""
    return os.path.isfile(filename)