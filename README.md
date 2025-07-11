# PathMatrix Optimizer – Intelligent Vehicle Routing Demo

[![Built with OR-Tools](https://img.shields.io/badge/Built%20with-Google%20OR--Tools-blue.svg?logo=google)](https://developers.google.com/optimization)

**PathMatrix Optimizer** is a web-based demo showcasing the power of mathematical optimization for vehicle routing problems. This minimal viable product (MVP) lets users simulate logistics scenarios by distributing packages across cities and solving for cost-optimal routes in real time.

---

## 🚀 What This Tool Does

This tool allows you to:

- Configure total package volume or manually assign city-level demand
- Solve the underlying Mixed Integer Program (MIP) using [Google OR-Tools](https://developers.google.com/optimization)
- Minimize total transport cost based on:
  - Distance
  - Vehicle capacity
  - Fixed minimum cost per trip
- Visualize routes on a map
- Generate vehicle schedules (Gantt chart)
- Download results as Excel or HTML files

---

## 🧠 How It Works

The app is split into a **Streamlit frontend** and a **FastAPI-powered backend** that runs the solver. The solver receives JSON-encoded input and returns optimized routing plans.

### Architecture

```text
Streamlit UI (Frontend)
│
▼
FastAPI Solver Endpoint (Backend)
│
▼
MIP Solver (Google OR-Tools)

```

The core problem is formulated as a **network flow optimization** problem using:

- Vehicle count and package flow variables
- Capacity and conservation constraints
- Cost functions combining per-km cost and minimum per-trip cost
- Solve-time control and Gantt chart visualization

---

## ⚙️ Current Features

| Feature                         | Status     |
|----------------------------------|------------|
| Fixed depot (injection hub)      | ✅ Enabled  |
| Vehicle capacity constraints     | ✅ Enforced |
| Package distribution logic       | ✅ Manual/Auto |
| Route cost minimization          | ✅ Active   |
| Visual route maps                | ✅ Included |
| Gantt chart generation           | ✅ Enabled  |
| Excel export                     | ✅ Ready    |
| Time windows & breaks            | 🚧 Planned  |
| Vehicle type selection           | 🚧 Planned  |
| Weight/volume limits             | 🚧 Planned  |

---

## 🧪 Why It’s Special

While many tools rely on heuristics, PathMatrix Optimizer uses **real mathematical optimization**.  
The current model focuses on simplicity, but already supports:

- Full MIP-based cost minimization
- Real-world constraints like vehicle capacity and cost thresholds
- Easily extendable backend API architecture

---

## 🔬 Use Cases

- Cost estimation for same-day delivery services
- Demand simulation for multi-destination transport
- Scenario testing for logistics planners
- Educational demonstration for Operations Research

---

## 📝 Demo Disclaimer

This is a **demo version** intended for experimentation and exploration.  
It is not production-ready and does not include full error handling, user authentication, or advanced time constraints (yet).

---

## 🛣 Future Plans

- Time windows and driver break logic
- Multiple vehicle classes with speed/cost parameters
- Multi-hub network support
- CO₂-aware optimization
- Integration with real-time or batch demand

---

## 🔌 API Endpoint & Backend Protection

The solver API is deployed at:

POST https://pathmatrix-solver-api.onrender.com/solve

⚠️ This endpoint is intended for use via the frontend application or custom tools only.  
Direct browser access will return `405 Method Not Allowed`.

🔒 The backend solver logic is **not part of this repository** and is considered **proprietary**.  
All intellectual property rights remain with the author and are **not licensed under the MIT license**.

For collaboration or licensing inquiries, please contact the maintainer.