# Initial Concept
A map-based shop management application built with Streamlit and Folium, allowing users to manage shop data in a CSV file and visualize them on a map with Gaode Map tiles.

# Product Guide - Shop Map Manager

## Target Users
- Individuals who want to record and track shops (restaurants, cafes, etc.) they have visited or plan to visit in the future.

## Core Goals
- Provide a simple interface to manage a personal directory of interesting locations.
- Visualize saved shops on an interactive map for easy spatial reference.
- Facilitate the discovery of shop details using the Gaode Map API.

## Key Features
- **Shop Search & Addition:** Integration with the Gaode Map API to search for shops by name or keyword and add them to the personal list.
- **Categorization:** Ability to assign categories (e.g., Cafe, Restaurant, Retail) to each shop for better organization.
- **Personal Notes & Ratings:** Users can record their personal experiences, notes, and star ratings for locations they've visited.
- **Map Visualization:**
    - Interactive map showing all saved locations.
    - Custom markers displaying the shop name and a category-specific icon.
    - **Color-Coded Markers:** Markers are color-coded based on visit status (e.g., "Visited" vs. "Want to Visit") for quick visual identification.
- **Visit Tracking:** Distinguish between shops "visited" and those the user "wants to visit".

## User Experience
- Focused on a clean, map-centric interface using Streamlit and Folium.
- Efficient search-and-add workflow to minimize manual data entry.