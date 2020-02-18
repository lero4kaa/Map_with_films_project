import os
os.environ["MAPQUEST_API_KEY"] = "w89COg4k1MUAjuvVeSwLaNclGg0nWKf9"
import geocoder
import folium
import geopy.distance
import pandas
import sys


def getting_film_name_address(line):
    """
    str -> str, str
    Function takes line and returns name of film and address,
    were it was filmed.
    >>> getting_film_name_address('Wolfe von Lenkiewicz (2013)33 Portland Place, Marylebone, London, England, UK')
    ('Wolfe von Lenkiewicz ', '33 Portland Place, Marylebone, London, England, UK')
    """
    end_of_name = line.index('(')
    film = line[0:end_of_name]
    start_of_address = line.index(')')
    address = line[start_of_address+1:]
    if "}" in address:
        start_of_address = address.index('}')
        address = address[start_of_address + 1:]
    if "\t" in address:
        start_of_address = address.index("\t")
        address = address[start_of_address + 1:]
    if "(" in address:
        end_of_address = address.index("(")
        address = address[:end_of_address]
    address = address.strip()

    return film, address


def measure_distance(user_lat, user_lng, film_lat, film_lng):
    """
    float, float, float, float -> number
    Function returns the distance between to locations on the
    map. Locations are set by coordinates.
    >>> measure_distance('51.5074', '-0.1278', '49.8397', '24.0297')
    1709.8232550253047
    """
    coords_user = (user_lat, user_lng)
    coords_film = (film_lat, film_lng)
    distance = geopy.distance.geodesic(coords_user, coords_film).km

    return distance


def find_coordinates(address):
    """
    str -> float, float
    Function returns coordinates of given address.
    >>> find_coordinates('London, UK')
    (51.50015, -0.12624)
    """
    coordinates = geocoder.mapquest(address)
    film_lat = coordinates.json['lat']
    film_lng = coordinates.json['lng']

    return film_lat, film_lng


def find_capitals():
    """
    () -> Series, Series
    Functions returns coordinates of all capitals in the world.
    """
    data = pandas.read_csv('country-capitals.csv')
    capitals_lat = data['CapitalLatitude']
    capitals_lng = data['CapitalLongitude']

    return capitals_lat, capitals_lng


year = input("Please enter a year you would like to have a map for:")
lt = float(input("Please enter latitude of your location "))
lg = float(input("Please enter longitude of your location "))
print("Please wait, map is generating....")
m = folium.Map(location=[lt, lg], zoom_start=11)

g = geocoder.mapquest([lt, lg], method='reverse')
location = g.city


f = open('locations.txt', encoding='utf-8')
lines = f.readlines()
f.close()

films = dict()

for line in lines:
    if (location in line) and (year in line):
        film_name, address = getting_film_name_address(line)
        films[film_name] = address

if len(films) == 0:
    print("There were no movies, filmed at that time in your city."
          "Please, restart program and enter another year or another "
          "location.")
    sys.exit()


distance_from_films = dict()
for element in films.keys():
    film_lat, film_lng = find_coordinates(films[element])
    distance = measure_distance(lt, lg, film_lat, film_lng)
    distance_from_films[element] = (distance, element, film_lng, film_lat)
    if distance_from_films[element][0] > 100:
        del(distance_from_films[element])


lst_distances = list(distance_from_films.values())
lst_distances = sorted(lst_distances)


if len(lst_distances) > 10:
    length_lst_distances = 10
else:
    length_lst_distances = len(lst_distances)

fg_films = folium.FeatureGroup(name="Films")
used_coordinates = set()
used_coordinates.add((lt, lg))
for i in range(length_lst_distances):
    if (lst_distances[i][3], lst_distances[i][2]) not in used_coordinates:
        film_lat, film_lng = lst_distances[i][3], lst_distances[i][2]
        used_coordinates.add((film_lat, film_lng))
    else:
        film_lat, film_lng = lst_distances[i][3] + 0.0001*i, \
                             lst_distances[i][2] + 0.0001*i
        used_coordinates.add((film_lat, film_lng))
    fg_films.add_child(folium.Marker([film_lat, film_lng],
                                     popup="{}".format(lst_distances[i][1]),
                                     icon=folium.Icon()))

m.add_child(folium.Marker([lt, lg],
                          popup="{}".format('You are here'),
                          icon=folium.Icon(color='green')))

m.add_child(fg_films)

capital_lat, capital_lng = find_capitals()

fg_capitals = folium.FeatureGroup(name="Capitals")
for i in range(len(capital_lng)):
    fg_capitals.add_child(folium.CircleMarker(location=[capital_lat[i],
                                                        capital_lng[i]],
                                              radius=10,
                                              fill_color='red',
                                              color='red',
                                              fill_opacity=0.5))

m.add_child(fg_capitals)

m.add_child(folium.LayerControl())
m.save('map_with_films.html')
print("You can see map at map_with_films.html")
