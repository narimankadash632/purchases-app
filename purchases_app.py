import streamlit as st
import pandas as pd
from datetime import datetime
import os
    
FILE_NAME = "purchases.csv"

COLUMNS = [
    "Дата", "ФИО", "Номер телефона", "Наименование товара",
    "Цена", "Количество", "Сумма покупки", "Сумма накопления", "Бонусы"
]

# Загрузка данных или создание пустого датафрейма
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = pd.DataFrame(columns=COLUMNS)


def recalculate_data(data, bonus_percent=0.0):
    if data.empty:
        return data.copy()
    data = data.copy()
    data["Цена"] = pd.to_numeric(data["Цена"], errors="coerce").fillna(0.0)
    data["Количество"] = pd.to_numeric(
        data["Количество"], errors="coerce").fillna(0).astype(int)
    data["Номер телефона"] = data["Номер телефона"].fillna("").astype(str)
    data["Сумма покупки"] = data["Цена"] * data["Количество"]
    data["Дата_parsed"] = pd.to_datetime(
        data["Дата"], errors="coerce").fillna(pd.Timestamp("1970-01-01"))
    data["Сумма накопления"] = 0.0
    data["Бонусы"] = 0.0
    for phone, group in data.groupby("Номер телефона", sort=False):
        total = 0.0
        for idx in group.sort_values("Дата_parsed", ascending=True).index:
            total += data.at[idx, "Сумма покупки"]
            data.at[idx, "Сумма накопления"] = total
            data.at[idx, "Бонусы"] = round(total * (bonus_percent / 100), 2)
    data = data.sort_values("Дата_parsed", ascending=False).drop(
        columns=["Дата_parsed"]).reset_index(drop=True)
    data = data.reindex(columns=COLUMNS)
    return data


st.title("Учёт покупок и бонусов")

bonus_percent = st.number_input(
    "Процент бонуса (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)

with st.form("add_purchase"):
    date = st.date_input("Дата покупки", datetime.now())
    name = st.text_input("ФИО")
    phone = st.text_input("Номер телефона")
    product = st.text_input("Наименование товара")
    price = st.number_input("Цена", min_value=0.0, step=0.01, format="%.2f")
    quantity = st.number_input("Количество", min_value=1, step=1)

    submitted = st.form_submit_button("Добавить запись")
    if submitted:
        if not name or not phone or not product:
            st.error("Заполните ФИО, номер телефона и товар.")
        else:
            new_row = {
                "Дата": date.strftime("%Y-%m-%d"),
                "ФИО": name,
                "Номер телефона": phone,
                "Наименование товара": product,
                "Цена": price,
                "Количество": quantity,
                "Сумма покупки": price * quantity,
                "Сумма накопления": 0,
                "Бонусы": 0
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df = recalculate_data(df, bonus_percent=bonus_percent)
            df.to_csv(FILE_NAME, index=False)
            st.success("Запись добавлена!")

search_phone = st.text_input(
    "Поиск по номеру телефона (оставьте пустым, чтобы показать всех)")

if search_phone.strip():
    mask = df["Номер телефона"].astype(
        str).str.contains(search_phone.strip(), na=False)
    filtered_df = df[mask]
    if filtered_df.empty:
        st.info("Клиент не найден.")
    else:
        st.dataframe(filtered_df)
        
else:
    st.dataframe(df)
    

st.markdown("---")
st.write("Удаление записей")
delete_indices = st.multiselect(
    "Выберите индексы для удаления", options=df.index.tolist())

if st.button("Удалить выбранные записи"):
    if delete_indices:
        df = df.drop(index=delete_indices).reset_index(drop=True)
        df = recalculate_data(df, bonus_percent=bonus_percent)
        df.to_csv(FILE_NAME, index=False)
        st.success("Записи удалены!")
        st.experimental_rerun()
    else:
        st.warning("Выберите записи для удаления.")
