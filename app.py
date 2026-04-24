import streamlit as st
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
    'master_vendors': pd.DataFrame([
        {"Nama": "PT. Sumber Pangan", "Status": "Active"},
        {"Nama": "UD. Makmur Jaya", "Status": "Active"}
    ]),
    'master_warehouses': pd.DataFrame([
        {"Nama": "Gudang Utama", "Status": "Active"},
        {"Nama": "Central Kitchen", "Status": "Active"},
        {"Nama": "Gudang Bahan Baku", "Status": "Active"},
    ]),
    'master_bahan_baku': pd.DataFrame([
        {"SKU": "RAW001", "Nama": "Tepung Terigu", "Satuan": "Kg", "Stok": 50.0, "Min_Stok": 10.0, "Status": "Active"}
    ]),
    'master_penjualan': pd.DataFrame([
        {"SKU": "SALE001", "Nama": "Roti Tawar", "Satuan": "Pcs", "Harga_Jual": 15000.0, "Status": "Active"}
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
    
    # 1. Definisi Tabs
    t_raw, t_vendor, t_wh, t_cfg = st.tabs(["🌾 Bahan Baku", "🏢 Vendor", "🏠 Warehouse", "🛠️ Unit & Expense"])
    
    with t_raw:
        st.subheader("Manajemen Bahan Baku")

        # Gunakan expander untuk form agar rapi
        with st.expander("➕ Tambah / Edit Bahan Baku"):
            with st.form("fm_raw_edit"):
                c1, c2 = st.columns(2)
                r_sku = c1.text_input("SKU (Gunakan SKU lama untuk Edit)")
                r_nama = c1.text_input("Nama Bahan")
                r_satuan = c2.selectbox("Satuan", st.session_state.master_units)
                r_min = c2.number_input("Minimal Stok", format="%.5f")
                # FITUR INAKTIF: Tambahkan field status
                r_status = c2.selectbox("Status", ["Active", "Inactive"]) 
                
                if st.form_submit_button("Simpan Data"):
                    # Logika UPSERT (Update or Insert)
                    mask = st.session_state.master_bahan_baku['SKU'] == r_sku
                    if mask.any():
                        # UPDATE jika SKU ditemukan
                        st.session_state.master_bahan_baku.loc[mask, ['Nama', 'Satuan', 'Min_Stok', 'Status']] = [r_nama, r_satuan, r_min, r_status]
                        st.success(f"Update Berhasil: {r_sku}")
                    else:
                        # INSERT jika SKU baru
                        new_data = {"SKU": r_sku, "Nama": r_nama, "Satuan": r_satuan, "Stok": 0.0, "Min_Stok": r_min, "Status": r_status}
                        st.session_state.master_bahan_baku = pd.concat([st.session_state.master_bahan_baku, pd.DataFrame([new_data])], ignore_index=True)
                        st.success("Item Baru Berhasil Ditambahkan")
                    st.rerun()
        
        # Menampilkan tabel master
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

# --- 3. PROCUREMENT (PR MULTI-ITEM) ---
elif menu == "Procurement (Bahan Baku)":
    st.header("🛒 Purchase Requisition (PR)")
    
    # DEFINISIKAN TABS DI SINI (Ini kunci perbaikan error Anda)
    tab_pr, tab_po = st.tabs(["📝 Buat PR Baru", "📄 Approval & Monitoring"])

    # --- TAB 1: BUAT PR BARU (MULTI-ITEM) ---
    with tab_pr:
        # HEADER SECTION
        with st.container(border=True):
            col1, col2, col3 = st.columns(3)
            pr_date = col1.date_input("Date Transaksi", datetime.now(), disabled=True)
            # Pastikan master_vendors sudah ada di session_state
            pr_vendor = col2.selectbox("Vendor Name", st.session_state.get('master_vendors', ["Umum"]))
            pr_delivery = col3.date_input("Estimated Delivery")

            col4, col5, col6 = st.columns(3)
            # Otomatis mengambil user yang login
            pr_requestor = col4.text_input("Requestor", value=st.session_state.get('username', 'Admin'), disabled=True)
            pr_wh = col5.selectbox("Warehouse", st.session_state.get('master_warehouses', ["Gudang Utama"]))
            pr_memo = col6.text_area("Memo (Catatan)", placeholder="Catatan tambahan...")

        st.divider()

        # ITEM LIST SECTION (ADD ROW LOGIC)
        st.subheader("📦 Item List")
        
        # Selectbox di luar form agar UI (Satuan & Kode) update otomatis saat item diganti
        active_items = st.session_state.master_bahan_baku[st.session_state.master_bahan_baku['Status'] == "Active"]
if active_items.empty:
        st.warning("Tidak ada item aktif di Master Data.")
else:
        p_item = st.selectbox("Pilih Bahan Baku", active_items['Nama'].tolist())
        it_info = active_items[active_items['Nama'] == p_item].iloc[0]
    
    # Ambil info dari active_items
        it_info = active_items[active_items['Nama'] == p_item_name].iloc[0]
        
        # Cari harga terakhir dari histori PR
        history = [p for p in st.session_state.pr_data if p.get('Item') == p_item_name]
        last_price = float(history[-1]['Harga']) if history else 0.0

        # Form untuk Add Row
        with st.form("add_row_form", clear_on_submit=True):
            c_sku, c_unit, c_qty, c_prc = st.columns([1.5, 1, 1.5, 2])
            c_sku.text_input("Kode Item", value=it_info['SKU'], disabled=True)
            c_unit.text_input("Unit Satuan", value=it_info['Satuan'], disabled=True)
            
            input_qty = c_qty.number_input(f"Qty ({it_info['Satuan']})", min_value=0.0, format="%.5f")
            input_prc = c_prc.number_input("Estimasi Harga", value=last_price, format="%.5f")
            
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
                    st.error("Qty harus lebih besar dari 0")

        # Tampilkan Tabel Sementara (Daftar Item Terpilih)
        if st.session_state.pr_items_temp:
            st.write("### Daftar Item Terpilih")
            df_temp = pd.DataFrame(st.session_state.pr_items_temp)
            st.table(df_temp) # Menampilkan tabel sesuai format yang Anda inginkan
            
            grand_total = df_temp['Total'].sum()
            st.markdown(f"## Grand Total: **Rp {smart_format(grand_total)}**")
            
            col_sub1, col_sub2 = st.columns([1, 5])
            if col_sub1.button("🚀 SUBMIT PR", type="primary"):
                pr_id = f"PR-{datetime.now().strftime('%y%m%d%H%M%S')}"
                # Simpan semua baris ke database pusat
                for item in st.session_state.pr_items_temp:
                    st.session_state.pr_data.append({
                        "PR_ID": pr_id,
                        "Tanggal": pr_date.strftime("%Y-%m-%d"),
                        "Vendor": pr_vendor,
                        "Delivery": pr_delivery.strftime("%Y-%m-%d"),
                        "Requestor": pr_requestor,
                        "Warehouse": pr_wh,
                        "Memo": pr_memo,
                        "Kode": item['Kode Item'],
                        "Item": item['Nama Item'],
                        "Satuan": item['Unit Satuan'],
                        "Qty": item['Qty'],
                        "Harga": item['Estimasi Harga'],
                        "Total": item['Total'],
                        "Status": "Pending Approval"
                    })
                st.session_state.pr_items_temp = [] # Kosongkan daftar sementara
                st.success(f"PR {pr_id} berhasil dikirim!")
                st.rerun()
            
            if col_sub2.button("🗑️ Reset Daftar"):
                st.session_state.pr_items_temp = []
                st.rerun()

    # --- TAB 2: APPROVAL & MONITORING ---
        with tab_po:
            st.subheader("Monitoring Approval")
        if not st.session_state.pr_data:
            st.info("Belum ada pengajuan PR.")
        else:
            st.dataframe(pd.DataFrame(st.session_state.pr_data))
            
            # Logika Approval per Nomor PR
            unique_prs = df_all[df_all['Status'] == "Pending Approval"]['PR_ID'].unique()
            for pid in unique_prs:
                with st.expander(f"Review Pengajuan: {pid}"):
                    items_in_pr = df_all[df_all['PR_ID'] == pid]
                    st.table(items_in_pr[['Kode', 'Item', 'Qty', 'Satuan', 'Total']])
                    st.write(f"**Total PR: Rp {smart_format(items_in_pr['Total'].sum())}**")
                    
                    if st.button(f"Approve {pid}", key=f"app_{pid}"):
                        for idx, pr in enumerate(st.session_state.pr_data):
                            if pr['PR_ID'] == pid:
                                st.session_state.pr_data[idx]['Status'] = "Approved"
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
