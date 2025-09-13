# Afforestation Model Frontend

This is a React.js web app for simulating the climate impact of tree planting. Enter tree species, years, and number of trees to see CO₂ sequestration results, powered by a Python backend.

## Features
- Nature-inspired, modern UI
- User input for species, years, and tree count
- Results and chart visualization
- Connects to Flask backend API

## Getting Started
1. Run the Flask backend (`python app.py` in the parent folder)
2. Start the frontend:
   ```sh
   npm run dev
   ```
3. Open the app in your browser (usually http://localhost:5173)

## Customization
- Update design in `src/App.jsx` and CSS files
- API endpoint is `/api/simulate` (edit in `src/api.js` if needed)

---

# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
