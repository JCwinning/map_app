# Plan: Enhance Shop Search & Management

## Phase 1: Data Model & Basic UI Update [checkpoint: de739d0]
- [x] Task: Update CSV handling to support new columns (visit_status, notes, rating) 628d04a
    - [x] Sub-task: Create a migration script or manually update `shops_data.csv` header.
    - [x] Sub-task: Update `app.py` data loading to ensure new columns exist with default values if missing.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Data Model & Basic UI Update' (Protocol in workflow.md) 85cc540

## Phase 2: Gaode API Search Integration [checkpoint: 4d52f09]
- [x] Task: Implement Gaode Place Search Function 19c81a8
    - [x] Sub-task: Create a new module/function `search_shops(keyword, city)` using `requests`.
    - [x] Sub-task: Write unit tests for the search function (mocking the API response).
- [x] Task: Create Search UI in Streamlit 1bf3ff1
    - [x] Sub-task: Add a text input for search keyword in the sidebar or main area.
    - [x] Sub-task: Display search results as a list or table.
    - [x] Sub-task: Allow selection of a result to pre-fill the "Add Shop" inputs.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Gaode API Search Integration' (Protocol in workflow.md) 85cc540

## Phase 3: Enhanced Shop Management UI [checkpoint: a908ab8]
- [x] Task: Update "Add Shop" Form ef42067
    - [x] Sub-task: Add `visit_status` selector (Radio/Select).
    - [x] Sub-task: Add `notes` text area.
    - [x] Sub-task: Add `rating` slider (1-5).
- [x] Task: Implement Save Logic for New Fields ef42067
    - [x] Sub-task: Update the dataframe saving logic to include the new fields.
    - [x] Sub-task: Write tests to verify data is saved correctly to CSV.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Enhanced Shop Management UI' (Protocol in workflow.md) 85cc540

## Phase 4: Map Visualization Updates [checkpoint: 85cc540]
- [x] Task: Implement Color-Coded Markers and Icons f627758
    - [x] Sub-task: Update the Folium marker generation loop.
    - [x] Sub-task: Logic: If `visit_status` == "Visited" -> Red; if "Want to Visit" -> Green.
    - [x] Sub-task: Implement logic to map `shop_type` to specific FontAwesome icons (e.g., 'cutlery' for food, 'shopping-cart' for retail).
- [x] Task: Update Marker Popups f627758
    - [x] Sub-task: Include Rating and Notes in the marker popup HTML/Text.
- [x] Task: Conductor - User Manual Verification 'Phase 4: Map Visualization Updates' (Protocol in workflow.md) 85cc540