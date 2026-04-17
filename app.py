import streamlit as st
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="ERP V7 - Full CRUD & Control", layout="wide")

# --- SMART FORMATTING ---
def smart_format(val):
    if val is None: return "0"
    if float(val).is_integer():
        return "{:,.0f}".format(val).replace(",", ".")
    formatted = "{:,.5f}".format(val).rstrip('0').rstrip('.')
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

# --- INITIALIZING SESSION STATES ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

default_states = {
    'master_units': ["Kg", "Liter", "Pcs", "Gram"],
    'expense_categories': ["Gaji", "Listrik/Air", "Sewa"],
    'master_items': pd.DataFrame([
        {"SKU": "BRG001", "Nama": "Espresso Coffee", "Satuan": "Kg", "Harga_Jual": 25000.0, "Stok": 100.0, "Min_Stok": 10.0}
    ]),
    'pr_data': [],
    'pos_transactions': [],
    'expenses_data': []
}

for key, val in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- LOGIN (admin/admin123) ---
if not st.session_state.logged_in:
    st.title("🔐 Login ERP System")
    with st.form("login"):
        u, p = st.text_input("User"), st.text_input("Pass", type="password")
        if st.form_submit_button("Login"):
            if u == "admin" and p == "admin123":
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

menu = st.sidebar.radio("Navigasi", ["Dashboard", "Master Management", "Procurement (PR/PO/GR)", "POS & Finance"])

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.header("📊 Dashboard Overview")
    st.table(st.session_state.master_items)

# --- 2. MASTER MANAGEMENT (EDIT & DELETE) ---
elif menu == "Master Management":
    st.header("⚙️ Master Data Management")
    
    t1, t2, t3 = st.tabs(["Master Items", "Units", "Expenses Categories"])
    
    with t1:
        # Form Add/Edit
        with st.expander("➕ Tambah / Edit Item"):
            with st.form("fm_item"):
                e_sku = st.text_input("SKU (Gunakan SKU lama untuk edit)")
                e_nama = st.text_input("Nama Baru")
                e_satuan = st.selectbox("Satuan", st.session_state.master_units)
                e_harga = st.number_input("Harga Jual", format="%.5f")
                e_min = st.number_input("Min Stok", format="%.5f")
                if st.form_submit_button("Update/Simpan Item"):
                    mask = st.session_state.master_items['SKU'] == e_sku
                    if mask.any(): # EDIT logic
                        st.session_state.master_items.loc[mask, ['Nama', 'Satuan', 'Harga_Jual', 'Min_Stok']] = [e_nama, e_satuan, e_harga, e_min]
                    else: # ADD logic
                        new_it = {"SKU": e_sku, "Nama": e_nama, "Satuan": e_satuan, "Harga_Jual": e_harga, "Stok": 0.0, "Min_Stok": e_min}
                        st.session_state.master_items = pd.concat([st.session_state.master_items, pd.DataFrame([new_it])], ignore_index=True)
                    st.rerun()

        # Delete Logic
        for i, row in st.session_state.master_items.iterrows():
            col_a, col_b = st.columns([4, 1])
            col_a.write(f"**{row['SKU']}** - {row['Nama']} ({row['Satuan']})")
            if col_b.button("🗑️ Delete", key=f"del_it_{i}"):
                st.session_state.master_items = st.session_state.master_items.drop(i).reset_index(drop=True)
                st.rerun()

    with t2:
        unit_to_add = st.text_input("Satuan Baru")
        if st.button("Tambah Satuan"): st.session_state.master_units.append(unit_to_add); st.rerun()
        for idx, u in enumerate(st.session_state.master_units):
            ca, cb = st.columns([4, 1])
            ca.write(u)
            if cb.button("🗑️", key=f"del_u_{idx}"): st.session_state.master_units.pop(idx); st.rerun()

# --- 3. PROCUREMENT (PR/PO/GR) DENGAN EDIT & CANCEL ---
elif menu == "Procurement (PR/PO/GR)":
    st.header("🛒 Procurement Control")
    
    # Form PR
    with st.expander("📝 Buat PR Baru"):
        with st.form("fm_pr"):
            p_item = st.selectbox("Item", st.session_state.master_items['Nama'].tolist())
            p_qty = st.number_input("Qty", format="%.5f")
            p_price = st.number_input("Harga Satuan", format="%.5f")
            if st.form_submit_button("Submit PR"):
                st.session_state.pr_data.append({
                    "ID": f"PR-{datetime.now().strftime('%H%M%S')}", "Item": p_item,
                    "Qty": p_qty, "Harga": p_price, "Status": "Pending"
                })
                st.rerun()

    st.subheader("📋 Transaksi PR Active")
    for i, pr in enumerate(st.session_state.pr_data):
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 2])
            col1.write(f"**{pr['ID']}** - {pr['Item']}")
            col1.write(f"Status: `{pr['Status']}`")
            
            # KONTROL BERDASARKAN STATUS
            if pr['Status'] == "Pending":
                new_q = col2.number_input("Edit Qty", value=float(pr['Qty']), key=f"q_{i}", format="%.5f")
                st.session_state.pr_data[i]['Qty'] = new_q
                if col3.button("✅ Approve", key=f"app_{i}"): 
                    st.session_state.pr_data[i]['Status'] = "Approved"; st.rerun()
                if col3.button("❌ Cancel PR", key=f"can_{i}"):
                    st.session_state.pr_data.pop(i); st.rerun()
            
            elif pr['Status'] == "Approved":
                if col2.button("🚚 Post GR (Terima)", key=f"gr_{i}"):
                    # Logic update stok
                    sku = st.session_state.master_items[st.session_state.master_items['Nama'] == pr['Item']]['SKU'].values[0]
                    idx_it = st.session_state.master_items[st.session_state.master_items['SKU'] == sku].index[0]
                    st.session_state.master_items.at[idx_it, 'Stok'] += pr['Qty']
                    st.session_state.pr_data[i]['Status'] = "Closed"; st.rerun()
                if col3.button("🔄 Reject ke Pending", key=f"rej_{i}"):
                    st.session_state.pr_data[i]['Status'] = "Pending"; st.rerun()

# --- 4. POS & FINANCE ---
elif menu == "POS & Finance":
    st.header("💰 POS & Financial Report")
    # (Logika POS dan Profit/Loss tetap menggunakan smart_format)
    rev = sum(t['Net_Total'] for t in st.session_state.pos_transactions)
    st.write(f"### Total Revenue: Rp {smart_format(rev)}")
