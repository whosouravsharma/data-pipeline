import os
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.common.keys import Keys

import time

# support functions
def is_valid_url(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except:
        return False

driver = webdriver.Chrome()

# redirect to find the resumes
def scrape_links():
    links = []
    url = 'https://dell.wd1.myworkdayjobs.com/en-US/External/?Location_Country=c4f78be1a8f14da0ab49ce1162348a5e&Location_Country=bc33aa3152ec42d4995f4791a106ed09&Location_Country=a30a87ed25634629aa6c3958aa2b91ea'
    driver.get(url)

    wait = WebDriverWait(driver, 1)

    # Get the initial height of the current page
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        updated_html = driver.page_source
        soup = BeautifulSoup(updated_html, 'html.parser')
        
        for link in soup.find_all("a", class_="css-19uc56f"):
            href = link.get("href")
            if href and "en-US" in href:
                full_href = f"https://dell.wd1.myworkdayjobs.com{href}"
                print(full_href)
                links.append(full_href)

        try:
            time.sleep(2)
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="next"]')))
            next_button.click()
        except:
            break
    return links

# Function to obtain all the details of the job taking each link from the list of links.
def scrape_job_descriptions(links):
    job_data = []
    count = 0
    for link in links:
        try:
            count+=1
            print(count)

            response = requests.get(link)
            soup = BeautifulSoup(response.content, 'html.parser')
            # Find the script tag with the type 'application/ld+json'
            script_tag = soup.find('script', {'type': 'application/ld+json'})

            # Parse the JSON content
            data = json.loads(script_tag.string)

            # Extract and print the job title
            datePosted = data.get('datePosted')
            job_title = data.get('title')
            job_type = data.get('employmentType')
            job_description = data.get('description')
            country = data.get('applicantLocationRequirements', {}).get('name')
            city = data.get('jobLocation', {}).get('address', {}).get('addressLocality')

            # Append the data to the list
            job_info = {
                'Date Posted':datePosted,
                'Company Name': 'DELL',
                'Job Title': job_title,
                'Job Type':job_type,
                'Description': job_description,
                'Country':country,
                'City':city,
                'Link':link,
            }
            job_data.append(job_info)
        except Exception as e:
            print(e)
    # Create a pandas DataFrame with the job data
    df = pd.DataFrame(job_data)
    return df


def append_to_excel(new_df, excel_file):
    if os.path.exists(excel_file):
        existing_df = pd.read_excel(excel_file)
        final_df = pd.concat([existing_df, new_df], ignore_index=True)
        print("Updating new file...")
    else:
        final_df = new_df
        print("Creating new file...")
    final_df.to_excel(excel_file, index=False)
    print("File updated successfully!")

if __name__ == "__main__":
    # function-call to store all the links from the homepage of the careers page
    job_links = scrape_links()
    
    # Function to generate the dataframe
    df = scrape_job_descriptions(job_links)

    # Export the DataFrame to an Excel file
    excel_file = '../job_data.xlsx'
    append_to_excel(df, excel_file)