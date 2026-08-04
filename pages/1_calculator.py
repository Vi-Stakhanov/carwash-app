import streamlit as st
from fpdf import FPDF

st.title("🧮 Расчет стоимости услуг автомойки")
st.markdown("---")

# 1. Базовые справочники цен
BODIES = {
    "Седан": {"coeff": 1.0, "base_body": 600, "base_complex": 1300},
    "Кроссовер": {"coeff": 1.2, "base_body": 750, "base_complex": 1500},
    "Внедорожник": {"coeff": 1.4, "base_body": 900, "base_complex": 1800},
    "Микроавтобус": {"coeff": 1.6, "base_body": 1200, "base_complex": 2300},
    "Автобус": {"coeff": 2.0, "base_body": 1800, "base_complex": 3500},
    "Грузовой 10т": {"coeff": 2.5, "base_body": 2500, "base_complex": 4500},
    "Фура": {"coeff": 3.0, "base_body": 3500, "base_complex": 6000},
    "Спецтехника": {"coeff": 3.5, "base_body": 4000, "base_complex": 7000}
}

ADD_SERVICES = {
    "Чернение резины": 400,
    "Удаление битумных пятен": 1500,
    "Воск кузова": 600,
    "Удаление и чистка (налет/реагенты)": 2000,
    "Санитарная обработка кузова/салона": 1200,
    "Сложные био-загрязнения (органика/волосы)": 5000
}

# 2. Интерфейс выбора параметров
st.markdown("### 1. Выберите тип транспорта")
body_type = st.radio("Тип кузова:", list(BODIES.keys()), horizontal=True)

st.markdown("### 2. Выберите пакет услуг")
package_type = st.radio("Пакет:", ["Кузов", "Комплекс"], horizontal=True)

st.markdown("### 3. Дополнительные опции")
selected_ops = []
for op_name, op_price in ADD_SERVICES.items():
    actual_op_price = int(op_price * BODIES[body_type]["coeff"])
    if st.checkbox(f"{op_name} (+{actual_op_price} ₽)"):
        selected_ops.append((op_name, actual_op_price))

st.markdown("### 4. Профессиональная химчистка салона")
need_dry_clean = st.checkbox("Требуется глубокая химчистка салона")
dry_clean_price = 0
if need_dry_clean:
    dry_clean_price = st.slider(
        "Оценка степени загрязнения (стоимость химчистки):",
        min_value=10000,
        max_value=100000,
        value=15000,
        step=5000,
        format="%d ₽"
    )

# 3. Калькуляция
base_cost = BODIES[body_type]["base_body"] if package_type == "Кузов" else BODIES[body_type]["base_complex"]
ops_cost = sum(price for name, price in selected_ops)
total_cost = base_cost + ops_cost + dry_clean_price

# Вывод результатов
st.markdown("---")
st.markdown("### 📋 Предварительная смета:")
st.write(f"• **Тип авто**: {body_type}")
st.write(f"• **Тариф ({package_type})**: {base_cost} ₽")

if selected_ops:
    st.write("**Дополнительные работы:**")
    for name, pr in selected_ops:
        st.write(f"  └ {name}: {pr} ₽")

if dry_clean_price > 0:
    st.write(f"• **Химчистка салона**: {dry_clean_price} ₽")

st.markdown(f"## **Итого к оплате: {total_cost} ₽**")

# 4. Функция генерации PDF-сметы
def generate_pdf():
    # Словарь для быстрой замены русских букв на латинские
    translit_dict = {
        'Седан': 'Sedan', 'Кроссовер': 'Krossover', 'Внедорожник': 'Vnedorozhnik',
        'Микроавтобус': 'Mikroavtobus', 'Автобус': 'Avtobus', 'Грузовой 10т': 'Gruzovoy 10t',
        'Фура': 'Fura', 'Спецтехника': 'Spectehnika', 'Кузов': 'Kuzov', 'Комплекс': 'Kompleks'
    }
    
    # Переводим тип авто и пакет в латиницу
    pdf_body = translit_dict.get(body_type, body_type)
    pdf_package = translit_dict.get(package_type, package_type)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(40, 10, "CarWash Estimate / Schet na uslugi")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(40, 10, f"Auto type: {pdf_body}")
    pdf.ln(8)
    pdf.cell(40, 10, f"Main Package ({pdf_package}): {base_cost} RUR")
    pdf.ln(8)
    
    if selected_ops:
        pdf.cell(40, 10, "Additional services:")
        pdf.ln(6)
        for name, pr in selected_ops:
            # Для допуслуг просто пишем Option, чтобы не упал шрифт
            pdf.cell(40, 10, f" - Option: {pr} RUR")
            pdf.ln(6)
            
    if dry_clean_price > 0:
        pdf.cell(40, 10, f"Dry cleaning salon: {dry_clean_price} RUR")
        pdf.ln(8)
        
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(40, 10, f"TOTAL PRICE: {total_cost} RUR")
    
    return pdf.output()

# Кнопка скачивания PDF
pdf_data = generate_pdf()
st.download_button(
    label="📥 Скачать PDF-смету",
    data=bytes(pdf_data),
    file_name="carwash_estimate.pdf",
    mime="application/pdf"
)
