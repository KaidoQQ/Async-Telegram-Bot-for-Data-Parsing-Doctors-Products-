from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class BaseParserSelenium(ABC):
  def __init__(self,headless = True):
    self.headless = headless
    self.driver = None
  
  def _setup_driver(self):
    chrome_option = Options()
    if self.headless:
      chrome_option.add_argument("--headless")
    chrome_option.add_argument("--window-size=1920,1080")
    chrome_option.add_argument("--no-sandbox")
    chrome_option.add_argument("--disable-dev-shm-usage")
    chrome_option.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    chrome_option.add_experimental_option("excludeSwitches",["enable-automation"])
    chrome_option.add_experimental_option('useAutomationExtension',False)

    service = Service(ChromeDriverManager().install())
    self.driver = webdriver.Chrome(service=service,options=chrome_option)

    self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument',{
      'source':'Object.defineProperty(navigator,"webdriver",{get: () => undefined})'
    })

  def close_driver(self):
    if self.driver:
      self.driver.quit()
      print("✴️ [SELENIUM] Driver closed")
  
  @abstractmethod
  def parser(self,**kwargs):
    pass

