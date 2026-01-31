import asyncio
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

from parsers.base import BaseParserSelenium

load_dotenv("tokens.env")

URL_1 = os.getenv("URL_1")
URL_2 = os.getenv("URL_2")

class LKZ(BaseParserSelenium):
  def __init__(self):
    super().__init__()
    self.url = URL_1

  def parser(self, doctor_name = None, doctor_name_spec = None, date = None, city = None):
    print(f"✳️ [LekarzeBezKolejki] Starts for {city}...")
    self._setup_driver()
    wait = WebDriverWait(self.driver, 7)
    parsed_data = []

    try:
      self.driver.get(URL_1)

      try:
        cook = self.driver.find_element(By.CSS_SELECTOR, ".cookies-buttons #btnCookiesAll")
        cook.click()
        time.sleep(1)
        
        container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"[class='pos:r m-b:xl']")))

        town_ent = container.find_element(By.CSS_SELECTOR, "#lokalizacja input")
        town_ent.clear()
        town_ent.send_keys(city)
        time.sleep(0.5)
        town_ent.send_keys(Keys.ENTER)

        if doctor_name_spec != None:
          doctor_ent = container.find_element(By.CSS_SELECTOR, "#specjalizacja input")
          doctor_ent.clear()
          doctor_ent.send_keys(doctor_name_spec)
          time.sleep(0.5)

          doctor_ent.send_keys(Keys.ENTER)

          try:
            first_doctor = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"[id^='wynik_lekarz_']")))

            if first_doctor:
              doctors = self.driver.find_elements(By.CSS_SELECTOR, "[id^='wynik_lekarz_']")

              for doctor in doctors:
                if doctor:
                  name_el = doctor.find_element(By.CSS_SELECTOR, ".thd-name a")
                  ph_number = "No phone number"
                  new_date = "Unknown"
                  try:
                    phone_btn = doctor.find_element(By.XPATH, ".//button[contains(@onclick, 'pokazTelefon')]")
                    self.driver.execute_script("arguments[0].click();", phone_btn)

                    time.sleep(0.5)
                    phone_link = doctor.find_element(By.XPATH, ".//a[contains(@href, 'tel:')]")

                    ph_number = phone_link.get_attribute("textContent").strip()

                    if not ph_number:
                      href_val = phone_link.get_attribute("href")
                      if href_val:
                        ph_number = href_val.replace("tel:", "").strip()

                    print("✅ Phone number of doctor was added")
                    print(ph_number)
                  except:
                    print("❌ No phone number was found")

                  name = name_el.text
                  n_date = date.lower()
                  n_date = n_date.replace(" ","")

                  if n_date == "nearest":
                    try:
                      near_date_el = doctor.find_element(By.CSS_SELECTOR, ".tb-data")
                      near_date = near_date_el.text
                      new_date = self._convert_polish_date(near_date)
                    except:
                      try:
                        near_date_el = doctor.find_element(By.CSS_SELECTOR, ".tb-none")
                        near_date = near_date_el.text
                        new_date = "This doctor didnt indicate an upcoming date"
                      except:
                        new_date = "Date info not found"

                  try:
                    street_el = doctor.find_element(By.CSS_SELECTOR, "span.device-n")
                    street = street_el.text

                    url_link = doctor.find_element(By.CSS_SELECTOR, "a[id^=linkNazwaZasobu_]")
                    url = url_link.get_attribute("href")
                  except Exception as e:
                    print(f"❌ [ERROR] Something wrong {e}")


                  parsed_doc = {
                    'name' : name,
                    'ph_number' : ph_number,
                    'near_date' : new_date,
                    'street': street,
                    'link': url
                  }

                  parsed_data.append(parsed_doc)
                  print(f"✅  Doctor: {name} | Tel: {ph_number} | Date: {new_date} | Street: {street} | Link: {url}")
                  print()
                else:
                  print("❌ [ERROR] cant find a doctor card!")
          except Exception as e:
            print(f"❌ [ERROR] No doctors was found {e}")

        if doctor_name != None:
          doctor_ent = container.find_element(By.CSS_SELECTOR, "#specjalizacja input")
          doctor_ent.clear()
          doctor_ent.send_keys(doctor_name)
          time.sleep(1)

          doctor_ent.send_keys(Keys.ENTER)

          time.sleep(3)

          try:
            info = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".page-content, .profile-header")))

            if info:
              street = "Address not found"
              try:
                street_el = self.driver.find_element(By.CSS_SELECTOR, "span[class='w-s:n']")
                street = street_el.text.strip()
              except:
                print(f"⚠️ Street element not found")

              ph_number = "No phone number"
              try:
                phone_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href^='tel:']")
                found_phone = False
                for link in phone_links:
                  href_val = link.get_attribute("href")
                  if href_val and "tel:" in href_val:
                    clean_phone = href_val.replace("tel:", "").strip()
                    if len(clean_phone) > 5: 
                      ph_number = clean_phone
                      found_phone = True
                      print(f"✅ Phone number found directly from hidden link: {ph_number}")
                      break
                
                if not found_phone:
                  print("⚠️ Hidden link empty, trying to click button...")
                  phone_btn = self.driver.find_element(By.CSS_SELECTOR, "button[onclick*='pokazTelefon']")
                  self.driver.execute_script("arguments[0].click();", phone_btn)
                  time.sleep(1)
                  
                  phone_link = self.driver.find_element(By.CSS_SELECTOR, "a[href^='tel:']")
                  ph_number = phone_link.get_attribute("textContent").strip()
                  print(f"✅ Phone number found after click: {ph_number}")
              except:
                print("❌ [ERROR] No phone number was found")
              
              name = doctor_name

              parsed_dates = []

              try:
                calendar_container = wait.until(EC.presence_of_element_located((By.ID, "kolumnaTerminyPRV")))
                if calendar_container:
                  days_cards = calendar_container.find_elements(By.CSS_SELECTOR, "div.agenda-day")
                  for card in days_cards:
                    try:
                      day=card.find_element(By.CSS_SELECTOR, "p.agenda-data") 
                      new_date = day.text
                      clean_date = self._convert_polish_date(new_date)
                      parsed_dates.append(clean_date)
                    except:
                      continue
                else:
                  print("❌ [ERROR] Cant find all dates!")
                
                if not parsed_dates:
                  parsed_dates.append("No available dates visible")

              except Exception as e:
                print(f"❌ [ERROR] {e}")

              full_url = self.driver.current_url

              parsed_doc = {
                'name' : name,
                'ph_number' : ph_number,
                'near_date' : ", ".join(parsed_dates[:3]),
                'street' : street,
                'link' : full_url
              }
              parsed_data.append(parsed_doc)
              print(f"✅  Doctor: {name} | Tel: {ph_number} | Dates: {len(parsed_dates)} | Street: {street} | Link: {full_url}")
              print()
            else:
              print(f"❌ [ERROR] Cant load the page of doctor [{doctor_name}]")
          except Exception as e:
            self.driver.save_screenshot("error_screenshot.png")
            print(f"❌ [ERROR] No doctor was found {e}")

      except Exception as e:
        print(f"⭕ [GLOBAL ERROR] Longer than 7 sec or ERROR_NAME: {e}")
      
      if len(parsed_data) > 0:
        return parsed_data
      else:
        return []
    except Exception as e:
      print(f"⭕ [LekarzeBezKolejki] Error: {e}")
    finally:
      self.close_driver()
  
  @staticmethod
  def _convert_polish_date(date_str):
    months_mapping_1 = {
    "stycznia": "01",
    "lutego": "02",
    "marca": "03",
    "kwietnia": "04",
    "maja": "05",
    "czerwca": "06",
    "lipca": "07",
    "sierpnia": "08",
    "września": "09",
    "października": "10",
    "listopada": "11",
    "grudnia": "12"
  }

    months_mapping_2 = {
      "sty": "01",
      "lut": "02",
      "mar": "03",
      "kwi": "04",
      "maj": "05",
      "cze": "06",
      "lip": "07",
      "sie": "08",
      "wrz": "09",
      "paź": "10",
      "lis": "11",
      "gru": "12"
    }
    try:
      clean_date = date_str.strip().lower()
      
      parts = clean_date.split()
      
      if len(parts) != 3 and len(parts) != 2:
        return date_str 

      if len(parts) == 3:   
        day, month_name, year = parts
        
        month_number = months_mapping_1.get(month_name)
        
        if not month_number:
          return date_str 
            
        day = day.zfill(2)
        
        return f"{year}-{month_number}-{day}"
      else:
        day, month_name = parts
        month_number = months_mapping_2.get(month_name)

        if not month_number:
          return date_str
        
        day = day.zfill(2)

        return f"{month_number}-{day}"
      
    except Exception as e:
      print(f"❌ [ERROR] Conversion: {e}")
      return date_str
    
class ZL(BaseParserSelenium):
  def __init__(self):
    super().__init__()
    self.url = URL_2

  def parser(self, doctor_name = None, doctor_name_spec = None, date = None, city = None):
    print(f"✳️ [ZnanyLekarz] Starts for {city}...")
    self._setup_driver()
    wait = WebDriverWait(self.driver, 7)
    parsed_data = []

    try:
      self.driver.get(URL_2)

      try:
        cook = wait.until(EC.presence_of_element_located((By.ID, "onetrust-button-group")))

        if cook:
          btn = cook.find_element(By.CLASS_NAME, "banner-actions-container")
          btn.click()
          print("✅🍪 Cookie was successful accepted")
          time.sleep(1)
        else:
          print("🍪 No cookie button was found")
        
        container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#search")))

        town_ent = container.find_element(By.CSS_SELECTOR, ".city-col input")
        town_ent.clear()
        town_ent.send_keys(city)
        time.sleep(0.5)
        town_ent.send_keys(Keys.ENTER)

        if doctor_name_spec != None:
          doctor_ent = container.find_element(By.CSS_SELECTOR, ".specialists-col input")
          doctor_ent.clear()
          doctor_ent.send_keys(doctor_name_spec)
          time.sleep(0.5)
          doctor_ent.send_keys(Keys.ENTER)
          time.sleep(0.5)

          final_btn = container.find_element(By.CSS_SELECTOR, ".button-col button")
          self.driver.execute_script("arguments[0].click();", final_btn)
          time.sleep(1.5)

          try:
            search_results = wait.until(EC.presence_of_element_located((By.ID, "search-content")))

            if search_results:
              doctors = self.driver.find_elements(By.CSS_SELECTOR, "li.has-cal-active")

              if doctors:
                print(f"✅ Doctors {len(doctors)} was found")

          except Exception  as e:
            print(f"❌ [ERROR] No doctors was found {e}")

      except Exception as e:
        print(f"⭕ [GLOBAL ERROR] Longer than 7 sec or ERROR_NAME: {e}")

      if len(parsed_data) > 0:
        return parsed_data
      else:
        return []
    except Exception as e:
      print(f"⭕ [ZnanyLekarz] Error: {e}") 
    finally:
      self.close_driver()

class DoctorSearchFunc:
  def __init__(self):
    self.parsers = [
      LKZ(),
      ZL()
    ]

  async def search(self,**kwargs):
    tasks = []
    print(f"🏥 Starting search with params: {kwargs}")

    for parser in self.parsers:
      tasks.append(asyncio.to_thread(parser.parser, **kwargs))
        
    results_lists = await asyncio.gather(*tasks)
    
    final_results = [
    item 
    for sublist in results_lists 
    if sublist 
    for item in sublist
  ]
    
    print(f"✅ Total doctors found: {len(final_results)}")
    return final_results
