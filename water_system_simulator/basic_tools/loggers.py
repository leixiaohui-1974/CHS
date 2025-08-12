import csv

class CSVLogger:
    """
    A simple logger for saving simulation data to a CSV file.
    """
    def __init__(self, filename, headers):
        """
        Initializes the CSV logger.

        Args:
            filename (str): The name of the file to save the data to.
            headers (list of str): A list of strings for the header row.
        """
        self.filename = filename
        self.headers = headers
        with open(self.filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)

    def log(self, data):
        """
        Logs a row of data to the CSV file.

        Args:
            data (list): A list of data to log, corresponding to the headers.
        """
        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data)
