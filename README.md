[English](README.md) | [中文](_README_CN.md)

# Shop Map Manager (店铺地图管理系统)

A map-based shop management application built with Streamlit and Folium, allowing users to manage shop data in CSV (local) or Supabase (cloud) and visualize them on an interactive map with Gaode (Amap) tiles.

![Screenshot](images/0.png)

## Live Demo

https://china-map.streamlit.app/

## Features

- **User Authentication**: Sign up and login to sync your data to the cloud
  - Local mode: Use without an account, data stored locally in CSV
  - Cloud mode: Login to sync data across devices via Supabase
- **Shop Search & Addition**: Integration with the Gaode Map API to search for shops by name or keyword and automatically add them to your personal list
- **Interactive Map Visualization**:
  - Displays all saved shop locations on an interactive map
  - Custom markers with category-specific icons
  - Color-coded markers based on visit status (red for "Visited", green for "Want to Visit")
- **Data Management**:
  - Editable table view for managing shop information
  - Auto-save to CSV (local) or Supabase (cloud)
  - Track visit status, ratings, and personal notes
- **Image Upload**: Upload and manage shop photos (cloud mode only)
  - Upload multiple images per shop
  - View images in the shop details panel
  - Delete images from cloud storage
- **Categorization**: Organize shops by type (餐饮, 零售, 服务, 娱乐, 教育, 医疗, 风景名胜, etc.)
- **Visit Tracking**: Distinguish between shops you've visited and those you want to visit
- **Personal Notes & Ratings**: Record experiences, notes, and star ratings (1-5) for visited locations

## Tech Stack

- **Frontend**: Streamlit
- **Mapping**: Folium with streamlit-folium
- **Data**: Pandas
- **Backend**: Supabase (Authentication & Database)
- **Storage**: Supabase Storage (Image hosting)
- **API**: Gaode Map API (高德地图API)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd map_app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the project root and add your API keys:
```
GAODE_API_KEY=your_gaode_api_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
```

To get the API keys:
- **Gaode API Key**: Visit https://console.amap.com/dev/key/app
- **Supabase**: Sign up at https://supabase.com and create a new project

**Note**: For cloud features (authentication, data sync, image upload), you need to set up Supabase with the following:
- Enable Email/Password authentication
- Create a table called `user_shops` with appropriate columns
- Create a storage bucket called `shopphoto` for images

Refer to `.env.example` for the required environment variables format.

## Usage

1. Run the application:
```bash
streamlit run app.py
```

2. The app will open in your browser at `http://localhost:8501`

3. **Local vs Cloud Mode**:
   - **Local Mode**: Start using the app without login - data saves to `shops_data.csv`
   - **Cloud Mode**: Sign up/Login to sync data across devices and enable image uploads

4. **Adding Shops**:
   - Use the sidebar search to find shops by name
   - Click "Add to List" (添加到列表) on any search result

5. **Managing Data**:
   - Switch to the "Data Table" (数据表格) tab
   - Edit shop details, visit status, ratings, and notes
   - Changes auto-save to CSV (local) or Supabase (cloud)

6. **Managing Images** (Cloud Mode):
   - Click on any shop marker on the map
   - Upload images in the shop details panel
   - View or delete existing images

7. **Viewing on Map**:
   - Switch to the "Map View" (地图视图) tab
   - Click on markers to see shop details and manage images

## Data Storage

The app supports two storage modes:

### Local Mode (No Login)
- Shop data is stored in `shops_data.csv`
- Images are not supported

### Cloud Mode (With Supabase Account)
- Shop data is synced to Supabase database (`user_shops` table)
- Images are stored in Supabase Storage (`shopphoto` bucket)
- Data persists across devices

### Data Schema

| Column | Description |
|--------|-------------|
| user_id | User ID (cloud mode only) |
| shop_name | Shop name |
| city | City name |
| address | Full address |
| latitude | Latitude coordinate |
| longitude | Longitude coordinate |
| shop_type | Shop category |
| type | Journey type (Coffee, Scenery, Food, Bar, Other) |
| visit_status | "Want to Visit" or "Visited" |
| notes | Personal notes |
| rating | Star rating (0-5) |
| image_url | Image URLs (JSON array, cloud mode) |

## Project Structure

```
map_app/
├── app.py              # Main Streamlit application
├── map_utils.py        # Gaode API and Supabase integration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .gitignore          # Git ignore rules
├── shops_data.csv      # Local data storage (auto-created)
├── static/
│   ├── style.css       # Custom styles
│   └── screenshots/    # App screenshots
├── images/             # Image assets
├── README.md           # This file (English)
└── _README_CN.md       # Chinese documentation
```

## Screenshots

![Map View](static/screenshots/map_view.png)
![Table View](static/screenshots/table_view.png)

## Dependencies

- streamlit - Web application framework
- folium - Map visualization
- streamlit-folium - Streamlit-Folium integration
- pandas - Data manipulation
- python-dotenv - Environment variable management
- requests - HTTP client for API calls
- supabase - Supabase client for authentication and database

## License

This project is open source and available under the MIT License.
