import os
import requests
from typing import List, Dict, Optional, Any

INFRASTRUCTURE_CATEGORIES = {
    "Супермаркеты": "супермаркет",
    "Торговые центры": "тц",
    "Школы": "школа",
    "Станции метро": "метро",
    "Спортзалы и фитнес-клубы": "спортзал, фитнес",
    "Рестораны и кафе": "ресторан, кафе",
    "Парки": "парк",
}

class TwoGisClient:
    """
    A client for interacting with the 2GIS API.
    It can be used to find coordinates for a given address and
    search for nearby places within a specified radius, including the distance to them.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("2GIS API key is required.")
        self.api_key = api_key
        # Note: geocode is a special endpoint, so we handle it separately
        self.places_api_url = "https://catalog.api.2gis.com/3.0/items"
        self.routing_api_url = "https://routing.api.2gis.com/get_dist_matrix"

    def _get_coordinates(self, address: str) -> Optional[Dict[str, float]]:
        """
        Converts a textual address to geographic coordinates (latitude and longitude).
        """
        params = {
            "q": address,
            "key": self.api_key,
            "fields": "items.point",
        }
        try:
            # The geocode endpoint is a path under the main places API url
            response = requests.get(f"{self.places_api_url}/geocode", params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("meta", {}).get("code") == 200 and data.get("result", {}).get("items"):
                point = data["result"]["items"][0]["point"]
                return {"lat": point["lat"], "lon": point["lon"]}
        except requests.exceptions.RequestException as e:
            print(f"Error fetching coordinates: {e}")
        except (KeyError, IndexError) as e:
            print(f"Could not parse coordinates from response: {e}")
        return None

    def _get_distances(self, start_point: Dict[str, float], places: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculates distances from a start point to a list of places using the Distance Matrix API.
        """
        if not places:
            return {}

        # The first point is our origin. The rest are destinations.
        points_payload = [{"lat": start_point["lat"], "lon": start_point["lon"]}]
        # Keep track of which place corresponds to which index in the payload
        place_id_map = []
        for place in places:
            if place.get("point"):
                points_payload.append({"lat": place["point"]["lat"], "lon": place["point"]["lon"]})
                place_id_map.append(place["id"])

        if len(points_payload) <= 1:
            return {}

        payload = {
            "points": points_payload,
            "sources": [0],
            "targets": list(range(1, len(points_payload))),
        }
        
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key, "version": "2.0"}

        try:
            response = requests.post(self.routing_api_url, json=payload, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            distances = {}
            if "routes" in data:
                # The routes are returned in the order of the targets
                for i, route in enumerate(data["routes"]):
                    place_id = place_id_map[i]
                    if place_id and route.get("status") == "OK":
                        distances[place_id] = route["distance"]
                return distances
        except requests.exceptions.RequestException as e:
            print(f"Error fetching distances: {e}")
        except (KeyError, IndexError) as e:
            print(f"Could not parse distances from response: {e}")
            
        return {}
    
    def _find_nearby_with_distances(self, start_coords: Dict[str, float], query: str, radius_meters: int) -> List[Dict[str, Any]]:
        """
        Internal method to find places using coordinates and calculate distances.
        """
        # Step 1: Find places
        places_params = {
            "q": query,
            "point": f"{start_coords['lon']},{start_coords['lat']}",
            "radius": radius_meters,
            "key": self.api_key,
            "fields": "items.point,items.name,items.purpose_name,items.id",
        }
        
        found_places = []
        try:
            response = requests.get(self.places_api_url, params=places_params)
            response.raise_for_status()
            data = response.json()
            if data.get("meta", {}).get("code") == 200 and data.get("result", {}).get("items"):
                found_places = data["result"]["items"]
        except requests.exceptions.RequestException as e:
            print(f"Error searching for '{query}': {e}")
            return []

        if not found_places:
            return []

        # Step 2: Get distances for found places
        distances = self._get_distances(start_coords, found_places)

        # Step 3: Combine places with their distances
        for place in found_places:
            place["distance"] = distances.get(place["id"])
        
        # Filter by radius and sort by distance
        found_places = [p for p in found_places if p.get("distance") is not None and p["distance"] <= radius_meters]
        found_places.sort(key=lambda p: p.get('distance', float('inf')))

        return found_places

    def get_infrastructure_summary(self, address: str, radius_meters: int = 1000) -> Dict[str, List[Dict[str, Any]]]:
        """
        Searches for a predefined list of infrastructure categories and returns a structured summary.
        """
        start_coords = self._get_coordinates(address)
        if not start_coords:
            print(f"Could not find coordinates for address: {address}")
            return {}
        
        infrastructure_summary = {}
        print(f"\nSearching for infrastructure within {radius_meters}m of {address}...\n")
        
        for category_name, query in INFRASTRUCTURE_CATEGORIES.items():
            print(f"-> Searching for: {category_name}")
            places = self._find_nearby_with_distances(start_coords, query, 2*radius_meters)
            
            if places:
                # Format the output to be just name and distance
                formatted_places = [
                    {"name": p.get("name"), "distance": p.get("distance")}
                    for p in places
                ]
                infrastructure_summary[category_name] = formatted_places
        
        return infrastructure_summary


if __name__ == '__main__':
    API_KEY = os.environ.get("TWOGIS_API_KEY")
    if not API_KEY:
        print("Please set the TWOGIS_API_KEY environment variable.")
    else:
        client = TwoGisClient(api_key=API_KEY)
        test_address = "Москва, ул. Тверская, 6"
        
        summary = client.get_infrastructure_summary(test_address)
        
        print("\n--- INFRASTRUCTURE SUMMARY ---")
        if summary:
            for category, places in summary.items():
                print(f"\n[{category}]")
                if places:
                    for place in places:
                        print(f"  - {place['name']} ({place['distance']}m)")
                else:
                    print("  - Not found nearby.")
        else:
            print("Could not retrieve infrastructure summary.") 