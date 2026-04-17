import streamlit as st
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="ERP Business Suite V6 - Smart Formatting", layout="wide")

# --- SMART FORMATTING FUNCTION ---
def smart_format(val):
    """Format ribuan: Bulat tanpa desimal, Pecahan maks 5 desimal."""
    if val is None: return "0"
    # Jika angka adalah bulat (integer), tampilkan tanpa desimal
    if float(val).is_integer():
        return "{:,.0f}".format(val).replace(",", ".")
    # Jika pecahan, tampilkan hingga 5 desimal dan hapus nol berlebih di ujung
    formatted = "{:,.5f}".format(val).rstrip('0').rstrip('.')
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

# --- INITIALIZING SESSION STATES ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

default_states = {
    'master_units': ["Kg", "Liter", "Pcs", "Box", "Gram"],
    'expense_categories': ["Gaji", "Listrik/Air", "Sewa", "Marketing"],
    'master_items': pd.DataFrame([
        {"SKU": "BRG001", "Nama": "Espresso Coffee", "Satuan": "Kg", "Harga_Jual": 25000.0, "Stok": 100.0, "Min_Stok": 10.0}
    ]),
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
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u == "admin" and p == "admin123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Gunakan admin/admin123")
    st.stop()

# --- SIDEBAR NAVIGASI ---
menu = st.sidebar.radio("Navigasi", [
    "Dashboard", 
    "Master Pengaturan", 
    "Master Barang & Promo", 
    "Procurement (PR/PO/GR)", 
    "POS (Kasir)", 
    "Financial Report"
])

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.header("📊 Ringkasan Operasional")
    c1, c2 = st.columns(2)
    rev = sum(t['Net_Total'] for t in st.session_state.pos_transactions)
    c1.metric("Revenue POS", smart_format(rev))
    
    st.subheader("📦 Inventory Alert")
    df_disp = st.session_state.master_items.copy()
    df_disp['Stok'] = df_disp['Stok'].apply(smart_format)
    df_disp['Min_Stok'] = df_disp['Min_Stok'].apply(smart_format)
    st.table(df_disp)

# --- 2. MASTER PENGATURAN ---
elif menu == "Master Pengaturan":
    st.header("⚙️ Unit & Expense Categories")
    col1, col2 = st.columns(2)
    with col1:
        new_u = st.text_input("Tambah Satuan")
        if st.button("Simpan Satuan"):
            st.session_state.master_units.append(new_u)
            st.rerun()
        st.write(st.session_state.master_units)
    with col2:
        new_e = st.text_input("Tambah Kategori Biaya")
        if st.button("Simpan Kategori"):
            st.session_state.expense_categories.append(new_e)
            st.rerun()

# --- 3. MASTER BARANG ---
elif menu == "Master Barang & Promo":
    st.header("📦 Master Data")
    with st.form("add_item"):
        c1, c2 = st.columns(2)
        n_sku = c1.text_input("SKU")
        n_nama = c1.text_input("Nama")
        n_satuan = c2.selectbox("Satuan Default", st.session_state.master_units)
        n_harga = c2.number_input("Harga Jual", format="%.5f")
        n_min = c2.number_input("Min Stok", format="%.5f")
        if st.form_submit_button("Simpan"):
            new_item = {"SKU": n_sku, "Nama": n_nama, "Satuan": n_satuan, "Harga_Jual": n_harga, "Stok": 0.0, "Min_Stok": n_min}
            st.session_state.master_items = pd.concat([st.session_state.master_items, pd.DataFrame([new_item])], ignore_index=True)
            st.rerun()
    st.table(st.session_state.master_items)

# --- 4. PROCUREMENT (PR/PO/GR) ---
elif menu == "Procurement (PR/PO/GR)":
    st.header("🛒 Procurement Workflow")
    
    with st.expander("📝 Buat Purchase Requisition (PR)", expanded=True):
        with st.form("pr_form"):
            p_item = st.selectbox("Pilih Barang", st.session_state.master_items['Nama'].tolist())
            
            # OTOMATIS AMBIL SATUAN DARI MASTER
            item_info = st.session_state.master_items[st.session_state.master_items['Nama'] == p_item].iloc[0]
            st.info(f"Satuan Barang: {item_info['Satuan']}") # Info untuk user
            
            p_qty = st.number_input("Quantity", format="%.5f")
            p_prc = st.number_input("Harga Satuan Beli", format="%.5f")
            
            if st.form_submit_button("Ajukan PR"):
                st.session_state.pr_data.append({
                    "ID": f"PR-{datetime.now().strftime('%H%M%S')}",
                    "Item": p_item,
                    "Satuan": item_info['Satuan'], # Satuan terkunci dari Master
                    "Qty": p_qty,
                    "Harga": p_prc,
                    "Total": p_qty * p_prc,
                    "Status": "Approved"
                })
                st.success("PR Berhasil Diajukan!")
    
    if st.session_state.pr_data:
        st.subheader("Daftar PR & Status Penerimaan")
        df_pr = pd.DataFrame(st.session_state.pr_data)
        # Apply smart formatting untuk tampilan tabel
        df_pr_disp = df_pr.copy()
        df_pr_disp['Qty'] = df_pr_disp['Qty'].apply(smart_format)
        df_pr_disp['Harga'] = df_pr_disp['Harga'].apply(smart_format)
        df_pr_disp['Total'] = df_pr_disp['Total'].apply(smart_format)
        st.table(df_pr_disp)

        # Proses GR (Goods Receipt)
        st.subheader("🚚 Penerimaan Barang (GR)")
        for i, pr in enumerate(st.session_state.pr_data):
            if pr['Status'] == "Approved":
                if st.button(f"Terima {pr['Item']} ({pr['ID']})", key=f"gr_{i}"):
                    sku = st.session_state.master_items[st.session_state.master_items['Nama'] == pr['Item']]['SKU'].values[0]
                    idx = st.session_state.master_items[st.session_state.master_items['SKU'] == sku].index[0]
                    st.session_state.master_items.at[idx, 'Stok'] += pr['Qty']
                    st.session_state.pr_data[i]['Status'] = "Closed"
                    st.rerun()

# --- 5. POS (KASIR) ---
elif menu == "POS (Kasir)":
    st.header("🛒 Point of Sales")
    # Logika POS dengan Smart Formatting
    items = st.session_state.master_items['Nama'].tolist()
    sel_item = st.selectbox("Item", items)
    qty = st.number_input("Qty", format="%.5f")
    if st.button("Add to Bill"):
        price = st.session_state.master_items[st.session_state.master_items['Nama'] == sel_item]['Harga_Jual'].values[0]
        st.session_state.pos_transactions.append({
            "Waktu": datetime.now().strftime("%H:%M"),
            "Item": sel_item,
            "Qty": qty,
            "Net_Total": qty * price
        })
        st.rerun()
    
    if st.session_state.pos_transactions:
        df_pos = pd.DataFrame(st.session_state.pos_transactions)
        df_pos['Qty'] = df_pos['Qty'].apply(smart_format)
        df_pos['Net_Total'] = df_pos['Net_Total'].apply(smart_format)
        st.table(df_pos)

# --- 6. FINANCIAL REPORT ---
elif menu == "Financial Report":
    st.header("📈 Profit & Loss Report")
    rev = sum(t['Net_Total'] for t in st.session_state.pos_transactions)
    exp = sum(e['Nominal'] for e in st.session_state.expenses_data)
    
    st.markdown(f"### Revenue: Rp {smart_format(rev)}")
    st.markdown(f"### Expenses: (Rp {smart_format(exp)})")
    st.divider()
    profit = rev - exp
    color = "green" if profit >= 0 else "red"
    st.markdown(f"## Net Profit: :{color}[Rp {smart_format(profit)}]")
