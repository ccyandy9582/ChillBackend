import googlemaps
import googlemaps.directions
import googlemaps.places
import operator
import datetime
import requests

class API():
    def __init__(self, transportMode):
        self.api_key = "AIzaSyBSBBEmsLVTTCM3vXMV6aUB6uw50F4BPQk"
        self.client = googlemaps.Client(key=self.api_key)
        self.transportMode = transportMode

    def findLocation(self, place):
        location = self.findAttraction(place)['geometry']['location']
        return location

    def findPhoneNum(self, googleID):
        try:
            parms = (googleID, self.api_key)
            string = "https://maps.googleapis.com/maps/api/place/details/json?place_id=%s&language=en&fields=name,rating,international_phone_number&key=%s" % parms
            json = requests.get(string).json()
            phone = ""
            if json['status'] == 'OK':
                if 'international_phone_number' in json['result'].keys():
                    phone = json['result']['international_phone_number']
            return phone
        except KeyError as e:
            print(e.args[0])
            return ""

    def findAttraction(self, placeName, type_='tourist_attraction'):
        result = self.client.places(placeName, type=type_, language='en')
        info = dict
        if result['status'] == 'OK':
            info = result['results'][0]
        else:
            info = self.findAttraction(placeName, "")
        return info

    def findPlaceID(self, name):
        location = self.findLocation(name)
        parms = (location['lat'], location['lng'], self.api_key)
        string = 'https://maps.googleapis.com/maps/api/geocode/json?latlng=%f,%f&key=%s' % parms
        json = requests.get(string).json()
        placeid = ""
        if json['status'] == 'OK':
            placeid = json['results'][0]['place_id']
        return placeid

    def searchNearby(self, type_, lat, lng, radius=15000):
        location = (lat, lng)
        radius = radius   # the unit is meter
        placeType = type_
        places = self.client.places_nearby(location, radius, type=placeType, language='en')
        return places['results']

    # TODO: need to add starttime in parms
    def genRoute(self, startName, endName):
        # there are 4 mode: driving, walking, bicycling, transit
        try:
            startID = self.findPlaceID(startName)
            endID = self.findPlaceID(endName)
            string = "https://maps.googleapis.com/maps/api/directions/json?"+\
                    "origin=place_id:%s&destination=place_id:%s&key=%s" % (startID, endID, self.api_key)
            json = requests.get(string).json()
            direction = ""
            if json['status'] == 'OK':
                direction = json['routes'][0]
            return direction
            # direction = self.client.directions(origin=startName,
            #                                     destination=endName,
            #                                     mode=self.transportMode,
            #                                     departure_time=datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day, hour = 14, minute = 00))
            # return direction[0] 
        except:
            return ""

    def findNameBy(self, googleID):
        parms = (googleID, self.api_key)
        string = "https://maps.googleapis.com/maps/api/place/details/json?place_id=%s&language=en&fields=name,rating,international_phone_number&key=%s" % parms
        json = requests.get(string).json()
        name = ""
        if json['status'] == 'OK':
            name = json['result']['name']
        return name

    def findPlaceBy(self, googleID):
        # Valid values for the `fields` param for `find_place` are 'geometry/viewport/southwest', 
        # 'permanently_closed', 'geometry/viewport', 'icon', 'geometry/viewport/northeast/lng', 
        # 'geometry/viewport/southwest/lng', 'geometry/location', 'geometry/viewport/northeast/lat', 
        # 'geometry/location/lng', 'name', 'price_level', 'types', 'photos', 
        # 'geometry/viewport/northeast', 'geometry/viewport/southwest/lat', 'plus_code', 'rating', 
        # 'formatted_address', 'opening_hours', 'place_id', 'geometry', 'user_ratings_total', 
        # 'geometry/location/lat'
        # address = self.client.reverse_geocode(self.findLocation(googleID))[0]['formatted_address']
        name = self.findNameBy(googleID)
        fields = 'place_id, photos, name, geometry/location, formatted_address, rating, types'
        parms = (name, fields, self.api_key)
        string = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input=%s&inputtype=textquery&fields=%s&language=en&key=%s' % parms
        json = requests.get(string).json()
        info = ""
        if json['status'] == 'OK':
            info = json['candidates'][0]
        return info
        # a = self.client.find_place(phoneNum, 'phonenumber', fields = fields, language='en')['candidates'][0]
        # return self.client.find_place(phoneNum, 'phonenumber', fields = fields, language='en')['candidates'][0]

    def findRestaurant(self, currentLocationName):
        location = self.findLocation(currentLocationName)
        near = self.searchNearby('restaurant', location['lat'], location['lng'])
        restList = []
        try:
            for restaurant in near:
                restList.append(restaurant)
            # restList.sort(key=operator.attrgetter('rating'))
            self.bubbleSort(restList)
        finally:
            return restList

    def findHotel(self, currentLocationName):
        location = self.findLocation(currentLocationName)
        near = self.searchNearby('lodging', location['lat'], location['lng'])
        hotelList = []
        try:
            for hotel in near:
                hotelList.append(hotel)
            # hotelList.sort(key=operator.attrgetter('rating'))
            self.bubbleSort(hotelList)
            return hotelList
        finally:
            pass

    def findNextAttraction(self, currentLocation, currentLat, currentLng, 
                           type_= 'tourist_attraction'):
        near = self.searchNearby(type_, currentLat, currentLng)
        nextList = []
        for attraction in near:
            nextList.append(attraction)
        if type_ == 'tourist_attraction':
            self.bubbleSort(nextList)
        return nextList

    def bubbleSort(self, arr): 
        n = len(arr) 
        # sort the list by rating
        for i in range(n): 
            swapped = False
            for j in range(0, n-i-1): 
                if 'rating' in arr[j] and 'rating' in arr[j+1]:
                    if arr[j]['rating'] > arr[j+1]['rating'] : 
                        arr[j], arr[j+1] = arr[j+1], arr[j] 
                        swapped = True
                else:
                    arr[j], arr[j+1] = arr[j+1], arr[j] 
                    swapped = True
                if swapped is False: 
                    break
        

api = API('driving')
# print(api.findHotel('愉景灣觀光馬車'))
print(api.findPlaceBy('ChIJncZGzPPiAzQRnjaSGIKQ9fk'))
# print(api.findPlaceID('Hong Kong Disneyland'))
# a= api.findAttraction("The Harbourview")
# print(a)
# route = api.genRoute('Hong Kong International Airport', 'Grand Hall of Ten Thousand Buddhas, Po Lin Monastery')
# print(route['legs'][0]['duration']['value'])
# print(route['overview_polyline']['points'])
# location = api.findLocation('Dotonbori japan')
# print("lat: %f, lng: %f" % (location['lat'], location['lng']))
# attractions_ = api.searchNearby('tourist_attraction', lat_, lng_)
# for attraction in attractions_:
#     print(attraction['name'])
# print(api.findHotel('Dotonbori japan', location['lat'], location['lng'], 'transit'))
# print(api.findPhoneNum('ChIJ7yglkB6oQjQRbTrDqneWpAA'))
# print(api.findAttraction('taiwan', 'airport'))
# print(api.genRoute('藝奇新日本料理桃園南華店', 'I Do Motel', 'driving'))