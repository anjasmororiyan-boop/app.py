import streamlit as st
import pandas as pd

# Judul Aplikasi
st.set_page_config(page_title="ERP SCM Test", layout="wide")
st.title("🚀 ERP Purchase & Supply Chain Prototype")

# Simulasi Database Sederhana
if 'inventory' not in st.session_state:
    st.session_state.inventory = [
        {"SKU": "B001", "Nama": "Tepung Terigu", "Stok": 50, "Min": 100},
        {"SKU": "B002", "Nama": "Mentega Blueband", "Stok": 120, "Min": 50},
        {"SKU": "B003", "Nama": "Gula Pasir", "Stok": 10, "Min": 60},
    ]

if 'po_list' not in st.session_state:
    st.session_state.po_list = []

# --- SIDEBAR MENU ---
menu = st.sidebar.selectbox("Menu Utama", ["Dashboard", "Procurement", "Inventory Control"])

# --- HALAMAN DASHBOARD ---
if menu == "Dashboard":
    st.header("Ringkasan Operasional")
    
    col1, col2, col3 = st.columns(3)
    low_stock_count = len([i for i in st.session_state.inventory if i['Stok'] < i['Min']])
    
    col1.metric("Total Item", len(st.session_state.inventory))
    col2.metric("Stok Kritis", low_stock_count, delta_color="inverse")
    col3.metric("PO Pending", len(st.session_state.po_list))

    st.subheader("Peringatan Stok Rendah")
    for item in st.session_state.inventory:
        if item['Stok'] < item['Min']:
            st.warning(f"⚠️ {item['Nama']} (SKU: {item['SKU']}) segera habis! Stok: {item['Stok']}, Batas Min: {item['Min']}")

# --- HALAMAN PROCUREMENT ---
elif menu == "Procurement":
    st.header("Buat Purchase Order (PO)")
    
    with st.form("form_po"):
        vendor = st.selectbox("Pilih Vendor", ["PT Indosari", "Logistik Utama", "CV Rasa"])
        item_name = st.selectbox("Pilih Barang", [i['Nama'] for i in st.session_state.inventory])
        qty = st.number_input("Jumlah Pesanan", min_value=1)
        price = st.number_input("Harga Satuan (Rp)", min_value=1000)
        submit = st.form_submit_button("Ajukan PO")

    if submit:
        total = qty * price
        # Logika Approval Berdasarkan Nominal
        status = "Menunggu Direktur" if total > 10000000 else "Disetujui Manajer"
        
        new_po = {
            "ID": f"PO-{len(st.session_state.po_list)+1:03d}",
            "Vendor": vendor,
            "Item": item_name,
            "Total": f"Rp {total:,.0f}",
            "Status": status
        }
        st.session_state.po_list.append(new_po)
        st.success(f"PO Berhasil Diajukan! Status: {status}")

    st.subheader("Riwayat PO")
    st.table(pd.DataFrame(st.session_state.po_list))

# --- HALAMAN INVENTORY ---
elif menu == "Inventory Control":
    st.header("Manajemen Inventori")
    df_inv = pd.DataFrame(st.session_state.inventory)
    st.dataframe(df_inv, use_container_width=True)
    
    st.info("Catatan: Data di atas disimulasikan sesuai dengan alur ROP (Reorder Point) yang telah kita bahas.")
