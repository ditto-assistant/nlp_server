import requests
import geocoder

coordinates = geocoder.ip('me').latlng  

# Get the coordinates from the user
lat = coordinates[0]
lng = coordinates[1]

# Make a request to the Google Maps API
url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(lat) + "," + str(lng) + "&key=YOUR_API_KEY"
response = requests.get(url)

# Parse the response
data = response.json()
zip_code = data["results"][0]["address_components"][1]["long_name"]

# Print the zip code
print("The zip code for the coordinates (lat, lng) = (" + str(lat) + ", " + str(lng) + ") is " + zip_code)

