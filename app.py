from flask import Flask, jsonify, request, current_app
import requests, sys, json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, UnexpectedAlertPresentException, \
    ElementClickInterceptedException, NoAlertPresentException, ElementNotInteractableException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

application = Flask(__name__)
with application.app_context():
        
    @application.route("/data", methods=["POST"])
    def crawl():    
        request_data = json.loads(request.get_data(), encoding='utf-8')
        title = request_data['title']
        theater = request_data['theater'] 
        best_price = 0
        
        response ={ "status" : "200", "result" : { "message" : "", "best_price": best_price}}

        try :
            # 크롬 드라이버 로드
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("detach", True)
            chrome_options.add_argument('window-size=800,600')
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get('https://ticket.interpark.com/TPGoodsList.asp?Ca=Dra&Sort=4')
        except WebDriverException :
            message = "크롬드라이버를 찾을 수 없습니다."
            response ={ "status" : "500", "result" : { "message" : message, "best_price": best_price}}
            driver.close()
            return jsonify(response)
        
        try :
            # 리스트에서 해당 타이틀 검색
            element = driver.find_element(By.CLASS_NAME, 'bjwEPif5TbJS3HdYBgz5')
            search = element.find_element(By.TAG_NAME, 'input')
            search.send_keys(title)
            search.send_keys(Keys.RETURN)
            time.sleep(2)
        except NoSuchElementException:
            message = "no such element exception!  - Can not find search input"
            response ={ "status" : "300", "result" : { "message" : message, "best_price": best_price}}
            driver.close()
            return jsonify(response)
        
        try :
            # 검색 페이지에서 첫번째 요소 클릭
            driver.find_element(By.XPATH, '//*[@id="__next"]/div/main/div/div/div[1]/div[2]/a[1]').click()
            time.sleep(3)
        except NoSuchElementException:
            message = "no such element exception!  - Can not find the play"
            response ={ "status" : "300", "result" : { "message" : message, "best_price": best_price}}
            driver.close()
            return jsonify(response)


        # 팝업이 있으면 닫음


        # 상세페이지에서 전체가격보기 모든 가격 선택
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'infoBtn'))
            )
            driver.find_element(By.CLASS_NAME, 'infoBtn.is-accent').click()

            price_list = []

            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            price_categories = soup.select('td.name + td')
            for category in price_categories:
                price_list.append(category.text)               
            num_price = []
            
            for price in price_list:
                price = price.replace('원', '')
                price = price.replace(',', '')
                num_price.append(int(price))

            best_price = num_price[0]
            for price in num_price:
                if price < best_price:
                    best_price = price
            message = "success!"
            response ={ "status" : "200", "result" : { "message" : message, "best_price": best_price}}
        except NoSuchElementException:
            message = "no such element exception!  - Can not collect prices"
            response ={ "status" : "300", "result" : { "message" : message, "best_price": best_price}}
        except UnexpectedAlertPresentException:
            message = "UnexpectedAlertPresentException!  - Can not collect prices"
            response ={ "status" : "301", "result" : { "message" : message, "best_price": best_price}}
        except ElementClickInterceptedException:
            message = "popup error - Can not collect prices"
            response ={ "status" : "302", "result" : { "message" : message, "best_price": best_price}}
        finally:
            driver.close()
            return jsonify(response)

    if __name__ == "__main__":
        application.run(host='0.0.0.0', port=5000, debug=True)