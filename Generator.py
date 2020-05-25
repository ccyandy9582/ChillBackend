import time
import datetime
import mysql.connector
import Crawler
import GoogleApi
import Plan

crawler = Crawler.Crawler()     # to find the duration time on internet
restList = []                   # to store the restaurants
hotelList = []                  # to store the hotels
attractionList = []             # to store the attractions from this program
attractionListFromDB = []       # to store the attractions from our database
mustGoList = []                 # the must-go place that is assigned day
anyDayMustGoList = []           # the must-go place that is no assigned day
endOfday = Plan.Point           # to store the end of day point 
went = []                       # to store the attraction that is went
blockPoint = []                 # some point has a route to go but no route to out

# to initial the day
def initialDayOfDuration(plan, day):
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
    duration = 0
    for a in attractionListFromDB:
        if attraction['name'] == a.name:
            duration = a.duration
            break
    if duration == 0:
        duration = crawler.crawlDruation(attraction['name'])
    point = Plan.Point(day, currentAttractionID()+1, attraction['place_id'], 
                        attraction['name'], len(routeList)+1, duration, 
                        startTime, 0)
    checkExist(point, plan)
    routeList.append(point)
    startTime = setStartTime(routeList)
    return {'startTime': startTime, 'routeList': routeList}

# to initial the day of plan except day 1
def initialDay(day, endOfday, plan):
    routeList = []
    point = endOfday
    point.setPlaceOrder(len(routeList)+1)
    startDate = datetime.datetime(plan.startDate.year, plan.startDate.month, 
                                  plan.startDate.day, hour=9)
    startDate = startDate + datetime.timedelta(days = day-1)
    point.setStartTime(startDate)
    point.setType(2)
    point.setDay(day)
    routeList.append(point)
    return routeList

# check the attraction infomation is correct
# if some information is lost or worng, correct it
# the name is assumed 100% correct
# the original data come from api.findAttraction or api.findNextAttraction
# and the check data come from api.findPhoneNum and api.findPlaceBy
def checkAttraction(attraction = Plan.Attraction):
    change = False
    googleID = api.findPlaceID(attraction.name)
    checker = api.findPlaceBy(googleID)

    if attraction.googleID != googleID:
        attraction.setGoogleID(googleID)
        change = True

    if attraction.lat != checker['geometry']['location']['lat']:
        attraction.setLat(checker['geometry']['location']['lat'])
        change = True

    if attraction.lng != checker['geometry']['location']['lng']:
        attraction.setLng(checker['geometry']['location']['lng'])
        change = True

    if ('photos' in checker.keys() and 
        attraction.img != checker['photos'][0]['photo_reference']):
        attraction.setImg(checker['photos'][0]['photo_reference'])
        change = True

    # keyword 'is' is compare the ram address same or not
    # '==' is compare the value same or not
    phone = api.findPhoneNum(attraction.googleID)
    if attraction.phone != phone:
        attraction.setPhone(phone)
        change = True

    if attraction.address != checker['formatted_address']:
        attraction.setAddress(checker['formatted_address'])
        change = True

    if 'lodging' in checker['types']:
        attraction.setDuration(0)
        change = True
    elif (attraction.duration == None or attraction.duration < 900 or 
          attraction.duration > 28800):
        attraction.setDuration(crawler.crawlDruation(attraction.name))
        change = True

    if attraction.type_ != checker['types']:
        attraction.setType(checker['types'])
        change = True

    return {'attraction': attraction, 'change': change}

# check the point information is correct
# assume the name is 100% correct
def checkPoint(point = Plan.Point):
    if 'from' not in point.name.split():
        query = 'select * from attraction where name = "%s"' % (point.name)
        cursor.execute(query)
        if cursor.rowcount > 0:
            attractionID = cursor.fetchall()[0][0]
            placeID = api.findPlaceID(point.name)
            if attractionID != point.attractionID:
                point.setAttractionID(attractionID)
            if point.duration <3600/4 or point.duration > 8*3600:
                point.setDuration(crawler.crawlDruation(point.name))
            if placeID != "" and placeID != point.googleID:
                point.setGoogleID(placeID)
    return point

# insert the new attraction into attraction table
def insertInAttraction(attraction, plan):    
    # to convert the country name to country ID
    query = "select countryID from country where EN = '%s'" % (plan.country)
    cursor.execute(query)
    temp = cursor.fetchall()
    countryID = temp[0][0]
    query = 'insert into attraction (googleID, name, lat, lon, img, phone, address, rating, '+\
            'countryID, duration) values ("%s", "%s", %f, %f, "%s", "%s", "%s", %f, %d, %d);' % (
            attraction.googleID, attraction.name, attraction.lat, attraction.lng, attraction.img, 
            attraction.phone, attraction.address, attraction.rating, countryID, 
            attraction.duration)
    print(query)
    cursor.execute(query)
    connection.commit()

    # to make sure the attractionID is correct
    query = 'select attractionID from attraction where googleId = "%s"' % (attraction.googleID)
    cursor.execute(query)
    attractionID = cursor.fetchall()[0][0]
    attraction.setAttractionID(attractionID)
    # to clear up the exist type
    query = 'delete from attraction_type where id = %d' % (attraction.attractionID)
    cursor.execute(query)
    connection.commit()
    for type_ in attraction.type_:
        query = 'insert into attraction_type values (%d, "%s");' % (
            attractionID, type_)
        cursor.execute(query)
        connection.commit()
    print("updated attractionID: "+str(attraction.attractionID))

# to insert attraction to database and double check the attraction is in database or not
# if not, insert it into database
def updateAttraction(attractionList, plan):
    try:
        for attraction in attractionList: 
            attraction = checkAttraction(attraction)['attraction']
            print(attraction)
            # double check the attraction
            query = "select * from attraction where googleId = '%s'" % (attraction.googleID)
            cursor.execute(query)
            temp1 = cursor.fetchall()
            query = "select * from attraction where name = '%s'" % (attraction.name)
            cursor.execute(query)
            temp2 = cursor.fetchall()
            # print(temp1 == None)
            # print(temp2 == None)
            if len(temp1) == 0 and len(temp2) == 0:
                insertInAttraction(attraction, plan)
            else:
                print("already exist: attractionID: "+str(attraction.name))
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
    
# to insert the attraction point in the route
def insertIntoRoute(point, route_, route, plan):
    if point.name != route[-1].name:
        route.append(route_)
        route.append(point)
        checkExist(point, plan)
    else:
        print("same point is not accept")
    return route

# to find the hotel
def findHotelList(currentLocationName):
    hotelList.append(api.findHotel(currentLocationName))
    return hotelList


# to find the next attraction point
def nextPoint(currentPoint, country, routeList, type_='tourist_attraction', *check):
    block, repeat, done, wordBlock = False, False, False, False
    location = api.findLocation(currentPoint)
    nextList = api.findNextAttraction(currentPoint, location['lat'], location['lng'], type_)
    temp = {}
    blockKeyWords = ['Hospital', 'Hotel', 'Airport']
    try:
        while not done:
            next_ = nextList.pop(-1)
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
                    # print(next_['name'] == point.name)
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
    maxID = 0
    if len(attractionList) > 0:
        maxID = attractionList[-1].attractionID
    return maxID

# check attraction is in database or not, if not insert it into attractionList
def checkExist(point, plan):
    exist = False
    for attraction in attractionListFromDB:
        if point.googleID is attraction.googleID:
            exist = True
    if not exist:
        try:
            temp = api.findAttraction(point.name)
            location = temp['geometry']['location']

            img = ""
            if 'photos' in temp.keys():
                img = temp['photos'][0]['photo_reference']

            address = ""
            if 'formatted_address' in temp.keys():
                address = temp['formatted_address']

            rating = ""
            if 'rating' in temp.keys():
                rating = temp['rating']

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

# to setup the start time of the attraction
def setStartTime(routeList):
   return routeList[-1].startTime + datetime.timedelta(seconds=routeList[-1].duration)

# to find the route between current point and the next point
# the nextPoint can be attraction or nextPoint
# the type for the point which is in start, attraction, hotel, end, transport
def findRouteBetween(day=int, nextPoint=dict, routeList=list, plan=Plan.Plan, type_=1):
    try:
        tempRoute = api.genRoute(routeList[-1].name, nextPoint['name'])
        if tempRoute != "":
            name = "from %s transport to %s" % (routeList[-1].name, nextPoint['name'])
            startTime = setStartTime(routeList)

            route = Plan.Route(routeList[0].day, name, len(routeList)+1, 
                                tempRoute['legs'][0]['duration']['value'], 
                                startTime, tempRoute['overview_polyline']['points'])

            startTime = route.startTime + datetime.timedelta(seconds=route.duration)

            point = Plan.Point(routeList[0].day, currentAttractionID()+1, nextPoint['googleID'], 
                            nextPoint['name'], len(routeList)+2, nextPoint['duration'], 
                            startTime, type_)
            return {'point': point, 'route': route}
        else:
            raise IndexError
    except IndexError:
        blockPoint.append(nextPoint)
        if len(routeList) == 1:
            return {'point':routeList[-1], 'route':""}
        elif len(routeList) >= 3:
            return {'point':routeList[-1], 'route':routeList[-2]}

# to catch the point in the day until the time is over 1830
def loopPointInDay(day, startTime, plan, routeList):
    startDate = datetime.datetime(plan.startDate.year, plan.startDate.month, 
                                  plan.startDate.day, hour=18, minute=30)
    startDate = startDate + datetime.timedelta(days = day-1)
    # find gen the schedule before 1830, after that go dinner and return to hotel
    while startTime < startDate:
        while True:
            nextPoint_ = nextPoint(routeList[-1].name, plan.country, routeList)
            temp = findRouteBetween(day, nextPoint_, routeList, plan)
            if temp['route'] == '':
                continue
            elif temp['route'].duration < 2*3600:
                break

        routeList = insertIntoRoute(temp['point'], temp['route'], routeList, plan_)
        print('found next point: ',temp['point'].name)
        went.append(temp['point'])
        startTime = setStartTime(routeList)
    # find the hotel
    nextPoint_ = nextPoint(routeList[-1].name, plan.country, routeList, 'lodging')
    temp = findRouteBetween(day, nextPoint_, routeList, plan_, type_=2)
    routeList = insertIntoRoute(temp['point'], temp['route'], routeList, plan_)
    return routeList

# get all attraction
def getAllAttraction():
    query = "select * from attraction"
    cursor.execute(query)
    attractions = cursor.fetchall()
    for attraction in attractions:
        types = []
        query = 'select type from attraction_type where id = %d' % attraction[0]
        cursor.execute(query)
        types_ = cursor.fetchall()
        for type in types_:
            types.append(type)

        attraction_ = Plan.Attraction(attraction[0], attraction[1], attraction[2], attraction[3], 
                                    attraction[4], attraction[5],  attraction[7], attraction[9],
                                    attraction[10], attraction[11], types, 
                                    phone=attraction[6], businessHour=attraction[8])
        # if db attraction information is not integrated, update it
        tempAtt = checkAttraction(attraction_)
        if tempAtt['change']:
            attraction_ = tempAtt['attraction']
            updateDBAttraction(attraction_)
            print("    updated attraction: ", attraction_.name)
        else:
            print("    no need to update: ", attraction_.name)
        attractionListFromDB.append(attraction_)

# update the attraction information in db
def updateDBAttraction(attraction):
    query = 'select country.countryID from attraction, country where attraction.attractionID = "%s" and attraction.countryID = country.countryID' % (attraction.attractionID)
    cursor.execute(query)
    countryID = cursor.fetchall()[0][0]
    query = 'update attraction set googleID = "%s", name = "%s", lat = %f, lon = %f, img = "%s", phone = "%s", address = "%s", rating = %f, countryID = %d, duration = %d where attractionID = %d' % (str(attraction.googleID), str(attraction.name), float(attraction.lat), float(attraction.lng), str(attraction.img), str(attraction.phone), str(attraction.address), float(attraction.rating), int(countryID), int(attraction.duration), int(attraction.attractionID))
    cursor.execute(query)
    connection.commit()

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
def loopMustGoInDay(mustGoList, anyDayMustGoList, routeList, plan, day, startTime):
    startDate = datetime.datetime(plan.startDate.year, plan.startDate.month, 
                                  plan.startDate.day, hour=18, minute=30)
    startDate = startDate + datetime.timedelta(days = day-1)
    while startTime < startDate:
        usedMustGo = False
        usedAnyGo = False
        mI = 0                  # must go list index
        aI = 0                  # any day go list index
        # set the nextPoint = nextPoint()
        nextPoint_ = nextPoint(routeList[-1].name, plan.country, routeList)
        # if any day must go place is match, use it
        for anyday in anyDayMustGoList:
            print(anyday)
            print(startTime)
            # print(startTime - anyday['startTime'])
            # print(startTime - anyday['startTime'] < datetime.timedelta(seconds = 3600))
            if anyday['startTime'] == '':
                nextPoint_ = anyday
                break
            elif startTime < anyday['startTime']:
                nextPoint_ = anyday
                usedAnyGo = True
                break
            else:
                aI = aI + 1
        # if must go place is match, use it
        for mustGo in mustGoList:
            print(mustGo)
            print(startTime)
            # print(startTime - mustGo['startTime'])
            # print(startTime - mustGo['startTime'] < datetime.timedelta(seconds = 3600))
            if mustGo['startTime'] == '':
                nextPoint_ = mustGo
                break
            elif startTime < mustGo['startTime']:
                nextPoint_ = mustGo
                usedMustGo = True
                break
            else:
                mI = mI + 1
        
        # remove the point in list
        if usedMustGo:
            mustGoList.pop(mI)
        elif usedAnyGo:
            anyDayMustGoList.pop(aI)

        temp = findRouteBetween(day, nextPoint_, routeList, plan)
        if temp['route'] == '':
            blockPoint.append(nextPoint_)
        else:
            routeList = insertIntoRoute(temp['point'], temp['route'], routeList, plan_)
            print('found next point: ',temp['point'].name)
            went.append(temp['point'])
            startTime = setStartTime(routeList)

    # find the hotel
    nextPoint_ = nextPoint(routeList[-1].name, plan.country, routeList, 'lodging')
    temp = findRouteBetween(day, nextPoint_, routeList, plan_, type_=2)
    routeList = insertIntoRoute(temp['point'], temp['route'], routeList, plan_)
    return routeList

# to store the original attraction in route
def getOriginalRoute(plan):
    query = 'select * from plan_content where planID = %d' % (plan.planID)
    cursor.execute(query)
    route = cursor.fetchall()
    originalList = []
    for point in route:
        if point[7] != 4:
            name = api.findNameBy(point[3])
            tempPoint = Plan.Point(point[1], point[2], point[3], name,
                                point[4], point[5], point[6], point[7], point[8])
            originalList.append(tempPoint)
            went.append(tempPoint)
    return originalList

# to update the route into plan content
def updatePlanContent(routeList, attractionList, plan):
    try:
        updateAttraction(attractionList, plan)
        for i in routeList:
            i = checkPoint(i)

            if type(i)==Plan.Point:
                query = 'insert into plan_content (planID, day, attractionID, googleId, '+\
                        'placeOrder, duration, start_time, type, add_by) values ('+\
                        '%d,%d,%d,"%s",%d,%d,"%s",%d,%d)' % (plan.planID, 
                        i.day, i.attractionID, i.googleID, i.placeOrder, i.duration, 
                        i.startTime.strftime("%H:%M"), i.type, i.addBy)
            else:
                query = 'insert into plan_content (planID, day, '+\
                        'placeOrder, duration, start_time, type, add_by, route) values ('+\
                        '%d,%d,%d,%d,"%s",%d,%d,"%s")' % (plan.planID, 
                        i.day, i.placeOrder, i.duration, 
                        i.startTime.strftime("%H:%M"), i.type, i.addBy, i.route)
            query = addslashes(query)
            print("    ",query)
            cursor.execute(query)
        connection.commit()
    except mysql.connector.Error as error:
        print("from updatePlanContent")
        print("Failed to insert record into Laptop table {}".format(error))

# to change \ to \\
def addslashes(s):
    l = ["\\"]
    for i in l:
        if i in s:
            s = s.replace(i, '\\'+i)
    return s

# for if len(planContent) == 0 and plan_.state == 1 and
# plan_.state == 3
def stateOneAndThree(plan):
    for day in range(1, plan.duration+1):
        print('start to gen day ',day)
        routeList = initialDayOfDuration(plan, day)['routeList']
        # the plan is empty: day 1
        if day == 1:
            init = initialDay1(day, routeList, plan, 1)
            # to find the route of day
            routeList = loopPointInDay(day, init['startTime'], plan, init['routeList'])
            endOfday = routeList[-1]
        else:               # if not day 1
            routeList = initialDay(day, endOfday, plan)
            startTime = setStartTime(routeList)

            routeList = loopPointInDay(day, startTime, plan, routeList)
            endOfday = routeList[-1]
            # if last day, then go back airport
            if day == plan.duration:
                startTime = setStartTime(routeList)
                airport = api.findAttraction(country, 'airport')
                for a in attractionListFromDB:
                    if airport['name'] == a.name:
                        duration = a.duration
                if duration == 0:
                    duration = crawler.crawlDruation(airport['name'])
                routeList[-1] = Plan.Point(day, currentAttractionID()+1, airport['place_id'], 
                                           airport['name'], len(routeList)+1, duration, 
                                           startTime, 3)
        print("day %d finished" % (day))
        updatePlanContent(routeList, attractionList, plan_)


def isAirport(mustGo = dict):
    isAirport = False
    query = 'select type from attraction_type where id = %d' % (mustGo['attractionID'])
    cursor.execute(query)
    types = cursor.fetchall()
    for type_ in types:
        if 'airport' in type_:
            isAirport = True
            break
    return isAirport

def convertToStartTime(mustGo, plan):
    hour = mustGo[-4].split(":")[0]
    minute = mustGo[-4].split(":")[1]
    startTime = datetime.datetime(plan.startDate.year, plan.startDate.month, plan.startDate.day+mustGo[1]-1, 
                                  hour=int(hour), minute=int(minute))
    return startTime

def getAllAssignedAttraction(plan):
    # store anyday-go-attraction into anydayMustGoList
    query = 'select * from plan_content where day = 0 and planID = %d' % (plan_.planID)
    cursor.execute(query)
    anydays = cursor.fetchall()
    for anyday in anydays:
        if anyday[2] != None:
            query = 'select googleID, name from attraction where attractionID = %d' % (anyday[2])
            cursor.execute(query)
            temp = cursor.fetchall()[0]
            googleID = temp[0]
            name = temp[1]
            startTime = convertToStartTime(anyday, plan)
            duration = anyday[-5]
            if anyday[-5] == None:
                duration = crawler.crawlDruation(name)
            anyDayMustGoList.append({'day':anyday[1], 'attractionID':anyday[2], 'duration': duration, 'startTime':startTime,
                                        'add_by': anyday[-2], 'googleID':googleID, 'name':name})
    # store assigned-day-must-go into to mustGoList
    query = 'select * from plan_content where day <> 0 and planID = %d' % (plan_.planID)
    cursor.execute(query)
    mustGos = cursor.fetchall()
    for mustGo in mustGos:
        query = 'select googleID, name, duration from attraction where attractionID = %d' % (mustGo[2])
        cursor.execute(query)
        temp = cursor.fetchall()[0]
        googleID = temp[0]
        name = temp[1]
        duration = mustGo[5]
        if duration == None:
            duration = temp[2]

        startTime = ""
        if mustGo[6] != None:
            startTime = convertToStartTime(mustGo, plan)

        mustGoList.append({'day':mustGo[1], 'attractionID':mustGo[2], 'duration': duration, 'startTime':startTime, 
                            'add_by': mustGo[-2], 'googleID':googleID, 'name':name})

while True:
    try:
        connection = mysql.connector.connect(       # to create the database connection
            host="58.152.180.221",
            username="chilladmin",
            password="ChillPa$$w0rd",
            database="hochilltrip",
            buffered=True)
        cursor = connection.cursor()                # create the cursor for database
        query = "select * from plan where state = 1 or state = 3"
        # query = "select * from plan where planID = 21"
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
                query = "select EN from country, plan where planID = %s and plan.countryID = country.countryID" % (plan_.planID)
                cursor.execute(query)
                country = cursor.fetchall()[0]
                print("catch plan: %d" % (plan_.planID))
                api = GoogleApi.API(plan_.useTransport)             # for using google api
                print("updating attraction information which is exist in database")
                getAllAttraction()

                # there is no point save in the route already and the plan is first time require to gen route
                if len(planContent) == 0 and plan_.state == 1:
                    stateOneAndThree(plan_)
                
                # there are some must-go attraction saved in the plan which is first time require to gen route
                elif len(planContent) != 0 and plan_.state == 1:
                    # get all assigned point
                    getAllAssignedAttraction(plan_)

                    # there are some place must be go
                    for day in range(1,plan_.duration+1):
                        # go all must-go place first, then gen the rest
                        routeList = initialDayOfDuration(plan_, day)['routeList']
                        print('start to gen day %d' % (day))
                        if day == 1:
                            if len(mustGoList) > 0 or len(anyDayMustGoList) > 0:
                                startTime = datetime.datetime(plan_.startDate.year,plan_.startDate.month, plan_.startDate.day, 
                                                              hour=9, minute=0)
                                if isAirport(mustGoList[0]):
                                    startTime = convertToStartTime(mustGoList, plan_)
                                    attraction = mustGoList.pop()
                                    point = Plan.Point(day, attraction['attractionID'], attraction['googleID'], 
                                                attraction['name'], len(routeList)+1, attraction['duration'], 
                                                startTime, 1)
                                    routeList[0]=point
                                else:
                                    init = initialDay1(day, routeList, plan_, 1)
                                    routeList = init['routeList']
                                    startTime = init['startTime']                                    
                                routeList = loopMustGoInDay(mustGoList, anyDayMustGoList, routeList, plan_, day, startTime)
                                endOfday = routeList[-1]
                                for a in routeList:
                                    print(a)
                        else:       # the day is not 1
                            if len(mustGoList) > 0 or len(anyDayMustGoList) > 0:
                                routeList = initialDay(day, endOfday, plan_)
                                routeList = loopMustGoInDay(mustGoList, anyDayMustGoList, routeList, plan_, day, startTime)
                                endOfday = routeList[-1]
                                for a in routeList:
                                    print(a)
                            else:
                                routeList = initialDay(day, endOfday, plan)
                                startTime = setStartTime(routeList)
                                routeList = loopPointInDay(day, startTime, plan, routeList)
                                endOfday = routeList[-1]
                                for a in routeList:
                                    print(a)

                            # if last day, then go back airport
                            if day == plan_.duration:
                                startTime = setStartTime(routeList)
                                airport = api.findAttraction(country, 'airport')
                                for a in attractionListFromDB:
                                    if airport['name'] == a.name:
                                        duration = a.duration
                                if duration == 0:
                                    duration = crawler.crawlDruation(airport['name'])

                                point = Plan.Point(day, currentAttractionID()+1, airport['place_id'], 
                                                   airport['name'], len(routeList)+1, duration, 
                                                   startTime, 3)
                            
                        print("day %d finished" % (day))
                        query = 'delete from plan_content where planID = %d and day = %d' % (plan_.planID, day)
                        cursor.execute(query)
                        connection.commit()
                        updatePlanContent(routeList, attractionList, plan_)
                
                # ther are the plan which is want to re-gen the route
                # the attraction of the route will no replucate
                # get all attraction and append it into went list
                # then clear plan_content in db
                elif plan_.state == 3:
                    original = getOriginalRoute(plan_)
                    query = 'delete from plan_content where planID = %d' % (plan_.planID)
                    cursor.execute(query)
                    connection.commit()
                    stateOneAndThree(plan_)
                
                # when all finish, set the plan to finish
                plan_.setState(2)
                query = "UPDATE plan SET state = %d WHERE planID = %d"%(plan_.state, plan_.planID)
                cursor.execute(query)
                connection.commit()
                print("plan %d finished" % (plan_.planID))
        cursor.close()
        connection.close()
    finally:
        time.sleep(5)