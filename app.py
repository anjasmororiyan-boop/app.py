import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="ERP SCM V2 - PR/PO/GR", layout="wide")

# --- INITIAL DATA ---
if 'master_items' not in st.session_state:
    st.session_state.master_items = pd.DataFrame([
        {"SKU": "BRG001", "Nama": "Tepung Terigu", "Satuan": "Kg", "Min_Stok": 50},
        {"SKU": "BRG002", "Nama": "Minyak Goreng", "Satuan": "Liter", "Min_Stok": 20}
    ])

if 'inventory' not in st.session_state:
    st.session_state.inventory = {"BRG001": 10, "BRG002": 5}

if 'pr_data' not in st.session_state:
    st.session_state.pr_data = []

# --- UI SIDEBAR ---
st.sidebar.title("ERP SCM System V2")
menu = st.sidebar.radio("Navigasi", ["Dashboard", "Master Item", "User PR", "Approval Workflow", "Purchase Order & GR"])

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.header("📊 Inventory Status")
    df_status = pd.DataFrame([
        {"Item": row['Nama'], "Stok Saat Ini": st.session_state.inventory.get(row['SKU'], 0), "Min": row['Min_Stok']}
        for _, row in st.session_state.master_items.iterrows()
    ])
    st.table(df_status)

# --- 2. MASTER ITEM (Sama seperti sebelumnya) ---
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
                st.rerun()
    st.table(st.session_state.master_items)

# --- 3. USER PR ---
elif menu == "User PR":
    st.header("📝 Purchase Requisition (PR)")
    with st.form("fm_pr"):
        u_item = st.selectbox("Pilih Barang", st.session_state.master_items['Nama'].tolist())
        u_sku = st.session_state.master_items[st.session_state.master_items['Nama'] == u_item]['SKU'].values[0]
        u_qty = st.number_input("Jumlah Pesanan", min_value=1)
        u_price = st.number_input("Estimasi Harga Satuan (Rp)", min_value=0)
        if st.form_submit_button("Ajukan PR"):
            st.session_state.pr_data.append({
                "ID_PR": f"PR-{datetime.now().strftime('%y%m%d%H%M')}",
                "SKU": u_sku, "Item": u_item, "Qty_PO": u_qty, "Qty_GR": 0,
                "Harga": u_price, "Total": u_qty * u_price, "Status": "Pending Manager"
            })
            st.success("PR Berhasil Diajukan")
    st.table(pd.DataFrame(st.session_state.pr_data) if st.session_state.pr_data else "Belum ada data")

# --- 4. APPROVAL WORKFLOW ---
elif menu == "Approval Workflow":
    st.header("⚖️ Approval Portal")
    for i, pr in enumerate(st.session_state.pr_data):
        if "Pending" in pr['Status']:
            st.info(f"**PR {pr['ID_PR']}** | Item: {pr['Item']} | Total: Rp{pr['Total']:,}")
            c1, c2 = st.columns(2)
            if c1.button(f"Approve {pr['ID_PR']}", key=f"app_{i}"):
                if pr['Total'] > 10000000 and pr['Status'] == "Pending Manager":
                    st.session_state.pr_data[i]['Status'] = "Pending Direktur"
                else:
                    st.session_state.pr_data[i]['Status'] = "Approved"
                st.rerun()
            if c2.button(f"Reject {pr['ID_PR']}", key=f"rej_{i}"):
                st.session_state.pr_data[i]['Status'] = "Rejected"
                st.rerun()

# --- 5. PO & GOODS RECEIPT (FORM TERLIHAT) ---
elif menu == "Purchase Order & GR":
    st.header("🚚 Purchase Order & Penerimaan Barang")
    approved_prs = [p for p in st.session_state.pr_data if p['Status'] == "Approved"]
    
    if not approved_prs:
        st.write("Tidak ada PO yang siap diterima.")
    else:
        # TAMPILKAN FORM PO
        selected_id = st.selectbox("Pilih Nomor PO", [p['ID_PR'] for p in approved_prs])
        po_detail = next(item for item in st.session_state.pr_data if item["ID_PR"] == selected_id)
        
        st.markdown("---")
        st.subheader(f"📄 FORM PURCHASE ORDER: {selected_id}")
        col_po1, col_po2 = st.columns(2)
        col_po1.write(f"**Item:** {po_detail['Item']} ({po_detail['SKU']})")
        col_po1.write(f"**Harga Satuan:** Rp{po_detail['Harga']:,}")
        col_po2.write(f"**Jumlah Dipesan (PO):** {po_detail['Qty_PO']}")
        col_po2.write(f"**Total Nilai:** Rp{po_detail['Total']:,}")
        
        st.markdown("---")
        st.subheader("📦 FORM PENERIMAAN BARANG (GR)")
        with st.form("gr_form"):
            actual_qty = st.number_input("Jumlah Fisik yang Diterima", min_value=0, value=int(po_detail['Qty_PO']))
            catatan = st.text_area("Catatan Penerimaan (misal: barang pecah 2, atau supplier kirim kurang)")
            
            if st.form_submit_button("Konfirmasi Penerimaan Barang (Post GR)"):
                for i, p in enumerate(st.session_state.pr_data):
                    if p['ID_PR'] == selected_id:
                        # Update Stok berdasarkan yang DITERIMA (GR), bukan yang DIPESAN (PO)
                        st.session_state.inventory[p['SKU']] = st.session_state.inventory.get(p['SKU'], 0) + actual_qty
                        st.session_state.pr_data[i]['Qty_GR'] = actual_qty
                        st.session_state.pr_data[i]['Status'] = "Closed (Received)"
                        st.session_state.pr_data[i]['Catatan'] = catatan
                        
                        if actual_qty < p['Qty_PO']:
                            st.warning(f"Terjadi selisih! Dipesan {p['Qty_PO']}, Diterima {actual_qty}.")
                        else:
                            st.success("Barang diterima sesuai pesanan.")
                        st.rerun()

    st.subheader("📜 Log Riwayat PO & GR")
    if st.session_state.pr_data:
        st.table(pd.DataFrame(st.session_state.pr_data))
