import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# ---------- вспомогательные функции ----------
def generate_sample_df() -> pd.DataFrame:
    """Создаёт псевдореальные данные потребления на сутки (24 ч)."""
    np.random.seed(42)
    hours = list(range(24))
    consumption = [
        np.random.uniform(1.5, 2.5) if h < 6 or h > 22        # ночь
        else np.random.uniform(3.0, 4.5) if 6 <= h < 17       # рабочий день
        else np.random.uniform(6.0, 8.5)                      # вечерний пик
        for h in hours
    ]
    return pd.DataFrame({"Час": hours, "Потребление (кВт·ч)": consumption})


def load_file(file) -> pd.DataFrame:
    """Читает CSV или Excel, возвращает DataFrame."""
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)
# ------------------------------------------------


st.set_page_config(page_title="Энерго-MVP", page_icon="🔋", layout="centered")
st.title("🔋 Мониторинг энергопотребления и расчёт экономии")

uploaded = st.file_uploader(
    "Загрузите CSV или Excel с колонками «Час» и «Потребление (кВт·ч)»",
    type=["csv", "xlsx"],
)

# ---- получаем данные: файл или генерация ----
if uploaded is None:
    st.info("Файл не выбран. Можно создать тестовые данные.")
    if not st.button("Сгенерировать тестовые данные"):
        st.stop()                                # ждём действий пользователя
    df = generate_sample_df()
else:
    try:
        df = load_file(uploaded)
    except Exception as e:
        st.error(f"Не удалось прочитать файл: {e}")
        st.stop()

# ---- валидация ----
required_cols = {"Час", "Потребление (кВт·ч)"}
if not required_cols.issubset(df.columns):
    st.error(f"В файле должны быть колонки: {', '.join(required_cols)}")
    st.stop()

# ---- анализ ----
THRESHOLD = 6.0                                 # кВт·ч — порог пика
df["Пик?"] = df["Потребление (кВт·ч)"] > THRESHOLD
df["Рекомендация"] = np.where(
    df["Пик?"], "Перенести нагрузку на ночь", ""
)

# ---- визуализация ----
st.subheader("📊 Загруженные данные")
st.dataframe(df, use_container_width=True)

st.subheader("График потребления за сутки")
st.line_chart(df.set_index("Час")["Потребление (кВт·ч)"])

st.subheader("⏰ Часы пиковых нагрузок (> 6 кВт·ч)")
peaks = df.loc[df["Пик?"], "Час"].tolist()
if peaks:
    st.write(peaks)
    st.write(
        "Совет: перенесите работу мощного оборудования на непиковое время "
        "(ночь или раннее утро)."
    )
else:
    st.write("Пиков не обнаружено 🎉")

# ---- блок расчёта экономии ----
st.subheader("💸 Потенциальная экономия")
tarif = st.number_input(
    "Текущий тариф, ₽ за кВт·ч",
    min_value=0.0,
    value=6.5,
    step=0.1,
)

if tarif > 0:
    total_kwh = df["Потребление (кВт·ч)"].sum()
    total_cost = total_kwh * tarif

    night_tarif = tarif * 0.8                     # условный ночной тариф (-20 %)
    peak_kwh = df.loc[df["Пик?"], "Потребление (кВт·ч)"].sum()
    optimized_cost = total_cost - peak_kwh * tarif + peak_kwh * night_tarif

    economy = total_cost - optimized_cost
    percent = economy / total_cost * 100 if total_cost else 0

    col1, col2 = st.columns(2)
    col1.metric("Текущая стоимость, ₽", f"{total_cost:,.2f}")
    col2.metric(
        "Оптимизированная, ₽",
        f"{optimized_cost:,.2f}",
        delta=f"-{economy:,.2f}",
    )
    st.success(f"💰 Экономия: **{economy:,.2f} ₽ ({percent:.1f} %)**")

    if percent > 10:
        st.info(
            "🔧 Рекомендуется установка таймеров / ИБП или перенастройка "
            "графиков работы оборудования."
        )

# ---- выгрузка результатов ----
with st.expander("⬇️ Скачать таблицу с результатами"):
    buf = BytesIO()
    df.to_excel(buf, index=False)
    st.download_button(
        "Скачать Excel",
        data=buf.getvalue(),
        file_name="energy_analysis.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )
