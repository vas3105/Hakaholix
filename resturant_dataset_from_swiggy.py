import kagglehub
import pandas as pd
import json
import os
import glob
import re


print("1. Downloading Swiggy Restaurants Dataset from Kaggle...")
try:
    
    path = kagglehub.dataset_download("ashishjangra27/swiggy-restaurants-dataset")
    
  
    data_file = None
    csv_files = glob.glob(os.path.join(path, '**', '*.csv'), recursive=True)
    if csv_files:
       
        data_file = next((f for f in csv_files if 'swiggy' in os.path.basename(f).lower()), csv_files[0])
    
    if not data_file:
        raise FileNotFoundError("Could not find a CSV data file in the downloaded path.")
        
    print(f"   Download complete. Data file found at: {data_file}")

  
    df = pd.read_csv(data_file)
    
  
    df['city'] = df['city'].str.title().str.strip()
    
   
    kerala_cities = [
        'Kochi', 'Thiruvananthapuram', 'Kozhikode', 'Thrissur', 
        'Kannur', 'Alappuzha', 'Kollam', 'Palakkad', 'Malappuram', 
        'Trivandrum', 'Calicut', 'Ernakulam'
    ]
    
    df_kerala = df[df['city'].isin(kerala_cities)].copy()
    
    if df_kerala.empty:
        print("Warning: No restaurants found for the specified cities in Kerala.")
      
        final_restaurants_list = []
    else:
        print(f"   Successfully filtered {len(df_kerala)} restaurants in Kerala cities.")
        
  
        final_restaurants_list = []
        
       
        def clean_cost(cost_str):
            if pd.isna(cost_str):
                return None
            try:
              
                return int(re.sub(r'[₹,]', '', str(cost_str).strip()))
            except ValueError:
                return None

        for index, row in df_kerala.iterrows():
            
            rating_count = str(row['rating_count']).replace(' ratings', '').strip()
            
            restaurant_entry = {
                "id": row['id'], 
                "name": row['name'], 
                "cuisine": row['cuisine'], 
                "cost_for_two": clean_cost(row['cost']),
                
                
                "review_options": { 
                    "rating_score": row['rating'], 
                    "total_ratings": rating_count 
                },
                
                "location": {
                    "city": row['city'],
                    "address": row['address']
                }
            }
            final_restaurants_list.append(restaurant_entry)

  
    output_filename = 'swiggy_kerala_restaurants_with_reviews.json'
    
    print("\n--- Saving File ---")
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump({"restaurants": final_restaurants_list}, f, indent=2, ensure_ascii=False)
        
        print(f" Successfully saved {len(final_restaurants_list)} restaurant entries to **'{output_filename}'**.")

    except Exception as e:
        print(f"Error saving file: {e}. Please check your directory permissions.")

except FileNotFoundError as e:
    print(f" Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
