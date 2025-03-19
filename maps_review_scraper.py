#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google Maps Review Scraper
A simplified script to scrape Google Maps reviews sorted by newest first
"""

import time
import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import argparse
import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def parse_time_text(time_text):
    """
    Parse the time text from Google Maps reviews into a datetime object.
    
    Args:
        time_text: Text representation of the review time (e.g., "2 days ago")
        
    Returns:
        parsed_time: Datetime object representing the estimated review time
    """
    now = datetime.datetime.now()
    
    # Handle different time formats
    if "a day ago" in time_text.lower() or "1 day ago" in time_text.lower():
        return now - datetime.timedelta(days=1)
    elif "days ago" in time_text.lower():
        days = int(re.search(r'(\d+)', time_text).group(1))
        return now - datetime.timedelta(days=days)
    elif "a week ago" in time_text.lower() or "1 week ago" in time_text.lower():
        return now - datetime.timedelta(weeks=1)
    elif "weeks ago" in time_text.lower():
        weeks = int(re.search(r'(\d+)', time_text).group(1))
        return now - datetime.timedelta(weeks=weeks)
    elif "a month ago" in time_text.lower() or "1 month ago" in time_text.lower():
        # Approximate a month as 30 days
        return now - datetime.timedelta(days=30)
    elif "months ago" in time_text.lower():
        months = int(re.search(r'(\d+)', time_text).group(1))
        # Approximate months as 30 days each
        return now - datetime.timedelta(days=30*months)
    elif "a year ago" in time_text.lower() or "1 year ago" in time_text.lower():
        # Approximate a year as 365 days
        return now - datetime.timedelta(days=365)
    elif "years ago" in time_text.lower():
        years = int(re.search(r'(\d+)', time_text).group(1))
        # Approximate years as 365 days each
        return now - datetime.timedelta(days=365*years)
    elif "an hour ago" in time_text.lower() or "1 hour ago" in time_text.lower():
        return now - datetime.timedelta(hours=1)
    elif "hours ago" in time_text.lower():
        hours = int(re.search(r'(\d+)', time_text).group(1))
        return now - datetime.timedelta(hours=hours)
    elif "minutes ago" in time_text.lower():
        minutes = int(re.search(r'(\d+)', time_text).group(1))
        return now - datetime.timedelta(minutes=minutes)
    
    # Try to parse specific date formats
    try:
        # Format: Month Year (e.g., "March 2022")
        dt = datetime.datetime.strptime(time_text, "%B %Y")
        return dt.replace(day=15)  # Middle of the month as an approximation
    except ValueError:
        pass
    
    # Default to current time if parsing fails
    print(f"Could not parse review time: {time_text}")
    return now

def scrape_reviews(url, max_reviews=None, wait_time=10):
    """
    Scrape reviews from a Google Maps URL.
    
    Args:
        url: Google Maps URL
        max_reviews: Maximum number of reviews to scrape (default: None = all available)
        wait_time: Time to wait between scrolls in seconds (default: 10)
            
    Returns:
        reviews_df: Pandas DataFrame with review data
    """
    # Set up WebDriver
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Performance optimizations
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--js-flags=--expose-gc")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument("--enable-unsafe-swiftshader")
    options.add_argument("--disk-cache-size=33554432")  # 32MB
    
    # Disable images to load faster
    prefs = {
        "profile.managed_default_content_settings.images": 2,  # Don't load images
        "profile.default_content_setting_values.notifications": 2  # Don't allow notifications
    }
    options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Set page load timeout
    driver.set_page_load_timeout(30)
    
    try:
        # Navigate to the URL
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "lMbq3e"))
        )
        
        # Extract location name
        try:
            location_name = driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf").text
            print(f"Location: {location_name}")
        except NoSuchElementException:
            location_name = "Unknown Location"
            print("Could not extract location name")
        
        # Click on reviews tab
        try:
            reviews_tab = driver.find_element(By.CSS_SELECTOR, "button[data-tab-index='1']")
            reviews_tab.click()
            print("Clicked on reviews tab")
            time.sleep(2)  # Wait for reviews to load
        except NoSuchElementException:
            print("Could not find reviews tab")
            return pd.DataFrame()
        
        # Sort reviews by newest first
        try:
            # Find and click on the sort button
            print("Looking for sort button...")
            sort_button = driver.find_element(By.CSS_SELECTOR, "button[data-value='Sort']")
            # Use JavaScript to click the button
            driver.execute_script("arguments[0].click();", sort_button)
            time.sleep(3)  # Reduced wait time from 4 to 3 seconds
            print("Clicked sort button")
            
            # Try to find all menu items
            try:
                # Try different selectors for menu items
                menu_items = driver.find_elements(By.CSS_SELECTOR, "div[role='menuitemradio']")
                if not menu_items:
                    menu_items = driver.find_elements(By.CSS_SELECTOR, "div[role='menuitem']")
                if not menu_items:
                    menu_items = driver.find_elements(By.CSS_SELECTOR, ".yr2tVc,.fxNQSd")  # Common Google Maps menu classes
                
                print(f"Found {len(menu_items)} menu items:")
                for i, item in enumerate(menu_items):
                    print(f"  Menu item {i+1}: '{item.text}' (class: {item.get_attribute('class')})")
                
                # Try to find "newest" option
                newest_option = None
                
                # First look for text containing "newest" (case insensitive)
                for item in menu_items:
                    if 'newest' in item.text.lower():
                        newest_option = item
                        print(f"Found 'Newest' in menu text: '{item.text}'")
                        break
                
                # If not found by text, try the second option (often "newest" is second)
                if newest_option is None and len(menu_items) >= 2:
                    newest_option = menu_items[1]  # Second option is often "newest"
                    print(f"Using second menu item as fallback: '{newest_option.text}'")
                
                # If we found an option to click
                if newest_option:
                    # Try best click method
                    try:
                        # JavaScript click is most reliable
                        driver.execute_script("arguments[0].click();", newest_option)
                    except Exception as e:
                        print(f"JavaScript click failed: {e}")
                    
                    # Wait after trying to click
                    time.sleep(3)  # Reduced from 5 to 3 seconds
                    print("Attempted to sort reviews by newest")
                else:
                    print("Could not identify 'newest' option in menu")
            
            except Exception as menu_error:
                print(f"Error finding menu items: {menu_error}")
                
        except Exception as e:
            print(f"Could not sort reviews: {e}")
            # Take a screenshot for debugging
            driver.save_screenshot("sort_error.png")
            print("Saved screenshot to sort_error.png")
        
        # Scroll to load more reviews
        print("Scrolling to load more reviews...")
        previous_height = 0
        max_scrolls = 30  
        reviews_container = None
        
        # Try to find the reviews container - try multiple selectors
        try:
            # Try different possible container selectors
            selectors = [
                ".m6QErb.DxyBCb.kA9KIf.dS8AEf", 
                ".m6QErb.DxyBCb.kA9KIf", 
                "div[role='feed']",
                ".lXJj5c.Hk4XGb"
            ]
            
            for selector in selectors:
                containers = driver.find_elements(By.CSS_SELECTOR, selector)
                if containers:
                    reviews_container = containers[0]
                    print(f"Found reviews container with selector: {selector}")
                    break
            
            if not reviews_container:
                print("Could not find specific reviews container, using body for scrolling")
        except Exception as e:
            print(f"Error finding reviews container: {e}")
        
        # Try an initial click on the reviews panel to ensure focus
        try:
            panel = driver.find_element(By.CSS_SELECTOR, ".lXJj5c.Hk4XGb")
            driver.execute_script("arguments[0].click();", panel)
            time.sleep(1)
        except:
            pass
        
        load_more_attempts = 0
        last_review_count = 0
        consecutive_same_count = 0
        
        # Main scrolling loop
        for i in range(max_scrolls):
            # Check if we've reached the maximum number of reviews
            current_reviews = len(driver.find_elements(By.CSS_SELECTOR, "div.jftiEf"))
            print(f"Current review count before scroll {i+1}: {current_reviews}")
            
            # Exit if we've reached the max_reviews limit
            if max_reviews and current_reviews >= max_reviews:
                print(f"Reached maximum requested reviews ({max_reviews}), stopping scrolling")
                break
            
            # Check if we're stuck at the same number
            if current_reviews == last_review_count:
                consecutive_same_count += 1
            else:
                consecutive_same_count = 0
            
            # If stuck at the same count for 3 consecutive scrolls, try more aggressive techniques
            if consecutive_same_count >= 3:  # Reduced from 5 to 3 for faster execution
                print("Stuck at same review count, trying more aggressive scrolling techniques...")
                
                # Try scrolling up then down to reset view
                driver.execute_script("window.scrollTo(0, 0);")  # Scroll to top
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Back to bottom
                time.sleep(wait_time)  # Use wait_time from parameter
                
                # If we're still stuck, break out of the loop earlier for faster execution
                if consecutive_same_count >= 5:  # Reduced from 8 to 5
                    print(f"Still stuck at {current_reviews} reviews, stopping scrolling")
                    break
            
            # Scroll methods
            if reviews_container:
                try:
                    # Method 1: Scroll the reviews container directly
                    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", reviews_container)
                except:
                    pass
                
            # Method 2: Standard scroll - most reliable
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait between scrolls
            print(f"Scroll {i+1}/{max_scrolls}...")
            print(f"Waiting {wait_time} seconds for content to load...")
            time.sleep(wait_time)  # Use wait_time from parameter
            
            # Skip button pressing as requested
            
            # Check if the page height has changed
            new_height = driver.execute_script("return document.body.scrollHeight")
            current_reviews_after_scroll = len(driver.find_elements(By.CSS_SELECTOR, "div.jftiEf"))
            
            if new_height == previous_height and current_reviews_after_scroll == current_reviews:
                # If neither height nor review count changed, try one more scroll with longer wait time
                extended_wait = wait_time + 5  # 5 seconds longer than normal wait
                print(f"No new content loaded, trying one more scroll with longer wait ({extended_wait} seconds)...")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(extended_wait)
                
                # Check one more time
                new_height = driver.execute_script("return document.body.scrollHeight")
                current_reviews_after_techniques = len(driver.find_elements(By.CSS_SELECTOR, "div.jftiEf"))
                
                # If still no change in either height or review count, break earlier
                if new_height == previous_height and current_reviews_after_techniques == current_reviews:
                    consecutive_same_count += 1
                    if consecutive_same_count >= 2:  # Reduced from 3 to 2
                        print(f"No more reviews loading after {consecutive_same_count} attempts, stopping")
                        break
                else:
                    consecutive_same_count = 0
            elif current_reviews_after_scroll > current_reviews:
                # If we got new reviews even though height didn't change, reset consecutive count
                consecutive_same_count = 0
            
            previous_height = new_height
            last_review_count = current_reviews
            
            # Count reviews after each scroll
            review_count = len(driver.find_elements(By.CSS_SELECTOR, "div.jftiEf"))
            print(f"Currently found {review_count} reviews after scroll {i+1}")
            
            # Stop if we've hit max_reviews or are close to it
            if max_reviews and review_count >= max_reviews:
                print(f"Reached maximum requested reviews ({max_reviews}), stopping scrolling")
                break
            
        print("Finished scrolling, waiting for reviews to fully load...")
        time.sleep(min(5, wait_time/2))  # Use half of wait_time but max 5 seconds
        
        # Extract reviews
        review_elements = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
        print(f"Found {len(review_elements)} review elements")
        
        reviews = []
        now = datetime.datetime.now()
        
        # Only process up to max_reviews if specified
        elements_to_process = review_elements[:max_reviews] if max_reviews else review_elements
        
        for element in elements_to_process:
            try:
                # Get rating
                rating_element = element.find_element(By.CSS_SELECTOR, "span.kvMYJc")
                aria_label = rating_element.get_attribute("aria-label")
                rating = float(aria_label.split()[0].replace(",", "."))
                
                # Get review time
                time_element = element.find_element(By.CSS_SELECTOR, "span.rsqaWe")
                time_text = time_element.text
                
                # Parse the time text to get exact datetime
                exact_time = parse_time_text(time_text)
                
                # Get reviewer name
                try:
                    reviewer_name = element.find_element(By.CSS_SELECTOR, "div.d4r55").text
                except NoSuchElementException:
                    try:
                        reviewer_name = element.find_element(By.CSS_SELECTOR, "span.X7jCAb").text
                    except NoSuchElementException:
                        reviewer_name = "Unknown Reviewer"
                
                reviews.append({
                    "location": location_name,
                    "reviewer_name": reviewer_name,
                    "rating": rating,
                    "time_text": time_text,
                    "exact_time": exact_time,
                    "scraped_at": now
                })
                
            except (NoSuchElementException, ValueError) as e:
                print(f"Error extracting review data: {e}")
        
        # Create DataFrame
        reviews_df = pd.DataFrame(reviews)
        print(f"Successfully scraped {len(reviews_df)} reviews for {location_name}")
        
        return reviews_df
    
    except Exception as e:
        print(f"Error scraping reviews: {e}")
        return pd.DataFrame()
    
    finally:
        driver.quit()
        print("WebDriver closed")

def plot_reviews_by_month(df, output_path='reviews_by_month.png'):
    """
    Plot the average review score by month with number of reviews as bar labels.
    
    Args:
        df: DataFrame containing the reviews
        output_path: Path to save the plot image
    """
    # Create a copy to avoid modifying the original dataframe
    plot_df = df.copy()
    
    # Determine the column name for ratings (either 'score' or 'rating')
    rating_column = 'rating' if 'rating' in plot_df.columns else 'score'
    if rating_column not in plot_df.columns:
        print("Error: Could not find rating column (tried 'rating' and 'score')")
        return
    
    # Determine the column name for time (either 'datetime', 'exact_time', or 'time_text')
    time_column = None
    if 'exact_time' in plot_df.columns:
        time_column = 'exact_time'
    elif 'datetime' in plot_df.columns:
        time_column = 'datetime'
    elif 'time_text' in plot_df.columns:
        # Try to convert time_text to datetime
        try:
            plot_df['datetime'] = pd.to_datetime(plot_df['time_text'])
            time_column = 'datetime'
        except:
            print("Error: Could not convert 'time_text' to datetime")
            return
    
    if time_column is None:
        print("Error: Could not find time column (tried 'exact_time', 'datetime', and 'time_text')")
        return
    
    # Make sure time column is datetime type
    if not pd.api.types.is_datetime64_any_dtype(plot_df[time_column]):
        try:
            plot_df[time_column] = pd.to_datetime(plot_df[time_column])
        except:
            print(f"Error: Could not convert {time_column} to datetime")
            return
    
    # Extract month and year from datetime
    plot_df['year_month'] = plot_df[time_column].dt.to_period('M')
    
    # Group by month and calculate mean score and count
    monthly_stats = plot_df.groupby('year_month').agg(
        avg_score=(rating_column, 'mean'),
        count=(rating_column, 'count')
    ).reset_index()
    
    # Convert period to datetime for plotting
    monthly_stats['date'] = monthly_stats['year_month'].dt.to_timestamp()
    
    # Sort by date to ensure proper chronological order
    monthly_stats = monthly_stats.sort_values('date')
    
    # Create figure with two subplots sharing the same x-axis
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    
    # Plot average score as a line with markers
    line = ax1.plot(monthly_stats['date'], monthly_stats['avg_score'], 'b-o', linewidth=2, markersize=8)
    ax1.set_ylabel('Average Rating', color='blue', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.set_ylim(1, 5)  # Review scores are typically 1-5
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Plot count as bars
    bars = ax2.bar(monthly_stats['date'], monthly_stats['count'], alpha=0.3, color='gray', width=20)
    ax2.set_ylabel('Number of Reviews', color='gray', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='gray')
    
    # Add count labels above the bars
    for bar in bars:
        height = bar.get_height()
        ax2.annotate(f'{int(height)}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10)
    
    # Format x-axis to show months nicely
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45)
    
    # Set title and adjust layout
    plt.title('Average Review Score by Month', fontsize=14, pad=20)
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    print(f"Review plot saved to {output_path}")
    plt.close()

def main():
    """Command line interface for the Google Maps Review Scraper."""
    parser = argparse.ArgumentParser(description='Scrape Google Maps reviews')
    parser.add_argument('--url', '-u', type=str, help='Google Maps URL to scrape')
    parser.add_argument('--output', '-o', type=str, help='Path to save CSV file')
    parser.add_argument('--max-reviews', '-m', type=int, help='Maximum number of reviews to scrape')
    parser.add_argument('--wait-time', '-w', type=int, default=10, help='Time to wait between scrolls in seconds (default: 10)')
    parser.add_argument('--plot', '-p', action='store_true', help='Generate a plot of average reviews by month')
    parser.add_argument('--plot-output', type=str, default='reviews_by_month.png', help='Path to save the plot image (default: reviews_by_month.png)')
    parser.add_argument('--load-reviews', '-l', type=str, help='Load previously scraped reviews from CSV file instead of scraping')
    args = parser.parse_args()
    
    # Check if loading from existing CSV file
    if args.load_reviews:
        print(f"Loading reviews from {args.load_reviews}...")
        try:
            reviews_df = pd.read_csv(args.load_reviews)
            
            # Convert exact_time column to datetime if it exists
            if 'exact_time' in reviews_df.columns:
                reviews_df['exact_time'] = pd.to_datetime(reviews_df['exact_time'])
                
            print(f"Loaded {len(reviews_df)} reviews from {args.load_reviews}")
        except Exception as e:
            print(f"Error loading reviews from CSV: {e}")
            return
    else:
        # Make sure URL is provided if not loading from CSV
        if not args.url:
            print("Error: Either --url or --load-reviews must be specified")
            return
            
        # Scrape reviews
        reviews_df = scrape_reviews(args.url, max_reviews=args.max_reviews, wait_time=args.wait_time)
    
    if not reviews_df.empty:
        # Print the first 5 reviews
        print("\n===== First 5 Reviews =====")
        print(reviews_df.head())
        print("==========================\n")
        
        # Save to CSV if requested and not already loading from CSV
        if args.output and not args.load_reviews:
            reviews_df.to_csv(args.output, index=False)
            print(f"Reviews saved to {args.output}")
            
        print(f"Total reviews: {len(reviews_df)}")
        if args.max_reviews and not args.load_reviews and len(reviews_df) < args.max_reviews:
            print(f"Note: Requested {args.max_reviews} reviews but could only find {len(reviews_df)}")

        # Generate plot if requested
        if args.plot:
            print("Generating monthly review plot...")
            plot_reviews_by_month(reviews_df, output_path=args.plot_output)
    else:
        print("No reviews were found.")

if __name__ == "__main__":
    main() 