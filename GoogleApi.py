import googlemaps
import googlemaps.directions
import googlemaps.places
import operator
import datetime
import requests

class API():
    def __init__(self, transportMode=str):
        self.api_key = "AIzaSyCrJ9yz3Z5_ob__LeGpJt2tidtzM8UXqxo"
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
        parms = (name, self.api_key)
        string = 'https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=%s' % parms
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

    def genRoute(self, startName, endName):
        # there are 4 mode: driving, walking, bicycling, transit
        direction = self.client.directions(origin=startName,
                                            destination=endName,
                                            mode=self.transportMode,
                                            avoid='ferries',
                                            departure_time=datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day, hour = 14, minute = 00))
        return direction[0]

    def findPlaceBy(self, googleID):
        # Valid values for the `fields` param for `find_place` are 'geometry/viewport/southwest', 
        # 'permanently_closed', 'geometry/viewport', 'icon', 'geometry/viewport/northeast/lng', 
        # 'geometry/viewport/southwest/lng', 'geometry/location', 'geometry/viewport/northeast/lat', 
        # 'geometry/location/lng', 'name', 'price_level', 'types', 'photos', 
        # 'geometry/viewport/northeast', 'geometry/viewport/southwest/lat', 'plus_code', 'rating', 
        # 'formatted_address', 'opening_hours', 'place_id', 'geometry', 'user_ratings_total', 
        # 'geometry/location/lat'
        address = self.client.reverse_geocode(self.findLocation(googleID))[0]['formatted_address']
        return self.client.find_place(address, 'textquery', fields=['place_id', 'name', 
                                     'geometry/location', 'photos', 'formatted_address', 
                                     'rating', 'types', 'photos'], language='en')['candidates'][0]

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
        

# api = API()
# a= api.findAttraction("The Harbourview")
# print(a)
# route = api.genRoute('Dotonbori', 'Osaka Castle Park', 'transit')
# print(route[0]['overview_polyline']['points'])
# location = api.findLocation('Dotonbori japan')
# print("lat: %f, lng: %f" % (location['lat'], location['lng']))
# attractions_ = api.searchNearby('tourist_attraction', lat_, lng_)
# for attraction in attractions_:
#     print(attraction['name'])
# print(api.findHotel('Dotonbori japan', location['lat'], location['lng'], 'transit'))
# print(api.findPhoneNum('ChIJ7yglkB6oQjQRbTrDqneWpAA'))
# print(api.findAttraction('taiwan', 'airport'))
# print(api.genRoute('藝奇新日本料理桃園南華店', 'I Do Motel', 'driving'))