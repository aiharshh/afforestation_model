# Afforestation CO₂ Sequestration Calculator

A simple web app to estimate the amount of CO₂ sequestered by planting trees of different species over time. Built with Python and Flask, this project provides an easy-to-use interface for users to select tree species, number of trees, and years, and view the estimated CO₂ sequestration results.

## Features
- Select tree species from a dropdown menu
- Input number of trees and years
- View yearly CO₂ sequestration and summary
- Clean, modern UI (HTML/CSS)
- No React or frontend build tools required

## Getting Started

### 1. Clone the Repository
```sh
git clone https://github.com/aiharshh/afforestation_model.git
cd afforestation_model
```

### 2. Set Up Python Environment
It is recommended to use a virtual environment:
```sh
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Required Libraries
Install dependencies using pip:
```sh
pip install flask pandas
```
You may need additional libraries if your `src/` code requires them (e.g., numpy). Add them to `requirement.txt` as needed.

### 4. Prepare Data Files
Ensure the following data files are present in the `data/` folder:
- `species_master_filled.csv`
- `growth_curves_filled.csv`

These files should contain the necessary species and growth data for the model to work.

### 5. Run the App
```sh
python app.py
```
The app will start on `http://localhost:5050/`.

### 6. Use the Web Interface
- Open your browser and go to `http://localhost:5050/`
- Select tree species, enter years and number of trees
- Click "Simulate" to view results

## Project Structure
```
├── app.py                  # Main Flask app (serves HTML form and handles logic)
├── src/                    # Python modules for data/model logic
│   ├── data_loader.py
│   ├── model.py
│   └── ...
├── data/                   # Data files (CSV)
│   ├── species_master_filled.csv
│   └── growth_curves_filled.csv
├── requirement.txt         # List of required Python packages
├── main.py                 # (Optional) CLI or other entry point
└── README.md               # This file
```

## Description
This project helps users estimate the impact of afforestation by calculating the total CO₂ sequestered by planting a given number of trees of a selected species over a specified number of years. The model uses species-specific growth curves and biomass-to-CO₂ conversion formulas.

## How It Works
1. User selects species, years, and number of trees.
2. The app loads growth and species data from CSV files.
3. It calculates yearly biomass and converts it to CO₂ sequestered.
4. Results are displayed in a summary and as yearly values.

## Contributing
Pull requests and suggestions are welcome! Please open an issue for bugs or feature requests.

## License
MIT License

## Author
Asmita Bag & Harsh Hublikar

---
If you have any questions or need help deploying, feel free to reach out!
