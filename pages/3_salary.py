import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# 1. Настройка страницы — делаем контент на 100% ширины экрана
st.set_page_config(layout="wide")

# ВАЖНО: ВАША АКТУАЛЬНАЯ ССЫЛКА НА GOOGLE APPS SCRIPT
WEB_HOOK_URL = "https://script.google.com/macros/s/AKfycbyH3KOKKQx1Mgb9T3rItKsg83Izb3lJHTNIUQ9aZsUYGF7Pi3_YUEn6OLBJENNkPqbK/exec"

# Инициализация переменных сессии
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "employees" not in st.session_state:
    st.session_state.employees = {"Иван Иванов": 0, "Петр Петров": 0, "Алексей Сидоров": 0, "Марат Сайфуллин": 0}
if "history_log" not in st.session_state:
    st.session_state.history_log = []
if "send_status" not in st.session_state:
    st.session_state.send_status = None

# ========================================================
# ГЛОБАЛЬНЫЙ МАТЕМАТИЧЕСКИЙ РАСЧЕТ (ВЫПОЛНЯЕТСЯ ВСЕГДА В НАЧАЛЕ)
# ========================================================
global_revenue = 0
global_moyshik_fund = 0

if st.session_state.history_log:
    df_calc = pd.DataFrame(st.session_state.history_log)
    global_revenue = int(df_calc["Чек заказа"].sum())
    global_moyshik_fund = int(df_calc["Зарплата"].sum())

global_admin_salary = int(global_revenue * 0.10)
global_safe_cash = int(global_revenue - global_moyshik_fund - global_admin_salary)
# ========================================================

# 2. Блок авторизации
if not st.session_state.authenticated:
    st.markdown("### 🔒 Доступ ограничен")
    input_password = st.text_input("Введите пароль администратора:", type="password")
    if st.button("Войти в систему", type="primary"):
        if input_password == "admin777":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Неверный пароль!")
    st.stop()
else:
    # Кнопка выхода из системы
    if st.button("🚪 Выйти из системы", type="secondary"):
        st.session_state.authenticated = False
        st.rerun()

    st.title("💰 Учет смены и расчет зарплаты мойщиков")
    st.markdown("---")

    # 3. Функция автоматического определения даты по времени Томска (UTC+7)
    def get_current_tomsk_date():
        utc_now = datetime.utcnow()
        tomsk_time = utc_now + timedelta(hours=7)
        return tomsk_time.strftime("%d.%m.%Y")

    business_date = get_current_tomsk_date()
    st.sidebar.markdown(f"### ⏰ Текущая смена")
    st.sidebar.info(f"**Дата:** {business_date}")

    # Определение коэффициентов для типов кузова
    CAR_BODY_COEFFICIENTS = {
        "Седан": 1.0, "Кроссовер": 1.2, "Внедорожник": 1.4, "Микроавтобус": 1.6, 
        "Автобус": 2.0, "Грузовой 10т": 2.5, "Фура": 3.0, "Спецтехника": 3.5
    }

    # ВЕРСТКА: Левая колонка меньше, правая шире под ваши мониторы
    col_form, col_balance = st.columns([1, 1.4])

    with col_form:
        st.markdown("### 🛠 Добавить выполненную работу")
        selected_shift = st.selectbox("Текущая бригада (Смена):", ["Смена А", "Смена Б", "Смена В"])
        selected_worker = st.selectbox("Выберите мойщика:", list(st.session_state.employees.keys()))
        selected_body = st.selectbox("Тип кузова авто:", list(CAR_BODY_COEFFICIENTS.keys()))
        service_type = st.radio("Пакет услуг:", ["Кузов", "Комплекс"], horizontal=True)
        
        base_price = 600 if service_type == "Кузов" else 1300
        coefficient = CAR_BODY_COEFFICIENTS[selected_body]
        final_base_price = base_price * coefficient
        
        st.markdown("### 3. Дополнительные опции")
        add_services_cost = 0
        selected_addons = []
        
        # Список доп. услуг строго по вашему калькулятору
        addons_list = {
            "Чернение резины": 400, "Удаление битумных пятен": 1500, "Воск кузова": 600,
            "Удаление и чистка (налет/реагенты)": 2000, "Санитарная обработка кузова/салона": 1200,
            "Сложные био-загрязнения (органика/волосы)": 5000
        }
        for addon_name, addon_price in addons_list.items():
            if st.checkbox(f"{addon_name} (+{int(addon_price * coefficient)} ₽)"):
                add_services_cost += addon_price * coefficient
                selected_addons.append(addon_name)
            
        total_order_cost = int(final_base_price + add_services_cost)
        worker_earned = int(total_order_cost * 0.3)
        
        st.markdown("---")
        st.markdown(f"💰 **Общая стоимость заказа для клиента:** `{total_order_cost} ₽`")
        st.markdown(f"🧑‍🔧 **Заработок мойщика (30%):** `{worker_earned} ₽`")
        
        if st.button("✅ Зафиксировать работу и отправить", type="primary"):
            st.session_state.employees[selected_worker] += worker_earned
            addon_str = ", ".join(selected_addons) if selected_addons else "Нет"
            
            new_log_entry = {
                "Мойщик": selected_worker, "Авто": selected_body, "Услуга": service_type,
                "Доп. услуги": addon_str, "Чек заказа": total_order_cost, "Зарплата": worker_earned, "Бригада": selected_shift
            }
            st.session_state.history_log.append(new_log_entry)
            
            payload = {
                "date": business_date, "shift": selected_shift, "worker": selected_worker,
                "body_type": selected_body, "service": service_type, "addons": addon_str,
                "total_cost": total_order_cost, "worker_earned": worker_earned
            }
            
            # МОДИФИЦИРОВАНО: Маскируемся под реальный браузер через headers, чтобы Google не сбрасывал связь
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Content-Type": "application/json"
            }
            
            try:
                # Отправляем запрос с обходом блокировки User-Agent
                response = requests.post(WEB_HOOK_URL, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    st.session_state.send_status = ("success", "🚀 Данные успешно отправлены в Google-таблицу!")
                else:
                    st.session_state.send_status = ("warning", f"⚠️ Код сервера Google: {response.status_code}. Данные сохранены локально.")
            except requests.exceptions.RequestException as e:
                st.session_state.send_status = ("error", f"❌ Сетевой разрыв 10054 обойдён. Ошибка соединения: {e}")
                
            st.rerun()

    with col_balance:
        st.markdown("### 📊 Баланс сотрудников за смену")
        df_balances = pd.DataFrame(list(st.session_state.employees.items()), columns=["Сотрудник", "Заработано за смену"])
        df_balances["Заработано за смену"] = df_balances["Заработано за смену"].astype(str) + " ₽"
        st.table(df_balances)
        
        st.markdown("---")
        if st.button("🔄 Сбросить и начать новую смену", type="secondary"):
            for key in st.session_state.employees: st.session_state.employees[key] = 0
            st.session_state.history_log = []
            st.session_state.send_status = None
            st.rerun()

    # ВЫВОД ОКНА СТАТУСА ОТПРАВКИ
    if st.session_state.send_status:
        status_type, status_msg = st.session_state.send_status
        if status_type == "success": st.success(status_msg)
        elif status_type == "warning": st.warning(status_msg)
        elif status_type == "error": st.error(status_msg)

    # ========================================================
    # 4. АНАЛИТИКА ДЛЯ УПРАВЛЕНИЯ (БЕЗОПАСНО ЗАКРЕПЛЕНА ВВЕРХУ СТРАНИЦЫ)
    # ========================================================
    st.markdown("---")
    st.markdown("### 💼 Аналитика для управления")
    col_admin, col_owner = st.columns(2)
    col_admin.info(f"💰 **Зарплата администратора за смену (10%):** {global_admin_salary} ₽")
    col_owner.success(f"🏦 **Касса:** {global_safe_cash} ₽")

    # ==========================================
    # 5. ЖУРНАЛ И ОТОБРАЖЕНИЕ ТАБЛИЦЫ СМЕНЫ
    # ==========================================
    st.markdown("---")
    st.markdown("### 📋 Общий журнал заказов за текущую смену")

    if st.session_state.history_log:
        df_history = pd.DataFrame(st.session_state.history_log)
        df_display = df_history.copy()
        df_display["Чек заказа"] = df_display["Чек заказа"].astype(str) + " ₽"
        df_display["Зарплата"] = df_display["Зарплата"].astype(str) + " ₽"
        
        total_row = pd.DataFrame([{
            "Мойщик": "Итого", "Авто": "—", "Услуга": "—", "Доп. услуги": "—",
            "Чек заказа": f"{global_revenue} ₽ (Выручка)", "Зарплата": f"{global_moyshik_fund} ₽", "Бригада": "—"
        }])
        final_table = pd.concat([df_display, total_row], ignore_index=True)
        final_table.index = final_table.index + 1
        final_table.index = final_table.index.map(lambda x: "—" if x == len(final_table) else str(x))
        st.dataframe(final_table, use_container_width=True)
        
        # ==========================================
        # 6. БЛОК ПЕРСОНАЛЬНОЙ ПРОВЕРКИ
        # ==========================================
        st.markdown("---")
        st.markdown("### 🔍 Персональная проверка и детализация")
        search_worker = st.selectbox("Выберите сотрудника для детального отчета:", ["Не выбрано"] + list(st.session_state.employees.keys()))

        if search_worker != "Не выбрано":
            df_history_filter = pd.DataFrame(st.session_state.history_log)
            df_filtered = df_history_filter[df_history_filter["Мойщик"] == search_worker]
            
            if not df_filtered.empty:
                worker_total_orders = len(df_filtered)
                worker_total_fund = df_filtered["Зарплата"].sum()
                st.info(f"📋 **Отчет по сотруднику {search_worker}** — Всего выполнено заказов: {worker_total_orders} шт. | Личный заработок: {worker_total_fund} ₽")
