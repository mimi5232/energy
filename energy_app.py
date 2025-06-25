import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# --------------------------- НАСТРОЙКИ СТРАНИЦЫ ---------------------------
st.set_page_config(
    page_title="Energy Monitor — Экономия энергии для бизнеса",
    page_icon="🔋",
    layout="centered"
)

# --------------------------- ШАПКА И ОПИСАНИЕ ---------------------------
st.markdown("""
# 🔋 **Energy Monitor**
### Умный анализ энергопотребления и расчёт экономии для малого бизнеса

📁 Загрузите данные в формате CSV или Excel  
📉 Получите визуализацию, пиковые часы и рекомендации  
💸 Узнайте, сколько вы можете сэкономить
""")

# --------------------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---------------------------
def generate_sample_df() -> pd.DataFrame:
    np.random.seed(42)
    hours = list(range(24))
    consumption = [
        np.random.uniform(1.5, 2.5) if h < 6 or h > 22
        else np.random.uniform(3.0, 4.5) if 6 <= h < 17
        else np.random.uniform(6.0, 8.5)
        for h in hours
    ]
    return pd.DataFrame({"Час": hours, "Потребление (кВт·ч)": consumption})


def load_file(file) -> pd.DataFrame:
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)

# --------------------------- ЗАГРУЗКА ДАННЫХ ---------------------------
uploaded = st.file_uploader(
    "Загрузите CSV или Excel с колонками «Час» и «Потребление (кВт·ч)»",
    type=["csv", "xlsx"],
)

if uploaded is None:
    st.info("Файл не выбран. Можно создать тестовые данные.")
    if not st.button("Сгенерировать тестовые данные"):
        st.stop()
    df = generate_sample_df()
else:
    try:
        df = load_file(uploaded)
    except Exception as e:
        st.error(f"Не удалось прочитать файл: {e}")
        st.stop()

# --------------------------- ВАЛИДАЦИЯ ---------------------------
required_cols = {"Час", "Потребление (кВт·ч)"}
if not required_cols.issubset(df.columns):
    st.error(f"В файле должны быть колонки: {', '.join(required_cols)}")
    st.stop()

# --------------------------- АНАЛИЗ ---------------------------
THRESHOLD = 6.0
df["Пик?"] = df["Потребление (кВт·ч)"] > THRESHOLD
df["Рекомендация"] = np.where(df["Пик?"], "Перенести нагрузку на ночь", "")

# --------------------------- ВИЗУАЛИЗАЦИЯ ---------------------------
st.subheader("📊 Загруженные данные")
st.dataframe(df, use_container_width=True)

st.subheader("📈 График потребления за сутки")
st.line_chart(df.set_index("Час")["Потребление (кВт·ч)"])

st.subheader("⏰ Часы пиковых нагрузок (> 6 кВт·ч)")
peaks = df.loc[df["Пик?"], "Час"].tolist()
if peaks:
    st.write(peaks)
    st.write("🔌 Рекомендуется перенести работу мощного оборудования на ночные или утренние часы.")
else:
    st.write("✅ Пиков не обнаружено. Распределение нагрузки сбалансировано.")

# --------------------------- ЭКОНОМИЯ ---------------------------
st.subheader("💸 Потенциальная экономия")
tarif = st.number_input(
    "Введите тариф (₽ за 1 кВт·ч):", min_value=0.0, value=6.5, step=0.1)

if tarif > 0:
    total_kwh = df["Потребление (кВт·ч)"].sum()
    total_cost = total_kwh * tarif
    night_tarif = tarif * 0.8
    peak_kwh = df.loc[df["Пик?"], "Потребление (кВт·ч)"].sum()
    optimized_cost = total_cost - peak_kwh * tarif + peak_kwh * night_tarif
    economy = total_cost - optimized_cost
    percent = (economy / total_cost * 100) if total_cost > 0 else 0

    col1, col2 = st.columns(2)
    col1.metric("Текущая стоимость", f"{total_cost:,.2f} ₽")
    col2.metric("Оптимизированная", f"{optimized_cost:,.2f} ₽", delta=f"-{economy:,.2f} ₽")

    st.success(f"💰 Вы можете сэкономить: **{economy:,.2f} ₽ ({percent:.1f}%)**")

    if percent > 10:
        st.info("📌 Совет: установите таймеры или ИБП, чтобы автоматически снижать пиковую нагрузку.")

# --------------------------- СКАЧИВАНИЕ ---------------------------
with st.expander("⬇️ Скачать таблицу с результатами"):
    buf = BytesIO()
    df.to_excel(buf, index=False)
    st.download_button(
        "Скачать Excel",
        data=buf.getvalue(),
        file_name="energy_analysis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
