import streamlit as st
import pandas as pd
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="ERP Purchase & SCM", layout="wide")

# --- DATABASE SIMULATION (SESSION STATE) ---
if 'master_items' not in st.session_state:
    st.session_state.master_items = pd.DataFrame([
        {"SKU": "BRG001", "Nama": "Tepung Terigu", "Satuan": "Kg", "Min_Stok": 50},
        {"SKU": "BRG002", "Nama": "Minyak Goreng", "Satuan": "Liter", "Min_Stok": 20}
    ])

if 'inventory' not in st.session_state:
    st.session_state.inventory = {"BRG001": 10, "BRG002": 5}

if 'pr_data' not in st.session_state:
    st.session_state.pr_data = []

# --- FUNGSI HELPER ---
def add_pr(user, item_sku, qty, price):
    total = qty * price
    status = "Pending Manager"
    st.session_state.pr_data.append({
        "ID_PR": f"PR-{datetime.now().strftime('%y%m%d%H%M%S')}",
        "User": user,
        "SKU": item_sku,
        "Qty": qty,
        "Harga_Satuan": price,
        "Total": total,
        "Status": status,
        "Tanggal": datetime.now().date()
    })

# --- UI SIDEBAR ---
st.sidebar.title("ERP SCM System")
menu = st.sidebar.radio("Navigasi", ["Dashboard", "Master Item", "User PR", "Approval Workflow", "PO & Goods Receipt"])

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.header("📊 Supply Chain Dashboard")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Status Stok")
        st.write(pd.DataFrame([
            {"Item": row['Nama'], "Stok": st.session_state.inventory.get(row['SKU'], 0), "Min": row['Min_Stok']}
            for _, row in st.session_state.master_items.iterrows()
        ]))

# --- 2. MASTER ITEM ---
elif menu == "Master Item":
    st.header("📦 Master Data Barang")
    with st.expander("Tambah Item Baru"):
        with st.form("fm_item"):
            n_sku = st.text_input("SKU")
            n_nama = st.text_input("Nama Barang")
            n_satuan = st.selectbox("Satuan", ["Kg", "Liter", "Pcs", "Box"])
            n_min = st.number_input("Minimum Stok", min_value=1)
            if st.form_submit_button("Simpan"):
                new_row = {"SKU": n_sku, "Nama": n_nama, "Satuan": n_satuan, "Min_Stok": n_min}
                st.session_state.master_items = pd.concat([st.session_state.master_items, pd.DataFrame([new_row])], ignore_index=True)
                st.success("Item berhasil ditambahkan!")
    st.table(st.session_state.master_items)

# --- 3. USER PR ---
elif menu == "User PR":
    st.header("📝 Purchase Requisition (PR)")
    with st.form("fm_pr"):
        u_name = st.text_input("Nama Peminta (User)")
        u_item = st.selectbox("Pilih Barang", st.session_state.master_items['Nama'].tolist())
        u_sku = st.session_state.master_items[st.session_state.master_items['Nama'] == u_item]['SKU'].values[0]
        u_qty = st.number_input("Jumlah", min_value=1)
        u_price = st.number_input("Estimasi Harga Satuan (Rp)", min_value=0)
        if st.form_submit_button("Ajukan PR"):
            add_pr(u_name, u_sku, u_qty, u_price)
            st.info("PR telah diajukan dan menunggu approval.")
    
    st.subheader("Data PR Anda")
    if st.session_state.pr_data:
        st.table(pd.DataFrame(st.session_state.pr_data))

# --- 4. APPROVAL WORKFLOW ---
elif menu == "Approval Workflow":
    st.header("⚖️ Approval Portal")
    if not st.session_state.pr_data:
        st.write("Tidak ada PR yang perlu diproses.")
    else:
        for i, pr in enumerate(st.session_state.pr_data):
            if "Pending" in pr['Status']:
                with st.container():
                    st.write(f"**PR ID:** {pr['ID_PR']} | **User:** {pr['User']} | **Total:** Rp{pr['Total']:,}")
                    col_a, col_b = st.columns(2)
                    if col_a.button(f"Approve {pr['ID_PR']}", key=f"app_{i}"):
                        # Logic Workflow: Jika > 10jt butuh Direktur
                        if pr['Total'] > 10000000 and pr['Status'] == "Pending Manager":
                            st.session_state.pr_data[i]['Status'] = "Pending Direktur"
                        else:
                            st.session_state.pr_data[i]['Status'] = "Approved (PO Ready)"
                        st.rerun()
                    if col_b.button(f"Reject {pr['ID_PR']}", key=f"rej_{i}"):
                        st.session_state.pr_data[i]['Status'] = "Rejected"
                        st.rerun()
        st.divider()
        st.table(pd.DataFrame(st.session_state.pr_data))

# --- 5. PO & GOODS RECEIPT ---
elif menu == "PO & Goods Receipt":
    st.header("🚚 Purchase Order & GR")
    approved_prs = [p for p in st.session_state.pr_data if p['Status'] == "Approved (PO Ready)"]
    
    if not approved_prs:
        st.write("Belum ada PR yang disetujui untuk dijadikan PO.")
    else:
        selected_pr_id = st.selectbox("Pilih PR untuk Penerimaan Barang (GR)", [p['ID_PR'] for p in approved_prs])
        if st.button("Terima Barang (GR)"):
            for i, p in enumerate(st.session_state.pr_data):
                if p['ID_PR'] == selected_pr_id:
                    # Update Stok
                    sku = p['SKU']
                    st.session_state.inventory[sku] = st.session_state.inventory.get(sku, 0) + p['Qty']
                    st.session_state.pr_data[i]['Status'] = "Received (Selesai)"
                    st.success(f"Stok {sku} berhasil ditambah sebanyak {p['Qty']}!")
                    st.rerun()
