import { useState, useEffect, useCallback } from 'react';
import { ImportJobStatus } from '@/types/lead';
import { leadsService } from '@/services/leads';

export function useImportJobPolling(jobId: string | null) {
  const [job, setJob] = useState<ImportJobStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pollInterval, setPollInterval] = useState(1500); // Start at 1.5s
  const [pollCount, setPollCount] = useState(0);

  const fetchJob = useCallback(async () => {
    if (!jobId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const jobStatus = await leadsService.getImportJob(jobId);
      setJob(jobStatus);
      setPollCount(prev => prev + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch job status');
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    if (!jobId) return;

    fetchJob();

    const interval = setInterval(() => {
      if (job?.status === 'pending' || job?.status === 'running') {
        fetchJob();
        // Exponential backoff: after 10s (7 polls), increase to 3s
        if (pollCount >= 7) {
          setPollInterval(3000);
        }
      }
    }, pollInterval);

    return () => clearInterval(interval);
  }, [jobId, job?.status, fetchJob, pollInterval, pollCount]);

  const stopPolling = useCallback(() => {
    setJob(null);
    setPollCount(0);
    setPollInterval(1500);
  }, []);

  return {
    job,
    loading,
    error,
    stopPolling,
    refetch: fetchJob
  };
}