# app.py - PathMatrix Optimizer Demo
"""PathMatrix Optimizer Demo - Streamlit app for vehicle routing optimization.

This application provides a web interface for optimizing vehicle routes
from a central hub to multiple destinations using OR-Tools.
Refactored with TypedDict for clean, type-safe configuration.
"""

# Standard library imports
import requests
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

# Third-party imports
import folium
import pandas as pd
import streamlit as st
from geopy.distance import geodesic
from streamlit_folium import st_folium
from typing_extensions import TypedDict


class ConfigDict(TypedDict):
    """Complete type-safe configuration schema for the optimizer."""
    
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


PackageDistribution = Dict[str, int]

CONFIG: ConfigDict = {
    # Vehicle parameters
    "VEHICLE_CAPACITY": 200,
    "MAX_VEHICLES_PER_ROUTE": 10,
    
    # Cost parameters
    "COST_PER_KM": 1.0,
    "MIN_COST_PER_TRIP": 100,
    
    # UI parameters
    "MAX_TOTAL_PACKAGES": 7500,
    "MAX_PACKAGES_PER_CITY": 1000,
    "DEFAULT_TOTAL_PACKAGES": 0,
    
    # Solver parameters
    "SOLVER_TIME_LIMIT_MS": 60000,
    "SOLVER_TYPE": "SCIP",
    
    # Geography parameters
    "MAP_CENTER_LAT": 51.1657,
    "MAP_CENTER_LON": 10.4515,
    "MAP_ZOOM_START": 6,
    
    # City coordinates
    "CITY_COORDINATES": {
        "Berlin": (52.5200, 13.4050),
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
    
    # Business logic
    "DEFAULT_DISTRIBUTION_PERCENT": {
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
    
    # Time parameters
    "AVERAGE_SPEED_KMH": 80,
    "UNLOAD_TIME_HOURS": 0.5,
    
    # Gantt parameters
    "GANTT_DPI": 150,
    "GANTT_FIGSIZE_WIDTH": 12,
    "GANTT_FIGSIZE_HEIGHT": 8,
    
    # Derived values (calculated below)
    "AVAILABLE_CITIES": [],
    "DESTINATION_CITIES": [],
    "MAX_TOTAL_CAPACITY": 0,
    "RECOMMENDED_MAX_PER_CITY": 0,
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


def call_solver_api(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Call the solver API with error handling.
    
    Args:
        input_data: Dictionary containing configuration and demand data.
        
    Returns:
        Dictionary containing solver results or error information.
        Keys include 'solver_status', 'total_cost', 'tour_costs', etc.
    """
    url = "https://pathmatrix-solver-api.onrender.com/solve"
    
    try:
        st.write("🔄 Sending request to solver...")
                
        response = requests.post(
            url, 
            json=input_data,
            timeout=120,
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
                return {"solver_status": "FAILED: Invalid JSON response"}
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
    """Mark map for update when distribution mode changes."""
    st.session_state["map_needs_update"] = True


def on_packages_change() -> None:
    """Mark map for update when package values change."""
    st.session_state["map_needs_update"] = True


def render_introduction() -> None:
    """Render the application introduction section."""
    hub = CONFIG["inject_hub"]
    capacity = CONFIG["VEHICLE_CAPACITY"]
    cost_km = CONFIG["COST_PER_KM"]
    min_cost = CONFIG["MIN_COST_PER_TRIP"]
    time_limit = CONFIG["SOLVER_TIME_LIMIT_MS"]
    
    with st.expander("ℹ️ Click here for introduction - Demo Version"):
        st.markdown(f"""
        Welcome to the **PathMatrix Optimizer Demo App** (MVP).

        This simplified version demonstrates **core vehicle routing 
        optimization** with **fixed, optimized parameters** to focus on 
        essential functionality.

        ## 🎯 What this Demo does:
        - **Optimizes routes** from {hub} (central hub) to selected 
          destinations
        - **Minimizes total transport costs** using mathematical optimization
        - **Prevents unnecessary detours** to cities without demand
        - **Finds efficient direct routes** or cost-effective multi-stop 
          combinations

        ## 🔧 Fixed Parameters:
        - **Vehicle Capacity**: **{capacity} packages per vehicle**
        - **Cost Structure**: **€{cost_km:.2f} per kilometer + €{min_cost} 
          minimum cost per trip**
        - **Operation**: **Same-day delivery** with cost optimization
        - **Solver Time Limit**: **{time_limit//1000} seconds**

        ## 📝 What you can configure:
        - **Package distribution**: Choose package quantities for cities
        - **Demand pattern**: Total packages with automatic distribution or 
          manual per-city input

        ## 🚀 Expected Results:
        For feasible scenarios you should see:
        - **Efficient tours** with minimal costs
        - **No unnecessary detours** through cities without demand
        - **Clear cost breakdown** and route visualization
        """)


def get_package_distribution(
    manual_distribution: bool, 
    total_packages: int
) -> PackageDistribution:
    """Get package distribution based on distribution mode.
    
    Args:
        manual_distribution: Whether to use manual distribution mode.
        total_packages: Total packages for automatic distribution.
        
    Returns:
        Dictionary mapping city names to package counts.
    """
    packages_per_destination: PackageDistribution = {}
    
    default_percentages = CONFIG["DEFAULT_DISTRIBUTION_PERCENT"]
    max_packages = CONFIG["RECOMMENDED_MAX_PER_CITY"]
    available_cities = CONFIG["AVAILABLE_CITIES"]
    vehicle_capacity = CONFIG["VEHICLE_CAPACITY"]
    
    if manual_distribution:
        st.subheader("Manual Package Distribution")
        st.markdown("*Enter the exact number of packages for each "
                   "destination:*")
        
        col1, col2 = st.columns(2)
        
        for i, city in enumerate(available_cities):
            col = col1 if i % 2 == 0 else col2
            with col:
                packages_per_destination[city] = st.number_input(
                    f"{city}", 
                    min_value=0,
                    max_value=max_packages,
                    value=st.session_state.get(f"parcels_{city}", 0),
                    key=f"parcels_{city}",
                    on_change=on_packages_change,
                    help=f"Max {max_packages} (based on {vehicle_capacity} "
                         f"pkg/vehicle) to deliver to {city}"
                )
    else:
        for city, percent in default_percentages.items():
            packages_per_destination[city] = int(total_packages * percent / 100)
    
    return packages_per_destination


def render_distribution_preview(
    packages_per_destination: PackageDistribution, 
    final_total_packages: int,
    manual_distribution: bool
) -> None:
    """Render package distribution preview.
    
    Args:
        packages_per_destination: Package distribution by city.
        final_total_packages: Total number of packages.
        manual_distribution: Whether manual distribution is enabled.
    """
    if manual_distribution and final_total_packages > 0:
        st.info(f"📊 Total packages from manual distribution: "
               f"**{final_total_packages}**")

    if not manual_distribution and final_total_packages > 0:
        st.subheader("📋 Automatic Distribution Preview")
        preview_data: List[Dict[str, Any]] = []
        
        for city, packages in packages_per_destination.items():
            if packages > 0:
                percentage = (packages / final_total_packages * 100)
                preview_data.append({
                    "City": city,
                    "Packages": packages,
                    "Percentage": f"{percentage:.1f}%"
                })
        
        if preview_data:
            df_preview = pd.DataFrame(preview_data)
            st.dataframe(df_preview, use_container_width=True)


def create_demand_map(
    packages_per_destination: PackageDistribution
) -> folium.Map:
    """Create a folium map showing demand distribution.
    
    Args:
        packages_per_destination: Package distribution by city.
        
    Returns:
        Folium map object with demand visualization.
    """
    city_coords = CONFIG["CITY_COORDINATES"]
    center_lat = CONFIG["MAP_CENTER_LAT"]
    center_lon = CONFIG["MAP_CENTER_LON"]
    zoom_start = CONFIG["MAP_ZOOM_START"]
    hub = CONFIG["inject_hub"]
    
    demand_map = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=zoom_start
    )
    
    max_packages = (max(packages_per_destination.values()) 
                   if packages_per_destination.values() else 0)
    
    for city, coords in city_coords.items():
        if city == hub:
            # Central hub marker
            folium.CircleMarker(
                location=coords,
                radius=8,
                color="red",
                fill=True,
                fill_opacity=0.8,
                tooltip=f"{city}: Central Distribution Hub",
                popup=f"🏭 Central Hub {city}"
            ).add_to(demand_map)
            
            # Hub demand marker
            folium.CircleMarker(
                location=coords,
                radius=5 + (packages_per_destination.get(city, 0) / 
                           max(max_packages, 1)) * 10,
                color="darkblue",
                fill=True,
                fill_opacity=0.5,
            ).add_to(demand_map)
        else:
            count = packages_per_destination.get(city, 0)
            if count > 0:
                # Cities with demand
                radius = 5 + (count / max(max_packages, 1)) * 10
                folium.CircleMarker(
                    location=coords,
                    radius=radius,
                    color="darkblue",
                    fill=True,
                    fill_opacity=0.7,
                    tooltip=f"{city}: {count} packages",
                    popup=f"📦 {city}<br>{count} packages"
                ).add_to(demand_map)
            else:
                # Cities without demand
                folium.CircleMarker(
                    location=coords,
                    radius=3,
                    color="lightgray",
                    fill=True,
                    fill_opacity=0.3,
                    tooltip=f"{city}: No packages",
                    popup=f"🚫 {city}<br>No demand"
                ).add_to(demand_map)
    
    return demand_map


def render_technical_specs() -> None:
    """Render the technical specifications section."""
    capacity = CONFIG["VEHICLE_CAPACITY"]
    max_vehicles = CONFIG["MAX_VEHICLES_PER_ROUTE"]
    cost_km = CONFIG["COST_PER_KM"]
    min_cost = CONFIG["MIN_COST_PER_TRIP"]
    
    with st.expander("🔧 Technical Specifications"):
        st.markdown(f"""
        ### Fixed Parameters in this Demo:
        
        **🚚 Vehicle Specifications:**
        - **Type**: Standard delivery van
        - **Capacity**: {capacity} packages per vehicle
        - **Max vehicles per route**: {max_vehicles}
        - **Cost**: €{cost_km:.2f} per kilometer
        - **Minimum cost**: €{min_cost} per trip (covers fixed costs)
        
        **📊 Optimization Logic:**
        - **Objective**: Minimize total transport costs
        - **Constraint**: Vehicle capacity limits
        """)


def render_results_section(
    results: Optional[Dict[str, Any]], 
    final_total_packages: int
) -> None:
    """Render the optimization results section.
    
    Args:
        results: Optimization results from solver.
        final_total_packages: Total number of packages.
    """
    if not results:
        return
        
    status = results.get("solver_status", "")
    
    if status in ["FEASIBLE", "OPTIMAL"]:
        render_successful_results(results, final_total_packages)
    elif status == "INFEASIBLE":
        render_infeasible_results(final_total_packages)
    elif status.startswith("FAILED"):
        render_failed_results(status, final_total_packages)
    else:
        render_unknown_status(status)


def show_simple_schedule_table(active_routes: List[Dict[str, Any]]) -> None:
    """Show simple schedule table as Gantt chart fallback.
    
    Args:
        active_routes: List of active route dictionaries.
    """
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
    """Render successful optimization results.
    
    Args:
        results: Optimization results from solver.
        final_total_packages: Total number of packages.
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
            cost_per_package = results["total_cost"] / final_total_packages
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
        df_routes = pd.DataFrame(results["tour_costs"])
        df_display = df_routes.copy()
        df_display = df_display.rename(columns={
            "from": "From",
            "to": "To", 
            "vehicles": "Vehicles",
            "packages": "Packages",
            "km": "Distance (km)",
            "cost": "Cost (€)"
        })
        df_display["Distance (km)"] = (df_display["Distance (km)"]
                                      .round(0).astype(int))
        df_display["Cost (€)"] = (df_display["Cost (€)"]
                                 .round(0).astype(int))
        st.dataframe(df_display, use_container_width=True)

    # Map Visualization
    st.subheader("🗺️ Route Map")
    if results.get("map_html"):
        st.components.v1.html(results["map_html"], height=500)

    # Vehicle Schedule
    st.subheader("⏱️ Vehicle Schedule")
    gantt_buffer: Optional[BytesIO] = None

    if results.get("active_routes"):
        # Check if backend provided Gantt chart
        if results.get("gantt_base64"):
            try:
                import base64
                gantt_data = base64.b64decode(results["gantt_base64"])
                gantt_buffer = BytesIO(gantt_data)
                st.image(gantt_buffer, 
                        caption="Vehicle Schedule Overview", 
                        use_container_width=True)
            except Exception as e:
                st.warning(f"⚠️ Could not display Gantt chart: {e}")
                st.info("📊 Showing schedule table instead")
                show_simple_schedule_table(results["active_routes"])
        else:
            st.info("📊 Backend provided no Gantt chart - showing "
                   "schedule table")
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
    """Render download options for results.
    
    Args:
        results: Optimization results.
        final_total_packages: Total number of packages.
        gantt_buffer: Gantt chart buffer (optional).
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
    excel_buffer = create_excel_summary(results, final_total_packages)
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
    """Create Excel summary of optimization results.
    
    Args:
        results: Optimization results.
        final_total_packages: Total number of packages.
        
    Returns:
        Excel file buffer ready for download.
    """
    excel_buffer = BytesIO()
    
    # Prepare summary data
    cost_per_package = ("N/A" if final_total_packages == 0 
                       else f"{results['total_cost']/final_total_packages:.2f}")
    
    summary_data = {
        "Metric": [
            "Total Cost (€)", 
            "Cost per Package (€)", 
            "Total Distance (km)", 
            "Solve Time (s)", 
            "Number of Routes"
        ],
        "Value": [
            f"{results['total_cost']:.2f}",
            cost_per_package,
            f"{results.get('total_km', 0):.0f}",
            f"{results.get('solve_time', 0):.1f}",
            f"{len(results.get('tour_costs', []))}"
        ]
    }
    
    packages_per_destination = st.session_state["packages_per_destination"]
    demand_data = {
        "City": list(packages_per_destination.keys()),
        "Packages": list(packages_per_destination.values())
    }
    
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        pd.DataFrame(summary_data).to_excel(
            writer, sheet_name='Summary', index=False)
        pd.DataFrame(demand_data).to_excel(
            writer, sheet_name='Demand', index=False)
        if results.get("tour_costs"):
            pd.DataFrame(results["tour_costs"]).to_excel(
                writer, sheet_name='Routes', index=False)
    
    excel_buffer.seek(0)
    return excel_buffer


def render_infeasible_results(final_total_packages: int) -> None:
    """Render infeasible optimization results.
    
    Args:
        final_total_packages: Total number of packages.
    """
    vehicle_capacity = CONFIG["VEHICLE_CAPACITY"]
    max_vehicles = CONFIG["MAX_VEHICLES_PER_ROUTE"]
    destination_cities = CONFIG["DESTINATION_CITIES"]
    
    st.error("❌ No feasible solution found!")
    st.markdown("""
    ### Possible reasons:
    - **Demand too high**: Some destinations may require more vehicles 
      than available
    - **Capacity constraints**: Package distribution exceeds vehicle 
      capacity limits  
    
    ### Quick fixes:
    - **Reduce package numbers** for distant cities
    - **Check your demand distribution** - is it realistic?
    """)
    
    if final_total_packages > 0:
        min_vehicles_needed = ((final_total_packages + vehicle_capacity - 1) 
                              // vehicle_capacity)
        system_capacity = (max_vehicles * vehicle_capacity * 
                          len(destination_cities))
        
        st.info(f"""
        ### 📊 Capacity Check:
        - **Total packages**: {final_total_packages:,}
        - **Vehicle capacity**: {vehicle_capacity} packages/vehicle
        - **Minimum vehicles needed**: {min_vehicles_needed}
        - **Max vehicles per route**: {max_vehicles}
        - **System capacity**: {system_capacity:,} packages
        """)
        
        if min_vehicles_needed > max_vehicles:
            st.error(f"🚨 **Problem identified**: You need "
                    f"{min_vehicles_needed} vehicles but only {max_vehicles} "
                    f"are allowed per route!")
            st.markdown("**Solution**: Reduce package numbers or increase "
                       "MAX_VEHICLES_PER_ROUTE in config.")


def render_failed_results(status: str, final_total_packages: int) -> None:
    """Render failed optimization results.
    
    Args:
        status: Solver status message.
        final_total_packages: Total number of packages.
    """
    hub = CONFIG["inject_hub"]
    time_limit = CONFIG["SOLVER_TIME_LIMIT_MS"]
    
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
    
    packages_per_destination = st.session_state["packages_per_destination"]
    active_destinations = len([
        city for city, pkg in packages_per_destination.items() 
        if pkg > 0 and city != hub
    ])
    
    with st.expander("🔧 Technical Details"):
        st.code(f"""
        Solver Status: {status}
        Total Packages: {final_total_packages}
        Active Destinations: {active_destinations}
        Time Limit: {time_limit/1000}s
        """)


def render_unknown_status(status: str) -> None:
    """Render unknown solver status results.
    
    Args:
        status: Unknown solver status message.
    """
    st.error(f"❌ Unknown solver status: {status}")
    st.info("Please try running the optimization again or check your "
           "input parameters.")


def main() -> None:
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()

    max_total_packages = CONFIG["MAX_TOTAL_PACKAGES"]

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
        help="Total packages to be distributed from injection hub to "
             "destination cities"
    )

    # Manual distribution checkbox
    manual_distribution = st.checkbox(
        "Enable manual per-city package input",
        key="manual_distribution",
        on_change=on_distribution_change,
        help="Manually specify packages for each destination instead of "
             "automatic distribution"
    )

    # Get package distribution
    packages_per_destination = get_package_distribution(
        manual_distribution, 
        st.session_state["total_packages"]
    )

    # Calculate final total packages
    if manual_distribution:
        final_total_packages = sum(packages_per_destination.values())
    else:
        final_total_packages = st.session_state["total_packages"]

    # Update session state
    st.session_state["packages_per_destination"] = packages_per_destination
    st.session_state["final_total_packages"] = final_total_packages

    # Render distribution preview
    render_distribution_preview(
        packages_per_destination, final_total_packages, manual_distribution)

    # Validation warning
    show_warning = final_total_packages == 0
    if show_warning:
        if manual_distribution:
            st.warning("🚨 Please enter package quantities for at least "
                      "one destination.")
        else:
            st.warning("🚨 Please define the total number of packages.")

    # Visual Demand Overview
    st.subheader("📍 Visual Demand Overview")

    # Create or update demand map
    if ("demand_map" not in st.session_state or 
        st.session_state.get("map_needs_update", True)):
        demand_map = create_demand_map(packages_per_destination)
        st.session_state["demand_map"] = demand_map
        st.session_state["map_needs_update"] = False

    # Display map
    st_folium(st.session_state["demand_map"], 
             height=400, use_container_width=True)

    # Technical specifications
    render_technical_specs()

    # Run Optimization section
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: grey;'>⚡ Optimized for speed "
        "- typically solves in under 30 seconds</p>",
        unsafe_allow_html=True
    )

    # Centered optimization button
    left, center, right = st.columns([1, 2, 1])
    run_button_disabled = final_total_packages == 0

    with center:
        run_clicked = st.button(
            "🚀 Optimize Routes", 
            help="Start route optimization with current package distribution",
            disabled=run_button_disabled,
            type="primary"
        )

    # Execute optimization
    if run_clicked and not run_button_disabled:
        with st.spinner("Optimizing routes... please wait"):
            config_dict = dict(CONFIG)
            user_input = {
                "demand": packages_per_destination,
                "config": config_dict
            }
            st.session_state["results"] = call_solver_api(user_input)

    # Show Results
    results = st.session_state.get("results")

    if results:
        render_results_section(results, final_total_packages)
    elif not show_warning:
        st.info("👆 Configure your package distribution above and click "
               "'Optimize Routes' to start")

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