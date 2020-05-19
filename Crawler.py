import selenium.webdriver
import time
import re
from selenium.webdriver.common.keys import Keys
import mysql.connector
from Plan import Attraction

# this class reponse to find the duration time of attraction
# the default duration time is 2 hours
# we find the duration on google and tripadvisor
# we using regular expression to locate the key words
# if cannot find on them, apply the default value
class Crawler():
    def __init__(self):
        self.duration = ""
    
    # to search the duration time by tripadvisor
    def _tripadvisorRecommandDuration(self):
        try:
            tripDuration = ""
            self._driver.get("https://www.google.com.hk/")
            time.sleep(1)
            searchBar = self._driver.find_element_by_name('q')
            searchBar.send_keys("tripadvisor "+self.attraction)
            searchBar.send_keys(Keys.ENTER)
            time.sleep(1)

            for a in self._driver.find_elements_by_css_selector(".r a"):
                link = a.get_attribute("href")
                if link.find('tripadvisor'):
                    self._driver.execute_script('''window.open("")''')
                    self._driver.switch_to.window(
                        self._driver.window_handles[-1])
                    self._driver.get(link)
                    time.sleep(2)
                    div = self._driver.find_elements_by_class_name(
                        "attractions-attraction-detail-about-card-AboutSection__sectionWrapper--3PMQg")
                    for row in div:
                        if row.text != 'Improve This Listing':
                            timeRange = re.search(
                                r'([0-9]-[0-9])', row.text).string
                            if timeRange:
                                try:
                                    tripDuration = (
                                        int(timeRange[7])+int(timeRange[9]))/2
                                    break
                                except:
                                    tripDuration = (
                                        int(timeRange[-7])+int(timeRange[-9]))/2
                    break
        finally:
            # self._driver.execute_script('''tab.close()''')
            self._driver.switch_to.window(
                self._driver.window_handles[-1])
            self._driver.close()
            return str(tripDuration)

    # to search the duration time by google
    def _googleRecommandDuration(self):
        try:
            googleDuration = ""
            self._driver.get("https://www.google.com.hk/")
            time.sleep(1)
            searchBar = self._driver.find_element_by_name('q')
            searchBar.send_keys(self.attraction)
            searchBar.send_keys(Keys.ENTER)
            time.sleep(1)
            googleDuration = self._driver.find_element_by_css_selector(
                '.UYKlhc b').text
            googleDuration = googleDuration.split()[0]
        finally:
            return str(googleDuration)

    # if cannot locate on google, then find on tripadvisor
    # if neither, apply the default duration time
    def crawlDruation(self, attraction):
        self._driver = selenium.webdriver.Chrome()
        self.attraction = attraction
        duration = self._googleRecommandDuration()
        if duration is not "":
            self.duration = duration
        elif duration is "":
            duration = self._tripadvisorRecommandDuration()
            self.duration = duration

        if duration is "":
            self.duration = "2"

        self._driver.switch_to.window(
                self._driver.window_handles[0])
        self._driver.close()

        if re.match(r'[0-9]-[0-9]', self.duration):
            splited = self.duration.split('-')
            duration = (int(splited[0])+int(splited[1]))*1800   # 3600/2
            if duration > 3600*8:
                duration = 2*3600
            return duration
        else:
            # return the duration of seconds
            if float(self.duration) > 8 and float(self.duration) <= 120:
                self.duration = str(float(self.duration)/60)
            elif float(self.duration) > 120:
                self.duration = '2'

        return float(self.duration)*3600

# to update all duration time of attraction once
# connection = mysql.connector.connect(
#     host="hotrip.cftxv1tfg8he.us-east-1.rds.amazonaws.com",
#     username="chilladmin",
#     password="ChillPa$$w0rd",
#     database="hochilltrip",
#     buffered=True)
# cursor = connection.cursor()
# query = 'select * from attraction'
# cursor.execute(query)
# attractions = cursor.fetchall()
# crawler = Crawler()
# for attraction in attractions:
#     attraction_ = Attraction(attraction[0], attraction[1], attraction[2], attraction[3], attraction[4], attraction[5], attraction[6], attraction[7], attraction[8], attraction[9], attraction[10], attraction[11], "")
#     if not attraction_.duration:
#         duration = crawler.crawlDruation(attraction_.name)
#         attraction_.setDuration(duration)
#         query = 'update attraction set duration = %f where attractionID = %d' % (
#             attraction_.duration, attraction_.attractionID
#         )
#         print(query, "name: ",attraction_.name)
#         cursor.execute(query)
#         connection.commit()
# cursor.close()
# connection.close()