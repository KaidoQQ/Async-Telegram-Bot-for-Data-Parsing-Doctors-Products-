import os
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

from parsers.base import BaseParserSelenium

load_dotenv("tokens.env")

TARGET_ITEMS = 30

class ProductParser(BaseParserSelenium):
  def __init__(self):
    super().__init__()
    self.url = os.getenv("URL_product")

  def parser(self,category = None,budget = None,**kwargs):
    print(f"✳️ [Amazon] Starts search: {category} (Budget: {budget})")
    self._setup_driver()
    wait = WebDriverWait(self.driver, 7)
    parsed_data = []

    try:
      self.driver.get(self.url)
      time.sleep(random.uniform(3, 5))

      try:
        cook = wait.until(EC.presence_of_element_located((By.ID, "sp-cc-accept")))
        cook.click()

        time.sleep(1.5)


        try:
          container = self.driver.find_element(By.ID, "twotabsearchtextbox")
          container.click()
          container.clear()
          container.send_keys(category)
          time.sleep(0.5)

          container.send_keys(Keys.ENTER)

          try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//span[@data-component-type='s-search-results']")))
            new_budget = int(budget)


            try:
              min_filter = self.driver.find_element(By.ID, "p_36/dynamic-picker-0")
              avg_1_filter = self.driver.find_element(By.ID, "p_36/dynamic-picker-1")
              avg_2_filter = self.driver.find_element(By.ID, "p_36/dynamic-picker-2")
              max_filter = self.driver.find_element(By.ID, "p_36/dynamic-picker-3")



              min_text = min_filter.find_element(By.CSS_SELECTOR, "span.a-size-base").text
              avg_1_text = avg_1_filter.find_element(By.CSS_SELECTOR, "span.a-size-base").text
              avg_2_text = avg_2_filter.find_element(By.CSS_SELECTOR, "span.a-size-base").text
              max_text = max_filter.find_element(By.CSS_SELECTOR, "span.a-size-base").text


              min_price = int(min_text.replace("Do", "").replace("zł", "").replace("\u00A0", "").replace(" ", "").strip())

              if " - " in avg_1_text or " - " in avg_2_text:
                if " - " in avg_1_text:
                  temp = avg_1_text.split(" - ")[1].replace("zł", "").replace("\u00A0", "").replace(" ", "").strip()
                  avg_1_price = int(temp)
                
                if " - " in avg_2_text:
                  temp = avg_2_text.split(" - ")[1].replace("zł", "").replace("\u00A0", "").replace(" ", "").strip()
                  avg_2_price = int(temp)


              max_price = int(max_text.replace("Powyżej", "").replace("zł", "").replace("\u00A0", "").replace(" ", "").strip())

              print(f"📊 Price ranges: {min_price} | {avg_1_text} | {avg_2_text} | {max_text}")

              target_element = None

              if new_budget <= min_price:
                target_element = min_filter.find_element(By.TAG_NAME, "a")
                print(f"✅ Selected: Do {min_price} zł")
                
              elif new_budget <= avg_1_price:
                target_element = avg_1_filter.find_element(By.TAG_NAME, "a")
                print(f"✅ Selected: {min_price} - {avg_1_price} zł")
              
              elif new_budget <= avg_2_price:
                target_element = avg_2_filter.find_element(By.TAG_NAME, "a")
                print(f"✅ Selected: {avg_1_price} - {avg_2_price} zł")
          
              else:
                target_element = max_filter.find_element(By.TAG_NAME, "a")
                print(f"✅ Selected: Powyżej {max_price} zł")

              if target_element:
                self.driver.execute_script("arguments[0].click();", target_element) 


              time.sleep(random.uniform(1.5, 2.5))
                

            except Exception as e:
              print(f"❌ [ERROR] Cant find a button with  prices {e}")
            while len(parsed_data) < TARGET_ITEMS:
              try:
                menu = self.driver.find_elements(By.XPATH, "//div[@data-component-type='s-search-result']")

                if menu:

                  print(f"✅ MENU was found, total items: {len(menu)}")

                  for product in menu[:100]:

                    if len(parsed_data) >= TARGET_ITEMS:
                      break

                    try:

                      print(f"✅ Item was found{product.text[:30]}")
                      name = None
                      price_clear = None
                      review = None
                      url = None
                      start_url = "https://www.amazon.pl"

                      try:
                        name_element = product.find_element(By.CSS_SELECTOR, "h2 span")
                        name = name_element.text
                        print(f"✅ Name: {name}")

                      except Exception as e:
                        print(f"❌ [ERROR] Problem with name: {e}")

                      try:
                        price_text_el = product.find_element(By.CLASS_NAME, "a-price")

                        price_text = price_text_el.text

                        price_clean = (price_text
                        .replace("\n", ".")      # 34\n99 → 34.99
                        .replace(",", ".")        
                        .replace("zł", "")
                        .replace("\u00A0", "")
                        .replace(" ", "")
                        .strip())

                        price_clear = float(price_clean)
                        print(f"✅  Price:{price_clear}")

                      except Exception as e:
                        print(f"❌  [ERROR] Problem with price: {e}")

                      try:
                        review_block = product.find_element(By.CSS_SELECTOR, "[data-cy='reviews-block']")
                        review_rait = review_block.find_element(By.CSS_SELECTOR, "span.a-size-small.a-color-base")

                        review_text = review_rait.text

                        review_clear = review_text.replace(",",".")
                        review = float(review_clear)
                        print(f"✅  Review:{review}")

                      except Exception as e:
                        print(f"❌  [ERROR] Problem with review: {e}")

                      try:
                        link_element = product.find_element(By.CSS_SELECTOR, "a.a-link-normal")
                        product_url = link_element.get_attribute("href")

                        if product_url.startswith("/"):
                          url = start_url + product_url
                        else:
                          url = product_url

                        print(f"✅  URL:{url}")

                      except Exception as e:
                        print(f"❌ [ERROR] Problem with URL: {e}")

                      if price_clear and price_clear <= new_budget and price_clear >= (new_budget // 1.50):
                        parsed_doc = {
                        'name' : name,
                        'price' : price_clear,
                        'review' : review,
                        'link' : url
                      }
                        if not any(d['link'] == url for d in parsed_data):
                          parsed_data.append(parsed_doc)
                          print(f"✅ Product: {name[:40]} | Price: {price_clear}")
                          print(f"✅ Found ({len(parsed_data)}/{TARGET_ITEMS}): {name[:30]}...")
                          print()
                      else:
                        print(f"⚠️  Problem with price: {price_clear} > {new_budget} or {price_clear} < {(new_budget) // 1.5}")

                    except Exception:
                      continue

                else:
                  print("❌ [ERROR] Cant find a Menu card!")

              except Exception as e:
                print(f"❌ [ERROR] No results found or XPath error: {e}")
              
              if len(parsed_data) >= TARGET_ITEMS:
                print("✅ Target reached!")
                break 

              try:
                next_btn = self.driver.find_element(By.CSS_SELECTOR, "a.s-pagination-next")

                if "s-pagination-disabled" in next_btn.get_attribute("class"):
                  print("⛔ Last page reached.")
                  break

                self.driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(random.uniform(3, 5))

              except Exception as e:
                print("⛔ No 'Next' button found (end of results).")
                break

          except Exception as e:
            self.driver.save_screenshot("error_screenshot.png")
            print(f"❌ [ERROR] No menu was found {e}")

        except Exception as e:
          print("❌ [ERROR] No search-box was found")

      except Exception as e:
        print(f"⭕ [GLOBAL ERROR] Longer than 7 sec or ERROR_NAME: {e}")

      return parsed_data
    except Exception as e:
      print(f"⭕ [Amazon] Error: {e}")
    finally:
      self.close_driver()

