import requests
from bs4 import BeautifulSoup
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

base_url = "https://www.askbankifsccode.com/"
limit = 1000  # Limit of entries per file

def get_option_values(url):
    logging.info(f"Fetching URL: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        options = soup.find_all("option")
        values = [option.get("value") for option in options if option.get("value")]
        return values
    else:
        logging.error(f"Failed to fetch URL: {url} with status code: {response.status_code}")
        return []

def write_to_file(data, file_index):
    filename = f'data_{file_index}.txt'
    with open(filename, 'w', encoding='utf-8') as file:
        for url in data:
            file.write(f"{url}\n")
    logging.info(f"Saved {len(data)} URLs to {filename}")

def main():
    data = []
    file_index = 1
    total_count = 0

    # Step 1: Get all names
    names_url = f"{base_url}"
    names = get_option_values(names_url)

    total_names = len(names)
    logging.info(f"Found {total_names} names")

    for i, name in enumerate(names, 1):
        # Step 2: Get all state names
        states = get_option_values(name)

        total_states = len(states)
        logging.info(f"Found {total_states} states for name {name} ({i}/{total_names})")

        for j, state in enumerate(states, 1):
            # Step 3: Get all district names
            districts = get_option_values(state)

            total_districts = len(districts)
            logging.info(f"Found {total_districts} districts for state {state} ({j}/{total_states})")

            for k, district in enumerate(districts, 1):
                # Step 4: Get all area with codes names
                areas = get_option_values(district)

                total_areas = len(areas)
                logging.info(f"Found {total_areas} areas for district {district} ({k}/{total_districts})")

                for l, area in enumerate(areas, 1):
                    # Step 5: Store the final URL
                    data.append(area)
                    total_count += 1
                    logging.info(f"Added area {area} ({l}/{total_areas})")

                    if total_count >= limit:
                        # Write to file and reset
                        write_to_file(data, file_index)
                        data = []
                        total_count = 0
                        file_index += 1

    # Write remaining data to a new file if any
    if data:
        write_to_file(data, file_index)

    logging.info("Data extraction completed")

if __name__ == "__main__":
    main()
