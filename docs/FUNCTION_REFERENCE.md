# PathMatrix Optimizer - Function Reference

> **Auto-generated from source code docstrings**  
> Version: `f83cdfe` | Last updated: `2025-07-11 11:13 UTC`

This document contains the complete function reference extracted from the source code. For a developer-friendly guide, see [API_REFERENCE.md](API_REFERENCE.md).

## Table of Contents

- [Classes](#classes)
- [Functions](#functions)
  - [Core Functions](#core-functions)
  - [Other Functions](#other-functions)
  - [UI Functions](#ui-functions)
  - [Utility Functions](#utility-functions)

---

## Module Description

PathMatrix Optimizer Demo - Streamlit app for vehicle routing optimization.

This application provides a web interface for optimizing vehicle routes
from a central hub to multiple destinations using OR-Tools.
Refactored with TypedDict for clean, type-safe configuration.


---

## Classes

### `ConfigDict`

**File:** `app.py` | **Line:** 23

**Inherits from:** TypedDict

**Description:**
Complete type-safe configuration schema for the optimizer.

---

## Functions

### Core Functions

#### `call_solver_api`

**File:** `app.py` | **Line:** 161

```python
def call_solver_api(input_data: Dict[(str, Any)]) -> Dict[(str, Any)]
```

**Description:**
Call the solver API with error handling.

Args:
    input_data: Dictionary containing configuration and demand data.
    
Returns:
    Dictionary containing solver results or error information.
    Keys include 'solver_status', 'total_cost', 'tour_costs', etc.

**Arguments:**
- `input_data` (Dict[(str, Any)])

**Returns:**
- `Dict[(str, Any)]`

---

#### `create_demand_map`

**File:** `app.py` | **Line:** 361

```python
def create_demand_map(packages_per_destination: PackageDistribution) -> folium.Map
```

**Description:**
Create a folium map showing demand distribution.

Args:
    packages_per_destination: Package distribution by city.
    
Returns:
    Folium map object with demand visualization.

**Arguments:**
- `packages_per_destination` (PackageDistribution)

**Returns:**
- `folium.Map`

---

#### `get_package_distribution`

**File:** `app.py` | **Line:** 280

```python
def get_package_distribution(manual_distribution: bool, total_packages: int) -> PackageDistribution
```

**Description:**
Get package distribution based on distribution mode.

Args:
    manual_distribution: Whether to use manual distribution mode.
    total_packages: Total packages for automatic distribution.
    
Returns:
    Dictionary mapping city names to package counts.

**Arguments:**
- `manual_distribution` (bool)
- `total_packages` (int)

**Returns:**
- `PackageDistribution`

---

### Other Functions

#### `create_excel_summary`

**File:** `app.py` | **Line:** 647

```python
def create_excel_summary(results: Dict[(str, Any)], final_total_packages: int) -> BytesIO
```

**Description:**
Create Excel summary of optimization results.

Args:
    results: Optimization results.
    final_total_packages: Total number of packages.
    
Returns:
    Excel file buffer ready for download.

**Arguments:**
- `results` (Dict[(str, Any)])
- `final_total_packages` (int)

**Returns:**
- `BytesIO`

---

#### `main`

**File:** `app.py` | **Line:** 799

```python
def main() -> None
```

**Description:**
Main application entry point.

**Returns:**
- `None`

---

#### `show_simple_schedule_table`

**File:** `app.py` | **Line:** 486

```python
def show_simple_schedule_table(active_routes: List[Dict[(str, Any)]]) -> None
```

**Description:**
Show simple schedule table as Gantt chart fallback.

Args:
    active_routes: List of active route dictionaries.

**Arguments:**
- `active_routes` (List[Dict[(str, Any)]])

**Returns:**
- `None`

---

### UI Functions

#### `render_distribution_preview`

**File:** `app.py` | **Line:** 327

```python
def render_distribution_preview(packages_per_destination: PackageDistribution, final_total_packages: int, manual_distribution: bool) -> None
```

**Description:**
Render package distribution preview.

Args:
    packages_per_destination: Package distribution by city.
    final_total_packages: Total number of packages.
    manual_distribution: Whether manual distribution is enabled.

**Arguments:**
- `packages_per_destination` (PackageDistribution)
- `final_total_packages` (int)
- `manual_distribution` (bool)

**Returns:**
- `None`

---

#### `render_download_options`

**File:** `app.py` | **Line:** 603

```python
def render_download_options(results: Dict[(str, Any)], final_total_packages: int, gantt_buffer: Optional[BytesIO]) -> None
```

**Description:**
Render download options for results.

Args:
    results: Optimization results.
    final_total_packages: Total number of packages.
    gantt_buffer: Gantt chart buffer (optional).

**Arguments:**
- `results` (Dict[(str, Any)])
- `final_total_packages` (int)
- `gantt_buffer` (Optional[BytesIO])

**Returns:**
- `None`

---

#### `render_failed_results`

**File:** `app.py` | **Line:** 748

```python
def render_failed_results(status: str, final_total_packages: int) -> None
```

**Description:**
Render failed optimization results.

Args:
    status: Solver status message.
    final_total_packages: Total number of packages.

**Arguments:**
- `status` (str)
- `final_total_packages` (int)

**Returns:**
- `None`

---

#### `render_infeasible_results`

**File:** `app.py` | **Line:** 702

```python
def render_infeasible_results(final_total_packages: int) -> None
```

**Description:**
Render infeasible optimization results.

Args:
    final_total_packages: Total number of packages.

**Arguments:**
- `final_total_packages` (int)

**Returns:**
- `None`

---

#### `render_introduction`

**File:** `app.py` | **Line:** 236

```python
def render_introduction() -> None
```

**Description:**
Render the application introduction section.

**Returns:**
- `None`

---

#### `render_results_section`

**File:** `app.py` | **Line:** 461

```python
def render_results_section(results: Optional[Dict[(str, Any)]], final_total_packages: int) -> None
```

**Description:**
Render the optimization results section.

Args:
    results: Optimization results from solver.
    final_total_packages: Total number of packages.

**Arguments:**
- `results` (Optional[Dict[(str, Any)]])
- `final_total_packages` (int)

**Returns:**
- `None`

---

#### `render_successful_results`

**File:** `app.py` | **Line:** 513

```python
def render_successful_results(results: Dict[(str, Any)], final_total_packages: int) -> None
```

**Description:**
Render successful optimization results.

Args:
    results: Optimization results from solver.
    final_total_packages: Total number of packages.

**Arguments:**
- `results` (Dict[(str, Any)])
- `final_total_packages` (int)

**Returns:**
- `None`

---

#### `render_technical_specs`

**File:** `app.py` | **Line:** 437

```python
def render_technical_specs() -> None
```

**Description:**
Render the technical specifications section.

**Returns:**
- `None`

---

#### `render_unknown_status`

**File:** `app.py` | **Line:** 788

```python
def render_unknown_status(status: str) -> None
```

**Description:**
Render unknown solver status results.

Args:
    status: Unknown solver status message.

**Arguments:**
- `status` (str)

**Returns:**
- `None`

---

### Utility Functions

#### `initialize_session_state`

**File:** `app.py` | **Line:** 210

```python
def initialize_session_state() -> None
```

**Description:**
Initialize all session state variables with default values.

**Returns:**
- `None`

---

#### `on_distribution_change`

**File:** `app.py` | **Line:** 226

```python
def on_distribution_change() -> None
```

**Description:**
Mark map for update when distribution mode changes.

**Returns:**
- `None`

---

#### `on_packages_change`

**File:** `app.py` | **Line:** 231

```python
def on_packages_change() -> None
```

**Description:**
Mark map for update when package values change.

**Returns:**
- `None`

---


*This documentation was automatically generated from source code docstrings.*  
*For questions or corrections, please see the [API Reference](API_REFERENCE.md) or [open an issue](https://github.com/your-username/pathmatrix-optimizer/issues).*

**Generation Info:**
- Source: `app.py`
- Version: `f83cdfe`
- Generated: `2025-07-11 11:13 UTC`
- Python: `3.13.2`
