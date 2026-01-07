# Specification: Enhance Shop Search & Management

## Goal
Enhance the Shop Map Manager application to allow users to easily find shops using the Gaode Map API, classify them into categories, track their visit status, and record personal notes and ratings.

## Core Features

### 1. Data Model Expansion
- **Storage:** Update `shops_data.csv` to support new fields.
- **Fields:**
    - `shop_name` (Existing)
    - `address` (Existing)
    - `latitude` (Existing)
    - `longitude` (Existing)
    - `shop_type` (Existing - to be used as Category)
    - `visit_status`: Enum ["Visited", "Want to Visit"]
    - `notes`: Free-form text
    - `rating`: Integer (1-5)

### 2. Gaode API Integration
- **Search:** Implement a search function that queries the Gaode Map API (Place Search).
- **Display:** Show search results with Name, Address, and Type.
- **Selection:** Allow user to select a result to populate the "Add Shop" form.

### 3. User Interface Enhancements
- **Add Shop Form:**
    - Input fields for `shop_name`, `address` (auto-filled from search).
    - Dropdown/Select for `shop_type`.
    - Radio/Select for `visit_status` (Default: "Want to Visit").
    - Text Area for `notes`.
    - Slider/Select for `rating` (1-5).
- **Map Visualization:**
    - Markers must be color-coded based on `visit_status`:
        - **Visited:** Red
        - **Want to Visit:** Green
    - **Category Icons:** Markers should display a different icon/logo based on the `shop_type`.
    - Popup/Tooltip should show Name, Type, Rating, and a snippet of Notes.

## Technical Implementation
- **Frontend:** Streamlit
- **Map:** Folium / Streamlit-Folium
- **Data:** Pandas for CSV manipulation
- **API:** Python `requests` to call Gaode API
