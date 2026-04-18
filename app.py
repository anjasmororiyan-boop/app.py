import streamlit as st
import pandas as pd
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="ERP V12 - Full Master Control", layout="wide")

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

default_states = {
    'master_units': ["Kg", "Liter", "Pcs", "Gram", "Box"],
    'expense_categories': ["Gaji", "Listrik/Air", "Sewa", "Marketing", "Maintenance"],
    'master_items': pd.DataFrame([
        {"SKU": "BRG001", "Nama": "Espresso Coffee", "Satuan": "Kg", "Harga_Jual": 25000.0, "Stok": 100.0, "Min_Stok": 10.0}
    ]),
    'pr_data': [],
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
    st.title("🔐 Login ERP & Finance System")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u == "admin" and p == "admin123":
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- SIDEBAR ---
menu = st.sidebar.radio("Navigasi Utama", [
    "Dashboard", 
    "Master Data Management", 
    "Procurement (PR/GR)", 
    "Pembayaran Hutang",
    "POS (Kasir)", 
    "Riwayat Transaksi",
    "Laporan Keuangan"
])

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.header("📊 Dashboard")
    rev = sum(t['Net_Total'] for t in st.session_state.pos_transactions)
    exp = sum(e['Nominal'] for e in st.session_state.expenses_data)
    st.metric("Estimasi Profit", f"Rp {smart_format(rev - exp)}")
    st.subheader("📦 Stok Barang")
    st.table(st.session_state.master_items)

# --- 2. MASTER DATA MANAGEMENT (FIXED & COMPLETE) ---
elif menu == "Master Data Management":
    st.header("⚙️ Pusat Kendali Master Data")
    
    t_item, t_unit, t_exp = st.tabs(["📦 Master Barang", "📏 Satuan (Units)", "💸 Kategori Biaya"])
    
    with t_item:
        st.subheader("Pengaturan Produk & Harga")
        with st.expander("➕ Tambah / Edit Item"):
            with st.form("fm_item"):
                e_sku = st.text_input("SKU")
                e_nama = st.text_input("Nama Barang")
                e_satuan = st.selectbox("Satuan Default", st.session_state.master_units)
                e_harga = st.number_input("Harga Jual", format="%.5f")
                e_min = st.number_input("Min Stok", format="%.5f")
                if st.form_submit_button("Simpan Data"):
                    mask = st.session_state.master_items['SKU'] == e_sku
                    if mask.any():
                        st.session_state.master_items.loc[mask, ['Nama', 'Satuan', 'Harga_Jual', 'Min_Stok']] = [e_nama, e_satuan, e_harga, e_min]
                    else:
                        new_row = {"SKU": e_sku, "Nama": e_nama, "Satuan": e_satuan, "Harga_Jual": e_harga, "Stok": 0.0, "Min_Stok": e_min}
                        st.session_state.master_items = pd.concat([st.session_state.master_items, pd.DataFrame([new_row])], ignore_index=True)
                    st.rerun()
        
        # Tabel View dengan Fitur Hapus
        for i, row in st.session_state.master_items.iterrows():
            c1, c2 = st.columns([5, 1])
            c1.write(f"**{row['SKU']}** | {row['Nama']} ({row['Satuan']}) | Harga: {smart_format(row['Harga_Jual'])}")
            if c2.button("🗑️", key=f"del_it_{i}"):
                st.session_state.master_items = st.session_state.master_items.drop(i).reset_index(drop=True); st.rerun()

    with t_unit:
        st.subheader("Pengaturan Satuan Unit")
        with st.form("fm_unit"):
            new_u = st.text_input("Nama Satuan Baru (misal: Gram, Dus, Pack)")
            if st.form_submit_button("Tambah Satuan"):
                if new_u and new_u not in st.session_state.master_units:
                    st.session_state.master_units.append(new_u); st.rerun()
        
        st.write("**Daftar Satuan Aktif:**")
        for idx, u in enumerate(st.session_state.master_units):
            col_ua, col_ub = st.columns([4, 1])
            col_ua.info(u)
            if col_ub.button("Hapus", key=f"del_u_{idx}"):
                st.session_state.master_units.pop(idx); st.rerun()

    with t_exp:
        st.subheader("Pengaturan Kategori Biaya (OPEX)")
        with st.form("fm_exp_cat"):
            new_cat = st.text_input("Nama Kategori Biaya Baru")
            if st.form_submit_button("Tambah Kategori"):
                if new_cat and new_cat not in st.session_state.expense_categories:
                    st.session_state.expense_categories.append(new_cat); st.rerun()
        
        st.write("**Daftar Kategori Biaya Aktif:**")
        for idx, ex in enumerate(st.session_state.expense_categories):
            col_ea, col_eb = st.columns([4, 1])
            col_ea.warning(ex)
            if col_eb.button("Hapus", key=f"del_ex_{idx}"):
                st.session_state.expense_categories.pop(idx); st.rerun()

# --- 3. PROCUREMENT (PR/GR) ---
elif menu == "Procurement (PR/GR)":
    st.header("🛒 Procurement Control")
    with st.expander("📝 Buat PR Baru"):
        with st.form("pr_form"):
            p_item = st.selectbox("Item", st.session_state.master_items['Nama'].tolist())
            it_info = st.session_state.master_items[st.session_state.master_items['Nama'] == p_item].iloc[0]
            st.info(f"Satuan: {it_info['Satuan']}") # Field Satuan Otomatis
            p_qty = st.number_input("Qty Pesanan", format="%.5f")
            p_prc = st.number_input("Harga Satuan Beli", format="%.5f")
            if st.form_submit_button("Submit"):
                st.session_state.pr_data.append({
                    "ID": f"PR-{datetime.now().strftime('%y%m%d%H%M')}", "Item": p_item, "Satuan": it_info['Satuan'],
                    "Qty_Pesanan": p_qty, "Qty_Terima": 0.0, "Harga": p_prc, "Status": "Pending", "Paid": False
                })
                st.rerun()
    
    # Logic GR tetap sama seperti V11 (Input Qty Fisik)
    for i, pr in enumerate(st.session_state.pr_data):
        if pr['Status'] != "Closed":
            st.write(f"**{pr['ID']}** - {pr['Item']}")
            if pr['Status'] == "Pending":
                if st.button("Approve", key=f"ap_{i}"): st.session_state.pr_data[i]['Status'] = "Approved"; st.rerun()
            elif pr['Status'] == "Approved":
                q_f = st.number_input("Qty Terima Fisik", key=f"qf_{i}", format="%.5f")
                if st.button("Konfirmasi GR", key=f"gr_{i}"):
                    sku = st.session_state.master_items[st.session_state.master_items['Nama'] == pr['Item']]['SKU'].values[0]
                    idx = st.session_state.master_items[st.session_state.master_items['SKU'] == sku].index[0]
                    st.session_state.master_items.at[idx, 'Stok'] += q_f
                    st.session_state.pr_data[i]['Qty_Terima'] = q_f
                    st.session_state.pr_data[i]['Status'] = "Closed"
                    st.rerun()

# --- 4. PEMBAYARAN HUTANG (NEW) ---
elif menu == "Pembayaran Hutang":
    st.header("💸 Pembayaran Pembelian (Account Payable)")
    unpaid_pr = [p for p in st.session_state.pr_data if p['Status'] == "Closed" and p['Paid'] == False]
    if unpaid_pr:
        for i, pr in enumerate(unpaid_pr):
            total_tagihan = pr['Qty_Terima'] * pr['Harga']
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"**{pr['ID']}** | {pr['Item']} | Tagihan: Rp {smart_format(total_tagihan)}")
            if c3.button("Bayar Sekarang", key=f"pay_{i}"):
                # Cari index aslinya di pr_data
                for idx, real_pr in enumerate(st.session_state.pr_data):
                    if real_pr['ID'] == pr['ID']:
                        st.session_state.pr_data[idx]['Paid'] = True
                        st.session_state.payments_data.append({
                            "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Ref": pr['ID'], "Item": pr['Item'], "Total_Bayar": total_tagihan
                        })
                        st.success(f"Pembayaran {pr['ID']} Berhasil.")
                        st.rerun()
    else:
        st.info("Semua tagihan pembelian sudah lunas.")

# --- 5. POS (KASIR) ---
elif menu == "POS (Kasir)":
    st.header("🛒 Point of Sales")
    with st.form("pos_f"):
        s_item = st.selectbox("Item", st.session_state.master_items['Nama'].tolist())
        s_qty = st.number_input("Qty", format="%.5f")
        if st.form_submit_button("Catat Penjualan"):
            price = st.session_state.master_items[st.session_state.master_items['Nama'] == s_item]['Harga_Jual'].values[0]
            st.session_state.pos_transactions.append({
                "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"), "Item": s_item, "Qty": s_qty, "Net_Total": s_qty * price
            })
            idx = st.session_state.master_items[st.session_state.master_items['Nama'] == s_item].index[0]
            st.session_state.master_items.at[idx, 'Stok'] -= s_qty
            st.rerun()

# --- 6. RIWAYAT TRANSAKSI (UPDATED) ---
elif menu == "Riwayat Transaksi":
    st.header("📜 Log Semua Aktivitas")
    t1, t2, t3, t4 = st.tabs(["GR (Stok Masuk)", "POS (Penjualan)", "OPEX (Biaya Umum)", "Pembayaran Supplier"])
    with t1:
        st.table(pd.DataFrame([p for p in st.session_state.pr_data if p['Status'] == "Closed"]))
    with t2:
        st.table(pd.DataFrame(st.session_state.pos_transactions))
    with t3:
        # LOG PENGELUARAN DINAMIS
        st.table(pd.DataFrame(st.session_state.expenses_data))
    with t4:
        st.table(pd.DataFrame(st.session_state.payments_data))

# --- 7. LAPORAN KEUANGAN (NEW: PNL, BALANCE, CASH FLOW) ---
elif menu == "Laporan Keuangan":
    st.header("📑 Financial Reports")
    rep1, rep2, rep3 = st.tabs(["Profit & Loss", "Balance Sheet", "Cash Flow"])
    
    # Perhitungan Dasar
    revenue = sum(t['Net_Total'] for t in st.session_state.pos_transactions)
    opex = sum(e['Nominal'] for e in st.session_state.expenses_data)
    purchases_paid = sum(p['Total_Bayar'] for p in st.session_state.payments_data)
    
    with rep1:
        st.subheader("Laporan Laba Rugi")
        st.write(f"Penjualan Bersih: Rp {smart_format(revenue)}")
        st.write(f"Biaya Operasional: (Rp {smart_format(opex)})")
        st.divider()
        st.subheader(f"Laba Bersih: Rp {smart_format(revenue - opex)}")

    with rep2:
        st.subheader("Neraca (Balance Sheet)")
        inventory_val = sum(row['Stok'] * 10000 for _, row in st.session_state.master_items.iterrows()) # Estimasi nilai stok
        st.write(f"**ASET**")
        st.write(f"Kas (Estimasi): Rp {smart_format(revenue - opex - purchases_paid)}")
        st.write(f"Persediaan Barang: Rp {smart_format(inventory_val)}")
        st.divider()
        unpaid_val = sum(p['Qty_Terima'] * p['Harga'] for p in st.session_state.pr_data if p['Status'] == "Closed" and p['Paid'] == False)
        st.write(f"**KEWAJIBAN (Hutang)**")
        st.write(f"Hutang Dagang (Belum Bayar): Rp {smart_format(unpaid_val)}")

    with rep3:
        st.subheader("Arus Kas (Cash Flow)")
        st.write(f"Uang Masuk (Sales): Rp {smart_format(revenue)}")
        st.write(f"Uang Keluar (Expenses): (Rp {smart_format(opex)})")
        st.write(f"Uang Keluar (Pembelian Barang): (Rp {smart_format(purchases_paid)})")
        st.divider()
        st.subheader(f"Net Cash Change: Rp {smart_format(revenue - opex - purchases_paid)}")

    # Form Input Biaya
    with st.expander("➕ Input Biaya Baru (OPEX)"):
        with st.form("exp_f"):
            c = st.selectbox("Kategori", st.session_state.expense_categories)
            n = st.number_input("Nominal", format="%.5f")
            if st.form_submit_button("Catat Biaya"):
                st.session_state.expenses_data.append({"Tanggal": datetime.now().strftime("%Y-%m-%d"), "Kategori": c, "Nominal": n})
                st.rerun()

