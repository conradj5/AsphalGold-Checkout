import atexit
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def on_exit(driver):
    try:
        driver.close()
    except:
        pass


class CheckoutDriver:
    opts = Options()
    opts.add_argument('--headless')

    def __init__(self, queue):
        # self.driver = webdriver.Chrome(chrome_options=self.opts)
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 5)
        self.driver.set_window_size(250, 800)

        self.queue = queue

        # initialize logger #
        self.log = logging.getLogger("Checkout Driver")
        log_format = logging.Formatter("[%(asctime)s.%(msecs)03d] Checkout Driver: %(message)s", "%H:%M:%S")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        self.log.addHandler(console_handler)
        self.log.setLevel(logging.DEBUG)
        # make sure driver closes on exit
        atexit.register(on_exit, [self.driver])

    def __click(self, locator, by=By.ID):
        elem = self.wait.until(EC.element_to_be_clickable((by, locator)))
        self.driver.execute_script("arguments[0].click();", elem)

    def __set_val(self, locator, val, by=By.ID):
        elem = self.wait.until(EC.presence_of_element_located((by, locator)))
        self.driver.execute_script("arguments[0].value ='" + val + "';", elem)

    def login(self, email, password):
        self.log.info("Signing into PayPal")

        self.driver.get("https://www.paypal.com/signin")
        # t email value
        self.__set_val('email', email)
        if self.driver.find_elements_by_id('btnNext'):
            # click next
            self.__click('btnNext')
        # wait, get, set password element
        self.__set_val('password', password)
        # click sign in
        self.__click('btnLogin')
        try:
            self.wait.until(lambda web_driver: web_driver.execute_script('return document.readyState;') == 'complete')
        except TimeoutError:
            self.log.info("Please check login window for " + email)
        finally:
            if 'paypal.com/myaccount/home' not in self.driver.current_url:
                self.driver.get('https://www.paypal.com/myaccount/home')
        self.wait.until(lambda web_driver: web_driver.execute_script('return document.readyState;') == 'complete')

        self.log.info("Logged into PayPal")
        self.driver.get('https://asphaltgold.de/en/imprint/')

    def checkout(self):
        self.log.info("Starting checkout")

        while 'www.paypal.com' not in self.driver.current_url:
            self.driver.get('https://asphaltgold.de/en/paypal/express/start/button/1/')


        # self.__click('button')

        # self.__click('confirmButtonTop')
