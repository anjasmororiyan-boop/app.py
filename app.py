import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="ERP SCM & Finance V3", layout="wide")

# --- INITIAL DATA (SESSION STATE) ---
if 'master_items' not in st.session_state:
    st.session_state.master_items = pd.DataFrame([
        {"SKU": "BRG001", "Nama": "Tepung Terigu", "Satuan": "Kg", "Min_Stok": 50},
        {"SKU": "BRG002", "Nama": "Minyak Goreng", "Satuan": "Liter", "Min_Stok": 20}
    ])

if 'inventory' not in st.session_state:
    st.session_state.inventory = {"BRG001": 10, "BRG002": 5}

if 'pr_data' not in st.session_state:
    st.session_state.pr_data = []

if 'sales_data' not in st.session_state:
    st.session_state.sales_data = []

if 'expenses_data' not in st.session_state:
    st.session_state.expenses_data = []

# --- UI SIDEBAR ---
st.sidebar.title("ERP Business Suite V3")
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
    st.header("📊 Executive Summary")
    total_sales = sum(s['Total'] for s in st.session_state.sales_data)
    total_costs = sum(p['Harga'] * p['Qty_GR'] for p in st.session_state.pr_data if p['Status'] == "Closed (Received)")
    total_opex = sum(e['Nominal'] for e in st.session_state.expenses_data)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Penjualan", f"Rp{total_sales:,.0f}")
    c2.metric("Total Pembelian (HPP)", f"Rp{total_costs:,.0f}")
    c3.metric("Net Profit Est.", f"Rp{(total_sales - total_costs - total_opex):,.0f}")

    st.subheader("📦 Inventory Alert")
    df_status = pd.DataFrame([
        {"Item": row['Nama'], "Stok": st.session_state.inventory.get(row['SKU'], 0), "Min": row['Min_Stok']}
        for _, row in st.session_state.master_items.iterrows()
    ])
    st.table(df_status)

# --- 2. MASTER ITEM ---
elif menu == "Master Item":
    st.header("📦 Master Data Barang")
    with st.form("fm_item"):
        col_m1, col_m2 = st.columns(2)
        n_sku = col_m1.text_input("SKU")
        n_nama = col_m1.text_input("Nama Barang")
        n_satuan = col_m2.selectbox("Satuan", ["Kg", "Liter", "Pcs", "Box"])
        n_min = col_m2.number_input("Minimum Stok", min_value=1)
        if st.form_submit_button("Simpan Item"):
            new_row = {"SKU": n_sku, "Nama": n_nama, "Satuan": n_satuan, "Min_Stok": n_min}
            st.session_state.master_items = pd.concat([st.session_state.master_items, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()
    st.table(st.session_state.master_items)

# --- 3. PROCUREMENT (PR/PO/GR combined for simplicity) ---
elif menu == "Procurement (PR/PO/GR)":
    st.header("🛒 Procurement Workflow")
    
    tab1, tab2, tab3 = st.tabs(["Create PR", "Approval", "PO & Goods Receipt"])
    
    with tab1:
        with st.form("fm_pr"):
            u_item = st.selectbox("Pilih Barang", st.session_state.master_items['Nama'].tolist())
            u_sku = st.session_state.master_items[st.session_state.master_items['Nama'] == u_item]['SKU'].values[0]
            u_qty = st.number_input("Jumlah Pesanan", min_value=1)
            u_price = st.number_input("Harga Satuan (Rp)", min_value=0)
            if st.form_submit_button("Ajukan PR"):
                st.session_state.pr_data.append({
                    "ID": f"PR-{datetime.now().strftime('%y%m%d%H%M')}",
                    "SKU": u_sku, "Item": u_item, "Qty_PO": u_qty, "Qty_GR": 0,
                    "Harga": u_price, "Total": u_qty * u_price, "Status": "Pending"
                })
        st.table(pd.DataFrame(st.session_state.pr_data))

    with tab2:
        for i, pr in enumerate(st.session_state.pr_data):
            if pr['Status'] == "Pending":
                st.write(f"**{pr['ID']}** - {pr['Item']} - Rp{pr['Total']:,}")
                if st.button(f"Approve {pr['ID']}", key=f"app_{i}"):
                    st.session_state.pr_data[i]['Status'] = "Approved"
                    st.rerun()

    with tab3:
        approved = [p for p in st.session_state.pr_data if p['Status'] == "Approved"]
        if approved:
            sel_id = st.selectbox("Pilih PO untuk GR", [p['ID'] for p in approved])
            with st.form("gr_form"):
                gr_qty = st.number_input("Jumlah Diterima Fisik", min_value=0)
                if st.form_submit_button("Post GR"):
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
        s_desc = st.text_input("Keterangan/Nama Customer")
        s_total = st.number_input("Total Nilai Penjualan (Rp)", min_value=0)
        if st.form_submit_button("Simpan Penjualan"):
            st.session_state.sales_data.append({
                "Tanggal": s_date, "Keterangan": s_desc, "Total": s_total
            })
            st.success("Data Penjualan Tersimpan")
    st.table(pd.DataFrame(st.session_state.sales_data))

# --- 5. EXPENSES ---
elif menu == "Expenses (Biaya)":
    st.header("💸 Biaya Operasional (OPEX)")
    with st.form("exp_form"):
        e_date = st.date_input("Tanggal Biaya")
        e_cat = st.selectbox("Kategori", ["Gaji", "Listrik/Air", "Sewa", "Marketing", "Lain-lain"])
        e_desc = st.text_input("Detail Biaya")
        e_val = st.number_input("Nominal (Rp)", min_value=0)
        if st.form_submit_button("Simpan Biaya"):
            st.session_state.expenses_data.append({
                "Tanggal": e_date, "Kategori": e_cat, "Keterangan": e_desc, "Nominal": e_val
            })
            st.success("Biaya Berhasil Dicatat")
    st.table(pd.DataFrame(st.session_state.expenses_data))

# --- 6. FINANCIAL REPORT ---
elif menu == "Financial Report":
    st.header("📈 Laporan Laba Rugi (Profit & Loss)")
    
    # Perhitungan
    rev = sum(s['Total'] for s in st.session_state.sales_data)
    cogs = sum(p['Harga'] * p['Qty_GR'] for p in st.session_state.pr_data if p['Status'] == "Closed (Received)")
    gross_profit = rev - cogs
    opex = sum(e['Nominal'] for e in st.session_state.expenses_data)
    net_profit = gross_profit - opex
    
    # Tampilan Laporan
    st.markdown("""---""")
    st.subheader("Statement of Profit or Loss")
    st.write(f"**Total Pendapatan (Sales):** Rp{rev:,.0f}")
    st.write(f"**Harga Pokok Penjualan (HPP):** (Rp{cogs:,.0f})")
    st.markdown(f"### **Laba Kotor (Gross Profit):** Rp{gross_profit:,.0f}")
    st.write(f"**Total Biaya Operasional (OPEX):** (Rp{opex:,.0f})")
    st.markdown("---")
    color = "green" if net_profit >= 0 else "red"
    st.markdown(f"## **Laba Bersih (Net Profit):** :{color}[Rp{net_profit:,.0f}]")
    st.markdown("""---""")
    
    if st.button("Export Laporan (Simulasi)"):
        st.info("Fitur export ke Excel/PDF dapat diaktifkan dengan library tambahan.")
