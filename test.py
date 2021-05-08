import os
import time
from configparser import ConfigParser
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException


# read config file
config = ConfigParser()
config.read('utils/config.ini')


# initialize Safari webdriver
"""
driver = webdriver.Safari()
driver.implicitly_wait(10)
driver.maximize_window()
"""

# initialize Chrome webdriver (for Mac)
driver_path = config.get('chromedriver', 'path')
executable_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), driver_path)
driver = webdriver.Chrome(executable_path = executable_path)
driver.implicitly_wait(10)
driver.maximize_window()


# load main collection page
def open_main_page():
    url = config.get('application', 'main.url')
    driver.get(url)
    # driver.find_element_by_css_selector("title")
    time.sleep(2)
    assert driver.current_url == url, "Test 1: Failed to load main page"


# load add image page
def open_add_image():
    add_image_url = config.get('application', 'add.url')
    add_button = driver.find_element_by_css_selector(".add-image a")
    add_button.click()
    time.sleep(2)
    assert driver.current_url == add_image_url, "Test 2: Failed to redirect to add new image page"


# load image info page
def open_info_page():
    info_url = config.get('application', 'info.url')
    image_name = config.get('image', 'image.name')
    image = driver.find_element_by_xpath("//div[@class='img-info']/a[text()='%s']" % image_name)
    image.click()
    time.sleep(2)
    assert driver.current_url.find(info_url) != -1, "Test 3: Failed to redirect to image info page"


# check flash message for correct output
# method for add image page
def check_message(message, duration):
    submit = driver.find_element_by_css_selector("input[type='submit']")
    submit.click()
    time.sleep(duration)
    error = driver.find_element_by_css_selector("p")
    assert error.text.strip() == message, "Test 2: Failed to produce correct error message. Correct message should be %s" % message


# enter image info into name and image url fields 
# method for add image page
def enter_image_info(image_name, image_url):
    name = driver.find_element_by_css_selector("input[name='name']")
    url = driver.find_element_by_css_selector("input[name='image_url']")
    name.send_keys(image_name)
    url.send_keys(image_url)

    assert name.get_attribute("value") == image_name, "Test 2: Failed to enter image name"
    assert url.get_attribute("value") == image_url, "Test 2: Failed to enter image url"


# check different responses for add image page
def check_add_image():
    # get image information
    image_name = config.get('image', 'image.name')
    image_url = config.get('image', 'image.url')
    local_url = config.get('image', 'local.url')
    pdf_url = config.get('image', 'pdf.url')

    # check error message for no input
    message = config.get('upload', 'incomplete.message')
    enter_image_info('', '')
    check_message(message, 1)
    
    # check error message for missing 1 input
    enter_image_info(image_name, '')
    check_message(message, 1)

    enter_image_info('', image_url)
    check_message(message, 1)

    # check error message for image with local path
    enter_image_info(image_name, local_url)
    message = config.get('upload', 'local.message')
    check_message(message, 1)

    # check error message for image with wrong extension
    enter_image_info(image_name, pdf_url)
    message = config.get('upload', 'extension.message')
    check_message(message, 1)

    # check confirm message and image photo for succesful addition of image
    enter_image_info(image_name, image_url)
    message = config.get('upload', 'complete.message')
    check_message(message, 10)

    image = driver.find_element_by_css_selector("img")
    assert image.get_attribute('src') == image_url, "Test 2: Failed to load new image correctly"

    # return to main page and check that new image is added
    main_url = config.get('application', 'main.url')
    collection = driver.find_element_by_css_selector(".add-image a")
    collection.click()
    time.sleep(2)
    assert driver.current_url == main_url, "Test 2: Failed to redirect from add image page back to main collection page"
    assert check_image_exists() == True


# check if image exists in main page collection
def check_image_exists():
    image_name = config.get('image', 'image.name')
    image_url = config.get('image', 'image.url')
    
    try:
        name = driver.find_element_by_xpath("//div[@class='img-info']/a[text()='%s']" % image_name)
        image = driver.find_element_by_xpath("//div[@class='img-info']/a[text()='%s']/parent::div/parent::div/img" % image_name)
    except NoSuchElementException:
        return False

    assert image.get_attribute('src') == image_url, "Test 2/4: Failed to load new image correctly"
    return True


# check image name and url on image info page
def check_image_info():
    image_name = config.get('image', 'image.name')
    image_url = config.get('image', 'image.url')
    name = driver.find_element_by_css_selector("body > div:nth-child(2) > h2:nth-child(2)")
    image = driver.find_element_by_css_selector("img")
    assert image.get_attribute('src') == image_url, "Test 3: Failed to load image correctly"

    # return to main page
    main_url = config.get('application', 'main.url')
    collection = driver.find_element_by_css_selector(".add-image a")
    collection.click()
    assert driver.current_url == main_url, "Test 3: Failed to redirect from add image page back to main collection page"


# enter image characteristic/label into search
# method for main page
def enter_search(label):
    search_bar = driver.find_element_by_css_selector("input[name='search']")
    search_button = driver.find_element_by_css_selector("input[type='submit']")
    search_bar.send_keys(label)
    assert search_bar.get_attribute("value") == label, "Test 4: Failed to enter search"

    search_button.click()
    time.sleep(1)


# check search results for image labels
# method for main page
def search_by_labels():
    # positive tests
    label1 = config.get('image', 'label1')
    label2 = config.get('image', 'label2')
    label3 = config.get('image', 'label3')

    # negative tests
    wrong_label1 = config.get('image', 'wrong.label1')
    wrong_label2 = config.get('image', 'wrong.label2')

    enter_search(label1)
    assert check_image_exists() == True, "Test 4: Failed to get correct search result for positive test"
    enter_search(wrong_label1)
    assert check_image_exists() == False, "Test 4: Failed to get correct search result for negative test"
    enter_search(label2)
    assert check_image_exists() == True, "Test 4: Failed to get correct search result for positive test"
    enter_search(label3)
    assert check_image_exists() == True, "Test 4: Failed to get correct search result for positive test"
    enter_search(wrong_label2)
    assert check_image_exists() == False, "Test 4: Failed to get correct search result for negative test"


# method call to check main page
def check_main_page():
    open_main_page()
    print("Test 1: Check Main Page - Pass")


# method call to check add image page
def check_add_page():
    open_add_image()
    check_add_image()
    print("Test 2: Check Add Image Page - Pass")


# method call to check image info page
def check_info_page():
    open_info_page()
    check_image_info()
    print("Test 3: Check Image Info Page - Pass")


# method call to check search results of image characteristics
def check_search():
    search_by_labels()
    print("Test 4: Check Search By Image Characteristic - Pass")


if __name__ == '__main__':
    check_main_page()
    check_add_page()
    check_info_page()
    check_search()
    driver.close()
 