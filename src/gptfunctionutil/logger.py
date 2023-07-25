import logging

# Define the logs
logs = logging.getLogger('gptfunctionutil')
logs.setLevel(logging.DEBUG)

# Create a console handler and set the level to INFO
console_handler = logging.StreamHandler()
console_handler.setLevel(logs.level)

# Create a formatter and add it to the console handler
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',dt_fmt)
console_handler.setFormatter(formatter)

# Add the console handler to the logs
logs.addHandler(console_handler)