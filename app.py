import streamlit as st
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="ERP Business Suite V5 - Dynamic Master", layout="wide")

# --- CUSTOM FORMATTING ---
def format_num(val):
    return "{:,.5f}".format(val).replace(",", "X").replace(".", ",").replace("X", ".")

# --- INITIALIZING SESSION STATES ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Inisialisasi Data Master Dinamis
default_states = {
    'master_units': ["Kg", "Liter", "Pcs", "Box"],
    'expense_categories': ["Gaji", "Listrik/Air", "Sewa", "Marketing"],
    'master_items': pd.DataFrame([
        {"SKU": "BRG001", "Nama": "Espresso Coffee", "Satuan": "Kg", "Harga_Jual": 25000.0, "Stok": 100.0, "Min_Stok": 10.0}
    ]),
    'promos': pd.DataFrame([{"Nama_Promo": "No Promo", "Diskon_Persen": 0.0, "Diskon_Nominal": 0.0}]),
    'inventory': {"BRG001": 100.0},
    'pr_data': [],
    'sales_data': [],
    'expenses_data': [],
    'pos_transactions': [],
    'cash_session': {"modal_awal": 0.0, "status": "Closed"}
}

for key, val in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.title("🔐 Login ERP & POS System")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Gunakan admin/admin123")
    st.stop()

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("ERP V5 Dynamic")
menu = st.sidebar.radio("Navigasi", [
    "Dashboard", 
    "Master Pengaturan (Unit/Expense)", 
    "Master Data Barang & Promo", 
    "POS (Kasir)", 
    "Procurement (PR/PO/GR)", 
    "Financial Report"
])

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.header("📊 Ringkasan Bisnis")
    c1, c2, c3 = st.columns(3)
    rev = sum(t['Net_Total'] for t in st.session_state.pos_transactions)
    exp = sum(e['Nominal'] for e in st.session_state.expenses_data)
    c1.metric("Penjualan POS", f"Rp {format_num(rev)}")
    c2.metric("Total Biaya (OPEX)", f"Rp {format_num(exp)}")
    c3.metric("Stok Item", len(st.session_state.master_items))

# --- 2. MASTER PENGATURAN (UNIT & EXPENSE) ---
elif menu == "Master Pengaturan (Unit/Expense)":
    st.header("⚙️ Pengaturan Satuan & Kategori Biaya")
    
    col_u, col_e = st.columns(2)
    
    with col_u:
        st.subheader("Manage Units (Satuan)")
        new_unit = st.text_input("Tambah Satuan Baru (misal: Pack)")
        if st.button("Simpan Satuan"):
            if new_unit and new_unit not in st.session_state.master_units:
                st.session_state.master_units.append(new_unit)
                st.success(f"Satuan {new_unit} ditambah.")
                st.rerun()
        st.write("**Daftar Satuan saat ini:**")
        st.write(", ".join(st.session_state.master_units))

    with col_e:
        st.subheader("Manage Expense Categories")
        new_cat = st.text_input("Tambah Kategori Biaya (misal: Parkir)")
        if st.button("Simpan Kategori"):
            if new_cat and new_cat not in st.session_state.expense_categories:
                st.session_state.expense_categories.append(new_cat)
                st.success(f"Kategori {new_cat} ditambah.")
                st.rerun()
        st.write("**Daftar Kategori saat ini:**")
        st.write(", ".join(st.session_state.expense_categories))

# --- 3. MASTER DATA BARANG & PROMO ---
elif menu == "Master Data Barang & Promo":
    tab1, tab2 = st.tabs(["Master Items", "Master Promos"])
    
    with tab1:
        with st.form("add_item"):
            c1, c2 = st.columns(2)
            n_sku = c1.text_input("SKU")
            n_nama = c1.text_input("Nama")
            # MENGGUNAKAN SATUAN DINAMIS
            n_satuan = c2.selectbox("Pilih Satuan", st.session_state.master_units)
            n_harga = c2.number_input("Harga Jual", format="%.5f")
            n_min = c2.number_input("Min Stok", format="%.5f")
            if st.form_submit_button("Simpan Item"):
                new_item = {"SKU": n_sku, "Nama": n_nama, "Satuan": n_satuan, "Harga_Jual": n_harga, "Stok": 0.0, "Min_Stok": n_min}
                st.session_state.master_items = pd.concat([st.session_state.master_items, pd.DataFrame([new_item])], ignore_index=True)
                st.rerun()
        st.table(st.session_state.master_items)

# --- 4. POS (KASIR) ---
elif menu == "POS (Kasir)":
    st.header("🛒 Kasir POS")
    if st.session_state.cash_session['status'] == "Closed":
        modal = st.number_input("Modal Awal", format="%.5f")
        if st.button("Buka Sesi Kasir"):
            st.session_state.cash_session = {"modal_awal": modal, "status": "Open"}
            st.rerun()
    else:
        # Logika Kasir sama seperti sebelumnya, namun menggunakan format desimal presisi
        items = st.session_state.master_items['Nama'].tolist()
        sel_item = st.selectbox("Item", items)
        qty = st.number_input("Quantity", min_value=0.00001, format="%.5f")
        if st.button("Tambah Transaksi"):
            price = st.session_state.master_items[st.session_state.master_items['Nama'] == sel_item]['Harga_Jual'].values[0]
            st.session_state.pos_transactions.append({
                "Waktu": datetime.now(), "Item": sel_item, "Qty": qty, "Net_Total": qty * price
            })
            st.success("Tercatat.")
        st.table(pd.DataFrame(st.session_state.pos_transactions).tail(5))

# --- 5. PROCUREMENT (PR/PO/GR) ---
elif menu == "Procurement (PR/PO/GR)":
    st.header("📦 Procurement Alur")
    with st.form("pr_form"):
        p_item = st.selectbox("Barang", st.session_state.master_items['Nama'].tolist())
        p_qty = st.number_input("Qty Beli", format="%.5f")
        p_prc = st.number_input("Harga Satuan Beli", format="%.5f")
        if st.form_submit_button("Submit PR"):
            st.session_state.pr_data.append({
                "ID": f"PR-{datetime.now().strftime('%M%S')}",
                "Item": p_item, "Qty": p_qty, "Harga": p_prc, "Status": "Approved"
            })
    
    st.subheader("Penerimaan Barang (GR)")
    # Simulasi GR Langsung untuk Test
    for i, pr in enumerate(st.session_state.pr_data):
        if pr['Status'] == "Approved":
            if st.button(f"Post GR untuk {pr['ID']} ({pr['Item']})"):
                sku = st.session_state.master_items[st.session_state.master_items['Nama'] == pr['Item']]['SKU'].values[0]
                idx = st.session_state.master_items[st.session_state.master_items['SKU'] == sku].index[0]
                st.session_state.master_items.at[idx, 'Stok'] += pr['Qty']
                st.session_state.pr_data[i]['Status'] = "Closed"
                st.rerun()

# --- 6. FINANCIAL REPORT ---
elif menu == "Financial Report":
    st.header("📈 Laporan Laba Rugi")
    
    # Pencatatan Biaya dengan Kategori Dinamis
    with st.expander("Input Biaya Baru"):
        with st.form("exp_form"):
            # MENGGUNAKAN KATEGORI DINAMIS
            e_cat = st.selectbox("Kategori Biaya", st.session_state.expense_categories)
            e_nom = st.number_input("Nominal", format="%.5f")
            if st.form_submit_button("Simpan Biaya"):
                st.session_state.expenses_data.append({"Kategori": e_cat, "Nominal": e_nom})
                st.rerun()

    rev = sum(t['Net_Total'] for t in st.session_state.pos_transactions)
    opex = sum(e['Nominal'] for e in st.session_state.expenses_data)
    
    st.divider()
    st.write(f"**Total Revenue:** Rp {format_num(rev)}")
    st.write(f"**Total OPEX:** (Rp {format_num(opex)})")
    st.subheader(f"Estimasi Laba Bersih: Rp {format_num(rev - opex)}")
