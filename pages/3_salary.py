import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.title("💰 Учет смены и расчет зарплаты мойщиков")
st.markdown("---")

# ВАЖНО: ВАША АКТУАЛЬНАЯ ССЫЛКА НА GOOGLE APPS SCRIPT (Окачивается на /exec)
WEB_HOOK_URL = "https://script.google.com/macros/s/AKfycbxy9grZ7ukBJtYNLCI4CQcfDMnSk-kHgO2CWO8k5YyJwBmGhRx-mWsEb4GpDvc4nxuY/exec"

# 1. Блок авторизации
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("### 🔒 Доступ ограничен")
    input_password = st.text_input("Введите пароль администратора:", type="password")
    
    if st.button("Войти в систему", type="primary"):
        if input_password == "admin777":
            st.session_state.authenticated = True
            st.success("Авторизация успешна!")
            st.rerun()
        else:
            st.error("❌ Неверный пароль! Доступ запрещен.")
    st.stop()

if st.button("🚪 Выйти из панели управления"):
    st.session_state.authenticated = False
    st.rerun()

st.markdown("---")

# 2. Функция автоматического определения бизнес-смены с привязкой к часовому поясу Томска (UTC+7)
def get_business_shift_info():
    # Получаем чистое время сервера UTC и принудительно прибавляем 7 часов для Томска
    utc_now = datetime.utcnow()
    tomsk_now = utc_now + timedelta(hours=7)
    current_hour = tomsk_now.hour
    
    # Дневная смена: с 08:00 до 20:00
    if 8 <= current_hour < 20:
        shift_type = "День"
        business_date = tomsk_now.strftime("%d.%m.%Y")
    # Ночная смена (вечер): с 20:00 до 00:00
    elif current_hour >= 20:
        shift_type = "Ночь"
        business_date = tomsk_now.strftime("%d.%m.%Y")
    # Ночная смена (утро следующего дня): с 00:00 до 08:00
    else:
        shift_type = "Ночь"
        # Заказы после полуночи относятся к вчерашней рабочей смене по часовому поясу Томска
        yesterday = tomsk_now - timedelta(days=1)
        business_date = yesterday.strftime("%d.%m.%Y")
        
    return business_date, shift_type

bus_date, bus_shift = get_business_shift_info()

# Выводим текущий статус смены на боковую панель для администратора
st.sidebar.markdown("### ⏰ Текущая рабочая смена")
st.sidebar.info(f"**Бизнес-дата:** {bus_date}\n\n**Тип смены:** {bus_shift}")

# 3. Справочники цен
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

if "employees" not in st.session_state:
    st.session_state.employees = {
        "Иван Иванов": 0, "Петр Петров": 0, "Алексей Сидоров": 0, "Марат Сайфуллин": 0
    }

if "history_log" not in st.session_state:
    st.session_state.history_log = []

col1, col2 = st.columns([1.3, 1])

with col1:
    st.markdown("### 🛠️ Добавить выполненную работу")
    
    # Выбор работающей сегодня бригады
    selected_brigade = st.selectbox("Текущая бригада (Смена):", ["Смена А", "Смена Б", "Смена В", "Смена Г"])
    
    selected_worker = st.selectbox("Выберите мойщика:", list(st.session_state.employees.keys()))
    body_type = st.selectbox("Тип кузова авто:", list(BODIES.keys()))
    package_type = st.radio("Пакет услуг:", ["Кузов", "Комплекс"], horizontal=True)
    
    base_cost = BODIES[body_type]["base_body"] if package_type == "Кузов" else BODIES[body_type]["base_complex"]
    
    st.markdown("**Дополнительные опции для этого заказа:**")
    selected_ops_names = []
    ops_cost = 0
    
    for op_name, op_price in ADD_SERVICES.items():
        actual_op_price = int(op_price * BODIES[body_type]["coeff"])
        if st.checkbox(f"{op_name} (+{actual_op_price} ₽)", key=f"salary_{op_name}"):
            selected_ops_names.append(op_name)
            ops_cost += actual_op_price
            
    order_total_cost = base_cost + ops_cost
    worker_share_pct = 30
    earned_money = int(order_total_cost * (worker_share_pct / 100))
    
    st.markdown("---")
    st.markdown(f"**Общий чек заказа (пакет + допы):** {order_total_cost} ₽")
    st.markdown(f"**Начисление сотруднику ({worker_share_pct}%):** {earned_money} ₽")
    
    if st.button("✅ Зафиксировать работу и отправить в Google", type="primary"):
        st.session_state.employees[selected_worker] += earned_money
        ops_text = ", ".join(selected_ops_names) if selected_ops_names else "Нет"
        
        st.session_state.history_log.append({
            "Мойщик": selected_worker,
            "Авто": body_type,
            "Услуга": package_type,
            "Чек": f"{order_total_cost} ₽",
            "Зарплата": f"{earned_money} ₽"
        })
        
        if WEB_HOOK_URL == "ВСТАВЬТЕ_СЮДА_ВАШУ_ССЫЛКУ_EXEC":
            st.warning("⚠️ Вы не заменили ссылку в коде!")
        else:
            try:
                payload = {
                    "dateTime": f"{bus_date} {(datetime.utcnow() + timedelta(hours=7)).strftime('%H:%M')}",
                    "worker": selected_worker,
                    "bodyType": body_type,
                    "packageType": package_type,
                    "opsText": ops_text,
                    "totalCost": f"{order_total_cost} ₽",
                    "earned": f"{earned_money} ₽",
                    "shiftType": bus_shift,          # Отправляем День/Ночь
                    "brigade": selected_brigade      # Отправляем бригаду А/Б/В/Г
                }
                resp = requests.post(WEB_HOOK_URL, json=payload, timeout=5)
                if resp.status_code == 200:
                    st.success(f"☁️ Заказ для {selected_brigade} ({bus_shift}) успешно отправлен!")
                    st.balloons()
                else:
                    st.error(f"Ошибка сервера Google: {resp.status_code}")
            except Exception as e:
                st.error(f"🔴 Ошибка отправки: {e}")

with col2:
    st.markdown("### 📊 Баланс сотрудников за смену")
    df_balances = pd.DataFrame(
        list(st.session_state.employees.items()), 
        columns=["Сотрудник", "Заработано за сегодня"]
    )
    df_balances["Заработано за сегодня"] = df_balances["Заработано за сегодня"].apply(lambda x: f"{x} ₽")
    st.table(df_balances)
    
    if st.button("🔄 Сбросить смену / Очистить кассу"):
        for worker in st.session_state.employees:
            st.session_state.employees[worker] = 0
        st.session_state.history_log = []
        st.rerun()

st.markdown("---")
st.markdown("### 📋 Журнал выполненных заказов за текущую смену (Локальный)")

if st.session_state.history_log:
    df_log = pd.DataFrame(st.session_state.history_log)
    st.dataframe(df_log, use_container_width=True)
