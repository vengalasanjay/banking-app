import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { accountAPI, transferAPI } from '../api';
import './Dashboard.css';

function fmt(n) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(n);
}

function Modal({ title, onClose, children }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const [accounts, setAccounts]       = useState([]);
  const [selected, setSelected]       = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [modal, setModal]             = useState(null); // 'deposit'|'withdraw'|'transfer'|'newaccount'
  const [amount, setAmount]           = useState('');
  const [desc, setDesc]               = useState('');
  const [toAcc, setToAcc]             = useState('');
  const [msg, setMsg]                 = useState({ text: '', ok: true });
  const [loading, setLoading]         = useState(false);

  const loadAccounts = useCallback(async () => {
    const { data } = await accountAPI.list();
    setAccounts(data);
    if (data.length && !selected) setSelected(data[0]);
  }, [selected]);

  const loadTx = useCallback(async () => {
    if (!selected) return;
    const { data } = await accountAPI.transactions(selected.id);
    setTransactions(data);
  }, [selected]);

  useEffect(() => { loadAccounts(); }, []);
  useEffect(() => { if (selected) loadTx(); }, [selected]);

  const closeModal = () => { setModal(null); setAmount(''); setDesc(''); setToAcc(''); setMsg({ text: '', ok: true }); };

  const doAction = async () => {
    setLoading(true); setMsg({ text: '', ok: true });
    try {
      const amt = parseFloat(amount);
      if (!amt || amt <= 0) throw new Error('Enter a valid amount');

      if (modal === 'deposit') {
        await accountAPI.deposit(selected.id, { amount: amt, description: desc || 'Deposit' });
        setMsg({ text: '✅ Deposit successful!', ok: true });
      } else if (modal === 'withdraw') {
        await accountAPI.withdraw(selected.id, { amount: amt, description: desc || 'Withdrawal' });
        setMsg({ text: '✅ Withdrawal successful!', ok: true });
      } else if (modal === 'transfer') {
        if (!toAcc) throw new Error('Enter destination account number');
        await transferAPI.send({ from_account_id: selected.id, to_account_number: toAcc, amount: amt });
        setMsg({ text: '✅ Transfer successful!', ok: true });
      }

      await loadAccounts();
      await loadTx();
      setSelected(prev => accounts.find(a => a.id === prev?.id) || accounts[0]);
      setTimeout(closeModal, 1200);
    } catch (err) {
      setMsg({ text: err.response?.data?.error || err.message, ok: false });
    } finally {
      setLoading(false);
    }
  };

  const createAccount = async (type) => {
    setLoading(true);
    try {
      await accountAPI.create({ account_type: type });
      await loadAccounts();
      setMsg({ text: '✅ Account created!', ok: true });
      setTimeout(closeModal, 1000);
    } catch (err) {
      setMsg({ text: 'Failed to create account', ok: false });
    } finally { setLoading(false); }
  };

  const logout = () => { localStorage.clear(); navigate('/login'); };

  // Keep selected in sync after reload
  useEffect(() => {
    if (selected && accounts.length) {
      const fresh = accounts.find(a => a.id === selected.id);
      if (fresh) setSelected(fresh);
    }
  }, [accounts]);

  return (
    <div className="dash-wrap">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">⎈ K8s Bank</div>
        <nav>
          <div className="nav-label">ACCOUNTS</div>
          {accounts.map(a => (
            <div key={a.id}
                 className={`nav-item ${selected?.id === a.id ? 'active' : ''}`}
                 onClick={() => setSelected(a)}>
              <span className="nav-icon">{a.account_type === 'savings' ? '🏦' : '💳'}</span>
              <div>
                <div className="nav-acc-num">{a.account_number}</div>
                <div className="nav-acc-type">{a.account_type}</div>
              </div>
            </div>
          ))}
          <button className="btn-secondary btn-sm add-acc-btn"
                  onClick={() => setModal('newaccount')}>+ New Account</button>
        </nav>
        <div className="sidebar-footer">
          <span>👤 {user.full_name}</span>
          <button className="btn-secondary btn-sm" onClick={logout}>Logout</button>
        </div>
      </aside>

      {/* Main */}
      <main className="dash-main">
        <div className="dash-header">
          <h1>Welcome back, {user.full_name?.split(' ')[0]} 👋</h1>
          <span className="k8s-badge">📦 Namespace: banking-poc</span>
        </div>

        {selected ? (
          <>
            {/* Balance card */}
            <div className="balance-card card">
              <div className="balance-info">
                <p className="balance-label">Available Balance</p>
                <h2 className="balance-amt">{fmt(selected.balance)}</h2>
                <p className="balance-acc">{selected.account_number} · {selected.account_type}</p>
              </div>
              <div className="balance-actions">
                <button className="btn-success"    onClick={() => setModal('deposit')}>⬆ Deposit</button>
                <button className="btn-primary"    onClick={() => setModal('withdraw')}>⬇ Withdraw</button>
                <button className="btn-warning"    onClick={() => setModal('transfer')}>↔ Transfer</button>
              </div>
            </div>

            {/* Transactions */}
            <div className="card tx-card">
              <h3 className="tx-title">Recent Transactions</h3>
              {transactions.length === 0 ? (
                <p className="no-tx">No transactions yet. Make a deposit to get started!</p>
              ) : (
                <table>
                  <thead>
                    <tr><th>Type</th><th>Description</th><th>Reference</th><th>Amount</th><th>Date</th></tr>
                  </thead>
                  <tbody>
                    {transactions.map(tx => (
                      <tr key={tx.id}>
                        <td><span className={`tag-${tx.type}`}>{tx.type.toUpperCase()}</span></td>
                        <td>{tx.description || '—'}</td>
                        <td style={{fontFamily:'monospace'}}>{tx.reference_account || '—'}</td>
                        <td style={{color: tx.type === 'deposit' ? 'var(--green)' : 'var(--red)', fontWeight:700}}>
                          {tx.type === 'deposit' ? '+' : '-'}{fmt(tx.amount)}
                        </td>
                        <td style={{color:'var(--gray)'}}>
                          {new Date(tx.created_at).toLocaleString('en-IN')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        ) : (
          <div className="card" style={{padding:40,textAlign:'center',color:'var(--gray)'}}>
            No accounts found. Create one to get started!
          </div>
        )}
      </main>

      {/* Modals */}
      {(modal === 'deposit' || modal === 'withdraw' || modal === 'transfer') && (
        <Modal title={modal === 'deposit' ? '⬆ Deposit' : modal === 'withdraw' ? '⬇ Withdraw' : '↔ Transfer'}
               onClose={closeModal}>
          <div className="modal-body">
            <div className="field">
              <label>Amount (₹)</label>
              <input type="number" min="1" value={amount}
                     onChange={e => setAmount(e.target.value)} placeholder="0.00" />
            </div>
            {modal === 'transfer' && (
              <div className="field">
                <label>Destination Account Number</label>
                <input value={toAcc} onChange={e => setToAcc(e.target.value)}
                       placeholder="ACC0000000002" />
              </div>
            )}
            <div className="field">
              <label>Description (optional)</label>
              <input value={desc} onChange={e => setDesc(e.target.value)}
                     placeholder="e.g. Monthly savings" />
            </div>
            {msg.text && <p className={msg.ok ? 'ok-msg' : 'error-msg'}>{msg.text}</p>}
            <button className={modal === 'deposit' ? 'btn-success' : modal === 'withdraw' ? 'btn-primary' : 'btn-warning'}
                    style={{width:'100%',marginTop:12}} onClick={doAction} disabled={loading}>
              {loading ? 'Processing…' : 'Confirm'}
            </button>
          </div>
        </Modal>
      )}

      {modal === 'newaccount' && (
        <Modal title="➕ Open New Account" onClose={closeModal}>
          <div className="modal-body">
            <p style={{color:'var(--gray)',marginBottom:16}}>Choose account type:</p>
            <div style={{display:'flex',gap:12}}>
              <button className="btn-success" style={{flex:1}}
                      onClick={() => createAccount('savings')} disabled={loading}>
                🏦 Savings
              </button>
              <button className="btn-secondary" style={{flex:1}}
                      onClick={() => createAccount('checking')} disabled={loading}>
                💳 Checking
              </button>
            </div>
            {msg.text && <p className={msg.ok ? 'ok-msg' : 'error-msg'}>{msg.text}</p>}
          </div>
        </Modal>
      )}
    </div>
  );
}
