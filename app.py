import streamlit as st
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="ERP V10 - Precision Procurement", layout="wide")

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
    'expense_categories': ["Gaji", "Listrik/Air", "Sewa", "Marketing", "Maintenance"],
    'master_items': pd.DataFrame([
        {"SKU": "BRG001", "Nama": "Espresso Coffee", "Satuan": "Kg", "Harga_Jual": 25000.0, "Stok": 100.0, "Min_Stok": 10.0}
    ]),
    'pr_data': [],
    'pos_transactions': [],
    'expenses_data': [],
    'cash_session': {"modal_awal": 0.0, "status": "Closed"}
}

for key, val in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.title("🔐 Login ERP & POS System")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u == "admin" and p == "admin123":
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- SIDEBAR NAVIGASI ---
menu = st.sidebar.radio("Navigasi Utama", [
    "Dashboard", 
    "Master Pengaturan", 
    "Master Barang & Promo", 
    "Procurement (PR/PO/GR)", 
    "POS (Kasir)", 
    "Riwayat Transaksi",
    "Financial Report"
])

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.header("📊 Ringkasan Bisnis")
    c1, c2, c3 = st.columns(3)
    rev = sum(t['Net_Total'] for t in st.session_state.pos_transactions)
    exp = sum(e['Nominal'] for e in st.session_state.expenses_data)
    c1.metric("Revenue POS", f"Rp {smart_format(rev)}")
    c2.metric("Total OPEX", f"Rp {smart_format(exp)}")
    c3.metric("Net Profit Est.", f"Rp {smart_format(rev - exp)}")
    st.table(st.session_state.master_items[['SKU', 'Nama', 'Satuan', 'Stok']])

# --- 2. MASTER PENGATURAN ---
elif menu == "Master Pengaturan":
    st.header("⚙️ Unit & Biaya")
    col1, col2 = st.columns(2)
    with col1:
        new_u = st.text_input("Tambah Satuan")
        if st.button("Simpan Satuan"): st.session_state.master_units.append(new_u); st.rerun()
        st.write(st.session_state.master_units)
    with col2:
        new_ex = st.text_input("Tambah Kategori Biaya")
        if st.button("Simpan Kategori"): st.session_state.expense_categories.append(new_ex); st.rerun()
        st.write(st.session_state.expense_categories)

# --- 3. MASTER BARANG ---
elif menu == "Master Barang & Promo":
    st.header("📦 Master Data")
    with st.expander("➕ Tambah / Edit Item"):
        with st.form("fm_item"):
            e_sku = st.text_input("SKU")
            e_nama = st.text_input("Nama Barang")
            e_satuan = st.selectbox("Satuan Default", st.session_state.master_units)
            e_harga = st.number_input("Harga Jual", format="%.5f")
            e_min = st.number_input("Min Stok", format="%.5f")
            if st.form_submit_button("Simpan Data Item"):
                mask = st.session_state.master_items['SKU'] == e_sku
                if mask.any():
                    st.session_state.master_items.loc[mask, ['Nama', 'Satuan', 'Harga_Jual', 'Min_Stok']] = [e_nama, e_satuan, e_harga, e_min]
                else:
                    new_row = {"SKU": e_sku, "Nama": e_nama, "Satuan": e_satuan, "Harga_Jual": e_harga, "Stok": 0.0, "Min_Stok": e_min}
                    st.session_state.master_items = pd.concat([st.session_state.master_items, pd.DataFrame([new_row])], ignore_index=True)
                st.rerun()
    st.table(st.session_state.master_items)

# --- 4. PROCUREMENT (PR/PO/GR) DENGAN INPUT QTY TERIMA ---
elif menu == "Procurement (PR/PO/GR)":
    st.header("🛒 Procurement Control")
    
    with st.expander("📝 Buat Purchase Requisition (PR)", expanded=True):
        with st.form("pr_form"):
            p_item = st.selectbox("Pilih Barang", st.session_state.master_items['Nama'].tolist())
            
            # FITUR BARU: AUTO-SYNC SATUAN
            it_info = st.session_state.master_items[st.session_state.master_items['Nama'] == p_item].iloc[0]
            st.info(f"Satuan Unit Terpilih: **{it_info['Satuan']}**")
            
            p_qty = st.number_input("Quantity Pesanan", format="%.5f")
            p_prc = st.number_input("Estimasi Harga Satuan Beli", format="%.5f")
            
            if st.form_submit_button("Ajukan PR"):
                st.session_state.pr_data.append({
                    "ID": f"PR-{datetime.now().strftime('%y%m%d%H%M')}", 
                    "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Item": p_item, 
                    "Satuan": it_info['Satuan'], 
                    "Qty_Pesanan": p_qty, 
                    "Qty_Diterima": 0.0,
                    "Harga": p_prc, 
                    "Status": "Pending", 
                    "Total_Estimasi": p_qty * p_prc
                })
                st.success("PR Berhasil Disimpan")
                st.rerun()

    st.subheader("📋 Daftar Transaksi Aktif")
    for i, pr in enumerate(st.session_state.pr_data):
        if pr['Status'] != "Closed":
            with st.container():
                st.markdown(f"**ID: {pr['ID']} | Item: {pr['Item']} ({smart_format(pr['Qty_Pesanan'])} {pr['Satuan']})**")
                col1, col2 = st.columns(2)
                
                if pr['Status'] == "Pending":
                    if col1.button("✅ Approve", key=f"ap_{i}"): 
                        st.session_state.pr_data[i]['Status'] = "Approved"; st.rerun()
                    if col2.button("🗑️ Cancel", key=f"cn_{i}"): 
                        st.session_state.pr_data.pop(i); st.rerun()
                
                elif pr['Status'] == "Approved":
                    # FITUR BARU: INPUT QTY SAAT GR
                    qty_fisik = col1.number_input(f"Input Qty Fisik Diterima ({pr['Satuan']})", key=f"gr_qty_{i}", format="%.5f")
                    if col2.button("🚚 Konfirmasi Penerimaan (GR)", key=f"gr_btn_{i}"):
                        if qty_fisik <= 0:
                            st.error("Qty fisik harus lebih dari 0")
                        else:
                            sku = st.session_state.master_items[st.session_state.master_items['Nama'] == pr['Item']]['SKU'].values[0]
                            idx_it = st.session_state.master_items[st.session_state.master_items['SKU'] == sku].index[0]
                            
                            # Stok bertambah sesuai Qty Fisik, bukan Qty Pesanan
                            st.session_state.master_items.at[idx_it, 'Stok'] += qty_fisik
                            st.session_state.pr_data[i]['Qty_Diterima'] = qty_fisik
                            st.session_state.pr_data[i]['Status'] = "Closed"
                            st.success(f"Berhasil update stok sebanyak {smart_format(qty_fisik)}")
                            st.rerun()

# --- 5. POS (KASIR) ---
elif menu == "POS (Kasir)":
    st.header("🛒 Kasir POS")
    if st.session_state.cash_session['status'] == "Closed":
        modal = st.number_input("Modal Awal", format="%.5f")
        if st.button("Buka Kasir"): 
            st.session_state.cash_session = {"modal_awal": modal, "status": "Open"}
            st.rerun()
    else:
        with st.form("pos_f"):
            s_item = st.selectbox("Menu", st.session_state.master_items['Nama'].tolist())
            s_qty = st.number_input("Qty", format="%.5f")
            if st.form_submit_button("Tambah"):
                price = st.session_state.master_items[st.session_state.master_items['Nama'] == s_item]['Harga_Jual'].values[0]
                st.session_state.pos_transactions.append({
                    "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"), "Item": s_item, "Qty": s_qty, "Net_Total": s_qty * price
                })
                idx = st.session_state.master_items[st.session_state.master_items['Nama'] == s_item].index[0]
                st.session_state.master_items.at[idx, 'Stok'] -= s_qty
                st.rerun()
        st.table(pd.DataFrame(st.session_state.pos_transactions).tail(5))

# --- 6. RIWAYAT TRANSAKSI ---
elif menu == "Riwayat Transaksi":
    st.header("📜 Log Aktivitas")
    t_pr, t_pos = st.tabs(["Log GR (Penerimaan)", "Log Penjualan"])
    with t_pr:
        closed = [p for p in st.session_state.pr_data if p['Status'] == "Closed"]
        if closed:
            df = pd.DataFrame(closed)
            # Menampilkan perbandingan pesanan vs fisik
            st.table(df[['ID', 'Tanggal', 'Item', 'Qty_Pesanan', 'Qty_Diterima', 'Satuan', 'Status']])
    with t_pos:
        if st.session_state.pos_transactions: st.table(pd.DataFrame(st.session_state.pos_transactions))

# --- 7. FINANCIAL REPORT ---
elif menu == "Financial Report":
    st.header("📈 Profit & Loss")
    rev = sum(t['Net_Total'] for t in st.session_state.pos_transactions)
    exp = sum(e['Nominal'] for e in st.session_state.expenses_data)
    st.metric("Total Revenue", smart_format(rev))
    st.metric("Total OPEX", smart_format(exp))
    st.subheader(f"Laba Bersih: Rp {smart_format(rev - exp)}")
