# Image Repository

## About
A python project to build an image repository with the following features:
1. Search from characteristics of the images
    * The project uses Google AI Vision API to generate a list of labels (characteristics) for each image provided
    * e.g. a photo of fried chicken might have labels such as 'chicken', 'food', 'fast food', 'frying', etc.
2. Add a new web image to the collection
    * Due to limitations of the API access, only web images can be used to generate list of labels

Automated tests of the UI are included. The tests include:
1. Tests for main page
2. Tests for add image page
3. Tests for image info page
4. Tests for search functionality of image characteristics (positive and negative)

The project uses Flask for web application and Selenium for automated testing.   

## Build project

In root, run
```
pip install -r requirements.txt
```
    
## Run project

* Run project
    ```
    python3 server.py
    ```
    * Default port for Flask UI is http://127.0.0.1:5000/

* Run UI tests
    ```
    python3 test.py
    ```
    * Ensure the application server is running before running the tests
    * Selenium will automatically open up a browser to run the tests
    * Webdriver configurations for Safari and Chrome (on Mac) are provided
    * To run Chrome on Mac, navigate to the _driver_ folder and run the following command before running the tests (if necessary):
        ```
        xattr -d com.apple.quarantine chromedriver 
        ```

## Screenshot
![UI screenshot](https://github.com/dpannguyen/stonks-analyzer/blob/master/frontend/public/ui.png)