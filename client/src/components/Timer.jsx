import { useState, useEffect, useRef } from 'react';
import { timeEntriesApi } from '../api/timeEntries';
import { useToast } from '../context/ToastContext';
import { Play, Square } from 'lucide-react';

export default function Timer({ taskId, taskTitle, initialSeconds = 0, onStop }) {
  const [running, setRunning] = useState(false);
  const [entryId, setEntryId] = useState(null);
  const [startedAt, setStartedAt] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const intervalRef = useRef(null);
  const { addToast } = useToast();

  // Check for existing running timer on mount
  useEffect(() => {
    checkRunningTimer();
  }, [taskId]);

  // Update elapsed time using timestamps (not setInterval counting)
  useEffect(() => {
    if (running && startedAt) {
      intervalRef.current = setInterval(() => {
        const startZ = startedAt.endsWith('Z') ? startedAt : `${startedAt}Z`;
        setElapsed(Math.floor((Date.now() - new Date(startZ).getTime()) / 1000));
      }, 1000);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [running, startedAt]);

  const checkRunningTimer = async () => {
    try {
      const res = await timeEntriesApi.list();
      const runningEntry = res.data.find(
        (e) => e.task_id === taskId && !e.ended_at
      );
      if (runningEntry) {
        setRunning(true);
        setEntryId(runningEntry.id);
        const startZ = runningEntry.started_at.endsWith('Z') ? runningEntry.started_at : `${runningEntry.started_at}Z`;
        setStartedAt(startZ);
        setElapsed(Math.floor((Date.now() - new Date(startZ).getTime()) / 1000));
      }
    } catch (err) {
      // Silently fail — timer will show as stopped
    }
  };

  const handleStart = async () => {
    try {
      const res = await timeEntriesApi.start(taskId);
      setRunning(true);
      setEntryId(res.data.id);
      const startZ = res.data.started_at.endsWith('Z') ? res.data.started_at : `${res.data.started_at}Z`;
      setStartedAt(startZ);
      setElapsed(0);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to start timer', 'error');
    }
  };

  const handleStop = async () => {
    try {
      const res = await timeEntriesApi.stop(entryId);
      setRunning(false);
      setEntryId(null);
      setStartedAt(null);
      const mins = Math.floor((res.data.duration_seconds || 0) / 60);
      const hrs = Math.floor(mins / 60);
      const remainMins = mins % 60;
      const timeStr = hrs > 0 ? `${hrs}h ${remainMins}m` : `${remainMins}m`;
      addToast(`Timer stopped — ${timeStr} recorded`, 'success');
      if (onStop) onStop();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to stop timer', 'error');
    }
  };

  const formatTime = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  return (
    <div className={`timer ${running ? 'timer-running' : ''}`} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <span className="timer-display" style={{ fontFamily: 'monospace', fontSize: '1.1rem', fontWeight: 600 }}>{formatTime(initialSeconds + elapsed)}</span>
      {running ? (
        <button className="btn btn-sm btn-danger" onClick={handleStop} title="Stop timer" style={{ display: 'flex', alignItems: 'center', gap: '4px', height: 'fit-content' }}>
          <Square size={12} fill="currentColor" /> Stop
        </button>
      ) : (
        <button className="btn btn-sm btn-success" onClick={handleStart} title="Start timer" style={{ display: 'flex', alignItems: 'center', gap: '4px', height: 'fit-content' }}>
          <Play size={12} fill="currentColor" /> Start
        </button>
      )}
      {running && <span className="timer-pulse" style={{ fontSize: '10px', color: 'var(--danger)' }}>●</span>}
    </div>
  );
}
