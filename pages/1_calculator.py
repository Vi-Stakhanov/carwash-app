import streamlit as st
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# 1. Настройка страницы — делаем контент на 100% ширины экрана
st.set_page_config(layout="wide")

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

# 2. Интерфейс выбора параметров автомойки
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

# Калькуляция автомойки
base_cost = BODIES[body_type]["base_body"] if package_type == "Кузов" else BODIES[body_type]["base_complex"]
ops_cost = sum(price for name, price in selected_ops)
wash_total_cost = base_cost + ops_cost

# Вывод результатов автомойки
st.markdown("---")
st.markdown("### 📋 Результат расчета мойки:")
st.write(f"• **Тип авто**: {body_type}")
st.write(f"• **Тариф ({package_type})**: {base_cost} ₽")
if selected_ops:
    st.write("**Дополнительные работы:**")
    for name, pr in selected_ops:
        st.write(f"  └ {name}: {pr} ₽")
st.markdown(f"## 💰 **Стоимость мойки: {wash_total_cost} ₽**")


# 3. Интерактивный блок химчистки
st.markdown("---")
st.markdown("### 🧼 Химчистка")
activate_dry_clean = st.checkbox("➕ Добавить профессиональную химчистку салона")

dry_clean_price = 0
if activate_dry_clean:
    dry_clean_price = st.slider(
        "Оценка степени загрязнения (стоимость химчистки):",
        min_value=10000,
        max_value=100000,
        value=10000,
        step=5000,
        format="%d ₽"
    )
    st.markdown(f"## 💰 **Стоимость химчистки: {dry_clean_price} ₽**")
else:
    st.info("Химчистка салона не выбрана (стоимость: 0 ₽)")


# 4. Функция генерации русского PDF через ReportLab
def generate_russian_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    font_path = "C:\\Windows\\Fonts\\arial.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Arial', font_path))
        c.setFont('Arial', 14)
    else:
        c.setFont('Helvetica', 14)
        
    c.drawString(100, 750, "📋 Смета на услуги автомоечного комплекса")
    c.setLineWidth(1)
    c.line(100, 735, 500, 735)
    
    if os.path.exists(font_path):
        c.setFont('Arial', 12)
    else:
        c.setFont('Helvetica', 12)
        
    c.drawString(100, 700, f"Тип автомобиля: {body_type}")
    c.drawString(100, 680, f"Основной пакет ({package_type}): {base_cost} ₽")
    
    y = 650
    if selected_ops:
        c.drawString(100, y, "Дополнительные работы:")
        y -= 20
        for name, price in selected_ops:
            c.drawString(120, y, f"- {name}: {price} ₽")
            y -= 20
            
    y -= 10
    if os.path.exists(font_path):
        c.setFont('Arial', 13)
    else:
        c.setFont('Helvetica', 13)
    c.drawString(100, y, f"ИТОГО ЗА МОЙКУ: {wash_total_cost} ₽")
    
    y -= 40
    if os.path.exists(font_path):
        c.setFont('Arial', 12)
    else:
        c.setFont('Helvetica', 12)
        
    if dry_clean_price > 0:
        c.drawString(100, y, f"Профессиональная химчистка салона: {dry_clean_price} ₽")
    else:
        c.drawString(100, y, "Профессиональная химчистка: Не выбрана (0 ₽)")
        
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# Кнопка скачивания PDF
st.markdown("---")
try:
    pdf_data = generate_russian_pdf()
    st.download_button(
        label="📥 Скачать раздельную PDF-смету",
        data=pdf_data,
        file_name="carwash_estimate.pdf",
        mime="application/pdf"
    )
except Exception as e:
    st.error(f"Ошибка генерации PDF: {e}")
