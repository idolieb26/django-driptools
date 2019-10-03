#!/home/gf/.virtualenvs/gf/bin/python
# coding: utf-8
# vim:softtabstop=4:ts=4:sw=4:expandtab:tw=120
import googlemaps
from googlemaps.exceptions import ApiError, HTTPError, Timeout, TransportError
from datetime import datetime

import math

def getUserInput(title, options, keys):
    while True:
        print title
        for opt in options:
            print "\t{}".format(opt)
        print "\t(x) Exit"

        if not (len(ans)==1 and ans in keys):
            print ("Invalid input.")
            continue
        break
    if ans=="x":
        sys.exit()
    return ans


def getDistance():
    """ Get Stuff """

    # sel = raw_input ("Enter address:")
    # print ("sel: {}".format(sel))

    try:
        gmaps = googlemaps.Client(key="AIzaSyCMhcLeZf1t4x2HJbdrn-23jHAX7KzYpaw")
    except ValueError as ve:
        print ("Value Error!. {}".format(ve))
    except NoImplementedError as ni:
        print ("NoImplementedError!. {}".format(ni))

    print ("Authenticated")

    try:
        # Geocoding an address
        # geocode_result = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')
        # print (geocode_result)

        # print ("------------------------------------------------\n\n")
        # # Look up an address with reverse geocoding
        # reverse_geocode_result = gmaps.reverse_geocode((40.714224, -73.961452))
        # print (reverse_geocode_result)
        # print ("------------------------------------------------\n\n")

        # Request directions via public transit
        # now = datetime.now()
        # directions_result = gmaps.directions("Sydney Town Hall",
        #                                      "Parramatta, NSW",
        #                                      mode="transit",
        #                                      departure_time=now)
        # print (directions_result)
        print ("\ndistance_matrix:\n")

        # origins = ["84003",]
        origins = [(40.450080, -111.799720)]
        # origins = ["5896 W. Century Heights Drive, Highland, Utah  84003",]
        destinations = ["1136 Birch Lane, Provo Utah, 84604", "990 Cedar Avenue, Provo Utah, 84604",
                        "Salt Lake City, Utah", "2111 NE 25th Ave., Hillsboro OR 97113",
                        "964 Oleander St., Cornelius OR 97113"]

        distance_matrix = gmaps.distance_matrix(origins=origins,
                                                destinations = destinations,
                                                mode = "driving",  # walking, transit, bicycling
                                                units="imperial",  # metric
                                                departure_time=datetime.now())
        showResults (distance_matrix)
    except ApiError as ae:
        print ("ApiError {}".format(ae))
    except HTTPError as ex:
        print ("HTTPError. An unexpected HTTP error occurred.: {}".format(ex))
    except Timeout as ex:
        print ("Timeout. : {}".format(ex))
    except TransportError as ex:
        print ("TransportError. Something went wrong while trying to execute the request.: {}".format(ex))

        # Google Maps parameters:
        # origins (a single location, or a list of locations, where a location is a string, dict, list, or tuple) – One or more locations and/or latitude/longitude values, from which to calculate distance and time. If you pass an address as a string, the service will geocode the string and convert it to a latitude/longitude coordinate to calculate directions.
        # destinations (a single location, or a list of locations, where a location is a string, dict, list, or tuple) – One or more addresses and/or lat/lng values, to which to calculate distance and time. If you pass an address as a string, the service will geocode the string and convert it to a latitude/longitude coordinate to calculate directions.
        # mode (string) – Specifies the mode of transport to use when calculating directions. Valid values are “driving”, “walking”, “transit” or “bicycling”.
        # language (string) – The language in which to return results.
        # avoid (string) – Indicates that the calculated route(s) should avoid the indicated features. Valid values are “tolls”, “highways” or “ferries”.
        # units (string) – Specifies the unit system to use when displaying results. Valid values are “metric” or “imperial”.
        # departure_time (int or datetime.datetime) – Specifies the desired time of departure.
        # arrival_time (int or datetime.datetime) – Specifies the desired time of arrival for transit directions. Note: you can’t specify both departure_time and arrival_time.
        # transit_mode (string or list of strings) – Specifies one or more preferred modes of transit. This parameter may only be specified for requests where the mode is transit. Valid values are “bus”, “subway”, “train”, “tram”, “rail”. “rail” is equivalent to [“train”, “tram”, “subway”].
        # transit_routing_preference (string) – Specifies preferences for transit requests. Valid values are “less_walking” or “fewer_transfers”.
        # traffic_model – Specifies the predictive travel time model to use. Valid values are “best_guess” or “optimistic” or “pessimistic”. The traffic_model parameter may only be specified for requests where the travel mode is driving, and where the request includes a departure_time.
        # region (string) – Specifies the prefered region the geocoder should search first, but it will not restrict the results to only this region. Valid values are a ccTLD code.

        # Return type:
        #  matrix of distances. Results are returned in rows, each row containing one origin paired with each destination.


def showResults(results):
    for o,origin in enumerate(results["origin_addresses"]):
        for d,dest in enumerate(results["destination_addresses"]):
            info = results["rows"][o]["elements"][d]
            showdistance = int(math.ceil(float(info["distance"]["text"].replace('mi', ''))))
            showdistance = str(showdistance) + ' mi'
            print ("{} to {}\n\tduration: {}\n\tdistance: {}\n"\
                   .format(origin, dest, info["duration"]["text"], showdistance))


# ---------------------------------------------------------------------------
def main():
    try:
        getDistance()
        # results = {u'status': u'OK', u'rows': [{u'elements': [{u'duration': {u'text': u'15 hours 0 mins', u'value': 53998}, u'distance': {u'text': u'950 mi', u'value': 1528179}, u'duration_in_traffic': {u'text': u'15 hours 26 mins', u'value': 55563}, u'status': u'OK'}, {u'duration': {u'text': u'3 hours 4 mins', u'value': 11044}, u'distance': {u'text': u'71.0 mi', u'value': 114190}, u'duration_in_traffic': {u'text': u'2 hours 53 mins', u'value': 10359}, u'status': u'OK'}]}, {u'elements': [{u'duration': {u'text': u'12 hours 33 mins', u'value': 45187}, u'distance': {u'text': u'808 mi', u'value': 1299785}, u'duration_in_traffic': {u'text': u'13 hours 10 mins', u'value': 47401}, u'status': u'OK'}, {u'duration': {u'text': u'4 hours 32 mins', u'value': 16308}, u'distance': {u'text': u'107 mi', u'value': 172218}, u'duration_in_traffic': {u'text': u'4 hours 23 mins', u'value': 15770}, u'status': u'OK'}]}], u'destination_addresses': [u'San Francisco, CA, USA', u'Victoria, BC, Canada'], u'origin_addresses': [u'Vancouver, BC, Canada', u'Seattle, WA, USA']}

        # showResults(results)
    except KeyboardInterrupt:
        print ""
        pass

if __name__ == "__main__":
    main()
