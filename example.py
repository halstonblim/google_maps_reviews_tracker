#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example script demonstrating how to use the Google Maps Review Scraper
"""

import argparse
from maps_review_scraper import scrape_reviews, plot_reviews_by_month

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run example Google Maps review scraper')
    parser.add_argument('--mode', choices=['scrape', 'load'], default='scrape',
                        help='Mode to run: scrape for new reviews or load from existing CSV')
    parser.add_argument('--input-file', default='reviews.csv',
                        help='CSV file to load reviews from (when mode=load)')
    args = parser.parse_args()
    
    # Example parameters
    url = "https://maps.app.goo.gl/aJCRiy3C5gtoBZpJ7"
    output_file = "reviews.csv"
    max_reviews = 500
    wait_time = 12
    plot_output = "monthly_reviews.png"
    
    if args.mode == 'scrape':
        # Scrape mode - get new reviews from URL
        print(f"Starting review scraping with the following parameters:")
        print(f"URL: {url}")
        print(f"Max reviews: {max_reviews}")
        print(f"Wait time: {wait_time} seconds")
        print(f"Output file: {output_file}")
        
        # Call the scrape_reviews function
        reviews_df = scrape_reviews(url, max_reviews=max_reviews, wait_time=wait_time)
        
        if not reviews_df.empty:
            # Print the first 5 reviews
            print("\n===== First 5 Reviews =====")
            print(reviews_df.head())
            print("==========================\n")
            
            # Save to CSV
            reviews_df.to_csv(output_file, index=False)
            print(f"Reviews saved to {output_file}")
            
            # Generate and save the plot
            print("Generating monthly review plot...")
            plot_reviews_by_month(reviews_df, output_path=plot_output)
            
            print(f"Total reviews scraped: {len(reviews_df)}")
            if max_reviews and len(reviews_df) < max_reviews:
                print(f"Note: Requested {max_reviews} reviews but could only find {len(reviews_df)}")
        else:
            print("No reviews were scraped.")
    
    else:  # Load mode
        import pandas as pd
        print(f"Loading reviews from: {args.input_file}")
        
        try:
            # Load the reviews from CSV
            reviews_df = pd.read_csv(args.input_file)
            
            # Convert the exact_time column to datetime for plotting
            if 'exact_time' in reviews_df.columns:
                reviews_df['exact_time'] = pd.to_datetime(reviews_df['exact_time'])
            
            # Show basic info about the loaded data
            print(f"Successfully loaded {len(reviews_df)} reviews")
            print("\n===== First 5 Reviews =====")
            print(reviews_df.head())
            print("==========================\n")
            
            # Generate and save the plot
            print("Generating monthly review plot...")
            plot_reviews_by_month(reviews_df, output_path=plot_output)
            
        except Exception as e:
            print(f"Error loading reviews: {e}")
            return

if __name__ == "__main__":
    main() 