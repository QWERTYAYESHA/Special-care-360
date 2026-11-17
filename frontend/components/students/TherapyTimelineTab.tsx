"use client";

import React, { useEffect, useState, useMemo } from "react";
import { therapyTimelineDb } from "@/lib/therapy-timeline-api";
import { abcDb, dailyCareDb, iepDb, milestoneObservationsDb, regressionDb, scopeOf } from "@/lib/firestore-api";
import { useAuth } from "@/lib/auth-context";
import { TherapySession } from "@/types";
import { homePlanDb } from "@/lib/teletherapy-api";
import { api } from "@/lib/api";
import type { MilestoneObservationDoc } from "@/lib/firestore-api";
import type { RegressionAlertDoc } from "@/lib/firestore-api";
import type { HomePlanLog } from "@/lib/teletherapy-api";
import {
  Clock,
  Video,
  MapPin,
  CheckCircle,
  Calendar,
  User,
  ChevronRight,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import TherapySessionDetails from "@/components/therapy-timeline/TherapySessionDetails";

interface Props {
  studentId: string;
  studentName: string;
}

const THERAPY_TYPE_COLORS: Record<string, string> = {
  "Speech Therapy": "#7bc4c4",
  "Physiotherapy": "#9b8ec4",
  "Occupational Therapy": "#319795",
  "Behavioral Therapy": "#dd6b20",
  "Special Education": "#38a169",
  "Psychology Session": "#d69e2e",
  "Other": "#718096",
};

const STATUS_COLOR_MAP: Record<string, { bg: string; color: string; border: string }> = {
  Scheduled: { bg: "rgba(123, 196, 196, 0.15)", color: "#2c7a7b", border: "rgba(123, 196, 196, 0.4)" },
  scheduled: { bg: "rgba(123, 196, 196, 0.15)", color: "#2c7a7b", border: "rgba(123, 196, 196, 0.4)" },
  Completed: { bg: "rgba(104, 211, 145, 0.15)", color: "#276749", border: "rgba(104, 211, 145, 0.4)" },
  completed: { bg: "rgba(104, 211, 145, 0.15)", color: "#276749", border: "rgba(104, 211, 145, 0.4)" },
  Cancelled: { bg: "rgba(252, 129, 129, 0.15)", color: "#c53030", border: "rgba(252, 129, 129, 0.4)" },
  cancelled: { bg: "rgba(252, 129, 129, 0.15)", color: "#c53030", border: "rgba(252, 129, 129, 0.4)" },
  Rescheduled: { bg: "rgba(236, 201, 75, 0.15)", color: "#975a16", border: "rgba(236, 201, 75, 0.4)" },
  rescheduled: { bg: "rgba(236, 201, 75, 0.15)", color: "#975a16", border: "rgba(236, 201, 75, 0.4)" },
  "No Show": { bg: "rgba(229, 62, 62, 0.15)", color: "#9b2c2c", border: "rgba(229, 62, 62, 0.4)" },
  "no-show": { bg: "rgba(229, 62, 62, 0.15)", color: "#9b2c2c", border: "rgba(229, 62, 62, 0.4)" },
};

function format12h(time24: string): string {
  if (!time24) return "";
  const parts = time24.split(":");
  let hours = parseInt(parts[0], 10);
  const minutes = parts[1] || "00";
  if (isNaN(hours)) return time24;
  const ampm = hours >= 12 ? "PM" : "AM";
  hours = hours % 12 || 12;
  return `${hours}:${minutes} ${ampm}`;
}

function formatDate(dateStr: string): string {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr.length === 10 ? `${dateStr}T12:00:00` : dateStr);
    return d.toLocaleDateString([], {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export default function TherapyTimelineTab({ studentId, studentName }: Props) {
  const { profile } = useAuth();
  const [sessions, setSessions] = useState<TherapySession[]>([]);
  const [clinicalEvents, setClinicalEvents] = useState<Array<{ id: string; date: string; category: string; summary: string }>>([]);
  const [unavailableSources, setUnavailableSources] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [selectedSession, setSelectedSession] = useState<TherapySession | null>(null);

  useEffect(() => {
    if (!profile) return;
    setLoading(true);
    setError(false);

    const scope = scopeOf(profile);
    let active = true;
    const dateText = (value: unknown): string => {
      if (typeof value === "string") return value;
      if (value && typeof value === "object" && "toDate" in value && typeof value.toDate === "function") {
        try { return value.toDate().toISOString(); } catch { return ""; }
      }
      return "";
    };
    const results = Promise.allSettled([
      therapyTimelineDb.list(scope, { studentId }),
      abcDb.listIncidents(studentId, scope, 50),
      dailyCareDb.history(studentId, scope, 30),
      iepDb.listIEPRecords(studentId),
      milestoneObservationsDb.listForStudent(studentId, profile.centerId),
      regressionDb.listForStudent(studentId, profile.centerId),
      homePlanDb.listActivities(scope, studentId),
      homePlanDb.listLogs(scope, studentId),
    ] as const);
    void results.then(async ([sessionResult, abcResult, careResult, iepResult, observationsResult, regressionResult, activitiesResult, logsResult]) => {
      const failures: string[] = [];
      const get = <T,>(result: PromiseSettledResult<T>, name: string, fallback: T): T => {
        if (result.status === "fulfilled") return result.value;
        failures.push(name);
        return fallback;
      };
      const sessionList = get(sessionResult, "therapy sessions", [] as TherapySession[]);
      const incidents = get(abcResult, "ABC observations", [] as Record<string, unknown>[]);
      const journals = get(careResult, "daily care journals", [] as Record<string, unknown>[]);
      const iepRecords = get(iepResult, "IEP history", [] as Record<string, unknown>[]);
      const observations = get(observationsResult, "milestone observations", [] as MilestoneObservationDoc[]);
      const alerts = get(regressionResult, "regression alerts", [] as RegressionAlertDoc[]);
      const activities = get(activitiesResult, "home activities", [] as Array<{ id: string; title: string }>);
      const logs = get(logsResult, "home activity logs", [] as HomePlanLog[]);
      setSessions(sessionList);
      const events: Array<{ id: string; date: string; category: string; summary: string }> = [];
      sessionList.forEach((item) => events.push({ id: `session-${item.id}`, date: item.date || item.startDateTime || "", category: "Therapy session", summary: `${item.therapyType} · ${item.status}` }));
      incidents.forEach((item) => events.push({ id: `abc-${item.id}`, date: dateText(item.timestamp), category: "ABC observation", summary: "Behavior observation recorded" }));
      journals.forEach((item, index) => events.push({ id: `care-${studentId}-${String(item.date || index)}`, date: dateText(item.date || item.submittedAt), category: "Daily care", summary: "Daily care journal submitted" }));
      iepRecords.forEach((item, index) => events.push({ id: `iep-${String(item.id || index)}`, date: dateText(item.finalizedAt || item.updatedAt || item.createdAt), category: "IEP version", summary: `Plan ${String(item.status || "updated")} · version ${String(item.version || "")}` }));
      observations.forEach((item, index) => events.push({ id: `observation-${String(item.id || index)}`, date: dateText(item.observedAt), category: "Milestone observation", summary: `Milestone marked ${String(item.observedStatus || "observed")}` }));
      alerts.filter((item) => item.resolved !== true).forEach((item, index) => events.push({ id: `regression-${String(item.id || index)}`, date: dateText(item.createdAt), category: "Regression alert", summary: String(item.alertLevel || "Progress alert") }));
      const activityNames = new Map(activities.map((item) => [item.id, item.title]));
      logs.forEach((item, index) => events.push({ id: `home-${String(item.id || index)}`, date: dateText(item.date), category: "Home plan", summary: `${activityNames.get(String(item.activityId || "")) || "Home activity"} · ${item.completed === true ? "completed" : "not completed"}` }));
      if (profile.role === "parent" || profile.role === "therapist") {
        const clips = await Promise.allSettled(activities.map(async (activity) => {
          const response = await api.get(`/api/progress-videos/${encodeURIComponent(studentId)}/${encodeURIComponent(activity.id)}`);
          return Array.isArray(response.data) ? response.data as Array<Record<string, unknown>> : [];
        }));
        clips.forEach((result, activityIndex) => {
          if (result.status === "rejected") { if (!failures.includes("progress videos")) failures.push("progress videos"); return; }
          result.value.forEach((clip, index) => events.push({
            id: `video-${String(clip.id || `${activityIndex}-${index}`)}`,
            date: dateText(clip.createdAt || clip.uploadedAt),
            category: "Progress video",
            summary: `${activityNames.get(activities[activityIndex].id) || "Home activity"} · video uploaded`,
          }));
        });
      }
      if (active) {
        setClinicalEvents(events.filter((event) => Boolean(event.date)).sort((a, b) => b.date.localeCompare(a.date)));
        setUnavailableSources(failures);
        setError(false);
        setLoading(false);
      }
    }).catch((err) => {
      console.error("Clinical timeline fetch failed:", err);
      if (active) { setError(true); setLoading(false); }
    });
    return () => { active = false; };
  }, [profile, studentId]);

  const now = new Date().toISOString().substring(0, 10);

  const { upcoming, past } = useMemo(() => {
    const up: TherapySession[] = [];
    const pa: TherapySession[] = [];

    sessions.forEach((s) => {
      const d = s.date || (s.startDateTime ? s.startDateTime.substring(0, 10) : "");
      if (d >= now && s.status !== "Completed" && s.status !== "completed") {
        up.push(s);
      } else {
        pa.push(s);
      }
    });

    up.sort((a, b) => (a.date || "").localeCompare(b.date || ""));
    pa.sort((a, b) => (b.date || "").localeCompare(a.date || ""));

    return { upcoming: up, past: pa };
  }, [sessions, now]);

  if (loading) {
    return (
      <div className="glass-card" style={{ padding: "40px", textAlign: "center" }}>
        <div className="skeleton" style={{ height: "180px", borderRadius: "12px" }} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card" style={{ padding: "24px", color: "var(--danger)", textAlign: "center" }}>
        <AlertCircle size={24} style={{ margin: "0 auto 8px" }} />
        Could not load therapy sessions for this student.
      </div>
    );
  }

  const renderTimelineItem = (s: TherapySession) => {
    const typeColor = THERAPY_TYPE_COLORS[s.therapyType as string] || "#7bc4c4";
    const statusStyle = STATUS_COLOR_MAP[s.status] || STATUS_COLOR_MAP["Scheduled"];
    const isTele = String(s.sessionType).toLowerCase().includes("tele") || s.sessionType === "Tele-Therapy";

    return (
      <div
        key={s.id}
        onClick={() => setSelectedSession(s)}
        className="glass-card"
        style={{
          padding: "16px 20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderLeft: `4px solid ${typeColor}`,
          cursor: "pointer",
          transition: "transform 0.15s ease, box-shadow 0.15s ease",
          gap: "14px",
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLElement).style.transform = "translateX(4px)";
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLElement).style.transform = "none";
        }}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Date & Time Header */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", marginBottom: "4px" }}>
            <span style={{ fontSize: "0.85rem", fontWeight: 800, color: "var(--primary-dark)", display: "flex", alignItems: "center", gap: "5px" }}>
              <Clock size={14} style={{ color: typeColor }} />
              {formatDate(s.date)} · {format12h(s.startTime)} - {format12h(s.endTime)}
            </span>
            <span
              style={{
                padding: "2px 8px",
                borderRadius: "999px",
                fontSize: "0.7rem",
                fontWeight: 700,
                background: statusStyle.bg,
                color: statusStyle.color,
                border: `1px solid ${statusStyle.border}`,
              }}
            >
              {s.status}
            </span>
            <span
              style={{
                padding: "2px 8px",
                borderRadius: "999px",
                fontSize: "0.7rem",
                fontWeight: 600,
                background: "rgba(61,79,107,0.08)",
                color: "var(--primary-dark)",
              }}
            >
              {s.sessionType}
            </span>
          </div>

          {/* Therapy Type */}
          <div style={{ fontSize: "1.02rem", fontWeight: 800, color: "var(--primary-dark)", marginBottom: "4px" }}>
            {s.therapyType}
          </div>

          {/* Therapist & Location */}
          <div style={{ display: "flex", alignItems: "center", gap: "14px", fontSize: "0.82rem", color: "var(--text-secondary)", flexWrap: "wrap" }}>
            <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <User size={13} style={{ color: "#9b8ec4" }} />
              Therapist: <strong style={{ color: "var(--primary-dark)" }}>{s.therapistName}</strong>
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              {isTele ? <Video size={13} style={{ color: "#9b8ec4" }} /> : <MapPin size={13} style={{ color: "var(--accent-teal)" }} />}
              {s.location || (isTele ? "Virtual Room" : "Room 1")}
            </span>
          </div>

          {/* Notes */}
          {s.notes && (
            <div style={{ marginTop: "6px", fontSize: "0.8rem", color: "var(--text-primary)", background: "rgba(255,255,255,0.4)", padding: "4px 8px", borderRadius: "6px" }}>
              {s.notes}
            </div>
          )}
        </div>

        {/* Join button & Details chevron */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexShrink: 0 }}>
          {isTele && (
            <Link
              href="/dashboard/teletherapy"
              onClick={(e) => e.stopPropagation()}
              className="btn-primary"
              style={{ padding: "6px 12px", fontSize: "0.78rem", display: "inline-flex", alignItems: "center", gap: "4px", textDecoration: "none" }}
            >
              <Video size={13} /> Join
            </Link>
          )}
          <ChevronRight size={18} style={{ color: "var(--text-secondary)" }} />
        </div>
      </div>

    );
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* ── Top Overview Banner ────────────────────────────────────────────── */}
      <div
        className="glass-card"
        style={{
          padding: "16px 20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "12px",
          background: "linear-gradient(135deg, rgba(123,196,196,0.12) 0%, rgba(184,168,212,0.12) 100%)",
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 800, color: "var(--primary-dark)" }}>
            Therapy Timeline for {studentName}
          </h3>
          <p style={{ margin: "2px 0 0", fontSize: "0.82rem", color: "var(--text-secondary)" }}>
            {upcoming.length} upcoming scheduled · {past.length} previous sessions
          </p>
        </div>
        <Link
          href="/dashboard/therapy-timeline"
          className="btn-primary"
          style={{ padding: "8px 14px", fontSize: "0.82rem", display: "inline-flex", alignItems: "center", gap: "6px", textDecoration: "none" }}
        >
          <Calendar size={14} /> Full Calendar Schedule
        </Link>
      </div>

      <section className="glass-card" style={{ padding: "20px" }}>
        <h4 style={{ margin: "0 0 6px", color: "var(--primary-dark)" }}>Clinical history</h4>
        <p style={{ margin: "0 0 14px", color: "var(--text-secondary)", fontSize: "0.82rem" }}>Chronological overview for {studentName}; open each feature for full details.</p>
        {unavailableSources.length > 0 && <p role="status" style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>Some history could not load: {unavailableSources.join(", ")}.</p>}
        {clinicalEvents.length === 0 ? <p style={{ color: "var(--text-secondary)" }}>No clinical history recorded yet.</p> : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {clinicalEvents.map((event) => <div key={event.id} style={{ display: "flex", gap: 12, alignItems: "baseline", padding: "9px 0", borderBottom: "1px solid rgba(61,79,107,0.1)" }}>
              <time dateTime={event.date} style={{ minWidth: 150, fontSize: "0.78rem", color: "var(--text-secondary)" }}>{formatDate(event.date)}</time>
              <span className="chip chip-info" style={{ whiteSpace: "nowrap" }}>{event.category}</span>
              <span style={{ fontSize: "0.86rem", color: "var(--primary-dark)" }}>{event.summary}</span>
            </div>)}
          </div>
        )}
      </section>

      {/* ── Upcoming ──────────────────────────────────────────────────────── */}
      {upcoming.length > 0 && (
        <section>
          <h4 style={{ margin: "0 0 12px", fontSize: "0.95rem", fontWeight: 800, color: "var(--primary-dark)", display: "flex", alignItems: "center", gap: "6px" }}>
            <Calendar size={16} style={{ color: "var(--accent-teal)" }} /> Upcoming Sessions ({upcoming.length})
          </h4>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {upcoming.map(renderTimelineItem)}
          </div>
        </section>
      )}
      {sessions.length === 0 && <div className="glass-card" style={{ padding: 18, color: "var(--text-secondary)" }}>No therapy sessions are scheduled yet.</div>}

      {/* ── Past ──────────────────────────────────────────────────────────── */}
      {past.length > 0 && (
        <section>
          <h4 style={{ margin: "0 0 12px", fontSize: "0.95rem", fontWeight: 800, color: "var(--primary-dark)", display: "flex", alignItems: "center", gap: "6px" }}>
            <CheckCircle size={16} style={{ color: "#38a169" }} /> Previous Sessions ({past.length})
          </h4>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {past.map(renderTimelineItem)}
          </div>
        </section>
      )}

      {/* Detail Modal */}
      {selectedSession && (
        <TherapySessionDetails
          session={selectedSession}
          isOpen={Boolean(selectedSession)}
          onClose={() => setSelectedSession(null)}
          onEdit={() => {}}
          onDelete={() => {}}
          onStatusChange={() => {}}
          currentUserRole={profile?.role || "parent"}
          currentUserId={profile?.uid || ""}
        />
      )}
    </div>
  );
}
