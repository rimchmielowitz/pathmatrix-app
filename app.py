# app.py - Demo Version with TypedDict (PEP 8 + Type-Safe)
"""
PathMatrix Optimizer Demo - Streamlit app for vehicle routing optimization.

This application provides a web interface for optimizing vehicle routes
from a central hub to multiple destinations using OR-Tools.
Refactored with TypedDict for clean, type-safe configuration.
"""

# Standard library imports
from typing import Dict, List, Any, Tuple, Optional
from typing_extensions import TypedDict
from io import BytesIO
import requests

# Third-party imports
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic


def call_solver_api(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call the solver API with improved error handling and debugging.
    
    Args:
        input_data: Dictionary containing config and demand data
        
    Returns:
        Dictionary with solver results or error information
    """
    url = "https://pathmatrix-solver-api.onrender.com/solve"
    
    try:
        # Log request details for debugging
        st.write("🔄 Sending request to solver...")
                
        # Make the request
        response = requests.post(
            url, 
            json=input_data,
            timeout=120,  # 2 minute timeout
            headers={'Content-Type': 'application/json'}
        )
                
        if response.status_code == 200:
            try:
                result = response.json()
                st.write("✅ Successfully received response from solver")
                return result
            except ValueError as e:
                st.error(f"❌ Failed to parse JSON response: {e}")
                st.write("Raw response:", response.text[:1000])
                return {"solver_status": f"FAILED: Invalid JSON response"}
        else:
            st.error(f"❌ HTTP Error: {response.status_code}")
            st.write("Response:", response.text[:1000])
            return {"solver_status": f"FAILED: HTTP {response.status_code}"}
            
    except requests.exceptions.Timeout:
        st.error("❌ Request timeout - solver took too long")
        return {"solver_status": "FAILED: Timeout"}
        
    except requests.exceptions.ConnectionError:
        st.error("❌ Connection error - could not reach solver API")
        return {"solver_status": "FAILED: Connection error"}
        
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return {"solver_status": f"FAILED: {str(e)}"}



# ========================================
# TYPE-SAFE CONFIG DEFINITIONS
# ========================================

class ConfigDict(TypedDict):
    """Complete type-safe configuration schema."""
    # Vehicle parameters
    VEHICLE_CAPACITY: int
    MAX_VEHICLES_PER_ROUTE: int
    
    # Cost parameters
    COST_PER_KM: float
    MIN_COST_PER_TRIP: int
    
    # UI parameters
    MAX_TOTAL_PACKAGES: int
    MAX_PACKAGES_PER_CITY: int
    DEFAULT_TOTAL_PACKAGES: int
    
    # Solver parameters
    SOLVER_TIME_LIMIT_MS: int
    SOLVER_TYPE: str
    
    # Geography parameters
    MAP_CENTER_LAT: float
    MAP_CENTER_LON: float
    MAP_ZOOM_START: int
    
    # City data
    CITY_COORDINATES: Dict[str, Tuple[float, float]]
    inject_hub: str
    
    # Business logic
    DEFAULT_DISTRIBUTION_PERCENT: Dict[str, int]
    
    # Time parameters
    AVERAGE_SPEED_KMH: int
    UNLOAD_TIME_HOURS: float
    
    # Gantt parameters
    GANTT_DPI: int
    GANTT_FIGSIZE_WIDTH: int
    GANTT_FIGSIZE_HEIGHT: int
    
    # Derived values
    AVAILABLE_CITIES: List[str]
    DESTINATION_CITIES: List[str]
    MAX_TOTAL_CAPACITY: int
    RECOMMENDED_MAX_PER_CITY: int

# Type aliases for better readability
PackageDistribution = Dict[str, int]

# ========================================
# TYPE-SAFE CONFIG INSTANCE
# ========================================

CONFIG: ConfigDict = {
    # === VEHICLE PARAMETERS ===
    "VEHICLE_CAPACITY": 200,                # packages per vehicle
    "MAX_VEHICLES_PER_ROUTE": 10,           # solver limit
    
    # === COST PARAMETERS ===
    "COST_PER_KM": 1.0,                     # €/km
    "MIN_COST_PER_TRIP": 100,               # €/trip minimum
    
    # === UI PARAMETERS ===
    "MAX_TOTAL_PACKAGES": 7500,             # max number of packages in total
    "MAX_PACKAGES_PER_CITY": 1000,          # input limit
    "DEFAULT_TOTAL_PACKAGES": 0,            # initial value
    
    # === SOLVER PARAMETERS ===
    "SOLVER_TIME_LIMIT_MS": 60000,          # 60 seconds
    "SOLVER_TYPE": "SCIP",                  # algorithm
    
    # === GEOGRAPHY PARAMETERS ===
    "MAP_CENTER_LAT": 51.1657,              # Germany center
    "MAP_CENTER_LON": 10.4515,              # Germany center
    "MAP_ZOOM_START": 6,                    # zoom level
    
    # === CITY COORDINATES (central!) ===
    "CITY_COORDINATES": {
        "Berlin": (52.5200, 13.4050),       # cities (11)
        "Hamburg": (53.5511, 9.9937),
        "Leipzig": (51.3397, 12.3731),
        "Halle (Saale)": (51.4964, 11.9684),
        "Dresden": (51.0504, 13.7373),
        "Krefeld": (51.3386, 6.5853),
        "Dortmund": (51.5136, 7.4653),
        "Frankfurt am Main": (50.1109, 8.6821),
        "Stuttgart": (48.7758, 9.1829),
        "Munich": (48.1351, 11.5820),
        "Leverkusen": (51.0459, 7.0192),
    },
    
    "inject_hub": "Dortmund",
    
    # === BUSINESS LOGIC ===
    "DEFAULT_DISTRIBUTION_PERCENT": {       # percentage distribution of total demand
        "Berlin": 28,
        "Dortmund": 11,
        "Dresden": 3,
        "Frankfurt am Main": 6,
        "Munich": 15,
        "Halle (Saale)": 1,
        "Hamburg": 12,
        "Krefeld": 9,
        "Leipzig": 3,
        "Leverkusen": 9,
        "Stuttgart": 3,
    },
    
    # === TIME PARAMETERS ===
    "AVERAGE_SPEED_KMH": 80,                # km/h for time calculations
    "UNLOAD_TIME_HOURS": 0.5,               # 30 minutes unloading
    
    # === GANTT PARAMETERS ===
    "GANTT_DPI": 150,                       # chart quality
    "GANTT_FIGSIZE_WIDTH": 12,              # chart width
    "GANTT_FIGSIZE_HEIGHT": 8,              # chart height
    
    # === DERIVED VALUES (automatically calculated) ===
    "AVAILABLE_CITIES": [],                 # Will be populated below
    "DESTINATION_CITIES": [],               # Will be populated below
    "MAX_TOTAL_CAPACITY": 0,                # Will be calculated below
    "RECOMMENDED_MAX_PER_CITY": 0,          # Will be calculated below
}

# Calculate derived values
CONFIG["AVAILABLE_CITIES"] = list(CONFIG["CITY_COORDINATES"].keys())
CONFIG["DESTINATION_CITIES"] = [
    city for city in CONFIG["AVAILABLE_CITIES"] 
    if city != CONFIG["inject_hub"]
]
CONFIG["MAX_TOTAL_CAPACITY"] = (
    CONFIG["VEHICLE_CAPACITY"] * 
    CONFIG["MAX_VEHICLES_PER_ROUTE"] * 
    len(CONFIG["DESTINATION_CITIES"])
)
CONFIG["RECOMMENDED_MAX_PER_CITY"] = min(
    CONFIG["MAX_PACKAGES_PER_CITY"],
    CONFIG["VEHICLE_CAPACITY"] * CONFIG["MAX_VEHICLES_PER_ROUTE"]
)

# ========================================
# FUNCTIONS
# ========================================

def initialize_session_state() -> None:
    """Initialize all session state variables with default values."""
    defaults: Dict[str, Any] = {
        "total_packages": CONFIG["DEFAULT_TOTAL_PACKAGES"],
        "packages_per_destination": {},
        "final_total_packages": 0,
        "manual_distribution": False,
        "results": None,
        "map_needs_update": True,
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def on_distribution_change() -> None:
    """Callback for distribution mode change."""
    st.session_state["map_needs_update"] = True


def on_packages_change() -> None:
    """Callback for map update when demand values change."""
    st.session_state["map_needs_update"] = True


def render_introduction() -> None:
    """Render the introduction section with app information."""
    inject_hub: str = CONFIG["inject_hub"]
    vehicle_capacity: int = CONFIG["VEHICLE_CAPACITY"]
    cost_per_km: float = CONFIG["COST_PER_KM"]
    min_cost_per_trip: int = CONFIG["MIN_COST_PER_TRIP"]
    solver_time_limit_ms: int = CONFIG["SOLVER_TIME_LIMIT_MS"]
    
    with st.expander("ℹ️ Click here for introduction - Demo Version"):
        st.markdown(f"""
        Welcome to the **PathMatrix Optimizer Demo App** (MVP).

        This simplified version demonstrates the **core vehicle routing optimization** with **fixed, optimized parameters** to focus on the essential functionality.

        ## 🎯 What this Demo does:
        - **Optimizes routes** from {inject_hub} (central hub) to your selected destinations
        - **Minimizes total transport costs** using mathematical optimization
        - **Prevents unnecessary detours** to cities without demand
        - **Finds the most efficient direct routes** or cost-effective multi-stop combinations

        ## 🔧 Fixed Parameters (optimized for typical e-commerce scenarios):
        - **Vehicle Type**: Standard delivery van
        - **Vehicle Capacity**: **{vehicle_capacity} packages per vehicle**
        - **Cost Structure**: **€{cost_per_km:.2f} per kilometer + €{min_cost_per_trip} minimum cost per trip**
        - **Operation**: **Same-day delivery** with cost optimization
        - **Route Logic**: **No complex time constraints** - focus on pure cost efficiency
        - **Solver Time Limit**: **{solver_time_limit_ms//1000} seconds**

        ## 📝 What you can configure:
        - **Package distribution**: Choose how many packages go to which cities
        - **Demand pattern**: Either total packages with automatic distribution or manual per-city input

        ## 🚀 Expected Results:
        For feasible scenarios you should see:
        - **Efficient tours** with minimal tour costs
        - **No unnecessary detours** through cities without demand
        - **Clear cost breakdown** and route visualization

        ## 💡 Why Demo?
        This version eliminates complexity to demonstrate the **core routing logic**. Future versions can add:
        - Multiple vehicle types
        - Complex time windows and break rules
        - Weight/volume constraints
        - Advanced multi-stop optimization

        Use this interface to understand how **demand patterns affect routing costs** and see the **power of mathematical optimization** in logistics!
        """)


def get_package_distribution(
    manual_distribution: bool, 
    total_packages: int
) -> PackageDistribution:
    """
    Get package distribution based on manual or automatic mode.
    
    Args:
        manual_distribution: Whether to use manual distribution
        total_packages: Total number of packages for automatic distribution
        
    Returns:
        Dictionary mapping cities to package counts
    """
    packages_per_destination: PackageDistribution = {}
    
    # Clean access without cast()!
    default_distribution_percent: Dict[str, int] = CONFIG["DEFAULT_DISTRIBUTION_PERCENT"]
    max_packages_for_city: int = CONFIG["RECOMMENDED_MAX_PER_CITY"]
    available_cities: List[str] = CONFIG["AVAILABLE_CITIES"]
    vehicle_capacity: int = CONFIG["VEHICLE_CAPACITY"]
    
    if manual_distribution:
        st.subheader("Manual Package Distribution")
        st.markdown("*Enter the exact number of packages for each destination:*")
        
        col1, col2 = st.columns(2)
        
        for i, city in enumerate(available_cities):
            col = col1 if i % 2 == 0 else col2
            with col:
                packages_per_destination[city] = st.number_input(
                    f"{city}", 
                    min_value=0,
                    max_value=max_packages_for_city,
                    value=st.session_state.get(f"parcels_{city}", 0),
                    key=f"parcels_{city}",
                    on_change=on_packages_change,
                    help=f"Max {max_packages_for_city} (based on {vehicle_capacity} pkg/vehicle) to deliver to {city}"
                )
    else:
        for city, percent in default_distribution_percent.items():
            packages_per_destination[city] = int(total_packages * percent / 100)
    
    return packages_per_destination


def render_distribution_preview(
    packages_per_destination: PackageDistribution, 
    final_total_packages: int,
    manual_distribution: bool
) -> None:
    """
    Render the distribution preview section.
    
    Args:
        packages_per_destination: Package distribution by city
        final_total_packages: Total number of packages
        manual_distribution: Whether manual distribution is enabled
    """
    if manual_distribution and final_total_packages > 0:
        st.info(f"📊 Total packages from manual distribution: **{final_total_packages}**")

    if not manual_distribution and final_total_packages > 0:
        st.subheader("📋 Automatic Distribution Preview")
        preview_data: List[Dict[str, Any]] = []
        
        for city, packages in packages_per_destination.items():
            if packages > 0:
                percentage: float = (packages / final_total_packages * 100)
                preview_data.append({
                    "City": city,
                    "Packages": packages,
                    "Percentage": f"{percentage:.1f}%"
                })
        
        if preview_data:
            df_preview: pd.DataFrame = pd.DataFrame(preview_data)
            st.dataframe(df_preview, use_container_width=True)


def create_demand_map(packages_per_destination: PackageDistribution) -> folium.Map:
    """
    Create a folium map showing demand distribution.
    
    Args:
        packages_per_destination: Package distribution by city
        
    Returns:
        Folium map object with demand visualization
    """
    city_coords: Dict[str, Tuple[float, float]] = CONFIG["CITY_COORDINATES"]
    map_center_lat: float = CONFIG["MAP_CENTER_LAT"]
    map_center_lon: float = CONFIG["MAP_CENTER_LON"]
    map_zoom_start: int = CONFIG["MAP_ZOOM_START"]
    inject_hub: str = CONFIG["inject_hub"]
    
    m_demand: folium.Map = folium.Map(
        location=[map_center_lat, map_center_lon], 
        zoom_start=map_zoom_start
    )
    
    max_packages: int = max(packages_per_destination.values()) if packages_per_destination.values() else 0
    
    for city, coords in city_coords.items():
        if city == inject_hub:
            # Red circle for injection hub
            folium.CircleMarker(
                location=coords,
                radius=8,
                color="red",
                fill=True,
                fill_opacity=0.8,
                tooltip=f"{city}: Central Distribution Hub",
                popup=f"🏭 Central Hub {city}"
            ).add_to(m_demand)
            
            # Blue circle for injection hub demand
            folium.CircleMarker(
                location=coords,
                radius=5 + (packages_per_destination.get(city, 0) / max(max_packages, 1)) * 10,
                color="darkblue",
                fill=True,
                fill_opacity=0.5,
            ).add_to(m_demand)
        else:
            count: int = packages_per_destination.get(city, 0)
            if count > 0 and city != inject_hub:
                # Blue circles for cities with demand
                radius: float = 5 + (count / max(max_packages, 1)) * 10
                color: str = "darkblue"
                folium.CircleMarker(
                    location=coords,
                    radius=radius,
                    color=color,
                    fill=True,
                    fill_opacity=0.7,
                    tooltip=f"{city}: {count} packages",
                    popup=f"📦 {city}<br>{count} packages"
                ).add_to(m_demand)
            else:
                # Cities without demand - small gray circles
                folium.CircleMarker(
                    location=coords,
                    radius=3,
                    color="lightgray",
                    fill=True,
                    fill_opacity=0.3,
                    tooltip=f"{city}: No packages",
                    popup=f"🚫 {city}<br>No demand"
                ).add_to(m_demand)
    
    return m_demand


def render_technical_specs() -> None:
    """Render the technical specifications section."""
    vehicle_capacity: int = CONFIG["VEHICLE_CAPACITY"]
    max_vehicles_per_route: int = CONFIG["MAX_VEHICLES_PER_ROUTE"]
    cost_per_km: float = CONFIG["COST_PER_KM"]
    min_cost_per_trip: int = CONFIG["MIN_COST_PER_TRIP"]
    
    with st.expander("🔧 Technical Specifications"):
        st.markdown(f"""
        ### Fixed Parameters in this Demo:
        
        **🚚 Vehicle Specifications:**
        - **Type**: Standard delivery van
        - **Capacity**: {vehicle_capacity} packages per vehicle
        - **Max vehicles per route**: {max_vehicles_per_route}
        - **Cost**: €{cost_per_km:.2f} per kilometer
        - **Minimum cost**: €{min_cost_per_trip} per trip (covers fixed costs)
        
        **📊 Optimization Logic:**
        - **Objective**: Minimize total transport costs
        - **Constraint**: Vehicle capacity limits
        """)


def render_results_section(
    results: Optional[Dict[str, Any]], 
    final_total_packages: int
) -> None:
    """
    Render the optimization results section.
    
    Args:
        results: Optimization results from solver
        final_total_packages: Total number of packages
    """
    if not results:
        return
        
    status: str = results.get("solver_status", "")
    
    if status in ["FEASIBLE", "OPTIMAL"]:
        render_successful_results(results, final_total_packages)
    elif status == "INFEASIBLE":
        render_infeasible_results(final_total_packages)
    elif status.startswith("FAILED"):
        render_failed_results(status, final_total_packages)
    else:
        render_unknown_status(status)

def show_simple_schedule_table(active_routes: List[Dict[str, Any]]) -> None:
    """Show simple schedule table as Gantt fallback"""
    schedule_data = []
    vehicle_counter = 0
    
    for route in active_routes:
        for v in range(route["vehicles"]):
            vehicle_counter += 1
            travel_time = route["km"] / CONFIG.get("AVERAGE_SPEED_KMH", 80)
            schedule_data.append({
                "Vehicle": f"Vehicle-{vehicle_counter}",
                "Route": f"{route['from']} → {route['to']}",
                "Packages": route["packages"],
                "Distance": f"{route['km']:.0f} km",
                "Drive Time": f"{travel_time:.1f} hours",
                "Unload Time": "0.5 hours"
            })
    
    if schedule_data:
        df_schedule = pd.DataFrame(schedule_data)
        st.dataframe(df_schedule, use_container_width=True)
        
def render_successful_results(
    results: Dict[str, Any], 
    final_total_packages: int
) -> None:
    """
    Render successful optimization results.
    
    Args:
        results: Optimization results from solver
        final_total_packages: Total number of packages
    """
    if results.get("solver_status") == "OPTIMAL":
        st.success("✅ Optimization completed successfully!")
    elif results.get("solver_status") == "FEASIBLE":  
        st.warning("⚠️ Found a feasible solution, but it may not be optimal.")
        st.info("Showing results anyway - the solution works!")
        
    st.subheader("📊 Optimization Results")
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Cost", f"€{results['total_cost']:.0f}")
    
    with col2:
        if final_total_packages > 0:
            cost_per_package: float = results["total_cost"] / final_total_packages
            st.metric("Cost per Package", f"€{cost_per_package:.2f}")
        else:
            st.metric("Cost per Package", "N/A")
    
    with col3:
        st.metric("Total Distance", f"{results.get('total_km', 0):.0f} km")
    
    with col4:
        st.metric("Solve Time", f"{results.get('solve_time', 0):.1f}s")

    # Route Analysis
    st.subheader("🗺️ Route Analysis")
    if results.get("tour_costs"):
        df_routes: pd.DataFrame = pd.DataFrame(results["tour_costs"])
        df_display: pd.DataFrame = df_routes.copy()
        df_display = df_display.rename(columns={
            "from": "From",
            "to": "To", 
            "vehicles": "Vehicles",
            "packages": "Packages",
            "km": "Distance (km)",
            "cost": "Cost (€)"
        })
        df_display["Distance (km)"] = df_display["Distance (km)"].round(0).astype(int)
        df_display["Cost (€)"] = df_display["Cost (€)"].round(0).astype(int)
        st.dataframe(df_display, use_container_width=True)

    # Map Visualization
    st.subheader("🗺️ Route Map")
    if results.get("map_html"):
        st.components.v1.html(results["map_html"], height=500)

    # Gantt Chart
    st.subheader("⏱️ Vehicle Schedule")
    gantt_buffer: Optional[BytesIO] = None

    if results.get("active_routes"):
        # Check if Backend provided Gantt chart
        if results.get("gantt_base64"):
            try:
                import base64
                gantt_data = base64.b64decode(results["gantt_base64"])
                gantt_buffer = BytesIO(gantt_data)
                st.image(gantt_buffer, caption="Vehicle Schedule Overview", use_container_width=True)
            except Exception as e:
                st.warning(f"⚠️ Could not display Gantt chart: {e}")
                st.info("📊 Showing schedule table instead")
                show_simple_schedule_table(results["active_routes"])
        else:
            # ✅ KORREKT: Nur Fallback-Tabelle, kein plot_gantt_diagram Aufruf!
            st.info("📊 Backend provided no Gantt chart - showing schedule table")
            show_simple_schedule_table(results["active_routes"])
    else:
        st.info("📊 No routes to display")
            
    # Download Options
    render_download_options(results, final_total_packages, gantt_buffer)

def render_download_options(
    results: Dict[str, Any], 
    final_total_packages: int,
    gantt_buffer: Optional[BytesIO]
) -> None:
    """
    Render download options for results.
    
    Args:
        results: Optimization results
        final_total_packages: Total number of packages
        gantt_buffer: Gantt chart buffer
    """
    st.subheader("📥 Download Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if results.get("map_html"):
            st.download_button(
                label="📍 Download Route Map (HTML)",
                data=results["map_html"],
                file_name="route_map.html",
                mime="text/html"
            )
    
    with col2:
        if gantt_buffer:
            st.download_button(
                label="📊 Download Schedule (PNG)",
                data=gantt_buffer,
                file_name="vehicle_schedule.png",
                mime="image/png"
            )

    # Excel Summary
    excel_buffer: BytesIO = create_excel_summary(results, final_total_packages)
    st.download_button(
        label="📑 Download Complete Results (Excel)",
        data=excel_buffer,
        file_name="pathmatrix_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def create_excel_summary(
    results: Dict[str, Any], 
    final_total_packages: int
) -> BytesIO:
    """
    Create Excel summary of results.
    
    Args:
        results: Optimization results
        final_total_packages: Total number of packages
        
    Returns:
        Excel file buffer
    """
    excel_buffer: BytesIO = BytesIO()
    
    # Prepare data
    summary_data: Dict[str, List[str]] = {
        "Metric": [
            "Total Cost (€)", 
            "Cost per Package (€)", 
            "Total Distance (km)", 
            "Solve Time (s)", 
            "Number of Routes"
        ],
        "Value": [
            f"{results['total_cost']:.2f}",
            f"{results['total_cost']/final_total_packages:.2f}" if final_total_packages > 0 else "N/A",
            f"{results.get('total_km', 0):.0f}",
            f"{results.get('solve_time', 0):.1f}",
            f"{len(results.get('tour_costs', []))}"
        ]
    }
    
    packages_per_destination: PackageDistribution = st.session_state["packages_per_destination"]
    demand_data: Dict[str, List[Any]] = {
        "City": list(packages_per_destination.keys()),
        "Packages": list(packages_per_destination.values())
    }
    
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        pd.DataFrame(demand_data).to_excel(writer, sheet_name='Demand', index=False)
        if results.get("tour_costs"):
            pd.DataFrame(results["tour_costs"]).to_excel(writer, sheet_name='Routes', index=False)
    
    excel_buffer.seek(0)
    return excel_buffer


def render_infeasible_results(final_total_packages: int) -> None:
    """
    Render infeasible results section.
    
    Args:
        final_total_packages: Total number of packages
    """
    # Clean access without cast()!
    vehicle_capacity: int = CONFIG["VEHICLE_CAPACITY"]
    max_vehicles_per_route: int = CONFIG["MAX_VEHICLES_PER_ROUTE"]
    destination_cities: List[str] = CONFIG["DESTINATION_CITIES"]
    
    st.error("❌ No feasible solution found!")
    st.markdown("""
    ### Possible reasons:
        - **Demand too high**: Some destinations may require more vehicles than available
        - **Capacity constraints**: Package distribution exceeds vehicle capacity limits  
    
    ### Quick fixes:
        - **Reduce package numbers** for distant cities
        - **Check your demand distribution** - is it realistic?
        """)
    
    if final_total_packages > 0:
        max_packages_per_vehicle: int = vehicle_capacity
        max_vehicles_estimate: int = max_vehicles_per_route
        min_vehicles_needed: int = (
            (final_total_packages + max_packages_per_vehicle - 1) // max_packages_per_vehicle
        )
        
        st.info(f"""
        ### 📊 Capacity Check:
        - **Total packages**: {final_total_packages:,}
        - **Vehicle capacity**: {max_packages_per_vehicle} packages/vehicle
        - **Minimum vehicles needed**: {min_vehicles_needed}
        - **Max vehicles per route**: {max_vehicles_estimate}
        - **System capacity**: {max_vehicles_estimate * max_packages_per_vehicle * len(destination_cities):,} packages
        """)
        
        if min_vehicles_needed > max_vehicles_estimate:
            st.error(f"🚨 **Problem identified**: You need {min_vehicles_needed} vehicles but only {max_vehicles_estimate} are allowed per route!")
            st.markdown("**Solution**: Reduce package numbers or increase MAX_VEHICLES_PER_ROUTE in config.")


def render_failed_results(status: str, final_total_packages: int) -> None:
    """
    Render failed optimization results.
    
    Args:
        status: Solver status
        final_total_packages: Total number of packages
    """
    # Clean access without cast()!
    inject_hub: str = CONFIG["inject_hub"]
    solver_time_limit_ms: int = CONFIG["SOLVER_TIME_LIMIT_MS"]
    
    st.error(f"❌ Solver failed with status: {status}")
    st.markdown("""
    ### Possible causes:
    - **Technical error**: Solver encountered an internal problem
    - **Memory issues**: Problem too large for available resources
    - **Time limit**: Solver couldn't find any solution within time limit
    - **Invalid input**: Check your parameter configuration
    
    ### Troubleshooting:
    - **Reduce problem size**: Try with fewer packages or destinations
    - **Check inputs**: Verify all parameters are valid
    - **Restart**: Try running the optimization again
    - **Simplify**: Use automatic distribution instead of manual
    """)
    
    packages_per_destination: PackageDistribution = st.session_state["packages_per_destination"]
    active_destinations: int = len([
        city for city, pkg in packages_per_destination.items() 
        if pkg > 0 and city != inject_hub
    ])
    
    with st.expander("🔧 Technical Details"):
        st.code(f"""
        Solver Status: {status}
        Total Packages: {final_total_packages}
        Active Destinations: {active_destinations}
        Time Limit: {solver_time_limit_ms/1000}s
        """)


def render_unknown_status(status: str) -> None:
    """
    Render unknown solver status.
    
    Args:
        status: Unknown solver status
    """
    st.error(f"❌ Unknown solver status: {status}")
    st.info("Please try running the optimization again or check your input parameters.")


def main() -> None:
    """Main application function."""
    # Initialize session state
    initialize_session_state()

    # Clean access without cast()!
    max_total_packages: int = CONFIG["MAX_TOTAL_PACKAGES"]

    # UI Header
    st.title("PathMatrix Optimizer 🚚 - Demo")

    # Introduction section
    render_introduction()

    # Package Distribution section
    st.subheader("📦 Package Distribution")

    # Total packages input
    st.number_input(
        "Total Number of packages",
        min_value=0,
        max_value=max_total_packages,
        value=st.session_state["total_packages"],
        key="total_packages",
        on_change=on_packages_change,
        help="Total packages to be distributed from injection hub to destination cities"
    )

    # Manual distribution checkbox
    manual_distribution: bool = st.checkbox(
        "Enable manual per-city package input",
        key="manual_distribution",
        on_change=on_distribution_change,
        help="Manually specify packages for each destination instead of automatic distribution"
    )

    # Get package distribution
    packages_per_destination: PackageDistribution = get_package_distribution(
        manual_distribution, 
        st.session_state["total_packages"]
    )

    # Calculate final total packages
    if manual_distribution:
        final_total_packages: int = sum(packages_per_destination.values())
    else:
        final_total_packages = st.session_state["total_packages"]

    # Update session state
    st.session_state["packages_per_destination"] = packages_per_destination
    st.session_state["final_total_packages"] = final_total_packages

    # Render distribution preview
    render_distribution_preview(packages_per_destination, final_total_packages, manual_distribution)

    # Validation warning
    show_warning: bool = final_total_packages == 0
    if show_warning:
        if manual_distribution:
            st.warning("🚨 Please enter package quantities for at least one destination.")
        else:
            st.warning("🚨 Please define the total number of packages.")

    # Visual Demand Overview
    st.subheader("📍 Visual Demand Overview")

    # Create or update demand map
    if "demand_map" not in st.session_state or st.session_state.get("map_needs_update", True):
        m_demand: folium.Map = create_demand_map(packages_per_destination)
        st.session_state["demand_map"] = m_demand
        st.session_state["map_needs_update"] = False

    # Display map
    st_folium(st.session_state["demand_map"], height=400, use_container_width=True)

    # Technical specifications
    render_technical_specs()

    # Run Optimization section
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: grey;'>⚡ Optimized for speed - typically solves in under 30 seconds</p>",
        unsafe_allow_html=True
    )

    # Centered button
    left, center, right = st.columns([1, 2, 1])
    run_button_disabled: bool = final_total_packages == 0

    with center:
        run_clicked: bool = st.button(
            "🚀 Optimize Routes", 
            help="Start route optimization with current package distribution",
            disabled=run_button_disabled,
            type="primary"
        )

    # Button logic
    if run_clicked and not run_button_disabled:
        with st.spinner("Optimizing routes... please wait"):
            # Convert ConfigDict to Dict[str, Any] for solver compatibility
            config_dict: Dict[str, Any] = dict(CONFIG)
            user_input: Dict[str, Any] = {
                "demand": packages_per_destination,
                "config": config_dict
            }
            st.session_state["results"] = call_solver_api(user_input)

    # Show Results
    results: Optional[Dict[str, Any]] = st.session_state.get("results")

    if results:
        render_results_section(results, final_total_packages)
    elif not show_warning:
        st.info("👆 Configure your package distribution above and click 'Optimize Routes' to start")

    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: grey; font-size: 0.8em;'>"
        "PathMatrix Optimizer Demo - Focused on core routing optimization"
        "</p>", 
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()