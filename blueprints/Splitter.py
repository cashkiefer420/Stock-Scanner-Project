import json
import schedule
import time

# Define the fields to keep
required_fields = [
    'Ticker', 
    'Price Change Today', 
    'Volume Today', 
    'DVAV (Day Volume Over Average Volume)', 
    'P/E Change (3 Mon)', 
    'Market Cap Change (3 Mon)'
]

def filter_and_update_data():
    try:
        # Open the stock data JSON file and load the data
        with open('/json/stock_data_export.json', 'r') as file:
            new_data = json.load(file)

        # If there's no data, just return and do nothing
        if not new_data:
            print("No new data found, skipping update.")
            return

        # Load the previously saved data if exists, otherwise initialize as empty list
        try:
            with open('json/Split_data.json', 'r') as file:
                existing_data = json.load(file)
        except FileNotFoundError:
            existing_data = []

        # Iterate through the new data and update existing data where necessary
        updated_data = []

        for new_item in new_data:
            updated_item = None
            for existing_item in existing_data:
                if existing_item.get('Ticker') == new_item.get('Ticker'):
                    updated_item = existing_item.copy()
                    for field in required_fields:
                        if new_item.get(field) != existing_item.get(field):
                            updated_item[field] = new_item.get(field)
                    break
            
            # If no existing data was found, add the new item
            if not updated_item:
                updated_item = {
                    'Ticker': new_item.get('Ticker'),
                    'Price Change Today': new_item.get('Price Change Today'),
                    'Volume Today': new_item.get('Avg Volume (3 mon)'),
                    'DVAV (Day Volume Over Average Volume)': new_item.get('DVAV (Day Volume Over Average Volume)'),
                    'P/E Change (3 Mon)': new_item.get('P/E Change (3 Mon)'),
                    'Market Cap Change (3 Mon)': new_item.get('Market Cap Change (3 Mon)')
                }

            updated_data.append(updated_item)

        # Save the updated data back to Split_data.json
        with open('json/Split_data.json', 'w') as file:
            json.dump(updated_data, file, indent=4)

        print("Data successfully filtered and saved.")
    
    except Exception as e:
        print(f"An error occurred: {e}")

# Function to run the process every 3 minutes
schedule.every(3).minutes.do(filter_and_update_data)

# Keep the script running to repeat the task every 3 minutes
while True:
    schedule.run_pending()
    time.sleep(1)
