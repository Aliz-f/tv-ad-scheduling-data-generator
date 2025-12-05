# TV Ad Scheduling Data Generator

Synthetic instance generator for the **TV advertising scheduling** problem.  
This tool creates realistic test data for:

- A **mathematical MILP model** (CPLEX-friendly JSON format)
- **Metaheuristic algorithms** (e.g., NSGA-II, SA, Tabu Search)

The generator constructs random but structured schedules of TV commercial breaks, advertisers, budgets, reach
requirements, penalties, and competitor relationships.

> All core logic is implemented in Python and outputs two JSON formats:
> - `data_nsga/` – detailed, time-based instances for metaheuristics
> - `data_cplex/` – normalized and scaled instances suitable for CPLEX models

---

## Features

- Random generation of:
    - TV **breaks** (number, duration, start/end times)
    - **Commercials** (IDs, duration, min/max plays)
    - **Price** and **reach** per position in each break
    - **Release** and **due** times for each ad
    - **Budgets** and **minimum reach** requirements
    - **Competitor pairs** (ads from rival advertisers that cannot be in the same break)
- Automatic derivation of:
    - Time horizon (`start_planning_horizon`, `end_planning_horizon`)
    - Planning **scale** (in hours)
- Dual data export:
    - Raw instance for metaheuristics (`data_nsga`)
    - Converted instance with time/price scaling for MILP/CPLEX (`data_cplex`)

---

## Repository Structure

```text
.
├── data_generator.py      # Main script to generate instances
├── cplex_wrapper.py       # Converts raw data to CPLEX-friendly scale
├── config.json            # Configuration file (you define this)
└── data/
    ├── data_nsga/         # Raw generated instances (metaheuristics)
    └── data_cplex/        # Scaled instances for CPLEX
````

> The `data/` directory is created automatically if it does not exist.

---

## Installation

### Requirements

* **Python** ≥ 3.8
* Dependencies:

    * `numpy`
    * `loguru`

Install dependencies with:

```bash
pip install -r requirements.txt
```

---

## Configuration (`config.json`)

The generator is fully driven by a JSON configuration file.
`data_generator.py` expects a file named `config.json` in the same directory.

### Required keys

From `GenerateData.read_config`, the following fields are required:

* `scale` – label or size tag for the instance (used in filenames; string or int)

* `name` – scenario/instance name (string)

* `schedule_start_time` – planning horizon start, format:
  `"YYYY-MM-DD HH:MM:SS"`

* `schedule_end_time` – planning horizon end, format:
  `"YYYY-MM-DD HH:MM:SS"`

* `commercial_count` – **list** of possible total numbers of commercials
  (one value is chosen randomly with `random.choice`)

* `commercial_duration` – **list** of possible commercial durations (seconds)

* `commercial_minimum_play` – **list** of possible minimum play counts

* `commercial_maximum_play` – **list** of possible maximum play counts

* `break_count` – **list** of possible numbers of breaks

* `break_duration` – **list** of possible break durations (seconds)

* `budget_chance` – **list** of percentages used to randomize budgets

* `reach_chance` – **list** of percentages used to randomize reach targets

* `price_range` – **list** of base values for price per position

* `reach_range` – **list** of base values for reach per position

* `penalty` – **list** of penalty values for not satisfying constraints

* `competitors_count` – integer, number of advertiser pairs to mark as competitors

### Example `config.json`

You can adapt this to your own scales:

```json
{
  "scale": "small",
  "name": "baseline_instance",
  "schedule_start_time": "2025-01-01 20:00:00",
  "schedule_end_time": "2025-01-01 23:00:00",
  "commercial_count": [
    10,
    12,
    15
  ],
  "commercial_duration": [
    20,
    30,
    40
  ],
  "commercial_minimum_play": [
    1,
    2
  ],
  "commercial_maximum_play": [
    3,
    4,
    5
  ],
  "break_count": [
    5,
    6,
    7
  ],
  "break_duration": [
    120,
    150,
    180
  ],
  "budget_chance": [
    10,
    20,
    30
  ],
  "reach_chance": [
    10,
    20,
    30
  ],
  "price_range": [
    5,
    6,
    7,
    8
  ],
  "reach_range": [
    100,
    120,
    140
  ],
  "penalty": [
    10,
    20,
    30
  ],
  "competitors_count": 5
}
```

---

## How the Generator Works

The main script is `data_generator.py`.
Its high-level flow:

1. **Read configuration** from `config.json`

```python
data = GenerateData.read_config("config.json")
```

2. Initialize planning horizon:

```python
generated_data['start_planning_horizon'] = data['schedule_start_time']
generated_data['end_planning_horizon'] = data['schedule_end_time']
```

3. **Generate breaks** (`manage_break`)

    * Randomly choose the number of breaks from `break_count`
    * For each break, randomly choose a duration from `break_duration`
    * Create a list of breaks with exact `start` and `end` timestamps

4. **Generate commercials** (`manage_commercial`)

    * Number of commercials from `commercial_count`
    * Create random names like `A-123`, `Q-45`, etc.
    * Assign durations from `commercial_duration`
    * Assign minimum/maximum play counts (from `commercial_minimum_play`, `commercial_maximum_play`)
    * Assign penalties from `penalty`

5. **Generate competitor pairs** (`manage_competitors`)

    * Randomly sample pairs of commercial names as competitors
    * Stored as a list of 2-element lists/tuples

6. **Generate release and due times** (`manage_commercial_time`)

    * For each commercial:

        * Select a random release time within early breaks
        * Compute a feasible window so that all required plays can fit before the end
        * Generate a random due time within the planning horizon

7. **Generate price and reach grids** (`manage_price_reach`)

    * For each break:

        * Determine the maximum number of positions based on break duration and minimum commercial duration
        * For each position:

            * Set price and reach values with a “hill-shaped” pattern: increase then decrease (or vice versa) across
              positions
    * Stored as 2D arrays: `price[break][position]`, `reach[break][position]`

8. **Generate budgets and required reach** (`manage_budget_reach`)

    * Use average price/reach from the matrix
    * For each commercial:

        * Estimate a baseline budget and reach based on its duration and copy count
        * Randomize using `budget_chance` and `reach_chance`

9. **Save raw data** (`data_nsga`)

    * Convert `price` and `reach` arrays to Python lists (JSON-serializable)
    * Write to:

      ```text
      data/data_nsga/{scale}_{today_date}_{name}.json
      ```

10. **Run CPLEX wrapper** (`cplex_wrapper`)

    * Call:

      ```python
      converted_data = cplex_wrapper(generated_data)
      ```
    * Convert:

        * Time to discrete units (seconds / 10)
        * Prices, reach, and penalties to scaled values
        * Budgets and required reach scaled down

11. **Save converted data** (`data_cplex`)

    * Write to:

      ```text
      data/data_cplex/{scale}_{today_date}_{name}.json
      ```

---

## Running the Generator

From the repository root:

```bash
python data_generator.py
```

* Ensure `config.json` is present.
* After running, you should see:

```text
data/
  data_nsga/
    <scale>_<YYYY-MM-DD>_<name>.json
  data_cplex/
    <scale>_<YYYY-MM-DD>_<name>.json
```

For example:

```text
data/data_nsga/small_2025-01-01_baseline_instance.json
data/data_cplex/small_2025-01-01_baseline_instance.json
```

---

## Output JSON Structure (Raw `data_nsga`)

Key fields in the raw (non-converted) JSON:

* `start_planning_horizon` (string)

* `end_planning_horizon` (string)

* `breaks` (int) – number of breaks

* `break_duration` (list[int]) – break durations in seconds

* `break_length` (list[{"start": str, "end": str}]) – exact timestamps for each break

* `commercials` (int) – number of commercials

* `name` (list[str]) – commercial IDs, e.g., `"A-23"`

* `commercial_duration` (list[int]) – durations in seconds

* `commercial_copy` (list[{"min": int, "max": int}]) – min and max play counts

* `penalty` (list[float or int]) – penalty for that commercial

* `competitors` (list[[str, str]]) – list of competitor pairs

* `release_time` (list[str]) – earliest allowed airing times

* `due_time` (list[str]) – latest times by which full airing must be completed

* `price` (list[list[float]]) – price grid per break/position

* `reach` (list[list[float]]) – reach grid per break/position

* `budget` (list[int]) – budgets per commercial

* `required_reach` (list[int]) – minimum reach per commercial

---

## Output JSON Structure (Converted `data_cplex`)

The CPLEX wrapper (`cplex_wrapper.py`) applies several conversions:

* **Time scaling to 10-second units**:

    * `commercial_duration`: divide by 10
    * `break_duration`: divide by 10
    * `break_length[i].start`, `break_length[i].end`:

        * offset from `start_planning_horizon`
        * measured in 10-second units
    * `release_time[]`, `due_time[]`:

        * offset from `start_planning_horizon`
        * measured in 10-second units

* **Planning horizon scale**:

    * `scale`: total length of horizon in **hours**

* **Budget and reach scaling**:

    * `budget[i] /= 100`
    * `required_reach[i] /= 100`

* **Price, reach, penalty scaling**:

    * `price[break][pos] /= 10`
    * `reach[break][pos] /= 10`
    * `penalty[i] /= 10`

The resulting JSON is more compact and numerically suitable for MILP models in CPLEX.

---

## Using the Data

Typical usage:

* **Metaheuristics repo (e.g., NSGA-II, SA, Tabu)**:
    * Read from `data/data_nsga/*.json`
    * Use timestamps and full-resolution times if needed
* **Mathematical model / CPLEX repo**:
    * Read from `data/data_cplex/*.json`
    * Use discrete time units and scaled monetary/reach values in the MILP

---

## Extending the Generator

You can easily extend this project by:

* Adding new fields to `config.json` (e.g., different ad categories)
* Changing the distributions in:
    * `manage_price_reach` (price/reach profiles)
    * `manage_budget_reach` (budget/reach randomness)
* Controlling randomness via a seed:

```python
import random
import numpy as np

random.seed(42)
np.random.seed(42)
```
---

## Relation to the Overall Project

This MILP model is one of three main components of the TV scheduling thesis project:

1. Data Generator (this repo)

    * Generates synthetic instances (breaks, commercials, budgets, reach, etc.)
    * Exports JSON for NSGA-II/metaheuristics and for CPLEX (scaled).

2. [**MILP Model**](https://github.com/Aliz-f/tv-ad-scheduling-milp-model)

    * Reads CPLEX-ready JSON.
    * Solves the scheduling problem exactly (within MIP gap limits).

3. [**Metaheuristic Algorithms**](https://github.com/Aliz-f/tv-ad-scheduling-metaheuristics)

    * NSGA-II, simulated annealing, tabu search.
    * Use the same data to compare against MILP performance.

