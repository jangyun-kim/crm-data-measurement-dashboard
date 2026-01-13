"use client";

import React, { useEffect, useMemo, useState } from "react";

/**
 * Phase 1 목표:
 * - 종이 상담서 이미지(템플릿) 위에 입력 필드를 좌표로 오버레이
 * - 저장/불러오기: localStorage 기반 (DB 붙이기 전)
 * - 한국어 UI
 *
 * 사용법:
 * - public/templates/consult.png 를 넣어두면 자동 로드됨
 * - 좌표는 FIELDS의 x,y,w,h(%)만 조정하면 됨
 */

type FieldType = "text" | "number" | "date" | "textarea";

type Field = {
  id: string;
  label: string;
  type: FieldType;
  x: number; // left in %
  y: number; // top in %
  w: number; // width in %
  h: number; // height in %
};

const TEMPLATE_SRC = "/templates/consult.png";

/**
 * TODO: 여기가 “핵심 조정 포인트”
 * - 네가 올린 상담지에 맞춰 x,y,w,h만 조정하면 종이랑 똑같이 맞출 수 있음
 * - 지금 값은 임시 배치(샘플)
 */
const FIELDS: Field[] = [
  { id: "name", label: "성명", type: "text", x: 6, y: 10, w: 28, h: 3.2 },
  { id: "birth", label: "생년월일", type: "text", x: 38, y: 10, w: 25, h: 3.2 },
  { id: "phone", label: "H.P", type: "text", x: 6, y: 15, w: 28, h: 3.2 },
  { id: "address", label: "주소", type: "text", x: 6, y: 20, w: 57, h: 3.2 },

  {
    id: "orderDate",
    label: "주문일",
    type: "date",
    x: 6,
    y: 25,
    w: 22,
    h: 3.2,
  },
  {
    id: "fittingDate",
    label: "가봉일",
    type: "date",
    x: 34,
    y: 25,
    w: 18,
    h: 3.2,
  },
  {
    id: "deliveryDate",
    label: "납품일",
    type: "date",
    x: 54,
    y: 25,
    w: 18,
    h: 3.2,
  },

  {
    id: "totalPrice",
    label: "주문금액",
    type: "number",
    x: 70,
    y: 10,
    w: 23,
    h: 3.2,
  },
  { id: "deposit", label: "선금", type: "number", x: 70, y: 15, w: 23, h: 3.2 },
  { id: "balance", label: "잔금", type: "number", x: 70, y: 20, w: 23, h: 3.2 },

  {
    id: "orderDetail",
    label: "주문내역",
    type: "textarea",
    x: 28,
    y: 33,
    w: 65,
    h: 18,
  },

  { id: "height", label: "신장", type: "text", x: 6, y: 33, w: 18, h: 3 },
  { id: "neck", label: "목", type: "text", x: 6, y: 37, w: 18, h: 3 },
  { id: "armhole", label: "진동", type: "text", x: 6, y: 41, w: 18, h: 3 },
  { id: "shoulder", label: "어깨", type: "text", x: 6, y: 49, w: 18, h: 3 },
  { id: "sleeve", label: "소매", type: "text", x: 6, y: 53, w: 18, h: 3 },
];

type SavedRecord = {
  id: string; // record id
  createdAt: string; // ISO string
  payload: Record<string, any>;
};

const STORAGE_KEY = "elburim_consult_records_v1";

function nowISO() {
  const d = new Date();
  // 한국식 보기 편하게: YYYY-MM-DD HH:mm:ss
  const pad = (n: number) => String(n).padStart(2, "0");
  const s = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(
    d.getDate()
  )} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  return s;
}

function safeParse<T>(v: string | null, fallback: T): T {
  if (!v) return fallback;
  try {
    return JSON.parse(v) as T;
  } catch {
    return fallback;
  }
}

export default function ConsultPage() {
  // 폼 값
  const [values, setValues] = useState<Record<string, any>>({});
  // 저장 기록
  const [records, setRecords] = useState<SavedRecord[]>([]);
  const [selectedRecordId, setSelectedRecordId] = useState<string>("");

  // 최초 로드: localStorage에서 기록 불러오기
  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    const list = safeParse<SavedRecord[]>(raw, []);
    // 최신순 정렬
    list.sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1));
    setRecords(list);
  }, []);

  const selectedRecord = useMemo(() => {
    if (!selectedRecordId) return null;
    return records.find((r) => r.id === selectedRecordId) || null;
  }, [records, selectedRecordId]);

  function onChange(fieldId: string, v: any) {
    setValues((prev) => ({ ...prev, [fieldId]: v }));
  }

  function clearAll() {
    setValues({});
    setSelectedRecordId("");
  }

  function saveRecord() {
    // date 타입은 문자열로 저장(YYYY-MM-DD)
    const payload: Record<string, any> = {};
    for (const f of FIELDS) {
      const v = values[f.id];
      if (f.type === "date") {
        // input type=date는 YYYY-MM-DD 문자열
        payload[f.id] = typeof v === "string" ? v : "";
      } else {
        payload[f.id] = v ?? "";
      }
    }

    const rec: SavedRecord = {
      id: `R-${Date.now()}`,
      createdAt: nowISO(),
      payload,
    };

    const next = [rec, ...records];
    setRecords(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    setSelectedRecordId(rec.id);
    alert("저장 완료");
  }

  function loadRecord(rec: SavedRecord) {
    setValues(rec.payload || {});
    setSelectedRecordId(rec.id);
  }

  function deleteRecord(recId: string) {
    if (!confirm("이 기록을 삭제할까요?")) return;
    const next = records.filter((r) => r.id !== recId);
    setRecords(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    if (selectedRecordId === recId) {
      setSelectedRecordId("");
      setValues({});
    }
  }

  return (
    <div style={{ padding: 16 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 12 }}>
        상담지 입력
      </h1>

      {/* 상단 액션 바 */}
      <div
        style={{
          display: "flex",
          gap: 8,
          alignItems: "center",
          flexWrap: "wrap",
          marginBottom: 12,
          padding: 12,
          border: "1px solid rgba(0,0,0,0.12)",
          borderRadius: 12,
          background: "rgba(255,255,255,0.75)",
        }}
      >
        <button
          onClick={clearAll}
          style={{
            padding: "10px 12px",
            borderRadius: 10,
            border: "1px solid rgba(0,0,0,0.2)",
            background: "white",
            cursor: "pointer",
          }}
        >
          새 입력(초기화)
        </button>

        <button
          onClick={saveRecord}
          style={{
            padding: "10px 12px",
            borderRadius: 10,
            border: "1px solid rgba(0,0,0,0.2)",
            background: "white",
            cursor: "pointer",
          }}
        >
          저장
        </button>

        <div
          style={{
            marginLeft: 8,
            display: "flex",
            gap: 8,
            alignItems: "center",
          }}
        >
          <span style={{ fontSize: 13, opacity: 0.7 }}>저장기록</span>
          <select
            value={selectedRecordId}
            onChange={(e) => setSelectedRecordId(e.target.value)}
            style={{ padding: "8px 10px", borderRadius: 10 }}
          >
            <option value="">선택 안 함</option>
            {records.map((r) => (
              <option key={r.id} value={r.id}>
                {r.createdAt}
              </option>
            ))}
          </select>

          <button
            onClick={() => {
              if (!selectedRecord) return;
              loadRecord(selectedRecord);
            }}
            disabled={!selectedRecord}
            style={{
              padding: "10px 12px",
              borderRadius: 10,
              border: "1px solid rgba(0,0,0,0.2)",
              background: selectedRecord ? "white" : "rgba(255,255,255,0.5)",
              cursor: selectedRecord ? "pointer" : "not-allowed",
            }}
          >
            불러오기
          </button>

          <button
            onClick={() => {
              if (!selectedRecord) return;
              deleteRecord(selectedRecord.id);
            }}
            disabled={!selectedRecord}
            style={{
              padding: "10px 12px",
              borderRadius: 10,
              border: "1px solid rgba(0,0,0,0.2)",
              background: selectedRecord ? "white" : "rgba(255,255,255,0.5)",
              cursor: selectedRecord ? "pointer" : "not-allowed",
            }}
          >
            삭제
          </button>
        </div>
      </div>

      {/* 템플릿 + 오버레이 입력 */}
      <div
        style={{
          position: "relative",
          width: "100%",
          maxWidth: 1100,
          margin: "0 auto",
          border: "1px solid rgba(0,0,0,0.12)",
          borderRadius: 12,
          overflow: "hidden",
          background: "white",
        }}
      >
        {/* 종이 느낌 유지: 이미지 비율 기준 */}
        <div style={{ position: "relative", width: "100%" }}>
          <img
            src={TEMPLATE_SRC}
            alt="상담지 템플릿"
            style={{ width: "100%", display: "block" }}
          />

          {/* 입력 오버레이 */}
          {FIELDS.map((f) => (
            <div
              key={f.id}
              style={{
                position: "absolute",
                left: `${f.x}%`,
                top: `${f.y}%`,
                width: `${f.w}%`,
                height: `${f.h}%`,
              }}
              title={f.label}
            >
              {f.type === "textarea" ? (
                <textarea
                  value={values[f.id] ?? ""}
                  onChange={(e) => onChange(f.id, e.target.value)}
                  style={{
                    width: "100%",
                    height: "100%",
                    resize: "none",
                    background: "rgba(255,255,255,0.55)",
                    border: "1px solid rgba(0,0,0,0.25)",
                    borderRadius: 6,
                    padding: "6px 8px",
                    fontSize: 14,
                    outline: "none",
                  }}
                />
              ) : (
                <input
                  type={
                    f.type === "date"
                      ? "date"
                      : f.type === "number"
                      ? "number"
                      : "text"
                  }
                  value={values[f.id] ?? ""}
                  onChange={(e) => onChange(f.id, e.target.value)}
                  style={{
                    width: "100%",
                    height: "100%",
                    background: "rgba(255,255,255,0.55)",
                    border: "1px solid rgba(0,0,0,0.25)",
                    borderRadius: 6,
                    padding: "6px 8px",
                    fontSize: 14,
                    outline: "none",
                  }}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 하단: 최근 기록 간단 표시 */}
      <div style={{ maxWidth: 1100, margin: "16px auto 0" }}>
        <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>
          최근 저장 기록
        </h2>
        {records.length === 0 ? (
          <div style={{ opacity: 0.7 }}>저장된 기록이 없습니다.</div>
        ) : (
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {records.slice(0, 5).map((r) => (
              <li key={r.id} style={{ marginBottom: 4 }}>
                {r.createdAt}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
