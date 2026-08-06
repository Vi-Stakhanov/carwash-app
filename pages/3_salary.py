import streamlit as st
import pandas as pd

st.title("💰 Учет смены и расчет зарплаты мойщиков")
st.markdown("---")

# 1. Блок авторизации (Проверка пароля)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("### 🔒 Доступ ограничен")
    # Поле ввода скрывает символы точками (type="password")
    input_password = st.text_input("Введите пароль администратора:", type="password")
    
    if st.button("Войти в систему", type="primary"):
        if input_password == "admin777":
            st.session_state.authenticated = True
            st.success("Авторизация успешна!")
            st.rerun()
        else:
            st.error("❌ Неверный пароль! Доступ запрещен.")
    st.stop() # Полностью останавливает выполнение кода ниже, пока пароль не верный

# --- КОД НИЖЕ ВЫПОЛНИТСЯ ТОЛЬКО ПОСЛЕ УСПЕШНОГО ВХОДА ---

# Кнопка «Выйти», чтобы закрыть панель от посторонних глаз
if st.button("🚪 Выйти из панели управления"):
    st.session_state.authenticated = False
    st.rerun()

st.markdown("---")

# 2. Справочники цен (точно такие же, как в калькуляторе)
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

# 3. Инициализация базы данных смены в памяти
if "employees" not in st.session_state:
    st.session_state.employees = {
        "Иван Иванов": 0,
        "Петр Петров": 0,
        "Алексей Сидоров": 0,
        "Марат Сайфуллин": 0
    }

if "history_log" not in st.session_state:
    st.session_state.history_log = []

# Разделение экрана на две колонки
col1, col2 = st.columns([1.3, 1])

with col1:
    st.markdown("### 🛠️ Добавить выполненную работу")
    
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
    
    if st.button("✅ Зафиксировать работу и начислить", type="primary"):
        st.session_state.employees[selected_worker] += earned_money
        ops_text = ", ".join(selected_ops_names) if selected_ops_names else "Нет"
        
        st.session_state.history_log.append({
            "Мойщик": selected_worker,
            "Авто": body_type,
            "Основной пакет": package_type,
            "Доп. услуги": ops_text,
            "Общий чек": f"{order_total_cost} ₽",
            "Зарплата (30%)": f"{earned_money} ₽"
        })
        st.success(f"Сотруднику {selected_worker} успешно начислено {earned_money} ₽!")
        st.rerun()

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
st.markdown("### 📋 Журнал выполненных заказов за текущую смену")

if st.session_state.history_log:
    df_log = pd.DataFrame(st.session_state.history_log)
    st.dataframe(df_log, use_container_width=True)
else:
    st.info("За сегодня заказов еще не зафиксировано. Оформите первую работу выше.")
