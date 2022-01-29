import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import logging
from dotenv import load_dotenv
from plyer import notification
import os

load_dotenv()

logging.basicConfig(filename='blazebot.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

# configurando o chromedriver
logging.info('configurando webdriver')
ser = Service("/usr/lib/chromium-browser/chromedriver")
op = webdriver.ChromeOptions()
op.add_argument("--start-maximized")
driver = webdriver.Chrome(service=ser, options=op)

driver.get("https://blaze.com/pt")
wait = WebDriverWait(driver, 60)

# realizando login
logging.info('realizando login')
loginLink = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[text()='Entrar']"))
    )
loginLink.click()

emailField = wait.until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
emailField.send_keys(os.environ['BLAZE_USERNAME'])

passwordField = wait.until(
        EC.presence_of_element_located((By.NAME, "password"))
    )
passwordField.send_keys(os.environ['BLAZE_PASSWORD'])

signInButton = driver.find_element(By.XPATH, "//button[text()='Entrar']")
time.sleep(2)
signInButton.click()

# entrando na roleta
time.sleep(5)
rouletteLink = wait.until(
    EC.presence_of_element_located((By.XPATH, '//*[@id="leftbar"]/ul/li[@data-testid="left-bar-roulette"]/a'))
)
rouletteLink.click()

# botoes e inputs do jogo da roleta
redButton = None
blackButton = None
amountInput = None
placeBetButton = None

# previous spins
previousSpinsParent = None
previousSpins = None

# bet states
base_bet_amount = float(os.environ['BASE_BET_AMOUNT'])
bet_already_placed = False

def check_spins():
    occurrences = 0
    last_color = ''
    logging.info('checking previous spins...')
    for spin in previousSpins:
        spin_color = spin.get_attribute("class").replace('sm-box ', '')
        if not last_color and spin_color == 'white':
            break
        if not last_color:
            last_color = spin_color
        if spin_color != last_color:
            break
        occurrences = occurrences + 1
    if occurrences >= 3:
        place_bet(last_color, occurrences)

def place_bet(color, occurrences):
    global bet_already_placed
    if bet_already_placed:
        return
    bet_amount = str(base_bet_amount if os.environ['BOOLEAN_DOUBLE_BET_ON_LOSS'] else round(base_bet_amount * (occurrences - 2), 2))
    amountInput.send_keys(bet_amount)
    logging.info(f'setting bet amount {bet_amount}')
    color_choosed = 'red'
    if color == 'red':
        blackButton.click()
        color_choosed = 'black'
        logging.info(f'choosing black color')
    elif color == 'black':
        redButton.click()
        logging.info(f'choosing red color')
    else:
        return
    logging.info(f'placing bet {bet_amount} on {color_choosed} color')
    notification.notify(
        title='Blazerbot',
        message=f'placing bet {bet_amount} on {color_choosed} color',
        timeout=10
    )
    placeBetButton.click()
    bet_already_placed = True

def set_roulette_elements():
    global redButton
    global blackButton
    global amountInput
    global placeBetButton
    global previousSpinsParent
    global previousSpins
    redButton = wait.until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="roulette-controller"]/div[1]/div[1]/div[2]/div/div[1]/div'))
    )
    blackButton = wait.until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="roulette-controller"]/div[1]/div[1]/div[2]/div/div[3]/div'))
    )
    amountInput = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="roulette-controller"]/div[1]/div[1]/div[1]/div/div[1]/input[@class="input-field"]'))
    )
    placeBetButton = wait.until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="roulette-controller"]/div[1]/div[2]/button'))
    )
    previousSpinsParent = driver.find_element(By.XPATH, '//*[@id="roulette-recent"]/div/div[@class="entries main"]')
    previousSpins = previousSpinsParent.find_elements(By.CLASS_NAME, 'sm-box')


while True:
    time.sleep(10)
    try:
        set_roulette_elements()
        if placeBetButton.text == 'Começar o jogo' and not bet_already_placed:
            check_spins()
        else:
            bet_already_placed = False
            logging.info('Waiting for round to end...')
    except Exception as e:
        logging.error(e)


# driver.close()
