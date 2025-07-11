# PathMatrix Optimizer - API Reference

> **Function signatures, parameters, and usage for developers**

This document focuses **only on the API** - function signatures, parameters, return values, and basic usage. For project overview, see the [README](../README.md).

## Table of Contents

- [Core API Functions](#core-api-functions)
- [Configuration API](#configuration-api)
- [Data Types](#data-types)
- [Quick Examples](#quick-examples)

---

## Core API Functions

### `call_solver_api(input_data: Dict[str, Any]) -> Dict[str, Any]`

**Primary optimization function** - sends requests to the OR-Tools solver.

**Parameters:**
- `input_data`: Dictionary with keys:
  - `"demand"`: PackageDistribution (Dict[str, int])
  - `"config"`: ConfigDict

**Returns:**
Dictionary with keys:
- `"solver_status"`: str - "OPTIMAL", "FEASIBLE", "INFEASIBLE", or "FAILED: ..."
- `"total_cost"`: float - Total cost in euros
- `"total_km"`: float - Total distance in kilometers  
- `"solve_time"`: float - Solver time in seconds
- `"tour_costs"`: List[Dict] - Route details (from, to, vehicles, packages, km, cost)
- `"map_html"`: str - HTML map visualization (optional)
- `"gantt_base64"`: str - Base64 Gantt chart (optional)
- `"active_routes"`: List[Dict] - Vehicle assignments (optional)

**Example:**
```python
results = call_solver_api({
    "demand": {"Berlin": 100, "Munich": 150},
    "config": CONFIG
})

if results["solver_status"] == "OPTIMAL":
    print(f"Cost: €{results['total_cost']:.2f}")
```

---

### `get_package_distribution(manual_distribution: bool, total_packages: int) -> PackageDistribution`

**Calculate package distribution** across cities.

**Parameters:**
- `manual_distribution`: bool - If True, uses Streamlit widgets for manual input
- `total_packages`: int - Total packages for automatic distribution (ignored if manual_distribution=True)

**Returns:**
- `PackageDistribution` (Dict[str, int]): City name → package count

**Example:**
```python
# Automatic distribution using CONFIG percentages
packages = get_package_distribution(False, 1000)
# Returns: {"Berlin": 280, "Munich": 150, ...}

# Manual distribution (requires Streamlit context)
packages = get_package_distribution(True, 0)
```

---

### `create_demand_map(packages_per_destination: PackageDistribution) -> folium.Map`

**Generate interactive map** with demand visualization.

**Parameters:**
- `packages_per_destination`: PackageDistribution - City → package count mapping

**Returns:**
- `folium.Map`: Interactive map object with proportional markers

**Example:**
```python
map_obj = create_demand_map({"Berlin": 200, "Munich": 150})
# Use with Streamlit: st_folium(map_obj, height=400)
```

---

### `initialize_session_state() -> None`

**Initialize Streamlit session state** with default values.

**Parameters:** None  
**Returns:** None

**Required before** using other functions in Streamlit context.

```python
initialize_session_state()  # Call once at app start
```

---

## Configuration API

### `CONFIG: ConfigDict`

**Global configuration object** with all system parameters.

**Key Parameters:**
- `CONFIG["VEHICLE_CAPACITY"]`: int (200) - Packages per vehicle
- `CONFIG["MAX_VEHICLES_PER_ROUTE"]`: int (10) - Maximum vehicles per route
- `CONFIG["COST_PER_KM"]`: float (1.0) - Cost per kilometer in euros
- `CONFIG["MIN_COST_PER_TRIP"]`: int (100) - Minimum cost per trip in euros
- `CONFIG["inject_hub"]`: str ("Dortmund") - Central distribution hub
- `CONFIG["CITY_COORDINATES"]`: Dict[str, Tuple[float, float]] - GPS coordinates
- `CONFIG["DEFAULT_DISTRIBUTION_PERCENT"]`: Dict[str, int] - Auto-distribution percentages
- `CONFIG["SOLVER_TIME_LIMIT_MS"]`: int (60000) - Solver timeout in milliseconds

**Usage:**
```python
# Read configuration
hub = CONFIG["inject_hub"]              # "Dortmund"
capacity = CONFIG["VEHICLE_CAPACITY"]   # 200

# Create custom configuration
custom_config = CONFIG.copy()
custom_config["VEHICLE_CAPACITY"] = 300  # Modify as needed
```

---

### `ConfigDict`

**Type definition** for configuration schema.

```python
class ConfigDict(TypedDict):
    VEHICLE_CAPACITY: int
    MAX_VEHICLES_PER_ROUTE: int
    COST_PER_KM: float
    MIN_COST_PER_TRIP: int
    inject_hub: str
    CITY_COORDINATES: Dict[str, Tuple[float, float]]
    DEFAULT_DISTRIBUTION_PERCENT: Dict[str, int]
    SOLVER_TIME_LIMIT_MS: int
    # ... and more
```

---

## Data Types

### `PackageDistribution`

```python
PackageDistribution = Dict[str, int]
```

Dictionary mapping city names to package counts.

**Example:**
```python
packages: PackageDistribution = {
    "Berlin": 150,
    "Munich": 200,
    "Hamburg": 100
}
```

---

### Solver Response Structure

```python
{
    "solver_status": str,        # "OPTIMAL" | "FEASIBLE" | "INFEASIBLE" | "FAILED: ..."
    "total_cost": float,         # Total euros
    "total_km": float,           # Total kilometers
    "solve_time": float,         # Seconds
    "tour_costs": [              # Route details
        {
            "from": str,         # Origin city
            "to": str,           # Destination city  
            "vehicles": int,     # Number of vehicles
            "packages": int,     # Packages on route
            "km": float,         # Distance
            "cost": float        # Route cost
        }
    ]
}
```

---

## Quick Examples

### Basic Optimization

```python
import app

# Initialize (required for Streamlit)
app.initialize_session_state()

# Define demand
demand = {"Berlin": 150, "Munich": 200}

# Optimize routes
results = app.call_solver_api({
    "demand": demand,
    "config": app.CONFIG
})

# Check results
if results["solver_status"] == "OPTIMAL":
    print(f"Total cost: €{results['total_cost']:.2f}")
    print(f"Number of routes: {len(results['tour_costs'])}")
```

### Custom Configuration

```python
# Modify configuration
custom_config = app.CONFIG.copy()
custom_config["VEHICLE_CAPACITY"] = 300
custom_config["COST_PER_KM"] = 1.5

# Use custom config
results = app.call_solver_api({
    "demand": demand,
    "config": custom_config
})
```

### Map Visualization

```python
# Create demand map
demand_map = app.create_demand_map(demand)

# In Streamlit app:
from streamlit_folium import st_folium
st_folium(demand_map, height=400, use_container_width=True)
```

---

**For complete function reference with all docstrings:** [FUNCTION_REFERENCE.md](FUNCTION_REFERENCE.md)  
**For user documentation:** [README.md](../README.md)