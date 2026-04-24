import streamlit as st
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="ERP V13 - Separated Masters", layout="wide")

# --- SMART FORMATTING FUNCTION ---
def smart_format(val):
    if val is None: return "0"
    try:
        val_float = float(val)
        if val_float.is_integer():
            return "{:,.0f}".format(val_float).replace(",", ".")
        formatted = "{:,.5f}".format(val_float).rstrip('0').rstrip('.')
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(val)

# --- INITIALIZING SESSION STATES ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

default_states = {
    'master_units': ["Kg", "Liter", "Pcs", "Gram", "Box"],
    'expense_categories': ["Gaji", "Listrik/Air", "Sewa", "Marketing"],
    # MASTER TERPISAH
    'master_bahan_baku': pd.DataFrame([
        {"SKU": "RAW001", "Nama": "Tepung Terigu", "Satuan": "Kg", "Stok": 50.0, "Min_Stok": 10.0}
    ]),
    'master_penjualan': pd.DataFrame([
        {"SKU": "SALE001", "Nama": "Roti Tawar", "Satuan": "Pcs", "Harga_Jual": 15000.0}
    ]),
    'pr_data': [],
    'pos_transactions': [],
    'expenses_data': [],
    'payments_data': [],
    'cash_session': {"modal_awal": 0.0, "status": "Closed"}
}

for key, val in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.title("🔐 Login ERP Management")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u == "admin" and p == "admin123":
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- SIDEBAR ---
menu = st.sidebar.radio("Navigasi Utama", [
    "Dashboard", 
    "Master Data Management", 
    "Procurement (Bahan Baku)", 
    "POS (Penjualan)", 
    "Laporan Keuangan"
])

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.header("📊 Stock & Sales Overview")
    st.subheader("📦 Stok Bahan Baku (Raw Materials)")
    st.table(st.session_state.master_bahan_baku)

# --- 2. MASTER DATA MANAGEMENT (SEPARATED) ---
elif menu == "Master Data Management":
    st.header("⚙️ Pusat Kendali Master Data")
    t_raw, t_sale, t_cfg = st.tabs(["🌾 Master Bahan Baku", "💰 Master Penjualan", "🛠️ Unit & Expense"])
    
    with t_raw:
        st.subheader("Database Bahan Baku (Input untuk Procurement)")
        with st.form("fm_raw"):
            c1, c2 = st.columns(2)
            r_sku = c1.text_input("SKU Bahan Baku")
            r_nama = c1.text_input("Nama Bahan Baku")
            r_satuan = c2.selectbox("Satuan Beli", st.session_state.master_units, key="sb1")
            r_min = c2.number_input("Minimal Stok", format="%.5f")
            if st.form_submit_button("Simpan Bahan Baku"):
                new_raw = {"SKU": r_sku, "Nama": r_nama, "Satuan": r_satuan, "Stok": 0.0, "Min_Stok": r_min}
                st.session_state.master_bahan_baku = pd.concat([st.session_state.master_bahan_baku, pd.DataFrame([new_raw])], ignore_index=True)
                st.rerun()
        st.table(st.session_state.master_bahan_baku)

    with t_sale:
        st.subheader("Database Menu Jual (Input untuk POS)")
        with st.form("fm_sale"):
            c1, c2 = st.columns(2)
            s_sku = c1.text_input("SKU Produk Jual")
            s_nama = c1.text_input("Nama Menu/Produk")
            s_harga = c2.number_input("Harga Jual (Rp)", format="%.5f")
            s_sat = c2.selectbox("Satuan Jual", st.session_state.master_units, key="sb2")
            if st.form_submit_button("Simpan Menu Jual"):
                new_sale = {"SKU": s_sku, "Nama": s_nama, "Satuan": s_sat, "Harga_Jual": s_harga}
                st.session_state.master_penjualan = pd.concat([st.session_state.master_penjualan, pd.DataFrame([new_sale])], ignore_index=True)
                st.rerun()
        st.table(st.session_state.master_penjualan)

    with t_cfg:
        st.subheader("Pengaturan Satuan & Biaya")
        # Logic tambah/hapus unit dan kategori expense tetap ada di sini
        st.write(st.session_state.master_units)

# --- 3. PROCUREMENT (INTEGRATED WITH RAW MATERIALS) ---
elif menu == "Procurement (Bahan Baku)":
    st.header("🛒 Pengadaan Bahan Baku")
    with st.expander("📝 Buat PR Bahan Baku"):
        with st.form("pr_raw"):
            # HANYA MENGAMBIL DARI MASTER BAHAN BAKU
            p_item = st.selectbox("Pilih Bahan Baku", st.session_state.master_bahan_baku['Nama'].tolist())
            it_info = st.session_state.master_bahan_baku[st.session_state.master_bahan_baku['Nama'] == p_item].iloc[0]
            st.info(f"Satuan Standar: {it_info['Satuan']}")
            p_qty = st.number_input("Qty Pesanan", format="%.5f")
            p_prc = st.number_input("Harga Beli per Satuan", format="%.5f")
            if st.form_submit_button("Submit PR"):
                st.session_state.pr_data.append({
                    "ID": f"PR-{datetime.now().strftime('%M%S')}", "Item": p_item, 
                    "Satuan": it_info['Satuan'], "Qty_Pesan": p_qty, "Qty_Terima": 0.0, "Status": "Pending"
                })
                st.rerun()
    
    # Logic GR (Goods Receipt) akan menambah stok ke st.session_state.master_bahan_baku

# --- 4. POS (INTEGRATED WITH SALES ITEMS) ---
elif menu == "POS (Penjualan)":
    st.header("💰 Kasir Penjualan")
    if st.session_state.cash_session['status'] == "Open":
        with st.form("pos_sale"):
            # HANYA MENGAMBIL DARI MASTER PENJUALAN
            s_item = st.selectbox("Pilih Menu", st.session_state.master_penjualan['Nama'].tolist())
            s_qty = st.number_input("Qty", format="%.5f")
            if st.form_submit_button("Tambahkan"):
                it_sale = st.session_state.master_penjualan[st.session_state.master_penjualan['Nama'] == s_item].iloc[0]
                st.session_state.pos_transactions.append({
                    "Item": s_item, "Qty": s_qty, "Total": s_qty * it_sale['Harga_Jual']
                })
                st.rerun()
    else:
        if st.button("Buka Kasir"):
            st.session_state.cash_session['status'] = "Open"
            st.rerun()

# --- 5. FINANCES ---
elif menu == "Laporan Keuangan":
    st.header("📈 Laporan Keuangan")
    # Profit Loss, Balance Sheet, dll
