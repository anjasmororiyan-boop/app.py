import streamlit as st
import pandas as pd
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="ERP Business Suite V4 - Precision Costing", layout="wide")

# --- FUNGSI FORMATTING CUSTOM ---
def format_money(value):
    """Format angka dengan separator ribuan dan 5 desimal"""
    return "{:,.5f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")

# --- INITIAL DATA (SESSION STATE) ---
if 'master_items' not in st.session_state:
    st.session_state.master_items = pd.DataFrame([
        {"SKU": "BRG001", "Nama": "Tepung Terigu", "Satuan": "Kg", "Min_Stok": 50.00000},
        {"SKU": "BRG002", "Nama": "Minyak Goreng", "Satuan": "Liter", "Min_Stok": 20.00000}
    ])

if 'inventory' not in st.session_state:
    st.session_state.inventory = {"BRG001": 10.00000, "BRG002": 5.00000}

if 'pr_data' not in st.session_state:
    st.session_state.pr_data = []

if 'sales_data' not in st.session_state:
    st.session_state.sales_data = []

if 'expenses_data' not in st.session_state:
    st.session_state.expenses_data = []

# --- UI SIDEBAR ---
st.sidebar.title("ERP Precision Suite V4")
menu = st.sidebar.radio("Navigasi", [
    "Dashboard", 
    "Master Item", 
    "Procurement (PR/PO/GR)", 
    "Sales & Revenue", 
    "Expenses (Biaya)", 
    "Financial Report"
])

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.header("📊 Executive Summary (Precision Mode)")
    total_sales = sum(s['Total'] for s in st.session_state.sales_data)
    total_costs = sum(p['Harga'] * p['Qty_GR'] for p in st.session_state.pr_data if p['Status'] == "Closed (Received)")
    total_opex = sum(e['Nominal'] for e in st.session_state.expenses_data)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Penjualan", format_money(total_sales))
    c2.metric("Total HPP (Procurement)", format_money(total_costs))
    c3.metric("Net Profit Est.", format_money(total_sales - total_costs - total_opex))

    st.subheader("📦 Inventory Alert")
    inventory_list = []
    for _, row in st.session_state.master_items.iterrows():
        current_stok = st.session_state.inventory.get(row['SKU'], 0)
        inventory_list.append({
            "Item": row['Nama'], 
            "Stok Saat Ini": format_money(current_stok), 
            "Batas Minimum": format_money(row['Min_Stok'])
        })
    st.table(pd.DataFrame(inventory_list))

# --- 2. MASTER ITEM ---
elif menu == "Master Item":
    st.header("📦 Master Data Barang")
    with st.form("fm_item"):
        col_m1, col_m2 = st.columns(2)
        n_sku = col_m1.text_input("SKU")
        n_nama = col_m1.text_input("Nama Barang")
        n_satuan = col_m2.selectbox("Satuan", ["Kg", "Liter", "Pcs", "Box"])
        n_min = col_m2.number_input("Minimum Stok (5 Desimal)", format="%.5f")
        if st.form_submit_button("Simpan Item"):
            new_row = {"SKU": n_sku, "Nama": n_nama, "Satuan": n_satuan, "Min_Stok": n_min}
            st.session_state.master_items = pd.concat([st.session_state.master_items, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()
    
    # Format tabel master untuk display
    display_master = st.session_state.master_items.copy()
    display_master['Min_Stok'] = display_master['Min_Stok'].apply(format_money)
    st.table(display_master)

# --- 3. PROCUREMENT (PR/PO/GR) ---
elif menu == "Procurement (PR/PO/GR)":
    st.header("🛒 Procurement Workflow")
    tab1, tab2, tab3 = st.tabs(["Create PR", "Approval", "PO & Goods Receipt"])
    
    with tab1:
        with st.form("fm_pr"):
            u_item = st.selectbox("Pilih Barang", st.session_state.master_items['Nama'].tolist())
            u_sku = st.session_state.master_items[st.session_state.master_items['Nama'] == u_item]['SKU'].values[0]
            u_qty = st.number_input("Jumlah Pesanan", format="%.5f")
            u_price = st.number_input("Harga Satuan (Rp)", format="%.5f")
            if st.form_submit_button("Ajukan PR"):
                st.session_state.pr_data.append({
                    "ID": f"PR-{datetime.now().strftime('%y%m%d%H%M')}",
                    "SKU": u_sku, "Item": u_item, "Qty_PO": u_qty, "Qty_GR": 0.00000,
                    "Harga": u_price, "Total": u_qty * u_price, "Status": "Pending"
                })
        
        if st.session_state.pr_data:
            df_pr = pd.DataFrame(st.session_state.pr_data)
            df_pr['Harga'] = df_pr['Harga'].apply(format_money)
            df_pr['Total'] = df_pr['Total'].apply(format_money)
            st.table(df_pr)

    with tab2:
        for i, pr in enumerate(st.session_state.pr_data):
            if pr['Status'] == "Pending":
                st.write(f"**{pr['ID']}** - {pr['Item']} - Rp {format_money(pr['Total'])}")
                if st.button(f"Approve {pr['ID']}", key=f"app_{i}"):
                    st.session_state.pr_data[i]['Status'] = "Approved"
                    st.rerun()

    with tab3:
        approved = [p for p in st.session_state.pr_data if p['Status'] == "Approved"]
        if approved:
            sel_id = st.selectbox("Pilih PO untuk Penerimaan (GR)", [p['ID'] for p in approved])
            with st.form("gr_form"):
                gr_qty = st.number_input("Jumlah Diterima Fisik", format="%.5f")
                if st.form_submit_button("Konfirmasi Penerimaan (GR)"):
                    for i, p in enumerate(st.session_state.pr_data):
                        if p['ID'] == sel_id:
                            st.session_state.inventory[p['SKU']] += gr_qty
                            st.session_state.pr_data[i]['Qty_GR'] = gr_qty
                            st.session_state.pr_data[i]['Status'] = "Closed (Received)"
                            st.rerun()

# --- 4. SALES & REVENUE ---
elif menu == "Sales & Revenue":
    st.header("💰 Input Penjualan")
    with st.form("sales_form"):
        s_date = st.date_input("Tanggal Penjualan")
        s_desc = st.text_input("Detail Transaksi")
        s_total = st.number_input("Total Penjualan (Rp)", format="%.5f")
        if st.form_submit_button("Simpan Penjualan"):
            st.session_state.sales_data.append({"Tanggal": s_date, "Keterangan": s_desc, "Total": s_total})
            st.success("Data Penjualan Tersimpan")
    
    if st.session_state.sales_data:
        df_sales = pd.DataFrame(st.session_state.sales_data)
        df_sales['Total'] = df_sales['Total'].apply(format_money)
        st.table(df_sales)

# --- 5. EXPENSES ---
elif menu == "Expenses (Biaya)":
    st.header("💸 Biaya Operasional")
    with st.form("exp_form"):
        e_date = st.date_input("Tanggal")
        e_cat = st.selectbox("Kategori", ["Gaji", "Listrik/Air", "Sewa", "Marketing", "Lain-lain"])
        e_val = st.number_input("Nominal (Rp)", format="%.5f")
        if st.form_submit_button("Simpan Biaya"):
            st.session_state.expenses_data.append({"Tanggal": e_date, "Kategori": e_cat, "Nominal": e_val})
            st.success("Biaya Tersimpan")
    
    if st.session_state.expenses_data:
        df_exp = pd.DataFrame(st.session_state.expenses_data)
        df_exp['Nominal'] = df_exp['Nominal'].apply(format_money)
        st.table(df_exp)

# --- 6. FINANCIAL REPORT ---
elif menu == "Financial Report":
    st.header("📈 Laporan Laba Rugi (Precision)")
    
    rev = sum(s['Total'] for s in st.session_state.sales_data)
    cogs = sum(p['Harga'] * p['Qty_GR'] for p in st.session_state.pr_data if p['Status'] == "Closed (Received)")
    opex = sum(e['Nominal'] for e in st.session_state.expenses_data)
    net_profit = rev - cogs - opex
    
    st.markdown("---")
    st.subheader("Statement of Profit or Loss")
    st.write(f"**Total Pendapatan (Sales):** Rp {format_money(rev)}")
    st.write(f"**Harga Pokok Penjualan (HPP):** (Rp {format_money(cogs)})")
    st.write(f"**Total Biaya Operasional (OPEX):** (Rp {format_money(opex)})")
    st.markdown("---")
    color = "green" if net_profit >= 0 else "red"
    st.markdown(f"## **Laba Bersih (Net Profit):** :{color}[Rp {format_money(net_profit)}]")
