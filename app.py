import streamlit as st
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="ERP Business Suite V9 - Transaction History", layout="wide")

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
    'cash_session': {"modal_awal": 0.0, "status": "Closed"},
    'promos': pd.DataFrame([{"Nama_Promo": "No Promo", "Diskon_Persen": 0.0, "Diskon_Nominal": 0.0}])
}

for key, val in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.title("🔐 Login ERP & POS System")
    with st.form("login_form"):
        u = st.text_input("Username (admin)")
        p = st.text_input("Password (admin123)", type="password")
        if st.form_submit_button("Login"):
            if u == "admin" and p == "admin123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Login Gagal.")
    st.stop()

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("ERP Business Suite")
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
    
    st.subheader("📦 Monitoring Stok")
    df_mon = st.session_state.master_items.copy()
    df_mon['Stok'] = df_mon['Stok'].apply(smart_format)
    st.table(df_mon[['SKU', 'Nama', 'Satuan', 'Stok', 'Min_Stok']])

# --- 2. MASTER PENGATURAN ---
elif menu == "Master Pengaturan":
    st.header("⚙️ Pengaturan Unit & Biaya")
    col_u, col_e = st.columns(2)
    with col_u:
        st.subheader("Manage Units")
        new_u = st.text_input("Tambah Satuan")
        if st.button("Simpan Satuan"):
            st.session_state.master_units.append(new_u); st.rerun()
        for idx, u in enumerate(st.session_state.master_units):
            ca, cb = st.columns([3,1])
            ca.write(u)
            if cb.button("🗑️", key=f"del_u_{idx}"): st.session_state.master_units.pop(idx); st.rerun()
    with col_e:
        st.subheader("Manage Expense Categories")
        new_ex = st.text_input("Tambah Kategori Biaya")
        if st.button("Simpan Kategori"):
            st.session_state.expense_categories.append(new_ex); st.rerun()
        for idx, ex in enumerate(st.session_state.expense_categories):
            ca, cb = st.columns([3,1])
            ca.write(ex)
            if cb.button("🗑️", key=f"del_ex_{idx}"): st.session_state.expense_categories.pop(idx); st.rerun()

# --- 3. MASTER BARANG ---
elif menu == "Master Barang & Promo":
    st.header("📦 Master Data")
    with st.expander("➕ Tambah / Edit Item"):
        with st.form("fm_item"):
            e_sku = st.text_input("SKU")
            e_nama = st.text_input("Nama Barang")
            e_satuan = st.selectbox("Satuan", st.session_state.master_units)
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
    
    for i, row in st.session_state.master_items.iterrows():
        c_a, c_b = st.columns([5, 1])
        c_a.write(f"**{row['SKU']}** | {row['Nama']} | Harga: {smart_format(row['Harga_Jual'])} | Stok: {smart_format(row['Stok'])} {row['Satuan']}")
        if c_b.button("🗑️ Delete", key=f"del_it_{i}"):
            st.session_state.master_items = st.session_state.master_items.drop(i).reset_index(drop=True); st.rerun()

# --- 4. PROCUREMENT ---
elif menu == "Procurement (PR/PO/GR)":
    st.header("🛒 Procurement Control")
    with st.expander("📝 Buat PR Baru"):
        with st.form("pr_form"):
            p_item = st.selectbox("Item", st.session_state.master_items['Nama'].tolist())
            it_info = st.session_state.master_items[st.session_state.master_items['Nama'] == p_item].iloc[0]
            p_qty = st.number_input("Qty", format="%.5f")
            p_prc = st.number_input("Harga Satuan Beli", format="%.5f")
            if st.form_submit_button("Submit PR"):
                st.session_state.pr_data.append({
                    "ID": f"PR-{datetime.now().strftime('%y%m%d%H%M')}", "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Item": p_item, "Satuan": it_info['Satuan'], "Qty": p_qty, "Harga": p_prc, "Status": "Pending", "Total": p_qty * p_prc
                })
                st.rerun()

    for i, pr in enumerate(st.session_state.pr_data):
        if pr['Status'] != "Closed":
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 2])
                col1.write(f"**{pr['ID']}** - {pr['Item']} ({smart_format(pr['Qty'])} {pr['Satuan']})")
                if pr['Status'] == "Pending":
                    new_q = col2.number_input("Edit Qty", value=float(pr['Qty']), key=f"eq_{i}", format="%.5f")
                    st.session_state.pr_data[i]['Qty'] = new_q
                    if col3.button("✅ Approve", key=f"ap_{i}"): st.session_state.pr_data[i]['Status'] = "Approved"; st.rerun()
                elif pr['Status'] == "Approved":
                    col2.write("Status: Approved")
                    if col3.button("🚚 Post GR", key=f"gr_{i}"):
                        sku = st.session_state.master_items[st.session_state.master_items['Nama'] == pr['Item']]['SKU'].values[0]
                        idx = st.session_state.master_items[st.session_state.master_items['SKU'] == sku].index[0]
                        st.session_state.master_items.at[idx, 'Stok'] += pr['Qty']
                        st.session_state.pr_data[i]['Status'] = "Closed"; st.rerun()

# --- 5. POS (KASIR) ---
elif menu == "POS (Kasir)":
    st.header("🛒 POS Kasir")
    if st.session_state.cash_session['status'] == "Closed":
        modal = st.number_input("Modal Awal", format="%.5f")
        if st.button("Buka Kasir"): 
            st.session_state.cash_session = {"modal_awal": modal, "status": "Open", "buka": datetime.now()}
            st.rerun()
    else:
        with st.form("pos_f"):
            s_item = st.selectbox("Menu", st.session_state.master_items['Nama'].tolist())
            s_qty = st.number_input("Qty", format="%.5f")
            if st.form_submit_button("Add to Bill"):
                p_jual = st.session_state.master_items[st.session_state.master_items['Nama'] == s_item]['Harga_Jual'].values[0]
                st.session_state.pos_transactions.append({
                    "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"), "Item": s_item, "Qty": s_qty, "Net_Total": s_qty * p_jual
                })
                idx = st.session_state.master_items[st.session_state.master_items['Nama'] == s_item].index[0]
                st.session_state.master_items.at[idx, 'Stok'] -= s_qty
                st.rerun()
        st.table(pd.DataFrame(st.session_state.pos_transactions).tail(5))

# --- 6. RIWAYAT TRANSAKSI (NEW MODULE) ---
elif menu == "Riwayat Transaksi":
    st.header("📜 Riwayat Transaksi Lengkap")
    t_pr, t_pos, t_exp = st.tabs(["Procurement (GR)", "Penjualan (POS)", "Pengeluaran (Expenses)"])
    
    with t_pr:
        st.subheader("Log Penerimaan Barang")
        closed_pr = [p for p in st.session_state.pr_data if p['Status'] == "Closed"]
        if closed_pr:
            df_cl_pr = pd.DataFrame(closed_pr)
            df_cl_pr['Harga'] = df_cl_pr['Harga'].apply(smart_format)
            df_cl_pr['Total'] = df_cl_pr['Total'].apply(smart_format)
            st.table(df_cl_pr)
        else: st.write("Belum ada riwayat pengadaan.")

    with t_pos:
        st.subheader("Log Penjualan POS")
        if st.session_state.pos_transactions:
            df_cl_pos = pd.DataFrame(st.session_state.pos_transactions)
            df_cl_pos['Net_Total'] = df_cl_pos['Net_Total'].apply(smart_format)
            st.table(df_cl_pos)
        else: st.write("Belum ada riwayat penjualan.")

    with t_exp:
        st.subheader("Log Pengeluaran Biaya")
        if st.session_state.expenses_data:
            df_cl_exp = pd.DataFrame(st.session_state.expenses_data)
            df_cl_exp['Nominal'] = df_cl_exp['Nominal'].apply(smart_format)
            st.table(df_cl_exp)
        else: st.write("Belum ada riwayat pengeluaran.")

# --- 7. FINANCIAL REPORT ---
elif menu == "Financial Report":
    st.header("📈 Financial Report")
    with st.expander("Input Biaya Operasional"):
        with st.form("exp_f"):
            cat = st.selectbox("Kategori", st.session_state.expense_categories)
            nom = st.number_input("Nominal", format="%.5f")
            if st.form_submit_button("Simpan Biaya"):
                st.session_state.expenses_data.append({
                    "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"), "Kategori": cat, "Nominal": nom
                })
                st.rerun()
    
    rev = sum(t['Net_Total'] for t in st.session_state.pos_transactions)
    opex = sum(e['Nominal'] for e in st.session_state.expenses_data)
    st.markdown(f"### Revenue: Rp {smart_format(rev)}")
    st.markdown(f"### Total OPEX: (Rp {smart_format(opex)})")
    st.divider()
    st.markdown(f"## Net Profit: Rp {smart_format(rev - opex)}")
