# Customer Spending Prediction

An end-to-end Machine Learning project predicting total customer spending based on demographic and behavioral data.

## Project Structure
- `backend/`: FastAPI server and XGBoost model pipeline.
- `notebooks/`: Jupyter notebooks for EDA and model training.
- `app.py`: Streamlit frontend application.

## Tech Stack
- **Model:** XGBoost Regression, Scikit-learn
- **Backend:** FastAPI, Uvicorn
- **Frontend:** Streamlit

## Local Setup
1. Clone the repository.
2. Run Backend: `cd backend && pip install -r requirements.txt && python -m uvicorn main:app --reload`
3. Run Frontend (in a new terminal): `pip install -r requirements.txt && python -m streamlit run app.py`