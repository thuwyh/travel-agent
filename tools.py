"""
Tool definitions and mock implementations for the Travel Assistant Agent.

This file contains:
  1. ALL_TOOLS  — OpenAI function-calling tool definitions (20 tools)
  2. TOOL_REGISTRY — name -> async implementation mapping

You should NOT need to modify this file for the interview.
Read it if you need to understand what tools are available.
"""

import asyncio
import random
import json
from typing import Any, Dict, List

# ===========================================================================
# 20 Tool Definitions — all crammed into one list, sent on every call
# ===========================================================================

ALL_TOOLS: List[Dict[str, Any]] = [
    # ---- Flights ----
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": (
                "Search for available flights between two cities. Supports one-way and round-trip. "
                "Returns a list of flights with prices, airlines, departure/arrival times, number of stops, "
                "and available seat classes. You should use this tool whenever the user wants to find flights, "
                "compare flight options, or check flight availability for specific dates. This tool queries "
                "multiple airline databases and aggregators to find the best options. Results are sorted by "
                "price by default but can be filtered by various criteria including number of stops, "
                "preferred airlines, departure time ranges, and cabin class preferences."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Departure city or IATA airport code (e.g. 'New York' or 'JFK')"},
                    "destination": {"type": "string", "description": "Arrival city or IATA airport code (e.g. 'London' or 'LHR')"},
                    "departure_date": {"type": "string", "description": "Departure date in YYYY-MM-DD format"},
                    "return_date": {"type": "string", "description": "Return date in YYYY-MM-DD format, omit for one-way"},
                    "passengers": {"type": "integer", "description": "Number of passengers, default is 1"},
                    "cabin_class": {
                        "type": "string",
                        "enum": ["economy", "premium_economy", "business", "first"],
                        "description": "Preferred cabin class for the flight booking",
                    },
                },
                "required": ["origin", "destination", "departure_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_flight",
            "description": (
                "Book a specific flight that was previously found via search_flights. This tool handles "
                "the complete booking process including seat selection, passenger details collection, "
                "payment processing, and confirmation email sending. You must have a flight_id from a "
                "previous search_flights call. The tool will return a booking confirmation number and "
                "complete itinerary details. Make sure the user has confirmed all details before booking."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "flight_id": {"type": "string", "description": "The unique flight identifier from search results"},
                    "passenger_name": {"type": "string", "description": "Full name of the passenger as it appears on their travel document"},
                    "passenger_email": {"type": "string", "description": "Email address for booking confirmation"},
                    "payment_method": {"type": "string", "enum": ["credit_card", "debit_card", "paypal"], "description": "Payment method"},
                },
                "required": ["flight_id", "passenger_name", "passenger_email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_flight",
            "description": (
                "Cancel a previously booked flight using the booking reference number. This tool checks "
                "the cancellation policy, calculates any applicable refund amount based on the airline's "
                "policy and the time remaining before departure, and processes the cancellation. It returns "
                "the cancellation confirmation and refund details. Note that some flights may have "
                "non-refundable components."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_reference": {"type": "string", "description": "The booking confirmation number"},
                    "reason": {"type": "string", "description": "Reason for cancellation (optional)"},
                },
                "required": ["booking_reference"],
            },
        },
    },
    # ---- Hotels ----
    {
        "type": "function",
        "function": {
            "name": "search_hotels",
            "description": (
                "Search for available hotels in a specific city or area for given dates. Returns hotel "
                "listings with name, star rating, price per night, location, amenities, guest ratings, "
                "and room availability. Supports filters for price range, star rating, amenities "
                "(pool, gym, spa, WiFi, parking, restaurant), and distance from city center. Results "
                "include photos and detailed descriptions. Use this whenever the user needs accommodation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name or area to search"},
                    "check_in": {"type": "string", "description": "Check-in date YYYY-MM-DD"},
                    "check_out": {"type": "string", "description": "Check-out date YYYY-MM-DD"},
                    "guests": {"type": "integer", "description": "Number of guests"},
                    "rooms": {"type": "integer", "description": "Number of rooms needed"},
                    "star_rating": {"type": "integer", "description": "Minimum star rating (1-5)"},
                    "max_price": {"type": "number", "description": "Maximum price per night in USD"},
                },
                "required": ["city", "check_in", "check_out"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_hotel",
            "description": (
                "Book a hotel room at a previously searched hotel. Requires hotel_id from search results. "
                "Handles room selection, guest registration, special requests (early check-in, extra bed, "
                "high floor, quiet room), payment processing, and confirmation. Returns booking ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "string", "description": "Hotel identifier from search results"},
                    "room_type": {"type": "string", "description": "Room type (standard, deluxe, suite)"},
                    "guest_name": {"type": "string", "description": "Primary guest full name"},
                    "guest_email": {"type": "string", "description": "Email for confirmation"},
                    "special_requests": {"type": "string", "description": "Any special requests"},
                },
                "required": ["hotel_id", "guest_name", "guest_email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_hotel",
            "description": (
                "Cancel a hotel reservation. Checks cancellation policy (free cancellation deadline, "
                "partial refund periods, non-refundable periods) and processes accordingly. Returns "
                "cancellation status, refund amount, and timeline for refund processing."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {"type": "string", "description": "Hotel booking confirmation number"},
                    "reason": {"type": "string", "description": "Reason for cancellation"},
                },
                "required": ["booking_id"],
            },
        },
    },
    # ---- Weather ----
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": (
                "Get the weather forecast for a specific city for the next 7 days. Returns daily "
                "forecasts including temperature (high/low), precipitation probability, wind speed, "
                "humidity, UV index, and a general weather description. Also includes sunrise/sunset "
                "times and packing suggestions based on the weather. Useful for trip planning to help "
                "users decide what to pack and which activities are weather-appropriate."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "days": {"type": "integer", "description": "Number of days (1-14, default 7)"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": (
                "Get the current real-time weather conditions for a city. Returns temperature, "
                "feels-like temperature, weather condition, humidity, wind speed/direction, "
                "visibility, air quality index, and UV index."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                },
                "required": ["city"],
            },
        },
    },
    # ---- Restaurants ----
    {
        "type": "function",
        "function": {
            "name": "search_restaurants",
            "description": (
                "Search for restaurants in a specific area. Returns restaurant listings with name, "
                "cuisine type, price range, rating, address, hours, menu highlights, dietary options "
                "(vegetarian, vegan, gluten-free, halal, kosher), and reservation availability. "
                "Supports filters for cuisine type, price level, rating, distance, and dietary needs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City or neighborhood"},
                    "cuisine": {"type": "string", "description": "Cuisine type (italian, japanese, etc.)"},
                    "price_level": {"type": "string", "enum": ["$", "$$", "$$$", "$$$$"], "description": "Price range"},
                    "dietary": {"type": "string", "description": "Dietary requirements"},
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "make_restaurant_reservation",
            "description": (
                "Make a reservation at a restaurant. Requires restaurant_id from search. Handles "
                "table selection, party size, date/time, special requests (window seat, birthday "
                "setup, high chair). Returns confirmation number and details."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_id": {"type": "string", "description": "Restaurant ID from search"},
                    "date": {"type": "string", "description": "Reservation date YYYY-MM-DD"},
                    "time": {"type": "string", "description": "Reservation time HH:MM"},
                    "party_size": {"type": "integer", "description": "Number of diners"},
                    "guest_name": {"type": "string", "description": "Name for the reservation"},
                    "special_requests": {"type": "string", "description": "Special requests"},
                },
                "required": ["restaurant_id", "date", "time", "party_size", "guest_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_reservation",
            "description": "Cancel a restaurant reservation by confirmation number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "confirmation_number": {"type": "string", "description": "Reservation confirmation number"},
                },
                "required": ["confirmation_number"],
            },
        },
    },
    # ---- Attractions / Activities ----
    {
        "type": "function",
        "function": {
            "name": "search_attractions",
            "description": (
                "Search for tourist attractions, landmarks, and points of interest in a city. "
                "Returns name, type (museum, park, monument, etc.), rating, opening hours, ticket "
                "prices, estimated visit duration, accessibility info, and tips. Useful for building "
                "itineraries and discovering things to do."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City to search"},
                    "category": {
                        "type": "string",
                        "enum": ["museum", "park", "monument", "market", "entertainment", "nature", "all"],
                        "description": "Category filter",
                    },
                    "max_results": {"type": "integer", "description": "Max results to return (default 10)"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_activities",
            "description": (
                "Search for bookable activities and tours (city tours, cooking classes, snorkeling, "
                "hiking, wine tasting, etc.) in a destination. Returns activity details with prices, "
                "duration, availability, included items, meeting points, and cancellation policy."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string", "description": "Destination city"},
                    "activity_type": {"type": "string", "description": "Type of activity"},
                    "date": {"type": "string", "description": "Preferred date YYYY-MM-DD"},
                    "participants": {"type": "integer", "description": "Number of participants"},
                },
                "required": ["destination"],
            },
        },
    },
    # ---- Transportation ----
    {
        "type": "function",
        "function": {
            "name": "get_directions",
            "description": (
                "Get directions and route information between two locations. Returns step-by-step "
                "directions, estimated travel time, distance, and transportation options (driving, "
                "walking, public transit, cycling). Includes real-time traffic data and alternative "
                "routes. For public transit, shows specific bus/train lines, stops, and transfers."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Starting location"},
                    "destination": {"type": "string", "description": "Destination location"},
                    "mode": {
                        "type": "string",
                        "enum": ["driving", "walking", "transit", "cycling"],
                        "description": "Transportation mode",
                    },
                },
                "required": ["origin", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_car_rentals",
            "description": (
                "Search for car rental options at a specific location. Returns available vehicles "
                "with type, daily rate, total cost, rental company, pickup/dropoff locations, "
                "insurance options, fuel policy, and mileage limits."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pickup_location": {"type": "string", "description": "Pickup city or airport code"},
                    "pickup_date": {"type": "string", "description": "Pickup date YYYY-MM-DD"},
                    "return_date": {"type": "string", "description": "Return date YYYY-MM-DD"},
                    "car_type": {
                        "type": "string",
                        "enum": ["economy", "compact", "midsize", "full_size", "suv", "luxury", "van"],
                        "description": "Preferred car type",
                    },
                },
                "required": ["pickup_location", "pickup_date", "return_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_car_rental",
            "description": "Book a car rental. Requires car_rental_id from search results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "car_rental_id": {"type": "string", "description": "Car rental option ID from search"},
                    "driver_name": {"type": "string", "description": "Driver full name"},
                    "driver_email": {"type": "string", "description": "Driver email"},
                    "insurance": {"type": "string", "enum": ["basic", "full", "none"], "description": "Insurance option"},
                },
                "required": ["car_rental_id", "driver_name", "driver_email"],
            },
        },
    },
    # ---- Utilities ----
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": (
                "Convert an amount from one currency to another using real-time exchange rates. "
                "Supports all major world currencies. Returns the converted amount, exchange rate, "
                "and rate timestamp. Also shows the inverse rate and a mini historical chart "
                "description of the rate trend over the past 30 days."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Amount to convert"},
                    "from_currency": {"type": "string", "description": "Source currency code (e.g. USD)"},
                    "to_currency": {"type": "string", "description": "Target currency code (e.g. EUR)"},
                },
                "required": ["amount", "from_currency", "to_currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "translate_text",
            "description": (
                "Translate text between languages. Supports 50+ languages. Returns the translated "
                "text, detected source language (if not specified), and a pronunciation guide "
                "for the target language. Also provides common alternative translations and "
                "cultural context notes when relevant."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to translate"},
                    "target_language": {"type": "string", "description": "Target language code (e.g. 'es', 'zh', 'ja')"},
                    "source_language": {"type": "string", "description": "Source language code (auto-detected if omitted)"},
                },
                "required": ["text", "target_language"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_travel_advisory",
            "description": (
                "Get official travel advisory and safety information for a country or region. "
                "Returns advisory level (1-4), safety tips, health requirements (vaccinations, "
                "COVID policies), entry requirements (visa, passport validity), local laws to "
                "be aware of, emergency contacts, and embassy/consulate locations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {"type": "string", "description": "Country name or ISO code"},
                    "nationality": {"type": "string", "description": "Traveler's nationality for visa info"},
                },
                "required": ["country"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_visa_requirements",
            "description": (
                "Check visa requirements for traveling to a specific country based on your "
                "nationality. Returns whether a visa is needed, visa types available, application "
                "process, required documents, processing time, fees, and links to official "
                "application portals."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "destination_country": {"type": "string", "description": "Country you plan to visit"},
                    "nationality": {"type": "string", "description": "Your passport nationality"},
                    "purpose": {
                        "type": "string",
                        "enum": ["tourism", "business", "transit", "study"],
                        "description": "Purpose of visit",
                    },
                },
                "required": ["destination_country", "nationality"],
            },
        },
    },
]


# ===========================================================================
# Mock tool implementations (simulate real API calls)
# ===========================================================================

async def search_flights(origin, destination, departure_date, **kw):
    await asyncio.sleep(0.8)
    cabin = kw.get("cabin_class", "economy")
    multiplier = {"economy": 1.0, "premium_economy": 1.6, "business": 3.2, "first": 5.5}.get(cabin, 1.0)
    return {"flights": [
        {"flight_id": "FL-UA789", "airline": "United Airlines", "price": round(452.00 * multiplier, 2),
         "stops": 0, "duration": "11h 15m", "cabin_class": cabin,
         "departure": f"{departure_date} 08:30", "arrival": f"{departure_date} 19:45"},
        {"flight_id": "FL-DL234", "airline": "Delta", "price": round(378.50 * multiplier, 2),
         "stops": 1, "stop_cities": ["Seattle"], "duration": "15h 20m", "cabin_class": cabin,
         "departure": f"{departure_date} 11:00", "arrival": f"{departure_date} 02:20+1"},
        {"flight_id": "FL-AA567", "airline": "American Airlines", "price": round(510.00 * multiplier, 2),
         "stops": 0, "duration": "11h 25m", "cabin_class": cabin,
         "departure": f"{departure_date} 15:45", "arrival": f"{departure_date} 03:10+1"},
        {"flight_id": "FL-BA102", "airline": "British Airways", "price": round(425.00 * multiplier, 2),
         "stops": 0, "duration": "10h 55m", "cabin_class": cabin,
         "departure": f"{departure_date} 21:00", "arrival": f"{departure_date} 07:55+1"},
        {"flight_id": "FL-VS401", "airline": "Virgin Atlantic", "price": round(389.00 * multiplier, 2),
         "stops": 1, "stop_cities": ["Boston"], "duration": "14h 10m", "cabin_class": cabin,
         "departure": f"{departure_date} 09:15", "arrival": f"{departure_date} 23:25"},
        {"flight_id": "FL-LH417", "airline": "Lufthansa", "price": round(465.00 * multiplier, 2),
         "stops": 1, "stop_cities": ["Frankfurt"], "duration": "13h 40m", "cabin_class": cabin,
         "departure": f"{departure_date} 17:30", "arrival": f"{departure_date} 07:10+1"},
    ]}

async def book_flight(flight_id, passenger_name, passenger_email, **kw):
    await asyncio.sleep(0.5)
    return {"booking_reference": f"BK-{random.randint(100000,999999)}", "flight_id": flight_id,
            "passenger": passenger_name, "status": "confirmed"}

async def cancel_flight(booking_reference, **kw):
    await asyncio.sleep(0.3)
    return {"booking_reference": booking_reference, "status": "cancelled", "refund_amount": 378.50}

async def search_hotels(city, check_in, check_out, **kw):
    await asyncio.sleep(0.7)
    return {"hotels": [
        {"hotel_id": "HT-001", "name": "Grand Plaza Hotel", "stars": 4, "price_per_night": 189.00,
         "rating": 4.5, "location": f"Downtown {city}", "amenities": ["WiFi", "Pool", "Gym", "Restaurant"],
         "distance_to_center": "0.3 km", "free_cancellation": True},
        {"hotel_id": "HT-002", "name": "Comfort Inn Express", "stars": 3, "price_per_night": 109.00,
         "rating": 4.2, "location": f"Midtown {city}", "amenities": ["WiFi", "Breakfast", "Parking"],
         "distance_to_center": "1.8 km", "free_cancellation": True},
        {"hotel_id": "HT-003", "name": "The Ritz London", "stars": 5, "price_per_night": 450.00,
         "rating": 4.9, "location": f"Piccadilly, {city}", "amenities": ["WiFi", "Spa", "Pool", "Restaurant", "Concierge", "Valet"],
         "distance_to_center": "0.1 km", "free_cancellation": False},
        {"hotel_id": "HT-004", "name": "Budget Lodge", "stars": 2, "price_per_night": 62.00,
         "rating": 3.6, "location": f"East {city}", "amenities": ["WiFi"],
         "distance_to_center": "5.2 km", "free_cancellation": True},
        {"hotel_id": "HT-005", "name": "Boutique Art Hotel", "stars": 4, "price_per_night": 215.00,
         "rating": 4.7, "location": f"Soho, {city}", "amenities": ["WiFi", "Bar", "Restaurant", "Rooftop"],
         "distance_to_center": "0.5 km", "free_cancellation": True},
    ]}

async def book_hotel(hotel_id, guest_name, guest_email, **kw):
    await asyncio.sleep(0.4)
    return {"booking_id": f"HB-{random.randint(100000,999999)}", "hotel_id": hotel_id, "status": "confirmed"}

async def cancel_hotel(booking_id, **kw):
    await asyncio.sleep(0.3)
    return {"booking_id": booking_id, "status": "cancelled", "refund": "full"}

async def get_weather_forecast(city, **kw):
    await asyncio.sleep(0.4)
    return {"city": city, "forecast": [
        {"date": "2025-07-15", "high": 24, "low": 15, "condition": "Sunny", "rain_chance": 5, "wind_kmh": 12},
        {"date": "2025-07-16", "high": 22, "low": 14, "condition": "Partly Cloudy", "rain_chance": 25, "wind_kmh": 18},
        {"date": "2025-07-17", "high": 18, "low": 13, "condition": "Rain", "rain_chance": 85, "wind_kmh": 30},
        {"date": "2025-07-18", "high": 20, "low": 14, "condition": "Showers", "rain_chance": 60, "wind_kmh": 22},
        {"date": "2025-07-19", "high": 23, "low": 15, "condition": "Cloudy", "rain_chance": 30, "wind_kmh": 15},
        {"date": "2025-07-20", "high": 26, "low": 17, "condition": "Sunny", "rain_chance": 5, "wind_kmh": 8},
        {"date": "2025-07-21", "high": 27, "low": 18, "condition": "Sunny", "rain_chance": 0, "wind_kmh": 6},
    ], "packing_suggestion": "Pack an umbrella for July 17-18. Light layers otherwise."}

async def get_current_weather(city, **kw):
    await asyncio.sleep(0.2)
    return {"city": city, "temperature": 25, "feels_like": 27, "condition": "Sunny", "humidity": 55}

async def search_restaurants(location, **kw):
    await asyncio.sleep(0.5)
    return {"restaurants": [
        {"restaurant_id": "RS-001", "name": "La Bella Italia", "cuisine": "Italian", "price_level": "$$$",
         "rating": 4.7, "avg_cost_per_person": 55, "address": f"23 King St, {location}"},
        {"restaurant_id": "RS-002", "name": "Sakura Sushi", "cuisine": "Japanese", "price_level": "$$",
         "rating": 4.5, "avg_cost_per_person": 35, "address": f"88 Oxford St, {location}"},
        {"restaurant_id": "RS-003", "name": "The Ledbury", "cuisine": "Modern European", "price_level": "$$$$",
         "rating": 4.9, "avg_cost_per_person": 120, "address": f"127 Ledbury Rd, {location}"},
        {"restaurant_id": "RS-004", "name": "Dishoom", "cuisine": "Indian", "price_level": "$$",
         "rating": 4.6, "avg_cost_per_person": 30, "address": f"5 Stable St, {location}"},
        {"restaurant_id": "RS-005", "name": "Borough Bites", "cuisine": "British", "price_level": "$",
         "rating": 4.3, "avg_cost_per_person": 18, "address": f"Borough Market, {location}"},
    ]}

async def make_restaurant_reservation(restaurant_id, date, time, party_size, guest_name, **kw):
    await asyncio.sleep(0.3)
    return {"confirmation_number": f"RR-{random.randint(10000,99999)}", "status": "confirmed"}

async def cancel_reservation(confirmation_number, **kw):
    await asyncio.sleep(0.2)
    return {"confirmation_number": confirmation_number, "status": "cancelled"}

async def search_attractions(city, **kw):
    await asyncio.sleep(0.5)
    return {"attractions": [
        {"name": "British Museum", "type": "museum", "rating": 4.8, "ticket_price": 0,
         "hours": "10:00-17:00", "visit_duration": "2-3 hours", "best_for": "rainy days"},
        {"name": "Tower of London", "type": "monument", "rating": 4.7, "ticket_price": 33,
         "hours": "09:00-17:30", "visit_duration": "3-4 hours", "best_for": "history lovers"},
        {"name": "Hyde Park", "type": "park", "rating": 4.6, "ticket_price": 0,
         "hours": "05:00-00:00", "visit_duration": "1-3 hours", "best_for": "sunny days"},
        {"name": "London Eye", "type": "entertainment", "rating": 4.4, "ticket_price": 35,
         "hours": "10:00-20:00", "visit_duration": "1 hour", "best_for": "clear weather"},
        {"name": "West End Theatre", "type": "entertainment", "rating": 4.9, "ticket_price": 75,
         "hours": "19:30-22:00", "visit_duration": "2.5 hours", "best_for": "evenings"},
        {"name": "Camden Market", "type": "market", "rating": 4.5, "ticket_price": 0,
         "hours": "10:00-18:00", "visit_duration": "2-3 hours", "best_for": "any weather"},
    ]}

async def search_activities(destination, **kw):
    await asyncio.sleep(0.5)
    return {"activities": [
        {"name": "City Walking Tour", "price": 35, "duration": "3 hours", "rating": 4.7,
         "time": "09:00", "weather_dependent": True, "min_participants": 1},
        {"name": "British Cooking Class", "price": 80, "duration": "4 hours", "rating": 4.9,
         "time": "10:00", "weather_dependent": False, "min_participants": 2},
        {"name": "Thames River Cruise", "price": 45, "duration": "2 hours", "rating": 4.6,
         "time": "14:00", "weather_dependent": True, "min_participants": 1},
        {"name": "Harry Potter Studio Tour", "price": 55, "duration": "4 hours", "rating": 4.8,
         "time": "10:00", "weather_dependent": False, "min_participants": 1},
        {"name": "Pub Crawl", "price": 25, "duration": "3 hours", "rating": 4.4,
         "time": "19:00", "weather_dependent": False, "min_participants": 1},
    ]}

async def get_directions(origin, destination, **kw):
    await asyncio.sleep(0.3)
    mode = kw.get("mode", "driving")
    return {"origin": origin, "destination": destination, "mode": mode,
            "distance": "15.3 km", "duration": "22 min" if mode == "driving" else "45 min"}

async def search_car_rentals(pickup_location, pickup_date, return_date, **kw):
    await asyncio.sleep(0.6)
    # Calculate days for total
    days = 4  # default
    try:
        from datetime import datetime
        d1 = datetime.strptime(pickup_date, "%Y-%m-%d")
        d2 = datetime.strptime(return_date, "%Y-%m-%d")
        days = max((d2 - d1).days, 1)
    except Exception:
        pass
    return {"rentals": [
        {"car_rental_id": "CR-001", "company": "Hertz", "car": "Toyota Corolla", "type": "compact",
         "daily_rate": 45, "total": 45 * days, "insurance_included": False},
        {"car_rental_id": "CR-002", "company": "Enterprise", "car": "Ford Explorer", "type": "suv",
         "daily_rate": 75, "total": 75 * days, "insurance_included": True},
        {"car_rental_id": "CR-003", "company": "Avis", "car": "VW Golf", "type": "compact",
         "daily_rate": 38, "total": 38 * days, "insurance_included": False},
    ]}

async def book_car_rental(car_rental_id, driver_name, driver_email, **kw):
    await asyncio.sleep(0.4)
    return {"booking_id": f"CRB-{random.randint(10000,99999)}", "status": "confirmed"}

async def convert_currency(amount, from_currency, to_currency, **kw):
    await asyncio.sleep(0.2)
    rates = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.5, "CNY": 7.24}
    converted = amount / rates.get(from_currency.upper(), 1.0) * rates.get(to_currency.upper(), 1.0)
    return {"original": f"{amount} {from_currency}", "converted": f"{converted:.2f} {to_currency}"}

async def translate_text(text, target_language, **kw):
    await asyncio.sleep(0.3)
    return {"original": text, "translated": f"[{target_language}] {text}", "target_language": target_language}

async def get_travel_advisory(country, **kw):
    await asyncio.sleep(0.3)
    return {"country": country, "advisory_level": 2, "advisory_text": "Exercise increased caution"}

async def get_visa_requirements(destination_country, nationality, **kw):
    await asyncio.sleep(0.3)
    return {"destination": destination_country, "nationality": nationality,
            "visa_required": True, "visa_type": "Tourist e-Visa", "fee": "$50"}


# ===========================================================================
# Additional tools — travel insurance, trains, events, local services, etc.
# ===========================================================================

# ---- Travel Insurance ----
async def search_travel_insurance(destination, trip_duration_days, travelers, **kw):
    await asyncio.sleep(0.3)
    return {"plans": [
        {"plan_id": "INS-001", "provider": "World Nomads", "coverage": "comprehensive",
         "price": 89.00, "medical_limit": 100000, "trip_cancel_limit": 5000},
        {"plan_id": "INS-002", "provider": "SafetyWing", "coverage": "basic",
         "price": 42.00, "medical_limit": 50000, "trip_cancel_limit": 1000},
        {"plan_id": "INS-003", "provider": "Allianz Travel", "coverage": "premium",
         "price": 134.00, "medical_limit": 250000, "trip_cancel_limit": 10000},
    ]}

async def buy_travel_insurance(plan_id, traveler_name, traveler_email, **kw):
    await asyncio.sleep(0.3)
    return {"policy_id": f"POL-{random.randint(100000,999999)}", "plan_id": plan_id, "status": "active"}

async def file_insurance_claim(policy_id, claim_type, description, amount, **kw):
    await asyncio.sleep(0.3)
    return {"claim_id": f"CLM-{random.randint(10000,99999)}", "status": "submitted", "estimated_review": "5-7 days"}

# ---- Train / Rail ----
async def search_trains(origin, destination, departure_date, **kw):
    await asyncio.sleep(0.5)
    return {"trains": [
        {"train_id": "TR-E301", "operator": "Eurostar", "price": 89.00, "duration": "2h 16m",
         "class": kw.get("travel_class", "standard"), "departure": f"{departure_date} 07:01", "arrival": f"{departure_date} 09:17"},
        {"train_id": "TR-E302", "operator": "Eurostar", "price": 125.00, "duration": "2h 16m",
         "class": "premier", "departure": f"{departure_date} 10:31", "arrival": f"{departure_date} 12:47"},
        {"train_id": "TR-T501", "operator": "Thalys", "price": 65.00, "duration": "3h 20m",
         "class": "standard", "departure": f"{departure_date} 08:25", "arrival": f"{departure_date} 11:45"},
    ]}

async def book_train(train_id, passenger_name, passenger_email, **kw):
    await asyncio.sleep(0.3)
    return {"booking_ref": f"TRB-{random.randint(10000,99999)}", "train_id": train_id, "status": "confirmed"}

async def cancel_train(booking_ref, **kw):
    await asyncio.sleep(0.2)
    return {"booking_ref": booking_ref, "status": "cancelled", "refund": "80%"}

# ---- Events / Concerts ----
async def search_events(city, date, **kw):
    await asyncio.sleep(0.4)
    return {"events": [
        {"event_id": "EV-001", "name": "West End: Hamilton", "venue": "Victoria Palace Theatre",
         "date": date, "time": "19:30", "price_from": 45, "category": "theatre"},
        {"event_id": "EV-002", "name": "Premier League: Arsenal vs Chelsea", "venue": "Emirates Stadium",
         "date": date, "time": "15:00", "price_from": 75, "category": "sports"},
        {"event_id": "EV-003", "name": "Jazz at Ronnie Scott's", "venue": "Ronnie Scott's",
         "date": date, "time": "20:00", "price_from": 35, "category": "music"},
        {"event_id": "EV-004", "name": "Stand-Up Comedy Night", "venue": "The Comedy Store",
         "date": date, "time": "20:30", "price_from": 20, "category": "comedy"},
    ]}

async def buy_event_tickets(event_id, quantity, attendee_name, attendee_email, **kw):
    await asyncio.sleep(0.3)
    return {"order_id": f"EVT-{random.randint(10000,99999)}", "event_id": event_id, "status": "confirmed"}

# ---- Airport Services ----
async def search_airport_lounges(airport_code, date, **kw):
    await asyncio.sleep(0.3)
    return {"lounges": [
        {"lounge_id": "LNG-001", "name": "Plaza Premium Lounge", "terminal": "T2",
         "price": 45, "amenities": ["food", "drinks", "wifi", "showers"]},
        {"lounge_id": "LNG-002", "name": "British Airways Galleries Club", "terminal": "T5",
         "price": 55, "amenities": ["food", "drinks", "wifi", "spa", "quiet zone"]},
    ]}

async def book_airport_lounge(lounge_id, guest_name, date, **kw):
    await asyncio.sleep(0.2)
    return {"booking_id": f"LB-{random.randint(10000,99999)}", "status": "confirmed"}

async def search_airport_parking(airport_code, start_date, end_date, **kw):
    await asyncio.sleep(0.3)
    return {"options": [
        {"parking_id": "PKG-001", "type": "short-stay", "daily_rate": 32, "distance": "on-site"},
        {"parking_id": "PKG-002", "type": "long-stay", "daily_rate": 18, "distance": "shuttle bus"},
        {"parking_id": "PKG-003", "type": "valet", "daily_rate": 50, "distance": "on-site"},
    ]}

async def book_fast_track(airport_code, date, passengers, **kw):
    await asyncio.sleep(0.2)
    return {"booking_id": f"FT-{random.randint(10000,99999)}", "airport": airport_code,
            "price_per_person": 8, "status": "confirmed"}

# ---- Local SIM / WiFi ----
async def search_travel_sim(destination_country, duration_days, **kw):
    await asyncio.sleep(0.2)
    return {"plans": [
        {"sim_id": "SIM-001", "provider": "Airalo", "data": "5GB", "price": 12, "type": "eSIM"},
        {"sim_id": "SIM-002", "provider": "Holafly", "data": "unlimited", "price": 29, "type": "eSIM"},
        {"sim_id": "SIM-003", "provider": "Three UK", "data": "12GB", "price": 18, "type": "physical"},
    ]}

async def buy_travel_sim(sim_id, email, **kw):
    await asyncio.sleep(0.2)
    return {"order_id": f"SIMO-{random.randint(10000,99999)}", "status": "confirmed", "delivery": "email (eSIM QR code)"}

# ---- Luggage ----
async def search_luggage_storage(city, date, **kw):
    await asyncio.sleep(0.2)
    return {"locations": [
        {"location_id": "LS-001", "name": "Stasher - King's Cross", "price_per_day": 6, "hours": "06:00-23:00"},
        {"location_id": "LS-002", "name": "LuggageHero - Paddington", "price_per_day": 8, "hours": "24/7"},
    ]}

async def book_luggage_storage(location_id, date, bags, **kw):
    await asyncio.sleep(0.2)
    return {"booking_id": f"LSB-{random.randint(10000,99999)}", "status": "confirmed"}

async def ship_luggage(origin_address, destination_address, bags, pickup_date, **kw):
    await asyncio.sleep(0.3)
    return {"shipment_id": f"SHP-{random.randint(10000,99999)}", "price": 45 * bags,
            "estimated_delivery": "2-3 days", "status": "scheduled"}

# ---- Reviews ----
async def get_hotel_reviews(hotel_id, **kw):
    await asyncio.sleep(0.3)
    return {"hotel_id": hotel_id, "average_rating": 4.5, "total_reviews": 1243, "reviews": [
        {"rating": 5, "title": "Excellent stay", "text": "Perfect location, great staff, clean rooms.", "date": "2025-06-20"},
        {"rating": 4, "title": "Good but noisy", "text": "Room was nice but street noise at night.", "date": "2025-06-15"},
        {"rating": 3, "title": "Average", "text": "Nothing special, overpriced for what you get.", "date": "2025-06-10"},
    ]}

async def get_restaurant_reviews(restaurant_id, **kw):
    await asyncio.sleep(0.3)
    return {"restaurant_id": restaurant_id, "average_rating": 4.6, "total_reviews": 892, "reviews": [
        {"rating": 5, "title": "Best Italian in London", "text": "Authentic pasta, great wine list.", "date": "2025-06-18"},
        {"rating": 4, "title": "Lovely ambiance", "text": "Food was good, service a bit slow.", "date": "2025-06-12"},
    ]}

# ---- Emergency ----
async def find_embassy(country, nationality, **kw):
    await asyncio.sleep(0.2)
    return {"embassy": {"country": country, "nationality": nationality,
            "address": "1 Grosvenor Square, London W1K 4AB", "phone": "+44-20-7499-9000",
            "hours": "Mon-Fri 08:30-17:00", "emergency_line": "+44-20-7499-9000 ext 1"}}

async def find_hospitals(city, **kw):
    await asyncio.sleep(0.2)
    return {"hospitals": [
        {"name": "St Thomas' Hospital", "address": "Westminster Bridge Rd", "phone": "+44-20-7188-7188", "emergency": True, "distance": "1.2 km"},
        {"name": "University College Hospital", "address": "235 Euston Rd", "phone": "+44-20-3456-7890", "emergency": True, "distance": "2.5 km"},
    ]}

async def get_emergency_numbers(country, **kw):
    await asyncio.sleep(0.1)
    return {"country": country, "police": "999", "ambulance": "999", "fire": "999",
            "european_emergency": "112", "non_emergency_police": "101"}

# ---- Loyalty / Points ----
async def check_loyalty_points(program, member_id, **kw):
    await asyncio.sleep(0.2)
    return {"program": program, "member_id": member_id, "points": 45200,
            "tier": "Gold", "points_expiring_soon": 5000, "expiry_date": "2025-12-31"}

async def redeem_loyalty_points(program, member_id, points, redemption_type, **kw):
    await asyncio.sleep(0.2)
    return {"redemption_id": f"RDM-{random.randint(10000,99999)}", "points_used": points,
            "value": f"${points * 0.01:.2f}", "status": "confirmed"}


# ===========================================================================
# Tool definitions for the new tools
# ===========================================================================

ALL_TOOLS.extend([
    # ---- Insurance ----
    {"type": "function", "function": {"name": "search_travel_insurance",
        "description": "Search travel insurance plans for a trip. Returns providers with coverage details, prices, medical limits, and trip cancellation limits.",
        "parameters": {"type": "object", "properties": {
            "destination": {"type": "string", "description": "Destination country"},
            "trip_duration_days": {"type": "integer", "description": "Trip duration in days"},
            "travelers": {"type": "integer", "description": "Number of travelers"},
        }, "required": ["destination", "trip_duration_days", "travelers"]}}},
    {"type": "function", "function": {"name": "buy_travel_insurance",
        "description": "Purchase a travel insurance plan using plan_id from search results.",
        "parameters": {"type": "object", "properties": {
            "plan_id": {"type": "string"}, "traveler_name": {"type": "string"}, "traveler_email": {"type": "string"},
        }, "required": ["plan_id", "traveler_name", "traveler_email"]}}},
    {"type": "function", "function": {"name": "file_insurance_claim",
        "description": "File a claim on an active travel insurance policy for medical, cancellation, or loss events.",
        "parameters": {"type": "object", "properties": {
            "policy_id": {"type": "string"}, "claim_type": {"type": "string", "enum": ["medical", "cancellation", "luggage_loss", "delay"]},
            "description": {"type": "string"}, "amount": {"type": "number"},
        }, "required": ["policy_id", "claim_type", "description", "amount"]}}},
    # ---- Trains ----
    {"type": "function", "function": {"name": "search_trains",
        "description": "Search train/rail tickets between two cities. Returns operators, prices, duration, and class options. Covers Eurostar, Thalys, TGV, and national rail.",
        "parameters": {"type": "object", "properties": {
            "origin": {"type": "string", "description": "Departure city or station"},
            "destination": {"type": "string", "description": "Arrival city or station"},
            "departure_date": {"type": "string", "description": "Date YYYY-MM-DD"},
            "travel_class": {"type": "string", "enum": ["standard", "premier", "business"]},
        }, "required": ["origin", "destination", "departure_date"]}}},
    {"type": "function", "function": {"name": "book_train",
        "description": "Book a train ticket using train_id from search results.",
        "parameters": {"type": "object", "properties": {
            "train_id": {"type": "string"}, "passenger_name": {"type": "string"}, "passenger_email": {"type": "string"},
        }, "required": ["train_id", "passenger_name", "passenger_email"]}}},
    {"type": "function", "function": {"name": "cancel_train",
        "description": "Cancel a train booking by reference number. Returns refund percentage based on cancellation policy.",
        "parameters": {"type": "object", "properties": {
            "booking_ref": {"type": "string"},
        }, "required": ["booking_ref"]}}},
    # ---- Events ----
    {"type": "function", "function": {"name": "search_events",
        "description": "Search for events, concerts, theatre shows, sports matches, and comedy nights in a city on a specific date.",
        "parameters": {"type": "object", "properties": {
            "city": {"type": "string"}, "date": {"type": "string", "description": "Date YYYY-MM-DD"},
            "category": {"type": "string", "enum": ["theatre", "music", "sports", "comedy", "all"]},
        }, "required": ["city", "date"]}}},
    {"type": "function", "function": {"name": "buy_event_tickets",
        "description": "Purchase tickets for an event using event_id from search results.",
        "parameters": {"type": "object", "properties": {
            "event_id": {"type": "string"}, "quantity": {"type": "integer"},
            "attendee_name": {"type": "string"}, "attendee_email": {"type": "string"},
        }, "required": ["event_id", "quantity", "attendee_name", "attendee_email"]}}},
    # ---- Airport Services ----
    {"type": "function", "function": {"name": "search_airport_lounges",
        "description": "Search airport lounges available at a specific airport. Returns lounge names, terminals, prices, and amenities.",
        "parameters": {"type": "object", "properties": {
            "airport_code": {"type": "string", "description": "IATA airport code (e.g. LHR, JFK)"},
            "date": {"type": "string"},
        }, "required": ["airport_code", "date"]}}},
    {"type": "function", "function": {"name": "book_airport_lounge",
        "description": "Book access to an airport lounge.",
        "parameters": {"type": "object", "properties": {
            "lounge_id": {"type": "string"}, "guest_name": {"type": "string"}, "date": {"type": "string"},
        }, "required": ["lounge_id", "guest_name", "date"]}}},
    {"type": "function", "function": {"name": "search_airport_parking",
        "description": "Search airport parking options with daily rates and distance from terminal.",
        "parameters": {"type": "object", "properties": {
            "airport_code": {"type": "string"}, "start_date": {"type": "string"}, "end_date": {"type": "string"},
        }, "required": ["airport_code", "start_date", "end_date"]}}},
    {"type": "function", "function": {"name": "book_fast_track",
        "description": "Book fast-track security lane at an airport to skip queues.",
        "parameters": {"type": "object", "properties": {
            "airport_code": {"type": "string"}, "date": {"type": "string"}, "passengers": {"type": "integer"},
        }, "required": ["airport_code", "date", "passengers"]}}},
    # ---- SIM / WiFi ----
    {"type": "function", "function": {"name": "search_travel_sim",
        "description": "Search for travel SIM cards and eSIMs for a destination. Returns data plans, prices, and providers.",
        "parameters": {"type": "object", "properties": {
            "destination_country": {"type": "string"}, "duration_days": {"type": "integer"},
        }, "required": ["destination_country", "duration_days"]}}},
    {"type": "function", "function": {"name": "buy_travel_sim",
        "description": "Purchase a travel SIM or eSIM plan.",
        "parameters": {"type": "object", "properties": {
            "sim_id": {"type": "string"}, "email": {"type": "string"},
        }, "required": ["sim_id", "email"]}}},
    # ---- Luggage ----
    {"type": "function", "function": {"name": "search_luggage_storage",
        "description": "Find luggage storage locations near train stations and airports in a city.",
        "parameters": {"type": "object", "properties": {
            "city": {"type": "string"}, "date": {"type": "string"},
        }, "required": ["city", "date"]}}},
    {"type": "function", "function": {"name": "book_luggage_storage",
        "description": "Book luggage storage at a specific location.",
        "parameters": {"type": "object", "properties": {
            "location_id": {"type": "string"}, "date": {"type": "string"}, "bags": {"type": "integer"},
        }, "required": ["location_id", "date", "bags"]}}},
    {"type": "function", "function": {"name": "ship_luggage",
        "description": "Ship luggage between addresses (hotel to airport, between cities, etc.).",
        "parameters": {"type": "object", "properties": {
            "origin_address": {"type": "string"}, "destination_address": {"type": "string"},
            "bags": {"type": "integer"}, "pickup_date": {"type": "string"},
        }, "required": ["origin_address", "destination_address", "bags", "pickup_date"]}}},
    # ---- Reviews ----
    {"type": "function", "function": {"name": "get_hotel_reviews",
        "description": "Get guest reviews and ratings for a specific hotel. Returns individual reviews with ratings, titles, and text.",
        "parameters": {"type": "object", "properties": {
            "hotel_id": {"type": "string"},
        }, "required": ["hotel_id"]}}},
    {"type": "function", "function": {"name": "get_restaurant_reviews",
        "description": "Get diner reviews and ratings for a specific restaurant.",
        "parameters": {"type": "object", "properties": {
            "restaurant_id": {"type": "string"},
        }, "required": ["restaurant_id"]}}},
    # ---- Emergency ----
    {"type": "function", "function": {"name": "find_embassy",
        "description": "Find the embassy or consulate for your nationality in a specific country. Returns address, phone, hours.",
        "parameters": {"type": "object", "properties": {
            "country": {"type": "string"}, "nationality": {"type": "string"},
        }, "required": ["country", "nationality"]}}},
    {"type": "function", "function": {"name": "find_hospitals",
        "description": "Find hospitals and emergency rooms near a location.",
        "parameters": {"type": "object", "properties": {
            "city": {"type": "string"},
        }, "required": ["city"]}}},
    {"type": "function", "function": {"name": "get_emergency_numbers",
        "description": "Get emergency phone numbers (police, ambulance, fire) for a country.",
        "parameters": {"type": "object", "properties": {
            "country": {"type": "string"},
        }, "required": ["country"]}}},
    # ---- Loyalty ----
    {"type": "function", "function": {"name": "check_loyalty_points",
        "description": "Check loyalty/frequent flyer points balance, tier status, and expiring points.",
        "parameters": {"type": "object", "properties": {
            "program": {"type": "string", "description": "Loyalty program name (e.g. 'Delta SkyMiles', 'Marriott Bonvoy')"},
            "member_id": {"type": "string"},
        }, "required": ["program", "member_id"]}}},
    {"type": "function", "function": {"name": "redeem_loyalty_points",
        "description": "Redeem loyalty points for flights, hotel nights, upgrades, or gift cards.",
        "parameters": {"type": "object", "properties": {
            "program": {"type": "string"}, "member_id": {"type": "string"},
            "points": {"type": "integer"}, "redemption_type": {"type": "string", "enum": ["flight", "hotel", "upgrade", "gift_card"]},
        }, "required": ["program", "member_id", "points", "redemption_type"]}}},
])


# ---------------------------------------------------------------------------
# Plain-text tool descriptions (for prompt injection, not OpenAI function calling)
# ---------------------------------------------------------------------------

def _build_tool_descriptions() -> str:
    lines = []
    for tool in ALL_TOOLS:
        func = tool["function"]
        params = func["parameters"]["properties"]
        required = set(func["parameters"].get("required", []))
        parts = []
        for name, spec in params.items():
            suffix = "" if name in required else "?"
            parts.append(f"{name}: {spec['type']}{suffix}")
        sig = ", ".join(parts)
        lines.append(f"{func['name']}({sig})")
        lines.append(f"  {func['description'][:120]}")
        lines.append("")
    return "\n".join(lines)


TOOL_DESCRIPTIONS: str = _build_tool_descriptions()
"""
Pre-formatted plain-text listing of all tools with signatures and descriptions.
Example entry:

  search_flights(origin: str, destination: str, departure_date: str, return_date: str?, ...)
    Search for available flights between two cities. Supports one-way and round-trip. ...
"""


# Tool name -> implementation function mapping
TOOL_REGISTRY: Dict[str, Any] = {
    "search_flights": search_flights,
    "book_flight": book_flight,
    "cancel_flight": cancel_flight,
    "search_hotels": search_hotels,
    "book_hotel": book_hotel,
    "cancel_hotel": cancel_hotel,
    "get_weather_forecast": get_weather_forecast,
    "get_current_weather": get_current_weather,
    "search_restaurants": search_restaurants,
    "make_restaurant_reservation": make_restaurant_reservation,
    "cancel_reservation": cancel_reservation,
    "search_attractions": search_attractions,
    "search_activities": search_activities,
    "get_directions": get_directions,
    "search_car_rentals": search_car_rentals,
    "book_car_rental": book_car_rental,
    "convert_currency": convert_currency,
    "translate_text": translate_text,
    "get_travel_advisory": get_travel_advisory,
    "get_visa_requirements": get_visa_requirements,
    "search_travel_insurance": search_travel_insurance,
    "buy_travel_insurance": buy_travel_insurance,
    "file_insurance_claim": file_insurance_claim,
    "search_trains": search_trains,
    "book_train": book_train,
    "cancel_train": cancel_train,
    "search_events": search_events,
    "buy_event_tickets": buy_event_tickets,
    "search_airport_lounges": search_airport_lounges,
    "book_airport_lounge": book_airport_lounge,
    "search_airport_parking": search_airport_parking,
    "book_fast_track": book_fast_track,
    "search_travel_sim": search_travel_sim,
    "buy_travel_sim": buy_travel_sim,
    "search_luggage_storage": search_luggage_storage,
    "book_luggage_storage": book_luggage_storage,
    "ship_luggage": ship_luggage,
    "get_hotel_reviews": get_hotel_reviews,
    "get_restaurant_reviews": get_restaurant_reviews,
    "find_embassy": find_embassy,
    "find_hospitals": find_hospitals,
    "get_emergency_numbers": get_emergency_numbers,
    "check_loyalty_points": check_loyalty_points,
    "redeem_loyalty_points": redeem_loyalty_points,
}


# ---------------------------------------------------------------------------
# Schema fixup: make optional parameters nullable.
# Reasoning models (e.g. oss-20b) frequently send null for optional params
# they don't need. Groq's strict validation rejects null unless the schema
# explicitly allows it. This loop patches every optional param to accept null.
# ---------------------------------------------------------------------------

def _make_optional_params_nullable(tools: List[Dict]) -> None:
    for tool in tools:
        params = tool["function"]["parameters"]
        required = set(params.get("required", []))
        for name, spec in params.get("properties", {}).items():
            if name not in required and isinstance(spec.get("type"), str):
                spec["type"] = [spec["type"], "null"]

_make_optional_params_nullable(ALL_TOOLS)
