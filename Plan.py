import datetime


class Plan():
    def __init__(self, planID, country, useTransport, startDate, endDate, state):
        self.planID = int(planID)
        self.country = country
        self.useTransport = self.setTransport(useTransport)
        self.startDate = startDate
        self.endDate = endDate
        self.duration = (endDate-startDate).days+1  # how many days will stay
        # 1: need to generate the plan, 2: finish, 3: require to re-generate
        self.state = state

    def setState(self, state):
        self.state = state

    def setTransport(self, useTransport):
        if useTransport is 0:
            mode = "transit"
        else:
            mode = "driving"
        return mode

    def __str__(self):
        return "planID: %d, country: %s, transport: %s , start date: %s, end date: %s, "+\
               "duration: %d, state: %d" % (self.planID, self.country, self.useTransport, 
               self.startDate.strftime("%d-%m-%y"), self.endDate.strftime("%d-%m-%y"), 
               self.duration, self.state)


class Point():
    def __init__(self, day, attractionID, googleID, name, placeOrder, duration, startTime, type_):
        self.day = int(day)
        self.attractionID = int(attractionID)
        self.googleID = googleID
        self.name = name
        self.placeOrder = int(placeOrder)
        self.startTime = startTime
        self.duration = int(duration)
        self.type = self.setType(type_)  # 0:start, 1:attraction, 2:hotel, 3:end, 4:transport

    def setDay(self, day):
        self.day = day

    def setAttractionID(self, attractionID):
        self.attractionID = attractionID

    def setStartTime(self, startTime):
        self.startTime = startTime

    def setPlaceOrder(self, idx):
        self.placeOrder = idx

    def setType(self, type_):
        if type_ >= 0 and type_ <= 4:
            self.type = type_

    def __str__(self):
        return "day: "+str(self.day)+\
               ", attractionID: "+str(self.attractionID)+\
               ", googleID: "+self.googleID+\
               ", name: "+self.name+\
               ", place order index: "+str(self.placeOrder)+\
               ", start time: "+self.startTime.strftime("%d-%m-%y, %H:%M")+\
               ", duration: "+str(self.duration)+\
               ", type: "+str(self.type)


class Attraction():
    def __init__(self, attractionID, googleID, name, lat, lng, img, address, 
                 rating, country, duration, type_, phone='', businessHour=''):
        self.attractionID = attractionID
        self.googleID = googleID
        self.name = name
        self.lat = float(lat)
        self.lng = float(lng)
        self.img = img
        self.phone = phone
        self.address = address
        self.businessHour = businessHour
        self.rating = rating
        self.country = country
        self.duration = duration
        self.type_ = type_

    def setDuration(self, duration):
        self.duration = duration

    def __str__(self):
        type_ = ""
        for _type in self.type_:
            type_ = type_ + " " + _type
        return "attractionID: "+str(self.attractionID)+\
               ", googleID: "+self.googleID+\
               ", name: "+self.name+\
               ", location: { "+str(self.lat)+", "+str(self.lng)+" }"+\
               ", img: "+self.img+\
               ", phone: "+self.phone+\
               ", address: "+self.address+\
               ", business hour: "+self.businessHour+\
               ", rating: "+str(self.rating)+\
               ", country: "+self.country+\
               ", duration: "+str(self.duration)+\
               ", type: "+type_


class Route(Point):
    def __init__(self, day, name, placeOrder, duration, startTime, route):
        super().__init__(day, 0, "", name, placeOrder, duration, startTime, type_=4)
        self.route = route

    def __str__(self):
        return super(Route, self).__str__() +\
             ", route: "+self.route