# Technology Stack - Shop Map Manager

## Language & Core Frameworks
- **Python:** The primary programming language.
- **Streamlit:** Used for building the interactive web application interface.

## Map & Visualization
- **Folium:** Library used for creating the interactive map.
- **Streamlit-Folium:** Integration component to render Folium maps within Streamlit.
- **Gaode Map Tiles:** Integrated via URL pattern for the base map layer.

## Data Management
- **Pandas:** Used for reading, writing, and manipulating shop data stored in CSV format.
- **CSV:** The primary storage format for the application's data (`shops_data.csv`).

## Integration & APIs
- **Gaode Map API:** Used for shop search and retrieving location details (Latitude/Longitude, Address).
- **Requests:** Python library used to interact with the Gaode Map API.
