import Crawler
import GoogleApi
from Connector import Connector
import Plan
import datetime
import mysql.connector
import operator
import random
import time


api = GoogleApi.API()           # for using google api
crawler = Crawler.Crawler()     # to find the duration time on internet
restList = []                   # to store the restaurants
hotelList = []                  # to store the hotels
attractionList = []             # to store the attractions
mustGoList = []                 # the must-go place that is assigned day
anyDayMustGoList = []           # the must-go place that is no assigned day
endOfday = Plan.Point(0,0,0,0,0,0,0,0)      # to store the end of day point
went = []                       # to store the attraction that is went
blockPoint = []                 # some point has a route to go but no route to out

# to initial the day of the day
def initialDayOfDuration(plan):
    for day in range(1, plan.duration+1):
        query = "select * from plan_content where planID = %d and day = %d" % (plan.planID, day)
        cursor.execute(query)
        planContent = cursor.fetchall()
        routeList = []
    return {'planContent': planContent, 'routeList': routeList}

# to initial day1 of the plan
def initialDay1(day, routeList, plan, *airport):
    startTime = datetime.datetime(plan.startDate.year,plan.startDate.month, plan.startDate.day, 
                                  hour=9, minute=0)
    if len(airport) < 1:
        attraction = api.findAttraction(country)
    else:
        attraction = api.findAttraction(country, 'airport')
    duration = crawler.crawlDruation(attraction['name'])
    point = Plan.Point(day, currentAttractionID()+1, attraction['id'], 
                        attraction['name'], len(routeList)+1, duration, 
                        startTime, 0)
    routeList.append(point)
    startTime = setStartTime(routeList)
    return {'startTime': startTime, 'routeList': routeList}

# to initial the day of plan except day 1
def initialDay(day, endOfday, plan):
    routeList = []
    point = endOfday
    point.setPlaceOrder(len(routeList)+1)
    point.setStartTime(datetime.datetime(plan.startDate.year,plan.startDate.month, 
                       plan.startDate.day+day-1, hour=9, minute=0))
    point.setType(1)
    point.setDay(day)
    routeList.append(point)
    return routeList

# check the attraction infomation is correct
# if some information is lost or worng, correct it
# the googleID is assumed 100% correct
# the original data come from api.findAttraction or api.findNextAttraction
# and the check data come from api.findPhoneNum and api.findPlaceBy
def checkAttraction(attraction):
    checker = api.findPlaceBy(attraction.name)
    phone = api.findPhoneNum(checker['place_id'])
    if attraction.name is not checker['name']:
        attraction.setName(checker['name'])
    if attraction.lat is not checker['geometry']['location']['lat']:
        attraction.setLat(checker['geometry']['location']['lat'])
    if attraction.lng is not checker['geometry']['location']['lng']:
        attraction.setLng(checker['geometry']['location']['lng'])
    if attraction.img is not checker['photos'][0]['photo_reference']:
        attraction.setImg(checker['photos'][0]['photo_reference'])
    if attraction.phone is not phone:
        attraction.setPhone(phone)
    if attraction.address is not checker['formatted_address']:
        attraction.setAddress(checker['formatted_address'])
    return attraction

# to insert attraction to database
def updateAttraction(attractionList, plan):
    try:
        for attraction in attractionList:
            attraction = checkAttraction(attraction)
            query = "select * from attraction where attractionID = %d " % attraction.attractionID
            cursor.execute(query)
            temp1 = cursor.fetchall()
            query = "select * from attraction where googleId = '%s' " % attraction.googleID
            cursor.execute(query)
            temp2 = cursor.fetchall()
            if len(temp1) == 0 and len(temp2) == 0:
                query = "select countryID from country where EN = '%s'" % (plan.country)
                cursor.execute(query)
                temp = cursor.fetchall()
                countryID = temp[0][0]
                query = 'insert into attraction (googleID, name, lat, lon, img, address, rating, '+\
                        'countryID, duration) values ("%s", "%s", %f, %f, "%s", "%s", %f, %d, %d);' % (
                        attraction.googleID, attraction.name, 
                        attraction.lat, attraction.lng, attraction.img, attraction.address, 
                        attraction.rating, countryID, attraction.duration)
                print(query)
                cursor.execute(query)
                connection.commit()
                for type in attraction.type_:
                    query = 'insert into attraction_type values (%d, "%s");' % (
                        attraction.attractionID, type)
                    cursor.execute(query)
                    connection.commit()
                print("updated attractionID: "+str(attraction.attractionID))
            else:
                print("already exist: attractionID: "+str(attraction.attractionID))
        print('all attraction synchronized')
    except mysql.connector.Error as error:
        print("from updateAttraction")
        print("Failed to insert record into Laptop table {}".format(error))

# to find the country name by using google ID
def findCountryName(countryID):
    query = "select en from country where countryID = %d" % countryID
    cursor.execute(query)
    countryName = cursor.fetchone()
    return countryName[0]

# to replace the None by empty string
def hasNoneIn(list):
    return any(elem is None for elem in list)

# to check the list included None of data or not
def replaceNone(list):
    list_ = []
    for index in range(len(list)):
        if list[index] is None:
            list_.append("")
        else:
            list_.append(list[index])
    return list_

# to find the duration time of the attraction point
def findDuration(placeName, countryName):
    query = 'select duration from attraction where name = "%s"' % (placeName)
    cursor.execute(query)
    temp = cursor.fetchall()
    if len(temp) > 0:
        duration = temp[0][0]
        return duration
    else:
        return crawler.crawlDruation(placeName + countryName)

# to check the replicate point when the route is required to re-generate
def isReplicate(attraction, originalList):
    for a in originalList:
        if a.googleID is attraction['googleID']:
            return True
    return False
    
# to insert the attraction point in the route
def insertIntoRoute(point, route_, route, plan):
    if point.name != route[-1].name:
        route.append(route_)
        route.append(point)
        checkExist(point, plan)
    return route

# to find the restaurant
def findRestaurantList(currentLocationName):
    restList.append(api.findRestaurant(currentLocationName))
    return restList

# to find the hotel
def findHotelList(currentLocationName):
    transportMode = 'transit'
    hotelList.append(api.findHotel(currentLocationName, transportMode))
    return hotelList



# to find the next attraction point
def nextPoint(currentPoint, country, routeList, type_='tourist_attraction', times=1):
    block, repeat, done, wordBlock = False, False, False, False
    location = api.findLocation(currentPoint)
    nextList = api.findNextAttraction(currentPoint, location['lat'], location['lng'], type_)
    temp = {}
    blockKeyWords = ['Hospital']
    try:
        while not done:
            next_ = nextList.pop(-1*times)
            temp = next_
            # to check the next point is in black list or repeated or not
            if len(blockPoint) > 0:
                for point in blockPoint:
                    if next_['name'] == point['name']:
                        block = True
                        break
                    else:
                        block = False
            if len(went) > 0:
                for point in went:
                    if next_['name'] == point.name:
                        repeat = True
                        break
                    else:
                        repeat = False
            for word in next_['name'].split():
                if word in blockKeyWords:
                    wordBlock = True
                    break
                else:
                    wordBlock = False
            if not block and not repeat and not wordBlock:
                done = True
        
        duration = findDuration(next_['name'],country)
        nextPoint_ = {'googleID': next_['place_id'], 'address': next_['vicinity'],
                    'name': next_['name'], 'duration': duration}
        return nextPoint_
    except IndexError :
        blockPoint.append(temp)

# to find the current attraction id
def currentAttractionID():
    if len(attractionList) > 0:
        maxID = attractionList[-1].attractionID
    else:
        maxID = 0
    return maxID

# check attraction is in database or not, if not insert it
def checkExist(point, plan):
    exist = False
    for attraction in attractionList:
        if point.googleID is attraction.googleID:
            exist = True
    if not exist:
        try:
            temp = api.findAttraction(point.name)
            location = temp['geometry']['location']
            if 'photos' in temp.keys():
                img = temp['photos'][0]['photo_reference']
            else:
                img = ""

            if 'formatted_address' in temp.keys():
                address = temp['formatted_address']
            elif 'vicinity' in temp.keys():
                address = temp['vicinity']
            else:
                address = ""

            if 'rating' in temp.keys():
                rating = temp['rating']
            else:
                rating = 0

            country = plan.country
            type_ = []
            for type in temp['types']:
                type_.append(type)
            attraction = Plan.Attraction(point.attractionID, point.googleID, point.name,
                                        location['lat'], location['lng'], img, address, rating, 
                                        country, point.duration, type_)
            attractionList.append(attraction)
        except IndexError:
            pass

# check the attraction is hotel or not
def isHotel(name):
    try:
        isHotel = False
        types = api.findAttraction(name, 'lodging')
        for type in types:
            if type is 'lodging':
                isHotel = True
        return isHotel
    except:
        return False

# to setup the start time of the attraction
def setStartTime(routeList):
    a = routeList[-1].startTime + datetime.timedelta(seconds=routeList[-1].duration)
    return a

# to find the restaurant for lunch
def golunch(routeList, plan):
    restaurant = findRestaurantList(routeList[-1].name).pop().pop(-1)
    tempRoute = api.genRoute(
        routeList[-1].name, restaurant['name'])
    name = "from %s transport to %s" % (
        routeList[-1].name, restaurant['name'])
    startTime = setStartTime(routeList)
    route = Plan.Route(routeList[0].day, name, len(routeList)+1, 
                    tempRoute['legs'][0]['duration']['value'], 
                    startTime, tempRoute['overview_polyline']['points'])
    startTime = route.startTime + datetime.timedelta(seconds=route.duration)
    point = Plan.Point(routeList[0].day, currentAttractionID()+1, restaurant['id'], 
                    restaurant['name'], len(routeList)+2, findDuration(restaurant['name'], 
                    plan.country), startTime, 1)
    checkExist(point, plan)
    routeList = insertIntoRoute(point, route, routeList, plan)
    return routeList

# to find the route between current point and the next point
# the nextPoint can be attraction or nextPoint
def findRouteBetween(day, nextPoint, routeList, plan, *last, type_=1):
    try:
        tempRoute = api.genRoute(routeList[-1].name, nextPoint['name'])
        name = "from %s transport to %s" % (routeList[-1].name, nextPoint['name'])
        startTime = setStartTime(routeList)

        route = Plan.Route(routeList[0].day, name, len(routeList)+1, 
                            tempRoute['legs'][0]['duration']['value'], 
                            startTime, tempRoute['overview_polyline']['points'])

        startTime = route.startTime + datetime.timedelta(seconds=route.duration)

        point = Plan.Point(routeList[0].day, currentAttractionID()+1, nextPoint['googleID'], 
                        nextPoint['name'], len(routeList)+2, nextPoint['duration'], 
                        startTime, type_)
        if len(last) != 0:
            point = routeList[0]
            point.setStartTime(startTime)
            point.setType(3)
            # point.setPlaceOrder(len(routeList)+2)
        return {'point': point, 'route': route}
    except:
        error = True
        blockPoint.append(nextPoint)
        if len(routeList) <= 3:
            return {'point':routeList[-1], 'route':routeList[-2]}
        else:
            return {'point':routeList[-1], 'route':routeList[-2]}

# to catch the point in the day until the time is over 1830
def loopPointInDay(day, startTime, plan, routeList):
    havelunch = False
    # find gen the schedule before 1830, after that go dinner and return to hotel
    while startTime < datetime.datetime(plan.startDate.year, plan.startDate.month, 
                                        plan.startDate.day+day-1, hour = 19, minute = 00):
        times = 1
        while True:
            nextPoint_ = nextPoint(routeList[-1].name, plan.country, routeList, times=times)
            temp = findRouteBetween(day, nextPoint_, routeList, plan)
            if temp['route'] == '':
                continue
            elif temp['route'].duration < 2*3600:
                break
            times = times + 1

        routeList = insertIntoRoute(temp['point'], temp['route'], routeList, plan_)
        print('found next point: ',temp['point'].name)
        went.append(temp['point'])
        startTime = setStartTime(routeList)
    # go back hotel
    # if the start point is hotel
    if isHotel(routeList[0].name):
        temp = findRouteBetween(day, routeList[0], routeList, plan_, type_=3)
        routeList = insertIntoRoute(temp['point'], temp['route'], routeList, plan_)
    else:
        nextPoint_ = nextPoint(routeList[-1].name, plan.country, routeList, 'lodging')
        temp = findRouteBetween(day, nextPoint_, routeList, plan_, type_=3)
        routeList = insertIntoRoute(temp['point'], temp['route'], routeList, plan_)
    return routeList

# get all attraction
def getAllAttraction():
    query = "select * from attraction"
    cursor.execute(query)
    attractions = cursor.fetchall()
    for attraction in attractions:
        types = []
        query = 'select * from attraction_type where id = %d' % attraction[0]
        cursor.execute(query)
        for type in cursor.fetchall():
            types.append(type)
            attraction_ = Plan.Attraction(attraction[0], attraction[1], attraction[2], attraction[3], 
                                      attraction[4], attraction[5],  attraction[7], attraction[9],
                                      attraction[10], attraction[11], types, 
                                      phone=attraction[6], businessHour=attraction[8])
        attractionList.append(attraction_)

# store the plan content in the must-go list which is assigned by user
def storeIn(googleID, list_):
    mustGo = list_
    info = api.findPlaceBy(googleID)
    duration = crawler.crawlDruation(info['name'])
    attraction = Plan.Attraction(len(attractionList)+1, info['place_id'], 
        info['name'], info['geometry']['location']['lat'], info['geometry']['location']['lng'],
        info['photos']['photo_reference'], "", info['formatted_address'], 
        "", info['rating'], plan_.country, duration, info['types'])
    mustGo.append(attraction)
    return mustGo

# to catch the point in the day until the time is over 1830
# this method will go all attraction which is in must-Go list first
# if there is no attraction in must-Go list, call loopPointInDay()
def loopMustGoInDay(mustGoList, anyDayMustGoList, routeList, plan):
    havelunch = False
    endPointFinished = True
    startTime = setStartTime(routeList)
    while startTime < datetime.time(18, 30):
        if len(mustGoList) > 0:
            nextPoint = mustGoList.pop()
            temp = findRouteBetween(nextPoint, routeList, plan)
            routeList = insertIntoRoute(temp['point'], temp['route'], routeList, plan_)
            startTime = setStartTime(routeList)
            
        elif len(anyDayMustGoList) > 0:
            nextPoint = anyDayMustGoList.pop()
            temp = findRouteBetween(nextPoint, routeList, plan)
            routeList = insertIntoRoute(temp['point'], temp['route'], routeList, plan_)
            startTime = setStartTime(routeList)
            
        else:
            routeList = loopPointInDay(day, startTime, plan, routeList)
            endPointFinished = False
        
    if endPointFinished:
        hotel = findHotelList(routeList[-1].name).pop()
        temp = findRouteBetween(hotel, routeList, plan, type_=3)
        temp['point'].setDuration(0)
        routeList = insertIntoRoute(temp['point'], temp['route'], routeList, plan_)
    return routeList

# to store the original attraction in route
def getOriginalRoute(plan):
    query = 'select day, attractionID, googleId, name, placeOrder, start_time, duration, '+\
            'type from plan_content, attraction where type = 3 and day = %d and '+\
            'attraction.attractionID = plan_content.attractionID' %(plan.day)
    cursor.execute(query)
    route = cursor.fetchall()
    originalList = []
    for point in route:
        tempPoint = Plan.Point(point[0], point[1], point[2], point[3], 
                               point[4], point[5], point[6], point[7])
        originalList.append(tempPoint)
    return originalList
    
# to catch the point in the day until the time is over 1830
# and exclude the original's attraction
def reLoopPointInDay(day, startTime, plan, routeList, originalList):
    havelunch = False
    while startTime < datetime.datetime(plan.startDate.year, plan.startDate.month, 
                                        plan.startDate.day+day, hour = 18, minute = 20):
        nextPoint_ = nextPoint(routeList[-1].name, plan.country, routeList)
        if isReplicate(nextPoint_, originalList):
            nextPoint_ = nextPoint(routeList[-1].name, plan.country, routeList, times=2)
        temp = findRouteBetween(nextPoint_, routeList)
        routeList = insertIntoRoute(temp['point'], temp['route'], routeList, plan_)
        startTime = setStartTime(routeList)
        
        # if startTime > datetime.time(12, 0) and startTime < datetime.time(16,0) and not havelunch:
        #     routeList = golunch(routeList, plan)
        #     startTime = setStartTime(routeList)
        #     havelunch = True

    # find restaurant for dinner
    # startTime = setStartTime(routeList)
    # restaurant = findRestaurantList(routeList[-1].name).pop()
    # temp = findRouteBetween(restaurant, routeList)
    # routeList = insertIntoRoute(temp['point'], temp['route'], routeList, plan_)
    # startTime = setStartTime(routeList)

    # go back hotel
    if isHotel(routeList[0].name):
        temp = findRouteBetween(routeList[0], routeList, plan_, type_=3)
        routeList = insertIntoRoute(temp['point'], temp['route'], routeList, plan_)
    else:
        hotel = findHotelList(routeList[-1].name).pop()
        temp = findRouteBetween(hotel, routeList, plan_, type_=3)
        routeList = insertIntoRoute(temp['point'], temp['route'], routeList, plan_)

    return routeList

# to update the route into plan content
def updatePlanContent(routeList, attractionList, plan):
    try:
        updateAttraction(attractionList, plan)
        for i in routeList:
            i = checkAttraction(i)
            if i.type != 3:
                query = "select * from attraction_type where id = %d and type = 'lodging'" % (i.attractionID)
                cursor.execute(query)
                if i.day==1 and i.placeOrder == 1:
                    i.setType(0)
                elif len(cursor.fetchall()) > 0:
                    i.setType(2)
                elif type(i) == Plan.Point:
                    i.setType(1)
                elif type(i) == Plan.Route:
                    i.setType(4)

            if i.placeOrder%2 == 1:
                query = 'insert into plan_content (planID, day, attractionID, googleId, '+\
                        'placeOrder, duration, start_time, type, add_by, route) values ('+\
                        '%d, %d, %d, "%s", %d, %d, "%s", %d, %d, "%s")' % (plan.planID, 
                        i.day, i.attractionID, i.googleID, i.placeOrder, i.duration, 
                        i.startTime.strftime("%H:%M"), i.type, 1, None)
            else:
                query = 'insert into plan_content (planID, day, '+\
                        'placeOrder, duration, start_time, type, add_by, route) values ('+\
                        '%d, %d, %d, %d, "%s", %d, %d, "%s")' % (plan.planID, 
                        i.day, i.placeOrder, i.duration, 
                        i.startTime.strftime("%H:%M"), i.type, 1, i.route)
            print(query)
            cursor.execute(query)
        connection.commit()
    except mysql.connector.Error as error:
        print("from updatePlanContent")
        print("Failed to insert record into Laptop table {}".format(error))


while True:
    try:
        connection = mysql.connector.connect(       # to create the database connection
            host="58.152.180.221",
            username="chilladmin",
            password="ChillPa$$w0rd",
            database="hochilltrip1",
            buffered=True)
        cursor = connection.cursor()    # create the cursor for database
        query = "select * from plan where state = 1 or state = 3"
        cursor.execute(query)
        toDoPlan = cursor.fetchall()
        print("waiting for create plan...")
        if len(toDoPlan) > 0:
            for plan in toDoPlan:
                countryName = findCountryName(plan[3])
                plan_ = Plan.Plan(plan[0], countryName, plan[1],
                                plan[4], plan[5], plan[-1])
                query = "select * from plan_content where planID = %d" % (plan_.planID)
                cursor.execute(query)
                planContent = cursor.fetchall()
                query = "select EN from country, plan where planID = %d and plan.countryID = country.countryID" % (
                    plan_.planID)
                cursor.execute(query)
                country = cursor.fetchall()[0]
                getAllAttraction()
                print("catch plan: %d" % (plan_.planID))
                # there is no point save in the route already and the plan is first time require to gen route
                if len(planContent) is 0 and plan_.state is 1:
                    # no place must go, whole trip require to generate
                    # for the first day
                    for day in range(1, plan_.duration+1):
                        print('start to gen day ',day)
                        routeList = initialDayOfDuration(plan_)['routeList']
                        # the plan is empty: day 1
                        if day is 1:
                            init = initialDay1(day, routeList, plan_, 1)
                            # to find the route of day
                            routeList = loopPointInDay(day, init['startTime'], plan_, init['routeList'])
                            endOfday = routeList[-1]
                            print("day 1 finished")
                        else:
                            # if not day 1
                            routeList = initialDay(day, endOfday, plan_)
                            startTime = setStartTime(routeList)

                            routeList = loopPointInDay(day, startTime, plan_, routeList)
                            endOfday = routeList[-1]
                            if day == plan_.duration:
                                routeList[-1].setType(3)
                            print("day " + str(day) + " finished")
                        # insert the route into database
                        updatePlanContent(routeList, attractionList, plan_)
                
                # there are some must-go attraction saved in the plan which is first time require to gen route
                elif len(planContent) is not 0 and plan_.state is 1:
                    # store point in class attraction
                    for point in planContent:
                        if point[1] == day and not point[3]:
                            mustGoList = storeIn(point[3], mustGoList)
                        elif point[1] == 0 and not point[3]:
                            anyDayMustGoList = storeIn(point[3], anyDayMustGoList)
                        elif point[1] == day and not point[2]:
                            query = "select googleId from attraction where attractionID = %d" %(point[2])
                            cursor.execute(query)
                            googleID = cursor.fetchall()[0]
                            mustGoList = storeIn(googleID, mustGoList)
                        elif point[1] == 0 and not point[2]:
                            query = "select googleId from attraction where attractionID = %d" %(point[2])
                            cursor.execute(query)
                            googleID = cursor.fetchall()[0]
                            anyDayMustGoList = storeIn(point[3], anyDayMustGoList)
                    # there are some place must be go
                    for day in range(1,plan_.duration+1):
                        # go all must-go place first, then gen the rest
                        routeList = initialDayOfDuration(plan_)['routeList']
                        startTime = datetime.time(9, 0)
                        if len(mustGoList) != 0 and day == 1:
                            print('start to gen day 1')
                            attraction = mustGoList.pop()
                            point = Plan.Point(day, attraction.attractionID, attraction.googleID, 
                                            attraction.name, len(routeList)+1, attraction.duration, 
                                            startTime, 1)
                            routeList.append(point)
                            routeList = loopMustGoInDay(mustGoList, anyDayMustGoList, routeList)
                            endOfday = routeList[-1]
                            print("day 1 finished")
                        else:
                            print('start to gen day %s') % (str(plan_.day))
                            routeList = initialDay(day, endOfday, plan_)
                            routeList = loopMustGoInDay(mustGoList, anyDayMustGoList, routeList)
                            endOfday = routeList[-1]
                            if plan_.day == plan_.duration:
                                routeList[-1].setType(3)
                            print("day %s finished") % (str(plan_.day))
                        updatePlanContent(routeList, attractionList, plan_)
                
                # ther are the plan which is want to re-gen the route
                # the attraction of the route will no replucate
                elif plan_.state == 3:
                    original = getOriginalRoute()
                    for day in range(1, plan_.duration+1):
                        routeList = initialDayOfDuration(plan_)['routeList']
                        if day is 1:
                            print('start to gen day 1')
                            init = initialDay1(day, routeList, plan_)
                            routeList = reLoopPointInDay(day, init['startTime'], plan_, init['routeList'], original)
                            endOfday = routeList[-1]
                            print("day 1 finished")
                        else:
                            print('start to gen day %s') % (str(plan_.day))
                            routeList = initialDay(day, endOfday, plan_)
                            startTime = setStartTime(routeList)

                            routeList = reLoopPointInDay(day, init['startTime'], plan_, init['routeList'], original)
                            endOfday = routeList[-1]
                            if plan_.day == plan_.duration:
                                routeList[-1].setType(3)
                            print("day %s finished") % (str(plan_.day))
                        updatePlanContent(routeList, attractionList, plan_)
                plan_.setState(2)
                query = "UPDATE plan SET state = %d WHERE planID = %d"%(plan_.state, plan_.planID)
                cursor.execute(query)
                connection.commit()
    finally:
        cursor.close()
        connection.close()
    time.sleep(5)