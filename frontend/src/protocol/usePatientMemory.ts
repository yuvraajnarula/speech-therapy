/**
 * usePatientMemory — fetches and caches clinical memory for a patient+dialect.
 *
 * Calls GET /api/v1/memory/{patientId}?dialect={lang}
 * Syncs into therapyStore.patientMemory on success.
 * Returns null on unauthenticated / backend unavailable.
 */
import { useEffect, useCallback } from "react";
import type { PatientMemory } from "../store/therapyStore";
import { therapyStore } from "../store/therapyStore";
import { useTherapyStore } from "../store/therapyStore";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  (window.location.hostname === "localhost" ? "http://localhost:8000" : "");

export function usePatientMemory(
  patientId: string | null,
  dialect: string,
  authToken: string | null
): PatientMemory | null {
  const memory = useTherapyStore((s) => s.patientMemory);

  const fetchMemory = useCallback(async () => {
    if (!patientId || !authToken) return;
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/memory/${encodeURIComponent(patientId)}?dialect=${encodeURIComponent(dialect)}`,
        {
          headers: { Authorization: `Bearer ${authToken}` },
        }
      );
      if (!res.ok) return;
      const data: PatientMemory = await res.json();
      therapyStore.setPatientMemory(data);
    } catch {
      // Silently fail — memory layer is non-blocking
    }
  }, [patientId, dialect, authToken]);

  useEffect(() => {
    fetchMemory();
    // Refresh every 30 seconds to pick up Celery batch analytics updates
    const interval = setInterval(fetchMemory, 30_000);
    return () => clearInterval(interval);
  }, [fetchMemory]);

  return memory;
}
