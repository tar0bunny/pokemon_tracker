import psycopg2
import requests
import glob
import pandas as pd
import os
import re
from difflib import get_close_matches
from ids import *
from datetime import datetime
from threading import Thread

DBNAME = "tar0bunny"
USER = "<your db user name>"
PASSWORD = "<your db password>"


def build_list(set_name):
    """
    Fetches trading card product and pricing data for a given set, processes it,
    and exports each card as a Python dictionary variable to a dated file.
    
    This function:
    1. Fuzzy matches the provided set name against known set IDs
    2. Fetches product details and pricing from tcgcsv.com API
    3. Extracts rarity information from extended product data
    4. Merges products with their market prices
    5. Filters out cards without rarity and code cards
    6. Removes duplicate cards (keeping first occurrence of each name+rarity combo)
    7. Generates a Python file containing each card as a dictionary variable with:
       - Sanitized variable name (lowercase, alphanumeric + underscores)
       - Card details: name, set_name, rarity, price, image URL
    8. Saves to ./lists/{set_name}_{MMDDYYYY}.py, removing any old files for this set
    
    Args:
        set_name (str): Name of the trading card set to process
    
    Returns:
        pandas.DataFrame: Processed card data with columns [productId, name, rarity, 
                         imageUrl, marketPrice], or None if set not found or error occurs
    """
    # Fuzzy match the set name
    matches = get_close_matches(set_name, IDS.keys(), n=1, cutoff=0.2)
    
    if not matches:
        print(f"No match found for '{set_name}'")
        return None
    
    matched_name = matches[0]
    set_id = IDS[matched_name] 
    
    print(f"Matched '{set_name}' to '{matched_name}' (ID: {set_id})")
    products_url = f"https://tcgcsv.com/tcgplayer/3/{set_id}/products"
    prices_url = f"https://tcgcsv.com/tcgplayer/3/{set_id}/prices"
    
    try:
        products_json = requests.get(products_url, timeout=30).json()
        prices_json = requests.get(prices_url, timeout=30).json()
    except requests.exceptions.Timeout:
        print(f"Timeout fetching data for {matched_name}")
        return None
    except Exception as e:
        print(f"Error fetching data for {matched_name}: {e}")
        return None

    products = pd.DataFrame(products_json['results'])
    prices = pd.DataFrame(prices_json['results'])

    rarity_values = []

    for extended_data in products['extendedData']:
        rarity = None
        if extended_data:
            for item in extended_data:
                if item['name'] == 'Rarity':
                    rarity = item['value']
                    break
        rarity_values.append(rarity)

    products['rarity'] = rarity_values

    products_subset = products[['productId', 'name', 'rarity', 'imageUrl']]
    prices_subset = prices[['productId', 'marketPrice']]

    # Merge on productId
    result = pd.merge(products_subset, prices_subset, on='productId', how='inner')
    result = result[result['rarity'].notna()]
    result = result[result['rarity'] != 'Code Card']
    
    # Remove duplicates - keep first occurrence of each name+rarity combo
    result = result.drop_duplicates(subset=['name', 'rarity'], keep='first')

    # Handle directories and files
    os.makedirs('./lists', exist_ok=True)
    formatted_set_name = matched_name.replace(' ', '_').replace(':', '_')
    
    existing_files = glob.glob(f'./lists/{formatted_set_name}_*.py')
    for file in existing_files:
        os.remove(file)
        print(f"Removed old file: {file}")
    current_date = datetime.now().strftime('%m%d%Y')
    filename = f'./lists/{formatted_set_name}_{current_date}.py'
    
    # Write to python files as dictionaries
    with open(filename, 'w') as f:
        for _, row in result.iterrows():
            temp = row['name'].lower()
            temp = re.sub(r'[^a-z0-9_]', '_', temp)
            temp = re.sub(r'_+', '_', temp).strip('_')
            if temp and temp[0].isdigit():
                temp = '_' + temp
            
            rarity_lower = row['rarity'].lower()
            
            f.write(f'{temp} = {{\n')
            f.write(f'    "name": "{row["name"]}",\n')
            f.write(f'    "set_name": "{matched_name}",\n')
            f.write(f'    "rarity": "{rarity_lower}",\n')
            f.write(f'    "price": {row["marketPrice"]},\n')
            f.write(f'    "image": "{row["imageUrl"]}"\n')
            f.write(f'}}\n\n')

    print(f"Extracted {len(result)} matching records for set {set_id}")
    print(f"Saved to: {filename}")
    return result


def search_card(name, set_name, rarity):
    """
    Searches for a specific trading card by name, set, and rarity, returning its details.
    
    This function:
    1. Fuzzy matches the provided set name against known sets (60% similarity threshold)
    2. Calls build_list() to fetch and generate the latest card data file for that set
    3. Locates and reads the generated Python file containing card dictionaries
    4. Executes the file content to load all card variables into memory
    5. Filters cards by the specified rarity
    6. Sanitizes the search name to match variable naming conventions
    7. Fuzzy matches the sanitized name against available card variable names
    8. Prints the matched card's details (name, set, rarity, price, image URL)
    
    Args:
        name (str): Name of the card to search for
        set_name (str): Name of the set the card belongs to
        rarity (str): Rarity level of the card (e.g., 'common', 'rare', 'ultra rare')
    
    Returns:
        dict: Card data dictionary with keys ['name', 'set_name', 'rarity', 'price', 'image'],
              or None if set not found, no matching cards, or search fails
    """
    matches = get_close_matches(set_name, IDS.keys(), n=1, cutoff=0.6)
    
    if not matches:
        print(f"No match found for set '{set_name}'")
        return None
    
    matched_set_name = matches[0]
    
    print(f"Fetching latest data for {matched_set_name}...")
    build_list(matched_set_name)


    formatted_set_name = matched_set_name.replace(' ', '_').replace(':', '_')
    matching_files = glob.glob(f'./lists/{formatted_set_name}_*.py')
    
    if not matching_files:
        print(f"Failed to find data file for {matched_set_name}")
        return None
    
    filename = matching_files[0]
    with open(filename, 'r') as f:
        file_content = f.read()
    
    local_vars = {}
    exec(file_content, {}, local_vars)
    
    search_name = name.lower()
    search_name = re.sub(r'[^a-z0-9_]', '_', search_name)
    search_name = re.sub(r'_+', '_', search_name).strip('_')
    
    matching_cards = {k: v for k, v in local_vars.items() 
                     if isinstance(v, dict) and v.get('rarity') == rarity}
    
    if not matching_cards:
        print(f"No cards found with rarity '{rarity}' in {matched_set_name}")
        return None
    
    var_names = list(matching_cards.keys())
    name_matches = get_close_matches(search_name, var_names, n=1, cutoff=0.2)
    
    if not name_matches:
        print(f"No card found matching name '{name}' with rarity '{rarity}' in {matched_set_name}")
        return None
    
    matched_var_name = name_matches[0]
    card_data = matching_cards[matched_var_name]
    
    print(f"Name: {card_data['name']}")
    print(f"Set name: {card_data['set_name']}")
    print(f"Rarity: {card_data['rarity']}")
    print(f"Price: ${card_data['price']}")
    print(f"Image: {card_data['image']}")
    
    return card_data


def add_card(name, set_name, rarity, price, image):
    """
    Inserts a new Pokémon card record into the PostgreSQL 'pokemon' table.
    
    Args:
        name (str): Name of the Pokémon card
        set_name (str): Name of the set the card belongs to
        rarity (str): Rarity level of the card
        price (float): Market price of the card
        image (str): URL to the card's image
    
    Returns:
        None
    """
    conn = psycopg2.connect(
        dbname=DBNAME,
        user=USER,
        password=PASSWORD,
        host="localhost",
        port=5432
    )

    cur = conn.cursor()

    sql = """
    INSERT INTO pokemon (name, set_name, rarity, price, image)
    VALUES (%s, %s, %s, %s, %s)
    """

    cur.execute(sql, (name,  set_name, rarity, price, image))
    conn.commit()
    cur.close()
    conn.close()


def remove_card(card_name):
    """
    Deletes the first matching Pokémon card from the database by name.
    
    Args:
        card_name (str): Name of the card to remove
    
    Returns:
        bool: True if a card was deleted, False if no match found
    """
    conn = psycopg2.connect(
        dbname=DBNAME,
        user=USER,
        password=PASSWORD,
        host="localhost",
        port=5432
    )
    
    cur = conn.cursor()
    
    sql = """
    DELETE FROM pokemon 
    WHERE id = (
        SELECT id FROM pokemon 
        WHERE name = %s 
        ORDER BY id 
        LIMIT 1
    )
    RETURNING id, name
    """
    
    cur.execute(sql, (card_name,))
    deleted = cur.fetchone()
    
    conn.commit()
    cur.close()
    conn.close()
    
    return deleted is not None
    

def refresh_all_prices():
    """
    Updates market prices for all Pokémon cards in the database by fetching latest data.
    
    Retrieves all unique sets from the database, rebuilds price lists for each set using
    build_list(), then fuzzy matches each card in the database to updated pricing data
    and updates the price field.
    
    Returns:
        dict: Results containing 'updated' (count), 'failed' (list of card names), 
              'total' (count), and optionally 'error' (str) if exception occurred
    """
    print("=== Starting refresh_all_prices ===")
    
    try:
        conn = psycopg2.connect(
            dbname=DBNAME,
            user=USER,
            password=PASSWORD,
            host="localhost",
            port=5432
        )
        
        cur = conn.cursor()
        
        # Get unique sets from database
        cur.execute("SELECT DISTINCT set_name FROM pokemon")
        db_sets = [row[0] for row in cur.fetchall()]
        print(f"Found {len(db_sets)} unique sets: {db_sets}")
        
        # Rebuild lists for each set
        for set_name in db_sets:
            print(f"Building list for: {set_name}")
            try:
                build_list(set_name)
            except Exception as e:
                print(f"Error building list for {set_name}: {e}")
        
        cur.execute("SELECT id, name, set_name, rarity FROM pokemon")
        cards = cur.fetchall()
        print(f"Updating {len(cards)} cards...")
        
        updated_count = 0
        failed_cards = []
        
        for card_id, card_name, card_set_name, card_rarity in cards:
            try:
                formatted_set_name = card_set_name.replace(' ', '_')
                matching_files = glob.glob(f'./lists/{formatted_set_name}_*.py')
                
                if not matching_files:
                    failed_cards.append(f"{card_name} ({card_set_name})")
                    continue
                
                filename = matching_files[0]
                with open(filename, 'r') as f:
                    file_content = f.read()
                
                local_vars = {}
                exec(file_content, {}, local_vars)
                
                search_name = card_name.lower()
                search_name = re.sub(r'[^a-z0-9_]', '_', search_name)
                search_name = re.sub(r'_+', '_', search_name).strip('_')
                
                rarity_lower = card_rarity.lower()
                matching_cards = {k: v for k, v in local_vars.items() 
                                 if isinstance(v, dict) and v.get('rarity') == rarity_lower}
                
                if not matching_cards:
                    failed_cards.append(f"{card_name} ({card_set_name})")
                    continue
                
                var_names = list(matching_cards.keys())
                name_matches = get_close_matches(search_name, var_names, n=1, cutoff=0.4)
                
                if not name_matches:
                    failed_cards.append(f"{card_name} ({card_set_name})")
                    continue
                
                matched_var_name = name_matches[0]
                card_data = matching_cards[matched_var_name]
                new_price = card_data.get('price', 0)
                
                cur.execute("UPDATE pokemon SET price = %s WHERE id = %s", (new_price, card_id))
                updated_count += 1
                
            except Exception as e:
                print(f"Error updating {card_name}: {str(e)}")
                failed_cards.append(f"{card_name} ({card_set_name})")
        
        conn.commit()
        cur.close()
        conn.close()
        
        result = {
            "updated": updated_count,
            "failed": failed_cards,
            "total": len(cards)
        }
        print(f"=== Refresh complete: {result} ===")
        return result
        
    except Exception as e:
        print(f"=== ERROR: {str(e)} ===")
        import traceback
        traceback.print_exc()
        return {
            "updated": 0,
            "failed": [],
            "total": 0,
            "error": str(e)
        }