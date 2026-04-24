mport streamlit as st
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="ERP V15 - Professional Procurement", layout="wide")

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

# State tambahan untuk Vendor, Warehouse, dan Multi-item
default_states = {
    'master_units': ["Kg", "Liter", "Pcs", "Gram", "Box"],
    'expense_categories': ["Gaji", "Listrik/Air", "Sewa", "Marketing"],
    'master_vendors': ["PT. Sumber Pangan", "UD. Makmur Jaya", "Toko Bahan Kue ABC"],
    'master_warehouses': ["Gudang Utama", "Central Kitchen", "Gudang Bahan Baku"],
    'master_bahan_baku': pd.DataFrame([
        {"SKU": "RAW001", "Nama": "Tepung Terigu", "Satuan": "Kg", "Stok": 50.0, "Min_Stok": 10.0}
    ]),
    'master_penjualan': pd.DataFrame([
        {"SKU": "SALE001", "Nama": "Roti Tawar", "Satuan": "Pcs", "Harga_Jual": 15000.0}
    ]),
    'pr_data': [], # Database PR pusat
    'pr_items_temp': [], # Daftar item sementara saat input PR
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
                st.session_state.username = u # Simpan untuk Requestor otomatis
                st.rerun()
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
    st.header("📊 Dashboard")
    st.subheader("📦 Stok Bahan Baku Saat Ini")
    st.table(st.session_state.master_bahan_baku)

# --- 2. MASTER DATA MANAGEMENT ---
elif menu == "Master Data Management":
    st.header("⚙️ Pusat Kendali Master Data")
    t_raw, t_sale, t_cfg, t_vendor, t_wh = st.tabs(["🌾 Bahan Baku", "💰 Penjualan", "🛠️ Unit & Expense", "🏢 Vendor", "🏠 Warehouse"])
    
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

    with t_vendor:
        st.subheader("Master Vendor")
        with st.form("fm_vendor"):
            v_new = st.text_input("Nama Vendor Baru")
            if st.form_submit_button("Tambah Vendor"):
                if v_new and v_new not in st.session_state.master_vendors:
                    st.session_state.master_vendors.append(v_new)
                    st.rerun()
        st.write(st.session_state.master_vendors)

    with t_wh:
        st.subheader("Master Warehouse / Gudang")
        with st.form("fm_wh"):
            wh_new = st.text_input("Nama Gudang Baru")
            if st.form_submit_button("Tambah Gudang"):
                if wh_new and wh_new not in st.session_state.master_warehouses:
                    st.session_state.master_warehouses.append(wh_new)
                    st.rerun()
        st.write(st.session_state.master_warehouses)

# --- 3. PROCUREMENT (MULTI-ITEM & INTEGRATED) ---
elif menu == "Procurement (Bahan Baku)":
    st.header("🛒 Create Purchase Requisition (PR)")
    
    # 3.1 HEADER SECTION (Formulir Atas)
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        pr_date = col1.date_input("Date Transaksi", datetime.now(), disabled=True)
        pr_vendor = col2.selectbox("Vendor Name", st.session_state.master_vendors)
        pr_delivery = col3.date_input("Estimated Delivery")

        col4, col5, col6 = st.columns(3)
        pr_requestor = col4.text_input("Requestor", value=st.session_state.get('username', 'Admin'), disabled=True)
        pr_wh = col5.selectbox("Warehouse", st.session_state.master_warehouses)
        pr_memo = col6.text_area("Memo (Catatan)", placeholder="Tulis catatan tambahan di sini...")

    st.divider()

    # 3.2 ITEM LIST SECTION (Multi-Item Add Row)
    st.subheader("📦 Item List (Multi-Item)")
    
    # Pemicu Update Satuan: Selectbox di luar form agar re-run otomatis
    p_item_name = st.selectbox("Pilih Bahan Baku untuk ditambahkan", 
                                st.session_state.master_bahan_baku['Nama'].tolist(), 
                                key="pr_item_select")
    
    # Cari Info Master & Harga Terakhir
    it_info = st.session_state.master_bahan_baku[st.session_state.master_bahan_baku['Nama'] == p_item_name].iloc[0]
    
    # Cari harga terakhir dari histori PR yang sudah Closed
    history = [p for p in st.session_state.pr_data if p.get('Item') == p_item_name]
    last_price = float(history[-1]['Harga']) if history else 0.0

    with st.form("add_row_form", clear_on_submit=True):
        c_sku, c_unit, c_qty, c_prc = st.columns([1,1,1,2])
        c_sku.text_input("Kode Item", value=it_info['SKU'], disabled=True)
        c_unit.text_input("Satuan", value=it_info['Satuan'], disabled=True)
        
        input_qty = c_qty.number_input("Qty Dibutuhkan", min_value=0.0, format="%.5f")
        input_prc = c_prc.number_input("Estimasi Harga Satuan (Rp)", value=last_price, format="%.5f")
        
        if st.form_submit_button("➕ Add Row"):
            if input_qty > 0:
                st.session_state.pr_items_temp.append({
                    "Kode Item": it_info['SKU'],
                    "Nama Item": p_item_name,
                    "Unit Satuan": it_info['Satuan'],
                    "Qty": input_qty,
                    "Estimasi Harga": input_prc,
                    "Total": input_qty * input_prc
                })
                st.rerun()
            else:
                st.warning("Qty harus lebih dari 0")

    # TAMPILKAN TABEL SEMENTARA
    if st.session_state.pr_items_temp:
        st.markdown("### Daftar Item Terpilih")
        df_temp = pd.DataFrame(st.session_state.pr_items_temp)
        st.table(df_temp)
        
        grand_total = df_temp['Total'].sum()
        st.markdown(f"## Grand Total: **Rp {smart_format(grand_total)}**")
        
        col_act1, col_act2 = st.columns([1, 4])
        if col_act1.button("🚀 SUBMIT PR", type="primary"):
            pr_id = f"PR-{datetime.now().strftime('%y%m%d%H%M%S')}"
            
            # Simpan semua baris ke Database PR
            for row in st.session_state.pr_items_temp:
                st.session_state.pr_data.append({
                    "PR_ID": pr_id,
                    "Tanggal": pr_date.strftime("%Y-%m-%d"),
                    "Vendor": pr_vendor,
                    "Delivery": pr_delivery.strftime("%Y-%m-%d"),
                    "Requestor": pr_requestor,
                    "Warehouse": pr_wh,
                    "Memo": pr_memo,
                    "Kode": row['Kode Item'],
                    "Item": row['Nama Item'],
                    "Satuan": row['Unit Satuan'],
                    "Qty_Pesan": row['Qty'],
                    "Harga": row['Estimasi Harga'],
                    "Total": row['Total'],
                    "Status": "Pending Approval"
                })
            
            st.session_state.pr_items_temp = [] # Kosongkan temp
            st.success(f"Berhasil membuat dokumen {pr_id}")
            st.rerun()
            
        if col_act2.button("🗑️ Reset Daftar"):
            st.session_state.pr_items_temp = []
            st.rerun()

    # --- TAB 2: APPROVAL & PRINT PO ---
    with tab_po:
        st.subheader("Approval & Dokumen Purchase Order")
        
        pending_list = [p for p in st.session_state.pr_data if p['Status'] == "Pending Approval"]
        
        if not pending_list:
            st.info("Tidak ada dokumen yang menunggu persetujuan.")
        
        for i, pr in enumerate(pending_list):
            with st.expander(f"Review {pr['ID']} - {pr['Item']}"):
                st.write(f"Tanggal: {pr['Tanggal']}")
                st.write(f"Estimasi Total: Rp {smart_format(pr['Total'])}")
                
                c1, c2 = st.columns(2)
                if c1.button("✅ Approve (Terbitkan PO)", key=f"app_v14_{i}"):
                    # Cari index asli di session state dan ubah status
                    for idx, item in enumerate(st.session_state.pr_data):
                        if item['ID'] == pr['ID']:
                            st.session_state.pr_data[idx]['Status'] = "Approved"
                    st.rerun()
                
                if c2.button("❌ Reject", key=f"rej_v14_{i}"):
                    for idx, item in enumerate(st.session_state.pr_data):
                        if item['ID'] == pr['ID']:
                            st.session_state.pr_data[idx]['Status'] = "Rejected"
                    st.rerun()

        # TAMPILAN UNTUK PRINT (PO YANG SUDAH APPROVED)
        st.divider()
        st.subheader("🖨️ Dokumen PO Siap Cetak")
        ready_po = [p for p in st.session_state.pr_data if p['Status'] == "Approved"]
        
        if ready_po:
            selected_po_id = st.selectbox("Pilih PO untuk Dicetak", [p['ID'] for p in ready_po])
            po_print = next(item for item in ready_po if item["ID"] == selected_id)

            # --- DOKUMEN PO AREA (PRINTABLE) ---
            st.markdown(f"""
            <div style="border: 2px solid black; padding: 20px; border-radius: 10px; background-color: white; color: black;">
                <h2 style="text-align: center;">PURCHASE ORDER</h2>
                <hr>
                <table style="width: 100%;">
                    <tr><td><strong>No. PO:</strong> {po_print['ID']}</td><td style="text-align: right;"><strong>Tanggal:</strong> {po_print['Tanggal']}</td></tr>
                </table>
                <br>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background-color: #f2f2f2;">
                        <th style="border: 1px solid black; padding: 8px;">Deskripsi Barang</th>
                        <th style="border: 1px solid black; padding: 8px;">Qty</th>
                        <th style="border: 1px solid black; padding: 8px;">Satuan</th>
                        <th style="border: 1px solid black; padding: 8px;">Harga Satuan</th>
                        <th style="border: 1px solid black; padding: 8px;">Total</th>
                    </tr>
                    <tr>
                        <td style="border: 1px solid black; padding: 8px;">{po_print['Item']}</td>
                        <td style="border: 1px solid black; padding: 8px; text-align: center;">{smart_format(po_print['Qty_Pesan'])}</td>
                        <td style="border: 1px solid black; padding: 8px; text-align: center;">{po_print['Satuan']}</td>
                        <td style="border: 1px solid black; padding: 8px; text-align: right;">Rp {smart_format(po_print['Harga'])}</td>
                        <td style="border: 1px solid black; padding: 8px; text-align: right;">Rp {smart_format(po_print['Total'])}</td>
                    </tr>
                </table>
                <br>
                <p><strong>Grand Total: Rp {smart_format(po_print['Total'])}</strong></p>
                <br><br>
                <table style="width: 100%; text-align: center;">
                    <tr>
                        <td>Dibuat Oleh,<br><br><br>( Staff Procurement )</td>
                        <td>Disetujui Oleh,<br><br><br>( Direktur Operasional )</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            st.caption("Gunakan Ctrl+P atau fitur browser 'Print to PDF' untuk menyimpan dokumen di atas.")
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
