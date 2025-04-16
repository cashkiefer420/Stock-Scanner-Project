def main():
    # Start the timer
    start_time = datetime.now()
    logger.info(f"Script started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    today = datetime.now().strftime("%Y-%m-%d")
    sync_tickers_and_names()

    formatted_tickers_data = read_json_file(FORMATTED_TICKERS_FILE_PATH)
    tickers = formatted_tickers_data.get("tickers", [])
    pe_data = read_json_file(PE_FILE_PATH)
    mc_data = read_json_file(MARKETCAP_FILE_PATH)
    export_data = read_json_file(EXPORT_FILE_PATH)

    existing_data_map = {item['Ticker']: item for item in export_data if isinstance(item, dict)}

    # Corrected ThreadPoolExecutor block
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda entry: fetch_price(
            entry["Ticker"] if isinstance(entry, dict) else entry, pe_data, mc_data, export_data, today), tickers))

    for data in filter(None, results):
        existing_data_map[data['Ticker']] = data

    write_json_file(EXPORT_FILE_PATH, list(existing_data_map.values()))
    write_json_file(PE_FILE_PATH, pe_data)
    write_json_file(MARKETCAP_FILE_PATH, mc_data)

    # End the timer
    end_time = datetime.now()
    elapsed_time = end_time - start_time
    logger.info(f"Processing complete. Script finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Total execution time: {elapsed_time}")

if __name__ == "__main__":
    main()
