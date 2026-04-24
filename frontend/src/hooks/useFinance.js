import { useState, useEffect, useCallback, useRef } from "react";
import { transactionsAPI, accountsAPI } from "../services/api";

export function useTransactions(filters = {}) {
  const [data, setData]       = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const res = await transactionsAPI.getAll(filters);
      setData(res.data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(filters)]);

  useEffect(() => { fetch(); }, [fetch]);
  return { data, loading, error, refetch: fetch };
}

export function useAccounts() {
  const [data, setData]       = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    accountsAPI.getAll()
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, []);

  const totalBalance = data.reduce((sum, acc) => sum + acc.balance, 0);
  return { data, loading, totalBalance };
}

export function useSpendingAnalytics(month, year) {
  const [data, setData]       = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    transactionsAPI.getSpending(month, year)
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, [month, year]);

  return { data, loading };
}

export function useMonthlyTrend(months = 6) {
  const [data, setData]       = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    transactionsAPI.getTrend(months)
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, [months]);

  return { data, loading };
}

export function useWebSocket(userId, onMessage) {
  const ws = useRef(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!userId) return;
    const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";
    ws.current = new WebSocket(`${WS_URL}/ws/${userId}`);
    ws.current.onopen    = () => setConnected(true);
    ws.current.onclose   = () => setConnected(false);
    ws.current.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)); } catch {}
    };
    const ping = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) ws.current.send("ping");
    }, 30000);
    return () => { clearInterval(ping); ws.current?.close(); };
  }, [userId]);

  return { connected };
}