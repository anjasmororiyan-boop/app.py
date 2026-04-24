import streamlit as st
import pandas as pd
from datetime import datetime

# --- INITIALIZING ADDITIONAL SESSION STATES ---
if 'master_vendors' not in st.session_state:
    st.session_state.master_vendors = ["PT. Sumber Pangan", "UD. Makmur Jaya"]
if 'master_warehouses' not in st.session_state:
    st.session_state.master_warehouses = ["Gudang Utama", "Hub Kitchen Jakarta"]
if 'pr_items_temp' not in st.session_state:
    st.session_state.pr_items_temp = []

# --- 2. MASTER DATA MANAGEMENT (TAMBAHAN VENDOR & WAREHOUSE) ---
elif menu == "Master Data Management":
    st.header("⚙️ Pusat Kendali Master Data")
    t_raw, t_sale, t_cfg, t_vendor, t_wh = st.tabs(["🌾 Bahan Baku", "💰 Penjualan", "🛠️ Unit & Expense", "🏢 Vendor", "🏠 Warehouse"])
    
    # ... (Tab t_raw, t_sale, t_cfg tetap seperti sebelumnya)

    with t_vendor:
        st.subheader("Master Vendor")
        with st.form("fm_vendor"):
            v_name = st.text_input("Nama Vendor Baru")
            if st.form_submit_button("Simpan Vendor"):
                if v_name and v_name not in st.session_state.master_vendors:
                    st.session_state.master_vendors.append(v_name)
                    st.rerun()
        st.write(st.session_state.master_vendors)

    with t_wh:
        st.subheader("Master Warehouse")
        with st.form("fm_wh"):
            wh_name = st.text_input("Nama Gudang Baru")
            if st.form_submit_button("Simpan Gudang"):
                if wh_name and wh_name not in st.session_state.master_warehouses:
                    st.session_state.master_warehouses.append(wh_name)
                    st.rerun()
        st.write(st.session_state.master_warehouses)

# --- 3. PROCUREMENT (MULTI-ITEM & INTEGRATED) ---
elif menu == "Procurement (Bahan Baku)":
    st.header("🛒 Purchase Requisition (Multi-Item)")
    
    # --- HEADER SECTION ---
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        pr_date = col1.date_input("Tanggal Transaksi", datetime.now(), disabled=True)
        pr_vendor = col2.selectbox("Vendor Name", st.session_state.master_vendors)
        pr_delivery = col3.date_input("Estimated Delivery")

        col4, col5, col6 = st.columns(3)
        pr_requestor = col4.text_input("Requestor", value="Admin (System)", disabled=True) # Sesuaikan dengan login user
        pr_wh = col5.selectbox("Warehouse", st.session_state.master_warehouses)
        pr_memo = col6.text_area("Memo / Catatan", placeholder="Keperluan produksi bakery...")

    st.divider()

    # --- MULTI-ITEM SECTION ---
    st.subheader("Item List")
    
    # Form untuk tambah item ke daftar sementara
    with st.expander("➕ Tambah Item Baru ke Baris", expanded=True):
        with st.form("add_item_row"):
            c_it, c_qty, c_prc = st.columns([3,1,2])
            selected_it = c_it.selectbox("Pilih Item", st.session_state.master_bahan_baku['Nama'].tolist())
            
            # Cari info item & harga terakhir
            it_info = st.session_state.master_bahan_baku[st.session_state.master_bahan_baku['Nama'] == selected_it].iloc[0]
            history = [p for p in st.session_state.pr_data if p.get('Item') == selected_it]
            last_price = float(history[-1]['Harga']) if history else 0.0
            
            q_val = c_qty.number_input(f"Qty ({it_info['Satuan']})", min_value=0.1)
            p_val = c_prc.number_input("Est. Harga Satuan", value=last_price)
            
            if st.form_submit_button("Add Row (Tambahkan Ke Daftar)"):
                st.session_state.pr_items_temp.append({
                    "Kode": it_info['SKU'],
                    "Item": selected_it,
                    "Satuan": it_info['Satuan'],
                    "Qty": q_val,
                    "Harga": p_val,
                    "Total": q_val * p_val
                })
                st.rerun()

    # Tampilkan Tabel Baris yang Sedang Dibuat
    if st.session_state.pr_items_temp:
        df_temp = pd.DataFrame(st.session_state.pr_items_temp)
        st.table(df_temp)
        
        grand_total = df_temp['Total'].sum()
        st.markdown(f"### Grand Total: **Rp {smart_format(grand_total)}**")

        if st.button("🚀 Submit Purchase Requisition"):
            pr_id = f"PR-{datetime.now().strftime('%y%m%d%H%M%S')}"
            # Simpan Header & Detail ke database PR
            for item in st.session_state.pr_items_temp:
                st.session_state.pr_data.append({
                    "PR_ID": pr_id,
                    "Tanggal": pr_date.strftime("%Y-%m-%d"),
                    "Vendor": pr_vendor,
                    "Delivery": pr_delivery.strftime("%Y-%m-%d"),
                    "Requestor": pr_requestor,
                    "Warehouse": pr_wh,
                    "Memo": pr_memo,
                    "Kode": item['Kode'],
                    "Item": item['Item'],
                    "Satuan": item['Satuan'],
                    "Qty_Pesan": item['Qty'],
                    "Harga": item['Harga'],
                    "Total": item['Total'],
                    "Status": "Pending Approval"
                })
            st.session_state.pr_items_temp = [] # Reset temp items
            st.success(f"PR {pr_id} Berhasil Diajukan!")
            st.rerun()
        
        if st.button("🗑️ Reset Form"):
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
