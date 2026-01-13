"use client";

import React, { useEffect, useMemo, useState } from "react";

type FieldType = "text" | "textarea" | "number" | "date";

type Field = {
  id: string;
  label: string;
  type: FieldType;
  x: number; // 0~1 (left)
  y: number; // 0~1 (top)
  w: number; // 0~1 (width)
  h?: number; // optional
};

type RecordRow = {
  createdAt: string; // ISO string
  memberKey: string; // name|phone
  values: Record<string, any>;
};

const TEMPLATE_SRC = "/templates/consult.png";

const FIELDS: Field[] = [
  { id: "name", label: "성명", type: "text", x: 0.1, y: 0.114, w: 0.16 },
  { id: "birth", label: "생년월일", type: "date", x: 0.47, y: 0.114, w: 0.22 },
  { id: "phone", label: "H.P", type: "text", x: 0.1, y: 0.182, w: 0.23 },
  { id: "address", label: "주소", type: "text", x: 0.1, y: 0.147, w: 0.59 },
  {
    id: "customer-id",
    label: "고객ID",
    type: "number",
    x: 0.8,
    y: 0.065,
    w: 0.185,
  },

  { id: "orderDate", label: "주문일", type: "date", x: 0.1, y: 0.215, w: 0.23 },
  {
    id: "fittingDate",
    label: "가봉일",
    type: "date",
    x: 0.47,
    y: 0.182,
    w: 0.22,
  },
  {
    id: "deliveryDate",
    label: "납품일",
    type: "date",
    x: 0.47,
    y: 0.215,
    w: 0.22,
  },

  {
    id: "price",
    label: "주문금액",
    type: "number",
    x: 0.81,
    y: 0.13,
    w: 0.16,
  },
  { id: "deposit", label: "선금", type: "number", x: 0.81, y: 0.181, w: 0.16 },
  { id: "balance", label: "잔금", type: "number", x: 0.81, y: 0.215, w: 0.16 },

  {
    id: "orderDetail",
    label: "주문내역",
    type: "textarea",
    x: 0.18,
    y: 0.28,
    w: 0.653,
    h: 0.22,
  },
  {
    id: "photoNo",
    label: "사진 NO.",
    type: "textarea",
    x: 0.835,
    y: 0.258,
    w: 0.151,
    h: 0.022,
  },
  {
    id: "fabricSample",
    label: "원단샘플",
    type: "textarea",
    x: 0.834,
    y: 0.315,
    w: 0.153,
    h: 0.185,
  },

  // 치수 일부(필요한 만큼 계속 추가)
  { id: "height", label: "신장", type: "text", x: 0.05, y: 0.285, w: 0.125 },
  { id: "neck", label: "목", type: "text", x: 0.05, y: 0.319, w: 0.125 },
  { id: "armhole", label: "진동", type: "text", x: 0.05, y: 0.353, w: 0.125 },
  {
    id: "suit-jacket",
    label: "상의장",
    type: "text",
    x: 0.05,
    y: 0.387,
    w: 0.125,
  },
  {
    id: "total-length",
    label: "총장",
    type: "text",
    x: 0.05,
    y: 0.421,
    w: 0.125,
  },
  { id: "shoulder", label: "어깨", type: "text", x: 0.05, y: 0.455, w: 0.125 },
  { id: "sleeve", label: "소매", type: "text", x: 0.05, y: 0.489, w: 0.125 },
  {
    id: "half-shoulder",
    label: "반어깨소매",
    type: "text",
    x: 0.05,
    y: 0.523,
    w: 0.125,
  },
  {
    id: "back-width",
    label: "뒤품",
    type: "text",
    x: 0.05,
    y: 0.557,
    w: 0.125,
  },
  {
    id: "front-shoulder",
    label: "앞어깨",
    type: "text",
    x: 0.05,
    y: 0.591,
    w: 0.125,
  },
  {
    id: "front-width",
    label: "앞품",
    type: "text",
    x: 0.05,
    y: 0.625,
    w: 0.125,
  },
  {
    id: "chest",
    label: "상동",
    type: "text",
    x: 0.05,
    y: 0.659,
    w: 0.125,
  },
  { id: "mid-waist", label: "중동", type: "text", x: 0.05, y: 0.693, w: 0.125 },
  { id: "waist", label: "허리", type: "text", x: 0.05, y: 0.727, w: 0.125 },
  { id: "hip", label: "볼기", type: "text", x: 0.05, y: 0.761, w: 0.125 },
  { id: "hem", label: "기장", type: "text", x: 0.05, y: 0.793, w: 0.125 },
  {
    id: "lining-length",
    label: "안기장",
    type: "text",
    x: 0.05,
    y: 0.829,
    w: 0.125,
  },
  { id: "thigh", label: "허벅", type: "text", x: 0.05, y: 0.861, w: 0.125 },
  { id: "calf", label: "종아리", type: "text", x: 0.05, y: 0.895, w: 0.125 },
  {
    id: "inseam",
    label: "마다/시리",
    type: "text",
    x: 0.05,
    y: 0.929,
    w: 0.125,
  },

  // =========================
  // <바지,조끼 디자인> 섹션
  // =========================

  // 디자인 메모(그림 주변에 적는 메모 용)
  {
    id: "designMemoLeft",
    label: "디자인메모(좌)",
    type: "textarea",
    x: 0.19,
    y: 0.525,
    w: 0.443,
    h: 0.256,
  },
  {
    id: "designMemoRight",
    label: "디자인메모(우)",
    type: "textarea",
    x: 0.65,
    y: 0.525,
    w: 0.33,
    h: 0.24,
  },

  // 가봉복 NO.(코트/상의/중/하의/셔츠) - 중앙 하단 표(좌)
  {
    id: "bft_coat",
    label: "가봉복_코트",
    type: "text",
    x: 0.265,
    y: 0.793,
    w: 0.085,
  },
  {
    id: "bft_top",
    label: "가봉복_상의",
    type: "text",
    x: 0.265,
    y: 0.827,
    w: 0.085,
  },
  {
    id: "bft_mid",
    label: "가봉복_중",
    type: "text",
    x: 0.265,
    y: 0.86,
    w: 0.085,
  },
  {
    id: "bft_bottom",
    label: "가봉복_하의",
    type: "text",
    x: 0.265,
    y: 0.895,
    w: 0.085,
  },
  {
    id: "bft_shirt",
    label: "가봉복_셔츠",
    type: "text",
    x: 0.265,
    y: 0.929,
    w: 0.085,
  },

  // 주문수량(코트/상의/중/하의/셔츠) - 중앙 하단 표(우)
  {
    id: "qty_coat",
    label: "주문수량_코트",
    type: "text",
    x: 0.511,
    y: 0.793,
    w: 0.085,
  },
  {
    id: "qty_top",
    label: "주문수량_상의",
    type: "text",
    x: 0.511,
    y: 0.827,
    w: 0.085,
  },
  {
    id: "qty_mid",
    label: "주문수량_중",
    type: "text",
    x: 0.511,
    y: 0.86,
    w: 0.085,
  },
  {
    id: "qty_bottom",
    label: "주문수량_하의",
    type: "text",
    x: 0.511,
    y: 0.895,
    w: 0.085,
  },
  {
    id: "qty_shirt",
    label: "주문수량_셔츠",
    type: "text",
    x: 0.511,
    y: 0.929,
    w: 0.085,
  },

  // 작업지시서(품명/제작/수량/입출고) - 우측 하단 표
  // 고정 5줄(코트/상의/중/하의/셔츠)로 먼저 생성,
  // 나중에 행추가(동적)로 수정.

  // ---- row1(코트)
  {
    id: "work_make_1",
    label: "작업_제작1",
    type: "text",
    x: 0.711,
    y: 0.793,
    w: 0.08,
  },
  {
    id: "work_qty_1",
    label: "작업_수량1",
    type: "text",
    x: 0.795,
    y: 0.793,
    w: 0.037,
  },
  {
    id: "work_in_1",
    label: "작업_입고1",
    type: "date",
    x: 0.835,
    y: 0.784,
    w: 0.113,
  },
  {
    id: "work_out_1",
    label: "작업_출고1",
    type: "date",
    x: 0.835,
    y: 0.801,
    w: 0.113,
  },

  // ---- row2(상의)
  {
    id: "work_make_2",
    label: "작업_제작2",
    type: "text",
    x: 0.711,
    y: 0.827,
    w: 0.08,
  },
  {
    id: "work_qty_2",
    label: "작업_수량2",
    type: "text",
    x: 0.795,
    y: 0.827,
    w: 0.037,
  },
  {
    id: "work_in_2",
    label: "작업_입고2",
    type: "date",
    x: 0.835,
    y: 0.818,
    w: 0.113,
  },
  {
    id: "work_out_2",
    label: "작업_출고2",
    type: "date",
    x: 0.835,
    y: 0.835,
    w: 0.113,
  },

  // ---- row3(중)
  {
    id: "work_make_3",
    label: "작업_제작3",
    type: "text",
    x: 0.711,
    y: 0.86,
    w: 0.08,
  },
  {
    id: "work_qty_3",
    label: "작업_수량3",
    type: "text",
    x: 0.795,
    y: 0.86,
    w: 0.037,
  },
  {
    id: "work_in_3",
    label: "작업_입고3",
    type: "date",
    x: 0.835,
    y: 0.852,
    w: 0.113,
  },
  {
    id: "work_out_3",
    label: "작업_출고3",
    type: "date",
    x: 0.835,
    y: 0.869,
    w: 0.113,
  },

  // ---- row4(하의)
  {
    id: "work_make_4",
    label: "작업_제작4",
    type: "text",
    x: 0.711,
    y: 0.895,
    w: 0.08,
  },
  {
    id: "work_qty_4",
    label: "작업_수량4",
    type: "text",
    x: 0.795,
    y: 0.895,
    w: 0.037,
  },
  {
    id: "work_in_4",
    label: "작업_입고4",
    type: "date",
    x: 0.835,
    y: 0.886,
    w: 0.113,
  },
  {
    id: "work_out_4",
    label: "작업_출고4",
    type: "date",
    x: 0.835,
    y: 0.903,
    w: 0.113,
  },

  // ---- row5(셔츠)
  {
    id: "work_make_5",
    label: "작업_제작5",
    type: "text",
    x: 0.711,
    y: 0.929,
    w: 0.08,
  },
  {
    id: "work_qty_5",
    label: "작업_수량5",
    type: "text",
    x: 0.795,
    y: 0.929,
    w: 0.037,
  },
  {
    id: "work_in_5",
    label: "작업_입고5",
    type: "date",
    x: 0.835,
    y: 0.92,
    w: 0.113,
  },
  {
    id: "work_out_5",
    label: "작업_출고5",
    type: "date",
    x: 0.835,
    y: 0.937,
    w: 0.113,
  },
];

function nowKSTISOString() {
  // 브라우저 로컬 시간 기준으로 ISO 찍되, 표시용으로만 사용
  return new Date().toISOString();
}

function toDateInputValue(v: any) {
  // date input은 YYYY-MM-DD만 받음
  if (!v) return "";
  if (typeof v === "string") {
    // ISO or YYYY-MM-DD 모두 커버
    const d = new Date(v);
    if (!isNaN(d.getTime())) return d.toISOString().slice(0, 10);
    if (/^\d{4}-\d{2}-\d{2}$/.test(v)) return v;
  }
  return "";
}

function storageKey(memberKey: string) {
  return `elburim_consult_records__${memberKey}`;
}

function readRecords(memberKey: string): RecordRow[] {
  if (!memberKey) return [];
  try {
    const raw = localStorage.getItem(storageKey(memberKey));
    if (!raw) return [];
    const arr = JSON.parse(raw);
    if (!Array.isArray(arr)) return [];
    return arr;
  } catch {
    return [];
  }
}

function writeRecords(memberKey: string, rows: RecordRow[]) {
  localStorage.setItem(storageKey(memberKey), JSON.stringify(rows));
}

export default function ConsultPage() {
  // “회원 선택” 대신, 일단 상담지에서 최소 식별키(이름/전화)로 묶음
  const [memberName, setMemberName] = useState("");
  const [memberPhone, setMemberPhone] = useState("");

  // 상담지 입력값들
  const [values, setValues] = useState<Record<string, any>>({});
  const memberKey = useMemo(() => {
    const n = memberName.trim();
    const p = memberPhone.trim();
    return `${n}|${p}`;
  }, [memberName, memberPhone]);

  const [records, setRecords] = useState<RecordRow[]>([]);
  const [selectedCreatedAt, setSelectedCreatedAt] = useState<string>("");

  // memberKey가 바뀌면 기록 불러오기
  useEffect(() => {
    if (!memberName.trim() && !memberPhone.trim()) {
      setRecords([]);
      setSelectedCreatedAt("");
      return;
    }
    const rows = readRecords(memberKey).sort((a, b) =>
      a.createdAt < b.createdAt ? 1 : -1
    );
    setRecords(rows);
    setSelectedCreatedAt("");
  }, [memberKey]);

  // “성명/HP”는 위의 memberName/memberPhone과 연동해 자동 채움
  useEffect(() => {
    setValues((prev) => ({
      ...prev,
      name: memberName,
      phone: memberPhone,
    }));
  }, [memberName, memberPhone]);

  const handleChange = (id: string, v: any) => {
    setValues((prev) => ({ ...prev, [id]: v }));
  };

  const handleReset = () => {
    // 회원 식별은 유지하고 상담지만 초기화
    const keepName = memberName;
    const keepPhone = memberPhone;
    setValues({
      name: keepName,
      phone: keepPhone,
    });
    setSelectedCreatedAt("");
  };

  const handleSave = () => {
    if (!memberName.trim() && !memberPhone.trim()) {
      alert("이름 또는 전화번호를 먼저 입력하세요.");
      return;
    }
    const row: RecordRow = {
      createdAt: nowKSTISOString(),
      memberKey,
      values,
    };
    const next = [row, ...records];
    writeRecords(memberKey, next);
    setRecords(next);
    setSelectedCreatedAt(row.createdAt);
    alert("저장 완료!");
  };

  const handleLoad = (createdAt: string) => {
    const found = records.find((r) => r.createdAt === createdAt);
    if (!found) return;
    setValues(found.values || {});
    setSelectedCreatedAt(createdAt);
  };

  return (
    <div style={{ padding: 16 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 10 }}>상담</h1>

      {/* 상단: 고객 식별 + 액션 */}
      <div
        style={{
          display: "flex",
          gap: 12,
          flexWrap: "wrap",
          alignItems: "flex-end",
          marginBottom: 12,
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <label style={{ fontSize: 12, opacity: 0.75 }}>이름</label>
          <input
            value={memberName}
            onChange={(e) => setMemberName(e.target.value)}
            placeholder="예) 박승필"
            style={topInputStyle}
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <label style={{ fontSize: 12, opacity: 0.75 }}>전화번호</label>
          <input
            value={memberPhone}
            onChange={(e) => setMemberPhone(e.target.value)}
            placeholder="예) 010-0000-0000"
            style={topInputStyle}
          />
        </div>

        <button onClick={handleReset} style={btnStyleGray}>
          새 입력
        </button>
        <button onClick={handleSave} style={btnStyle}>
          저장
        </button>

        {selectedCreatedAt ? (
          <span style={{ fontSize: 12, opacity: 0.7 }}>
            불러온/저장 시각: {selectedCreatedAt}
          </span>
        ) : null}
      </div>

      {/* 본문: 좌측 상담지 / 우측 기록 */}
      <div
        style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: 14 }}
      >
        {/* 상담지 영역 */}
        <div>
          <div style={sheetWrapStyle}>
            <div
              style={{
                ...sheetStyle,
                backgroundImage: `url(${TEMPLATE_SRC})`,
              }}
            >
              {FIELDS.map((f) => {
                const left = `${f.x * 100}%`;
                const top = `${f.y * 100}%`;
                const width = `${f.w * 100}%`;

                const common = {
                  position: "absolute" as const,
                  left,
                  top,
                  width,
                };

                const value = values[f.id] ?? "";

                if (f.type === "textarea") {
                  const height = `${(f.h ?? 0.15) * 100}%`;
                  return (
                    <textarea
                      key={f.id}
                      value={String(value)}
                      onChange={(e) => handleChange(f.id, e.target.value)}
                      placeholder=""
                      style={{
                        ...inputOverlayStyle,
                        ...common,
                        height,
                        resize: "none",
                        paddingTop: 8,
                      }}
                    />
                  );
                }

                if (f.type === "date") {
                  return (
                    <input
                      key={f.id}
                      type="date"
                      value={toDateInputValue(value)}
                      onChange={(e) => handleChange(f.id, e.target.value)}
                      style={{
                        ...inputOverlayStyle,
                        ...common,
                      }}
                    />
                  );
                }

                if (f.type === "number") {
                  return (
                    <input
                      key={f.id}
                      inputMode="numeric"
                      value={String(value)}
                      onChange={(e) => handleChange(f.id, e.target.value)}
                      style={{
                        ...inputOverlayStyle,
                        ...common,
                        textAlign: "right",
                      }}
                    />
                  );
                }

                return (
                  <input
                    key={f.id}
                    value={String(value)}
                    onChange={(e) => handleChange(f.id, e.target.value)}
                    style={{
                      ...inputOverlayStyle,
                      ...common,
                    }}
                  />
                );
              })}
            </div>
          </div>

          <p style={{ marginTop: 10, fontSize: 12, opacity: 0.75 }}>
            ※ 입력칸 위치가 안 맞으면 “어느 항목이 위/아래/좌/우로 얼마나”만
            말해줘. FIELDS의 x/y만 조정해서 바로 종이처럼 맞춘다.
          </p>
        </div>

        {/* 기록 영역 */}
        <div style={sidePanelStyle}>
          <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>
            저장 기록
          </h2>

          {!memberName.trim() && !memberPhone.trim() ? (
            <div style={{ fontSize: 13, opacity: 0.7 }}>
              이름/전화번호 입력 후 기록이 표시됩니다.
            </div>
          ) : records.length === 0 ? (
            <div style={{ fontSize: 13, opacity: 0.7 }}>
              저장된 기록이 없습니다.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {records.slice(0, 30).map((r) => (
                <button
                  key={r.createdAt}
                  onClick={() => handleLoad(r.createdAt)}
                  style={{
                    ...recordBtnStyle,
                    borderColor:
                      selectedCreatedAt === r.createdAt
                        ? "#111"
                        : "rgba(0,0,0,0.15)",
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: 13 }}>
                    {r.createdAt}
                  </div>
                  <div style={{ fontSize: 12, opacity: 0.75, marginTop: 4 }}>
                    {previewText(r.values)}
                  </div>
                </button>
              ))}
            </div>
          )}

          <div
            style={{
              marginTop: 14,
              fontSize: 12,
              opacity: 0.7,
              lineHeight: 1.5,
            }}
          >
            지금은 localStorage 저장(이 PC/브라우저 한정)임. 다음 단계에서
            Docker Postgres + Prisma로 “진짜 DB”로 옮길 거다.
          </div>
        </div>
      </div>
    </div>
  );
}

/** ===== styles ===== */

const topInputStyle: React.CSSProperties = {
  width: 260,
  height: 38,
  border: "1px solid rgba(0,0,0,0.18)",
  borderRadius: 8,
  padding: "0 10px",
  outline: "none",
};

const btnStyle: React.CSSProperties = {
  height: 38,
  padding: "0 14px",
  borderRadius: 10,
  border: "1px solid rgba(0,0,0,0.25)",
  background: "#111",
  color: "white",
  cursor: "pointer",
};

const btnStyleGray: React.CSSProperties = {
  ...btnStyle,
  background: "white",
  color: "#111",
};

const sheetWrapStyle: React.CSSProperties = {
  width: "100%",
  maxWidth: 980,
};

const sheetStyle: React.CSSProperties = {
  position: "relative",
  width: "100%",
  // 비율 유지: 상담지 이미지가 세로로 길어서 대략 140%로 잡음(필요시 조정)
  paddingTop: "140%",
  backgroundSize: "contain",
  backgroundRepeat: "no-repeat",
  backgroundPosition: "center top",
  borderRadius: 10,
  border: "1px solid rgba(0,0,0,0.15)",
  boxShadow: "0 6px 20px rgba(0,0,0,0.06)",
  overflow: "hidden",
};

const inputOverlayStyle: React.CSSProperties = {
  height: 34,
  borderRadius: 6,
  border: "1px solid rgba(0,0,0,0.18)",
  background: "rgba(255,255,255,0.55)",
  padding: "0 8px",
  outline: "none",
  fontSize: 14,
};

const sidePanelStyle: React.CSSProperties = {
  border: "1px solid rgba(0,0,0,0.12)",
  borderRadius: 12,
  padding: 12,
  height: "fit-content",
  position: "sticky",
  top: 12,
  background: "white",
};

const recordBtnStyle: React.CSSProperties = {
  textAlign: "left",
  border: "1px solid rgba(0,0,0,0.15)",
  borderRadius: 10,
  padding: 10,
  background: "white",
  cursor: "pointer",
};

function previewText(values: Record<string, any>) {
  const a = values?.orderDetail
    ? String(values.orderDetail).replace(/\s+/g, " ").slice(0, 40)
    : "";
  const price = values?.totalPrice ? ` / 금액:${values.totalPrice}` : "";
  return `${a}${price}`.trim() || "(내용 없음)";
}
