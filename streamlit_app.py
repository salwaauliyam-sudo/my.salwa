import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

st.title("Aplikasi Regresi Linear")

file = st.file_uploader("Upload file CSV", type="csv")

if file:
    df = pd.read_csv(file)
    st.subheader("Data")
    st.dataframe(df.head())

    kolom = df.select_dtypes(include="number").columns.tolist()
    x_col = st.selectbox("Variabel X", kolom)
    y_col = st.selectbox("Variabel Y", kolom, index=min(1, len(kolom) - 1))

    X = df[[x_col]].values
    y = df[y_col].values

    model = LinearRegression().fit(X, y)
    st.write(f"Koefisien: {model.coef_[0]:.4f}")
    st.write(f"Intersep: {model.intercept_:.4f}")
    st.write(f"R²: {model.score(X, y):.4f}")

    fig, ax = plt.subplots()
    ax.scatter(X, y, label="Data")
    ax.plot(X, model.predict(X), color="red", label="Regresi")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.legend()
    st.pyplot(fig)
