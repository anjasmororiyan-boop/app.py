import streamlit as st
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="ERP V13 - Fixed Master Config", layout="wide")

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
            else:
                st.error("Login Gagal. Gunakan admin/admin123")
    st.stop()

# --- SIDEBAR ---
menu = st.sidebar.radio("Navigasi Utama", [
    "Dashboard", 
    "Master Data Management", 
    "Procurement (Bahan Baku)", 
    "POS (Kasir)", 
    "Laporan Keuangan"
])

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.header("📊 Stock & Sales Overview")
    st.subheader("📦 Stok Bahan Baku (Raw Materials)")
    st.table(st.session_state.master_bahan_baku)

# --- 2. MASTER DATA MANAGEMENT (REPAIRED) ---
elif menu == "Master Data Management":
    st.header("⚙️ Pusat Kendali Master Data")
    t_raw, t_sale, t_cfg = st.tabs(["🌾 Master Bahan Baku", "💰 Master Penjualan", "🛠️ Unit & Expense"])
    
    with t_raw:
        st.subheader("Database Bahan Baku")
        with st.form("fm_raw"):
            c1, c2 = st.columns(2)
            r_sku = c1.text_input("SKU Bahan Baku")
            r_nama = c1.text_input("Nama Bahan Baku")
            r_satuan = c2.selectbox("Satuan Beli", st.session_state.master_units)
            r_min = c2.number_input("Minimal Stok", format="%.5f")
            if st.form_submit_button("Simpan Bahan Baku"):
                new_raw = {"SKU": r_sku, "Nama": r_nama, "Satuan": r_satuan, "Stok": 0.0, "Min_Stok": r_min}
                st.session_state.master_bahan_baku = pd.concat([st.session_state.master_bahan_baku, pd.DataFrame([new_raw])], ignore_index=True)
                st.success(f"Berhasil menambah {r_nama}")
                st.rerun()
        st.dataframe(st.session_state.master_bahan_baku, use_container_width=True)

    with t_sale:
        st.subheader("Database Menu Jual")
        with st.form("fm_sale"):
            c1, c2 = st.columns(2)
            s_sku = c1.text_input("SKU Produk Jual")
            s_nama = c1.text_input("Nama Menu/Produk")
            s_harga = c2.number_input("Harga Jual (Rp)", format="%.5f")
            s_sat = c2.selectbox("Satuan Jual", st.session_state.master_units)
            if st.form_submit_button("Simpan Menu Jual"):
                new_sale = {"SKU": s_sku, "Nama": s_nama, "Satuan": s_sat, "Harga_Jual": s_harga}
                st.session_state.master_penjualan = pd.concat([st.session_state.master_penjualan, pd.DataFrame([new_sale])], ignore_index=True)
                st.success(f"Berhasil menambah {s_nama}")
                st.rerun()
        st.dataframe(st.session_state.master_penjualan, use_container_width=True)

    with t_cfg:
        st.subheader("Konfigurasi Satuan & Tipe Biaya")
        
        col_unit, col_exp = st.columns(2)
        
        # --- BAGIAN SATUAN UNIT ---
        with col_unit:
            st.write("### 📏 Manage Units")
            with st.form("add_unit_form", clear_on_submit=True):
                new_u = st.text_input("Tambah Satuan Baru")
                if st.form_submit_button("Tambah Unit"):
                    if new_u and new_u not in st.session_state.master_units:
                        st.session_state.master_units.append(new_u)
                        st.rerun()
            
            # List Satuan dengan tombol hapus
            for idx, u in enumerate(st.session_state.master_units):
                ca, cb = st.columns([3, 1])
                ca.write(f"- {u}")
                if cb.button("🗑️", key=f"del_u_{idx}"):
                    st.session_state.master_units.pop(idx)
                    st.rerun()

        # --- BAGIAN TIPE BIAYA ---
        with col_exp:
            st.write("### 💸 Manage Expense Types")
            with st.form("add_exp_form", clear_on_submit=True):
                new_e = st.text_input("Tambah Tipe Biaya Baru")
                if st.form_submit_button("Tambah Biaya"):
                    if new_e and new_e not in st.session_state.expense_categories:
                        st.session_state.expense_categories.append(new_e)
                        st.rerun()
            
            # List Biaya dengan tombol hapus
            for idx, e in enumerate(st.session_state.expense_categories):
                ca, cb = st.columns([3, 1])
                ca.write(f"- {e}")
                if cb.button("🗑️", key=f"del_e_{idx}"):
                    st.session_state.expense_categories.pop(idx)
                    st.rerun()
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
